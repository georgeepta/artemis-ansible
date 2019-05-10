import sys, json, conf_lib
from netaddr import IPAddress

def create_prefixes_dict(jdata):
    prefixes = {}
    counter=0
    for key in jdata['prefixes']:
        cidr = str(key['network']) + "/" + str(IPAddress(key['mask']).netmask_bits())
        prefixes.update({cidr: "prefix_"+str(counter)})
        counter = counter + 1
    return prefixes




jdata = json.loads(sys.argv[1])
prefixes = create_prefixes_dict(jdata)
asns = {}
prefix_pols = {}
conf_lib.generate_config_yml({'10.0.0.0/24': 'my_prefix'},{
  1234: ('AS_1234', 'PEER_GROUP_X'),
  5678: ('AS_5678', 'PEER_GROUP_X'),
  9012: ('AS_9012', None)
},{'10.0.0.0/24': {'origins': [9012],'neighbors': [1234, 5678]}}, "conf.yaml")


f = open("file.txt", "w+")
f.write(str(prefixes))
f.close()
