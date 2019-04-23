from ciscoconfparse import CiscoConfParse

parse = CiscoConfParse("real.txt")

def print_sections(text):
    serial_objs = parse.find_objects(text)
    obs = []
    for x in  serial_objs:
        obs.append(x.text)
    print(obs)


print_sections("^router bgp")
print_sections("neighbor")
print_sections("^ip prefix-list")
print_sections("^route-map")
print_sections("^access-list")
