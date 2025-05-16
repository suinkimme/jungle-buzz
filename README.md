# 🐯 Jungle Buzz

> 감정 터기, 정규에서 시작된다.
> 감정을 툩툩 터로놓고, 위로받고, 기록하는 감정 공유 플랫폼

---

## 📌 프로젝트 소개

**Jungle Buzz**는 정규러(사용자)들이
자신의 감정을 자유롭게 표현하고,
매일 아침 GPT 기반의 위로 포스터를 받으며 하루를 시작할 수 있는
실시간 감정 공유 서비스입니다.

---

## 🧹 주요 기능

* 🔐 **회원가입 / 로그인** (JWT 기반)
* ✍️ **실시간 채팅 뷰즈 작성 및 공유 (WebSocket, Socket.io)**
* 📦 **버퍼 기반 채팅 저장 (MongoDB)**
* 📬 **GPT 배안 기반 뷰저레터 수신 (매일 아침 9:50)**
* 📄 **마이페이지에서 내 뷰즈 히스토리 확인 (페이지넷이션)**

---

## 🏗️ 시스템 아키텍처

```
📈 Frontend (HTML/JS)
       ⇄ Flask REST API (/api/...)
                        ⇃
               WebSocket 서버 (Flask-SocketIO)
                        ⇃
                     MongoDB (chat/logs)
                        ⇃
       GPT 배안 에어지니 (gpt-4o-mini)
```

---

## 📂 주요 구성 파일

| 파일명            | 설명                                    |
| -------------- | ------------------------------------- |
| `app.py`       | REST API 서버 (회원가입, 로그인, 채팅 저장, 배안)    |
| `ws_server.py` | WebSocket 실시간 채팅 서버                   |
| `auth.py`      | JWT 인증 데코리어 (`@token_required`)       |
| `templates/`   | HTML 템플릿 (`main.html`, `mypage.html`) |
| `static/`      | JS, CSS 등 정적 파일                       |

---

## 🔑 해당 기술 스택

| 항목    | 사용 기술                             |
| ----- | --------------------------------- |
| 백엔드   | Flask, Flask-CORS, Flask-SocketIO |
| DB    | MongoDB                           |
| 인증    | JWT (PyJWT)                       |
| 감정 배안 | OpenAI GPT (gpt-4o-mini)          |
| 비동기   | threading, schedule               |
| 배포    | Flask 기본 서버 (실제 Nginx 미사용)        |

---

## 🚀 실행 방법

```bash
# 가상환경 설치 및 패키지 설치
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 환경 변수 .env 설정
# .env 파일에:
# OPENAI_API_KEY="YOUR_KEY"

# 백엔드 실행
python app.py           # REST API 서버
python ws_server.py     # WebSocket 서버
```

---

## ⚙️ API 요약

| 엔드토피트                       | 설명                        |
| --------------------------- | ------------------------- |
| `POST /api/register`        | 회원가입                      |
| `POST /api/login`           | 로그인 (→ JWT 반환)            |
| `GET /api/profile`          | 사용자 프로필 조회                |
| `GET /api/chat-logs?page=n` | 내 채팅 로그 페이지넷              |
| `POST /api/send-chat`       | 채팅 저장 (JWT 필요)            |
| `GET /api/recent-chats`     | 가장 간단한 채팅 20개 (누군이든 조회가능) |
| `POST /api/check-username`  | 사용자명 중복 검사                |

---

## 📢 WebSocket 이벤트

| 이벤트명        | 설명                |
| ----------- | ----------------- |
| `connect`   | 접속 시 캡스에 출력       |
| `join_main` | 메인 채팅방 입장         |
| `send_chat` | 채팅 전송 (JWT 포함 필요) |
| `typing`    | 타이핑 브로드커스트        |

---

## 📬 뷰저레터 자동 발송

* 매일 아침 `9:50`, 경과 24시간 채팅 배안
* GPT 통한 감성 레터 생성 → `analysis` 콜렌션 저장
* 메인페이지(`main.html`)에서 최신 레터 표시

---

## 📌 기타

* 버퍼링 저장으로 DB 부하 감소, 채팅 손실 방지
* 모든 민감 API는 `Bearer <JWT>` 인증 필요
* WebSocket은 채팅 읽기는 누군이든 가능, 쓰기는 로그인 필요

---

## 👨‍👨‍👦 팀원

* 김민규
* 이주명
* 김현호

---

## ✨ 메인 로고 디폴트 URL

[http://www.jungle9-zzang.shop/](http://www.jungle9-zzang.shop/)
