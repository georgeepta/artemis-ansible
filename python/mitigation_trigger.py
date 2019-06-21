import sys, getopt, json

def main(argv):
   json_data = ''
   try:
      opts, args = getopt.getopt(argv,"i:",["ifile="])
   except getopt.GetoptError:
      print('mitigation_trigger.py -i <inputfile>')
      sys.exit(2)
   for opt, arg in opts:
      if opt in ("-i", "--ifile"):
          json_data =  arg
   print ('Input data are : ', json_data)

if __name__ == "__main__":
   main(sys.argv[1:])