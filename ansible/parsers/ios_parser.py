import sys
import json
from ciscoconfparse import CiscoConfParse

def main():

    #write ios configurion into the tmp file router_config.txt
    #with open(sys.argv[1], 'w') as ios_config:
    #    ios_config.write(sys.argv[2])

    parse = CiscoConfParse(sys.argv[1], syntax='ios')

    #empty data dictionary
    data = {}

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
        if asn != "null":
            origin_as_list.append({"asn": asn})
    data["origin_as"] = origin_as_list

    neighbors_list = []
    # Iterate over matching bgp neighbors
    for obj in parse.find_objects(r"^router\s+bgp"):
        for child_obj in obj.children :  # Iterate over bgp children
            interface_ip = child_obj.re_match_typed(r"^\s+neighbor\s+(\S+)\s+remote-as\s+\d+", default="null")
            asn = child_obj.re_match_typed(r"^\s+neighbor\s+\S+\s+remote-as\s+(\d+)", default=-1, result_type=int)
            if interface_ip != "null" and asn != "null":
                neighbors_list.append({"interface_ip": interface_ip, "asn": asn})
    data["neighbors"] = neighbors_list

    peer_groups_list = []
    # Iterate over matching peer-groups
    for obj in parse.find_objects(r"^router\s+bgp"):
        for child_obj in obj.children:  # Iterate over bgp children
            interface_ip = child_obj.re_match_typed(r"^\s+neighbor\\s+(\S+)\s+peer-group\s+\w+", default="null")
            asn = child_obj.re_match_typed(r"^\s+neighbor\\s+(\S+)\s+peer-group\s+(\w+)", default="null")
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
    data["routemaps_definitions"] = routemaps_per_neighbor_list

    routemaps_definitions_list = []
    # Iterate over matching routemaps_definitions
    for obj in parse.find_objects(r"^route-map\s+\S+"):
        routemap_name = obj.re_match_typed(r"route-map\s+(\S+)\s+\S+\s+\d+", default="null")
        action = obj.re_match_typed(r"route-map\s+\S+\s+(\S+)\s+\d+", default="null")
        sequence_number = obj.re_match_typed(r"route-map\s+\S+\s+\S+\s+(\d+)", default="-1", result_type=int)
        for child_obj in obj.children:  # Iterate over routemaps_definitions children
            prefixlist = child_obj.re_match_typed(r"^\s+match\s+ip\s+address\s+(prefix-list)\s+.+", default="null")
            #in a cisco route map we can define prefixlists match or acl match statement not both
            if prefixlist == "prefix-list":
                list_type = "prefix-list"
                prefixl_acl_list = child_obj.re_match_typed(r"^\s+match\s+ip\s+address\s+prefix-list\s+(.+)", default="null")
                prefixl_acl_list = prefixl_acl_list.split(' ')
                routemaps_definitions_list.append({"action": action, "list_type": list_type, "prefixl_acl_list": prefixl_acl_list, "sequence_number": sequence_number, "routemap_name": routemap_name})
            elif prefixlist == "null":
                list_type = "acl"
                prefixl_acl_list = child_obj.re_match_typed(r"^\s+match\s+ip\s+address\s+(.+)", default="null")
                prefixl_acl_list = prefixl_acl_list.split(' ')
                routemaps_definitions_list.append({"action": action, "list_type": list_type, "prefixl_acl_list": prefixl_acl_list, "sequence_number": sequence_number, "routemap_name": routemap_name})
    data["routemaps_definitions"] = routemaps_definitions_list









    json_data = json.dumps(data)
    print(json_data)



if __name__ == '__main__':
    main()


