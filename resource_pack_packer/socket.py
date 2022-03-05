import json
import socket
from typing import Callable, Optional

PORT = 8080


def socket_json_run(command, callback: Callable, arg: Optional = None):
    """
    Run callback when socket send json command
    :param command: The json command that triggers the callback
    :param callback: The callback run when the command is run
    :param arg: A argument that will be passed into the callback
    """
    s = socket.socket()
    s.bind(("", PORT))
    s.listen(5)

    # Socket loop
    while True:
        # Establish connection with client.
        c, address = s.accept()
        data = json.loads(c.recv(1024).decode("utf-8")[2:])

        if data:
            if "command" in data:
                if data["command"] == command:
                    s.close()
                    c.close()
                    if arg is not None:
                        callback(arg)
                    else:
                        callback()
