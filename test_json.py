def adressage(networks):
    for network, routers in networks.items():
        base = network.split('::')[0]
        for router, _ in routers.items():
            if router.endswith('1'):
                routers[router] = base + '::1'
            elif router.endswith('2'):
                routers[router] = base + '::2'
    return networks

networks = {
    "2001:192:168:1::/126": {
        "R1": "GigabitEthernet1/0", 
        "R2": "GigabitEthernet1/0"
    },
    "2001:192:168:2::/126": {
        "R2": "GigabitEthernet2/0", 
        "R3": "GigabitEthernet2/0"
    }, 
    "2001:192:168:10::/126": {
        "R3": "GigabitEthernet3/0", 
        "R4": "GigabitEthernet3/0"
    }, 
    "2001:192:168:3::/126": {
        "R4": "GigabitEthernet1/0",
        "R5": "GigabitEthernet1/0"
    }, 
    "2001:192:168:4::/126":{
        "R5": "GigabitEthernet2/0", 
        "R6": "GigabitEthernet2/0"
    }
}

print(adressage(networks))
