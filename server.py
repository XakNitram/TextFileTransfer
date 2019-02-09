#!/usr/bin/python
import socket
import random

import logging
from sys import stderr, argv

root_logger = logging.getLogger("server")
root_logger.setLevel(logging.INFO)
root_logger.addHandler(logging.StreamHandler(stderr))


def main(port):
    # negotiation process
    sock = socket.socket(type=socket.SOCK_STREAM)
    host = socket.gethostname()
    sock.bind((host, port))
    sock.listen(5)  # become a server socket, max 5 connections.

    conn, addr = sock.accept()  # blocking
    root_logger.debug("{} connected.".format(addr))
    data = conn.recv(3)  # assume data is b'259'
    if data == b"259":
        root_logger.debug("Recieved correct message.")
    r_port = random.randint(1024, 65535)
    conn.send(
        b"Negotiation has been detected. "
        b"Please select your special random port "
        # + bytes(f"{r_port:0>5d}", "utf-8")
        + bytes("{:0>5d}".format(r_port))
    )
    root_logger.debug("Sent negotiation port to {}".format(addr))
    conn.close()

    # file transfer process
    sock = socket.socket(type=socket.SOCK_DGRAM)
    host = socket.gethostname()
    port = r_port
    sock.bind((host, port))

    with open("output.txt", "wb") as file:
        while True:
            data, addr = sock.recvfrom(5)
            # data is type bytes
            # addr is type Tuple[str, int]

            file.write(data[:-1])
            sock.sendto(bytes(str(data)[:-1].upper()), addr)

            if data[-1:] == b"T":
                # At this point the data has been
                # written to the file, so we can
                # safely exit the loop.
                break
        root_logger.debug("File Transfer Complete.")


if __name__ == '__main__':
    try:
        main(int(argv[1]))
    except (IndexError, ValueError):
        root_logger.info(
            "Usage:   server <n_port>\n"
            "Example: server  pluto"
        )
    except OSError as e:
        root_logger.info("Something went wrong.")
        root_logger.debug(e)
