#!/usr/bin/env python3
"""
Simple static file server for SkillSprint frontend
Run: python server.py
Then visit: http://localhost:5500/frontend/html/signup.html
"""

import http.server
import socketserver
import os

PORT = 5500
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"✅ Server running at http://localhost:{PORT}")
        print(f"📁 Serving from: {DIRECTORY}")
        print(f"\n🔗 Access your pages:")
        print(f"   • Signup: http://localhost:{PORT}/frontend/html/signup.html")
        print(f"   • Dashboard: http://localhost:{PORT}/frontend/html/dashboard.html")
        print(f"   • Quiz: http://localhost:{PORT}/frontend/html/quiz.html")
        print(f"\n⌨️  Press Ctrl+C to stop the server\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✋ Server stopped")
