#!/usr/bin/python
import socket
import random

import logging
from sys import stderr, argv, version_info


def tobytes(x):
    if version_info[0] == 3:
        return bytes(x, encoding="ascii")
    elif version_info[0] == 2:
        return bytes(x)


def tostr(x):
    if version_info[0] == 3:
        return str(x, encoding="ascii")
    elif version_info[0] == 2:
        return str(x)


root_logger = logging.getLogger("server")
root_logger.setLevel(logging.INFO)
root_logger.addHandler(logging.StreamHandler(stderr))


def select_port(sock, port):
    # negotiation process
    host = socket.gethostname()
    sock.bind((host, port))
    sock.listen(5)  # become a server socket, max 5 connections.

    conn, addr = sock.accept()  # blocking
    root_logger.debug("{} connected.".format(addr))
    data = conn.recv(3)  # assume data is b'259'
    if data == b"259":
        root_logger.debug("Recieved correct message.")
    r_port = random.randint(1024, 65535)
    root_logger.info(
        "Negotiation has been detected. "
        "Please select your special random port "
        + str(r_port)
    )
    conn.send(tobytes(str(r_port)))
    root_logger.debug("Sent negotiation port to {}".format(addr))
    conn.close()
    return r_port


def receive_file(sock, port):
    # file transfer process
    host = socket.gethostname()
    sock.bind((host, port))

    with open("output.txt", "wb") as file:
        while True:
            data, addr = sock.recvfrom(5)
            # data is type bytes
            # addr is type Tuple[str, int]

            file.write(data[:-1])
            sock.sendto(tobytes(tostr(data)[:-1].upper()), addr)

            if data[-1:] == b"T":
                # At this point the data has been
                # written to the file, so we can
                # safely exit the loop.
                break
        root_logger.debug("File Transfer Complete.")

    # new system
    # This may not be accepted because it adds
    # extra information sent over the network
    # that are not detailed in the assignment.

    # with open("output.txt", "wb") as file:
    #     data, addr = sock.recvfrom(128)  # way more than enough to recieve the length of the file.
    #     sock.sendto(b"File length recieved.", addr)
    #
    #     for i in range(int(data)):
    #         data, addr = sock.recvfrom(5)
    #         # data is type bytes
    #         # addr is type Tuple[str, int]
    #
    #         file.write(data[:-1])
    #         sock.sendto(tobytes(tostr(data)[:-1].upper()), addr)
    #
    #         if data[-1:] == b"T":
    #             # At this point the data has been
    #             # written to the file, so we can
    #             # safely exit the loop.
    #             break
    #     root_logger.debug("File Transfer Complete.")


if __name__ == '__main__':
    try:
        # TCP negotiation
        ssock = socket.socket(type=socket.SOCK_STREAM)
        rport = select_port(ssock, int(argv[1]))
        ssock.close()

        # UDP file transfer
        ssock = socket.socket(type=socket.SOCK_DGRAM)
        receive_file(ssock, rport)
        ssock.close()
    except (IndexError, ValueError):
        root_logger.info(
            "Usage:   server <n_port>\n"
            "Example: server  pluto"
        )
    except OSError as e:
        root_logger.info("Something went wrong.")
        root_logger.debug(e)
    except (SystemExit, SystemError):
        # just make sure that the socket is closed.
        # it doesn't hurt if the socket is closed twice.
        ssock.close()
