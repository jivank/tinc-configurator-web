# tinc-configurator-web
Easily create zip files containing tinc configuration for clients to easily connect.
Note: This will generate the public/private key for the client.

##Prerequsites
install flask
>pip3 install flask

Make sure you have a currently working setup. See how 'externalnyc' is configured. [here](https://www.digitalocean.com/community/tutorials/how-to-install-tinc-and-set-up-a-basic-vpn-on-ubuntu-14-04)
This tool will run on your public ip node (as configured in the digitalocean article).

##Running the application
Be sure to run as a user that has read/write permissions to /etc/tinc or wherever your tinc folder resides.
>python3 tinczip.py

##Todo
* Allow user to use only public key
* Handle more than 254 clients


