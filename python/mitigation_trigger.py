#!/usr/bin/env python

import re, sys, argparse, radix, json, subprocess
from json import JSONDecoder, JSONDecodeError
from netaddr import IPAddress, IPNetwork



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


#create radix-prefix tree with json data (config-file) of each router
def create_prefix_tree(json_data):

   # Create a new tree
   rtree = radix.Radix()

   #Adding a node returns a RadixNode object. You can create
   #arbitrary members in its 'data' dict to store your data.
   #Each node contains a prefix (which a router anounce)
   #as search value and as data asn, bgp router-id of router
   for i in json_data:
      prefixes_list = i["prefixes"]
      for j in prefixes_list:
         mask = str(IPAddress(j["mask"]).netmask_bits())
         cidr = j["network"] + "/" + mask
         #search if prefix already exists in tree
         tmp_node = rtree.search_exact(cidr)
         if tmp_node == None :
             #prefix does not exist
             rnode = rtree.add(cidr)
             rnode.data["data_list"] = []
             rnode.data["data_list"].append((str(i["origin_as"][0]["asn"]), i["bgp_router_id"][0]["router_id"]))
         else:
             #prefix exist -> update list
             rnode.data["data_list"].append((str(i["origin_as"][0]["asn"]), i["bgp_router_id"][0]["router_id"]))

   return rtree


def prefix_deaggregation(hijacked_prefix):

    subnets =  list(hijacked_prefix.subnet(hijacked_prefix.prefixlen+1))
    prefix1_data = [str(subnets[0]), str(subnets[0].network), str(subnets[0].netmask)]
    prefix2_data = [str(subnets[1]), str(subnets[1].network), str(subnets[1].netmask)]
    return prefix1_data, prefix2_data


def mitigate_prefix(hijack_json, json_data, admin_configs):

    hijacked_prefix = IPNetwork(json.loads(hijack_json)["prefix"])
    rtree = create_prefix_tree(json_data)
    prefix1_data, prefix2_data = prefix_deaggregation(hijacked_prefix)

    # Best-match search will return the longest matching prefix
    # that contains the search term (routing-style lookup)
    rnode = rtree.search_best(str(hijacked_prefix.ip))

    #call mitigation playbook for each
    #tuple in longest prefix match node
    for tuple in rnode.data["data_list"]:
        host = "target="+tuple[0]+":&"+tuple[1]+" asn="+tuple[0]
        prefixes_str = " pr1_cidr="+prefix1_data[0]+" pr1_network="+prefix1_data[1]+" pr1_netmask="+prefix1_data[2]+" pr2_cidr="+prefix2_data[0]+" pr2_network="+prefix2_data[1]+" pr2_netmask="+prefix2_data[2]
        cla = host + prefixes_str
        subprocess.call(["sudo",
                         "ansible-playbook",
                         "-i",
                         admin_configs["ansible_hosts_file_path"],
                         admin_configs["mitigation_playbook_path"],
                         "--extra-vars",
                         cla
                         ])


def main():

   parser = argparse.ArgumentParser(description="test ARTEMIS mitigation")
   parser.add_argument("-i", "--info_hijack", dest="info_hijack", type=str, help="hijack event information", required=True)
   #parser.add_argument("-c", "--admin_config_path", dest="admin_config_path", type=str, help="path of admin_configs.json", required=True)
   hijack_arg = parser.parse_args()

   # write the information to a file (example script)
   # with open('/root/mit.txt', 'w') as f:
   #   f.write(args.info_hijack)
   print(hijack_arg.info_hijack)

   with open("/home/george/UOC-CSD/Diploma_Thesis/ansible/bgp_config_files/admin_configs.json") as json_file:
      admin_configs = json.load(json_file)
      json_data = read_json_file(admin_configs["bgp_results_path"])
      mitigate_prefix(hijack_arg.info_hijack, json_data, admin_configs)


if __name__ == '__main__':
    main()