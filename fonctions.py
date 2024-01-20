from gns3fy import Gns3Connector, Project, Node, Link
import telnetlib
import time

#Fonction pour effacer la configuration actuelle des routeurs. Elle nous permet de partir d'une configuration vièrge
def reset_router(host, port):
    # Connection à Telnet
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    # Reset la config du routeur
    tn.write(b"\r\n")
    time.sleep(timer)
    tn.write(b"enable\r\n")
    time.sleep(timer)
    tn.write(b"delete nvram:startup-config\r\n") #efface toute la config du routeur
    time.sleep(timer)
    tn.write(b"\r\n")  #Confirmation du "erase"
    time.sleep(timer)
    tn.write(b"\r\n")  #Confirmation du "erase"
    time.sleep(timer)

def conft(tn):
    timer = 0.2
    tn.write(b"\r\n")
    time.sleep(timer)
    tn.write(b"enable\r\n")
    time.sleep(timer)
    tn.write(b"configure terminal\r\n")
    time.sleep(timer)
    
def configure_router(host, port, interfaces):
    # Connection à Telnet
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    conft(tn)
    tn.write(b"ipv6 unicast-routing\r\n")
    time.sleep(timer)

    # Configuration des interfaces
    for interface in interfaces:
        tn.write("interface {}\r\n".format(interface['interface_id']).encode('ascii'))
        time.sleep(timer)
        tn.write(b"ipv6 enable\r\n")
        time.sleep(timer)
        tn.write("ipv6 address {}\r\n".format(interface['ip_address']).encode('ascii'))
        time.sleep(timer)
        tn.write(b"no shutdown\r\n")
        time.sleep(timer)
        tn.write(b"exit\r\n")
        time.sleep(timer)

    tn.write(b"end\r\n")
    time.sleep(timer) 
    tn.write(b"write\r\n")
    time.sleep(timer)
    tn.write(b"\r\n")
    time.sleep(timer)

def configure_RIP(host, port, interfaces):
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    conft(tn)
    tn.write(b"ipv6 router rip ripng\r\n")
    time.sleep(timer)
    tn.write(b"redistribute connected\r\n")
    time.sleep(timer)
    tn.write(b"exit\r\n")
    time.sleep(timer)
    for interface in interfaces:
        if interface["border_if"] == 0:
            tn.write("interface {}\r\n".format(interface['interface_id']).encode('ascii'))
            time.sleep(timer)
            tn.write(b"ipv6 rip ripng enable\r\n")
            time.sleep(timer)
            tn.write(b"exit\r\n")
            time.sleep(timer)
    tn.write(b"end\r\n")
    time.sleep(timer)
    tn.write(b"write\r\n")
    time.sleep(timer)
    tn.write(b"\r\n")
    time.sleep(timer)
    
def configure_OSPF(host, port, router_id, interfaces): 
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    conft(tn)
    for interface in interfaces:
        tn.write("interface {}\r\n".format(interface['interface_id']).encode('ascii'))
        time.sleep(timer)
        tn.write("ipv6 ospf 1 area {}\r\n".format(interface["area"]).encode('ascii'))
        time.sleep(timer)
        tn.write("ipv6 ospf cost {}\r\n".format(interface["cost"]).encode('ascii'))
        time.sleep(timer)
        tn.write(b"exit\r\n")
        time.sleep(timer)
    tn.write(b"ipv6 router ospf 1\r\n")
    time.sleep(timer)
    tn.write("router-id {}\r\n".format(router_id).encode('ascii'))
    time.sleep(timer)
    for interface in interfaces: 
        if interface["border_if"] == 1: 
            tn.write("passive-interface {}\r\n".format(interface["interface_id"]).encode('ascii'))
            time.sleep(timer)
    tn.write(b"end\r\n")
    time.sleep(timer)
    tn.write(b"write\r\n")
    time.sleep(timer)
    tn.write(b"\r\n")
    time.sleep(timer)
    
def configure_eBGP(host, port, as_id, router_id):
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    conft(tn)
    tn.write("router bgp {}\r\n".format(as_id).encode('ascii'))
    time.sleep(timer)
    tn.write(b"no bgp default ipv4-unicast\r\n")
    time.sleep(timer)
    tn.write("bgp router {}\r\n".format(router_id).encode('ascii'))
    time.sleep(timer)
    tn.write(b"end\r\n")
    time.sleep(timer)
    tn.write(b"write\r\n")
    time.sleep(timer)
    tn.write(b"\r\n")
    time.sleep(timer)

def configure_eBGP_BR(host, port, as_id, neighbors, networks):
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    conft(tn)
    tn.write("router bgp {}\r\n".format(as_id).encode('ascii'))
    time.sleep(timer)
    for neighbor in neighbors :
        tn.write("neighbor {} remote-as {}\r\n".format(neighbor["ipv6"], neighbor["as_id"]).encode('ascii'))
        time.sleep(timer)
        tn.write(b"address-family ipv6 unicast\r\n")
        time.sleep(timer)
        tn.write("neighbor {} activate\r\n".format(neighbor["ipv6"]).encode('ascii'))
        time.sleep(timer)
        tn.write(b"exit\r\n")
        time.sleep(timer)
    tn.write(b"address-family ipv6 unicast\r\n")
    time.sleep(timer)
    for network in networks :
        tn.write("network {}\r\n".format(network).encode('ascii'))
        time.sleep(timer)
    tn.write(b"exit\r\n")
    time.sleep(timer)
    tn.write(b"exit\r\n")
    time.sleep(timer)
    for network in networks :
        tn.write("ipv6 route {} Null0\r\n".format(network).encode('ascii'))
        time.sleep(timer)
    tn.write(b"end\r\n")
    time.sleep(timer)
    tn.write(b"write\r\n")
    time.sleep(timer) 
    tn.write(b"\r\n")  
    time.sleep(timer) 


def configure_iBGP(host, port, as_id, ipv6_loopback, neighbors, protocol, area):
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    conft(tn)
    tn.write(b"interface loopback 0\r\n")
    time.sleep(timer)
    tn.write(b"ipv6 enable\r\n")
    time.sleep(timer)
    tn.write("ipv6 address {}/126\r\n".format(ipv6_loopback).encode('ascii'))
    time.sleep(timer)
    if protocol == "RIP" :
        tn.write(b"ipv6 rip ripng enable\r\n")
    elif protocol == "OSPF" :
        tn.write("ipv6 ospf 1 area {}\r\n".format(area).encode('ascii'))
    time.sleep(timer)
    tn.write(b"exit\r\n")
    time.sleep(timer)
    tn.write("router bgp {}\r\n".format(as_id).encode('ascii'))
    time.sleep(timer)
    for neighbor in neighbors :
        tn.write("neighbor {} remote-as {}\r\n".format(neighbor, as_id).encode('ascii'))
        time.sleep(timer)
        tn.write("neighbor {} update-source loopback 0\r\n".format(neighbor).encode('ascii'))
        time.sleep(timer)
        tn.write(b"address-family ipv6 unicast\r\n")
        time.sleep(timer)
        tn.write("neighbor {} activate\r\n".format(neighbor).encode('ascii'))
        time.sleep(timer)
        tn.write(b"exit\r\n")
        time.sleep(timer)
    tn.write(b"end\r\n")
    time.sleep(timer)
    tn.write(b"write\r\n")
    time.sleep(timer)
    tn.write(b"\r\n")
    time.sleep(timer)

    
