import telnetlib
import time

def ecriture_fichier(fichier, contenu):
    """
    Cette fonction ouvre un fichier en mode 'append' et y écrit le contenu spécifié.
    
    Args:
        fichier (str): Le nom du fichier à ouvrir.
        contenu (str): Le contenu à écrire dans le fichier.
    """
    with open(fichier, 'a') as fichier:
        fichier.write(contenu)


#Fonction pour effacer la configuration actuelle des routeurs. Elle nous permet de partir d'une configuration vièrge
def reset_router(host, port, fichier):
    """
    Cette fonction se connecte à un routeur via Telnet et réinitialise sa configuration. 
    Elle enregistre également les commandes utilisées dans un fichier.
    
    Args:
        host (str): L'adresse IP du routeur.
        port (int): Le port Telnet du routeur.
        fichier (str): Le nom du fichier où sauvegarder les commandes.
    """
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
    
    ecriture_fichier(fichier, "\r\nenable\r\ndelete nvram:startup-config\r\n\r\n\r\n")

def conft(tn, fichier):
    """
    Cette fonction se connecte à un routeur via Telnet et entre en mode de configuration globale. 
    Elle enregistre également les commandes utilisées dans un fichier.
    
    Args:
        tn (Telnet): Une instance de Telnet.
        fichier (str): Le nom du fichier où sauvegarder les commandes.
    """
    timer = 0.2
    tn.write(b"\r\n")
    time.sleep(timer)
    tn.write(b"enable\r\n")
    time.sleep(timer)
    tn.write(b"configure terminal\r\n")
    time.sleep(timer)
    
    ecriture_fichier(fichier, "\r\nenable\r\nconfigure terminal\r\n")
    
def configure_router(host, port, interfaces, fichier):
    """
    Cette fonction se connecte à un routeur via Telnet et configure ses interfaces. 
    Elle enregistre également les commandes utilisées dans un fichier.
    
    Args:
        host (str): L'adresse IP du routeur.
        port (int): Le port Telnet du routeur.
        interfaces (list): Une liste des interfaces à configurer.
        fichier (str): Le nom du fichier où sauvegarder les commandes.
    """
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    conft(tn, fichier)
    tn.write(b"ipv6 unicast-routing\r\n")
    time.sleep(timer)
    
    ecriture_fichier(fichier,
                     "ipv6 unicast-routing\r\n")

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
        
        ecriture_fichier(fichier, 
                         "interface " + interface['interface_id'] + "\r\n" + "ipv6 enable\r\n" +
                         "ipv6 address " + interface['ip_address'] + "\r\n" + "no shutdown\r\nexit\r\n")

    tn.write(b"end\r\n")
    time.sleep(timer) 
    tn.write(b"write\r\n")
    time.sleep(timer)
    tn.write(b"\r\n")
    time.sleep(timer)
    
    ecriture_fichier(fichier, "end\r\nwrite\r\n\r\n")

def configure_RIP(host, port, interfaces, fichier):
    """
    Cette fonction se connecte à un routeur via Telnet et configure le protocole RIP. 
    Elle enregistre également les commandes utilisées dans un fichier.
    
    Args:
        host (str): L'adresse IP du routeur.
        port (int): Le port Telnet du routeur.
        interfaces (list): Une liste des interfaces à configurer.
        fichier (str): Le nom du fichier où sauvegarder les commandes.
    """
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    conft(tn, fichier)
    tn.write(b"ipv6 router rip ripng\r\n")
    time.sleep(timer)
    tn.write(b"redistribute connected\r\n")
    time.sleep(timer)
    tn.write(b"exit\r\n")
    time.sleep(timer)
    
    ecriture_fichier(fichier,
                     "ipv6 router rip ripng\r\nredistribute connected\r\nexit\r\n")
    
    for interface in interfaces:
        if interface["border_if"] == 0:
            tn.write("interface {}\r\n".format(interface['interface_id']).encode('ascii'))
            time.sleep(timer)
            tn.write(b"ipv6 rip ripng enable\r\n")
            time.sleep(timer)
            tn.write(b"exit\r\n")
            time.sleep(timer)
            
            ecriture_fichier(fichier, 
                             "interface " + interface['interface_id'] + "\r\n" +
                             "ipv6 rip ripng enable\r\nexit\r\n")
                        
    tn.write(b"end\r\n")
    time.sleep(timer)
    tn.write(b"write\r\n")
    time.sleep(timer)
    tn.write(b"\r\n")
    time.sleep(timer)
    
    ecriture_fichier(fichier, 
                     "end\r\nwrite\r\n\r\n")
    
def configure_OSPF(host, port, router_id, interfaces, fichier):
    """
    Cette fonction se connecte à un routeur via Telnet et configure le protocole OSPF. 
    Elle enregistre également les commandes utilisées dans un fichier.
    
    Args:
        host (str): L'adresse IP du routeur.
        port (int): Le port Telnet du routeur.
        router_id (str): L'ID du routeur.
        interfaces (list): Une liste des interfaces à configurer.
        fichier (str): Le nom du fichier où sauvegarder les commandes.
    """ 
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    conft(tn, fichier)
    for interface in interfaces:
        tn.write("interface {}\r\n".format(interface['interface_id']).encode('ascii'))
        time.sleep(timer)
        tn.write("ipv6 ospf 1 area {}\r\n".format(interface["area"]).encode('ascii'))
        time.sleep(timer)
        tn.write("ipv6 ospf cost {}\r\n".format(interface["cost"]).encode('ascii'))
        time.sleep(timer)
        tn.write(b"exit\r\n")
        time.sleep(timer)
        
        ecriture_fichier(fichier,
                         "interface " + interface['interface_id'] + "\r\n" +
                         "ipv6 ospf 1 area " + interface["area"] + "\r\n" +
                         "ipv6 ospf cost " + interface["cost"] + "\r\n" +
                         "exit\r\n")
        
    tn.write(b"ipv6 router ospf 1\r\n")
    time.sleep(timer)
    tn.write("router-id {}\r\n".format(router_id).encode('ascii'))
    time.sleep(timer)
    
    ecriture_fichier(fichier,
                     "ipv6 router ospf 1\r\n" + "router-id " + router_id + "\r\n")
    
    for interface in interfaces: 
        if interface["border_if"] == 1: 
            tn.write("passive-interface {}\r\n".format(interface["interface_id"]).encode('ascii'))
            time.sleep(timer)
            
            ecriture_fichier(fichier, 
                             "passive-interface " + interface["interface_id"] + "\r\n")
            
    tn.write(b"end\r\n")
    time.sleep(timer)
    tn.write(b"write\r\n")
    time.sleep(timer)
    tn.write(b"\r\n")
    time.sleep(timer)
    
    ecriture_fichier(fichier,
                     "end\r\nwrite\r\n\r\n")
    
def configure_eBGP(host, port, as_id, router_id, fichier):
    """
    Cette fonction se connecte à un routeur via Telnet et configure le protocole eBGP. 
    Elle enregistre également les commandes utilisées dans un fichier.
    
    Args:
        host (str): L'adresse IP du routeur.
        port (int): Le port Telnet du routeur.
        as_id (str): L'ID du système autonome.
        router_id (str): L'ID du routeur.
        fichier (str): Le nom du fichier où sauvegarder les commandes.
    """
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    conft(tn, fichier)
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
    
    ecriture_fichier(fichier,
                     "router bgp " + as_id + "\r\n" +
                     "no bgp default ipv4-unicast\r\n"+
                     "bgp router " + router_id + "\r\n" +
                     "end\r\nwrite\r\n\r\n")

def configure_eBGP_BR(host, port, as_id, policies, neighbors, networks, fichier):
    """
    Cette fonction se connecte à un routeur via Telnet et configure le protocole eBGP pour les routeurs de bordure. 
    Elle enregistre également les commandes utilisées dans un fichier.
    
    Args:
        host (str): L'adresse IP du routeur.
        port (int): Le port Telnet du routeur.
        as_id (str): L'ID du système autonome.
        neighbors (list): Une liste des voisins à configurer.
        networks (list): Une liste des réseaux à configurer.
        fichier (str): Le nom du fichier où sauvegarder les commandes.
    """
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    conft(tn, fichier)
    tn.write("router bgp {}\r\n".format(as_id).encode('ascii'))
    time.sleep(timer)
    
    ecriture_fichier(fichier,
                     "router bgp " + as_id + "\r\n")
    
    for neighbor in neighbors :        
        ip_neighbor = neighbor["ipv6"][:(neighbor["ipv6"].find("/"))]
        tn.write("neighbor {} remote-as {}\r\n".format(ip_neighbor, neighbor["as_id"]).encode('ascii'))
        time.sleep(timer)
        tn.write(b"address-family ipv6 unicast\r\n")
        time.sleep(timer)
        tn.write("neighbor {} activate\r\n".format(ip_neighbor).encode('ascii'))
        time.sleep(timer)
        tn.write(b"exit\r\n")
        time.sleep(timer)
        
        ecriture_fichier(fichier,
                         "neighbor " + ip_neighbor + " remote-as " + neighbor["as_id"] + "\r\n" +
                         "address-family ipv6 unicast\r\n"+
                         "neighbor " + ip_neighbor + " activate\r\n" +
                         "exit\r\n")
        
    tn.write(b"address-family ipv6 unicast\r\n")
    time.sleep(timer)    
    ecriture_fichier(fichier, "address-family ipv6 unicast\r\n")
    
    for network in networks :
        tn.write("network {}\r\n".format(network).encode('ascii'))
        time.sleep(timer)
        ecriture_fichier(fichier, "network " + network + "\r\n")
    tn.write(b"exit\r\n")
    time.sleep(timer)
    tn.write(b"exit\r\n")
    time.sleep(timer)
    ecriture_fichier(fichier, "exit\r\nexit\r\n")
    for network in networks :
        tn.write("ipv6 route {} Null0\r\n".format(network).encode('ascii'))
        time.sleep(timer)
        ecriture_fichier(fichier, "ipv6 route " + network + " Null0\r\n")
        
    tn.write(b"end\r\n")
    time.sleep(timer)
    tn.write(b"write\r\n")
    time.sleep(timer) 
    tn.write(b"\r\n")  
    time.sleep(timer)
    
    ecriture_fichier(fichier,
                     "end\r\nwrite\r\n\r\n") 


def configure_iBGP(host, port, as_id, ipv6_loopback, neighbors, protocol, area, fichier):
    """
    Cette fonction se connecte à un routeur via Telnet et configure le protocole iBGP. 
    Elle enregistre également les commandes utilisées dans un fichier.
    
    Args:
        host (str): L'adresse IP du routeur.
        port (int): Le port Telnet du routeur.
        as_id (str): L'ID du système autonome.
        ipv6_loopback (str): L'adresse IPv6 de l'interface de bouclage.
        neighbors (list): Une liste des voisins à configurer.
        protocol (str): Le protocole de routage à utiliser ("RIP" ou "OSPF").
        area (str): L'aire OSPF à configurer.
        fichier (str): Le nom du fichier où sauvegarder les commandes.
    """
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    conft(tn, fichier)
    tn.write(b"interface loopback 0\r\n")
    time.sleep(timer)
    tn.write(b"ipv6 enable\r\n")
    time.sleep(timer)
    tn.write("ipv6 address {}\r\n".format(ipv6_loopback).encode('ascii'))
    time.sleep(timer)
    
    ecriture_fichier(fichier,
                     "interface loopback 0\r\nipv6 enable\r\n" +
                     "ipv6 address " + ipv6_loopback + "\r\n")
    
    if protocol == "RIP" :
        tn.write(b"ipv6 rip ripng enable\r\n")
        ecriture_fichier(fichier, "ipv6 rip ripng enable\r\n")
    elif protocol == "OSPF" :
        tn.write("ipv6 ospf 1 area {}\r\n".format(area).encode('ascii'))
        ecriture_fichier(fichier, "ipv6 ospf 1 area " + area + "\r\n")        
    time.sleep(timer)
    tn.write(b"exit\r\n")
    time.sleep(timer)
    tn.write("router bgp {}\r\n".format(as_id).encode('ascii'))
    time.sleep(timer)
    ecriture_fichier(fichier, "exit\r\n" + "router bgp " + as_id + "\r\n")
    for neighbor in neighbors :
        ipv6_neighbor = neighbor[:neighbor.find('/')]
        tn.write("neighbor {} remote-as {}\r\n".format(ipv6_neighbor, as_id).encode('ascii'))
        time.sleep(timer)
        tn.write("neighbor {} update-source loopback 0\r\n".format(ipv6_neighbor).encode('ascii'))
        time.sleep(timer)
        tn.write(b"address-family ipv6 unicast\r\n")
        time.sleep(timer)
        tn.write("neighbor {} activate\r\n".format(ipv6_neighbor).encode('ascii'))
        time.sleep(timer)
        tn.write(b"exit\r\n")
        time.sleep(timer)
        
        ecriture_fichier(fichier,
                         "neighbor " + neighbor + " remote-as " + as_id + "\r\n" +
                         "neighbor " + neighbor + " update-source loopback 0\r\n" +
                         "address-family ipv6 unicast\r\n"+
                         "neighbor " + ipv6_neighbor + " activate\r\n" + "exit\r\n")
        
    tn.write(b"end\r\n")
    time.sleep(timer)
    tn.write(b"write\r\n")
    time.sleep(timer)
    tn.write(b"\r\n")
    time.sleep(timer)
    
    ecriture_fichier(fichier,
                     "end\r\nwrite\r\n\r\n")

def policies(host, port, as_id, neighbors, policies, fichier):
    """
    Cette fonction se connecte à un routeur via Telnet et configure les politiques de routage BGP. 
    Elle enregistre également les commandes utilisées dans un fichier.
    
    Args:
        host (str): L'adresse IP du routeur.
        port (int): Le port Telnet du routeur.
        as_id (str): L'ID du système autonome.
        neighbors (list): Une liste des voisins à configurer.
        policies (dict): Un dictionnaire des politiques à appliquer.
        fichier (str): Le nom du fichier où sauvegarder les commandes.
    """
    tn = telnetlib.Telnet(host, port)
    timer = 0.2
    conft(tn, fichier)
    tn.write("router bgp {}\r\n".format(as_id).encode('ascii'))
    time.sleep(timer)
    tn.write(b"address-family ipv6 unicast\r\n")
    time.sleep(timer)

    ecriture_fichier(fichier, 
                     "router bgp " + as_id + "\r\n" +
                     "address-family ipv6 unicast\r\n")

    for neighbor in neighbors:
        policy = policies["AS" + neighbor["as_id"]]
        ip_neighbor = neighbor["ipv6"][:(neighbor["ipv6"].find("/"))]
        tn.write("neighbor {} route-map {} in\r\n".format(ip_neighbor, policy).encode('ascii'))
        time.sleep(timer)
        ecriture_fichier(fichier, "neighbor " + ip_neighbor + " route-map " + policy + " in\r\n")
    tn.write(b"exit\r\n")
    time.sleep(timer)
    tn.write(b"exit\r\n")
    time.sleep(timer)
    tn.write("route-map {} permit 10\r\n".format(policy).encode('ascii'))
    time.sleep(timer)
    ecriture_fichier(fichier, "exit\r\nexit\r\n" + "route-map " + policy + " permit 10\r\n")    
    if policy == "client" :
        tn.write(b"set local-preference 300\r\n")
        ecriture_fichier(fichier, "set local-preference 300\r\n")
    elif policy == "peer" :
        tn.write(b"set local-preference 100\r\n")
        ecriture_fichier(fichier, "set local-preference 100\r\n")
    elif policy == "provider" :
        tn.write(b"set local-preference 50\r\n")
        ecriture_fichier(fichier, "set local-preference 50\r\n")
    time.sleep(timer)
    tn.write(b"end\r\n")
    time.sleep(timer)
    tn.write(b"write\r\n")
    time.sleep(timer)
    tn.write(b"\r\n")
    time.sleep(timer)

    ecriture_fichier(fichier, 
                     "end\r\nwrite\r\n\r\n")


