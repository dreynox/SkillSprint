import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_sanitize_middleware():
    payload = {
        "name": "<script>alert(1)</script>John",
        "description": "<img src=x onerror=alert(1)>Test",
        "nested": {
            "key": "javascript:alert(1)"
        },
        "list": [
            "<a href='javascript:alert(1)'>Link</a>"
        ]
    }
    
    @app.post("/test-sanitize")
    def echo(data: dict):
        return data

    response = client.post("/test-sanitize", json=payload)
    data = response.json()
    
    assert "<script>" not in data["name"]
    assert "onerror" not in data["description"]
    assert "javascript:" not in data["list"][0]
