# coding=utf-8
from flask import Flask, request, jsonify
from flask_cors import CORS

from handler import query_handler
from two_stage import two_stage_qa

app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    return 'server running'


@app.route('/query_v2', methods=['POST'])
def query_v2():
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({"state": 1, "msg": "缺少question参数"}), 400
        question = data["question"]
        result = two_stage_qa(question)
        return jsonify(result)
    except Exception as e:
        return jsonify({"state": 1, "msg": f"处理出错: {str(e)}"}), 500


@app.route('/query', methods=['POST'])
def query():
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({"state": 1, "msg": "缺少question参数"}), 400
        question = data["question"]
        return query_handler(question)
    except Exception as e:
        return jsonify({"state": 1, "msg": f"处理出错: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(port=5001, debug=True)