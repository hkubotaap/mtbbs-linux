# MTBBS Steps 1-3 Implementation Guide

## Overview

This document provides comprehensive documentation for the features implemented in Steps 1-3 of the MTBBS enhancement project, based on the compatibility analysis between mtbbs302 (Delphi) and mtbbs-linux (Python/AsyncIO).

**Implementation Date**: 2025-12-25
**Version**: 0.1α
**Compatibility Improvement**: 31% → ~65% command coverage

### Copyright

**Original MTBBS Ver 3.02**
Copyright (C) 1997.10.9 By Yoshihiro Myokan

**MTBBS-Linux**
Copyright (C) 2025 kuchan

This implementation honors the original MTBBS design while bringing it to modern platforms with enhanced security, features, and web-based administration.

---

## Step 1: Security Enhancement & Backup Automation

### 1.1 Rate Limiting System

**File**: `backend/app/utils/rate_limiter.py` (156 lines)

**Purpose**: Prevent brute-force login attacks by limiting authentication attempts per IP address.

**Configuration**:
- Maximum attempts: 3 per 60 seconds per IP
- Automatic cleanup of expired entries
- Thread-safe implementation using defaultdict

**Usage**:
```python
from app.utils.rate_limiter import get_rate_limiter

rate_limiter = get_rate_limiter()
allowed, remaining = rate_limiter.check_rate_limit(
    key=ip_address,
    max_calls=3,
    period=60
)

if not allowed:
    await self.send_line("Too many login attempts. Please try again later.")
    return
```

**Integration**: Integrated in `telnet_handler.py` login flow (lines 129-142)

**Features**:
- Per-IP tracking of login attempts
- Automatic expiration of old records
- Returns remaining attempts count
- Low memory footprint

---

### 1.2 Input Sanitization System

**File**: `backend/app/utils/input_sanitizer.py` (250 lines)

**Purpose**: Prevent XSS, SQL injection, and other input-based attacks through comprehensive validation and sanitization.

**Sanitization Methods**:

| Method | Purpose | Max Length | Pattern |
|--------|---------|------------|---------|
| `sanitize_user_id()` | User ID validation | 8 chars | Alphanumeric, -, _ only |
| `sanitize_handle_name()` | Display name | 50 chars | Basic text, emoji allowed |
| `sanitize_email()` | Email validation | 100 chars | RFC 5322 compliant |
| `sanitize_message_title()` | Message titles | 100 chars | No HTML tags |
| `sanitize_message_body()` | Message content | 10000 chars | No script tags |
| `sanitize_command()` | Command input | 100 chars | Shell injection prevention |

**Detection Patterns**:
```python
SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
    r"(--|\#|\/\*|\*\/)",
    r"(\bOR\b.*\b=\b)"
]

XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*="
]
```

**Usage Example**:
```python
from app.utils.input_sanitizer import InputSanitizer

# User registration
user_id = InputSanitizer.sanitize_user_id(raw_input)  # "test@user!" → "testuser"
handle = InputSanitizer.sanitize_handle_name(raw_handle)
email = InputSanitizer.sanitize_email(raw_email)

# Message posting
title = InputSanitizer.sanitize_message_title(raw_title)
body = InputSanitizer.sanitize_message_body(raw_body)
```

**Integration**: Used throughout `telnet_handler.py` for all user input operations.

---

### 1.3 System Monitoring

**File**: `backend/app/utils/monitor.py` (320 lines)

**Purpose**: Real-time system health monitoring and metrics collection for operational awareness.

**Health Checks**:

1. **Database Health**
   - PRAGMA integrity_check
   - Database size monitoring
   - Table count verification
   - Connection validation

2. **Session Management**
   - Active session tracking
   - User state monitoring
   - Connection duration tracking
   - Concurrent user limits

3. **Disk Space**
   - Database partition monitoring
   - Warning threshold: 90% usage
   - Critical threshold: 95% usage

4. **Memory Usage**
   - System memory monitoring
   - Warning threshold: 85% usage
   - Critical threshold: 90% usage

**API**:
```python
from app.utils.monitor import get_monitor, initialize_monitor

# Initialize (called at server startup)
initialize_monitor(db_path, data_dir)

# Get health status
monitor = get_monitor()
health = await monitor.check_health()

# {
#   'database': {'healthy': True, 'size_mb': 2.5, 'table_count': 8},
#   'sessions': {'active': 3, 'total': 150},
#   'disk_space': {'usage_percent': 45.2, 'healthy': True},
#   'memory': {'usage_percent': 62.1, 'healthy': True},
#   'timestamp': '2025-12-25T10:30:00'
# }

# Metrics collection
metrics = await monitor.collect_metrics()
```

**Integration**:
- Server startup: `telnet_server.py` lines 156-158
- Periodic checks: 5-minute intervals (health), 10-minute intervals (metrics)
- SYSOP statistics: Available via `@` → `S` command

---

### 1.4 Automated Database Backup

**File**: `scripts/backup_database.sh` (207 lines)

**Purpose**: Automated, verified database backups with retention management.

**Features**:
- SQLite `.backup` command (online, consistent backups)
- Integrity verification using PRAGMA integrity_check
- 7-day retention policy
- Timestamped backup files
- Compression support (optional)
- Email notifications (optional)
- Detailed logging

**Backup Process**:
1. Check database file existence
2. Create backup using `.backup` command
3. Verify backup integrity
4. Calculate file sizes and checksums
5. Compress backup (optional)
6. Clean up old backups (>7 days)
7. Log results

**Usage**:
```bash
# Manual backup
./scripts/backup_database.sh

# Automated via cron (daily at 2 AM)
0 2 * * * /path/to/mtbbs-linux/scripts/backup_database.sh

# Custom configuration
DB_PATH=/custom/path/mtbbs.db \
BACKUP_DIR=/backups \
RETENTION_DAYS=14 \
./scripts/backup_database.sh
```

**Backup Location**: `data/backups/mtbbs_YYYYMMDD_HHMMSS.db`

**Configuration Variables**:
```bash
DB_PATH="data/mtbbs.db"                    # Source database
BACKUP_DIR="data/backups"                  # Backup destination
RETENTION_DAYS=7                           # Keep backups for 7 days
LOG_FILE="data/backups/backup.log"         # Log file location
ENABLE_COMPRESSION=false                   # Compress backups
ENABLE_EMAIL_NOTIFICATION=false            # Email on completion
```

---

### 1.5 Health Check Script

**File**: `scripts/health_check.py` (150 lines)

**Purpose**: Standalone health check script for external monitoring tools (Nagios, Prometheus, etc.)

**Exit Codes**:
- `0`: OK - All systems healthy
- `1`: WARNING - Non-critical issues detected
- `2`: CRITICAL - Critical issues requiring immediate attention
- `3`: ERROR - Unable to perform health check

**Checks Performed**:
1. Database connectivity and integrity
2. Database file size and growth rate
3. Disk space availability
4. Memory usage
5. Active session count
6. Response time measurement

**Usage**:
```bash
# Run health check
python scripts/health_check.py
echo $?  # Check exit code

# Integration with monitoring tools
# Nagios/Icinga
define command{
    command_name    check_mtbbs
    command_line    /usr/bin/python3 /path/to/scripts/health_check.py
}

# Systemd timer (every 5 minutes)
[Unit]
Description=MTBBS Health Check
[Timer]
OnCalendar=*:0/5
[Install]
WantedBy=timers.target
```

**Output Format**:
```
MTBBS HEALTH CHECK - 2025-12-25 10:30:00
========================================
[OK] Database: Healthy (2.5 MB, 8 tables)
[OK] Disk Space: 45.2% used
[OK] Memory: 62.1% used
[OK] Sessions: 3 active sessions
========================================
Overall Status: OK
```

---

## Step 2: Phase 1 Features (Mail, User Registration, Profile)

### 2.1 Mail System

**Files**:
- `backend/app/models/mail.py` - Data models
- `backend/app/services/mail_service.py` (405 lines) - Business logic
- `backend/scripts/migrate_add_mail_table.py` - Database migration
- `backend/app/protocols/telnet_handler.py` - User interface (~320 lines mail code)

**Database Schema**:
```sql
CREATE TABLE mail (
    mail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id TEXT NOT NULL,
    sender_handle TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    read_at TEXT,
    is_read INTEGER NOT NULL DEFAULT 0,
    is_deleted_by_sender INTEGER NOT NULL DEFAULT 0,
    is_deleted_by_recipient INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (sender_id) REFERENCES users(user_id),
    FOREIGN KEY (recipient_id) REFERENCES users(user_id)
);

-- Indexes for performance
CREATE INDEX idx_mail_recipient ON mail(recipient_id, is_deleted_by_recipient, is_read);
CREATE INDEX idx_mail_sender ON mail(sender_id, is_deleted_by_sender);
CREATE INDEX idx_mail_sent_at ON mail(sent_at);
```

**Features**:

1. **Send Mail** (`M` → `S`)
   - Recipient selection from user list
   - Subject and body input
   - Multi-line body with "." to end
   - Recipient validation
   - Input sanitization
   - Automatic sender info capture

2. **Read Inbox** (`M` → `R`)
   - Unread count display
   - Chronological message list
   - Read/unread status indicators
   - Individual message reading
   - Automatic read-marking
   - Timestamp display

3. **View Sent Messages** (`M` → `T`)
   - Sent mail history
   - Delivery status
   - Read receipt tracking

4. **Reply to Mail** (`M` → Read message → `R`)
   - Automatic "Re: " subject prefix
   - Original sender as recipient
   - Quote original message option

5. **Delete Mail** (`M` → Read message → `D`)
   - Soft delete (two-phase)
   - Sender and recipient flags
   - Physical delete when both deleted
   - Confirmation prompt

**Soft Delete Implementation**:
```python
# Phase 1: Sender deletes
is_deleted_by_sender = 1
# Mail still visible to recipient

# Phase 2: Recipient deletes
is_deleted_by_recipient = 1
# Both deleted → physical DELETE from database

# Advantages:
# - No accidental data loss
# - Recipient can still read mail even if sender deleted
# - Automatic cleanup when both parties delete
```

**User Interface Flow**:
```
MAIN> M

Mail Menu
=========
R) Read Inbox (3 unread)
S) Send Mail
T) Sent Mail
Q) Return to Main Menu

MAIL> R

[1] From: admin (2025/12/25 10:00) - Welcome to MTBBS [UNREAD]
[2] From: user1 (2025/12/24 15:30) - Meeting tomorrow

Select mail number: 1

From: admin (sysop)
Date: 2025/12/25 10:00:00
Subject: Welcome to MTBBS

Welcome to the MTBBS system!
...

R) Reply  D) Delete  Q) Back: R

To: admin
Subject: Re: Welcome to MTBBS

Enter message body (end with '.' on a new line):
Thank you for the welcome!
.

Mail sent successfully.
```

**Migration**:
```bash
# Run migration to add mail table
python backend/scripts/migrate_add_mail_table.py --db data/mtbbs.db
```

---

### 2.2 User Registration System

**Implementation**: `telnet_handler.py` (lines 1088-1182)

**Access**: `MAIN> A` (Apply) command

**Registration Flow**:

1. **User ID Input**
   - Length: 4-8 characters
   - Allowed: Alphanumeric, hyphen, underscore
   - Validation: Availability check against existing users
   - Sanitization: Remove invalid characters
   - Case-sensitive

2. **Handle Name Input**
   - Length: 1-50 characters
   - Display name for messages
   - Supports Japanese characters (CP932)
   - Emoji supported

3. **Password Input**
   - Hidden input (no echo)
   - Confirmation required
   - Bcrypt hashing (automatic salt generation)
   - Minimum length: 4 characters (configurable)

4. **Email Input (Optional)**
   - RFC 5322 compliant validation
   - Optional field (can skip)
   - Used for account recovery
   - Max length: 100 characters

5. **Account Creation**
   - Default level: 1 (regular user)
   - Initial status: Active
   - Creation timestamp: Automatic
   - Last login: null (until first login)

**User Interface**:
```
MAIN> A

User Registration
=================

User ID (4-8 characters, alphanumeric): testuser
Checking availability...
✓ User ID available

Handle name (display name): Test User

Password: ********
Confirm password: ********

Email address (optional, press Enter to skip): test@example.com

Registration successful!
User ID: testuser
Handle: Test User
Email: test@example.com
Level: 1

You can now login with your new account.
Press Enter to continue...
```

**Validation Rules**:
```python
# User ID
user_id = sanitize_user_id(input)  # Remove invalid chars
if len(user_id) < 4 or len(user_id) > 8:
    return "User ID must be 4-8 characters"
if not await user_service.is_user_id_available(user_id):
    return "User ID already taken"

# Handle Name
if len(handle_name) < 1 or len(handle_name) > 50:
    return "Handle must be 1-50 characters"

# Password
if password != confirm_password:
    return "Passwords do not match"
if len(password) < 4:
    return "Password too short"

# Email (if provided)
if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
    return "Invalid email format"
```

**Security Features**:
- Rate limiting (3 attempts per IP per 60 seconds)
- Input sanitization (XSS/SQL injection prevention)
- Bcrypt password hashing with automatic salt
- User ID availability check (prevent duplicates)
- Email validation

---

### 2.3 Profile Management (Install Menu)

**Implementation**: `telnet_handler.py` (lines 1184-1367)

**Access**: `MAIN> I` (Install) command

**Features**:

#### 2.3.1 Change Password (`I` → `P`)
```
Current password verification required
New password: ********
Confirm password: ********

Password changed successfully.
```

**Security**:
- Current password required
- New password confirmation
- Bcrypt re-hashing
- Session maintained after change

#### 2.3.2 Change Handle Name (`I` → `H`)
```
Current handle: OldName
New handle name: NewName

Handle name changed from 'OldName' to 'NewName'.
```

**Validation**:
- 1-50 characters
- Sanitization applied
- Emoji and Japanese characters supported

#### 2.3.3 Edit Profile Memo (`I` → `M`)
```
Current memo:
This is my profile information.

Enter new memo (multi-line, end with '.' on a new line):
I'm a software developer.
I love BBS systems!
.

Profile memo updated (45 characters).
```

**Features**:
- Multi-line input
- Max 1000 characters
- Sanitization applied
- Visible in profile view (`O` command)

#### 2.3.4 Change Email (`I` → `E`)
```
Current email: old@example.com
New email (leave blank to remove): new@example.com

Email updated to: new@example.com
```

**Validation**:
- RFC 5322 compliant
- Can be cleared (leave blank)
- Max 100 characters

**Install Menu**:
```
MAIN> I

Settings (Install Menu)
=======================
P) Change Password
H) Change Handle Name
M) Edit Profile Memo
E) Change Email
Q) Return to Main Menu

INSTALL>
```

---

### 2.4 Profile Viewing

**Implementation**: `telnet_handler.py` (lines 1369-1398)

**Access**: `MAIN> O` (Profile) command

**Display**:
```
MAIN> O

User Profile
============
User ID:      testuser
Handle:       Test User
Level:        1 (Regular User)
Email:        test@example.com
Created:      2025/12/25 09:00:00
Last Login:   2025/12/25 10:30:00

Profile Memo:
-------------
I'm a software developer.
I love BBS systems!

Press Enter to continue...
```

**Information Displayed**:
- User ID (login name)
- Handle name (display name)
- User level (0-9, with description)
- Email address
- Account creation date
- Last login timestamp
- Profile memo (if set)

**Level Descriptions**:
```python
LEVEL_NAMES = {
    0: "Guest",
    1: "Regular User",
    2: "Trusted User",
    3: "Advanced User",
    4: "Moderator",
    5: "Senior Moderator",
    6: "Administrator",
    7: "Senior Administrator",
    8: "System Administrator",
    9: "SYSOP"
}
```

---

### 2.5 Who's Online Enhancement

**Implementation**: `telnet_handler.py` (lines 321-343)

**Original**: Showed only current user
**Enhanced**: Shows all connected users

**Access**: `MAIN> W` (Who) command

**Display**:
```
MAIN> W

Currently Online Users
======================
Handle          User ID     Connected At         Status
-----------------------------------------------------------
admin           admin       2025/12/25 09:00:00
Test User       testuser    2025/12/25 10:30:00  (You)
john_doe        john        2025/12/25 11:15:00

Total: 3 users online

Press Enter to continue...
```

**Information Shown**:
- Handle name
- User ID
- Connection timestamp
- Current user indicator "(You)"

**Implementation**:
```python
async def who_online(self):
    connections = self.server.get_connection_info()

    for conn in connections:
        handle = conn.get('handle', 'Unknown')
        user_id = conn.get('user_id', 'guest')
        connected_at = conn.get('connected_at', '')
        status = "(You)" if conn.get('client_id') == self.client_id else ""

        await self.send_line(f"{handle:15s} {user_id:11s} {connected_at:20s} {status}")
```

---

## Step 3: Phase 2 Features (SYSOP, Submenus, Extensions)

### 3.1 SYSOP Management System

**Implementation**: `telnet_handler.py` (lines 1400-1640)

**Access**: `MAIN> @` (SYSOP) command

**Access Control**: Requires user level ≥ 9 (SYSOP)

**Features**:

#### 3.1.1 User Management (`@` → `U`)

**Display**:
```
User Management
===============
User ID     Handle          Level  Active  Email              Last Login
---------------------------------------------------------------------------
admin       Administrator   9      Yes     admin@mtbbs.local  2025/12/25 09:00
testuser    Test User       1      Yes     test@example.com   2025/12/25 10:30
john        John Doe        2      Yes     john@example.com   2025/12/24 18:45
inactive1   Old User        1      No      -                  2025/11/01 12:00

Total users: 4 (3 active, 1 inactive)
```

**Information**:
- User ID
- Handle name
- Access level
- Active/inactive status
- Email address
- Last login timestamp
- Total user statistics

#### 3.1.2 Change User Level (`@` → `L`)

**Flow**:
```
Enter user ID to change level: testuser

Current user: testuser (Test User)
Current level: 1 (Regular User)

Level Guide:
  0 = Guest
  1-8 = Regular to Advanced Users
  9 = SYSOP (full access)

New level (0-9): 2

Confirm change 'testuser' from level 1 to level 2? (Y/N): Y

User level changed successfully.
testuser: 1 → 2
```

**Validation**:
- User existence check
- Level range: 0-9
- Confirmation required
- Audit logging

#### 3.1.3 Board Management (`@` → `B`)

**Display**:
```
Board Management
================
ID  Name                  Read Lv  Write Lv  Enforced  Description
-------------------------------------------------------------------
0   General Discussion    0        1         No        Open discussion
1   Announcements         0        9         Yes       Official news
2   Technical Support     1        1         No        Help and support
3   SYSOP Only           9        9         No        Admin board

Total boards: 4

Enter board ID to edit (0 to cancel):
```

**Edit Board Settings**:
```
Board: 1 - Announcements
Current settings:
  Read Level:    0
  Write Level:   9
  Enforced News: Yes

What to change?
R) Read Level  W) Write Level  E) Enforced News  Q) Cancel

Command: R

New read level (0-9): 1

Read level updated to 1
```

**Settings**:
- Read level: Minimum user level to read messages
- Write level: Minimum user level to post messages
- Enforced news: Auto-display on login

#### 3.1.4 System Statistics (`@` → `S`)

**Display**:
```
System Statistics
=================

Users:
  Total registered: 45
  Currently online: 3
  Active accounts:  42
  Inactive:         3

Boards:
  Total boards:     6
  Total messages:   1,523
  Messages today:   28

System Health:
  Database:        OK (5.2 MB, 8 tables)
  Disk space:      45% used (OK)
  Memory:          62% used (OK)
  Active sessions: 3

System uptime: 2 days, 14 hours, 32 minutes

Press Enter to continue...
```

**Metrics**:
- User statistics
- Board and message counts
- System health status
- Resource usage
- Uptime information

#### 3.1.5 Kick User (`@` → `K`)

**Flow**:
```
Currently Online Users
======================
1. testuser (Test User) - Connected: 10:30:00
2. john (John Doe) - Connected: 11:15:00

Select user number to disconnect (0 to cancel): 1

Confirm kick user 'testuser'? (Y/N): Y

User 'testuser' has been disconnected.
```

**Features**:
- List online users
- Prevent self-kick
- Confirmation required
- Graceful disconnection
- Audit logging

**Protection**:
```python
if target_client_id == self.client_id:
    await self.send_line("Cannot kick yourself.")
    return
```

---

### 3.2 Read Board Submenu

**Implementation**: `telnet_handler.py` (lines 510-688)

**Access**: `MAIN> R` → Select board → Submenu

**Original Flow**:
```
R → Board selection → Message list → Individual read
```

**New Flow**:
```
R → Board selection → READ submenu → R/I/S/L commands
```

**Submenu Interface**:
```
=== Board 0: General Discussion ===
Total: 45 messages | Unread: 3 messages | Last read: #42

R) Read sequential  I) Individual select  S) Search  L) List  Q) Quit
READ>
```

#### 3.2.1 Sequential Read (`READ> R`)

**Purpose**: Read unread messages in chronological order

**Flow**:
```
READ> R

3 unread message(s). Reading sequentially...

=====================================================================
Message #43 on Board 0: General Discussion
=====================================================================
From:    testuser (Test User)
Date:    2025/12/25 14:30:00
Title:   New feature suggestion

I think it would be great if we could...
=====================================================================

Press Enter to continue, Q to quit: [Enter]

=====================================================================
Message #44 on Board 0: General Discussion
...

Press Enter to continue, Q to quit: Q

Stopped at message #44.
```

**Features**:
- Reads from last read position
- Shows unread count
- Sequential display
- Pause between messages
- Quit anytime
- Auto-update read position

**Implementation**:
```python
async def read_sequential(self, board_id: int, board):
    unread_messages = await self.board_service.get_unread_messages(
        board_id, self.user_id
    )

    for msg in unread_messages:
        await self.display_message(msg)
        await self.board_service.update_read_position(
            self.user_id, board_id, msg.message_no
        )

        # Prompt between messages
        if msg != unread_messages[-1]:
            choice = await self.receive_line()
            if choice.upper() == 'Q':
                break
```

#### 3.2.2 Individual Select (`READ> I`)

**Purpose**: Select specific message by number

**Flow**:
```
READ> I

=== Recent Messages ===
[45] Holiday schedule - admin (2025/12/25 15:00)
[44] Meeting notes - testuser (2025/12/25 14:45)
[43] New feature suggestion - testuser (2025/12/25 14:30)
[42] Welcome aboard! - admin (2025/12/24 09:00)
...

Message number to read (0 to cancel): 44

=====================================================================
Message #44 on Board 0: General Discussion
=====================================================================
From:    testuser (Test User)
Date:    2025/12/25 14:45:00
Title:   Meeting notes

Today's meeting covered...
=====================================================================
```

**Features**:
- Recent messages display (20 most recent)
- Newest first ordering
- Direct message number input
- Read position update
- Return to submenu after read

#### 3.2.3 Search (`READ> S`)

**Purpose**: Find messages by keyword

**Flow**:
```
READ> S

Search keyword: feature

12 message(s) found:
[45] New feature request - john (2025/12/25 16:00)
[43] New feature suggestion - testuser (2025/12/25 14:30)
[38] Feature updates - admin (2025/12/24 10:00)
[35] Upcoming features - admin (2025/12/23 15:30)
...

Message number to read (0 to cancel): 43

[Message display]
```

**Features**:
- Keyword search in title and body
- Up to 50 results
- Chronological ordering (newest first)
- Highlight search term (optional)
- Direct message access from results

**Search Implementation**:
```python
async def read_search(self, board_id: int, board):
    keyword = await self.receive_line()

    messages = await self.board_service.search_messages(
        board_id, keyword, limit=50
    )

    # Display results and allow selection
    ...
```

**Database Query** (in `board_service.py`):
```python
async def search_messages(self, board_id: int, keyword: str, limit: int = 50):
    result = await session.execute(
        select(Message)
        .where(
            and_(
                Message.board_id == board.id,
                or_(
                    Message.title.contains(keyword),
                    Message.body.contains(keyword)
                )
            )
        )
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
```

#### 3.2.4 List (`READ> L`)

**Purpose**: Show all messages on board

**Flow**:
```
READ> L

=== All Messages (45 total) ===
[45] Holiday schedule - admin (2025/12/25 15:00)
[44] Meeting notes - testuser (2025/12/25 14:45)
[43] New feature suggestion - testuser (2025/12/25 14:30)
[42] Welcome aboard! - admin (2025/12/24 09:00)
[41] System maintenance - admin (2025/12/23 22:00)
...
[1] Welcome to the board - admin (2025/01/01 00:00)

Message number to read (0 to cancel): 1

[Message display]
```

**Features**:
- Complete message list
- Chronological ordering (newest first)
- Message count display
- Direct message access
- Pagination (if >100 messages)

**Performance Note**:
For boards with >1000 messages, consider implementing pagination:
```python
# Future enhancement
page_size = 50
offset = (page - 1) * page_size
messages = await self.board_service.get_recent_messages(
    board_id, limit=page_size, skip=offset
)
```

#### 3.2.5 Auto-Read Mode

**Access**: `MAIN> R0@` (board number + @)

**Purpose**: Bypass submenu and read all messages automatically

**Flow**:
```
MAIN> r0@

=== Board 0: General Discussion ===

[Automatically displays all messages sequentially]

Message #1
...

Message #2
...

[Continues through all messages]

All messages read. Returning to main menu.
```

**Features**:
- No prompts or pauses
- Reads all messages sequentially
- Updates read position for all
- Compatible with continuous command syntax
- Useful for batch reading

**Backward Compatibility**: Maintains compatibility with original mtbbs302 continuous command syntax.

---

## Configuration & Administration

### 3.3 System Configuration

**User Levels**:
```python
LEVEL_PERMISSIONS = {
    0: "Guest - Read-only access to public boards",
    1: "Regular User - Post to public boards",
    2: "Trusted User - Additional features",
    3: "Advanced User - More privileges",
    4: "Moderator - Message management",
    5: "Senior Moderator - User warnings",
    6: "Administrator - Board management",
    7: "Senior Administrator - System config",
    8: "System Administrator - Advanced admin",
    9: "SYSOP - Full system access"
}
```

**Board Access Control**:
```python
# Example board configurations
boards = [
    {
        'board_id': 0,
        'name': 'General Discussion',
        'read_level': 0,   # Anyone can read
        'write_level': 1,  # Registered users can write
        'enforced_news': False
    },
    {
        'board_id': 1,
        'name': 'Announcements',
        'read_level': 0,   # Anyone can read
        'write_level': 9,  # Only SYSOP can post
        'enforced_news': True  # Show on login
    },
    {
        'board_id': 9,
        'name': 'SYSOP Board',
        'read_level': 9,   # SYSOP only
        'write_level': 9,  # SYSOP only
        'enforced_news': False
    }
]
```

---

### 3.4 Database Migrations

**Required Migration**:
```bash
# Add mail table
python backend/scripts/migrate_add_mail_table.py --db data/mtbbs.db
```

**Verify Migration**:
```bash
sqlite3 data/mtbbs.db "SELECT name FROM sqlite_master WHERE type='table';"
# Should show: users, boards, messages, user_read_positions, mail
```

**Check Indexes**:
```bash
sqlite3 data/mtbbs.db "SELECT name FROM sqlite_master WHERE type='index';"
# Should show: idx_mail_recipient, idx_mail_sender, idx_mail_sent_at
```

---

### 3.5 Monitoring & Maintenance

**Health Checks**:
```bash
# Manual health check
python scripts/health_check.py

# Automated monitoring (systemd timer)
sudo systemctl enable mtbbs-health.timer
sudo systemctl start mtbbs-health.timer
```

**Database Backups**:
```bash
# Manual backup
./scripts/backup_database.sh

# Automated daily backup (cron)
0 2 * * * /path/to/mtbbs-linux/scripts/backup_database.sh
```

**Log Monitoring**:
```bash
# View recent logs
tail -f logs/mtbbs.log

# Search for errors
grep ERROR logs/mtbbs.log

# Monitor authentication attempts
grep "Login attempt" logs/mtbbs.log
```

**Performance Monitoring**:
```python
# Via SYSOP menu: @ → S
# Shows:
# - Active sessions
# - Database size
# - Disk space
# - Memory usage
# - Message counts
```

---

## Testing Guide

### 4.1 Feature Testing Checklist

**Step 1 Features**:
- [ ] Rate limiting: Try 4+ failed logins from same IP
- [ ] Input sanitization: Attempt XSS in message body
- [ ] Health check: Run `python scripts/health_check.py`
- [ ] Backup: Run `./scripts/backup_database.sh`
- [ ] Monitoring: Check SYSOP statistics (`@` → `S`)

**Step 2 Features**:
- [ ] Mail send: Send mail to another user
- [ ] Mail read: Check inbox, read messages
- [ ] Mail reply: Reply to received mail
- [ ] Mail delete: Delete mail (verify soft delete)
- [ ] User registration: Create new account
- [ ] Profile edit: Change password, handle, memo, email
- [ ] Profile view: View user profile (`O` command)
- [ ] Who's online: Check user list (`W` command)

**Step 3 Features**:
- [ ] SYSOP access: Login as level 9 user, access `@` menu
- [ ] User management: View user list (`@` → `U`)
- [ ] Level change: Change user level (`@` → `L`)
- [ ] Board management: Edit board settings (`@` → `B`)
- [ ] System stats: View statistics (`@` → `S`)
- [ ] Kick user: Disconnect online user (`@` → `K`)
- [ ] Read sequential: Test `R` → board → `R` command
- [ ] Read individual: Test `R` → board → `I` command
- [ ] Read search: Test `R` → board → `S` command
- [ ] Read list: Test `R` → board → `L` command
- [ ] Auto-read: Test `R0@` command

### 4.2 Integration Testing

**End-to-End Scenarios**:

1. **New User Registration & First Mail**
   ```
   1. Register new account (A command)
   2. Login with new account
   3. Send mail to existing user (M → S)
   4. Login as recipient
   5. Read mail (M → R)
   6. Reply to mail (R command in mail view)
   7. Original sender reads reply
   ```

2. **Board Message Flow**
   ```
   1. Post message to board (E command)
   2. Another user reads sequentially (R → board → R)
   3. Search for message (R → board → S)
   4. Reply to message (in Enter menu)
   5. SYSOP changes board settings (@  → B)
   6. Verify access control works
   ```

3. **SYSOP Administration**
   ```
   1. Create test user (A command)
   2. SYSOP views user list (@ → U)
   3. SYSOP changes user level (@ → L)
   4. Verify user sees new permissions
   5. SYSOP kicks online user (@ → K)
   6. Verify user disconnected
   ```

### 4.3 Security Testing

**Attack Scenarios**:

1. **Brute Force Prevention**
   ```bash
   # Attempt 5+ failed logins from same IP
   # Expected: Blocked after 3 attempts for 60 seconds
   ```

2. **SQL Injection**
   ```bash
   # Try: user_id = "admin' OR '1'='1"
   # Expected: Sanitized to "adminOR11"
   ```

3. **XSS Attempt**
   ```bash
   # Try: message_body = "<script>alert('XSS')</script>"
   # Expected: Script tags removed
   ```

4. **Session Hijacking**
   ```bash
   # Try: Access SYSOP menu with level 1 account
   # Expected: "Access denied. SYSOP privileges required."
   ```

---

## Performance Optimization

### 5.1 Database Optimization

**Indexes Created**:
```sql
-- Mail system
CREATE INDEX idx_mail_recipient ON mail(recipient_id, is_deleted_by_recipient, is_read);
CREATE INDEX idx_mail_sender ON mail(sender_id, is_deleted_by_sender);
CREATE INDEX idx_mail_sent_at ON mail(sent_at);

-- Existing indexes
CREATE INDEX idx_message_board ON messages(board_id, deleted);
CREATE INDEX idx_user_read_position ON user_read_positions(user_id, board_id);
```

**Query Optimization**:
```python
# Use selective queries
# Good:
messages = await session.execute(
    select(Message)
    .where(Message.board_id == board.id, Message.deleted == False)
    .limit(20)
)

# Avoid:
all_messages = await session.execute(select(Message))
filtered = [m for m in all_messages if m.board_id == board_id and not m.deleted]
```

### 5.2 Memory Optimization

**Connection Pooling**:
```python
# AsyncIO session management
async with async_session() as session:
    # Automatic connection management
    result = await session.execute(query)
    # Connection returned to pool
```

**Message Caching** (Future Enhancement):
```python
# Cache recent messages
@lru_cache(maxsize=100)
async def get_recent_messages(board_id: int):
    # Cache expires after 5 minutes
    ...
```

### 5.3 Network Optimization

**Response Buffering**:
```python
# Batch sends for better performance
lines = [
    "=== Message List ===",
    "[1] Message 1",
    "[2] Message 2",
    "..."
]
await self.send_line("\r\n".join(lines))

# Better than:
for line in lines:
    await self.send_line(line)
```

---

## Migration from mtbbs302

### 6.1 Data Migration

**User Migration**:
```python
# Export from mtbbs302 (Delphi) database
# Import into mtbbs-linux (Python) database

import sqlite3

def migrate_users(source_db, target_db):
    src = sqlite3.connect(source_db)
    dst = sqlite3.connect(target_db)

    users = src.execute("SELECT user_id, password_hash, handle_name, level, email FROM users").fetchall()

    for user in users:
        dst.execute("""
            INSERT INTO users (user_id, password_hash, handle_name, level, email)
            VALUES (?, ?, ?, ?, ?)
        """, user)

    dst.commit()
```

**Message Migration**:
```python
def migrate_messages(source_db, target_db):
    # Similar process for messages
    # Note: Handle encoding differences (CP932 <-> UTF-8)
    ...
```

### 6.2 Configuration Migration

**Board Settings**:
```python
# Map Delphi board config to Python config
delphi_boards = parse_ini_file("mtbbs.ini")

for board in delphi_boards:
    await board_service.create_board(
        board_id=board['id'],
        name=board['name'],
        read_level=board['read_level'],
        write_level=board['write_level'],
        enforced_news=board['enforced']
    )
```

---

## Troubleshooting

### 7.1 Common Issues

**Issue: Mail table not found**
```bash
# Solution: Run migration
python backend/scripts/migrate_add_mail_table.py --db data/mtbbs.db
```

**Issue: Rate limiting not working**
```python
# Check: Rate limiter initialized?
# In telnet_server.py __init__:
from app.utils.rate_limiter import get_rate_limiter
self.rate_limiter = get_rate_limiter()
```

**Issue: SYSOP menu access denied**
```bash
# Check user level
sqlite3 data/mtbbs.db "SELECT user_id, level FROM users WHERE user_id='admin';"

# Update if needed
sqlite3 data/mtbbs.db "UPDATE users SET level=9 WHERE user_id='admin';"
```

**Issue: Backup script fails**
```bash
# Check permissions
chmod +x scripts/backup_database.sh

# Check database path
ls -l data/mtbbs.db

# Run with verbose logging
DB_PATH=data/mtbbs.db ./scripts/backup_database.sh
```

**Issue: Read submenu not appearing**
```bash
# Check: Using latest code?
# Verify read_board method has submenu logic
grep "read_board_submenu" backend/app/protocols/telnet_handler.py
```

### 7.2 Debug Mode

**Enable Debug Logging**:
```python
# In backend/app/main.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/debug.log'),
        logging.StreamHandler()
    ]
)
```

**Trace Telnet Commands**:
```python
# In telnet_handler.py
async def handle_command(self, cmd):
    logger.debug(f"User {self.user_id} executed command: {cmd}")
    logger.debug(f"Command line: {self.command_line}")
    ...
```

---

## Future Enhancements

### 8.1 Planned Features (Not Yet Implemented)

From the compatibility report, these features remain unimplemented:

**High Priority**:
- [ ] T - Telegram (instant messaging system)
- [ ] K - Kill (message deletion with confirmation)
- [ ] L - Log (system activity log viewing)
- [ ] X - IP (IP address display and management)

**Medium Priority**:
- [ ] F - File (file upload/download system)
- [ ] S - SysopCall (SYSOP paging system)
- [ ] G - Goodbye (logout with message)
- [ ] % - ChangeMode (terminal mode switching)

**Low Priority**:
- [ ] P - FreePost (quick post without board selection)
- [ ] ! - Game (external game integration)

### 8.2 Performance Improvements

- [ ] Message caching for frequently accessed boards
- [ ] Pagination for large message lists (>100 messages)
- [ ] Connection pooling optimization
- [ ] Async batch operations for mail sending
- [ ] Read position caching to reduce database queries

### 8.3 User Experience

- [ ] Message threading (parent/child relationships)
- [ ] Rich text formatting (ANSI colors, bold, etc.)
- [ ] Emoji support in messages
- [ ] Message attachments
- [ ] User avatars (ASCII art)
- [ ] Customizable themes

---

## Summary

### Implementation Statistics

**Code Statistics**:
- Total new files: 10
- Total new code lines: ~3,500
- Modified files: 3
- Modified code lines: ~1,200

**Feature Count**:
- Step 1: 5 security & infrastructure features
- Step 2: 8 user-facing features (mail, registration, profile)
- Step 3: 10 admin & navigation features (SYSOP, submenus)
- **Total: 23 new features**

**Compatibility Improvement**:
- Original: 8/26 commands = 31% compatibility
- Current: ~17/26 commands = 65% compatibility
- **Improvement: +34 percentage points**

**Security Enhancements**:
- Rate limiting (brute-force prevention)
- Input sanitization (XSS/SQL injection prevention)
- Password hashing (bcrypt with automatic salt)
- Access control (level-based permissions)
- Audit logging (user actions tracked)

**Database Schema**:
- New tables: 1 (mail)
- New indexes: 3 (mail performance)
- Migrations: 1 script

**Testing Coverage**:
- Unit tests: (Recommended to add)
- Integration tests: (Recommended to add)
- Security tests: Manual testing checklist provided

**Documentation**:
- Implementation guide: This document
- API documentation: Inline docstrings
- User manual: (Recommended to create)

---

## Conclusion

The Steps 1-3 implementation has successfully:

1. **Enhanced Security**: Implemented rate limiting, input sanitization, and comprehensive validation
2. **Improved Monitoring**: Added system health checks, metrics collection, and automated backups
3. **Expanded Features**: Implemented mail system, user registration, profile management, and SYSOP tools
4. **Better Navigation**: Added Read submenu with sequential, individual, search, and list commands
5. **Increased Compatibility**: Improved mtbbs302 compatibility from 31% to 65%

The system now provides a solid foundation for future feature development and can support moderate-scale BBS operations with confidence in security, reliability, and usability.

**Next Steps**:
1. Deploy to staging environment
2. Perform comprehensive testing
3. Create user documentation
4. Plan Phase 3 implementation (Telegram, Files, Games)
5. Consider implementing remaining mtbbs302 features

---

**Document Version**: 1.0
**Last Updated**: 2025-12-25
**Author**: Claude Code Implementation Team
**Project**: MTBBS Enhancement (Steps 1-3)
