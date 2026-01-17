"""STUDENT: Add Service - Port 5001 - Only handles addition"""
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/add', methods=['POST'])
def add():
    """TODO: Return {"operation": "add", "a": ..., "b": ..., "result": ..., "service": "add_service"}"""
    pass

@app.route('/health', methods=['GET'])
def health():
    """TODO: Return {"status": "healthy", "service": "add_service"}"""
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
