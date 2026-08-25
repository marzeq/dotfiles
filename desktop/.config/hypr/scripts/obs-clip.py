#!/usr/bin/env python3
import obsws_python as obs
import os


def main():
    home_dir = os.path.expanduser("~")
    with open(os.path.join(home_dir, ".local", ".obs-password"), "r") as f:
        password = f.read().strip()

    with obs.ReqClient(host="localhost", port=4455, password=password, timeout=3) as client:
        client.save_replay_buffer()


if __name__ == "__main__":
    main()
