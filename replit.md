# Discord Bot

## Overview
A feature-rich Discord bot with custom prefix management, role-based permissions, leveling system, moderation tools, and fun commands.

## Recent Changes
- **November 28, 2025**: Added role reaction system
  - New `/addrolereact` command for creating role selection messages
  - Support for both button and reaction modes
  - Button mode: Users click buttons to toggle roles
  - Reaction mode: Users react/unreact to add/remove roles
  - Persistent buttons that work after bot restarts
  - Role hierarchy validation to prevent permission errors
- **November 28, 2025**: Fixed DM crash bugs
  - Added guild null checks to all slash commands to prevent crashes when used in DMs
  - Commands now properly respond with "This command can only be used in a server"
- **November 15, 2025**: Added protection system and bot warning prevention
  - New `k!protection` command to protect users from warnings
  - Support for both timed and infinite protection
  - Bots cannot be warned (custom error message)
  - Protected users cannot be warned
  - Background task to automatically remove expired protections
- **November 13, 2025**: Converted to Python implementation
  - Rewrote entire bot in Python using discord.py
  - Custom prefix system (default: `?`)
  - Permission hierarchy (Bot Owner, Owner, Admin)
  - Leveling system with XP tracking
  - Moderation commands (mute, ban, kick, warn)
  - Fun commands (say, sayembed, slap)
  - Welcome DM system
  - Data persistence with JSON files
  - Secure token management via environment variables

## Project Architecture

### File Structure
- `bot.py` - Main Python bot file with all commands and event handlers
- `requirements.txt` - Python dependencies
- `data/` - Persistent storage directory
  - `config.json` - Server prefixes, permissions, welcome DM settings
  - `levels.json` - User XP and message tracking
  - `mutes.json` - Active mute tracking for auto-unmute
  - `protections.json` - User protection tracking with expiration
  - `role_reactions.json` - Role reaction/button configurations

### Key Features

#### Permission System
- **Bot Owner**: Set automatically on first run, can add owners
- **Owner** (⭐): Can add admins and use all commands
- **Admin** (🛡️): Can use moderation and fun commands

#### Leveling System
- Users gain 1 XP per message (1 message/second rate limit)
- Level 1: 10 messages, Level 2: 20 messages, Level 3: 30 messages, etc.
- Maximum level: 1000
- Commands: `?levelstats`, `?levelboard`

#### Moderation
- Staff protection: Cannot moderate users with Administrator, Ban, Kick, or Timeout permissions
- Bot admin bypass: Bot admins/owners cannot be moderated
- Bot protection: Bots cannot be warned or moderated
- User protection: Users can be protected from warnings for a specific duration or infinitely
- All actions send DM notifications to affected users
- Mute system uses Discord's timeout feature with auto-unmute scheduling
- Protection system with automatic expiration tracking

### Commands

**Prefix Management**
- `?newprefix <prefix>` - Change server prefix (Admin+)

**Permissions**
- `?addowner <@user>` - Add server owner (Bot Owner only)
- `?addadmin <@user>` - Add server admin (Owner+)

**Leveling**
- `?levelstats` - View your level and progress
- `?levelboard` - View top 10 users by level

**Moderation**
- `?mute <@user> <duration> [reason]` - Timeout user (Admin+ or Moderate Members permission)
- `?ban <@user> [reason]` - Ban user (Admin+ or Ban Members permission)
- `?kick <@user> [reason]` - Kick user (Admin+ or Kick Members permission)
- `?warn <@user> <reason>` - Warn user (Admin+ or Moderate Members permission)
- `k!protection <@user> <duration/inf>` - Protect user from warnings (Admin+ or Moderate Members permission)

**Role Reactions**
- `/addrolereact <message_id> <description> <mode> <roles>` - Create role selection message (Admin+ or Manage Roles)
  - Button mode: Creates buttons that toggle roles on click
  - Reaction mode: Creates reactions that add/remove roles
  - Format: `"Label:@Role,Label2:@Role2"` for buttons or `"🎮:@Role,🎨:@Role2"` for reactions

**Fun**
- `?say <message>` - Make bot say something (Admin+)
- `?sayembed <title> | <description>` - Send embed message (Admin+)
- `?slap <@user>` - Slap a user with random intensity

**System**
- `?addit` - Toggle welcome DM system (Admin+)
- `?beta` - Display bot beta status and features

## Bot Token
The bot token is stored in the environment variable `DISCORD_BOT_TOKEN`. The bot will not start without this environment variable set.

## Dependencies
- discord.py v2.3.2 - Discord API wrapper for Python
- Background task loops for auto-unmute and protection expiration functionality
