from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
import threading
import time
from utils.auth import token_required, SECRET_KEY
import openai
import schedule
import ast
import os

load_dotenv()

# Flask 앱 생성
app = Flask(__name__)
CORS(app)

# MongoDB 연결
client = MongoClient('mongodb://localhost:27017/')
db = client['your_db_name']
article_col = db['article']
chat_col = db['chat']
analysis_col = db['analysis']

#버퍼 설정 및 Flush 쓰레드
chat_buffer = []
buffer_lock = threading.Lock()
MAX_BUFFER_SIZE = 10
FLUSH_INTERVAL = 2  # 초

openaiClient = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def flush_chat_buffer():
    global chat_buffer
    while True:
        time.sleep(FLUSH_INTERVAL)
        with buffer_lock:
            if chat_buffer:
                chat_col.insert_many(chat_buffer)
                # print(f"[Flush] {len(chat_buffer)} chat logs inserted")
                chat_buffer.clear()

flush_thread = threading.Thread(target=flush_chat_buffer, daemon=True)
flush_thread.start()

# 채팅 가져오기
def get_recent_chat_logs(ms):
    now = datetime.utcnow()
    delta = timedelta(milliseconds=ms)
    cutoff_time = now - delta

    chat_logs = chat_col.find(
        {'timestamp': {'$gte': cutoff_time}},
        {'_id': 0, 'username': 0}
    ).sort('timestamp', -1)

    return list(chat_logs)

# 채팅 분석
def format_chat_logs_markdown(chat_logs):
    # 테이블 헤더
    table_lines = [
        "| 작성일 | 버즈 내용 |",
        "| --- | --- |"
    ]
    
    for log in chat_logs:
        timestamp = log.get('timestamp')
        content = log.get('content', '')
        
        if timestamp:
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp_str = 'Unknown Time'
        
        # 마크다운 테이블 형식으로 추가
        line = f"| {timestamp_str} | {content} |"
        table_lines.append(line)
    
    # 줄바꿈으로 이어붙이기
    return '\n'.join(table_lines)

def analyze_chat():
    query = (
        "당신은 섬세하고 따뜻한 조언자입니다. "
        "이제부터 제공된 데이터를 기반으로 참가자들의 심리 상태를 부드럽게 읽어내고, "
        "편지를 쓰듯 자연스럽고 진심 어린 문장으로 답변을 작성해야 합니다. "
        "결과물은 분석 리포트처럼 딱딱해서는 안 되고, "
        "편안한 말투로 길게 써 내려가야 하며, 친근하고 신뢰를 줄 수 있어야 합니다."
        "또한 정글러들이 작성한 버즈를 직접적으로 언급하지마"
    )

    chat_logs = get_recent_chat_logs(1000 * 60 * 60 * 24)
    formatted_logs = format_chat_logs_markdown(chat_logs)

    if len(chat_logs) == 0:
        print("분석할 채팅 로그가 없습니다.")
        analysis_col.insert_one({
            'timestamp': datetime.utcnow(),
            'content': '버즈가 하나도 없어요. ✨ 아마 모두 오늘은 걱정 없이 행복하게 보내고 있나 봐요! :)'
        })
        return None

    response = openaiClient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 데이터 분석가입니다. 제공된 데이터를 기반으로 사용자의 심리와 관심사를 분석해야 합니다."},
            {"role": "user", "content": f"{query}\n\n{formatted_logs}"}
        ],
        temperature=0.3,
        max_tokens=2000
    )

    # print(response.choices[0].message.content)
    analysis_col.insert_one({
        'timestamp': datetime.utcnow(),
        'content': response.choices[0].message.content
    })
    

# 채팅 분석 스케줄러
schedule.every().day.at("09:50").do(analyze_chat)
# schedule.every(10).seconds.do(analyze_chat)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


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
    logs_cursor = chat_col.find(
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
    total_count = chat_col.count_documents({'username': user})
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
    # 가장 최근 분석 결과 가져오기
    analysis_logs = list(analysis_col.find().sort('timestamp', -1).limit(1))[0]
    content = ast.literal_eval(f"'''{analysis_logs['content']}'''")
    return render_template('main.html', current_path=request.path, analysis_logs=content)

@app.route('/mypage')
def mypage():
    return render_template('mypage.html', current_path=request.path)

@app.route('/api/recent-chats', methods=['GET'])
def get_recent_chats():
    try:
        recent_logs = chat_col.find({}).sort('timestamp', -1).limit(20)
        recent_chats = []
        for log in reversed(list(recent_logs)):
            recent_chats.append({
                'username': log.get('username'),
                'content': log.get('content'),
                'timestamp': log.get('timestamp').strftime('%Y-%m-%d %H:%M:%S') if log.get('timestamp') else None
            })
        return jsonify({'chats': recent_chats})
    except Exception as e:
        return jsonify({'error': '채팅 로딩 실패', 'details': str(e)}), 500



if __name__ == '__main__':
    t = threading.Thread(target=run_schedule)
    t.daemon = True
    t.start()

    app.run('0.0.0.0', port=5001, debug=True)
