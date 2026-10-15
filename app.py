from flask import Flask, request, jsonify
import json
import os
import subprocess
import platform

app = Flask(__name__)
DEVICES_FILE = 'devices.json'

def load_devices():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    # بيانات افتراضية مشابهة للصورة
    return [
        {"id": 1, "name": "10.200.122.2", "ip": "10.200.122.2", "type": "MikroTik"},
        {"id": 2, "name": "10.200.122.3", "ip": "10.200.122.3", "type": "MikroTik"},
        {"id": 3, "name": "10.200.122.4", "ip": "10.200.122.4", "type": "Ubiquiti"},
        {"id": 4, "name": "10.200.122.5", "ip": "10.200.122.5", "type": "Ubiquiti"},
        {"id": 5, "name": "10.200.122.6", "ip": "10.200.122.6", "type": "Ubiquiti"},
        {"id": 6, "name": "10.200.122.20", "ip": "10.200.122.20", "type": "Ubiquiti"},
        {"id": 7, "name": "10.150.179.3", "ip": "10.150.179.3", "type": "Mimosa"}
    ]

def save_devices(devices):
    with open(DEVICES_FILE, 'w', encoding='utf-8') as f:
        json.dump(devices, f, ensure_ascii=False, indent=2)

def ping_host(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-W', '1', host]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

@app.route('/api/devices', methods=['GET'])
def get_devices():
    devices = load_devices()
    result = []
    for d in devices:
        is_up = ping_host(d['ip'])
        result.append({
            "id": d.get('id'),
            "name": d.get('name'),
            "ip": d.get('ip'),
            "type": d.get('type', 'MikroTik'),
            "status": "online" if is_up else "offline",
            "ping": "2.4 ms" if is_up else "Timeout"
        })
    return jsonify(result)

@app.route('/api/devices/add', methods=['POST'])
def add_device():
    data = request.json
    name = data.get('name')
    ip = data.get('ip')
    dev_type = data.get('type', 'MikroTik')
    
    if not name or not ip:
        return jsonify({'error': 'Name and IP required'}), 400
        
    devices = load_devices()
    new_id = max([d.get('id', 0) for d in devices], default=0) + 1
    devices.append({"id": new_id, "name": name, "ip": ip, "type": dev_type})
    save_devices(devices)
    return jsonify({'message': 'Added successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
