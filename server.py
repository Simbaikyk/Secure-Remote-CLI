import socket
import ssl
import json
import secrets
import datetime
import os

HOST = "0.0.0.0"
PORT = 8443
CERT_FILE = "server.crt"
KEY_FILE = "server.key"
AUTH_TOKEN = "fSwscUi04xXkA9bP7PxT5jThHPwqzCyhWpIgPBSN17Q"
LOG_DIR = "../logs"
LOG_FILE = os.path.join(LOG_DIR, "server.log")

ALLOWED_COMMANDS = {"whoami", "hostname", "ipconfig", "systeminfo", "dir", "date"}

def log(message):
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {message}
")

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
        if not chunk: raise ConnectionError("Connection closed")
        data += chunk
    return json.loads(data.decode("utf-8"))

def authenticate(connection):
    send_json(connection, {"type": "auth_request"})
    response = receive_json(connection)
    if not response or response.get("type") != "auth": return False
    received_token = response.get("token", "")
    if secrets.compare_digest(received_token, AUTH_TOKEN):
        send_json(connection, {"type": "auth_response", "status": "success"})
        return True
    send_json(connection, {"type": "auth_response", "status": "failed"})
    return False

def handle_client(connection, address):
    log(f"Connection from {address}")
    print(f"
[+] TCP/TLS connection from {address}")
    try:
        if not authenticate(connection):
            print("[!] Authentication failed")
            log(f"Authentication failed: {address}")
            return
        print("[+] Client authenticated
Type 'help' to see commands.")
        log(f"Authentication successful: {address}")
        while True:
            command = input("
secure-cli> ").strip().lower()
            if command == "help":
                print("
Allowed commands:")
                for item in sorted(ALLOWED_COMMANDS): print(f"  {item}")
                print("  help
  exit")
                continue
            if command == "exit":
                send_json(connection, {"type": "command", "command": "exit"})
                log(f"Session closed by server: {address}")
                break
            if command not in ALLOWED_COMMANDS:
                print("[!] Command is not allowed.")
                continue
            send_json(connection, {"type": "command", "command": command})
            log(f"Command sent: {command}")
            response = receive_json(connection)
            if not response:
                print("[!] No response received.")
                break
            print("
" + response.get("output", ""))
            log(f"Result received for: {command}")
    except Exception as error:
        print(f"
[!] Client error: {error}")
        log(f"Client error {address}: {error}")
    finally:
        try: connection.shutdown(socket.SHUT_RDWR)
        except: pass
        connection.close()
        log(f"Connection closed: {address}")
        print("
[*] Connection closed.")

def main():
    print("=" * 60 + "
       SECURE REMOTE CLI SERVER
" + "=" * 60)
    print(f"[*] Server IP : {HOST}
[*] Port      : {PORT}
[*] Protocol  : TCP + TLS
[*] Commands  : Allowlisted
" + "=" * 60)
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls_context.minimum_version = ssl.TLSVersion.TLSv1_2
    tls_context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"
[*] Listening on {HOST}:{PORT}
[*] Waiting for authorized client...")
    log(f"Server started on port {PORT}")
    try:
        while True:
            raw_connection, address = server_socket.accept()
            try:
                tls_connection = tls_context.wrap_socket(raw_connection, server_side=True)
                handle_client(tls_connection, address)
            except ssl.SSLError as error:
                print(f"[!] TLS error: {error}")
                log(f"TLS error: {error}")
                raw_connection.close()
    except KeyboardInterrupt:
        print("
[*] Server stopped.")
    finally:
        server_socket.close()
        log("Server stopped")

if __name__ == "__main__":
    main()
