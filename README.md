# Discord Bot Setup Instructions

## ⚠️ CRITICAL: Enable Required Bot Intents First!

**The bot will not work until you enable these intents in Discord:**

### Steps to Enable Intents:

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your bot application
3. Click on **Bot** in the left sidebar
4. Scroll down to **Privileged Gateway Intents**
5. **Enable these two required intents:**
   - ✅ **Server Members Intent** (REQUIRED)
   - ✅ **Message Content Intent** (REQUIRED)
6. Click **Save Changes**
7. Come back to Replit - the bot should now connect successfully!

### Why These Intents Are Needed:
- **Message Content Intent**: Allows the bot to read message content for commands
- **Server Members Intent**: Allows the bot to access member information for moderation

---

## First Time Setup

After enabling the intents and starting the bot, **you need to claim bot ownership:**

1. Send `?setbotowner` in any server where the bot is present
2. The first person to use this command becomes the Bot Owner
3. Once set, only you can add server owners with `?addowner <@user>`

---

## Bot Features

### Commands Overview

**Initial Setup**
- `?setbotowner` - Claim bot ownership (first use only)

**Prefix Management**
- `?newprefix <prefix>` - Change the server's command prefix (Admin+)

**Permission Management**
- `?addowner <@user>` - Add a server owner (Bot Owner only)
- `?addadmin <@user>` - Add a server admin (Owner+)

**Leveling System**
- `?levelstats` - View your current level and progress
- `?levelboard` - View the top 10 users by level
- Users gain 1 XP per message (max 1 message/second)
- Level progression: Level 1 = 10 messages, Level 2 = 20 messages, etc.
- Maximum level: 1000

**Moderation Commands**
- `?mute <@user> <duration> [reason]` - Mute a user (Admin+ or Moderate Members permission)
  - Duration examples: `1 minute 30 seconds`, `67 minutes`, `2 hours`, `1 day`
- `?ban <@user> [reason]` - Ban a user (Admin+ or Ban Members permission)
- `?kick <@user> [reason]` - Kick a user (Admin+ or Kick Members permission)
- `?warn <@user> <reason>` - Warn a user (Admin+ or Moderate Members permission)

All moderation actions will:
- Send a DM to the affected user with details
- Prevent actions against staff members (users with Administrator, Ban, Kick, or Timeout permissions)
- Prevent actions against bot admins/owners

**Fun Commands**
- `?say <message>` - Make the bot say something (Admin+)
- `?sayembed <title> | <description>` - Send an embed message (Admin+)
- `?slap <@user>` - Slap a user with random intensity

**System Commands**
- `?addit` - Toggle welcome DMs for new members (Admin+)
- `?beta` - Display bot beta status and features

## Permission Hierarchy

1. **BOT OWNER** ⭐ - Set automatically to the bot owner
   - Can add server owners
   - Bypasses all restrictions

2. **OWNER** ⭐ - Added via `?addowner`
   - Can add admins
   - Can use all commands
   - Bypasses moderation restrictions

3. **ADMIN** 🛡️ - Added via `?addadmin`
   - Can use moderation commands
   - Can use fun commands
   - Bypasses moderation restrictions

## Bot Invite Link

Make sure your bot has these permissions when inviting:
- Send Messages
- Read Message History
- Manage Messages
- Embed Links
- Moderate Members (for mute)
- Ban Members
- Kick Members

Required Permission Integer: `1099511627862`

## Data Storage

The bot stores data in the `data/` directory:
- `config.json` - Server prefixes, permissions, welcome DM settings
- `levels.json` - User XP and leveling data
- `mutes.json` - Active mute tracking for auto-unmute

## Troubleshooting

**Bot not responding to commands:**
- Make sure Message Content Intent is enabled
- Check that the bot has Send Messages permission in the channel
- Verify you're using the correct prefix (default is `?`)

**Moderation commands not working:**
- Ensure the bot's role is higher than the target user's highest role
- Check that the bot has the required permissions (Ban Members, Kick Members, Moderate Members)
- Make sure you're not trying to moderate someone with staff permissions

**Welcome DMs not working:**
- Enable the feature with `?addit`
- Some users may have DMs disabled
