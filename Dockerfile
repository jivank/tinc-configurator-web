FROM debian:jessie
RUN apt-get update && apt-get upgrade && apt-get install tinc python3 python3-pip -y
RUN pip3 install flask
RUN mkdir /etc/tinc/testnet
RUN mkdir /etc/tinc/testnet/hosts
RUN sh -c 'printf "Name = dockerhost" > /etc/tinc/testnet/tinc.conf'
RUN sh -c 'printf "Address = 127.0.0.1\nSubnet = 10.0.0.1/32" > /etc/tinc/testnet/hosts/dockerhost'
RUN tincd -n testnet -K4096

COPY tinczip.py /root/

CMD ["python3","/root/tinczip.py"]
