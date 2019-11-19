# Setup and Run Auto-Configuration and Auto-Mitigation Mechanisms in ARTEMIS tool

1. You must have install the ARTEMIS tool in your host machine following exactly all the steps described in ARTEMIS wiki
   (https://github.com/FORTH-ICS-INSPIRE/artemis/wiki)
  
2. Clone https://github.com/georgeepta/Diploma_Thesis repository in ../artemis/backend/ directory 

3. In ../artemis/docker-compose.yaml in section services at tag backend change this:
   image: inspiregroup/artemis-backend:${SYSTEM_VERSION}  to  build: ./backend

4. In ../artemis/docker-compose.yaml add the below mappings at tag volumes in section services :

   - ./backend/Diploma_Thesis/automation_tools/configs/admin_configs.json:/root/admin_configs.json
   - ./backend/Diploma_Thesis/automation_tools/auto_mitigation/playbooks/mitigation_playbook.yaml:/root/mitigation_playbook.yaml
   - ./backend/Diploma_Thesis/automation_tools/auto_mitigation/playbooks/tunnel_mitigation_playbook.yaml:/root/tunnel_mitigation_playbook.yaml
   - ./backend/Diploma_Thesis/automation_tools/configs/ansible/hosts:/root/hosts
   - ./backend/Diploma_Thesis/automation_tools/configs/ansible/ansible.cfg:/root/ansible.cfg
   - ./backend/Diploma_Thesis/automation_tools/auto_mitigation/core/mitigation_trigger.py:/root/mitigation_trigger.py
   - ./backend/Diploma_Thesis/automation_tools/auto_mitigation/playbooks/ios_mitigation.yaml:/root/ios_mitigation.yaml
   - ./backend/Diploma_Thesis/automation_tools/auto_mitigation/playbooks/ios_tunnel_mitigation.yaml:/root/ios_tunnel_mitigation.yaml
   - ./backend/Diploma_Thesis/automation_tools/utils/test.py:/root/test.py
   - ./backend/Diploma_Thesis/automation_tools/auto_configuration/playbooks/main_playbook.yaml:/root/main_playbook.yaml
   - ./local_configs/backend/config.yaml:/root/config.yaml
   - ./backend/Diploma_Thesis/automation_tools/auto_configuration/core/conf_generator.py:/root/conf_generator.py
   - ./backend/Diploma_Thesis/automation_tools/auto_configuration/parsers/ios_parser.py:/root/ios_parser.py
   - ./backend/Diploma_Thesis/automation_tools/auto_configuration/playbooks/ios_playbook.yaml:/root/ios_playbook.yaml
   - ./backend/Diploma_Thesis/automation_tools/auto_configuration/core/timer.py:/root/timer.py
   - ./backend/Diploma_Thesis/automation_tools/utils/conf_lib.py:/root/conf_lib.py
   - ./backend/Diploma_Thesis/automation_tools/utils/logger.py:/root/logger.py
   - ./backend/Diploma_Thesis/automation_tools/configs/logging.yaml:/etc/artemis/automation_tools/logging.yaml
   

5. In ../artemis/backend/requirements.txt add the below modules:

   - py-radix==0.10.0
   - json-schema-matcher==0.1.7.1
   - ciscoconfparse==1.4.7 
   - filelock==3.0.12 


6. In ../artemis/backend/Dockerfile before "WORKDIR /root" command add the below commands in order to install Ansible 
   software in backend container (Be careful with the sequence):

   - RUN apt-get update
   - RUN apt-get -y install software-properties-common
   - RUN apt-get update
   - RUN apt-get -y install ansible
   - RUN pip3 install --upgrade ansible
   - RUN pip3 install paramiko

7. In ../artemis/backend/Dockerfile after "COPY . ./" command add the below commands in order to save log messages from
   both of mechanisms:

   - RUN mkdir -p /var/log/artemis/auto_configuration/
   - RUN mkdir -p /var/log/artemis/auto_mitigation/ 

8. Open a terminal in ../artemis directory and type the following:

   - sudo docker ps                     (in order to check that we dont have another docker process open for artemis)
   - sudo docker-compose build          (in order to build container with the above changes)

9. In ../artemis/backend/Diploma_Thesis/automation_tools/configs/ansible/hosts you must define the directly connected 
   routers from which auto_configuration mechanism gets feed in order to produce the ARTEMIS Configuration File. 
   
   Important !!!, this file must have the following structure:


   [ASN:children]<br>
   vendor1-ASN<br>
   vendor2-ASN<br>
      .....<br>
   vendorX-ASN


   [vendor1-ASN:children]<br>
   ASN_router-id1<br>
   ASN_router-id2<br>
      .....<br>
   ASN_router-idX


   [ASN_router-id1]<br>
   ansible_host=router-id1

   [ASN_router-id2]<br>
   ansible_host=router-id2

   ......

   [ASN_router-idX]<br>
   ansible_host=router-idX
  
 
   [vendor1-ASN:vars]<br>
   ansible_user= "ssh username for router"<br>
   ansible_ssh_pass="ssh password for router"<br>
   ansible_connection=network_cli<br>
   ansible_network_os={ios, eos, junos, ...}<br>
   ansible_become=yes<br>
   ansible_become_method=enable 


  
            ........



   [vendorX-ASN:children]<br>
   ASN_router-idY<br>
   ASN_router-idZ<br>
      .....<br>
   ASN_router-idW

  
   [ASN_router-idY]<br>
   ansible_host=router-idY

   [ASN_router-idZ]<br>
   ansible_host=router-idZ

   ......

   [ASN_router-idW]<br>
   ansible_host=router-idW


   [vendorX-ASN:vars]<br>
   ansible_user= "ssh username for router"<br>
   ansible_ssh_pass="ssh password for router"<br>
   ansible_connection=network_cli<br>
   ansible_network_os={ios, eos, junos, ...}<br>
   ansible_become=yes<br>
   ansible_become_method=enable
   

   - Where "ASN" is the real Autonomous System Number of AS in which directly connected routers "ASN_router-id{1,2, N}" belongs to.    
   - You must specify the real ASN number and the real router-id in groups and subgroups in host file. 
     For example parent group [ASN:children] could be in format [65001:children] or [40:children].
     For example children group [ASN_router-idX] could be in format [65001_192.168.10.1] or [40_c3725]. 
   - If you have directly connected routers which belongs to different ASNs, you must create exactly the above schema multiple times
     (for each ASN)    

   
   For Example a host file could be the above:


   [65001:children]<br>
   CISCO-ROUTERS-65001

   [65006:children]<br>
   CISCO-ROUTERS-65006


   [CISCO-ROUTERS-65001:children]<br>
   65001_192.168.10.1

   [CISCO-ROUTERS-65006:children]<br>
   65006_192.168.100.2


   [65001_192.168.10.1]<br>
   c7200_Stable ansible_host=192.168.10.1

   [65006_192.168.100.2]<br>
   helper_as ansible_host=192.168.100.2

   [CISCO-ROUTERS-65001:vars]<br>
   ansible_user=admin<br>
   ansible_ssh_pass=george<br>
   ansible_connection=network_cli<br>
   ansible_network_os=ios<br>
   ansible_become=yes<br>
   ansible_become_method=enable 

   [CISCO-ROUTERS-65006:vars]<br>
   ansible_user=admin1234<br>
   ansible_ssh_pass=george1234<br>
   ansible_connection=network_cli<br>
   ansible_network_os=ios<br>
   ansible_become=yes<br>
   ansible_become_method=enable 


