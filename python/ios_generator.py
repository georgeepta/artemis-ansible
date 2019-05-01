import sys
import json

data = sys.argv[1]
jdata = json.loads(data)

print(jdata)
f = open("file.txt", "w+")
f.write(jdata)
f.close()
