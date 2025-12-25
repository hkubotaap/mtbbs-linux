# MTBBS-Linux Claude Code Skills

Custom skills for MTBBS-Linux BBS system development and maintenance.

## Available Skills

### `/mtbbs-debug` - MTBBS Debugging System

Comprehensive debugging and diagnostics tool for MTBBS-Linux.

**Categories**:
- `telnet` - Telnet protocol, connections, encoding issues
- `database` - Database queries, integrity, migrations
- `session` - User sessions, authentication, state management
- `mail` - Mail system, sending/receiving, soft delete
- `board` - Message boards, reading, posting, search
- `error` - Error log analysis, exception traces
- `performance` - Performance profiling, slow queries, bottlenecks
- `all` - Comprehensive system health check

**Quick Examples**:
```bash
# Debug Japanese character encoding issues
/mtbbs-debug telnet --issue "Japanese characters garbled"

# Investigate mail not appearing
/mtbbs-debug mail --issue "sent mail not in inbox"

# Analyze slow board loading
/mtbbs-debug performance --issue "slow board loading"

# Comprehensive health check
/mtbbs-debug all
```

**Common Use Cases**:

1. **User Login Issues**
   ```
   /mtbbs-debug session --issue "can't login with correct password"
   ```

2. **Mail System Problems**
   ```
   /mtbbs-debug mail --issue "unread count wrong"
   ```

3. **Message Display Issues**
   ```
   /mtbbs-debug board --issue "messages not showing"
   ```

4. **Performance Problems**
   ```
   /mtbbs-debug performance --issue "board takes 10 seconds to load"
   ```

5. **Error Investigation**
   ```
   /mtbbs-debug error --issue "rate limiter exception in logs"
   ```

## Skill Development

To create a new skill for MTBBS-Linux:

1. Create a new `.md` file in `.claude/skills/`
2. Follow the skill template structure
3. Include description, usage examples, and implementation details
4. Test with `/skill-name` command

### Skill Template

```markdown
# Skill Name

Brief description.

## Description

Detailed description of what the skill does.

## When to Use

List scenarios when this skill should be used.

## Usage

\```
/skill-name [args]
\```

## Implementation

Detailed implementation steps and code examples.
```

## Integration with MTBBS-Linux

These skills are specifically designed for MTBBS-Linux and integrate with:

- **Telnet Server** (`backend/app/protocols/telnet_server.py`)
- **Telnet Handler** (`backend/app/protocols/telnet_handler.py`)
- **Services** (`backend/app/services/*.py`)
- **Utilities** (`backend/app/utils/*.py`)
- **Database** (`data/mtbbs.db`)
- **Logs** (`logs/mtbbs.log`)

## Contributing

To add new skills:

1. Identify common debugging or development tasks
2. Create a skill file with comprehensive documentation
3. Include diagnostic commands and solutions
4. Test thoroughly with real scenarios
5. Update this README with the new skill

---

**Project**: MTBBS-Linux v0.1α
**Copyright**: (C) 2025 kuchan
**Original MTBBS**: (C) 1997.10.9 Yoshihiro Myokan
