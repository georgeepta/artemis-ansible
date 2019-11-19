# Setup and Run Auto-Configuration and Auto-Mitigation Mechanisms in ARTEMIS tool

1. You must have install the ARTEMIS tool in your host machine following exactly all the steps described in ARTEMIS wiki
   (https://github.com/FORTH-ICS-INSPIRE/artemis/wiki)
  
2. Clone https://github.com/georgeepta/Diploma_Thesis repository in ../artemis/backend/ directory 

3. In ../artemis/docker-compose.yaml in section services at tag backend change this:
   image: inspiregroup/artemis-backend:${SYSTEM_VERSION}  to  build: ./backend

4. Add the below mappings at tag volumes in section services :

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
