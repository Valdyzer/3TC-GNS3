from gns3fy import Gns3Connector, Project, Node, Link
import telnetlib
import json
import os
import time
import threading 

# path pour le fichier json
json_file = os.path.join(os.path.dirname(__file__), 'network.json')
host = "127.0.0.1"
# Ouvre le fichier JSON
with open(json_file, 'r') as file:
    # Carga los datos JSON desde el archivo
    data = json.load(file)

# Connect to GNS3 server
gns3_server = Gns3Connector("http://127.0.0.1:3080")

# Se connecter au projet
project = Project(name="PGNS3", connector=gns3_server)
project.get()

# Crea instancias de routers utilizando la información del JSON
for AS in data['autonomous_systems']:
    for router in AS['routers']:
        node = Node(project_id=project.project_id, name=router, node_type="dynamips", connector=gns3_server)
        node.start()
        AS["routers"][router]['gns3_id'] = node.node_id

for link in data['links']:
    source_node = link['from'] #R1, nous avons besoin du node_id et pas du nom du routeur
    target_node = link['to']
    interface_a = link['interface_from']
    interface_b = link['interface_to']
    trouve = 0
    i = 0
    #on cherche les node_id
    while i < len(data['autonomous_systems']) and trouve < 2:
        AS = data['autonomous_systems'][i]
        for router in AS['routers']:
            if router == source_node: 
                node_a = AS["routers"][router]['gns3_id']
                trouve += 1
            if router == target_node: 
                node_b = AS["routers"][router]['gns3_id']
                trouve += 1
        i +=1 

    link = Link(project_id=project.project_id, nodes=[node_a, node_b], node_interfaces=[interface_a,interface_b], link_type="ethernet")

#------------------------------------------------------------------
#Fonction pour effacer la configuration actuelle des routeurs. Elle nous permet de partir d'une configuration vièrge
def reset_router(host, port):
    # Connection à Telnet
    tn = telnetlib.Telnet(host, port)
    timer = 2
    # Reset la config du routeur
    tn.write(b"\r\n")
    time.sleep(timer)
    tn.write(b"enable\r\n")
    time.sleep(timer)
    tn.write(b"write erase\r\n") #efface toute la config du routeur
    time.sleep(timer)
    tn.write(b"\r\n")  #Confirmation du "erase"
    time.sleep(timer)
    
def configure_router(host, port, interfaces):
    # Connection à Telnet
    tn = telnetlib.Telnet(host, port)
    timer = 2
    tn.write(b"\r\n")
    time.sleep(timer)
    tn.write(b"enable\r\n")
    time.sleep(timer)
    tn.write(b"configure terminal\r\n")
    time.sleep(timer)
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
    timer = 2
    tn.write(b"\r\n")
    time.sleep(timer)
    tn.write(b"enable\r\n")
    time.sleep(timer)
    tn.write(b"configure terminal\r\n")
    time.sleep(timer)
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
    timer = 2
    tn.write(b"\r\n")
    time.sleep(timer)
    tn.write(b"enable\r\n")
    time.sleep(timer)
    tn.write(b"configure terminal\r\n")
    time.sleep(timer)
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
    timer = 5
    tn.write(b"\r\n")
    time.sleep(timer)
    tn.write(b"enable\r\n")
    time.sleep(timer)
    tn.write(b"configure terminal\r\n")
    time.sleep(timer)
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
    timer = 5
    tn.write(b"\r\n")
    time.sleep(timer)
    tn.write(b"enable\r\n")
    time.sleep(timer)
    tn.write(b"configure terminal\r\n")
    time.sleep(timer)
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
    tn.write(b"end\r\n")
    time.sleep(timer)
    tn.write(b"write\r\n")
    time.sleep(timer) 
    tn.write(b"\r\n")  
    time.sleep(timer) 


def configure_iBGP(host, port, as_id, ipv6_loopback, neighbors, protocol, area):
    tn = telnetlib.Telnet(host, port)
    timer = 5
    tn.write(b"\r\n")
    time.sleep(timer)
    tn.write(b"configure terminal\r\n")
    time.sleep(timer)
    tn.write(b"interface loopback 0\r\n")
    time.sleep(timer)
    tn.write(b"ipv6 enable\r\n")
    time.sleep(timer)
    tn.write("ipv6 address {}\r\n".format(ipv6_loopback).encode('ascii'))
    time.sleep(timer)
    if protocol == "RIP" :
        tn.write(b"ipv6 rip RIPng enable\r\n")
    elif protocol == "OSPF" :
        tn.write("ipv6 ospf 1 area {}\r\n".format(area).encode('ascii'))
    time.sleep(timer)
    tn.write(b"exit\r\n")
    time.sleep(timer)
    tn.write("router bgp {}".format(as_id).encode('ascii'))
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


#-----------Appel aux fonctions------------

#Effacer configuration des routeurs (pour être sûr qu'on part dès zéro)
threads_reset = []   

for autonomous_system in data['autonomous_systems']:
    for router_name, router_data in autonomous_system['routers'].items():
        preset = threading.Thread(target=reset_router, args=(host, router_data['port']))
        preset.start()
        threads_reset.append(preset)

for thread in threads_reset: 
    thread.join()

time.sleep(60)


threads_config = []
#paralelisation pour configurer chaque routeur
for autonomous_system in data['autonomous_systems']:
    for router_name, router_data in autonomous_system['routers'].items():
        pconfig= threading.Thread(target=configure_router, args=(host, router_data['port'], router_data['interfaces']))
        pconfig.start()
        threads_config.append(pconfig)
for thread in threads_config: 
    thread.join()

threads_IGP = []     
#Appel aux fonctions de configuration des protocoles de routage
for AS in data['autonomous_systems']:
    # Regarde si le routing protocol est RIP
    if AS['protocol'] == "RIP":
        # Iteration pour chaque routeur dans l'AS
        for router_name, router_info in AS['routers'].items():
            port = router_info['port']
            interfaces = router_info['interfaces']
            pRIP = threading.Thread(target=configure_RIP,args=(host, port, interfaces))
            pRIP.start()
            threads_IGP.append(pRIP)
    # Regarde si le protocol de l'AS est OSPF
    elif AS['protocol'] == "OSPF":
        for router_name, router_info in AS['routers'].items():
            port = router_info['port']
            router_id = router_info['router_id']
            interfaces = router_info['interfaces']
            threading.Thread(target=configure_OSPF, args=(host, port, router_id, interfaces))
            
            pOSPF = threading.Thread(target=configure_OSPF, args=(host, port, router_id, interfaces))
            pOSPF.start()
            threads_IGP.append(pOSPF)
            
for thread in threads_IGP:
    thread.join()

threads_iBGP = []
for AS in data['autonomous_systems'] :
    for router_info in AS["routers"].values :
        port = router_info['port']
        as_id = AS['as_id']
        ipv6 = router_info['iBGP']['ipv6_loopback']
        neighbors = router_info['iBGP']['neighbors']
        protocol = AS['protocol']
        interface = 0
        while router_info['interfaces'][interface]['border_if'] != 0 :
            interface += 1
        area = router_info['interfaces'][interface]['area']    
        t_iBGP = threading.Thread(target=configure_iBGP, args=(host, port, as_id, ipv6, neighbors, protocol, area))
        t_iBGP.start()
        threads_iBGP.append(t_iBGP)
for thread in threads_iBGP:
    thread.join()


for AS in data['autonomous_systems']:
    for router_info in AS["routers"].values:
        port = router_info['port']
        as_id = AS['as_id']
        router_id = router_info['router_id']
        t_eBGP = threading.Thread(target=configure_eBGP, args=(host, port, as_id, router_id))
        t_eBGP.start()
        t_eBGP.join()  

        if router_info["BR"]==1: 
            neighbors = router_info['eBGP']['neighbors']
            networks = router_info['networks']
            t_eBGP_BR = threading.Thread(target=configure_eBGP_BR, args=(host, port, as_id, neighbors, networks))
            t_eBGP_BR.start()
          