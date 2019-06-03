import time, subprocess

# calls main_playbook to get routers configuration file
def get_feed():

    subprocess.call(["sudo",
          "ansible-playbook",
          "-i",
          "/home/george/UOC-CSD/Diploma_Thesis/ansible/hosts",
          "/home/george/UOC-CSD/Diploma_Thesis/ansible/playbooks/main_playbook.yaml"
        ])

def main():
    print("--> Timer Started")
    try:
        while True:
            get_feed()
            time.sleep(10)
    except KeyboardInterrupt:
        print("--> Timer Stopped")
    except:
        print("--> An error occured !!!")

if __name__ == '__main__':
    main()



