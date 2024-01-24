from gns3fy import Gns3Connector, Project, Node, Link
import json
import os

def lect(dict) :
    # path pour le fichier json
    json_file = os.path.join(os.path.dirname(__file__), dict)
    
    # Ouvre le fichier JSON
    with open(json_file, 'r') as file:
        # Carga los datos JSON desde el archivo
        data = json.load(file)

    return(data)

def adressage(data):
    for subnetworks in data["networks"].values():
        for subnetwork, routers in subnetworks.items():
            position = subnetwork.find("::")
            base = subnetwork.split('::')[0]
            for i, router in enumerate(routers.keys()):
                routers[router]["ipv6"] = f"{subnetwork[:position+2]}{i+1}{subnetwork[position+2:]}"



def data_interf(data): 
    for subnetworks in data["networks"].values():
        for subnetwork, routers in subnetworks.items():
            router = list(routers.keys())
            for AS in data['autonomous_systems']:
                if (router[0] in AS["routers"].keys()) and (router[1] in AS["routers"].keys()) :
                    interface = {"interface_id": routers[router[0]]["interface"], "link_to": router[1], "ip_address": routers[router[0]]["ipv6"], "area": "0", "border_if": 0, "cost": "100"}
                    AS["routers"][router[0]]["interfaces"].append(interface)
                    interface = {"interface_id": routers[router[1]]["interface"], "link_to": router[0], "ip_address": routers[router[1]]["ipv6"], "area": "0", "border_if": 0, "cost": "100"}
                    AS["routers"][router[1]]["interfaces"].append(interface)  
                    break 
                elif router[0] in AS["routers"].keys():
                    interface = {"interface_id": routers[router[0]]["interface"], "link_to": router[1], "ip_address": routers[router[0]]["ipv6"], "area": "0", "border_if": 1, "cost": "100"}
                    AS["routers"][router[0]]["interfaces"].append(interface)                
                elif router[1] in AS["routers"].keys():
                    interface = {"interface_id": routers[router[1]]["interface"], "link_to": router[0], "ip_address": routers[router[1]]["ipv6"], "area": "0", "border_if": 1, "cost": "100"}
                    AS["routers"][router[1]]["interfaces"].append(interface) 
                

def data_iBGP(data): 
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
                                    ipv6_neighbor = ipv6[:position_slash]
                                    position_points = ipv6.find("::")
                                    ipv6_network = ipv6[:position_points+2]+ipv6[position_slash:]
                                    router_info["eBGP"]["networks"].append(ipv6_network)
                                    neighbor = {"ipv6": intf["ip_address"], "as_id": AS1["as_id"]}
                                    router_info["eBGP"]["neighbors"].append(neighbor)
                    print(router_info["eBGP"])

def init_json(dict):
    data = lect(dict)
    adressage(data)
    data_interf(data)
    data_iBGP(data)
    data_eBGP(data)
    return data 
  

def init_GNS3(data, nom_projet):
    # Connect to GNS3 server
    gns3_server = Gns3Connector("http://127.0.0.1:3080")
    # Se connecter au projet
    project = Project(name=nom_projet, connector=gns3_server)
    project.get()

    for AS in data['autonomous_systems']:
        for router in AS['routers']:
            node = Node(project_id=project.project_id, name=router, node_type="dynamips", connector=gns3_server)
            node.start()
            AS["routers"][router]['gns3_id'] = node.node_id
""" 
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

 """

