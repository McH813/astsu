#!/usr/bin/env python3

# -*- coding:utf-8 -*-
import os,sys,socket,ipaddress,argparse
from scapy.all import *
from ctypes import *
from time import sleep
from modules import service_detection,os_detection

if os.name == 'nt':
    clear = lambda:os.system('cls')
else:
    clear = lambda:os.system('clear')
    

def print_figlet():
    clear()
    print(
    '''
    .d8b.  .d8888. d888888b .d8888. db    db 
    d8' `8b 88'  YP `~~88~~' 88'  YP 88    88 
    88ooo88 `8bo.      88    `8bo.   88    88 
    88~~~88   `Y8b.    88      `Y8b. 88    88 
    88   88 db   8D    88    db   8D 88b  d88 
    YP   YP `8888Y'    YP    `8888Y' ~Y8888P' 
    '''
    )

class Scanner:
    def __init__(self,target=None,my_ip=None,protocol=None,timeout=5,interface=None):
        self.target = target
        self.my_ip = my_ip
        self.protocol = protocol
        self.timeout = timeout
        self.interface = interface

    def port_scan(self,stealth=None,port=80):
        if not self.protocol:
            protocol = "TCP"
        else:
            protocol = self.protocol

        if stealth:
            pkt = IP(dst=self.target)/TCP(dport=port,flags="S")
            scan = sr1(pkt,timeout=self.timeout,verbose=0)

            if scan is None:
                return {port: 'Filtered'}

            elif scan.haslayer(TCP):
                if scan.getlayer(TCP).flags == 0x12: # 0x12 SYN+ACk
                    pkt = IP(dst=self.target)/TCP(dport=port,flags="R")
                    send_rst = sr(pkt,timeout=self.timeout,verbose=0)

                    return {port: 'Open'}
                elif scan.getlayer(TCP).flags == 0x14:
                    return {port: 'Closed'}
            elif scan.haslayer(ICMP):
                if int(scan.getlayer(ICMP).type) == 3 and int(scan.getlayer(ICMP).code in [1,2,3,9,10,13]):
                    return {port: 'Filtered'}

        else:
            if protocol is "TCP":
                pkt = IP(dst=self.target)/TCP(dport=port,flags="S")
                scan = sr1(pkt,timeout=self.timeout,verbose=0)

                if scan is None:
                    return {port: 'Filtered'}

                elif scan.haslayer(TCP):
                    if scan.getlayer(TCP).flags == 0x12: # 0x12 SYN+ACk
                        pkt = IP(dst=self.target)/TCP(dport=port,flags="AR")
                        send_rst = sr(pkt,timeout=self.timeout,verbose=0)

                        return {port: 'Open'}
                    elif scan.getlayer(TCP).flags == 0x14:
                        return {port: 'Closed'}

            elif protocol is "UDP":
                pkt = IP(dst=self.target)/UDP(dport=port)
                scan = sr1(pkt, timeout=self.timeout,verbose=0)

                if scan is None:
                    return {port: 'Open/Filtered'}
                elif scan.haslayer(UDP):
                    return {port: 'Closed'}
                elif scan.haslayer(ICMP):
                    if int(scan.getlayer(ICMP).type) == 3 and int(scan.getlayer(ICMP).code) == 3:
                        return {port: 'Closed'}
                    elif int(scan.getlayer(ICMP).type) == 3 and int(scan.getlayer(ICMP).code) in [1,2,9,10,13]:
                        return {port: 'Closed'}

    def handle_port_response(self,ports_saved,response,port):
        """

        Handle the port_scan response

        ports_saved : Dict with the variables where's located the open ports, filtered ports, open or filtered.
        response : the response of port_scan function
        port : port of the scan

        """

        open_ports = ports_saved['open']
        filtered_ports = ports_saved['filtered']
        open_or_filtered = ports_saved['open/filtered']

        if response[port] == "Closed":
            print(f"[-]Port: {port} - Closed")
        elif response[port] == "Open":
            print(f"[+]Port: {port} - Open")
            open_ports.append(port)
        elif response[port] == "Filtered":
            print(f"[*]Port: {port} - Filtered")
            filtered_ports.append(port)
        elif response[port] == "Open/Filtered":
            print(f"[+]Port: {port} - Open/Filtered")
            open_or_filtered.append(port)
        else:
            pass

        return (
            open_ports,
            filtered_ports,
            open_or_filtered
        )

    def common_scan(self,stealth=None):
        print_figlet()

        if not self.protocol:
            protocol = "TCP"
        else:
            protocol = self.protocol

        ports = [21,22,80,443,3306,14147,2121,8080,8000]
        open_ports = []
        filtered_ports = []
        open_or_filtered = []

        if stealth:
            print("[+]Starting - Stealth TCP Port Scan\n")
        else:
            if protocol is "TCP":
                print("[+]Starting - TCP Connect Port Scan\n")
            elif protocol is "UDP":
                print("[+]Starting - UDP Port Scan\n")
            else:
                pass

        for port in ports:
            
            scan = self.port_scan(port=port,stealth=stealth)
        
            if scan:
                ports_saved = {
                    "open": open_ports,
                    "filtered": filtered_ports,
                    "open/filtered": open_or_filtered
                }

                open_ports, filtered_ports, open_or_filtered = self.handle_port_response(ports_saved=ports_saved,response=scan,port=port)

        if open_ports or filtered_ports or open_or_filtered:
            total = len(open_ports) + len(filtered_ports) + len(open_or_filtered)

            print_figlet()
            print(f"[+]Founded {total} ports!")

            for port in open_ports:
                print(f"[+]Port: {port} - Open")
            for port in filtered_ports:
                print(f"[*]Port: {port} - Filtered")
            for port in open_or_filtered:
                print(f"[+]Port: {port} - Open/Filtered")

    def range_scan(self,start,end=None,stealth=None):
        open_ports = []
        filtered_ports = []
        open_or_filtered = []
        protocol = self.protocol

        if not protocol:
            protocol = "TCP"

        print_figlet()
        if protocol is "TCP" and stealth:
            print("[+]Starting - TCP Stealth Port Scan\n")
        elif protocol is "TCP" and not stealth:
            print("[+]Starting - TCP Connect Port Scan\n")
        elif protocol is "UDP":
            print("[+]Starting - UDP Port Scan\n")
        else:
            pass

        if end:
            for port in range(start,end):
                scan = self.port_scan(stealth,port=port)

                if scan:
                    ports_saved = {
                        "open": open_ports,
                        "filtered": filtered_ports,
                        "open/filtered": open_or_filtered
                    }

                    open_ports, filtered_ports, open_or_filtered = self.handle_port_response(ports_saved=ports_saved,response=scan,port=port)

            if open_ports or filtered_ports or open_or_filtered:
                total = len(open_ports) + len(filtered_ports) + len(open_or_filtered)

                print_figlet()
                print(f"[+]Founded {total} ports!")

                for port in open_ports:
                    print(f"[+]Port: {port} - Open")
                for port in filtered_ports:
                    print(f"[*]Port: {port} - Filtered")
                for port in open_or_filtered:
                    print(f"[+]Port: {port} - Open/Filtered")
        else:
            scan = self.port_scan(stealth)

            if scan:
                    ports_saved = {
                        "open": open_ports,
                        "filtered": filtered_ports,
                        "open/filtered": open_or_filtered
                    }

                    open_ports, filtered_ports, open_or_filtered = self.handle_port_response(ports_saved=ports_saved,response=scan,port=start)

            if open_ports or filtered_ports or open_or_filtered:
                total = len(open_ports) + len(filtered_ports) + len(open_or_filtered)

                print_figlet()
                print(f"[+]Founded {total} ports!")

                for port in open_ports:
                    print(f"[+]Port: {port} - Open")
                for port in filtered_ports:
                    print(f"[*]Port: {port} - Filtered")
                for port in open_or_filtered:
                    print(f"[+]Port: {port} - Open/Filtered")

    def os_scan(self):
        print_figlet()

        target_os = os_detection.scan(self.target)
        
        if target_os:
            print(f"[+]Target OS: {target_os}")
        else:
            print("[-]Error when scanning OS")

    def discover_net(self,ip_range=24):
        protocol = self.protocol
        base_ip = self.my_ip

        print_figlet()

        if not protocol:
            protocol = "ICMP"
        else:
            if protocol != "ICMP":
                print(f"[!]Warning: {protocol} is not supported by discover_net function! Changed to ICMP")

        if protocol == "ICMP":
            print("[+]Starting - Discover Hosts Scan")

            base_ip = base_ip.split('.')
            base_ip = f"{str(base_ip[0])}.{str(base_ip[1])}.0.0/{str(ip_range)}"
            hosts_found = []

            hosts = list(ipaddress.ip_network(base_ip))

            for i in hosts:
                try:
                    target = str(i)

                    pkg = IP(dst=target)/ICMP()

                    if interface:
                        answers, unanswered = sr(pkg,timeout=1,verbose=0,iface=interface)
                    else:
                        answers, unanswered = sr(pkg,timeout=1,verbose=0)
                    
                    print(f"[+]Sending ICMP request to {target}")
                    answers.summary(lambda r : hosts_found.append(target))
                except:
                    pass
            
            if not hosts_found:
                print('[-]Not found any host')
            else:
                print(f'\n[+]{len(hosts_found)} hosts founded')
                for host in hosts_found:
                    print(f'[+]Host found: {host}')
            
            return True
        else:
            print("[-]Invalid protocol for this scan")

            return False

    # def list_interfaces(self):
    #     print_figlet()
    #     show_interfaces()

    #     return True

def arguments():
    parser = argparse.ArgumentParser(description="ASTSU - Network Tool",usage="\n\tastsu.py -sC 192.168.0.106\n\tastsu.py -sA 192.168.0.106")
    
    parser.add_argument('-sC',"--scan-common",help="Scan common ports",action="count")
    parser.add_argument('-sA',"--scan-all",help="Scan all ports",action="count")
    parser.add_argument('-sO',"--scan-os",help="Scan OS",action="count")
    parser.add_argument('-sP',"--scan-port",help="Scan defined port",nargs='+',type=int)
    parser.add_argument('-d',"--discover",help="Discover hosts in the network",action="count")
    parser.add_argument('-p',"--protocol",help="Protocol to use in the scans. ICMP,UDP,TCP.",type=str,choices=['ICMP','UDP','TCP'],default=None)
    parser.add_argument('-i',"--interface",help="Interface to use",default=None)
    # parser.add_argument('-li',"--list-interfaces",help="List avaliables interfaces",action="count")
    parser.add_argument('-t',"--timeout",help="Timeout to each request",default=5,type=int)
    parser.add_argument('-st',"--stealth",help="Use Stealth scan method (TCP)",action="count")
    parser.add_argument('Target',nargs='?',default=None)

    args = parser.parse_args()

    return (args, parser)

if __name__ == '__main__':
    args, parser = arguments() 

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8",80))
    ip = s.getsockname()[0]
    s.close()

    scanner = Scanner(target=args.Target,my_ip=ip,protocol=args.protocol,timeout=args.timeout,interface=args.interface)

    if args.scan_common:
        if not args.Target:
            sys.exit(parser.print_help())

        scanner.common_scan(stealth=args.stealth)

    elif args.scan_all:
        if not args.Target:
            sys.exit(parser.print_help())
        
        scanner.range_scan(start=0,end=65535,stealth=args.stealth)

    elif args.scan_os:
        if not args.Target:
            sys.exit(parser.print_help())

        scanner.os_scan()

    elif args.scan_port:
        if not args.Target:
            sys.exit(parser.print_help())
        
        try:
            scanner.range_scan(start=args.scan_port[0],end=args.scan_port[1],stealth=args.stealth)
        except:
            scanner.range_scan(start=args.scan_port,stealth=args.stealth)

    elif args.discover:
        scanner.discover_net() 

    # elif args.list_interfaces:
    #     scanner.list_interfaces()
    else:
        parser.print_help()

