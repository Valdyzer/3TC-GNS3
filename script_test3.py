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
    timer = 5
    # Reset la config du routeur
    tn.write(b"\r\n")
    time.sleep(timer)
    tn.write(b"enable\r\n")
    time.sleep(timer)
    tn.write(b"write erase\r\n") #efface toute la config du routeur
    time.sleep(timer)
    tn.write(b"\r\n")  #Confirmation du "erase"
    time.sleep(timer)
    tn.write(b"reload\r\n") #reload le routeur pour bien appliquer les changements et que la config soit bien effacée
    time.sleep(timer)
    tn.write(b"\r\n")  #Confirmation du "reload"
    time.sleep(timer)
    
def configure_router(host, port, interfaces):
    # Connection à Telnet
    tn = telnetlib.Telnet(host, port)
    timer = 5
    # Configuration des interfaces
    for interface in interfaces:
        tn.write(b"\r\n")
        time.sleep(timer)
        tn.write(b"enable\r\n")
        time.sleep(timer)
        tn.write(b"configure terminal\r\n")
        time.sleep(timer)
        tn.write(b"ipv6 unicast-routing\r\n")
        time.sleep(timer)
        tn.write("interface {}\r\n".format(interface['interface_id']).encode('ascii'))
        time.sleep(timer)
        tn.write(b"ipv6 enable\r\n")
        time.sleep(timer)
        tn.write("ipv6 address {}\r\n".format(interface['ip_address']).encode('ascii'))
        time.sleep(timer)
        tn.write(b"no shutdown\r\n")
        time.sleep(timer)
        tn.write(b"end\r\n")
        time.sleep(timer)

    tn.write(b"exit\r\n") #je suis pas sûre que ça soit nécessaire


def configure_RIP(host, port, interfaces):
    tn = telnetlib.Telnet(host, port)
    timer = 5
    tn.write(b"\r\n")
    time.sleep(timer)
    tn.write(b"enable\r\n")
    time.sleep(timer)
    tn.write(b"configure terminal\r\n")
    time.sleep(timer)
    tn.write(b"ipv6 router rip RIPng\r\n")
    time.sleep(timer)
    tn.write(b"redistribute connected\r\n")
    time.sleep(timer)
    tn.write(b"exit\r\n")
    time.sleep(timer)
    for interface in interfaces:
        if not bool(interface["border_if"]):
            tn.write("interface {}\r\n".format(interface['interface_id']).encode('ascii'))
            time.sleep(timer)
            tn.write(b"ipv6 rip RIPng enable\r\n")
            time.sleep(timer)
            tn.write(b"exit\r\n")
            time.sleep(timer)
    tn.write(b"end\r\n")
    time.sleep(timer)
    tn.write(b"write\r\n")
    
def configure_OSPF(host, port, router_id, area, interfaces): 
    tn = telnetlib.Telnet(host, port)
    timer = 5
    tn.write(b"\r\n")
    time.sleep(timer)
    tn.write(b"enable\r\n")
    time.sleep(timer)
    tn.write(b"configure terminal\r\n")
    time.sleep(timer)
    for interface in interfaces:
        tn.write("interface {}\r\n".format(interface['interface_id']).encode('ascii'))
        time.sleep(timer)
        tn.write("ipv6 ospf 1 area {}\r\n".format(area).encode('ascii'))
        time.sleep(timer)
        tn.write(b"exit\r\n")
        time.sleep(timer)
    tn.write(b"ipv6 router ospf 1\r\n")
    time.sleep(timer)
    tn.write("router-id {}\r\n".format(router_id).encode('ascii'))
    time.sleep(timer)
    for interface in interfaces: 
        if bool(interface["border_if"]): 
            tn.write("passive-interface {}\r\n".format(interface["interface_id"]).encode('ascii'))
            time.sleep(timer)
    tn.write(b"end\r\n")
    time.sleep(timer)
    tn.write(b"write\r\n")
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


def configure_iBGP(host, port, as_id, ipv6_loopback, neighbors, protocol):
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
        tn.write(b"ipv6 ospf 1 area 0\r\n")
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
    
"""
je veux paraleliser ça comme j'ai fait pour la configuration de chaque routeur mais jsp si c'est mieux 
de mettre les deux dans la même boucle for, faire une double boucle pour chaque cas ou une autre chose. 
il faut faire attention à que la configuration ne commence avant d'avoir fini le "reset" de chaque routeur
----À demander--- :) 
"""
for autonomous_system in data['autonomous_systems']:
    for router_name, router_data in autonomous_system['routers'].items():
        threading.Thread(target=reset_router, args=(host, router_data['port'])).start()
time.sleep(100)    

#paralelisation pour configurer chaque routeur
for autonomous_system in data['autonomous_systems']:
    for router_name, router_data in autonomous_system['routers'].items():
        threading.Thread(target=configure_router, args=(host, router_data['port'], router_data['interfaces'])).start()
time.sleep(100)       
#Appel à la fonction qui configure RIP, il faudra paralleliser ça aussi je crois
for AS in data['autonomous_systems']:
    # Regarde si le routing protocol est RIP
    if AS['protocol'] == "RIP":
        # Iteration pour chaque routeur dans l'AS
        for router_name, router_info in AS['routers'].items():
            port = router_info['port']
            interfaces = router_info['interfaces']
            configure_RIP(host, port, interfaces)

#Appel à la fonction configure_OSPF (il faudra paralleliser)
for AS in data['autonomous_systems']:
    # Regarde si le protocol de l'AS est OSPF
    if AS['protocol'] == "OSPF":
        for router_name, router_info in AS['routers'].items():
            port = router_info['port']
            router_id = router_info['router_id']
            area = router_info['area']
            interfaces = router_info['interfaces']
            configure_OSPF(host, port, router_id, area, interfaces)