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
    print("[DEBUG] send_chat data:", data)  # ← 반드시 있어야 함

    token = data.get("token")
    content = data.get("content", "").strip()

    if not token or not content:
        emit("error", {"msg": "토큰 또는 메시지가 없습니다."}, to=request.sid)
        print("[DEBUG] 메시지 거부됨: 토큰 or 내용 없음")
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
        print("[DEBUG] 토큰 만료")
    except Exception as e:
        emit("error", {"msg": "토큰 검증 실패"}, to=request.sid)
        print("[DEBUG] 토큰 검증 실패:", str(e))


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
        pass  # 에러 무시 (유효하지 않은 토큰이면 무시)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5002)
