import sys, time, subprocess, json

# calls main_playbook to get routers configuration file
def get_feed(admin_configs):

    subprocess.call(["sudo",
          "ansible-playbook",
          "-i",
          admin_configs["ansible_hosts_file_path"],
          admin_configs["main_playbook_path"]
        ])

def main():

    with open(sys.argv[1]) as json_file:
        admin_configs = json.load(json_file)
        print("--> Timer Started")
        try:
            while True:
                get_feed(admin_configs)
                time.sleep(10)
        except KeyboardInterrupt:
            print("--> Timer Stopped")
        except:
            print("--> An error occured !!!")

if __name__ == '__main__':
    main()



