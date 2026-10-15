from flask import Flask, request, jsonify
import json
import os
import subprocess
import platform

app = Flask(__name__)
TOWERS_FILE = 'towers.json'

def load_towers():
    if os.path.exists(TOWERS_FILE):
        with open(TOWERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return [
        {"id": 1, "name": "قطاع الشمال - Sector 1", "ip": "192.168.88.2"},
        {"id": 2, "name": "برج السوق الرئيسي", "ip": "192.168.88.5"}
    ]

def save_towers(towers):
    with open(TOWERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(towers, f, ensure_ascii=False, indent=2)

def ping_host(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-W', '1', host]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

@app.route('/api/towers', methods=['GET'])
def get_towers():
    towers = load_towers()
    status_list = []
    for t in towers:
        is_up = ping_host(t['ip'])
        status_list.append({
            "id": t.get('id'),
            "name": t['name'],
            "ip": t['ip'],
            "status": "online" if is_up else "offline",
            "ping": "2ms" if is_up else "Timeout",
            "ccq": "95%" if is_up else "0%",
            "signal": "-55 dBm" if is_up else "Disconnected"
        })
    return jsonify(status_list)

@app.route('/api/towers/add', methods=['POST'])
def add_tower():
    data = request.json
    name = data.get('name')
    ip = data.get('ip')
    if not name or not ip:
        return jsonify({'error': 'Name and IP required'}), 400
    
    towers = load_towers()
    new_id = max([t.get('id', 0) for t in towers], default=0) + 1
    towers.append({"id": new_id, "name": name, "ip": ip})
    save_towers(towers)
    return jsonify({'message': 'Added successfully'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
