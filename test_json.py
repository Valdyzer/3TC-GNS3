import json
import os
from lecture_json import lect



data = lect('adressage.json')

print(data)   

def adressage(networks):
    for network, routers in networks.items():
        base = network.split('::')[0]
        for router, _ in routers.items():
            if router.endswith('1'):
                routers[router] = base + '::1'
            elif router.endswith('2'):
                routers[router] = base + '::2'
    return networks


print(adressage(data))
