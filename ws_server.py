from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room
import jwt
from utils.auth import SECRET_KEY  # 기존 코드에서 활용

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 누가 접속했는지 관리용 (선택)
connected_users = {}

@socketio.on("connect")
def handle_connect():
    print(f"[Connected] SID: {request.sid}")

@socketio.on("disconnect")
def handle_disconnect():
    print(f"[Disconnected] SID: {request.sid}")
    connected_users.pop(request.sid, None)

@socketio.on("join_main")
def handle_join_main(data):
    # 누구나 메인 채팅방 join 가능
    join_room("main")
    emit("system", {"msg": "메인 채팅방에 입장했습니다."}, to=request.sid)

@socketio.on("send_chat")
def handle_send_chat(data):
    # JWT 토큰이 있는 유저만 채팅 전송 가능
    token = data.get("token")
    content = data.get("content", "").strip()

    if not token or not content:
        emit("error", {"msg": "토큰 또는 메시지가 없습니다."}, to=request.sid)
        return

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload["username"]

        emit("new_chat", {
            "username": username,
            "content": content
        }, to="main")

        print(f"[Chat] {username}: {content}")

    except jwt.ExpiredSignatureError:
        emit("error", {"msg": "토큰 만료"}, to=request.sid)
    except Exception:
        emit("error", {"msg": "토큰 검증 실패"}, to=request.sid)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5002)
