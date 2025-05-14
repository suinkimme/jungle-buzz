from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
import threading
import time
from utils.auth import token_required, SECRET_KEY  

# Flask 앱 생성
app = Flask(__name__)
CORS(app)

# MongoDB 연결
client = MongoClient('mongodb://localhost:27017/')
db = client['your_db_name']
article_col = db['article']
chat_col = db['chat']

#버퍼 설정 및 Flush 쓰레드
chat_buffer = []
buffer_lock = threading.Lock()
MAX_BUFFER_SIZE = 10
FLUSH_INTERVAL = 2  # 초

def flush_chat_buffer():
    global chat_buffer
    while True:
        time.sleep(FLUSH_INTERVAL)
        with buffer_lock:
            if chat_buffer:
                chat_col.insert_many(chat_buffer)
                print(f"[Flush] {len(chat_buffer)} chat logs inserted")
                chat_buffer.clear()

flush_thread = threading.Thread(target=flush_chat_buffer, daemon=True)
flush_thread.start()


#API: 회원가입

# [요청 방식] POST /api/register
# [요청 body 예시]
# {
#   "username": "testuser",
#   "password": "1234",
#   "name": "홍길동"
# }

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    name = data.get('name', '')


    create_date = datetime.utcnow().strftime('%Y-%m-%d')

    if not username or not password:
        return jsonify({'error': 'username과 password는 필수입니다'}), 400

    if article_col.find_one({'username': username}):
        return jsonify({'error': '이미 존재하는 사용자입니다'}), 400

    hashed_pw = generate_password_hash(password)
    article_col.insert_one({
        'username': username,
        'user_password': hashed_pw,
        'name': name,
        'create_date': create_date 
    })
    return jsonify({'msg': '회원가입 성공'})



#프론트엔드에서 회원가입 시, 입력한 username이   존재하는지 즉시 확인 가능

# [요청 방식] GET /api/check-username?username=testuser
# → 사용 가능하면 { 200 }, 중복이면 { 400 }

@app.route('/api/check-username', methods=['POST'])
def check_username():
    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({'error': 'username 쿼리 파라미터가 필요합니다'}), 400

    exists = article_col.find_one({'username': username}) is not None

    if exists:
        return jsonify({'error': '이미 존재하는 사용자입니다'}), 400

    return jsonify({'msg': '사용 가능한 아이디입니다'}), 200



#API: 로그인

# [요청 방식] POST /api/login
# [요청 body 예시]
# {
#   "username": "testuser",
#   "password": "1234"
# }
# [응답] { "token": "..." }

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = article_col.find_one({'username': username})
    if user and check_password_hash(user['user_password'], password):
        payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'token': token})

    return jsonify({'error': '로그인 실패'}), 401


#API: 프로필 조회

# [요청 방식] GET /api/profile
# [헤더에 Authorization: Bearer <token> 포함 필요]

@app.route('/api/profile', methods=['GET'])
@token_required
def api_profile(user):
    user_data = article_col.find_one(
        {'username': user},
        {'_id': 0, 'user_password': 0}
    )

    if not user_data:
        return jsonify({'error': '사용자를 찾을 수 없습니다'}), 404

    # 생성년도 및 생성월 추출
    try:
        date = datetime.strptime(user_data['create_date'], '%Y-%m-%d')
        create_year = date.year
        create_month = date.month
    except:
        create_year = None
        create_month = None

    return jsonify({
        'profile': {
            'name': user_data.get('name', ''),
            'email': user_data.get('username', ''),
            'create_year': create_year,
            'create_month': create_month
        }
    })



#API: 마이페이지 채팅로그 가져오기

# [요청 방식] GET /api/chat-logs?page=1
# [헤더에 Authorization: Bearer <token> 포함 필요]
# [응답 예시] { logs: [...], has_more: true }

@app.route('/api/chat-logs', methods=['GET'])
@token_required
def get_chat_logs(user):
    #쿼리 파라미터에서 페이지 번호 가져오기
    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            raise ValueError
    except ValueError:
        return jsonify({'error': 'page는 양의 정수여야 합니다'}), 400

    #페이지네이션 10개
    page_size = 10
    skip = (page - 1) * page_size

    #MongoDB에서 해당 사용자 채팅 로그 조회 (최신순) /timestamp는 반드시 datetime 객체로 저장되어 있어야 정렬이 정확
    logs_cursor = cheat_col.find(
        {'username': user}
    ).sort('timestamp', -1).skip(skip).limit(page_size)

    logs = []
    for log in logs_cursor:
        timestamp = log.get('timestamp')
        logs.append({
            'content': log.get('content'),
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else None
        })

    #다음 페이지 존재 여부 판단
    total_count = cheat_col.count_documents({'username': user})
    has_more = total_count > skip + page_size

    #결과 반환
    return jsonify({
        'logs': logs,
        'has_more': has_more
    })



#채팅 저장 API (버퍼 기반 저장)
# [요청 방식] POST /api/send-chat
# [요청 body 예시] { "content": "안녕하세요!" }
# [헤더에 Authorization: Bearer <token> 포함 필요]
@app.route('/api/send-chat', methods=['POST'])
@token_required
def send_chat(user):
    data = request.get_json()
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'error': '내용이 비어있습니다'}), 400

    log = {
        'username': user,
        'content': content,
        'timestamp': datetime.utcnow()
    }

    with buffer_lock:
        chat_buffer.append(log)
        if len(chat_buffer) >= MAX_BUFFER_SIZE:
            chat_col.insert_many(chat_buffer)
            print(f"[Immediate Flush] {len(chat_buffer)} chat logs inserted")
            chat_buffer.clear()

    return jsonify({'msg': '채팅 저장 대기중'})

@app.route('/')
def index():
    return render_template('main.html', current_path=request.path)

@app.route('/mypage')
def mypage():
    return render_template('mypage.html', current_path=request.path)


if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)
