from gns3fy import Gns3Connector, Project, Node
import json
import os

def lect(dict) :
    """
    Lit et charge des données depuis un fichier JSON.

    Parameters:
        dict (str): Nom du fichier JSON.

    Returns:
        dict: Données chargées depuis le fichier JSON.
    """
    # path pour le fichier json
    json_file = os.path.join(os.path.dirname(__file__), dict)
    
    # Ouvre le fichier JSON
    with open(json_file, 'r') as file:
        # Carga los datos JSON desde el archivo
        data = json.load(file)

    return(data)

def adressage(data):
    """
    Attribue des adresses IPv6 aux routeurs en fonction de la structure du sous-réseau.

    Parameters:
        data (dict): Données réseau au format JSON.

    Returns:
        None
    """
    for subnetworks in data["networks"].values():
        for subnetwork, routers in subnetworks.items():
            position = subnetwork.find("::")
            base = subnetwork.split('::')[0]
            for i, router in enumerate(routers.keys()):
                routers[router]["ipv6"] = f"{subnetwork[:position+2]}{i+1}{subnetwork[position+2:]}"



def data_interf(data): 
    """
    Met à jour les informations d'interface en fonction de la structure du réseau dans le dictionnaire.
    Chaque interface contient {interface, link_to, ip_address, area, border_if (si l'interface est de bordure) et cost (OSPF)}

    Parameters:
        data (dict): Données réseau au format JSON.

    Returns:
        None
    """
    for subnetworks in data["networks"].values():
        for subnetwork, routers in subnetworks.items():
            router = list(routers.keys())
            for AS in data['autonomous_systems']:
                if (router[0] in AS["routers"].keys()) and (router[1] in AS["routers"].keys()) :
                    interface = {"interface_id": routers[router[0]]["interface"], "link_to": router[1], "ip_address": routers[router[0]]["ipv6"], "area": "0", "border_if": 0, "cost": routers[router[0]]["cost"]}
                    AS["routers"][router[0]]["interfaces"].append(interface)
                    interface = {"interface_id": routers[router[1]]["interface"], "link_to": router[0], "ip_address": routers[router[1]]["ipv6"], "area": "0", "border_if": 0, "cost": routers[router[1]]["cost"]}
                    AS["routers"][router[1]]["interfaces"].append(interface)  
                    break 
                elif router[0] in AS["routers"].keys():
                    interface = {"interface_id": routers[router[0]]["interface"], "link_to": router[1], "ip_address": routers[router[0]]["ipv6"], "area": "0", "border_if": 1, "cost": routers[router[0]]["cost"]}
                    AS["routers"][router[0]]["interfaces"].append(interface)                
                elif router[1] in AS["routers"].keys():
                    interface = {"interface_id": routers[router[1]]["interface"], "link_to": router[0], "ip_address": routers[router[1]]["ipv6"], "area": "0", "border_if": 1, "cost": routers[router[1]]["cost"]}
                    AS["routers"][router[1]]["interfaces"].append(interface) 
                    

def data_iBGP(data):
    """
    Configure les informations iBGP pour les routeurs. L'adresse loopback sera 
    2001:192:168:1{num_router}/126 (num_router avec 2 chiffres)

    Parameters:
        data (dict): Données réseau au format JSON.

    Returns:
        None
    """ 
    for AS in data['autonomous_systems']:
        loopback = []
        for router_name, router_info in AS["routers"].items():
            router_number = router_name[1:]  # Obtient  le numéro après "R"
            if len(router_number) ==1: 
                router_number = "0" + router_number
            router_info["iBGP"]  = {}
            addr_loopback = "2001:192:168:1{}::1/126".format(router_number)
            loopback.append(addr_loopback)
            router_info["iBGP"]["ipv6 loopback"] = addr_loopback
            router_info["iBGP"]["neighbors"] = []
            
        for router_name, router_info in AS["routers"].items():
            router_info["iBGP"]["neighbors"] = [addr for addr in loopback if addr != router_info["iBGP"]["ipv6 loopback"]]   

def data_eBGP(data): 
    """
    Configure les informations eBGP pour les routeurs telles que les neighbors eBGP et les networks 

    Parameters:
        data (dict): Données réseau au format JSON.

    Returns:
        None
    """
    for AS in data['autonomous_systems']:
        for routerA, router_info in AS['routers'].items():
            for interface in router_info["interfaces"]:
                if interface["border_if"] == 1:
                    routerB = interface["link_to"]
                    router_info["eBGP"] = {}
                    router_info["eBGP"]["neighbors"] = [] #liste de dictionnaires
                    router_info["eBGP"]["networks"] = [AS["network address"]] #liste de strings
                    #router_info["eBGP"]["networks"].append(""" adresse reseau lien """) 
                    #je sais pas comment la retrouver, elle est dans "networks"
                    for AS1 in data["autonomous_systems"]:
                        if routerB in AS1["routers"].keys():
                            for intf in AS1["routers"][routerB]["interfaces"]:
                                if intf["link_to"] == routerA: 
                                    ipv6 = intf["ip_address"]
                                    position_slash = ipv6.find("/")
                                    position_points = ipv6.find("::")
                                    ipv6_network = ipv6[:position_points+2]+ipv6[position_slash:]
                                    router_info["eBGP"]["networks"].append(ipv6_network)
                                    neighbor = {"ipv6": intf["ip_address"], "as_id": AS1["as_id"]}
                                    router_info["eBGP"]["neighbors"].append(neighbor)

def init_json(dict_name):
    """
    Initialise et configure les données réseau à partir d'un fichier JSON.
    Fonction qui appelle toutes les autres fonctions pour remplir automatiquement le dictionnaire 

    Parameters:
        dict (str): Chemin relatif du fichier JSON.

    Returns:
        dict: Données réseau configurées.
    """
    data = lect(dict_name)
    adressage(data)
    data_interf(data)
    data_iBGP(data)
    data_eBGP(data)
    dict_name = dict_name[(dict_name.find('\\')+1):]
    if "\\" in dict_name :
        dict_name = dict_name[(dict_name.find('\\')+1):]
    new_json = "auto_" + dict_name 
    print(new_json)
    json_object = json.dumps(data, indent=4)
    with open(new_json, 'w') as fichier_json: 
        fichier_json.write(json_object)
    return data 
  

def init_GNS3(data, nom_projet):
    """
    Initialise et configure la connexion à un projet GNS3 avec des informations réseau.

    Parameters:
        data (dict): Données réseau au format JSON.
        nom_projet (str): Nom du projet GNS3.
        host (str): adresse ip de la machine

    Returns:
        None
        
    """
    # Connect to GNS3 server
    gns3_server = Gns3Connector("http://127.0.0.1:3080")
    # Se connecter au projet
    project = Project(name=nom_projet, connector=gns3_server)
    project.get()

    for AS in data['autonomous_systems']:
        for router in AS['routers'].keys():
            node = Node(project_id=project.project_id, name=router, node_type="dynamips", connector=gns3_server)
            node.start()
            node.get()
            AS['routers'][router]['port'] = node.console
            