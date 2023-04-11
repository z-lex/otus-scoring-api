import json
import logging
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from optparse import OptionParser

from otus_scoring_api.constants import (
    BAD_REQUEST,
    ERRORS,
    INTERNAL_ERROR,
    NOT_FOUND,
    OK,
)
from otus_scoring_api.handlers import method_handler
from otus_scoring_api.store import DEFAULT_REDIS_URL, RedisStore


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {"method": method_handler}
    store = None

    @staticmethod
    def get_request_id(headers):
        return headers.get("HTTP_X_REQUEST_ID", uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        data_string = None
        request = None
        try:
            data_string = self.rfile.read(int(self.headers["Content-Length"]))
            request = json.loads(data_string)
        except Exception as e:
            logging.info("cannot parse request, %s: %s", type(e), e)
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info(
                "%s: '%s' %s" % (self.path, data_string, context["request_id"])
            )
            if path in self.router:
                try:
                    response, code = self.router[path](
                        {"body": request, "headers": self.headers},
                        context,
                        self.store,
                    )
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {
                "error": response or ERRORS.get(code, "Unknown Error"),
                "code": code,
            }
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r).encode("utf-8"))


def main():
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option(
        "-r", "--redis-url", action="store", default=DEFAULT_REDIS_URL
    )
    (opts, args) = op.parse_args()
    logging.basicConfig(
        filename=opts.log,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )
    MainHTTPHandler.store = RedisStore(url=opts.redis_url)
    server = HTTPServer(("0.0.0.0", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()


if __name__ == "__main__":
    main()
