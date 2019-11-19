FROM mavromat/bgpstream-redis:v1.0

LABEL maintainer="Dimitrios Mavrommatis <jim.mavrommatis@gmail.com>"

RUN apt-get update && \
    apt-get -y install --no-install-recommends python3-pip supervisor tcl postgresql-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update
RUN apt-get -y install software-properties-common
RUN apt-get update
RUN apt-get install nano
RUN apt-get -y install ansible
RUN pip3 install --upgrade ansible
RUN pip3 install paramiko

WORKDIR /root

COPY . ./

RUN pip3 --no-cache-dir install -r requirements.txt
RUN pip3 install git+https://github.com/supervisor/supervisor@a0ee8f1026c929ae4d9fc84741924414e8008f49
RUN make clean && make
RUN mkdir -p /etc/artemis/ && \
    mkdir -p /var/log/artemis/ && \
    mkdir -p /var/log/artemis/auto_configuration/ && \
    mkdir -p /var/log/artemis/auto_mitigation/

COPY ./configs/* /etc/artemis/

ENTRYPOINT ["./entrypoint"]
