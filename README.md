# Secure Remote CLI

A secure, authenticated, allowlisted Remote Command Line Interface (CLI) built with Python. 

This project demonstrates secure remote administration by establishing an encrypted TCP+TLS tunnel between a Kali Linux server and a Windows client. It features token-based authentication and strictly restricts remote execution to a predefined list of safe commands.

> **⚠️ Disclaimer:** This project is for educational purposes and malware analysis lab environments only. Use only on systems you own or are explicitly authorized to test.

## Features
* **Encrypted Communication:** Uses TLSv1.2+ to prevent eavesdropping and packet sniffing.
* **Token Authentication:** Hardcoded 32-byte secure token prevents unauthorized server connections.
* **Command Allowlisting:** Restricts execution to specific commands (e.g., `whoami`, `ipconfig`), preventing arbitrary remote code execution (RCE).
* **Standalone Payload:** The client is compiled into a portable `.exe` file that requires no dependencies on the target Windows machine.
* **Activity Logging:** Both client and server log connections, authentications, and errors.

## Architecture

- **Server (Listening Post):** Kali Linux (`server.py`)
- **Client (Target):** Windows (`client.exe`)
- **Protocol:** TCP + TLS
- **Default Port:** 8443

---

## 1. Kali Linux Setup (Server)

First, prepare your environment and generate the necessary TLS certificates.

Open your Kali terminal and run:

```bash
# Create project directories
mkdir -p ~/secure-remote-cli/server
mkdir -p ~/secure-remote-cli/logs
cd ~/secure-remote-cli/server

# Generate a 2048-bit RSA private key
openssl genrsa -out server.key 2048

# Generate a self-signed X.509 certificate (valid for 365 days)
openssl req -new -x509 -key server.key -out server.crt -days 365 -subj "/CN=SecureRemoteCLI"
```

Next, generate a secure authentication token:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```
*Copy this token. You will need to paste it into the `AUTH_TOKEN` variable in both `server.py` and `client.py`.*

## 2. Configuration

### Server Configuration (`server.py`)
Ensure your server is set to listen on all interfaces.
```python
HOST = "0.0.0.0"
PORT = 8443
AUTH_TOKEN = "<YOUR_GENERATED_TOKEN>"
```

### Client Configuration (`client.py`)
Find your Kali Linux IP address:
```bash
ip -4 addr
```
Update the client script with your Kali IP and the same authentication token:
```python
SERVER_HOST = "<YOUR_KALI_IP>"
SERVER_PORT = 8443
AUTH_TOKEN = "<YOUR_GENERATED_TOKEN>"
```

## 3. Build the Windows Executable

On your Windows development machine (which must have Python installed):

1. Install PyInstaller:
   ```powershell
   pip install pyinstaller
   ```
2. Compile the Python script into a hidden, standalone executable:
   ```powershell
   python -m PyInstaller --onefile --noconsole --clean client.py
   ```
3. Locate the compiled executable inside the newly created `dist/` folder (`dist\client.exe`).
4. Transfer **only** `client.exe` to your target Windows test machine.

## 4. Usage Instructions

### Step 1: Start the Server
On your Kali Linux machine:
```bash
cd ~/secure-remote-cli/server
python3 server.py
```
*Expected Output:* `[*] Waiting for authorized client...`

### Step 2: Run the Client
On your target Windows machine, simply double-click `client.exe` or run it from the command line. It will run silently in the background.

### Step 3: Execute Commands
Once the client connects and authenticates, your Kali terminal will drop into a custom prompt:
```text
secure-cli>
```

Type `help` to see the allowed commands:
* `whoami`
* `hostname`
* `ipconfig`
* `systeminfo`
* `dir`
* `date`

Type `exit` to safely terminate the TLS session.

## 5. Command Flow

```text
[Kali Server]                         [Windows Client]
      |                                      |
      | --- 1. TCP Connection Request -----> |
      | <------ 2. TLS Handshake --------- > |
      | --- 3. Auth Token Request ---------> |
      | <--- 4. Token Validated (Success) -- |
      |                                      |
      | --- 5. secure-cli> ipconfig -------> |
      |                                      | (Subprocess Execution)
      | <--- 6. Command Output Result ------ |
```

## 6. Troubleshooting

* **Connection Refused / Timeout:** 
  Check if both VMs are on the same NAT Network. On Windows, test the connection to the Kali server using PowerShell: 
  `Test-NetConnection <KALI_IP> -Port 8443`
* **IP Address Changed:** 
  If your Kali IP changes after a reboot, you **must** update `SERVER_HOST` in `client.py` and recompile `client.exe`. Setting a static IP on your Kali VM is highly recommended.
* **Logs:** 
  Check `logs/server.log` on Kali or `client.log` in the same directory as the `.exe` on Windows for detailed error messages.