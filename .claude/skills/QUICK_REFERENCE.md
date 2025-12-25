# MTBBS-Linux Debug Skill - Quick Reference

## Quick Commands

### Most Common Issues

```bash
# Japanese text garbled
/mtbbs-debug telnet --issue "Japanese characters garbled"

# Can't login
/mtbbs-debug session --issue "authentication failed"

# Mail not showing
/mtbbs-debug mail --issue "sent mail not appearing"

# Messages not loading
/mtbbs-debug board --issue "board shows no messages"

# Slow performance
/mtbbs-debug performance --issue "slow response"

# Check error logs
/mtbbs-debug error

# Full system check
/mtbbs-debug all
```

## Category Reference

| Category | Use For | Example Issue |
|----------|---------|---------------|
| `telnet` | Connection, encoding, protocol | "Characters garbled", "Can't connect" |
| `database` | Data not found, schema issues | "Table not found", "Data missing" |
| `session` | Login, permissions, state | "Can't login", "Permission denied" |
| `mail` | Mail sending, reading, deleting | "Mail not delivered", "Can't read" |
| `board` | Messages, search, display | "No messages", "Search broken" |
| `error` | Exceptions, crashes, logs | "Server crashed", "Exception in logs" |
| `performance` | Slow operations, bottlenecks | "Slow loading", "High CPU" |
| `all` | General health check | "System check before deployment" |

## Quick Diagnostic Commands

### Database
```bash
# Check tables
sqlite3 data/mtbbs.db "SELECT name FROM sqlite_master WHERE type='table';"

# Check mail count
sqlite3 data/mtbbs.db "SELECT COUNT(*) FROM mail;"

# Integrity check
sqlite3 data/mtbbs.db "PRAGMA integrity_check;"
```

### Server
```bash
# Check if running
ps aux | grep python | grep telnet

# Check port
netstat -an | grep :23

# View logs
tail -f logs/mtbbs.log
```

### Testing
```bash
# Connect to server
telnet localhost 23

# Health check
python scripts/health_check.py

# Test encoding
python backend/scripts/check_message_encoding.py
```

## Common Fixes

### Issue: Mail table not found
```bash
python backend/scripts/migrate_add_mail_table.py --db data/mtbbs.db
```

### Issue: User can't login
```bash
sqlite3 data/mtbbs.db "UPDATE users SET is_active=1 WHERE user_id='admin';"
```

### Issue: Server won't start
```bash
# Check if port is in use
netstat -an | grep :23

# Kill existing process
pkill -f "python.*telnet"

# Start server
python backend/app/main.py
```

### Issue: Encoding problems
1. Configure Telnet client to use CP932 or Shift-JIS
2. Verify `self.encoding = 'cp932'` in telnet_handler.py
3. Test with TeraTerm (recommended) or PuTTY

## Debug Workflow

1. **Identify Issue** → Choose category
2. **Run Debug Skill** → `/mtbbs-debug <category> --issue "description"`
3. **Follow Diagnostics** → Run suggested commands
4. **Apply Fix** → Implement recommended solution
5. **Verify** → Test to confirm fix works
6. **Document** → Update troubleshooting guide if new issue

## File Quick Access

**Critical Files**:
```
backend/app/protocols/telnet_handler.py    # Command handling
backend/app/services/mail_service.py       # Mail operations
backend/app/services/board_service.py      # Board operations
backend/app/utils/rate_limiter.py          # Rate limiting
logs/mtbbs.log                             # Application logs
data/mtbbs.db                              # Database
```

**Configuration**:
```
backend/app/resources/messages_ja.py       # Messages and version
backend/app/core/database.py               # Database config
```

**Scripts**:
```
scripts/health_check.py                    # Health check
backend/scripts/migrate_add_mail_table.py  # Mail table migration
backend/scripts/check_message_encoding.py  # Encoding check
```

## Troubleshooting Decision Tree

```
Problem detected
│
├─ Can't connect to server?
│  └─ /mtbbs-debug telnet
│
├─ Login issues?
│  └─ /mtbbs-debug session
│
├─ Data not showing?
│  ├─ Mail? → /mtbbs-debug mail
│  └─ Messages? → /mtbbs-debug board
│
├─ Errors in logs?
│  └─ /mtbbs-debug error
│
├─ Slow performance?
│  └─ /mtbbs-debug performance
│
└─ General issues?
   └─ /mtbbs-debug all
```

## Emergency Commands

```bash
# Stop server immediately
pkill -9 -f "python.*telnet"

# Backup database before fixes
cp data/mtbbs.db data/mtbbs.db.backup.$(date +%Y%m%d_%H%M%S)

# Restore database
cp data/mtbbs.db.backup.YYYYMMDD_HHMMSS data/mtbbs.db

# Clear all logs
> logs/mtbbs.log

# Restart from scratch
python backend/scripts/init_db.py
python backend/app/main.py
```

## Support Resources

- **Implementation Guide**: `claudedocs/STEP1-3_IMPLEMENTATION_GUIDE.md`
- **Compatibility Report**: `claudedocs/COMMAND_COMPATIBILITY_REPORT.md`
- **README**: `README.md`
- **CHANGELOG**: `CHANGELOG.md`

---

**Tip**: Always run `/mtbbs-debug all` after major changes to verify system health!
