from flask import Flask, request, jsonify
import json
import os
import subprocess
import platform

app = Flask(__name__)
DATA_FILE = 'towers_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ping_host(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-W', '1', host]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

@app.route('/api/towers', methods=['GET'])
def get_towers():
    data = load_data()
    result = {}
    for tower_name, devices in data.items():
        result[tower_name] = []
        for d in devices:
            is_up = ping_host(d['ip'])
            result[tower_name].append({
                "id": d.get('id'),
                "name": d.get('name'),
                "ip": d.get('ip'),
                "type": d.get('type', 'MikroTik'),
                "status": "online" if is_up else "offline",
                "ping": "2.1ms" if is_up else "Timeout"
            })
    return jsonify(result)

@app.route('/api/tower/add', methods=['POST'])
def add_tower():
    req = request.json
    name = req.get('name')
    if not name:
        return jsonify({'error': 'Tower name required'}), 400

    data = load_data()
    if name not in data:
        data[name] = []
        save_data(data)
    return jsonify({'message': 'Tower added successfully'}), 200

@app.route('/api/device/add', methods=['POST'])
def add_device():
    req = request.json
    tower_name = req.get('tower')
    name = req.get('name', 'نقطة بث')
    ip = req.get('ip')
    dev_type = req.get('type', 'MikroTik')

    if not tower_name or not ip:
        return jsonify({'error': 'Tower and IP required'}), 400

    data = load_data()
    if tower_name not in data:
        data[tower_name] = []

    new_id = max([d.get('id', 0) for devices in data.values() for d in devices], default=0) + 1
    data[tower_name].append({"id": new_id, "name": name, "ip": ip, "type": dev_type})
    save_data(data)
    return jsonify({'message': 'Device added successfully'}), 200

@app.route('/api/data/export', methods=['GET'])
def export_data():
    return jsonify(load_data())

@app.route('/api/data/import', methods=['POST'])
def import_data():
    req = request.json
    if req:
        save_data(req)
        return jsonify({'message': 'Imported successfully'})
    return jsonify({'error': 'Invalid data'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
