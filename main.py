from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import socket
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import os

HOST = 'localhost'
HTTP_PORT = 3000
SOCKET_PORT = 5000

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('templates/index.html', 'rb') as file:
                self.wfile.write(file.read())
        elif parsed_path.path == '/message.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('templates/message.html', 'rb') as file:
                self.wfile.write(file.read())
        elif parsed_path.path.startswith('/static/'):
            filename = parsed_path.path.split('/')[-1]
            filepath = os.path.join('static', filename)
            if os.path.exists(filepath):
                self.send_response(200)
                if filename.endswith('.css'):
                    self.send_header('Content-type', 'text/css')
                elif filename.endswith('.png'):
                    self.send_header('Content-type', 'image/png')
                self.end_headers()
                with open(filepath, 'rb') as file:
                    self.wfile.write(file.read())
            else:
                self.send_error(404)
                self.end_headers()
                self.wfile.write(b'Error 404: Not Found')
                # Перенаправление на страницу error.html
                self.send_response(301)
                self.send_header('Location', '/error.html')
                self.end_headers()
        else:
            self.send_error(404)
            self.end_headers()
            self.wfile.write(b'Error 404: Not Found')
            # Перенаправление на страницу error.html
            self.send_response(301)
            self.send_header('Location', '/error.html')
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data_dict = parse_qs(post_data.decode())
        print("Received data:", data_dict)
        data_dict['timestamp'] = str(datetime.now())
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(json.dumps(data_dict).encode(), (HOST, SOCKET_PORT))

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

class SocketHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data, _ = self.request
        message_data = json.loads(data.decode())
        message_data['timestamp'] = str(datetime.now())
        print("Received data from HTTP server:", message_data)
        with open('storage/data.json', 'a') as file:
            file.write(json.dumps(message_data) + '\n')
            file.close()



def main():
    http_server = HTTPServer((HOST, HTTP_PORT), HttpHandler)
    socket_server = socketserver.ThreadingUDPServer((HOST, SOCKET_PORT), SocketHandler)
    print(f"HTTP Server running at http://{HOST}:{HTTP_PORT}")
    print(f"Socket Server running at {HOST}:{SOCKET_PORT}")

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()
    finally:
        socket_server.shutdown()

if __name__ == '__main__':
    main()
