# -*- coding: utf-8 -*-
"""
MTBBS Japanese Message Templates
Original MTBBS Ver 3.02
Copyright (C) 1997.10.9 By Yoshihiro Myokan
"""

MTBBS_VERSION = "4.0.0-linux"

# Main Menu Message
MAIN_MENU = """MTBBS Ver {version} - Main Menu   {time}  {user_id} / {handle}
BOARD/MAIL -------------  INFORMATION ------------  OTHERS -----------------
[N]ews  新着記事を読む| [A]pply   ユーザ登録    | [Q]uit    接続を切る
[N@]    全て News       | [H]elp    コマンド一覧  | [I]nstall ユーザ設定
[R]ead  メッセージを読む| [U]sers   ユーザリスト  | [W]ho     ログイン中
[E]nter メッセージの書込| [L]og     ログ記録      | [C]hat    チャット・電報
[K]ill  メッセージの削除| pr[O]file プロフィール  | [T]elegram 電報
[#]     ステータスの表示| s[Y]sinfo ホストの紹介  | e[X]who   IPアドレス表示
[M]ail  メール読む      | [_]       Version 表示  | [F]ile    ファイルボード
[P]ost  投稿            | [S]ysop   SYSOP呼び出し | [FN]      新ファイル
"""

# File Board Menu
FILE_MENU = """MTBBS Ver {version} - File Board Menu
 コマンド ---------------- ダウンロード ------------  アップロード------------
  [L]ist    ファイルリスト| [ZD] : Zmodem Download   | [FU] : FTP経由Upload
  [K]ill    削除          | [YD] : Ymodem Download   | [ZU] : Zmodem Upload
  [I]nfo    情報          | [MD] : Mlink  Download   | [YU] : Ymodem Upload
  [?]       Fileメニュー  | [XD] : Xmodem Download   | [MU] : Mlink  Upload
  [0]       終了          | [D]  : ファイルを読む    | [XU] : Xmodem Upload
"""

# Read Menu
READ_MENU = """                                                                / read menu
COMMANDS ---------------  COMMANDS ---------------  番号指定 ---------------
[R]ead       順番に読む  | [#]     status          |  n   n番から順番に読む
[I]ndividual 個別の番号  | [?]     メニュー        | -n   n番から逆に読む
[S]earch     検索        | [0]     終了            |  0   最初から順番に読む
[L]ist      タイトルのみ |                         |[RET] 最後から逆に読む
"""

# Install Menu
INSTALL_MENU = """                                                               / install menu
---------------------------------- INSTALL -----------------------------------
[-]:改行コード  | [P]:パスワード   | [H]:ハンドル名    | [M]:メモ
[N]:新着リスト   | [-]:ESC 使用     | [-]:YMODEM-g     | [B]:電報着信表示
[-]:漢字表示    | [-]:漢字範囲     | [-]:カナ変換表示  | [R]:既読日付
[A]:ログイン通知 |                   |                   | [0]:end
"""

# Chat Menu
CHAT_MENU = """                                                            / chat menu
-------------------------------- CHAT ----------------------------------
[W]ho     ログイン中 | [E]cho   ECHO ON/OFF | [T]elegram 電報を送る
pr[O]file プロフィール | [?]      この画面    | [N]ow      現在時刻
[M]ain    MAINコマンド | [S]ysop  SYSOP 呼出  | //,^^      終了
[C]hat    チャット編集  |                      |
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

 KANJI CODE = [UTF-8]

今日は{date} {weekday}曜日です。
---------------------------------------------------------
MTBBSへようこそ！
MTBBSはTelnetで接続可能なホストプログラムです。
Python + FastAPIによって開発されLinuxで動作します。
---------------------------------------------------------

<<< あなたは、{access_count}番目のログイン者です >>>

# ゲストでログインする場合は guest と入力してください.
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
