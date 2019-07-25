from netaddr import IPAddress, IPNetwork, IPSet

s1 = IPSet(['130.10.1.1/24'])
s2 = IPSet(['130.10.1.64/26'])


my_set = {'Geeks', 'for', 'for', 'geeks'}

my_list = list(my_set)

print(my_list)


print(type(s1.issuperset(s2)))
