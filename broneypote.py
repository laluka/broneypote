#!/usr/bin/env python3

import os
from os import system
from psutil import net_connections
from sys import argv
from urllib.request import urlopen
import json
import shutil


def get_public_ip():
    try:
        with urlopen("https://api.ipify.org?format=json") as response:
            data = json.load(response)
            return data["ip"]
    except Exception as e:
        print(f"Error retrieving public IP: {e}")
        exit(1)


def read_ports_from_file(filename):
    try:
        with open(filename, "r") as file:
            ports = list({int(line.strip()) for line in file if line.strip()})
            validate_ports(ports)
            return ports
    except FileNotFoundError:
        print(f"Error: Port file '{filename}' not found.")
        exit(1)


def validate_ports(ports):
    try:
        for port in ports:
            if not (1 <= port <= 65535):
                raise ValueError(
                    f"Invalid port number: {port}. Port number should be between 1 and 65535."
                )
    except ValueError as ve:
        print(f"Error validating port: {ve}")
        exit(1)


def parse_port_range(port_specifier):
    try:
        start_port, end_port = map(int, port_specifier.split("-"))
        if not (1 <= start_port <= end_port <= 65535):
            raise ValueError(
                "Invalid port range. Both start and end port should be between 1 and 65535."
            )
        return list(range(start_port, end_port + 1))
    except ValueError as ve:
        print(f"Error parsing port range: {ve}")
        exit(1)


def generate_caddyfile(pub_ip, ports, filename):
    try:
        busy_ports = [
            conn.laddr.port
            for conn in filter(
                lambda con: "SOCK_STREAM" in str(con.type) and con.status == "LISTEN",
                net_connections(),
            )
        ]

        if {80}.intersection(busy_ports):
            raise ValueError("Please unbind port 80 as Caddy uses it by default.")

        for port in set(busy_ports).intersection(ports):
            print(f"Skipping port {port} as it is in use.")

        # Keep some free ports, just in case.
        free_ports = [
            str(port)
            for port in ports
            if not (65111 <= port <= 65222) and port not in busy_ports
        ]

        https_ports = [f"{pub_ip}:{port}" for port in free_ports if "443" in str(port)]
        http_ports = [
            f"{pub_ip}:{port}" for port in free_ports if "443" not in str(port)
        ]

        https_hosts = " ".join(https_ports)
        http_hosts = " ".join(http_ports)

        caddyfile = ""

        caddyfile += f"""
        {{
            servers {{
                protocols h1 h2 h2c
            }}
        }}
        """
        if https_ports:
            caddyfile += f"""
            {https_hosts} {{
                tls internal
                reverse_proxy 127.0.0.1:65111
            }}
            """
        if http_ports:
            caddyfile += f"""
            {http_hosts} {{
                reverse_proxy 127.0.0.1:65111
            }}
            """
        with open(filename, "w") as out:
            out.write(caddyfile)
    except Exception as e:
        print(f"Error generating Caddyfile: {e}")
        exit(1)


def start_caddy_docker(pub_ip):
    print("[+] Config file is ready.")
    print("[+] Now starting caddy docker")
    system(
        "tmux split-window -d 'docker run --rm -it --net=host -v $PWD/Caddyfile:/etc/caddy/Caddyfile -v /tmp/caddy_data2:/data caddy'"
    )
    print(f"Caddy sample running on http://{pub_ip}/")
    print(f"Caddy sample running on https://{pub_ip}/")
    print("[+] Now starting bro-http.py")
    exit(system("python3 bro-http.py"))


def check_tmux_docker():
    if not shutil.which("tmux"):
        print(
            "Tmux is not installed or in PATH. Please install it before running the script."
        )
        exit(1)
    if not shutil.which("docker"):
        print(
            "Docker is not installed or in PATH. Please install it before running the script."
        )
        exit(1)
    if not "TMUX" in os.environ:
        print("Please run the script inside tmux for proper execution.")
        exit(1)


def main():
    check_tmux_docker()
    if len(argv) < 3:
        print(f"Usage: python3 {argv[0]} -p [port_file|start_port-end_port]")
        exit(1)

    if argv[1] == "-p":
        port_specifier = argv[2]
        if os.path.isfile(port_specifier):
            ports = read_ports_from_file(port_specifier)
        elif "-" in port_specifier:
            ports = parse_port_range(port_specifier)
        else:
            print(
                "Invalid port specifier. Use either a file or a range (e.g., 8000-8100)."
            )
            exit(1)
        pub_ip = get_public_ip()
        generate_caddyfile(pub_ip, ports, "Caddyfile")
        start_caddy_docker(pub_ip)
    else:
        print(
            f"Invalid option {argv[1]}. Use -p to specify a port list file or range (e.g., 8000-8100)."
        )
        exit(1)


if __name__ == "__main__":
    main()
