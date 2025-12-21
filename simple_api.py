"""
Simple API Server for MTBBS Admin UI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List
import uvicorn

app = FastAPI(title="MTBBS Admin API")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# インメモリデータ
users_db = [
    {"user_id": "admin", "handle_name": "Administrator", "email": "admin@mtbbs.local", "level": 9, "last_login": datetime.now(), "created_at": datetime.now()},
    {"user_id": "test", "handle_name": "TestUser", "email": "test@mtbbs.local", "level": 1, "last_login": datetime.now(), "created_at": datetime.now()},
]

boards_db = [
    {"board_id": 1, "name": "General", "description": "General discussion", "read_level": 0, "write_level": 1, "is_active": True},
    {"board_id": 2, "name": "Announcements", "description": "System announcements", "read_level": 0, "write_level": 5, "is_active": True},
]

messages_db = []

@app.get("/")
def root():
    return {
        "name": "MTBBS Admin API",
        "version": "4.0.0",
        "status": "running",
        "telnet": {
            "host": "localhost",
            "port": 2323,
            "active_connections": 0
        }
    }

@app.get("/api/admin/stats")
def get_stats():
    return {
        "active_users": 0,
        "total_users": len(users_db),
        "total_boards": len(boards_db),
        "total_messages": len(messages_db),
        "telnet_connections": 0
    }

@app.get("/api/admin/users")
def get_users():
    return users_db

@app.get("/api/admin/users/{user_id}")
def get_user(user_id: str):
    for user in users_db:
        if user["user_id"] == user_id:
            return user
    return {"error": "User not found"}

@app.post("/api/admin/users")
def create_user(user_data: dict):
    user = {
        "user_id": user_data.get("user_id"),
        "handle_name": user_data.get("handle_name"),
        "email": user_data.get("email"),
        "level": user_data.get("level", 1),
        "last_login": None,
        "created_at": datetime.now()
    }
    users_db.append(user)
    return user

@app.delete("/api/admin/users/{user_id}")
def delete_user(user_id: str):
    global users_db
    users_db = [u for u in users_db if u["user_id"] != user_id]
    return {"message": "User deleted"}

@app.get("/api/admin/boards")
def get_boards():
    return boards_db

@app.get("/api/admin/boards/{board_id}")
def get_board(board_id: int):
    for board in boards_db:
        if board["board_id"] == board_id:
            return board
    return {"error": "Board not found"}

@app.post("/api/admin/boards")
def create_board(board_data: dict):
    board = {
        "board_id": board_data.get("board_id"),
        "name": board_data.get("name"),
        "description": board_data.get("description"),
        "read_level": board_data.get("read_level", 0),
        "write_level": board_data.get("write_level", 1),
        "is_active": True
    }
    boards_db.append(board)
    return board

@app.delete("/api/admin/boards/{board_id}")
def delete_board(board_id: int):
    global boards_db
    boards_db = [b for b in boards_db if b["board_id"] != board_id]
    return {"message": "Board deleted"}

@app.get("/api/admin/connections")
def get_connections():
    return {"connections": []}

@app.get("/api/bbs/boards")
def list_bbs_boards():
    return [{"board_id": b["board_id"], "name": b["name"], "description": b["description"]} for b in boards_db]

if __name__ == "__main__":
    print("=" * 60)
    print("MTBBS Admin API Server")
    print("=" * 60)
    print("API: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
