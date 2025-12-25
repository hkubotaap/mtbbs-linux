# -*- coding: utf-8 -*-
"""
MTBBS Japanese Message Templates

Original MTBBS Ver 3.02
Copyright (C) 1997.10.9 By Yoshihiro Myokan

MTBBS-Linux
Copyright (C) 2025 kuchan
"""

MTBBS_VERSION = "0.1α"

# Main Menu Message
MAIN_MENU = """MTBBS Ver {version} - Main Menu
{time}  {user_id} / {handle}
================================================================================
[N]ews   新着を読む        [R]ead   メッセージを読む      [E]nter  メッセージ書込
[N@]     全て News         [M]ail   メールを読む          [P]ost   投稿
--------------------------------------------------------------------------------
[A]pply  ユーザ登録        [H]elp   ヘルプ                [U]sers  ユーザリスト
[W]ho    ログイン中        [C]hat   チャット              [I]nstall 設定
--------------------------------------------------------------------------------
[Q]uit   ログアウト        [#]      ステータス
"""

# File Board Menu
FILE_MENU = """MTBBS Ver {version} - File Board
========================================
[L]ist  ファイルリスト
[I]nfo  情報
[K]ill  削除
[?]     ヘルプ
[0]     終了
"""

# Read Menu
READ_MENU = """Read Menu
========================================
[R]ead    順番に読む
[I]ndiv   個別指定
[S]earch  検索
[L]ist    一覧
[#]       ステータス
[?]       ヘルプ
[0]       終了
"""

# Install Menu
INSTALL_MENU = """Install Menu (設定)
========================================
[P] パスワード変更
[H] ハンドル名変更
[M] メモ編集
[0] 終了
"""

# Chat Menu
CHAT_MENU = """Chat Menu
========================================
[W]ho      ログイン中
[T]elegram 電報送信
[C]hat     チャット編集
[M]ain     メインへ
[?]        ヘルプ
//,^^      終了
"""

# Sysop Menu
SYSOP_MENU = """                                                                 / sysop menu
------------------------------------------------------------------------------
[A] ユーザ登録     | [Q] クイック(記録なし)| [-] ボード設定リスト  | [-]ボード数変更
[-] 利用権変更 | [-] ファイル削除    | [L] レベル変更      | [-]メッセージ登録
[R] 設定再読込   | [-] 認証        | [K] チャンネル開放  | [0]end
"""

# Version Message
HOST_VERSION = """
 ホストプログラム MTBBS Version {version}
 Copyright(C) 1997.10,1999.8 By Yoshihiro Myokan
 Linux Port 2024

-------------------------------------------------------
 MTBBS Linux - Modern BBS System with Telnet & Web UI
-------------------------------------------------------
"""

# Help Message
HELP_MESSAGE = """
<< 困ったらここへ...ヘルプです >>

[基本コマンド]
  N  - 新着記事を読む
  R  - メッセージボードを読む
  E  - メッセージを書き込む
  M  - メールを読む
  P  - メールを投稿
  Q  - ログアウト

[情報]
  A  - ユーザ登録
  H  - ヘルプ（この画面）
  U  - ユーザリスト
  W  - ログイン中のユーザ
  Y  - システム情報

[その他]
  C  - チャット・電報
  F  - ファイルボード
  I  - 個人設定
  #  - ステータス表示
"""

# Chat Room Opening
CHAT_ROOM_OPENING = """

======================================================
        チャットルームへようこそ (^^)/
======================================================
"""

# Opening Message
OPENING_MESSAGE = """
KANJI CODE = [SJIS]

今日は{date} {weekday}曜日です。
========================================
MTBBSへようこそ！
========================================

<<< {access_count}番目のログイン者です >>>

# ゲストは guest と入力
"""

# Logout Message
LOGOUT_MESSAGE = """
{handle} さん、ログアウトありがとうございました。
またお越しください。
(^^)/~
"""

# Login Message
LOGIN_MESSAGE = """
{handle}さん、{greeting}
ご来訪ありがとうございます。

"""

# File Board Info
FILE_BOARD_INFO = """ ファイルボードへようこそ(^^)
-------------------------------------------------------------------------
  現在TELNETでのX,Y,ZMODEM,MLINKの転送はできません。ご注意ください。
  なお、各自経由でファイルボードにアクセスできるようになっていますので
インターネット経由での接続の方はご利用ください。
  各自経由を使用したアップロードも可能となっています。
-------------------------------------------------------------------------
"""

# System Info
SYSINFO_MESSAGE = """【 機種名 】MTBBS NET
【 担当者 】SYSOP
【 回線種 】Telnet(インターネット)
【 ホスト 】
【        】MTBBS Version {version}
【 人数等 】0人 (00/00/00現在)
【運営形態】オンラインサイトアップ
【サービス】メール、メッセージボード、ファイルボード、電報、チャット..etc
"""

# 日本の格言・諺
KOTOWAZA = [
    "どっこいしょ",
    "がんばれDelphi",
    "継続は力なり",
    "念には念を入れよ",
    "口は災いの元",
    "備えあれば憂いなし",
    "人の上に人を造らず人の下に人を造らず",
    "笑って暮らすも一生泣いて暮らすも一生",
    "出る杭は打たれる",
    "必要は発明の母",
    "人の可能性は無限大",
    "人は見かけによらぬもの",
    "人の振り見て我が振り直せ",
    "人の噂も七十五日",
    "善は急げ",
    "急がば回れ",
    "好きこそものの上手なれ",
    "負けるが勝ち",
    "ローマは一日にしてならず",
    "今日の一針明日の十針",
    "歳月人を待たず",
    "雨降って地固まる",
    "一度あることは二度ある",
    "井の中の蛙大海を知らず",
    "海老で鯛を釣る",
    "親しき仲にも礼儀あり",
    "習うより慣れよ",
    "早起きは三文の徳",
    "三人寄れば文殊の知恵"
]

# Template variable replacements
def format_message(template: str, **kwargs) -> str:
    """Format message template with provided variables"""
    return template.format(**kwargs)
