from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import json
import os
import subprocess
import platform

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'ali-abbas-isp-master-key-2026'
jwt = JWTManager(app)

USERS_FILE = 'users_db.json'
TOWERS_FILE = 'towers_db.json'
VPN_FILE = 'vpn_db.json'

def init_db():
    if not os.path.exists(USERS_FILE):
        # إنشاء حساب تجريبي افتراضي لصاحب برج
        default_users = {"tower_owner_1": {"password": "123", "name": "برج الحلة الرئيسي", "active": True}}
        with open(USERS_FILE, 'w', encoding='utf-8') as f: json.dump(default_users, f, ensure_ascii=False, indent=2)
    if not os.path.exists(TOWERS_FILE):
        with open(TOWERS_FILE, 'w', encoding='utf-8') as f: json.dump({}, f, ensure_ascii=False, indent=2)
    if not os.path.exists(VPN_FILE):
        with open(VPN_FILE, 'w', encoding='utf-8') as f: json.dump({}, f, ensure_ascii=False, indent=2)

init_db()

def load_json(file):
    with open(file, 'r', encoding='utf-8') as f: return json.load(f)

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

def ping_host(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-W', '1', host]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

# تسجيل دخول أصحاب الأبراج (الـ 50 مشترك)
@app.route('/api/login', methods=['POST'])
def login():
    req = request.json
    username = req.get('username')
    password = req.get('password')
    users = load_json(USERS_FILE)
    
    if username in users and users[username]['password'] == password:
        if not users[username].get('active', True):
            return jsonify({'error': 'الحساب موقوف، يراجع الإدارة'}), 403
        token = create_access_token(identity=username)
        return jsonify({'token': token, 'name': users[username]['name']})
    return jsonify({'error': 'خطأ في اسم المستخدم أو كلمة المرور'}), 401

# جلب أبراج المشترك الحالي فقط
@app.route('/api/towers', methods=['GET'])
@jwt_required()
def get_towers():
    current_user = get_jwt_identity()
    all_data = load_json(TOWERS_FILE)
    user_towers = all_data.get(current_user, {})
    
    result = {}
    for tower_name, devices in user_towers.items():
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

# إضافة برج خاص بالمشترك
@app.route('/api/tower/add', methods=['POST'])
@jwt_required()
def add_tower():
    current_user = get_jwt_identity()
    req = request.json
    name = req.get('name')
    if not name: return jsonify({'error': 'Name required'}), 400
    
    all_data = load_json(TOWERS_FILE)
    if current_user not in all_data: all_data[current_user] = {}
    if name not in all_data[current_user]:
        all_data[current_user][name] = []
        save_json(TOWERS_FILE, all_data)
    return jsonify({'message': 'Success'})

# إضافة جهاز خاص بالمشترك
@app.route('/api/device/add', methods=['POST'])
@jwt_required()
def add_device():
    current_user = get_jwt_identity()
    req = request.json
    tower = req.get('tower')
    name = req.get('name', 'AP')
    ip = req.get('ip')
    dev_type = req.get('type', 'MikroTik')
    
    if not tower or not ip: return jsonify({'error': 'Data required'}), 400
    
    all_data = load_json(TOWERS_FILE)
    if current_user not in all_data: all_data[current_user] = {}
    if tower not in all_data[current_user]: all_data[current_user][tower] = []
    
    new_id = max([d.get('id', 0) for t in all_data[current_user].values() for d in t], default=0) + 1
    all_data[current_user][tower].append({"id": new_id, "name": name, "ip": ip, "type": dev_type})
    save_json(TOWERS_FILE, all_data)
    return jsonify({'message': 'Success'})

# حفظ إعدادات الـ VPN الخاصة بكل مشترك
@app.route('/api/vpn', methods=['POST'])
@jwt_required()
def save_vpn():
    current_user = get_jwt_identity()
    req = request.json
    vpn_data = load_json(VPN_FILE)
    vpn_data[current_user] = req
    save_json(VPN_FILE, vpn_data)
    return jsonify({'message': 'VPN saved successfully'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
