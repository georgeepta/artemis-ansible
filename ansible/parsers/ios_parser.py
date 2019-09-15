import sys
import json
from ciscoconfparse import CiscoConfParse

def main():

    #write ios configurion into the tmp file router_config.txt
    with open(sys.argv[1], 'w') as ios_config:
        ios_config.write(sys.argv[2])

    parse = CiscoConfParse(sys.argv[1], syntax='ios')

    #empty data dictionary
    data = {}

    #tag this json as ios config
    data["router_ios"] = {"name": "cisco_ios"}


    prefixes_list = []
    # Iterate over matching network commands
    for obj in parse.find_objects(r"^router\s+bgp"):
        for child_obj in obj.children :  # Iterate over bgp children
            network = child_obj.re_match_typed(r"^\s+network\s+(\S+)\s+mask\s+\S+", default="null")
            mask = child_obj.re_match_typed(r"^\s+network\s+\S+\s+mask\s+(\S+)", default="null")
            if network != "null" and mask != "null":
                prefixes_list.append({"mask": mask, "network": network})
    data["prefixes"] = prefixes_list


    origin_as_list = []
    # Iterate over matching origin_as
    for obj in parse.find_objects(r"^router\s+bgp"):
        asn = obj.re_match_typed(r"^router\s+bgp\s+(\d+)", default="-1", result_type=int)
        if asn != -1:
            origin_as_list.append({"asn": asn})
    data["origin_as"] = origin_as_list


    neighbors_list = []
    # Iterate over matching bgp neighbors
    for obj in parse.find_objects(r"^router\s+bgp"):
        for child_obj in obj.children :  # Iterate over bgp children
            interface_ip = child_obj.re_match_typed(r"^\s+neighbor\s+(\S+)\s+remote-as\s+\d+", default="null")
            asn = child_obj.re_match_typed(r"^\s+neighbor\s+\S+\s+remote-as\s+(\d+)", default=-1, result_type=int)
            if interface_ip != "null" and asn != -1:
                neighbors_list.append({"interface_ip": interface_ip, "asn": asn})
    data["neighbors"] = neighbors_list


    peer_groups_list = []
    # Iterate over matching peer-groups
    for obj in parse.find_objects(r"^router\s+bgp"):
        for child_obj in obj.children:  # Iterate over bgp children
            interface_ip = child_obj.re_match_typed(r"^\s+neighbor\s+(\S+)\s+peer-group\s+\w+", default="null")
            asn = child_obj.re_match_typed(r"^\s+neighbor\s+\S+\s+peer-group\s+(\w+)", default="null")
            if interface_ip != "null" and asn != "null":
                peer_groups_list.append({"interface_ip": interface_ip, "asn": asn})
    data["peer-groups"] = peer_groups_list


    bgp_router_id_list = []
    # Iterate over matching bgp_router_id
    for obj in parse.find_objects(r"^router\s+bgp"):
        for child_obj in obj.children:  # Iterate over bgp children
            router_id = child_obj.re_match_typed(r"^\s+bgp\s+router-id\s+(\S+)", default="null")
            if router_id != "null":
                bgp_router_id_list.append({"router_id": router_id})
    data["bgp_router_id"] = bgp_router_id_list


    interfaces_list = []
    # Iterate over matching interfaces
    for obj in parse.find_objects(r"^interface\s+\S+"):
        interface_name = obj.re_match_typed(r"^interface\s+(\S+)", default="null")
        for child_obj in obj.children:  # Iterate over interface children
            interface_ip = child_obj.re_match_typed(r"^\s+ip\s+address\s+(\S+)\s+\S+", default="null")
            interface_mask = child_obj.re_match_typed(r"^\s+ip\s+address\s+\S+\s+(\S+)", default="null")
            if interface_ip != "null" and interface_mask != "null":
                interfaces_list.append({"interface_ip": interface_ip, "interface_mask": interface_mask, "interface_name": interface_name})
    data["interfaces"] = interfaces_list


    routemaps_per_neighbor_list = []
    # Iterate over matching routemaps_per_neighbor
    for obj in parse.find_objects(r"^router\s+bgp"):
        for child_obj in obj.children:  # Iterate over bgp children
            peerName_intIp = child_obj.re_match_typed(r"^\s+neighbor\s+(\S+)\s+route-map\s+\S+\s+\S+", default="null")
            routemap_name = child_obj.re_match_typed(r"^\s+neighbor\s+\S+\s+route-map\s+(\S+)\s+\S+", default="null")
            direction = child_obj.re_match_typed(r"^\s+neighbor\s+\S+\s+route-map\s+\S+\s+(\S+)", default="null")
            if peerName_intIp != "null" and routemap_name != "null" and direction != "null":
                routemaps_per_neighbor_list.append({"direction": direction, "routemap_name": routemap_name, "peerName_intIp": peerName_intIp})
    data["routemaps_per_neighbor"] = routemaps_per_neighbor_list


    routemaps_definitions_list = []
    # Iterate over matching routemaps_definitions
    for obj in parse.find_objects(r"^route-map\s+\S+"):
        routemap_name = obj.re_match_typed(r"route-map\s+(\S+)\s+\S+\s+\d+", default="null")
        action = obj.re_match_typed(r"route-map\s+\S+\s+(\S+)\s+\d+", default="null")
        sequence_number = obj.re_match_typed(r"route-map\s+\S+\s+\S+\s+(\d+)", default="-1", result_type=int)
        if sequence_number == -1: sequence_number = "null"
        # in a cisco route map we can define prefixlists match or acl match statement not both
        for child_obj in obj.children:  # Iterate over routemaps_definitions children
            list_type = child_obj.re_match_typed(r"^\s+match\s+ip\s+address\s+((prefix-list)\s+)*.+", default="null", group=2)
            prefixl_acl_list = child_obj.re_match_typed(r"^\s+match\s+ip\s+address\s+(prefix-list\s+)*(.+)", default="null", group=2)
            if list_type != "null" and prefixl_acl_list != "null":
                list_type = "prefix-list"
                prefixl_acl_list = prefixl_acl_list.split(' ')
                routemaps_definitions_list.append({"action": action, "list_type": list_type, "prefixl_acl_list": prefixl_acl_list, "sequence_number": sequence_number, "routemap_name": routemap_name})
            elif list_type == "null" and prefixl_acl_list != "null":
                list_type = "acl"
                prefixl_acl_list = prefixl_acl_list.split(' ')
                routemaps_definitions_list.append({"action": action, "list_type": list_type, "prefixl_acl_list": prefixl_acl_list, "sequence_number": sequence_number, "routemap_name": routemap_name})
    data["routemaps_definitions"] = routemaps_definitions_list


    prefixlists_definitions_list=[]
    # Iterate over matching prefixlists_definitions
    for obj in parse.find_objects(r"^ip\s+prefix-list"):
        prefixlist_name = obj.re_match_typed(r"^ip\s+prefix-list\s+(\S+)(\s+seq\s+\d+)*\s+\S+\s+\S+(\s+\S+\s+\d+(\s+\S+\s+\d+)*)*", default="null")
        sequence_number = obj.re_match_typed(r"^ip\s+prefix-list\s+\S+(\s+seq\s+(\d+))*\s+\S+\s+\S+(\s+\S+\s+\d+(\s+\S+\s+\d+)*)*", default=-1, result_type=int, group=2)
        action = obj.re_match_typed(r"^ip\s+prefix-list\s+\S+(\s+seq\s+\d+)*\s+(\S+)\s+\S+(\s+\S+\s+\d+(\s+\S+\s+\d+)*)*", default="null", group=2)
        prefix = obj.re_match_typed(r"ip\s+prefix-list\s+\S+(\s+seq\s+\d+)*\s+\S+\s+(\S+)(\s+\S+\s+\d+(\s+\S+\s+\d+)*)*", default="null", group=2)
        symbol1 = obj.re_match_typed(r"^ip\s+prefix-list\s+\S+(\s+seq\s+\d+)*\s+\S+\s+\S+(\s+(\S+)\s+\d+(\s+\S+\s+\d+)*)*", default="null", group=3)
        value1 = obj.re_match_typed(r"^ip\s+prefix-list\s+\S+(\s+seq\s+\d+)*\s+\S+\s+\S+(\s+\S+\s+(\d+)(\s+\S+\s+\d+)*)*", default=-1, result_type=int, group=3)
        symbol2 = obj.re_match_typed(r"^ip\s+prefix-list\s+\S+(\s+seq\s+\d+)*\s+\S+\s+\S+(\s+\S+\s+\d+(\s+(\S+)\s+\d+)*)*", default="null", group=4)
        value2 = obj.re_match_typed(r"^ip\s+prefix-list\s+\S+(\s+seq\s+\d+)*\s+\S+\s+\S+(\s+\S+\s+\d+(\s+\S+\s+(\d+))*)*", default=-1, result_type=int, group=4)
        if sequence_number == -1: sequence_number = "null"
        if value1 == -1: value1 = "null"
        if value2 == -1: value2 = "null"
        prefixlists_definitions_list.append({"prefixlist_name": prefixlist_name, "prefix": prefix, "value2": value2, "value1": value1, "symbol2": symbol2, "action": action, "symbol1": symbol1, "sequence_number": sequence_number})
    data["prefixlists_definitions"] = prefixlists_definitions_list


    acls_definitions_list = []
    # Iterate over matching acls_definitions (numbered and standard)

    #numbered
    for obj in parse.find_objects(r"^access-list\s+"):
        type = "null"
        acl_name = obj.re_match_typed(r"^access-list\s+(\d+)\s+\S+\s+\S+\s+\S+", default=-1, result_type=int)
        action = obj.re_match_typed(r"^access-list\s+\d+\s+(\S+)\s+\S+\s+\S+", default="null")
        prefix = obj.re_match_typed(r"^access-list\s+\d+\s+\S+\s+(\S+)\s+\S+", default="null")
        wildcard = obj.re_match_typed(r"^access-list\s+\d+\s+\S+\s+\S+\s+(\S+)", default="null")
        acls_definitions_list.append({"action": action, "prefix": prefix, "type": type, "wildcard": wildcard, "acl_name": acl_name})

    #standard
    for obj in parse.find_objects(r"^ip\s+access-list\s+standard\s+"):
        type = "standard"
        acl_name = obj.re_match_typed(r"^ip\s+access-list\s+standard\s+(\S+)", default="null")
        for child_obj in obj.children:  # Iterate over standard acl children
            action = child_obj.re_match_typed(r"^\s+(\S+)\s+\S+\s+\S+", default="null")
            prefix = child_obj.re_match_typed(r"^\s+\S+\s+(\S+)\s+\S+", default="null")
            wildcard = child_obj.re_match_typed(r"^\s+\S+\s+\S+\s+(\S+)", default="null")
            acls_definitions_list.append({"action": action, "prefix": prefix, "type": type, "wildcard": wildcard, "acl_name": acl_name})
    data["acls_definitions"] = acls_definitions_list


    json_data = json.dumps(data)
    print(json_data)

    with open(sys.argv[3], 'a') as results:
        results.write(json_data)

if __name__ == '__main__':
    main()


