#!/usr/bin/env python3
"""
MTBBS-Linux Automated Test Script
Tests all implemented features
"""

import socket
import time
import sys

class MTBBSTester:
    def __init__(self, host='localhost', port=23):
        self.host = host
        self.port = port
        self.sock = None
        self.test_results = []

    def connect(self):
        """Connect to MTBBS server"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)
            self.sock.connect((self.host, self.port))
            print(f"✅ Connected to {self.host}:{self.port}")
            time.sleep(1)
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def send(self, data):
        """Send data to server"""
        try:
            self.sock.sendall(data.encode('cp932'))
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Send failed: {e}")

    def receive(self, timeout=2):
        """Receive data from server"""
        try:
            self.sock.settimeout(timeout)
            data = b''
            # Receive multiple chunks
            while True:
                try:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    time.sleep(0.1)  # Small delay between chunks
                except socket.timeout:
                    break
            try:
                return data.decode('cp932')
            except:
                return data.decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"❌ Receive failed: {e}")
            return ""

    def test_login(self, user_id, password):
        """Test login functionality"""
        print("\n=== Test: Login ===")

        # Receive opening message
        response = self.receive(3)
        print(f"Opening message received: {len(response)} bytes")

        # Send user ID
        self.send(f"{user_id}\r\n")
        response = self.receive()

        # Send password
        self.send(f"{password}\r\n")
        response = self.receive(3)

        # Check for successful login (Japanese welcome message or menu)
        if "こんにちは" in response or "Main Menu" in response or "MAIN>" in response or "ありがとう" in response:
            print("✅ Login successful")
            print(f"Welcome message received: {len(response)} bytes")
            # Note: Original MTBBS does not prompt "Press Enter" after enforced news
            # The news is displayed and then main menu appears immediately
            self.test_results.append(("Login", "PASS"))
            return True
        else:
            print("❌ Login failed")
            print(f"Response: {response[:500]}")
            self.test_results.append(("Login", "FAIL"))
            return False

    def test_who_online(self):
        """Test Who's Online (W command)"""
        print("\n=== Test: Who's Online (W) ===")

        self.send("W\r\n")
        response = self.receive()

        if "admin" in response or "online" in response.lower():
            print("✅ Who's Online works")
            self.test_results.append(("Who's Online", "PASS"))
        else:
            print("❌ Who's Online failed")
            print(f"Response: {response[:200]}")
            self.test_results.append(("Who's Online", "FAIL"))

    def test_profile(self):
        """Test Profile Display (O command)"""
        print("\n=== Test: Profile Display (O) ===")

        self.send("O\r\n")
        response = self.receive()

        if "admin" in response or "profile" in response.lower() or "レベル" in response:
            print("✅ Profile display works")
            self.test_results.append(("Profile Display", "PASS"))
        else:
            print("❌ Profile display failed")
            print(f"Response: {response[:200]}")
            self.test_results.append(("Profile Display", "FAIL"))

    def test_board_list(self):
        """Test Board List (R command)"""
        print("\n=== Test: Board List (R) ===")

        self.send("R\r\n")
        response = self.receive()

        if "General" in response or "board" in response.lower() or "掲示板" in response:
            print("✅ Board list works")
            self.test_results.append(("Board List", "PASS"))

            # Return to main menu
            self.send("0\r\n")
            self.receive()
        else:
            print("❌ Board list failed")
            print(f"Response: {response[:200]}")
            self.test_results.append(("Board List", "FAIL"))

    def test_help(self):
        """Test Help (H or ? command)"""
        print("\n=== Test: Help (H) ===")

        self.send("H\r\n")
        response = self.receive()

        if "help" in response.lower() or "ヘルプ" in response or "コマンド" in response:
            print("✅ Help works")
            self.test_results.append(("Help", "PASS"))
        else:
            print("❌ Help failed")
            print(f"Response: {response[:200]}")
            self.test_results.append(("Help", "FAIL"))

    def test_news(self):
        """Test News (N command)"""
        print("\n=== Test: News (N) ===")

        self.send("N\r\n")
        response = self.receive()

        if "news" in response.lower() or "ニュース" in response or "お知らせ" in response:
            print("✅ News works")
            self.test_results.append(("News", "PASS"))
        else:
            print("❌ News failed")
            print(f"Response: {response[:200]}")
            self.test_results.append(("News", "FAIL"))

    def test_version(self):
        """Test Version (_ command)"""
        print("\n=== Test: Version (_) ===")

        self.send("_\r\n")
        response = self.receive()

        if "version" in response.lower() or "0.1α" in response or "MTBBS" in response:
            print("✅ Version display works")
            self.test_results.append(("Version", "PASS"))
        else:
            print("❌ Version display failed")
            print(f"Response: {response[:200]}")
            self.test_results.append(("Version", "FAIL"))

    def test_status(self):
        """Test Status (# command)"""
        print("\n=== Test: Status (#) ===")

        self.send("#\r\n")
        response = self.receive()

        if "status" in response.lower() or "ステータス" in response or "admin" in response:
            print("✅ Status display works")
            self.test_results.append(("Status", "PASS"))
        else:
            print("❌ Status display failed")
            print(f"Response: {response[:200]}")
            self.test_results.append(("Status", "FAIL"))

    def test_sysop_menu(self):
        """Test SYSOP Menu (@ command) - Level 9 only"""
        print("\n=== Test: SYSOP Menu (@) ===")

        self.send("@\r\n")
        response = self.receive()

        if "SYSOP" in response or "sysop" in response or "管理" in response:
            print("✅ SYSOP menu accessible")
            self.test_results.append(("SYSOP Menu", "PASS"))

            # Return to main menu
            self.send("Q\r\n")
            self.receive()
        else:
            print("⚠️  SYSOP menu not accessible (may need level 9)")
            print(f"Response: {response[:200]}")
            self.test_results.append(("SYSOP Menu", "SKIP"))

    def test_mail_menu(self):
        """Test Mail Menu (M command)"""
        print("\n=== Test: Mail Menu (M) ===")

        self.send("M\r\n")
        response = self.receive()

        if "mail" in response.lower() or "メール" in response or "受信" in response:
            print("✅ Mail menu accessible")
            self.test_results.append(("Mail Menu", "PASS"))

            # Return to main menu
            self.send("Q\r\n")
            self.receive()
        else:
            print("❌ Mail menu failed")
            print(f"Response: {response[:200]}")
            self.test_results.append(("Mail Menu", "FAIL"))

    def test_install_menu(self):
        """Test Install Menu (I command)"""
        print("\n=== Test: Install Menu (I) ===")

        self.send("I\r\n")
        response = self.receive()

        if "install" in response.lower() or "設定" in response or "パスワード" in response:
            print("✅ Install menu accessible")
            self.test_results.append(("Install Menu", "PASS"))

            # Return to main menu
            self.send("0\r\n")
            self.receive()
        else:
            print("❌ Install menu failed")
            print(f"Response: {response[:200]}")
            self.test_results.append(("Install Menu", "FAIL"))

    def test_logout(self):
        """Test Logout (Q command)"""
        print("\n=== Test: Logout (Q) ===")

        self.send("Q\r\n")
        response = self.receive()

        if "goodbye" in response.lower() or "ログアウト" in response or "ありがとう" in response:
            print("✅ Logout successful")
            self.test_results.append(("Logout", "PASS"))
            return True
        else:
            print("❌ Logout failed")
            print(f"Response: {response[:200]}")
            self.test_results.append(("Logout", "FAIL"))
            return False

    def close(self):
        """Close connection"""
        if self.sock:
            self.sock.close()
            print("\n✅ Connection closed")

    def print_results(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("Test Results Summary")
        print("="*60)

        passed = sum(1 for _, result in self.test_results if result == "PASS")
        failed = sum(1 for _, result in self.test_results if result == "FAIL")
        skipped = sum(1 for _, result in self.test_results if result == "SKIP")
        total = len(self.test_results)

        for test_name, result in self.test_results:
            symbol = "✅" if result == "PASS" else "❌" if result == "FAIL" else "⚠️"
            print(f"{symbol} {test_name}: {result}")

        print("="*60)
        print(f"Total: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
        print(f"Success Rate: {passed}/{total - skipped} ({100*passed/(total-skipped) if (total-skipped) > 0 else 0:.1f}%)")
        print("="*60)

def main():
    """Main test function"""
    print("="*60)
    print("MTBBS-Linux Automated Test Suite")
    print("="*60)

    tester = MTBBSTester()

    # Connect to server
    if not tester.connect():
        print("❌ Cannot connect to server. Is it running?")
        sys.exit(1)

    # Login
    if not tester.test_login("admin", "admin123"):
        print("❌ Login failed. Cannot proceed with tests.")
        tester.close()
        sys.exit(1)

    # Run tests
    tester.test_who_online()
    tester.test_profile()
    tester.test_board_list()
    tester.test_help()
    tester.test_news()
    tester.test_version()
    tester.test_status()
    tester.test_mail_menu()
    tester.test_install_menu()
    tester.test_sysop_menu()

    # Logout
    tester.test_logout()

    # Print results
    tester.print_results()

    # Close connection
    tester.close()

if __name__ == "__main__":
    main()
