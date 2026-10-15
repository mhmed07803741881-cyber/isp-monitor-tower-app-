from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import json
import os
import subprocess
import platform

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your-master-secret-key-ali' # مفتاح تشفير الحسابات
jwt = JWTManager(app)

USERS_FILE = 'users.json'
DATA_FILE = 'towers_data.json'

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 1. تسجيل دخول المشترك
@app.route('/api/login', methods=['POST'])
def login():
    req = request.json
    username = req.get('username')
    password = req.get('password')
    
    users = load_json(USERS_FILE)
    user = users.get(username)
    
    if user and user['password'] == password:
        if not user.get('is_active', True):
            return jsonify({'error': 'تم إيقاف حسابك، يرجى تجديد الاشتراك'}), 403
            
        access_token = create_access_token(identity=username)
        return jsonify({'token': access_token, 'expiry_days': user.get('days_left', 30)})
    
    return jsonify({'error': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401

# 2. جلب أبراج المشترك الحالي فقط (محمية بـ Token)
@app.route('/api/my-towers', methods=['GET'])
@jwt_required()
def get_my_towers():
    current_user = get_jwt_identity()
    all_data = load_json(DATA_FILE)
    user_towers = all_data.get(current_user, {})
    
    # فحص البنغ وحالة الأجهزة
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
                "ping": "2.5ms" if is_up else "Timeout"
            })
    return jsonify(result)

def ping_host(host):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-W', '1', host]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
