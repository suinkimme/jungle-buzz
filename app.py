# 내장
import json
from functools import wraps
from datetime import datetime, timezone

# 외부
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from flask.json.provider import JSONProvider
from bson import ObjectId

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client.dbjungle


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, **kwargs, cls=CustomJSONEncoder)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)


app.json = CustomJSONProvider(app)

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)
