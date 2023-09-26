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
import logging
import os
import secrets
import socket
import ssl
import tempfile

import click
import click_spinner

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from platformdirs import PlatformDirs
from scramp import ScramClient, ScramException, ScramMechanism, make_channel_binding
from scramp.core import SERVER_ERROR_UNKNOWN_USER


HOSTNAME = "localhost"
USERNAME = "user"
PASSWORD = "password"

MECHANISM = "SCRAM-SHA-256-PLUS"
MECHANISMS = [MECHANISM]


appdirs = PlatformDirs("zshare.py", "zshare.py")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

m = ScramMechanism(MECHANISM)


def server(out):
    db = {USERNAME: m.make_auth_info(PASSWORD)}

    def auth_fn(username):
        logger.debug(f"authenticating as {username} ...")

        try:
            return db[username]
        except KeyError:
            raise ScramException("User unknown.", SERVER_ERROR_UNKNOWN_USER)

    key = ec.generate_private_key(ec.SECP256R1)

    logger.debug(
        "ssl generated temporary %s private key (x=%x, y=%x)",
        key.curve.name,
        key.public_key().public_numbers().x,
        key.public_key().public_numbers().y % 2,
    )

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "My Company"),
            x509.NameAttribute(NameOID.COMMON_NAME, HOSTNAME),
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

    logger.debug(
        "ssl generated temporary certificate %s", cert.subject.rfc4514_string()
    )

    certfile = tempfile.NamedTemporaryFile(mode="wb")
    certfile.write(cert.public_bytes(serialization.Encoding.PEM))
    certfile.flush()

    keyfile = tempfile.NamedTemporaryFile(mode="wb")
    key_password = secrets.token_bytes(16)
    keyfile.write(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.BestAvailableEncryption(key_password),
        )
    )
    keyfile.flush()

    sock = socket.create_server(("", 8080), family=socket.AF_INET6, dualstack_ipv6=True)
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile.name, keyfile.name, key_password)

    sock = context.wrap_socket(sock, server_side=True)

    logger.debug("listening for connections on %s:%d ...", *sock.getsockname()[:2])

    with click_spinner.Spinner():
        while True:
            client, addr = sock.accept()

            logger.debug("accepted connection from %s:%d", *addr[:2])

            channel_binding = make_channel_binding("tls-unique", client)
            server = m.make_server(auth_fn, channel_binding)

            logger.debug("waiting for authentication ...")

            cfirst = client.recv().decode("utf-8")
            logger.debug("scram client-first: %s", cfirst)

            try:
                server.set_client_first(cfirst)
            except ScramException:
                sfinal = server.get_server_final()
                client.send(sfinal.encode("utf-8"))
                logger.debug("scram server-final: %s", sfinal)

                raise

            sfirst = server.get_server_first()
            client.send(sfirst.encode("utf-8"))
            logger.debug("scram server-first: %s", sfirst)

            cfinal = client.recv().decode("utf-8")
            logger.debug("scram client-final: %s", cfinal)

            try:
                server.set_client_final(cfinal)
            except ScramException:
                sfinal = server.get_server_final()
                client.send(sfinal.encode("utf-8"))
                logger.debug("scram server-final: %s", sfinal)

                raise

            sfinal = server.get_server_final()
            client.send(sfinal.encode("utf-8"))
            logger.debug("scram server-final: %s", sfinal)

            logger.debug("ready to receive transfer")

            logger.debug("receiving transfer ...")

            received = 0
            while True:
                data = client.recv(8192)
                if not data:
                    break
                received += out.write(data)

            logger.debug("received %d bytes", received)

            client.shutdown(socket.SHUT_RDWR)
            client.close()

            break

    sock.shutdown(socket.SHUT_RDWR)
    sock.close()

    logger.debug("connection closed")

    certfile.close()
    keyfile.close()


def client(in_):
    logger.debug("connecting to %s:%d ...", HOSTNAME, 8080)

    sock = socket.create_connection((HOSTNAME, 8080), timeout=60.0)

    logger.debug("connected to %s:%d", *sock.getpeername()[:2])

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    sock = context.wrap_socket(sock)

    channel_binding = make_channel_binding("tls-unique", sock)
    client = ScramClient(MECHANISMS, USERNAME, PASSWORD, channel_binding)

    logger.debug("authenticating as %s ...", USERNAME)

    cfirst = client.get_client_first()
    sock.send(cfirst.encode("utf-8"))
    logger.debug("scram client-first: %s", cfirst)

    sfirst = sock.recv().decode("utf-8")
    logger.debug("scram server-first: %s", sfirst)

    if sfirst == "e=unknown-user":
        raise ScramException("User unknown.", SERVER_ERROR_UNKNOWN_USER)

    client.set_server_first(sfirst)

    cfinal = client.get_client_final()
    sock.send(cfinal.encode("utf-8"))
    logger.debug("scram client-final: %s", cfinal)

    sfinal = sock.recv().decode("utf-8")
    logger.debug("scram server-final: %s", sfinal)
    client.set_server_final(sfinal)

    logger.debug("ready to send transfer")

    logger.debug("sending transfer ...")

    sent = 0
    with click_spinner.Spinner():
        while True:
            data = in_.read(8192)
            if not data:
                break

            sent += sock.send(data)

    # TODO: if we not sending we need to split the previous receive on a
    # separator and then prepend the remainder onto any received data now

    # TODO: send xfer

    logger.debug("transferred %d bytes", sent)

    sock.shutdown(socket.SHUT_RDWR)
    sock.close()

    logger.debug("connection closed")


@click.command
@click.argument("file")
@click.argument("target", required=False)
def cli(file, target=None):
    if os.path.isdir(file):
        raise click.BadParameter(f"File '{file}' is a directory.", param_hint="'FILE'")

    if file and target and not os.path.exists(file):
        raise click.BadParameter(f"Path '{file}' does not exist.", param_hint="'FILE'")

    if target:
        with open(file, "rb") as f:
            client(f)
    else:
        with open(file, "wb") as f:
            server(f)


if __name__ == "__main__":
    cli()
