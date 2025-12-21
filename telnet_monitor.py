"""
Telnet Connection Monitor
リアルタイムでTelnet接続状態を監視するAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import os

app = FastAPI(title="MTBBS Telnet Monitor API")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 接続情報ファイル
CONNECTIONS_FILE = "telnet_connections.json"

def load_connections():
    """接続情報を読み込む"""
    if os.path.exists(CONNECTIONS_FILE):
        try:
            with open(CONNECTIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"connections": [], "last_updated": None}
    return {"connections": [], "last_updated": None}

@app.get("/")
def root():
    return {
        "name": "MTBBS Telnet Monitor API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/telnet/connections")
def get_connections():
    """現在のTelnet接続一覧を取得"""
    data = load_connections()
    return {
        "connections": data.get("connections", []),
        "total": len(data.get("connections", [])),
        "last_updated": data.get("last_updated")
    }

@app.get("/api/telnet/stats")
def get_stats():
    """Telnet接続統計情報"""
    data = load_connections()
    connections = data.get("connections", [])

    # ユーザーレベル別集計
    level_counts = {}
    for conn in connections:
        level = conn.get("level", 0)
        level_counts[level] = level_counts.get(level, 0) + 1

    # 認証状態別集計
    authenticated = sum(1 for c in connections if c.get("authenticated", False))
    guest = sum(1 for c in connections if c.get("user_id") == "guest")

    return {
        "total_connections": len(connections),
        "authenticated_users": authenticated,
        "guest_users": guest,
        "level_distribution": level_counts,
        "last_updated": data.get("last_updated")
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("MTBBS Telnet Monitor API")
    print("=" * 60)
    print("Monitor API: http://localhost:8001")
    print("Connections: http://localhost:8001/api/telnet/connections")
    print("Stats: http://localhost:8001/api/telnet/stats")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8001)
