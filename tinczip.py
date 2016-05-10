from flask import Flask, request, send_file
import io
import json
import os
import subprocess
import platform
import shutil
import stat


app = Flask(__name__)
tinc_dir = ''
if not tinc_dir:
    os_ = platform.platform()
    if os_.startswith('Darwin'):
        tinc_dir = '/opt/local/etc/tinc'
    elif os_.startswith('Linux'):
        tinc_dir = '/etc/tinc'

networks = []
if not networks:
    networks = [x for x in os.listdir(tinc_dir) if not x.endswith('tinczip')]

def _get_network_dir(network):
    global tinc_dir
    return os.path.join(tinc_dir,network)

def _get_hosts_dir(network):
    return os.path.join(_get_network_dir(network), 'hosts')


def get_hostname(network):
    with open(os.path.join(_get_network_dir(network),'tinc.conf'),'r') as tinc_conf:
        for line in tinc_conf.readlines():
            if line.startswith('Name'):
                name = line.split('=')[1]
                break
    return name.strip()


def find_free_ip(network):
    hosts_dir = _get_hosts_dir(network)
    files = [os.path.join(hosts_dir,f) for f in os.listdir(hosts_dir) if os.path.isfile(os.path.join(hosts_dir, f))]
    ips = []
    for f in files:
        with open(f,'r') as host_file:
            for line in host_file.readlines():
                if line.startswith('Subnet'):
                    ips.append(line.split('=')[1].split('/')[0])
                    continue
    free_ip = ips[0].split('.')[:-1]
    last_digits = sorted([int(ip.split('.')[-1]) for ip in ips])

    open_slots = []
    for i in range(len(last_digits)-1):
        open_slots.extend(range(last_digits[i]+1,last_digits[i+1]))
        if open_slots:
            break
    if not open_slots:
        free_ip += [str(last_digits[-1] + 1)]
    else:
        free_ip += [str(open_slots[0])]
    return '.'.join(free_ip)




def process(network, name, os_):
    tmp_network = network+'_tinczip'
    tmp_dir = os.path.join(tinc_dir,tmp_network)
    tmp_hosts_dir = os.path.join(tmp_dir,'hosts')
    os.mkdir(tmp_dir)
    os.mkdir(tmp_hosts_dir)
    assigned_ip = find_free_ip(network)
    tinc_conf = '''Name = {name}
                ConnectTo = {host}
                '''
    host_conf = '''Subnet = {}/32'''.format(assigned_ip)

    if os_ == 'windows':
        tinc_conf += 'Interface = VPN'
    # if _os == "linux":
    #     tinc_conf += 'Device = /dev/net/tun0'

    #write tinc.conf
    with open(os.path.join(tmp_dir, 'tinc.conf'), 'w') as tinc_conf_file:
        tinc_conf_file.write(tinc_conf)
    #write hostname file
    with open(os.path.join(tmp_hosts_dir, name), 'w') as host_conf_file:
        host_conf_file.write(host_conf)

    subprocess.check_output('tincd -n {} -K4096 | </dev/null'.format(tmp_network),shell=True)


    #copy client key to server folder
    local_hosts_dir = _get_hosts_dir(network)
    shutil.copy(os.path.join(tmp_hosts_dir, name),local_hosts_dir)
    #copy server key to tmp folder
    shutil.copy(os.path.join(local_hosts_dir, get_hostname(network)), tmp_hosts_dir)

    if os_ == 'linux' or os_ == 'osx':
        #make tinc-up and tinc-down
        tinc_up = 'ifconfig $INTERFACE {} netmask 255.255.255.0'.format(assigned_ip)
        tinc_down = 'ifconfig $INTERFACE down'
        tinc_up_path = os.path.join(tmp_dir,'tinc-up')
        tinc_down_path = os.path.join(tmp_dir,'tinc-down')
        with open(tinc_up_path, 'w') as tu:
            tu.write(tinc_up)
        st = os.stat(tinc_up_path)
        os.chmod(tinc_up_path, st.st_mode | stat.S_IXUSR)
        with open(tinc_down_path, 'w') as td:
            td.write(tinc_down)
        st = os.stat(tinc_down_path)
        os.chmod(tinc_down_path, st.st_mode | stat.S_IXUSR)

    zip_location = os.path.join(tinc_dir,tmp_network)

    zip_file = shutil.make_archive(zip_location, 'zip', tmp_dir)
    zip_bytes = ''
    with open(zip_file,'rb') as zip_:
        zip_bytes = zip_.read()

    #cleanup
    shutil.rmtree(tmp_dir)
    os.remove(zip_file)
    return send_file(io.BytesIO(zip_bytes),
                     attachment_filename='{}.zip'.format(tmp_network),
                     mimetype='application/zip',
                     as_attachment=True)




@app.route('/', methods=['GET','POST'])
def root():
    global networks
    if request.method == 'GET':
        return '''<!DOCTYPE html>
                <html>
                <body><form id="form" method="post">
                Your PC Name:<br>
                <input type="text" name="pcname"><br>
                <input type="radio" name="os" value="linux" checked> Linux<br>
                <input type="radio" name="os" value="windows"> Windows<br>
                <input type="radio" name="os" value="osx"> OSX <br>
                Choose Network<br>
                <select name="network" form="form">
                {}
                </select><br>
                <input type="submit" value="Submit">
                </form>
                </body>
                </html>'''.format('\n'.join(
                ['<option value="{n}">{n}</option>'.format(n=n) for n in networks]
                ))
    if request.method == 'POST':
        network = request.form['network']
        pc_os = request.form['os']
        pc_name = request.form['pcname']
        if not pc_name:
            return 'invalid name'
        if network not in networks:
            return 'invalid network'
        return process(network,pc_name,pc_os)



if __name__ == '__main__':
    app.run(debug=True)
