"""STUDENT: Complete the TODOs to build a monolithic calculator"""
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/add', methods=['POST'])
def add():
    """TODO: Get JSON with a,b and return {"operation": "add", "a": ..., "b": ..., "result": ...}"""
    data = request.get_json()
    a, b = data['a'], data['b']
    return jsonify({"operation": "add", "a": a, "b": b, "result": a + b})
    pass

@app.route('/multiply', methods=['POST'])
def multiply():
    """TODO: Similar to add but multiply"""
    data = request.get_json()
    a, b = data['a'], data['b']
    return jsonify({"operation": "multiply", "a": a, "b": b, "result": a * b})
    pass

@app.route('/health', methods=['GET'])
def health():
    """TODO: Return {"status": "healthy", "service": "monolith"}"""
    return jsonify({"status": "healthy", "service": "monolith"})
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
