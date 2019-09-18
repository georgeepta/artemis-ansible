#!/usr/bin/env python

import argparse
import json
import radix
import re
import subprocess
from json_schema import json_schema
from json import JSONDecoder, JSONDecodeError
from netaddr import IPAddress, IPNetwork, IPSet
from filelock import Timeout, FileLock


# returns a generator which seperates the json objects in file
def decode_stacked(document, pos=0, decoder=JSONDecoder()):
    NOT_WHITESPACE = re.compile(r'[^\s]')
    while True:
        match = NOT_WHITESPACE.search(document, pos)
        if not match:
            return
        pos = match.start()

        try:
            obj, pos = decoder.raw_decode(document, pos)
        except JSONDecodeError:
            # do something sensible if there's some error
            raise
        yield obj


# returns a list with json objects, each object corresponds to bgp
# configuration of each router with which artemis is connected
def read_json_file(filename):
    json_data = []
    with open(filename, 'r') as json_file:
        json_stacked_data = json_file.read()
        for obj in decode_stacked(json_stacked_data):
            json_data.append(obj)

    return json_data


# create radix-prefix tree with json data (config-file) of each router
def create_prefix_tree(json_data):
    # Create a new tree
    rtree = radix.Radix()

    # Adding a node returns a RadixNode object. You can create
    # arbitrary members in its 'data' dict to store your data.
    # Each node contains a prefix (which a router anounce)
    # as search value and as data --> (asn, bgp router-id, interface
    # name of super-prefix of that prefix) of router
    for i in json_data:
        prefixes_list = i["prefixes"]
        for j in prefixes_list:
            mask = str(IPAddress(j["mask"]).netmask_bits())
            cidr = j["network"] + "/" + mask

            # find out in which interface name this subprefix match
            interface_name = None
            interfaces_list = i["interfaces"]
            for k in interfaces_list:
                interface_mask = str(IPAddress(k["interface_mask"]).netmask_bits())
                interface_cidr = k["interface_ip"] + "/" + interface_mask
                s1 = IPSet([interface_cidr])
                s2 = IPSet([cidr])
                if s1.issuperset(s2) == True:
                    # we found the interface of the superprefix of current subprefix
                    interface_name = k["interface_name"]
                    break

            # search if prefix already exists in tree
            tmp_node = rtree.search_exact(cidr)
            if tmp_node == None:
                # prefix does not exist
                rnode = rtree.add(cidr)
                rnode.data["data_list"] = []
                rnode.data["data_list"].append(
                    (str(i["origin_as"][0]["asn"]), i["bgp_router_id"][0]["router_id"], interface_name))
            else:
                # prefix exist -> update list
                tmp_node.data["data_list"].append(
                    (str(i["origin_as"][0]["asn"]), i["bgp_router_id"][0]["router_id"], interface_name))

    return rtree


def prefix_deaggregation(hijacked_prefix):
    subnets = list(hijacked_prefix.subnet(hijacked_prefix.prefixlen + 1))
    prefix1_data = [str(subnets[0]), str(subnets[0].network), str(subnets[0].netmask)]
    prefix2_data = [str(subnets[1]), str(subnets[1].network), str(subnets[1].netmask)]
    return prefix1_data, prefix2_data


def isInputValid(rtree, json_data, admin_configs):
    prefix_keys_list = list(admin_configs["mitigation"]["configured_prefix"].keys())
    if not prefix_keys_list:
        # empty prefix_keys_list
        print("No prefixes have been added in configured_prefix dictionary !!!")
        return False
    else:
        # list prefix_keys_list has elements

        mitigation_json_schema = '{"netmask_threshold": "int","less_than_threshold": "str","equal_greater_than_threshold": "str","tunnel_definitions": {"helperAS": {"asn": "int","router_id": "str","tunnel_interface_name": "str","tunnel_interface_ip_address": "str","tunnel_interface_ip_mask": "str","tunnel_source_ip_address": "str","tunnel_source_ip_mask": "str","tunnel_destination_ip_address": "str","tunnel_destination_ip_mask": "str"}}}'

        # check only the json schema
        ipv4_cidr_regex = re.compile(
            r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$")
        for prefix in admin_configs["mitigation"]["configured_prefix"]:
            if type(prefix) != str or not ipv4_cidr_regex.match(prefix):
                print("Invalid configured prefix string-cidr format !!!")
                return False
            else:
                mitigation_json_input = json.dumps(admin_configs["mitigation"]["configured_prefix"][prefix])
                if not json_schema.match(mitigation_json_input, mitigation_json_schema):
                    print("Mitigation json input schema not matched !!!")
                    return False

        # check the values-fields
        for prefix in admin_configs["mitigation"]["configured_prefix"]:
            netmask_threshold = int(admin_configs["mitigation"]["configured_prefix"][prefix]["netmask_threshold"])
            less_than_threshold = admin_configs["mitigation"]["configured_prefix"][prefix]["less_than_threshold"]
            equal_greater_than_threshold = admin_configs["mitigation"]["configured_prefix"][prefix][
                "equal_greater_than_threshold"]
            asn = int(admin_configs["mitigation"]["configured_prefix"][prefix]["tunnel_definitions"]["helperAS"]["asn"])
            router_id = admin_configs["mitigation"]["configured_prefix"][prefix]["tunnel_definitions"]["helperAS"][
                "router_id"]
            tunnel_interface_name = \
                admin_configs["mitigation"]["configured_prefix"][prefix]["tunnel_definitions"]["helperAS"][
                    "tunnel_interface_name"]
            tunnel_interface_ip_address = \
                admin_configs["mitigation"]["configured_prefix"][prefix]["tunnel_definitions"]["helperAS"][
                    "tunnel_interface_ip_address"]
            tunnel_interface_ip_mask = \
                admin_configs["mitigation"]["configured_prefix"][prefix]["tunnel_definitions"]["helperAS"][
                    "tunnel_interface_ip_mask"]
            tunnel_source_ip_address = \
                admin_configs["mitigation"]["configured_prefix"][prefix]["tunnel_definitions"]["helperAS"][
                    "tunnel_source_ip_address"]
            tunnel_source_ip_mask = \
                admin_configs["mitigation"]["configured_prefix"][prefix]["tunnel_definitions"]["helperAS"][
                    "tunnel_source_ip_mask"]
            tunnel_destination_ip_address = \
                admin_configs["mitigation"]["configured_prefix"][prefix]["tunnel_definitions"]["helperAS"][
                    "tunnel_destination_ip_address"]
            tunnel_destination_ip_mask = \
                admin_configs["mitigation"]["configured_prefix"][prefix]["tunnel_definitions"]["helperAS"][
                    "tunnel_destination_ip_mask"]

            # check prefix value
            node = rtree.search_exact(prefix)
            if node == None:
                print("Invalid configured prefix !!!")
                return False

            # check netmask_threshold, less_than_threshold, equal_greater_than_threshold values
            if netmask_threshold < 8 or netmask_threshold > 30 or less_than_threshold not in ["deaggregate", "tunnel",
                                                                                              "deaggregate+tunnel",
                                                                                              "manual"] or equal_greater_than_threshold not in [
                "tunnel", "manual"]:
                print("netmask_threshold or less_than_threshold or equal_greater_than_threshold field is invalid")
                return False

            # check asn, router_id, tunnel_interface_name,
            # tunnel_interface_ip_address, tunnel_interface_ip_mask values
            check_flag = 0
            for item in json_data:
                if item["origin_as"][0]["asn"] == asn and item["bgp_router_id"][0]["router_id"] == router_id:
                    for element in item["interfaces"]:
                        if element["interface_name"] == tunnel_interface_name and element[
                            "interface_ip"] == tunnel_interface_ip_address and element[
                            "interface_mask"] == tunnel_interface_ip_mask:
                            check_flag = 1
                            break
                    if check_flag == 1:
                        # fields were found
                        break
            if check_flag == 0:
                print(
                    "asn or router_id or tunnel_interface_name or tunnel_interface_ip_address or tunnel_interface_ip_mask field is invalid")
                return False

            # check tunnel_source_ip_address, tunnel_source_ip_mask fields
            ipv4_regex = re.compile(
                r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$")
            if ipv4_regex.match(tunnel_source_ip_address) and ipv4_regex.match(tunnel_source_ip_mask):
                mask = str(IPAddress(tunnel_source_ip_mask).netmask_bits())
                cidr = tunnel_source_ip_address + "/" + mask
                prefix = str(IPNetwork(cidr).network) + "/" + mask
                node = rtree.search_exact(prefix)
                if node != None:
                    print("Physical source interface of tunnel must not has hijacked ip !!!")
                    return False
                else:
                    check_flag = 0
                    for item in json_data:
                        for element in item["interfaces"]:
                            if element["interface_ip"] == tunnel_source_ip_address and element[
                                "interface_mask"] == tunnel_source_ip_mask:
                                check_flag = 1
                                break
                        if check_flag == 1:
                            # fields were found
                            break
                    if check_flag == 0:
                        print("Invalid physical tunnnel source interface !!!")
            else:
                print("Invalid physical tunnel_source_ip_address or tunnel_source_ip_mask format !!!")
                return False

            # check tunnel_destination_ip_address, tunnel_destination_ip_mask fields
            if ipv4_regex.match(tunnel_destination_ip_address) and ipv4_regex.match(tunnel_destination_ip_mask):
                mask = str(IPAddress(tunnel_destination_ip_mask).netmask_bits())
                cidr = tunnel_destination_ip_address + "/" + mask
                prefix = str(IPNetwork(cidr).network) + "/" + mask
                node = rtree.search_exact(prefix)
                if node != None:
                    print("Physical destination interface of tunnel must not has hijacked ip !!!")
                    return False
                else:
                    check_flag = 0
                    for item in json_data:
                        for element in item["interfaces"]:
                            if element["interface_ip"] == tunnel_destination_ip_address and element[
                                "interface_mask"] == tunnel_destination_ip_mask:
                                check_flag = 1
                                break
                        if check_flag == 1:
                            # fields were found
                            break
                    if check_flag == 0:
                        print("Invalid physical tunnnel destination interface !!!")

            else:
                print("Invalid physical tunnel_destination_ip_address or tunnel_destination_ip_mask format !!!")
                return False

    return True


def deaggregation_technique(hijacked_prefix, rtree, admin_configs):
    ##perform prefix-deaggregation technique

    prefix1_data, prefix2_data = prefix_deaggregation(hijacked_prefix)

    # Best-match search will return the longest matching prefix
    # that contains the search term (routing-style lookup)
    rnode = rtree.search_best(str(hijacked_prefix.ip))

    # call mitigation playbook for each
    # tuple in longest prefix match node
    for ttuple in rnode.data["data_list"]:
        host = "target=" + ttuple[0] + ":&" + ttuple[0] + "_" + ttuple[1] + " asn=" + ttuple[0]
        prefixes_str = " pr1_cidr=" + prefix1_data[0] + " pr1_network=" + prefix1_data[1] + " pr1_netmask=" + \
                       prefix1_data[2] + " pr2_cidr=" + prefix2_data[0] + " pr2_network=" + prefix2_data[
                           1] + " pr2_netmask=" + prefix2_data[2] + " interface_name=" + ttuple[2]
        cla = host + prefixes_str
        arg = "ansible-playbook -i " + admin_configs["ansible_hosts_file_path"] + " " + admin_configs[
            "mitigation_playbook_path"] + " --extra-vars " + "\"" + cla + "\""
        subprocess.call(arg, shell=True)


def tunnel_technique(hijacked_prefix, json_prefix_key, rtree, admin_configs):
    ##perform tunnel technique

    # Best-match search will return the longest matching prefix
    # that contains the search term (routing-style lookup)
    rnode = rtree.search_best(str(hijacked_prefix.ip))

    # call mitigation playbook for each
    # tuple in longest prefix match node
    for ttuple in rnode.data["data_list"]:
        host = "target=" + ttuple[0] + ":&" + ttuple[0] + "_" + ttuple[1] + " asn=" + ttuple[0]
        prefixes_str = " pr_cidr=" + str(hijacked_prefix.cidr) + " pr_network=" + str(
            hijacked_prefix.ip) + " pr_netmask=" + str(hijacked_prefix.netmask) + " interface_name=" + ttuple[2]
        cla = host + prefixes_str
        arg = "ansible-playbook -i " + admin_configs["ansible_hosts_file_path"] + " " + admin_configs[
            "tunnel_mitigation_playbook_path"] + " --extra-vars " + "\"" + cla + "\""
        subprocess.call(arg, shell=True)

    # call tunnel_mitigation_playbook for helper as
    # to redirect traffic into the tunnel
    prefix_key = admin_configs["mitigation"]["configured_prefix"][json_prefix_key]["tunnel_definitions"]

    host = "target=" + str(prefix_key["helperAS"]["asn"]) + ":&" + str(prefix_key["helperAS"]["asn"]) + "_" + \
           prefix_key["helperAS"][
               "router_id"] + " asn=" + str(prefix_key["helperAS"]["asn"])
    prefixes_str = " pr_cidr=" + str(hijacked_prefix.cidr) + " pr_network=" + str(
        hijacked_prefix.ip) + " pr_netmask=" + str(hijacked_prefix.netmask) + " interface_name=" + \
                   str(prefix_key["helperAS"]["tunnel_interface_name"])
    cla = host + prefixes_str
    arg = "ansible-playbook -i " + admin_configs["ansible_hosts_file_path"] + " " + admin_configs[
        "tunnel_mitigation_playbook_path"] + " --extra-vars " + "\"" + cla + "\""
    subprocess.call(arg, shell=True)


def mitigate_prefix(hijack_json, json_data, admin_configs):
    hijacked_prefix = IPNetwork(json.loads(hijack_json)["prefix"])
    rtree = create_prefix_tree(json_data)

    if not isInputValid(rtree, json_data, admin_configs):
        print("Invalid json input !!!")
        return False
    else:
        json_prefix_key = ""
        for prefix in list(admin_configs["mitigation"]["configured_prefix"].keys()):
            if IPSet([prefix]).issuperset(IPSet([hijacked_prefix.cidr])):
                ## we found the tunnel configs for this prefix
                json_prefix_key = prefix
                break

        if json_prefix_key == "":
            # better call the logger from utils
            # from utils import get_logger
            # log = get_logger() , log.info("...")
            # or you can apply a default mitigation method
            print("Mitigation definition for this prefix not found")
            return False
        else:
            # perform user mitigation technique
            netmask_threshold = admin_configs["mitigation"]["configured_prefix"][json_prefix_key]["netmask_threshold"]
            less_than_threshold = admin_configs["mitigation"]["configured_prefix"][json_prefix_key][
                "less_than_threshold"]
            equal_greater_than_threshold = admin_configs["mitigation"]["configured_prefix"][json_prefix_key][
                "equal_greater_than_threshold"]

            if hijacked_prefix.prefixlen < netmask_threshold:
                if less_than_threshold == "deaggregate":
                    # perform prefix-deaggregation technique
                    deaggregation_technique(hijacked_prefix, rtree, admin_configs)
                elif less_than_threshold == "tunnel":
                    # perform tunnel technique
                    tunnel_technique(hijacked_prefix, json_prefix_key, rtree, admin_configs)
                elif less_than_threshold == "deaggregate+tunnel":
                    # perform deaggregation and tunnel technique
                    deaggregation_technique(hijacked_prefix, rtree, admin_configs)
                    tunnel_technique(hijacked_prefix, json_prefix_key, rtree, admin_configs)
                else:
                    # manual
                    print("Manual mitigiation !!!")
            else:
                if equal_greater_than_threshold == "tunnel":
                    # perform tunnel technique
                    tunnel_technique(hijacked_prefix, json_prefix_key, rtree, admin_configs)
                else:
                    # manual
                    print("Manual mitigiation !!!")


def main():
    parser = argparse.ArgumentParser(description="ARTEMIS mitigation")
    parser.add_argument("-i", "--info_hijack", dest="info_hijack", type=str, help="hijack event information",
                        required=True)
    hijack_arg = parser.parse_args()

    # creation (if not exists) of file result.txt.lock in shared /tmp
    # directory in order to implement lock-unlock technique to results.json
    with open('/tmp/result.json.lock', 'w'):
        pass

    # we need this lock to elimininate concurrent access to results.json
    # from other processes (auto mitigation mechanism) at the same time
    lock = FileLock("/tmp/result.json.lock")
    with lock.acquire(timeout=-1, poll_intervall=0.05):
        # If timeout <= 0, there is no timeout and this
        # method will block until the lock could be acquired
        with open("/root/admin_configs.json") as json_file:
            admin_configs = json.load(json_file)
            json_data = read_json_file(admin_configs["bgp_results_path"])
            mitigate_prefix(hijack_arg.info_hijack, json_data, admin_configs)


if __name__ == '__main__':
    main()
