from functools import wraps
from flask import request, jsonify
import jwt
import os

# 나중에 app.py에서 이 값을 import 해야 함
SECRET_KEY = os.getenv("SECRET_KEY")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': '토큰 없음'}), 401

        try:
            token_type, token = auth_header.split()
            if token_type != 'Bearer':
                raise ValueError('잘못된 형식')

            decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '토큰 만료'}), 401
        except Exception:
            return jsonify({'error': '유효하지 않은 토큰'}), 401

        return f(user=decoded['username'], *args, **kwargs)

    return decorated
