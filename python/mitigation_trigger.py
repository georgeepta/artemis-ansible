#!/usr/bin/env python

import argparse

parser = argparse.ArgumentParser(description="test ARTEMIS mitigation")
parser.add_argument("-i", "--info_hijack", dest="info_hijack", type=str, help="hijack event information",        required=True)
args = parser.parse_args()

# write the information to a file (example script)
with open('/root/mit.txt', 'w') as f:
   f.write(args.info_hijack)