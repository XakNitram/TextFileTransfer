#!/usr/bin/python
import socket

import logging
from sys import stderr, argv

# logging setup
root_logger = logging.getLogger("client")
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(logging.StreamHandler(stderr))


def main(host, port, filename):
    # negotiation process
    conn = socket.socket(type=socket.SOCK_STREAM)
    # SOCK_STREAM == TCP Socket
    server = (host, port)

    conn.connect(server)
    """I like this idea. Sending a connection type code.
    Perhaps 258 to have the server log to this connection."""
    conn.send(b"259")

    data = conn.recv(1024)  # blocking
    root_logger.debug(str(data))
    conn.close()

    # file transfer process
    conn = socket.socket(type=socket.SOCK_DGRAM)
    # SOCK_DGRAM == UDP Socket
    server = (host, int(str(data)[-5:]))

    with open(filename, "rb") as file:
        sdata = b"F"
        while sdata[-1:] != b"T":
            sdata = file.read(4)
            if len(sdata) < 4:
                sdata += b"T"
            else:
                sdata += b"F"
            conn.sendto(sdata, server)
            ack, addr = conn.recvfrom(4)
            root_logger.debug(
                repr(str(ack))
            )


if __name__ == '__main__':
    try:
        main(argv[1], int(argv[2]), argv[3])
    except (IndexError, ValueError) as e:
        root_logger.info(
            "Usage:   client <hostname> <n_port> <file>\n"
            "Example: client   pluto      8080  file.txt"
        )
        root_logger.info(e)
    except OSError as e:
        root_logger.info("Something went wrong.")
        root_logger.info(e)
