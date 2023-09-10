#!/usr/bin/env python3

import json
import socket
import struct

SERVER_IP = "127.0.0.1"


def prompt(p):
    print(p, end=" ")
    return input().strip()


def sendall(s, d):
    d = d.encode("utf-8")
    s.sendall(struct.pack("!i", len(d)))
    s.sendall(d)


def recv(s):
    (l,) = struct.unpack("!i", s.recv(4))
    return s.recv(l).decode()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((SERVER_IP, 54249))
    while True:
        cmd = prompt(">")

        if cmd == "beacons":
            sendall(sock, "beacons")
            print(recv(sock))

        else:
            target = prompt("Which beacon to run on? >")
            sendall(sock, json.dumps({"command": cmd, "beacon_id": target}))
            cid = json.loads(recv(sock))
            print("Waiting...")
            while True:
                p = json.loads(recv(sock))
                if p["command_id"] == cid["command_id"]:
                    print(p["result"])
                    break
