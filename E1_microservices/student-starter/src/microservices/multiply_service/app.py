"""STUDENT: Multiply Service - Port 5002 - Only handles multiplication"""
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/multiply', methods=['POST'])
def multiply():
    """TODO: Return {"operation": "multiply", "a": ..., "b": ..., "result": ..., "service": "multiply_service"}"""
    pass

@app.route('/health', methods=['GET'])
def health():
    """TODO: Return {"status": "healthy", "service": "multiply_service"}"""
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
