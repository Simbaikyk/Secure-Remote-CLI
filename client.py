import socket
import ssl
import json
import subprocess
import datetime
import os
import sys

# ============================================================
# CONFIGURATION
# ============================================================
SERVER_HOST = "10.117.52.32"
SERVER_PORT = 8443
AUTH_TOKEN = "{Your_auth_Token}"
LOG_FILE = "client.log"

def log(message):
    timestamp = datetime.datetime.now().isoformat()
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as file:
            file.write(f"[{timestamp}] {message}
")
    except Exception:
        pass

def send_json(connection, data):
    message = json.dumps(data).encode("utf-8")
    length = len(message).to_bytes(4, "big")
    connection.sendall(length + message)

def receive_json(connection):
    length_data = b""
    while len(length_data) < 4:
        chunk = connection.recv(4 - len(length_data))
        if not chunk: return None
        length_data += chunk
    length = int.from_bytes(length_data, "big")
    data = b""
    while len(data) < length:
        chunk = connection.recv(length - len(data))
        if not chunk: raise ConnectionError("Server closed connection")
        data += chunk
    return json.loads(data.decode("utf-8"))

def execute_command(command):
    commands = {
        "whoami": ["whoami"],
        "hostname": ["hostname"],
        "ipconfig": ["ipconfig"],
        "systeminfo": ["systeminfo"],
        "dir": ["cmd", "dir"],
        "date": ["cmd", "/c", "date", "/t"]
    }
    if command not in commands:
        return "ERROR: Command is not allowed."
    try:
        result = subprocess.run(commands[command], capture_output=True, text=True, timeout=15, shell=False)
        output = result.stdout
        if result.stderr: output += "
" + result.stderr
        return output
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out."
    except Exception as error:
        return f"ERROR: {error}"

def connect_to_server():
    log("Client started")
    log(f"Connecting to {SERVER_HOST}:{SERVER_PORT}")
    tls_context = ssl.create_default_context()
    tls_context.check_hostname = False
    tls_context.verify_mode = ssl.CERT_NONE
    raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_socket.settimeout(None) # Fixed timeout issue
    tls_socket = tls_context.wrap_socket(raw_socket, server_hostname="SecureRemoteCLI")
    tls_socket.connect((SERVER_HOST, SERVER_PORT))
    log("TLS connection established")
    request = receive_json(tls_socket)
    if not request or request.get("type") != "auth_request": raise ConnectionError("Invalid auth request")
    send_json(tls_socket, {"type": "auth", "token": AUTH_TOKEN})
    response = receive_json(tls_socket)
    if not response or response.get("status") != "success":
        log("Authentication failed")
        raise PermissionError("Authentication failed")
    log("Authentication successful")
    while True:
        message = receive_json(tls_socket)
        if not message: break
        if message.get("type") != "command": continue
        command = message.get("command")
        log(f"Command received: {command}")
        if command == "exit":
            log("Server requested session termination")
            break
        output = execute_command(command)
        send_json(tls_socket, {"type": "result", "output": output})
        log(f"Command completed: {command}")
    tls_socket.close()
    log("TLS connection closed")

def main():
    try:
        connect_to_server()
    except Exception as error:
        log(f"Client error: {error}")

if __name__ == "__main__":
    main()
