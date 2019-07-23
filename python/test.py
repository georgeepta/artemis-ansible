from netaddr import IPAddress, IPNetwork


ip = IPNetwork('130.10.1.1/24')

print(ip.network)