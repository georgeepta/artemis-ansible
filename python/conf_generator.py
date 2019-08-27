import re, sys, python.conf_lib, json
from netaddr import IPAddress
from json import JSONDecoder, JSONDecodeError


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

# returns a dictionary with prefixes
def create_prefixes_dict(json_data):
    counter=0
    prefixes_dict = {}
    prefixes_set = set()
    for i in json_data:
        prefixes_list = i["prefixes"]
        for j in prefixes_list:
            mask = str(IPAddress(j["mask"]).netmask_bits())
            cidr = j["network"] + "/" + mask
            prefixes_set.add(cidr)

    for i in sorted(prefixes_set):
        prefixes_dict.update({i: "prefix_"+str(counter)})
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
                if(j["interface_ip"] == k["interface_ip"]):
                    # we found peer_group match for this ip
                    asns.update({int(j["asn"]): ("AS_" + str(j["asn"]), k["asn"])})
                    flag = 1
            if flag == 0:
                # we didnt found peer_group match for this ip
                asns.update({int(j["asn"]): ("AS_" + str(j["asn"]), None)})
    return asns


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
            for k in i["origin_as"]: #here perform check for caveats and tips
                origin_as_set.add(int(k["asn"]))#here perform check for caveats and tips#here perform check for caveats and tips
            for k in i["neighbors"]:
                neighbors_set.add(int(k["asn"]))

            # Create rule definitions
            if cidr not in prefix_pols.keys():
                prefix_pols.update({cidr: [dict(origins=list(origin_as_set), neighbors=list(neighbors_set))]})
            else:
                prefix_pols[cidr].append(dict(origins=list(origin_as_set), neighbors=list(neighbors_set)))

    return prefix_pols


def main():
    with open(sys.argv[1]) as json_file:
        admin_configs = json.load(json_file)
        json_data = read_json_file(admin_configs["bgp_results_path"])
        print(json_data)
        prefixes = create_prefixes_dict(json_data)
        print(prefixes)
        asns = create_asns_dict(json_data)
        print(asns)
        prefix_pols = create_rules_dict(json_data)
        print(prefix_pols)
        python.conf_lib.generate_config_yml(prefixes, admin_configs["monitors"], asns, prefix_pols, admin_configs["mitigation_script_path"], admin_configs["artemis_config_file_path"])

if __name__ == '__main__':
    main()