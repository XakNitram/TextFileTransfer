#!/usr/bin/python
import socket
import logging
from os.path import exists
from sys import stderr, argv, version_info


def tostr(x):
    if version_info[0] == 3:
        return str(x, encoding="ascii")
    elif version_info[0] == 2:
        return str(x)


# logging setup
root_logger = logging.getLogger("client")
root_logger.setLevel(logging.DEBUG)

# handler setup
# formatters   - https://docs.python.org/3.7/library/logging.html#formatter-objects
# time formats - https://docs.python.org/3.7/library/time.html#time.strftime
handlr = logging.StreamHandler(stderr)
fmtr = logging.Formatter(
    "(%(asctime)s) %(name)s: "  # prepend message with name and time
    "%(message)s",              # actual message
    "%I:%M %p"                   # date format
)
handlr.setFormatter(fmtr)

# add handler to logger
root_logger.addHandler(handlr)
del handlr, fmtr


def get_port(host, port):
    # negotiation process
    conn = socket.socket(type=socket.SOCK_STREAM)

    # SOCK_STREAM == TCP Socket
    server = (host, port)

    conn.connect(server)
    """I like this idea. Sending a connection-type code.
    Perhaps 258 to have the server log to this connection."""
    conn.send(b"259")

    port = conn.recv(5)
    conn.close()
    return int(tostr(port))


def send_file(host, port, filename):
    # file transfer process
    conn = socket.socket(type=socket.SOCK_DGRAM)
    # SOCK_DGRAM == UDP Socket
    server = (host, port)
    with open(filename, "rb") as file:
        sdata = b"F"
        while sdata[-1:] != b"T":
            sdata = file.read(4)
            if len(sdata) < 4:
                sdata += b"T"
            else:
                sdata += b"F"

            conn.sendto(sdata, server)
            try:
                ack, addr = conn.recvfrom(4)
                root_logger.debug(
                    repr(tostr(ack))
                )
            except socket.error:
                root_logger.info("'' - Malformed data? Timeout?")


if __name__ == '__main__':
    if not exists(argv[3]):
        root_logger.info("No file %s found." % argv[3])
    try:
        hostname = argv[1]
        if hostname == "localhost":
            hostname = socket.gethostname()

        # TCP negotiation
        new_port = get_port(hostname, int(argv[2]))

        # UDP file transfer
        send_file(hostname, new_port, argv[3])
    except (IndexError, ValueError) as e:
        root_logger.info(
            "Usage:   client <hostname> <n_port> <file>\n"
            "Example: client   pluto      8080  file.txt"
        )
        root_logger.info(e)
    except OSError as e:
        root_logger.info("Something went wrong.")
        root_logger.info(e)
