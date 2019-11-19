# Setup and Run Auto-Configuration and Auto-Mitigation Mechanisms in ARTEMIS

1. You must have install the ARTEMIS tool in your host machine following exactly all the steps described in ARTEMIS wiki
   (https://github.com/FORTH-ICS-INSPIRE/artemis/wiki)
  
2. Clone https://github.com/georgeepta/Diploma_Thesis repository in ../artemis/backend/ directory 

3. In ../artemis/docker-compose.yaml at section services at tag backend change this :
   image: inspiregroup/artemis-backend:${SYSTEM_VERSION}  to --> build: ./backend
