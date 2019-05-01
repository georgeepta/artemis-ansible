import sys
import json

jdata = json.loads(sys.argv[1])

print(jdata['prefixes'])
f = open("file.txt", "w+")
f.write(str(jdata['prefixes'][0]['mask']))
f.close()
