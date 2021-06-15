#!/usr/bin/env python3
from .worker import Worker, parse_arguments

def main():
    Worker("aqualin.yaml", parse_arguments()).mqtt_connect().timers().run()

if __name__ == "__main__":
    main()
