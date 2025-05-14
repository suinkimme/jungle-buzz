from pymongo import MongoClient
from datetime import datetime, timedelta
import random

client = MongoClient('mongodb://localhost:27017/')
db = client['your_db_name']
chat_col = db['chat']

username = 'a@a.com'

dummy_logs = []
base_time = datetime.utcnow()

for i in range(300):
    dummy_logs.append({
        'username': username,
        'content': f'테스트 메시지 {i+1}',
        'timestamp': base_time - timedelta(seconds=random.randint(0, 86400))  # 최근 하루 이내 시간
    })
chat_col.insert_many(dummy_logs)
print("채팅 로그 삽입 완료")