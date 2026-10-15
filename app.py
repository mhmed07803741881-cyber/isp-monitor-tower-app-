from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import json
import os
import subprocess
import platform

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'ali-abbas-master-secret-key'
jwt = JWTManager(app)

USERS_FILE = 'users.json'
DATA_FILE = 'towers_data.json'

def init_default_user():
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin": {
                "password": "@ali@51",
                "is_active": True,
                "days_left": 30
            }
        }
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_users, f, ensure_ascii=False, indent=2)

init_default_user()

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/api/login', methods=['POST'])
def login():
    req = request.json
    username = req.get('username')
    password = req.get('password')
    
    users = load_json(USERS_FILE)
    user = users.get(username)
    
    if user and user['password'] == password:
        if not user.get('is_active', True):
            return jsonify({'error': 'تم إيقاف الاشتراك'}), 403
            
        access_token = create_access_token(identity=username)
        return jsonify({'token': access_token, 'expiry_days': user.get('days_left', 30)})
    
    return jsonify({'error': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401

@app.route('/api/towers', methods=['GET'])
@jwt_required(optional=True) # يسمح بالتجاوز للتجربة المباشرة
def get_towers():
    data = load_json(DATA_FILE)
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
    if not name: return jsonify({'error': 'Name required'}), 400
    data = load_json(DATA_FILE)
    if name not in data:
        data[name] = []
        save_json(DATA_FILE, data)
    return jsonify({'message': 'Success'}), 200

@app.route('/api/device/add', methods=['POST'])
def add_device():
    req = request.json
    tower_name = req.get('tower')
    name = req.get('name', 'نقطة بث')
    ip = req.get('ip')
    dev_type = req.get('type', 'MikroTik')
    
    if not tower_name or not ip: return jsonify({'error': 'Data required'}), 400
    data = load_json(DATA_FILE)
    if tower_name not in data: data[tower_name] = []
    
    new_id = max([d.get('id', 0) for devices in data.values() for d in devices], default=0) + 1
    data[tower_name].append({"id": new_id, "name": name, "ip": ip, "type": dev_type})
    save_json(DATA_FILE, data)
    return jsonify({'message': 'Success'}), 200

def ping_host(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-W', '1', host]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
