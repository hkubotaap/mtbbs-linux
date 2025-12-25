# MTBBS-Linux Debug System

Comprehensive debugging and diagnostics tool for MTBBS-Linux BBS system.

## Description

This skill provides systematic debugging capabilities for MTBBS-Linux, covering Telnet protocol issues, database queries, user sessions, mail system, message boards, error logs, and performance analysis.

## When to Use

Use this skill when:
- Investigating Telnet connection or protocol issues
- Debugging database queries or data integrity problems
- Tracing user session behavior or authentication issues
- Troubleshooting mail system delivery or reading problems
- Analyzing message board operations or encoding issues
- Reviewing error logs and stack traces
- Investigating performance bottlenecks or slow operations
- User reports "command not working" or "can't see messages"

## Usage

```
/mtbbs-debug [category] [--issue "description"]
```

**Categories**:
- `telnet` - Telnet protocol, connections, encoding (CP932/UTF-8)
- `database` - Database queries, integrity, migrations
- `session` - User sessions, authentication, state management
- `mail` - Mail system, sending/receiving, soft delete
- `board` - Message boards, reading, posting, search
- `error` - Error log analysis, exception traces
- `performance` - Performance profiling, slow queries, bottlenecks
- `all` - Comprehensive system health check

**Examples**:
```
/mtbbs-debug telnet --issue "Japanese characters garbled"
/mtbbs-debug database --issue "mail table not found"
/mtbbs-debug session --issue "user logged out unexpectedly"
/mtbbs-debug mail --issue "sent mail not appearing in inbox"
/mtbbs-debug board --issue "search returns no results"
/mtbbs-debug error --issue "rate limiter exception"
/mtbbs-debug performance --issue "slow board loading"
/mtbbs-debug all
```

## Debug Process

### Step 1: Issue Classification
Analyze the issue description and classify into appropriate categories:
- Connection/Protocol issues → telnet
- Data not found/incorrect → database
- Authentication/permission → session
- Mail delivery/reading → mail
- Message operations → board
- Exceptions/crashes → error
- Slow operations → performance

### Step 2: Investigation Strategy

#### Telnet Category
1. **Check Telnet Server Status**
   - Read `backend/app/protocols/telnet_server.py`
   - Verify server is running: `ps aux | grep telnet_server`
   - Check port binding: `netstat -an | grep :23`

2. **Encoding Issues (CP932/UTF-8)**
   - Verify encoding in `telnet_handler.py` (self.encoding = 'cp932')
   - Check message encoding: `backend/scripts/check_message_encoding.py`
   - Test with: `telnet localhost 23` and input Japanese characters

3. **Protocol Flow**
   - Trace command handling in `telnet_handler.py:handle_command()`
   - Check command_line parsing (lines 40-50)
   - Verify main_loop() execution (lines 95-200)

4. **Connection Issues**
   - Check active connections: `server.get_connection_info()`
   - Review connection logs in `logs/mtbbs.log`
   - Verify rate limiting isn't blocking: `backend/app/utils/rate_limiter.py`

#### Database Category
1. **Check Database Existence**
   ```bash
   ls -l data/mtbbs.db
   sqlite3 data/mtbbs.db "SELECT name FROM sqlite_master WHERE type='table';"
   ```

2. **Verify Table Schema**
   ```bash
   sqlite3 data/mtbbs.db ".schema mail"
   sqlite3 data/mtbbs.db ".schema users"
   sqlite3 data/mtbbs.db ".schema boards"
   sqlite3 data/mtbbs.db ".schema messages"
   ```

3. **Check Migrations**
   - Review migration scripts in `backend/scripts/migrate_*.py`
   - Verify mail table: `python backend/scripts/migrate_add_mail_table.py --db data/mtbbs.db`

4. **Database Integrity**
   ```bash
   sqlite3 data/mtbbs.db "PRAGMA integrity_check;"
   sqlite3 data/mtbbs.db "PRAGMA foreign_key_check;"
   ```

5. **Query Analysis**
   - Read service files: `backend/app/services/*.py`
   - Check SQLAlchemy queries for performance
   - Look for missing indexes

#### Session Category
1. **Check User Authentication**
   - Read `backend/app/services/user_service.py:authenticate()`
   - Verify password hashing: `UserService.verify_password()`
   - Check user active status in database

2. **Session State Management**
   - Review `telnet_handler.py` session variables (user_id, user_level, handle_name)
   - Check session registration in `telnet_server.py`
   - Verify monitor.register_session() calls

3. **Permission Issues**
   - Check user level: `sqlite3 data/mtbbs.db "SELECT user_id, level FROM users WHERE user_id='<userid>';"`
   - Verify board access levels in `board_service.py`
   - Review SYSOP check (level >= 9)

4. **Rate Limiting**
   - Check `backend/app/utils/rate_limiter.py`
   - Verify attempts: `rate_limiter.check_rate_limit(ip_address, 3, 60)`
   - Clear rate limit if needed

#### Mail Category
1. **Check Mail Table**
   ```bash
   sqlite3 data/mtbbs.db "SELECT COUNT(*) FROM mail;"
   sqlite3 data/mtbbs.db "SELECT * FROM mail WHERE recipient_id='<userid>' LIMIT 5;"
   ```

2. **Soft Delete Investigation**
   - Check delete flags: `is_deleted_by_sender`, `is_deleted_by_recipient`
   - Verify soft delete logic in `mail_service.py:delete_mail()`
   - Check both parties haven't deleted

3. **Mail Service Methods**
   - Read `backend/app/services/mail_service.py`
   - Test send_mail(), get_inbox(), mark_as_read()
   - Verify recipient validation

4. **Mail Commands in Telnet**
   - Review `telnet_handler.py:read_mail()` (lines 750-1050)
   - Check mail menu rendering
   - Verify unread count calculation

#### Board Category
1. **Check Board Configuration**
   ```bash
   sqlite3 data/mtbbs.db "SELECT board_id, name, read_level, write_level FROM boards;"
   ```

2. **Message Retrieval**
   - Review `board_service.py:get_recent_messages()`, `get_all_messages()`
   - Check deleted flag filtering
   - Verify message count

3. **Search Functionality**
   - Test search in `board_service.py:search_messages()`
   - Check keyword matching in title/body
   - Verify LIKE query performance

4. **Read Submenu**
   - Review `telnet_handler.py:read_board_submenu()` (lines 510-688)
   - Check R/I/S/L command handling
   - Verify read position tracking

5. **Encoding Issues**
   - Check message body encoding
   - Run `backend/scripts/check_message_encoding.py`
   - Verify CP932 encoding in database

#### Error Category
1. **Review Error Logs**
   ```bash
   tail -100 logs/mtbbs.log | grep ERROR
   tail -100 logs/mtbbs.log | grep Exception
   tail -100 logs/mtbbs.log | grep Traceback
   ```

2. **Common Error Patterns**
   - Database locked: SQLite concurrent access
   - Encoding errors: CP932/UTF-8 mismatch
   - KeyError: Missing session/user data
   - AttributeError: None object access
   - ImportError: Missing dependencies

3. **Stack Trace Analysis**
   - Identify error location (file:line)
   - Review relevant code section
   - Check for None checks, try/except blocks
   - Verify error handling

4. **Exception Handling**
   - Review try/except blocks in relevant modules
   - Check logger.error() calls
   - Verify proper error propagation

#### Performance Category
1. **Identify Slow Operations**
   - Check logs for slow query warnings
   - Measure operation time with logging
   - Use SQLite EXPLAIN QUERY PLAN

2. **Database Performance**
   ```bash
   sqlite3 data/mtbbs.db "EXPLAIN QUERY PLAN SELECT * FROM messages WHERE board_id=0;"
   sqlite3 data/mtbbs.db ".indexes"
   ```

3. **Index Optimization**
   - Verify indexes on frequently queried columns
   - Check index usage in query plans
   - Add missing indexes if needed

4. **Connection Pooling**
   - Review async_session usage in `backend/app/core/database.py`
   - Check for connection leaks
   - Verify proper session cleanup

5. **Monitoring Metrics**
   - Check system monitor: `backend/app/utils/monitor.py`
   - Review SYSOP statistics (@→S)
   - Run health check: `python scripts/health_check.py`

### Step 3: Diagnostic Commands

Generate specific diagnostic commands based on issue category:

**Telnet**:
```bash
# Test connection
telnet localhost 23

# Check server process
ps aux | grep python | grep telnet

# Monitor connections
watch -n 1 'netstat -an | grep :23'

# Check encoding
python backend/scripts/check_message_encoding.py
```

**Database**:
```bash
# Verify tables
sqlite3 data/mtbbs.db "SELECT name FROM sqlite_master WHERE type='table';"

# Check mail table
sqlite3 data/mtbbs.db "SELECT COUNT(*) FROM mail;"

# Integrity check
sqlite3 data/mtbbs.db "PRAGMA integrity_check;"

# Run migrations
python backend/scripts/migrate_add_mail_table.py --db data/mtbbs.db
```

**Session**:
```bash
# Check user
sqlite3 data/mtbbs.db "SELECT user_id, level, is_active FROM users WHERE user_id='admin';"

# View sessions
# Access @ → S in Telnet for session info

# Test login
telnet localhost 23
# Login: admin / <password>
```

**Mail**:
```bash
# Check mail for user
sqlite3 data/mtbbs.db "SELECT mail_id, sender_id, subject, is_read FROM mail WHERE recipient_id='testuser';"

# Verify soft delete
sqlite3 data/mtbbs.db "SELECT mail_id, is_deleted_by_sender, is_deleted_by_recipient FROM mail WHERE mail_id=1;"

# Test mail service
python -c "
import asyncio
from backend.app.services.mail_service import MailService
ms = MailService('data/mtbbs.db')
print(asyncio.run(ms.get_unread_count('admin')))
"
```

**Board**:
```bash
# Check boards
sqlite3 data/mtbbs.db "SELECT board_id, name, read_level, write_level FROM boards;"

# Check messages
sqlite3 data/mtbbs.db "SELECT COUNT(*) FROM messages WHERE board_id=0 AND deleted=0;"

# Test search
sqlite3 data/mtbbs.db "SELECT message_no, title FROM messages WHERE board_id=0 AND (title LIKE '%test%' OR body LIKE '%test%');"
```

**Error**:
```bash
# Recent errors
tail -100 logs/mtbbs.log | grep ERROR

# Exception traces
tail -200 logs/mtbbs.log | grep -A 10 "Traceback"

# Filter by timestamp
tail -500 logs/mtbbs.log | grep "2025-12-25"
```

**Performance**:
```bash
# Database size
ls -lh data/mtbbs.db

# Query plan
sqlite3 data/mtbbs.db "EXPLAIN QUERY PLAN SELECT * FROM messages WHERE board_id=0 ORDER BY message_no DESC LIMIT 20;"

# Health check
python scripts/health_check.py

# System stats
# Access @ → S in Telnet
```

### Step 4: Solution Recommendations

Based on findings, provide specific solutions:

**Telnet Issues**:
- Server not running → Start: `python backend/app/main.py`
- Port conflict → Check port 23, change if needed
- Encoding errors → Verify CP932, check client encoding settings
- Command not recognized → Check command_handlers dict in telnet_handler.py

**Database Issues**:
- Table not found → Run migration scripts
- Integrity errors → Check foreign keys, run PRAGMA integrity_check
- Slow queries → Add indexes, optimize queries
- Database locked → Reduce concurrent access, use WAL mode

**Session Issues**:
- Authentication failed → Check password hash, verify user active
- Permission denied → Check user level vs required level
- Session lost → Check session registration, verify timeout
- Rate limited → Wait 60 seconds or clear rate limit

**Mail Issues**:
- Mail not found → Check soft delete flags
- Unread count wrong → Verify is_read flag and query logic
- Send failed → Check recipient exists, verify mail service
- Reply broken → Check sender_id extraction, subject prefix

**Board Issues**:
- Messages not shown → Check deleted flag, read_level permission
- Search no results → Verify keyword, check encoding
- Slow loading → Add board_id index, limit message count
- Encoding garbled → Check CP932 encoding, database collation

**Error Handling**:
- Unhandled exceptions → Add try/except blocks
- Missing error logs → Add logger.error() calls
- Stack trace unclear → Add more context in logging
- Repetitive errors → Fix root cause, not symptoms

**Performance Issues**:
- Slow queries → Add indexes, use LIMIT
- High CPU → Profile code, optimize loops
- Memory leak → Check session cleanup, async resource management
- Network latency → Reduce data transfer, implement caching

### Step 5: Verification

After applying fixes, verify the solution:

1. **Reproduce Original Issue**
   - Document exact steps to reproduce
   - Note error messages or unexpected behavior

2. **Apply Fix**
   - Make code changes
   - Run migrations if database changes
   - Restart server if needed

3. **Test Fix**
   - Repeat reproduction steps
   - Verify expected behavior
   - Check for side effects

4. **Regression Testing**
   - Test related functionality
   - Run comprehensive tests
   - Monitor logs for new errors

5. **Document Solution**
   - Add comments to code
   - Update troubleshooting guide
   - Create issue/PR if needed

## Common Issues Reference

### Issue: "Japanese characters appear garbled"
**Category**: telnet
**Diagnosis**:
- Check client encoding (should be CP932 or Shift-JIS)
- Verify server encoding: `self.encoding = 'cp932'` in telnet_handler.py
- Test with different Telnet clients (TeraTerm, PuTTY, Tera Term)

**Solution**:
1. Configure client to use CP932/Shift-JIS encoding
2. Verify database stores text as UTF-8 internally
3. Check encoding conversion in send/receive methods

### Issue: "Mail table not found error"
**Category**: database
**Diagnosis**:
```bash
sqlite3 data/mtbbs.db "SELECT name FROM sqlite_master WHERE type='table' AND name='mail';"
```

**Solution**:
```bash
python backend/scripts/migrate_add_mail_table.py --db data/mtbbs.db
```

### Issue: "User can't login"
**Category**: session
**Diagnosis**:
1. Check user exists: `SELECT * FROM users WHERE user_id='<userid>';`
2. Verify is_active=1
3. Check password hash matches
4. Verify rate limiting not blocking

**Solution**:
- Reset password: Update users SET password_hash=<new_hash>
- Activate account: Update users SET is_active=1
- Clear rate limit: Wait 60 seconds

### Issue: "Sent mail not appearing in inbox"
**Category**: mail
**Diagnosis**:
1. Check mail exists: `SELECT * FROM mail WHERE sender_id='<sender>' ORDER BY sent_at DESC LIMIT 5;`
2. Verify soft delete flags: is_deleted_by_recipient=0
3. Check recipient_id matches
4. Verify inbox query filters

**Solution**:
- Check mail_service.py:get_inbox() query
- Verify recipient_id parameter
- Check is_deleted_by_recipient flag

### Issue: "Search returns no results"
**Category**: board
**Diagnosis**:
1. Check messages exist: `SELECT COUNT(*) FROM messages WHERE board_id=<id>;`
2. Test search query: `SELECT * FROM messages WHERE title LIKE '%<keyword>%';`
3. Verify encoding matches (CP932/UTF-8)
4. Check deleted flag filtering

**Solution**:
- Verify keyword encoding
- Check search_messages() implementation
- Add debug logging to see actual SQL query
- Test with ASCII-only keyword first

### Issue: "Rate limiter blocking legitimate users"
**Category**: session
**Diagnosis**:
1. Check rate_limiter.py configuration (3 attempts/60s)
2. Review login attempt logs
3. Verify IP address extraction

**Solution**:
- Increase max_calls if needed
- Reduce period if too strict
- Add whitelist for admin IPs
- Clear rate limit cache for specific IP

### Issue: "Slow board loading"
**Category**: performance
**Diagnosis**:
1. Check message count: `SELECT COUNT(*) FROM messages WHERE board_id=<id>;`
2. Analyze query plan: `EXPLAIN QUERY PLAN SELECT ...`
3. Check for missing indexes
4. Measure query time

**Solution**:
- Add LIMIT to queries (e.g., recent 20 messages)
- Create index on board_id: `CREATE INDEX idx_message_board ON messages(board_id, deleted);`
- Implement pagination
- Cache frequently accessed boards

## Debug Workflow Template

```markdown
## Issue Debug Report

**Issue**: [Brief description]
**Category**: [telnet|database|session|mail|board|error|performance]
**Reported By**: [User/System]
**Timestamp**: [YYYY-MM-DD HH:MM:SS]

### 1. Reproduction Steps
1. [Step 1]
2. [Step 2]
3. [Expected behavior]
4. [Actual behavior]

### 2. Investigation

**Relevant Files**:
- [file1.py:line]
- [file2.py:line]

**Diagnostic Commands Run**:
```bash
[command 1]
[command 2]
```

**Output**:
```
[output]
```

### 3. Root Cause

[Description of root cause]

**Code Location**: [file.py:line]

### 4. Solution

**Changes Made**:
- [change 1]
- [change 2]

**Code**:
```python
# Before
[old code]

# After
[new code]
```

### 5. Verification

**Test Steps**:
1. [test step 1]
2. [test step 2]

**Result**: ✅ PASS / ❌ FAIL

**Side Effects**: [None / Description]

### 6. Documentation

**Updated Files**:
- [ ] Code comments added
- [ ] Troubleshooting guide updated
- [ ] CHANGELOG.md updated
- [ ] Issue closed / PR created
```

## Advanced Debugging Techniques

### 1. Live Telnet Session Tracing

Add debug logging to trace session flow:

```python
# In telnet_handler.py
async def handle_command(self, cmd):
    logger.debug(f"[SESSION:{self.client_id}] User:{self.user_id} Command:{cmd} Line:{self.command_line}")
    # ... existing code
```

### 2. Database Query Profiling

Use SQLite explain to analyze queries:

```bash
sqlite3 data/mtbbs.db
.timer on
.explain on
SELECT * FROM messages WHERE board_id=0 ORDER BY message_no DESC LIMIT 20;
```

### 3. Async Code Debugging

Add timing to async operations:

```python
import time
start = time.time()
result = await some_async_function()
logger.debug(f"Operation took {time.time() - start:.3f}s")
```

### 4. Memory Profiling

Check for memory leaks:

```python
import tracemalloc
tracemalloc.start()
# ... run operations
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

### 5. Connection Pool Monitoring

Track database connections:

```python
# In database.py
logger.debug(f"Active connections: {engine.pool.size()}")
logger.debug(f"Checked out: {engine.pool.checkedout()}")
```

## Integration with Development Workflow

### Pre-Commit Checks
```bash
# Run before committing
python scripts/health_check.py
python -m pytest tests/
python -m pylint backend/app/**/*.py
```

### Continuous Monitoring
```bash
# Setup monitoring
watch -n 30 'python scripts/health_check.py'

# Monitor logs
tail -f logs/mtbbs.log | grep ERROR

# Monitor connections
watch -n 5 'netstat -an | grep :23 | wc -l'
```

### Automated Testing
```python
# Add to tests/
def test_mail_system():
    """Test mail send/receive/delete"""
    # ... test code

def test_board_search():
    """Test board search functionality"""
    # ... test code
```

## Resources

**Key Files**:
- `backend/app/protocols/telnet_handler.py` - Command handling
- `backend/app/services/*.py` - Business logic
- `backend/app/utils/*.py` - Utilities (rate limiting, monitoring)
- `backend/scripts/*.py` - Maintenance scripts
- `logs/mtbbs.log` - Application logs
- `data/mtbbs.db` - SQLite database

**Documentation**:
- `claudedocs/STEP1-3_IMPLEMENTATION_GUIDE.md` - Implementation guide
- `claudedocs/COMMAND_COMPATIBILITY_REPORT.md` - Command compatibility
- `README.md` - General documentation
- `CHANGELOG.md` - Version history

**Tools**:
- SQLite CLI: `sqlite3 data/mtbbs.db`
- Telnet client: `telnet localhost 23`
- Health check: `python scripts/health_check.py`
- Log viewer: `tail -f logs/mtbbs.log`

---

**Version**: 0.1α
**Last Updated**: 2025-12-25
**Maintained By**: Claude Code + kuchan
