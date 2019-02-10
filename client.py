#!/usr/bin/python
import socket
import logging
from sys import stderr, argv, version_info


if version_info[0] == 3:
    tostr = lambda x: str(x, encoding="utf-8")
else:
    tostr = lambda x: str(x)

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
    root_logger.debug(tostr(data))
    conn.close()

    # file transfer process
    conn = socket.socket(type=socket.SOCK_DGRAM)
    # SOCK_DGRAM == UDP Socket
    server = (host, int(tostr(data)[-5:]))

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
                repr(tostr(ack))
            )


if __name__ == '__main__':
    try:
        hostname = argv[1]
        if hostname == "localhost":
            hostname = socket.gethostname()
        main(hostname, int(argv[2]), argv[3])
    except (IndexError, ValueError) as e:
        root_logger.info(
            "Usage:   client <hostname> <n_port> <file>\n"
            "Example: client   pluto      8080  file.txt"
        )
        root_logger.info(e)
    except OSError as e:
        root_logger.info("Something went wrong.")
        root_logger.info(e)
