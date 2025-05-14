from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
import jwt
from utils.auth import SECRET_KEY  # JWT 검증용 키


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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
    join_room("main")
    emit("system", {"msg": "메인 채팅방에 입장했습니다."}, to=request.sid)

@socketio.on("leave_main")
def handle_leave_main(data):
    print(f"[DEBUG] {request.sid} leave main")
    leave_room("main")  # ✅ 올바른 사용 방식
    emit("system", {"msg": "메인 채팅방에서 나갔습니다."}, to=request.sid)

@socketio.on("send_chat")
def handle_send_chat(data):
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

    except jwt.ExpiredSignatureError:
        emit("error", {"msg": "토큰 만료"}, to=request.sid)
    except Exception as e:
        emit("error", {"msg": "토큰 검증 실패"}, to=request.sid)

@socketio.on("typing")
def handle_typing(data):
    token = data.get("token")
    content = data.get("content", "")

    if not token:
        return  # 로그인 안 한 사용자 무시

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload["username"]

        emit("typing_broadcast", {
            "username": username,
            "content": content
        }, to="main")

    except:
        pass  # 유효하지 않은 토큰 무시

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5002)
