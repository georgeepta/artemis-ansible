Ansible-based Auto-Configuration and Auto-Mitigation Mechanisms in ARTEMIS
  * [General](#general)
  * [Setup and Install](#setup-and-install)
  * [Configure](#configure)
  * [Run](#run)

## General

This repository contains prototype software to enable auto-configuration and auto-mitigation in ARTEMIS using Ansible. Note that while this has been tested in an emulatiomn environment (GNS3) and works in the current form, we are in the process of integrating it as a set of auto-configuration and auto-mitigation microservices in the ARTEMIS container-based architecture.

(TBD: Placeholder for architecture figure)

## Setup and Install

1. First, install ARTEMIS on your host machine following exactly the steps described in [ARTEMIS wiki](https://github.com/FORTH-ICS-INSPIRE/artemis/wiki#artemis-installation-and-setup).
  
2. Clone the current repository within `artemis/backend` directory. 

3. In `artemis/docker-compose.yaml`, under section `services` and tag `backend` replace the following line:
   ```
   image: inspiregroup/artemis-backend:${SYSTEM_VERSION}  
   ```
   with:
   ```
   build: ./backend
   ```

4. In `artemis/docker-compose.yaml` add the following mappings under section `services`, tag `backend`, sub-tag `volumes`:
   ```
   - ./backend/artemis-ansible/automation_tools/configs/admin_configs.json:/root/admin_configs.json
   - ./backend/artemis-ansible/automation_tools/configs/ansible/hosts:/root/hosts
   - ./backend/artemis-ansible/automation_tools/configs/ansible/ansible.cfg:/root/ansible.cfg
   - ./backend/artemis-ansible/automation_tools/utils/test.py:/root/test.py
   - ./backend/artemis-ansible/automation_tools/auto_configuration/playbooks/main_playbook.yaml:/root/main_playbook.yaml
   - ./local_configs/backend/config.yaml:/root/config.yaml
   - ./backend/artemis-ansible/automation_tools/auto_configuration/core/conf_generator.py:/root/conf_generator.py
   - ./backend/artemis-ansible/automation_tools/auto_configuration/parsers/ios_parser.py:/root/ios_parser.py
   - ./backend/artemis-ansible/automation_tools/auto_configuration/playbooks/ios_playbook.yaml:/root/ios_playbook.yaml
   - ./backend/artemis-ansible/automation_tools/auto_configuration/core/timer.py:/root/timer.py
   - ./backend/artemis-ansible/automation_tools/utils/conf_lib.py:/root/conf_lib.py
   - ./backend/artemis-ansible/automation_tools/utils/logger.py:/root/logger.py
   - ./backend/artemis-ansible/automation_tools/configs/logging.yaml:/etc/artemis/automation_tools/logging.yaml
   ```
   Optionally, if you want to also enable auto-mitigation capabilities, please add the following mappings:
   ```
   - ./backend/artemis-ansible/automation_tools/auto_mitigation/playbooks/mitigation_playbook.yaml:/root/mitigation_playbook.yaml
   - ./backend/artemis-ansible/automation_tools/auto_mitigation/playbooks/tunnel_mitigation_playbook.yaml:/root/tunnel_mitigation_playbook.yaml
   - ./backend/artemis-ansible/automation_tools/auto_mitigation/core/mitigation_trigger.py:/root/mitigation_trigger.py
   - ./backend/artemis-ansible/automation_tools/auto_mitigation/playbooks/ios_mitigation.yaml:/root/ios_mitigation.yaml
   - ./backend/artemis-ansible/automation_tools/auto_mitigation/playbooks/ios_tunnel_mitigation.yaml:/root/ios_tunnel_mitigation.yaml
   ```

5. In `artemis/backend/requirements.txt` add the following modules:
   - py-radix==0.10.0
   - json-schema-matcher==0.1.7.1
   - ciscoconfparse==1.4.7 
   - filelock==3.0.12 

6. In `artemis/backend/Dockerfile` before `WORKDIR /root` command add the following commands in order to install Ansible on the backend container:
   ```
   RUN apt-get update
   RUN apt-get -y install software-properties-common
   RUN apt-get update
   RUN apt-get -y install ansible
   RUN pip3 install --upgrade ansible
   RUN pip3 install paramiko
   ```

7. In `artemis/backend/Dockerfile` after `COPY . ./` command add the following commands in order to save log messages from both auto-configuration and auto-mitigation mechanisms:
   ```
   RUN mkdir -p /var/log/artemis/auto_configuration/
   RUN mkdir -p /var/log/artemis/auto_mitigation/
   ``` 

8. Open a terminal in `artemis` directory, stop and re-build ARTEMIS with ansible:
   ```
   docker-compose stop
   docker-compose build
   ```

## Configure

1. In `artemis/backend/artemis-ansible/automation_tools/configs/ansible/hosts` you must define the directly connected routers of your network from which the auto-configuration mechanism gets feed in order to produce the ARTEMIS Configuration File. The structure is hierarchical, and looks as follows:     
   ```
   [ASN:children]
   vendor1-ASN
   vendor2-ASN
      .....
   vendorX-ASN

   [vendor1-ASN:children]
   ASN_router-id1
   ASN_router-id2
      .....
   ASN_router-idX

   [ASN_router-id1]
   ansible_host="IP address or the domain name of the host to connect to"

   [ASN_router-id2]
   ansible_host="IP address or the domain name of the host to connect to"

   ......

   [ASN_router-idX]
   ansible_host="IP address or the domain name of the host to connect to"
  
   [vendor1-ASN:vars]
   ansible_user= "ssh username for router"
   ansible_ssh_pass="ssh password for router"
   ansible_connection=network_cli
   ansible_network_os={ios, eos, junos, ...}
   ansible_become=yes
   ansible_become_method=enable 
   
   ........
   ```   
   Note that the following primitives are involved:
   - `ASN` is the Autonomous System Number to which directly connected routers `ASN_router-id{1,2, N}` belong.    
   - You must specify the ASN and the real router-id in groups and subgroups in host file. For example parent group `[ASN:children]` could be in format `[65001:children]` or `[40:children]`. Children group `[ASN_router-idX]` could be in format `[65001_192.168.10.1]` or `[40_c3725]`. 
   - If you have directly connected routers which belong to different ASNs, you must create exactly the above schema multiple times (for each ASN).

   For Example a real host file could look as follows:
   ```
   [65001:children]
   CISCO-ROUTERS-65001

   [65006:children]
   CISCO-ROUTERS-65006

   [CISCO-ROUTERS-65001:children]
   65001_192.168.10.1

   [CISCO-ROUTERS-65006:children]
   65006_192.168.100.2

   [65001_192.168.10.1]
   c7200_Stable ansible_host=192.168.10.1

   [65006_192.168.100.2]
   helper_as ansible_host=192.168.100.2

   [CISCO-ROUTERS-65001:vars]
   ansible_user=admin
   ansible_ssh_pass=george
   ansible_connection=network_cli
   ansible_network_os=ios
   ansible_become=yes
   ansible_become_method=enable 

   [CISCO-ROUTERS-65006:vars]
   ansible_user=admin1234
   ansible_ssh_pass=george1234
   ansible_connection=network_cli
   ansible_network_os=ios
   ansible_become=yes
   ansible_become_method=enable 
   ```
2. Edit `admin_configs.json` according to your preferences. For more details, check the example in the repository, and contact the ARTEMIS dev team.

## Run

1. First, boot ARTEMIS:
   ```
    docker-compose -f docker-compose.yaml -f docker-compose.exabgp.yaml up -d
    ```
2. Then, connect to the running backend container:
   ```
   docker-compose exec backend bash
   ```
3. On the backend terminal, initiate the auto-configuration timer:
   ```
    ./timer.py /root/admin_configs.json
   ```

That's it !!! From now on, the Auto-Configuration Mechanism executes its work periodically, by polling the connected routers. All changes in ARTEMIS Configurations File will appear in ARTEMIS UI.
