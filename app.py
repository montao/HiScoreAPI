
"""Demo of a RESTful API server in Python, using only the standard library.

The API here is extremely simple:

 *  a POST request stores a JSON object (from the POST body) at the given path
 *  a GET request returns a JSON object stored at the given path

Example usage:

    # Save some JSON to /my/test
    curl -X POST http://127.0.0.1:8080/my/test --data '{"test": 1}'

    # Retrieve the saved JSON data
    curl http://127.0.0.1:8080/my/test

"""

import http.server
import json
import traceback


class ApiRequestHandler(http.server.BaseHTTPRequestHandler):
    """Handle a single HTTP request to the server."""


    def do_GET(self):
        print({self.path})
        if self.path.split("/")[2] == "login":
            print("login")
            data = self.path.split("/")[1]
            self.send_response(200, 'OK')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return
        
        try:
            data = self.server.storage.get(self.path.split("/")[1])
            if data is None:
                self.send_response(404, 'Not Found')
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(b'{}')
                return
            self.send_response(200, 'OK')
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        except:
            traceback.print_exc()

    def do_POST(self):
        try:
            length = int(self.headers['Content-Length'])
            charset = self.headers.get_content_charset('ascii')
            data = json.loads(self.rfile.read(length).decode(charset))
            sessionkey = self.path.split("sessionkey")[1][1:]
            
            if sessionkey not in self.server.records:
                # did not log in
                self.server.records[sessionkey] = str(userid)
            else:
                userid = self.server.records.get(sessionkey) 
            print(f"userid:{userid}")
            self.server.storage[self.path.split("/")[1]] = data
            self.send_response(200, 'OK')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{}')
        except:
            traceback.print_exc()

class ApiServer(http.server.HTTPServer):
    """HTTP server for API requests."""

    def __init__(self, host, port):
        super().__init__((host, port), ApiRequestHandler)
        # Create the dict that will hold the objects we store and retrieve.
        self.storage = {}        
        self.records = {"2600": "42"} # dummy user to populate with something



def main():
    """Main program."""
    server = ApiServer('127.0.0.1', 8080)
    server.serve_forever()


if __name__ == '__main__':
    main()
