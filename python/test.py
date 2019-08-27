from netaddr import IPNetwork, IPSet
import radix, json

elem = {
    "main_playbook_path": "/home/george/UOC-CSD/Diploma_Thesis/ansible/playbooks/main_playbook.yaml",
    "mitigation_playbook_path": "/root/mitigation_playbook.yaml",
    "ansible_hosts_file_path": "/root/hosts",
    "artemis_config_file_path": "/home/george/artemis/local_configs/backend/config.yaml",
    "config_generator_path": "/home/george/UOC-CSD/Diploma_Thesis/python/conf_generator.py",
    "bgp_results_path": "/root/results.json",
    "mitigation_script_path": "/root/mitigation_trigger.py",
    "parsers_paths": {
        "ios_parser": "/home/george/UOC-CSD/Diploma_Thesis/ansible/parsers/ios_parser.yaml"
    },
    "monitors": {
        "riperis": [""],
        "bgpstreamlive": ["routeviews", "ris"],
        "betabmp": ["betabmp"],
        "exabgp": {
            "ip": "exabgp",
            "port": 5000
        }
    },
    "tunnel_definitions": {
        "hijacked_prefix": {
            "130.10.0.0/20": {
                "myAS": {
                    "asn": 65001,
                    "router_id": "192.168.10.1",
                    "tunnel_interface_name": "Tunnel0",
                    "tunnel_interface_ip_address": "",
                    "tunnel_interface_ip_mask": "",
                    "tunnel_source_ip_address": "",
                    "tunnel_destination_ip_address": "",
                    "tunnel_mtu": "",
                    "tunnel_mss": ""
                },
                "helperAS": {
                    "asn": 65006,
                    "router_id": "192.168.100.2",
                    "tunnel_interface_name": "Tunnel0",
                    "tunnel_interface_ip_address": "",
                    "tunnel_interface_ip_mask": "",
                    "tunnel_source_ip_address": "",
                    "tunnel_destination_ip_address": "",
                    "tunnel_mtu": "",
                    "tunnel_mss": ""
                }
            }
        }
    }
}

hijacked_prefix = IPNetwork("130.10.0.0/24")

print(hijacked_prefix.prefixlen == 24)

prefixes_str = " pr_cidr=" + str(hijacked_prefix.cidr) + " pr_network=" + str(hijacked_prefix.ip) + " pr_netmask=" + str(hijacked_prefix.netmask) + " interface_name="

tunnel_json_key = ""
for prefix in list(elem["tunnel_definitions"]["hijacked_prefix"].keys()):
    if IPSet([prefix]).issuperset(IPSet([hijacked_prefix.cidr])):
        ## we found the tunnel configs for this prefix
        tunnel_json_key = prefix
        break
print(tunnel_json_key)

print(elem["tunnel_definitions"]["hijacked_prefix"][tunnel_json_key])

rtree = radix.Radix()
rnode = rtree.add("130.10.0.0/21")
rnode.data["data_list"] = "130.10.0.0/21"
rnode = rtree.add("130.10.0.0/23")
rnode.data["data_list"] = "130.10.0.0/23"
rnode = rtree.add("130.10.2.0/23")
rnode.data["data_list"] = "130.10.2.0/23"
rnode = rtree.add("130.10.0.0/24")
rnode.data["data_list"] = "130.10.0.0/24"
rnode = rtree.add("130.10.1.0/24")
rnode.data["data_list"] = "130.10.1.0/24"
rnode = rtree.add("130.10.3.0/24")
rnode.data["data_list"] = "130.10.3.0/24"


rnode = rtree.search_best("130.10.2.0")
print(rnode.data["data_list"])

prefix_pols = {}
origin_as_set = set()
origin_as_set.add(65001)
print(origin_as_set)
neighbors_set = set()
neighbors_set.add(65002)
neighbors_set.add(65010)

prefix_pols = {
    "10.0.0.0/24":[
        {
            "origins":[9012],
            "neighbors":[1234,5678]
        },
        {
            "origins": [65001],
            "neighbors": [65002, 65006]
        },
    ]
}

print(prefix_pols["10.0.0.0/24"])


prefixes_per_orig_neighb_group = {}
for prefix in sorted(prefix_pols):
    for dict_item in prefix_pols[prefix]:
        origin_asns = sorted(list(dict_item["origins"]))
        neighbors = sorted(list(dict_item["neighbors"]))
        key = (json.dumps(origin_asns), json.dumps(neighbors))
        if key not in prefixes_per_orig_neighb_group:
            prefixes_per_orig_neighb_group[key] = set()
            prefixes_per_orig_neighb_group[key].add(prefix)
