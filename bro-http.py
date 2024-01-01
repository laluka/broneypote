#!/usr/bin/env python

from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json
import socket
import uuid

LHOST = "127.0.0.1"
LPORT = 65111
Path("dump/http").mkdir(parents=True, exist_ok=True)


class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    def handle_ALL(self):
        # Dump our logs
        data = dict()
        data["ip"] = self.client_address[0]
        data["port"] = self.client_address[1]
        data["date"] = self.date_time_string()
        data["method"] = self.command
        data["path"] = self.path
        data["version"] = self.request_version
        data.update(dict(self.headers))

        if "Content-Length" in self.headers:
            # from rich import inspect as i
            # import ipdb; ipdb.set_trace()
            data["body"] = self.rfile.read(int(self.headers["Content-Length"])).decode(
                "utf-8"
            )
            print("body: ", data["body"])

        with open(f"dump/http/{uuid.uuid4().hex}.json", "w") as f:
            f.write(json.dumps(data, indent=2))

        # Handle a minimalist answer
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"ok")
        return

    def handle_one_request(self):
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ""
                self.request_version = ""
                self.command = ""
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                return
            mname = "do_" + self.command
            self.handle_ALL()
            self.wfile.flush()
        except socket.timeout as e:
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return


httpd = HTTPServer((LHOST, LPORT), MyHTTPRequestHandler)

print(f"Server running on http://{LHOST}:{LPORT}/")
httpd.serve_forever()
