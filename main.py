from lecture_json import *
import fonctions as fct
import threading 
import time

if __name__ == '__main__' :

    data = init_json('Policies.json')  
    host = "127.0.0.1"
    nom_projet = "Policies"
    init_GNS3(data, nom_projet)

    print(data)

   # Efface les fichiers R.txt
    
    
    for AS in data['autonomous_systems']:
        for router_name in AS['routers'].keys():
            os.remove("Configs/" + router_name + ".txt")  

            
    # Effacer configuration des routeurs (pour être sûr qu'on part dès zéro)
    threads_reset = []   

    for autonomous_system in data['autonomous_systems']:
        for router_name, router_data in autonomous_system['routers'].items():
            preset = threading.Thread(target=fct.reset_router, args=(host, router_data['port'], "Configs/"+router_name+".txt"))
            preset.start()
            threads_reset.append(preset)

    for thread in threads_reset: 
        thread.join()

    print('Va reload stp')
    time.sleep(60)


    threads_config = []
    # Parallélisation pour configurer chaque routeur
    for autonomous_system in data['autonomous_systems']:
        for router_name, router_data in autonomous_system['routers'].items():
            pconfig= threading.Thread(target=fct.configure_router, args=(host, router_data['port'], router_data['interfaces'], "Configs/"+router_name+".txt"))
            pconfig.start()
            threads_config.append(pconfig)
    for thread in threads_config: 
        thread.join()

    threads_IGP = []     
    #Appel aux fonctions de configuration des protocoles de routage RIP et OSPF
    for AS in data['autonomous_systems']:
        # Regarde si le routing protocol est RIP
        if AS['protocol'] == "RIP":
            # Iteration pour chaque routeur dans l'AS
            for router_name, router_info in AS['routers'].items():
                port = router_info['port']
                interfaces = router_info['interfaces']
                pRIP = threading.Thread(target=fct.configure_RIP,args=(host, port, interfaces, "Configs/"+router_name+".txt"))
                pRIP.start()
                threads_IGP.append(pRIP)
        # Regarde si le protocol de l'AS est OSPF
        elif AS['protocol'] == "OSPF":
            for router_name, router_info in AS['routers'].items():
                port = router_info['port']
                router_id = router_info['router_id']
                interfaces = router_info['interfaces']
                pOSPF = threading.Thread(target=fct.configure_OSPF, args=(host, port, router_id, interfaces, "Configs/"+router_name+".txt"))
                pOSPF.start()
                threads_IGP.append(pOSPF)
                
    for thread in threads_IGP:
        thread.join()


# Configuration eBGP des routeurs
    threads_eBGP = []
    for AS in data['autonomous_systems']:
        for router_name, router_info in AS["routers"].items():
            port = router_info['port']
            as_id = AS['as_id']
            router_id = router_info['router_id']
            t_eBGP = threading.Thread(target=fct.configure_eBGP, args=(host, port, as_id, router_id, "Configs/"+router_name+".txt"))
            t_eBGP.start()
            t_eBGP.join()  
            
            #Routeurs de bordure
            if "eBGP" in router_info.keys():
                policies = AS["BGP Policies"]
                neighbors = router_info['eBGP']['neighbors']
                networks = router_info['eBGP']['networks']
                t_eBGP_BR = threading.Thread(target=fct.configure_eBGP_BR, args=(host, port, as_id, policies, neighbors, networks, "Configs/"+router_name+".txt"))
                t_eBGP_BR.start()
                threads_eBGP.append(t_eBGP_BR)
                
    for thread in threads_eBGP: 
        thread.join()            

# Configuration iBGP de tous les routeurs
    threads_iBGP = []
    for AS in data['autonomous_systems'] :
        for router_name, router_info in AS["routers"].items() :
            port = router_info['port']
            as_id = AS['as_id']
            ipv6 = router_info['iBGP']['ipv6 loopback']
            neighbors = router_info['iBGP']['neighbors']
            protocol = AS['protocol']
            area = router_info['interfaces'][0]['area']    
            t_iBGP = threading.Thread(target=fct.configure_iBGP, args=(host, port, as_id, ipv6, neighbors, protocol, area, "Configs/"+router_name+".txt"))
            t_iBGP.start()
            threads_iBGP.append(t_iBGP)
    for thread in threads_iBGP:
        thread.join()
        
    
# Ajout des politiques BGP
    threads_policies = []
    for AS in data['autonomous_systems'] :
        policies = AS["BGP Policies"]
        for router_name, router_info in AS["routers"].items() :
            port = router_info['port']
            as_id = AS['as_id']
            if AS['Policies activate'] == 1:
                if "eBGP" in router_info.keys():
                    neighbors = router_info['eBGP']['neighbors']
                    t_policies = threading.Thread(target=fct.policies, args=(host, port, as_id, neighbors, policies, "Configs/"+router_name+".txt"))
                    t_policies.start()
                    threads_policies.append(t_policies)
    for thread in threads_policies:
        thread.join()
    
    print("fin")