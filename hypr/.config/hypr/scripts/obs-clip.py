#!/usr/bin/env python3
import obsws_python as obs


def main():
    with obs.ReqClient(host="localhost", port=4455, password="", timeout=3) as client:
        client.save_replay_buffer()


if __name__ == "__main__":
    main()
