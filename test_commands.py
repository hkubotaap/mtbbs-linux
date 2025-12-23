#!/usr/bin/env python3
"""
MTBBS Command Test Script
テストしたいコマンドを選択して実行できます
"""
import socket
import time
import sys

class MTBBSTester:
    def __init__(self, host='localhost', port=23):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        """Telnetサーバーに接続"""
        print(f"Connecting to {self.host}:{self.port}...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.sock.settimeout(2.0)

        # Opening message受信
        time.sleep(2)
        response = self.recv()
        print("Connected!")
        print("=" * 70)
        return response

    def send(self, data):
        """データ送信"""
        self.sock.sendall(data.encode('utf-8') if isinstance(data, str) else data)

    def recv(self, wait=0.5):
        """データ受信"""
        time.sleep(wait)
        response = b''
        try:
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                response += chunk
        except socket.timeout:
            pass
        return response.decode('utf-8', errors='ignore')

    def login(self, user_id='sysop', password='p'):
        """ログイン"""
        print(f"\n[LOGIN] Logging in as {user_id}...")

        # User ID入力
        self.send(f'{user_id}\r\n')
        response = self.recv(0.5)

        # Password入力
        self.send(f'{password}\r\n')
        response = self.recv(1.5)

        if '登録ありがとうございました' in response or 'こんにちは' in response or 'こんばんは' in response:
            print("✅ Login successful!")
            return True
        else:
            print("❌ Login failed!")
            return False

    def test_command(self, command, description, expected_keywords=None, wait=1.5):
        """コマンドをテスト"""
        print(f"\n{'='*70}")
        print(f"[TEST] {description}")
        print(f"Command: {command}")
        print('-' * 70)

        self.send(f'{command}\r\n')
        response = self.recv(wait)

        # 結果判定
        success = False
        if expected_keywords:
            if isinstance(expected_keywords, str):
                expected_keywords = [expected_keywords]

            found_keywords = [kw for kw in expected_keywords if kw in response]
            if found_keywords:
                print(f"✅ SUCCESS: Found keywords: {found_keywords}")
                success = True
            else:
                print(f"❌ FAILED: Expected keywords not found: {expected_keywords}")

        # Unknown commandチェック
        if 'Unknown command' in response:
            print("❌ FAILED: Unknown command error")
            success = False

        # レスポンス表示（最初の500文字）
        print("\nResponse:")
        print(response[:500])
        if len(response) > 500:
            print("... (truncated)")

        return success, response

    def disconnect(self):
        """切断"""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        print("\n" + "=" * 70)
        print("Disconnected")

def main():
    """メインテスト"""
    tester = MTBBSTester()

    try:
        # 接続
        tester.connect()

        # ログイン
        if not tester.login():
            return

        # テストメニュー
        print("\n" + "=" * 70)
        print("MTBBS Command Test Menu")
        print("=" * 70)
        print("1. Basic Commands (N, R, E, H, W, U, Y, _, #)")
        print("2. Continuous Commands (N@, R0, R0@, E0)")
        print("3. News Commands (N, N@)")
        print("4. Board Commands (R, R0, R0@)")
        print("5. Post Commands (E, E0)")
        print("6. All Tests")
        print("0. Custom Command")
        print("=" * 70)

        choice = input("\nSelect test (0-6): ").strip()

        results = []

        if choice == '1':
            # 基本コマンドテスト
            results.append(tester.test_command('N', 'News command', 'New Messages'))
            results.append(tester.test_command('H', 'Help command', 'HELP'))
            results.append(tester.test_command('U', 'Users command', 'User List'))
            results.append(tester.test_command('W', 'Who online command', 'Online Users'))
            results.append(tester.test_command('Y', 'System info command', 'MTBBS'))
            results.append(tester.test_command('_', 'Version command', 'Version'))
            results.append(tester.test_command('#', 'Status command', 'Status'))

        elif choice == '2':
            # 連続実行コマンドテスト
            results.append(tester.test_command('N@', 'Auto-read news (N@)', '==='))
            results.append(tester.test_command('R0', 'Read board 0 (R0)', ['Board 0', 'info']))

            # R0@テスト用にメッセージがあるか確認
            success, resp = tester.test_command('R0@', 'Auto-read board 0 (R0@)', ['===', 'Board 0']))
            results.append((success, resp))

            results.append(tester.test_command('E0', 'Enter message to board 0 (E0)', 'Title'))
            # E0の後はキャンセル
            tester.send('Test Title\r\n')
            time.sleep(0.3)
            tester.send('Test body\r\n')
            time.sleep(0.3)
            tester.send('.\r\n')
            resp = tester.recv(1.0)
            print("Message posted:", 'posted successfully' in resp)

        elif choice == '3':
            # Newsコマンド詳細テスト
            results.append(tester.test_command('N', 'Normal news (N)', 'New Messages'))
            results.append(tester.test_command('N@', 'Auto-read news (N@)', '==='))

        elif choice == '4':
            # Boardコマンド詳細テスト
            results.append(tester.test_command('R', 'Read board list (R)', 'Message Boards'))
            tester.send('0\r\n')  # Cancel
            tester.recv(0.5)

            results.append(tester.test_command('R0', 'Read board 0 directly (R0)', ['Board 0', 'info']))
            tester.send('0\r\n')  # Cancel message selection
            tester.recv(0.5)

            results.append(tester.test_command('R0@', 'Auto-read board 0 (R0@)', ['===', 'Board']))

        elif choice == '5':
            # 投稿コマンドテスト
            results.append(tester.test_command('E', 'Enter message (E)', 'Message Boards'))
            tester.send('0\r\n')  # Cancel
            tester.recv(0.5)

            results.append(tester.test_command('E0', 'Enter to board 0 directly (E0)', 'Title'))
            tester.send('Test Title\r\n')
            time.sleep(0.3)
            tester.send('Test message body\r\n')
            time.sleep(0.3)
            tester.send('.\r\n')
            resp = tester.recv(1.0)
            print("Message posted:", 'posted successfully' in resp)

        elif choice == '6':
            # 全テスト実行
            print("\n[RUNNING ALL TESTS]")

            # 基本コマンド
            results.append(tester.test_command('N', 'News', 'New Messages'))
            results.append(tester.test_command('N@', 'Auto-read news', '==='))
            results.append(tester.test_command('R0', 'Read board 0', ['Board 0', 'info']))
            tester.send('0\r\n'); tester.recv(0.5)  # Cancel
            results.append(tester.test_command('R0@', 'Auto-read board 0', '==='))
            results.append(tester.test_command('E0', 'Enter to board 0', 'Title'))
            tester.send('.\r\n'); tester.recv(0.5)  # Cancel with empty title
            results.append(tester.test_command('H', 'Help', 'HELP'))
            results.append(tester.test_command('U', 'Users', 'User List'))
            results.append(tester.test_command('W', 'Who online', 'Online Users'))

        elif choice == '0':
            # カスタムコマンド
            custom_cmd = input("Enter command to test: ").strip()
            expected = input("Expected keyword (optional): ").strip()
            results.append(tester.test_command(
                custom_cmd,
                f'Custom command: {custom_cmd}',
                expected if expected else None
            ))

        # テスト結果サマリー
        if results:
            print("\n" + "=" * 70)
            print("TEST SUMMARY")
            print("=" * 70)
            success_count = sum(1 for r in results if r[0])
            total_count = len(results)
            print(f"Passed: {success_count}/{total_count}")
            print(f"Success Rate: {success_count/total_count*100:.1f}%")

            if success_count == total_count:
                print("\n✅ All tests passed!")
            else:
                print(f"\n❌ {total_count - success_count} test(s) failed")

        # 終了
        print("\n[QUIT] Logging out...")
        tester.send('Q\r\n')
        response = tester.recv(1.0)
        print(response[:200])

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tester.disconnect()

if __name__ == '__main__':
    main()
