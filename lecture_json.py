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
    for network, routers in data["networks"].items():
        base = network.split('::')[0]
        for i, router in enumerate(routers.keys()):
                routers[router]["ipv6"] = base + f'::{i+1}'

def data_interf(data): 
    for network, routers in data["networks"].items():
        router = routers.keys()
        for AS in data['autonomous_systems']:
            if (router[0] in AS["routers"].keys()) and (router[1] in AS["routers"].keys() in AS["routers"].keys()) :
                interface = {"interface_id": network[router[0]]["interface"], "link_to": router[1], "ip_address": network[router[0]]["ipv6"], "area": "0", "border_if": 0}
                AS["routers"][router[0]]["interfaces"].append(interface)
                interface = {"interface_id": network[router[1]]["interface"], "link_to": router[0], "ip_address": network[router[1]]["ipv6"], "area": "0", "border_if": 0}
                AS["routers"][router[1]]["interfaces"].append(interface)  
                break 
            elif router[0] in AS["routers"].keys():
                interface = {"interface_id": network[router[0]]["interface"], "link_to": router[1], "ip_address": network[router[0]]["ipv6"], "area": "0", "border_if": 1}
                AS["routers"][router[0]]["interfaces"].append(interface)                
            elif router[1] in AS["routers"].keys():
                interface = {"interface_id": network[router[1]]["interface"], "link_to": router[0], "ip_address": network[router[1]]["ipv6"], "area": "0", "border_if": 1}
                AS["routers"][router[1]]["interfaces"].append(interface) 

def initialisation(data):
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
  