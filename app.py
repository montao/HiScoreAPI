# HTTP GET /<userid/login will return a session token that will expire after 10 minutes
# HTTP POST /<levelid>/score?sessionkey=<sessionkey> will let you post {"score": <score>} and store it
# HTTP GET /<levelid>/highscorelist will retrieve the highscore list of the top 15 unique users
  

from datetime import timedelta, datetime
import http.server
import json
import random
import string
import time
import traceback


class ApiRequestHandler(http.server.BaseHTTPRequestHandler):

    def update(self):
        current_hour_epoch = int(time.time() / 3600)  # Truncate to hour epoch.

        # If the hour has changed we'll update which generation is which.
        if self.server.current_hour_epoch is None:
            self.server.current_hour_epoch = current_hour_epoch
        elif self.server.current_hour_epoch != current_hour_epoch:
            self.server.current_hour_epoch = current_hour_epoch
            self.server.g1 = self.server.g0
            self.server.g0 = {}

    def do_GET(self):

        self.update()

        if self.path.split("/")[2] == "login":
            userid = self.path.split("/")[1]
            sessionkey = "".join(random.choices(string.ascii_uppercase, k=7))
            self.server.g0[sessionkey] = str(userid)
            self.server.ages[sessionkey] = datetime.utcnow()
            data = {"user": sessionkey}
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

        self.update()

        sessionkey = self.path.split("sessionkey")[1][1:]

        age = self.server.ages.get(sessionkey)
        if age is not None and age < datetime.utcnow() + timedelta(minutes=-10):
            del self.server.g0[sessionkey]
            del self.server.g1[sessionkey]
            print("too old session. evicted")
            return

        # Generation 0 - we know all sessions in here are valid.
        if sessionkey in self.server.g0:
            userid = self.server.g0.get(sessionkey)

        elif sessionkey in self.server.g1:
            # Generation 1 - a session in here might be valid.
            userid = self.server.g1[sessionkey]

        try:
            length = int(self.headers['Content-Length'])
            charset = self.headers.get_content_charset('ascii')

            scores = []

            data = json.loads(self.rfile.read(length).decode(charset))
            data["user"] = int(userid)
            print(f"userid:{userid}")

            if self.path.split("/")[1] in self.server.storage:
                scores = self.server.storage.get(self.path.split("/")[1])

                # A user may only appear once per high score list for any given level
                for d in scores:
                    if d['user'] == int(userid) and int(data["score"]) > d['score']:
                        # remove the lower
                        scores.remove(d)

                if len(scores) == 15:
                    # replace only if current is better than lowest
                    print("replace")
                    if scores[14].get("score") < int(data.get("score")):
                        print(f"{userid} made the list")
                    else:
                        return

                scores.append(data)
                scores = sorted(scores, key=lambda k: k['score'], reverse=True)
                self.server.storage[self.path.split("/")[1]] = scores
            else:
                self.server.storage[self.path.split("/")[1]] = [data]
            self.send_response(200, 'OK')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{}')
        except:
            traceback.print_exc()


class ApiServer(http.server.HTTPServer):

    def __init__(self, host, port):
        super().__init__((host, port), ApiRequestHandler)
        # Create the dicts that will hold the objects we store and retrieve.
        self.storage = {}
        self.ages = {}
        self.g0 = {}
        self.g1 = {}
        self.current_hour_epoch = int(time.time() / 3600)


def main():
    server = ApiServer('127.0.0.1', 8080)
    server.serve_forever()


if __name__ == '__main__':
    main()
