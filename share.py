""" share.py

Author: Michael de Villiers <michael@devilears.co.za>

Simple Zero-Configuration Sharing

A simple server-client software for zero-configuration sharing of files from the
browser and command-line, as well as arbitary network data streams.

The use of SCRAM means that passwords are not passed over the wire in plaintext and
there is mutual authentication too, the server and client must know the password,
which combined with channel binding provides moderate protection against MITM attacks
while still maintaing the zero configuration nature of this software.

"""

import datetime as dt
import socket
import ssl

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from platformdirs import PlatformDirs
from scramp import ScramClient, ScramMechanism, make_channel_binding


HOSTNAME = ""
USERNAME = ""
PASSWORD = ""

MECHANISM = "SCRAM-SHA-256-PLUS"
MECHANISMS = [MECHANISM]


appdirs = PlatformDirs("zshare.py", "zshare.py")

m = ScramMechanism(MECHANISM)


def server():
    db = {USERNAME: m.make_auth_info(PASSWORD)}

    def auth_fn(username):
        return db[username]

    key = ec.generate_private_key(ec.SECP256R1)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Company"),
            x509.NameAttribute(NameOID.COMMON_NAME, "mysite.com"),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(dt.datetime.now(dt.timezone.utc))
        .not_valid_after(dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1))
        .sign(key, hashes.SHA256())
    )

    sock = socket.create_server(("", 8080), socket.AF_INET, dualstack_ipv6=True)

    context = ssl.create_default_context()

    cert_bytes = cert.public_bytes(serialization.Encoding.PEM)
    key_bytes = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption,
    )

    context.load_cert_chain(cert_bytes, key_bytes)

    sock = context.wrap_socket(sock, server_side=True, server_hostname=HOSTNAME)

    sock.listen()

    while True:
        client, addr = sock.accept()

        channel_binding = make_channel_binding("tls-server-end-point", sock)
        server = m.make_server(auth_fn, channel_binding)

        cfirst = client.recv().decode("utf-8")
        server.set_client_first(cfirst)

        sfirst = server.get_server_first()
        client.send(sfirst.encode("utf-8"))

        cfinal = client.recv().decode("utf-8")
        server.set_client_final(cfinal)

        sfinal = server.get_server_final()
        client.send(sfinal.encode("utf-8"))

        # TODO: receive transfer

    sock.close()


def client():
    sock = socket.create_connection(("", 8080), timeout=60.0)

    context = ssl.create_default_context()
    context.verify_mode = ssl.CERT_NONE

    sock = context.wrap_socket(sock, server_hostname=HOSTNAME)

    channel_binding = make_channel_binding("tls-server-end-point", sock)
    client = ScramClient(MECHANISMS, USERNAME, PASSWORD, channel_binding)

    cfirst = client.get_client_first()
    sock.send(cfirst.encode("utf-8"))

    sfirst = sock.recv().decode("utf-8")
    client.set_server_first(sfirst)

    cfinal = client.get_client_final()
    sock.send(cfinal.encode("utf-8"))

    sfinal = sock.recv().decode("utf-8")
    client.set_server_final(sfinal)

    # TODO: if we not sending we need to split the previous receive on a
    # separator and then prepend the remainder onto any received data now

    # TODO: send xfer

    sock.close()
