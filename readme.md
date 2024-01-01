# Broneypote

- Bro 🤜🤛
- Honey 🌹
- Pote 🎮

Basically, a honneypot for the bros!

## Setup

```bash
# Setup
sudo apt update && sudo apt install -y python3 python3-pip virtualenv docker tmux
virtualenv -p python3 .py3 && source .py3/bin/activate
pip install -r requirements.txt

# Usage
python3 broneypote.py -p [port_file|start_port-end_port]

# You can specify a port list in a file
python3 broneypote.py -p top1k.txt

# Or a port range
python3 broneypote.py -p 80-550

# You need to install tmux and docker for proper execution
```
