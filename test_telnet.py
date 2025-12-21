import socket
import time

def test_telnet():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('localhost', 2323))

        # Receive welcome message
        data = sock.recv(4096).decode('utf-8', errors='ignore')
        print("=== Received from server ===")
        print(data[:500])

        # Send guest login
        sock.send(b"guest\n")
        time.sleep(0.5)

        # Receive response
        data = sock.recv(4096).decode('utf-8', errors='ignore')
        print("\n=== After login ===")
        print(data[:500])

        sock.close()
        print("\n✅ Telnet connection successful!")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_telnet()
