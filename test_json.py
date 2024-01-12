from lecture_json import lect

data = lect("adressage.json")

def adressage(networks):
    for network, routers in networks.items():
        base = network.split('::')[0]
        for i, router in enumerate(routers.keys()):
                print(i, router)
                routers[router] = base + f'::{i+1}'
    
    return networks

print(adressage(data))
