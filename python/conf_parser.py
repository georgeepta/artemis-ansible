import ast
import conf_lib
from netaddr import IPAddress



def create_asns_dict(filename):
    asns = {}
    fd = open(filename, "r")
    router_bgp_conf = ast.literal_eval(fd.read())[0]

    #Search for Asns
    for line in router_bgp_conf:
        if "router bgp" in line:
            my_asn = int(line.split(" ")[2])
            asns.update({my_asn: ("my_asns", None)})
        elif "neighbor" in line and "remote-as" in line:
            my_neighbor = int(line.split(" ")[4])
            asns.update({my_neighbor: ("my_neighbors", "my_neighbors")})

    fd.close()
    return asns


def create_prefixes_dict(filename):
    prefixes = {}
    fd = open(filename, "r")
    router_bgp_conf = ast.literal_eval(fd.read())[0]

    # Search for Prefixes
    for line in router_bgp_conf:
        if "network" in line:
            prefix = line.split(" ")[2]
            mask = str(IPAddress(line.split(" ")[4]).netmask_bits())
            cidr = prefix + "/" + mask
            prefixes.update({cidr: "my_prefix"})
    fd.close()
    return prefixes


def create_rules_dict(asns, prefixes):
    prefix_pols = {}

    #Make lists for prefix policies
    my_asn_list = []
    my_neighbor_list = []
    for key, value in asns.items():
        if value[0] == "my_asns":
            my_asn_list.append(key)
        elif value[0] == "my_neighbors":
            my_neighbor_list.append(key)

    #Create rule definitions
    for prefix in prefixes:
        prefix_pols.update({prefix: dict(origins = my_asn_list, neighbors = my_neighbor_list)})

    return prefix_pols

asns = create_asns_dict("router_data.txt")
prefixes = create_prefixes_dict("router_data.txt")
prefix_pols = create_rules_dict(asns, prefixes)
conf_lib.generate_config_yml(prefixes, asns, prefix_pols, "conf.yaml")

print(asns)
print(prefixes)
print(prefix_pols)
