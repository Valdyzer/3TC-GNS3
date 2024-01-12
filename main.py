from lecture_json import lect, initialisation
import fonctions as fct
import threading 
import time

if __name__ == '__main__' :

    data = lect('network.json')
    host = "127.0.0.1"
    initialisation(data)

    #Effacer configuration des routeurs (pour être sûr qu'on part dès zéro)
    threads_reset = []   

    for autonomous_system in data['autonomous_systems']:
        for router_name, router_data in autonomous_system['routers'].items():
            preset = threading.Thread(target=fct.reset_router, args=(host, router_data['port']))
            preset.start()
            threads_reset.append(preset)

    for thread in threads_reset: 
        thread.join()

    time.sleep(60)


    threads_config = []
    #paralelisation pour configurer chaque routeur
    for autonomous_system in data['autonomous_systems']:
        for router_name, router_data in autonomous_system['routers'].items():
            pconfig= threading.Thread(target=fct.configure_router, args=(host, router_data['port'], router_data['interfaces']))
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
                pRIP = threading.Thread(target=fct.configure_RIP,args=(host, port, interfaces))
                pRIP.start()
                threads_IGP.append(pRIP)
        # Regarde si le protocol de l'AS est OSPF
        elif AS['protocol'] == "OSPF":
            for router_name, router_info in AS['routers'].items():
                port = router_info['port']
                router_id = router_info['router_id']
                interfaces = router_info['interfaces']
                threading.Thread(target=fct.configure_OSPF, args=(host, port, router_id, interfaces))
                
                pOSPF = threading.Thread(target=fct.configure_OSPF, args=(host, port, router_id, interfaces))
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
            t_iBGP = threading.Thread(target=fct.configure_iBGP, args=(host, port, as_id, ipv6, neighbors, protocol, area))
            t_iBGP.start()
            threads_iBGP.append(t_iBGP)
    for thread in threads_iBGP:
        thread.join()


    for AS in data['autonomous_systems']:
        for router_info in AS["routers"].values:
            port = router_info['port']
            as_id = AS['as_id']
            router_id = router_info['router_id']
            t_eBGP = threading.Thread(target=fct.configure_eBGP, args=(host, port, as_id, router_id))
            t_eBGP.start()
            t_eBGP.join()  

            if router_info["BR"]==1: 
                neighbors = router_info['eBGP']['neighbors']
                networks = router_info['networks']
                t_eBGP_BR = threading.Thread(target=fct.configure_eBGP_BR, args=(host, port, as_id, neighbors, networks))
                t_eBGP_BR.start()
            