import re
import sys
import conf_lib
import json
from logger import get_logger
from netaddr import IPAddress, IPNetwork
from json import JSONDecoder, JSONDecodeError


log = get_logger(path="/etc/artemis/automation_tools/logging.yaml", logger="auto_configuration")

# returns a generator which seperates the json objects in file
def decode_stacked(document, pos=0, decoder=JSONDecoder()):
    not_whitespace = re.compile(r'[^\s]')
    while True:
        match = not_whitespace.search(document, pos)
        if not match:
            return
        pos = match.start()

        try:
            obj, pos = decoder.raw_decode(document, pos)
        except JSONDecodeError as e:
            raise e
        yield obj


# returns a list with json objects, each object corresponds to bgp
# configuration of each router with which artemis is connected
def read_json_file(filename):
    try:
        json_data = []
        with open(filename, 'r') as json_file:
            json_stacked_data = json_file.read()
            for obj in decode_stacked(json_stacked_data):
                json_data.append(obj)
        return json_data
    except Exception as e:
        raise e


# returns a dictionary with prefixes
def create_prefixes_dict(json_data):
    counter = 0
    prefixes_dict = {}
    prefixes_set = set()
    for i in json_data:
        prefixes_list = i["prefixes"]
        for j in prefixes_list:
            mask = str(IPAddress(j["mask"]).netmask_bits())
            cidr = j["network"] + "/" + mask
            prefixes_set.add(cidr)

    for i in sorted(prefixes_set):
        prefixes_dict.update({i: "prefix_" + str(counter)})
        counter = counter + 1

    return prefixes_dict



# returns a dictionary with asn as keys
def create_asns_dict(json_data):
    asns = {}
    for i in json_data:
        # first insert origin as in list
        asns.update({int(i["origin_as"][0]["asn"]): ("AS_" + str(i["origin_as"][0]["asn"]), None)})

        # second insert peer_groups and neighbors asns
        neighbors_list = i["neighbors"]
        for j in neighbors_list:
            flag = 0
            for k in i["peer-groups"]:
                if j["interface_ip"] == k["interface_ip"] or j["interface_ip"] == k["asn"]:
                    # we found peer_group match for this ip
                    asns.update({int(j["asn"]): ("AS_" + str(j["asn"]), k["asn"])})
                    flag = 1
            if flag == 0:
                # we didnt found peer_group match for this ip
                asns.update({int(j["asn"]): ("AS_" + str(j["asn"]), None)})
    return asns



# update filter dictionary with new keys or values per key
def update_filter_dict(filter_dict, prefix_cidr, element, routemap_per_neighbor):

    # add or create prefix key in filter_dict
    # prefix as key and set as value with asns

    if element["peer-groups"] == []:
        # peer-groups did not defined
        for neighbor in element["neighbors"]:
            if routemap_per_neighbor["peerName_intIp"] == neighbor["interface_ip"]:
                if prefix_cidr not in filter_dict.keys():
                    filter_dict.update({prefix_cidr: {neighbor["asn"]}})
                else:
                    filter_dict[prefix_cidr].add(neighbor["asn"])
                break
    else:
        # peer-groups defined
        peer_check = 0
        for peer_group in element["peer-groups"]:
            if peer_group["asn"] == routemap_per_neighbor["peerName_intIp"] or \
                    peer_group["interface_ip"] == routemap_per_neighbor[
                "peerName_intIp"]:
                for neighbor in element["neighbors"]:
                    if peer_group["asn"] == neighbor["interface_ip"] or \
                            peer_group["interface_ip"] == neighbor[
                        "interface_ip"]:
                        # we found a peer-group match
                        peer_check = 1
                        if prefix_cidr not in filter_dict.keys():
                            filter_dict.update({prefix_cidr: {neighbor["asn"]}})
                        else:
                            filter_dict[prefix_cidr].add(neighbor["asn"])
                        break
            if peer_check == 1:
                break
        if peer_check == 0:
            # we dint found a peer-group match
            for neighbor in element["neighbors"]:
                if routemap_per_neighbor["peerName_intIp"] == neighbor[
                    "interface_ip"]:
                    if prefix_cidr not in filter_dict.keys():
                        filter_dict.update({prefix_cidr: {neighbor["asn"]}})
                    else:
                        filter_dict[prefix_cidr].add(neighbor["asn"])
                    break



# creates a dict with the following contents
# prefix N should not be announced to asn1 , ... ,asnN
# {
#  "prefix/mask 1": {asn1, asn2, ... ,asnN}
#  "prefix/mask 2": {asn1, asn2, ... ,asnN}
#   .............
#  "prefix/mask N": {asn1, asn2, ... ,asnN}
# }

def create_filter_dict(json_data):

    filter_dict = {}

    for element in json_data:
        for routemap_per_neighbor in element["routemaps_per_neighbor"]:
            if routemap_per_neighbor["direction"] == "out":
                for routemap_definition in element["routemaps_definitions"]:
                    if str(routemap_definition["routemap_name"]) == str(routemap_per_neighbor["routemap_name"]) and \
                            routemap_definition["action"] == "deny":
                        if routemap_definition["list_type"] == "prefix-list":
                            for prefix_list_name in routemap_definition["prefixl_acl_list"]:
                                for prefixlist_definition in element["prefixlists_definitions"]:
                                    if str(prefixlist_definition["prefixlist_name"]) == prefix_list_name and \
                                            prefixlist_definition["action"] == "permit":
                                        for prefix in element["prefixes"]:

                                            prefix_mask = str(IPAddress(prefix["mask"]).netmask_bits())
                                            prefix_cidr = prefix["network"] + "/" + prefix_mask
                                            definition_prefix_ip = str(IPNetwork(prefixlist_definition["prefix"]).ip)
                                            definition_prefix_mask = str(
                                                IPNetwork(prefixlist_definition["prefix"]).prefixlen)
                                            concat_prefix = prefix["network"] + "/" + definition_prefix_mask

                                            if prefixlist_definition["symbol1"] == "null":
                                                # 1st case exactly prefix match
                                                if prefixlist_definition["prefix"] == prefix_cidr:
                                                    update_filter_dict(filter_dict, prefix_cidr, element,
                                                                       routemap_per_neighbor)
                                                    break
                                            elif prefixlist_definition["symbol1"] == "le" and prefixlist_definition[
                                                "symbol2"] == "null":
                                                # 2nd case prefix le ...
                                                if str(IPNetwork(
                                                        concat_prefix).network) == definition_prefix_ip and int(
                                                    prefix_mask) >= int(definition_prefix_mask) and int(
                                                    prefix_mask) <= int(prefixlist_definition["value1"]):
                                                    update_filter_dict(filter_dict, prefix_cidr, element,
                                                                       routemap_per_neighbor)
                                            elif prefixlist_definition["symbol1"] == "ge" and prefixlist_definition[
                                                "symbol2"] == "null":
                                                # 3rd case prefix ge ...
                                                if str(IPNetwork(
                                                        concat_prefix).network) == definition_prefix_ip and int(
                                                    prefix_mask) >= int(prefixlist_definition["value1"]) and int(
                                                    prefix_mask) <= 32:
                                                    update_filter_dict(filter_dict, prefix_cidr, element,
                                                                       routemap_per_neighbor)
                                            elif prefixlist_definition["symbol1"] == "ge" and prefixlist_definition["symbol2"] == "le":
                                                # 4rth case prefix ge ... le ...
                                                if str(IPNetwork(
                                                        concat_prefix).network) == definition_prefix_ip and int(
                                                    prefix_mask) >= int(prefixlist_definition["value1"]) and int(
                                                    prefix_mask) <= int(prefixlist_definition["value2"]):
                                                    update_filter_dict(filter_dict, prefix_cidr, element,
                                                                       routemap_per_neighbor)


                        elif routemap_definition["list_type"] == "acl":
                            for acl_name in routemap_definition["prefixl_acl_list"]:
                                for acl_definition in element["acls_definitions"]:
                                    if str(acl_definition["acl_name"]) == acl_name and acl_definition[
                                        "action"] == "permit" and acl_definition["type"] in ["standard", "null"]:
                                        for prefix in element["prefixes"]:
                                            prefix_cidr = str(IPNetwork(prefix["network"] + "/" + prefix["mask"]))
                                            prefix_acl = str(
                                                IPNetwork(acl_definition["prefix"] + "/" + acl_definition["wildcard"]))

                                            if prefix_cidr == prefix_acl:
                                                # exactly prefix match
                                                update_filter_dict(filter_dict, prefix_cidr, element,
                                                                   routemap_per_neighbor)
                                                break

    return filter_dict


# returns a dictionary with rules for each prefix
def create_rules_dict(json_data):

    prefix_pols = {}
    for i in json_data:
        # process each json element (configuration file) in list
        origin_as_set = set()
        neighbors_set = set()
        prefixes_list = i["prefixes"]
        for prefix in prefixes_list:
            # for each prefix make a rule definition
            mask = str(IPAddress(prefix["mask"]).netmask_bits())
            cidr = prefix["network"] + "/" + mask
            for k in i["origin_as"]:  # here perform check for caveats and tips
                origin_as_set.add(
                    int(k["asn"]))  # here perform check for caveats and tips#here perform check for caveats and tips
            for k in i["neighbors"]:
                neighbors_set.add(int(k["asn"]))

            # Create rule definitions
            if cidr not in prefix_pols.keys():
                prefix_pols.update({cidr: [dict(origins=list(origin_as_set), neighbors=list(neighbors_set))]})
            else:
                prefix_pols[cidr].append(dict(origins=list(origin_as_set), neighbors=list(neighbors_set)))

    # check route-maps for selective prefix announcement
    # prefix N should not be announced to asn1 , ... ,asnN
    # {
    #  "prefix/mask 1": {asn1, asn2, ... ,asnN}
    #  "prefix/mask 2": {asn1, asn2, ... ,asnN}
    #   .............
    #  "prefix/mask N": {asn1, asn2, ... ,asnN}
    # }
    filter_dict = create_filter_dict(json_data)

    # update prefix_pols dictionary with the correct
    # neighbors per prefix. Apply difference beetween sets
    for prefix in filter_dict:
        for dict_item in prefix_pols[prefix]:
            dict_item["neighbors"] = list(set(dict_item["neighbors"]).difference(filter_dict[prefix]))

    return prefix_pols



def main():

    log.info("Starting config generator...")

    try:
        with open(sys.argv[1]) as json_file:
            admin_configs = json.load(json_file)
            json_data = read_json_file(admin_configs["bgp_results_path"])
            prefixes = create_prefixes_dict(json_data)
            asns = create_asns_dict(json_data)
            prefix_pols = create_rules_dict(json_data)
            conf_lib.generate_config_yml(prefixes, admin_configs["monitors"], asns, prefix_pols,
                                                admin_configs["mitigation_script_path"],
                                                admin_configs["artemis_config_file_path"])
    except Exception as e:
        log.error(e, exc_info=True)

    log.info("Stoping config generator...")


if __name__ == '__main__':
    main()
