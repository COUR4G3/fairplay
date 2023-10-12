import base64

from requests import Response
from requests.auth import AuthBase
from requests.cookies import extract_cookies_to_jar
from requests.utils import parse_dict_header
from scramp import ScramClient
from scramp.core import ClientStage


MECHANISMS = (
    "SCRAM-SHA-1",
    "SCRAM-SHA-256",
    "SCRAM-SHA-512",
    "SCRAM-SHA3-512",
)


class HTTPSCRAMAuth(AuthBase):
    """Attaches RFC7804 HTTP SCRAM authentication to the given Request object."""

    def __init__(self, username, password, mechanisms=None, sid=None):
        self.mechanisms = mechanisms or MECHANISMS
        self.client = ScramClient(self.mechanisms, username, password)

        self.pos = None
        self.realm = None
        self.sid = None

    def __call__(self, request):
        if self.sid:
            auth_header = self.generate_request_header()
            request.headers["Authorization"] = auth_header

        request.register_hook("response", self.handle_response)

        try:
            self.pos = request.body.tell()
        except AttributeError:
            # In the case of HTTPSCRAMAuth being reused and the body
            # of the previous request was a file-like object, pos has
            # the file position of the previous body. Ensure it's set to
            # None.
            self.pos = None
        return request

    def deregister(self, response):
        response.request.deregister_hook("response", self.handle_response)

    def generate_request_header(self):
        type = self.client.mechanism_name

        if self.client.stage == ClientStage.set_server_first:
            data = self.client.get_client_final()
        else:
            data = self.client.get_client_first()

        encoded_data = base64.b64encode(data.encode("utf-8")).decode("utf-8")

        if self.sid:
            return f"{type} sid={self.sid}, data={encoded_data}"
        else:
            return f"{type} data={encoded_data}"

    def handle_response(self, response, **kwargs):
        print(response.headers)

        if response.status_code != 401:
            return response

        num_401s = kwargs.pop("num_401s", 0)

        if self.pos is not None:
            # Rewind the file position indicator of the body to where
            # it was to resend the request.
            response.request.body.seek(self.pos)

        # authentication has failed
        if response.status_code == 401 and num_401s >= 2:
            return response

        # auth_headers = response.headers.get("www-authenticate", "")
        # auth_headers = [a.strip() for a in auth_headers.split(",")]

        # # we find the first supported mechanism
        # for auth_header in auth_headers:
        #     type, params = auth_header.split(" ", 1)

        #     if type in self.mechanisms:
        #         break
        # else:
        #     return

        type, params = response.headers.get("www-authenticate", "").split(" ", 1)

        params = parse_dict_header(params)

        data = params.get("data")
        if data:
            decoded_data = base64.b64decode(data).decode("utf-8")

        if self.client.stage == ClientStage.get_client_first:
            self.client.set_server_first(decoded_data)
            self.sid = params["sid"]
        elif self.client.stage == ClientStage.get_client_final:
            self.client.set_server_final(decoded_data)

        response.request.headers["Authorization"] = self.generate_request_header()

        # consume content and release connection
        response.content
        response.raw.release_conn()

        if response.headers.get("set-cookie"):
            response.request.headers["Cookie"] = response.headers.get("set-cookie")

        new_response = response.connection.send(response.request, **kwargs)
        new_response.history.append(response)

        return self.handle_response(new_response, num_401s=num_401s)
