from netaddr import IPNetwork, IPSet, IPAddress
import radix, json, ruamel.yaml
from json_schema import json_schema


with open("/home/george/UOC-CSD/Diploma_Thesis/ansible/bgp_config_files/admin_configs.json") as json_file:
    admin_configs = json.load(json_file)

    prefix_keys_list = list(admin_configs["mitigation"]["configured_prefix"].keys())
    if not prefix_keys_list:
        # empty prefix_keys_list
        print("No prefixes have been added in configured_prefix dictionary !!!")
    else:
        # list prefix_keys_list has elements

        mitigation_json_schema = '{"netmask_threshold": "int:8:30","less_than_threshold": "regex:\\btunnel\\b|\\bdeaggregate\\b","equal_greater_than_threshold": "str","tunnel_definitions": {"helperAS": {"asn": "int","router_id": "str","tunnel_interface_name": "str","tunnel_interface_ip_address": "str","tunnel_interface_ip_mask": "str","tunnel_source_ip_address": "str","tunnel_source_ip_mask": "str","tunnel_destination_ip_address": "str","tunnel_destination_ip_mask": "str"}}}'

        # check only the json schema
        for prefix in admin_configs["mitigation"]["configured_prefix"]:
            if type(prefix) != str:
                print("Invalid configured prefix or wrong type !!!")
            else:
                mitigation_json_input = json.dumps(admin_configs["mitigation"]["configured_prefix"][prefix])
                if not json_schema.match(mitigation_json_input, mitigation_json_schema):
                    print("Mitigation json input schema not matched !!!")



mask = str(IPAddress("255.255.255.252").netmask_bits())
cidr = "192.168.200.2" + "/" + mask
prefix = str(IPNetwork(cidr).network) + "/" + mask
print(prefix)


rtree = radix.Radix()
rnode = rtree.add("10.0.0.0/8")
rnode = rtree.search_exact("10.1.3.0/22")

if rnode == None:
    print("george")