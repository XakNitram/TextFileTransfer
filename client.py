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


# logging setup. I got bored.
root_logger = logging.getLogger("client")
# root_logger.setLevel(logging.DEBUG)
root_logger.setLevel(logging.INFO)

# handler setup
# formatters   - https://docs.python.org/3.7/library/logging.html#formatter-objects
# time formats - https://docs.python.org/3.7/library/time.html#time.strftime
handlr = logging.StreamHandler(stderr)
fmtr = logging.Formatter(
    "(%(asctime)s) %(name)s: "  # prepend message with name and time
    "%(message)s",              # actual message
    "%I:%M %p"                  # date format
)
handlr.setFormatter(fmtr)

# add handler to logger
root_logger.addHandler(handlr)
del handlr, fmtr


def get_port(host, port):
    # open a TCP socket.
    conn = socket.socket(type=socket.SOCK_STREAM)
    server = (host, port)

    # establish a client connection to the server.
    conn.connect(server)

    """I like this idea. Sending a connection-type code.
    Perhaps 258 to have the server log to this connection.
    logging.handlers.SocketHandler. """
    conn.send(b"259")

    """
    Receive 5 bytes over TCP that should be an integer
    from 1024 to 65535 referring to the port the file
    number will be sent over.
    """
    port = conn.recv(5)

    # close the TCP connection.
    conn.close()

    # return the port used for UDP transfer.
    return int(port)


def send_file(host, port, filename):
    # open a UDP socket with a timeout of 2 seconds.
    conn = socket.socket(type=socket.SOCK_DGRAM)
    conn.settimeout(2)

    server = (host, port)

    # open the file and send the data over UDP.
    with open(filename, "rb") as file:
        sdata = b"F"
        while sdata[-1:] != b"T":
            # read the data from the file.
            sdata = file.read(4)

            """
            Check the length of the data received from
            the file. If the length of the data is less
            than 4, the file is assumed to be finished.
            """
            if len(sdata) < 4:
                sdata += b"T"
            else:
                sdata += b"F"

            # send the data over UDP.
            conn.sendto(sdata, server)
            try:
                ack, addr = conn.recvfrom(4)
                root_logger.info(
                    repr(tostr(ack))
                )
            except socket.timeout:
                # ensure that the file gets closed.
                root_logger.info("File transfer unsuccessful. Please try again.")
                break
            except socket.error:
                """
                The socket module has only general 'error' and
                'timeout' errors. This exception handles the
                general errors. Timeouts can sometimes throw
                general errors.
                """
                root_logger.info(
                    "'' - Malformed data? Timeout?"
                )
    conn.close()


if __name__ == '__main__':
    if not exists(argv[3]):
        root_logger.info("No file %s found." % argv[3])
    try:
        hostname = argv[1]
        if hostname == "localhost":
            hostname = socket.gethostname()

        # TCP negotiation
        new_port = get_port(hostname, int(argv[2]))
        root_logger.debug("Port is " + str(new_port))

        # UDP file transfer
        send_file(hostname, new_port, argv[3])
    except (IndexError, ValueError) as e:
        root_logger.info(
            "Usage:   client <hostname> <n_port> <file>\n"
            "Example: client   pluto      8080  file.txt"
        )
        root_logger.debug(e)
    except OSError as e:
        root_logger.info("Something went wrong. Please try again.")
        root_logger.debug(e)
