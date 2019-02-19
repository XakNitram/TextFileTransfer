#!/usr/bin/python
import socket
import random

import logging
from sys import stderr, argv, version_info
from contextlib import closing


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


# logging setup
root_logger = logging.getLogger("server")
# root_logger.setLevel(logging.DEBUG)
root_logger.setLevel(logging.INFO)

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


def select_port(sock, port):
    # negotiation process
    host = socket.gethostname()
    sock.bind((host, port))
    sock.listen(1)  # become a server socket, max 1 connection.

    # recieve connection from client.
    conn, addr = sock.accept()  # blocking
    root_logger.debug("{} connected.".format(addr))
    data = conn.recv(3)  # assume data is b'259'
    if data == b"259":
        root_logger.debug("Recieved correct message.")

    # generate a random port.
    r_port = random.randint(1024, 65535)

    # check whether port is open.
    port_taken = True
    while port_taken:
        with closing(socket.socket(type=socket.SOCK_STREAM)) as test_sock:
            # may screw over other people, but nobody
            # should be testing their code after the
            # submit date.
            if test_sock.connect_ex((host, port)) == 0:
                port_taken = False
            else:
                root_logger.debug("Port was taken. Selecting new port.")
                r_port = random.randint(1024, 65535)

    # log negotiation message.
    root_logger.info(
        "Negotiation has been detected. "
        "Please select your special random port "
        + str(r_port)
    )

    # send port to client.
    conn.send(tobytes(str(r_port)))
    root_logger.debug("Sent negotiation port to {}".format(addr))
    conn.close()
    return r_port


def receive_file(sock, port):
    # file transfer process
    host = socket.gethostname()
    sock.bind((host, port))
    sock.settimeout(2)

    with open("output.txt", "wb") as file:
        finished = False
        while True:
            try:
                data, addr = sock.recvfrom(5)
                # data is type bytes in the form b'\w{,4}(F|T)'
                # addr is type Tuple[str, int]

                file.write(data[:-1])
                sock.sendto(tobytes(tostr(data)[:-1].upper()), addr)

                if data[-1:] == b"T":
                    # At this point the data has been
                    # written to the file, so we can
                    # safely exit the loop.
                    finished = True
                    break
            except socket.timeout:
                # ensure that the file gets closed.
                break

        if finished:
            root_logger.debug("File transfer complete.")
        else:
            root_logger.info("File transfer interrupted. Please try again.")


if __name__ == '__main__':
    try:
        # TCP negotiation
        ssock = socket.socket(type=socket.SOCK_STREAM)
        rport = select_port(ssock, int(argv[1]))
        root_logger.debug("Port is " + str(rport))
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
        root_logger.info("Something went wrong. Please try again.")
        root_logger.debug(e)
    except (SystemExit, SystemError):
        # just make sure that the socket is closed.
        # it doesn't hurt if the socket is closed twice.
        ssock.close()
