import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import random

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

def get_command_prefix(bot, message):
    if message.guild is None:
        return '?'
    return get_prefix(message.guild.id)

bot = commands.Bot(command_prefix=get_command_prefix, intents=intents, help_command=None)

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

CONFIG_FILE = DATA_DIR / 'config.json'
LEVELS_FILE = DATA_DIR / 'levels.json'
MUTES_FILE = DATA_DIR / 'mutes.json'
WARNS_FILE = DATA_DIR / 'warns.json'
GAMBLING_FILE = DATA_DIR / 'gambling.json'
AFK_FILE = DATA_DIR / 'afk.json'
PROTECTIONS_FILE = DATA_DIR / 'protections.json'
COMMAND_PENALTIES_FILE = DATA_DIR / 'command_penalties.json'

config = {
    'bot_owner': '',
    'prefixes': {},
    'owners': {},
    'admins': {},
    'welcome_dm': {}
}

levels = {}
active_mutes = {}
warns = {}
gambling_data = {}
afk_users = {}
protections = {}
command_penalties = {}

def load_data():
    global config, levels, active_mutes, warns, gambling_data, afk_users, protections, command_penalties
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                config['bot_owner'] = loaded_config.get('bot_owner', loaded_config.get('botOwner', ''))
                config['prefixes'] = loaded_config.get('prefixes', {})
                config['owners'] = loaded_config.get('owners', {})
                config['admins'] = loaded_config.get('admins', {})
                config['welcome_dm'] = loaded_config.get('welcome_dm', loaded_config.get('welcomeDM', {}))
        if LEVELS_FILE.exists():
            with open(LEVELS_FILE, 'r') as f:
                levels = json.load(f)
        if MUTES_FILE.exists():
            with open(MUTES_FILE, 'r') as f:
                active_mutes = json.load(f)
        if WARNS_FILE.exists():
            with open(WARNS_FILE, 'r') as f:
                warns = json.load(f)
        if GAMBLING_FILE.exists():
            with open(GAMBLING_FILE, 'r') as f:
                gambling_data = json.load(f)
        if AFK_FILE.exists():
            with open(AFK_FILE, 'r') as f:
                afk_users = json.load(f)
        if PROTECTIONS_FILE.exists():
            with open(PROTECTIONS_FILE, 'r') as f:
                protections = json.load(f)
        if COMMAND_PENALTIES_FILE.exists():
            with open(COMMAND_PENALTIES_FILE, 'r') as f:
                command_penalties = json.load(f)
    except Exception as e:
        print(f'Error loading data: {e}')

def save_data():
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        with open(LEVELS_FILE, 'w') as f:
            json.dump(levels, f, indent=2)
        with open(MUTES_FILE, 'w') as f:
            json.dump(active_mutes, f, indent=2)
        with open(WARNS_FILE, 'w') as f:
            json.dump(warns, f, indent=2)
        with open(GAMBLING_FILE, 'w') as f:
            json.dump(gambling_data, f, indent=2)
        with open(AFK_FILE, 'w') as f:
            json.dump(afk_users, f, indent=2)
        with open(PROTECTIONS_FILE, 'w') as f:
            json.dump(protections, f, indent=2)
        with open(COMMAND_PENALTIES_FILE, 'w') as f:
            json.dump(command_penalties, f, indent=2)
    except Exception as e:
        print(f'Error saving data: {e}')

def get_prefix(guild_id):
    return config['prefixes'].get(str(guild_id), '?')

def is_bot_owner(user_id):
    return str(user_id) == config['bot_owner']

def is_owner(guild_id, user_id):
    guild_id = str(guild_id)
    user_id = str(user_id)
    return is_bot_owner(user_id) or (guild_id in config['owners'] and user_id in config['owners'][guild_id])

def is_admin(guild_id, user_id):
    guild_id = str(guild_id)
    user_id = str(user_id)
    return is_owner(guild_id, user_id) or (guild_id in config['admins'] and user_id in config['admins'][guild_id])

def has_staff_permissions(member):
    return (member.guild_permissions.administrator or 
            member.guild_permissions.ban_members or 
            member.guild_permissions.kick_members or 
            member.guild_permissions.moderate_members)

def get_user_badge(guild_id, user_id):
    if is_bot_owner(user_id):
        return 'BOT OWNER ⭐'
    if is_owner(guild_id, user_id):
        return 'OWNER ⭐'
    if is_admin(guild_id, user_id):
        return 'ADMIN 🛡️'
    return ''

def get_messages_for_level(level):
    return level * 10

def get_level_from_xp(xp):
    level = 0
    total_messages = 0
    
    while level < 1000:
        messages_needed = get_messages_for_level(level + 1)
        if total_messages + messages_needed > xp:
            break
        total_messages += messages_needed
        level += 1
    
    return {
        'level': level,
        'messages_in_level': xp - total_messages,
        'messages_needed': get_messages_for_level(level + 1)
    }

def add_xp(guild_id, user_id):
    key = f'{guild_id}-{user_id}'
    if key not in levels:
        levels[key] = {'xp': 0, 'last_message': 0}
    
    if 'last_message' not in levels[key]:
        levels[key]['last_message'] = 0
    
    now = datetime.now().timestamp()
    if now - levels[key]['last_message'] < 1:
        return None
    
    old_level = get_level_from_xp(levels[key]['xp'])['level']
    levels[key]['xp'] += 1
    levels[key]['last_message'] = now
    new_level = get_level_from_xp(levels[key]['xp'])['level']
    save_data()
    
    # Return new level if user leveled up
    if new_level > old_level:
        return new_level
    return None

def parse_duration(duration_str):
    pattern = r'(\d+)\s*(second|sec|s|minute|min|m|hour|h|day|d)s?'
    matches = re.findall(pattern, duration_str.lower())
    
    if not matches:
        return None
    
    total_seconds = 0
    for value, unit in matches:
        value = int(value)
        if unit.startswith('s'):
            total_seconds += value
        elif unit.startswith('m'):
            total_seconds += value * 60
        elif unit.startswith('h'):
            total_seconds += value * 3600
        elif unit.startswith('d'):
            total_seconds += value * 86400
    
    return total_seconds

def split_duration_and_reason(text):
    compact_pattern = r'^\d+\s*(?:second|sec|s|minute|min|m|hour|h|day|d)s?$'
    tokens = text.split()
    duration_tokens = []
    i = 0
    
    while i < len(tokens):
        token = tokens[i]
        
        if re.match(compact_pattern, token, re.IGNORECASE):
            duration_tokens.append(token)
            i += 1
        elif re.match(r'^\d+$', token):
            if i + 1 < len(tokens) and re.match(r'^(?:second|sec|s|minute|min|m|hour|h|day|d)s?$', tokens[i + 1], re.IGNORECASE):
                duration_tokens.extend([token, tokens[i + 1]])
                i += 2
            else:
                return ' '.join(duration_tokens), ' '.join(tokens[i:]) or 'No reason provided'
        else:
            return ' '.join(duration_tokens), ' '.join(tokens[i:]) or 'No reason provided'
    
    return ' '.join(duration_tokens), 'No reason provided'

def format_duration(seconds):
    if seconds == 0:
        return '0 seconds'
    
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f'{days} day{"s" if days != 1 else ""}')
    if hours > 0:
        parts.append(f'{hours} hour{"s" if hours != 1 else ""}')
    if minutes > 0:
        parts.append(f'{minutes} minute{"s" if minutes != 1 else ""}')
    if secs > 0:
        parts.append(f'{secs} second{"s" if secs != 1 else ""}')
    
    return ', '.join(parts)

def is_protected(guild_id, user_id):
    key = f'{guild_id}-{user_id}'
    if key not in protections:
        return False
    
    protection_data = protections[key]
    
    if protection_data.get('infinite', False):
        return True
    
    if protection_data['end_time'] <= datetime.now().timestamp():
        return False
    
    return True

def is_command_banned(user_id):
    user_id_str = str(user_id)
    if user_id_str not in command_penalties:
        return False
    
    penalty_data = command_penalties[user_id_str]
    return penalty_data.get('type') == 'ban'

def is_command_muted(user_id):
    user_id_str = str(user_id)
    if user_id_str not in command_penalties:
        return False
    
    penalty_data = command_penalties[user_id_str]
    if penalty_data.get('type') != 'mute':
        return False
    
    if penalty_data['end_time'] <= datetime.now().timestamp():
        return False
    
    return True

def get_command_penalty_message(user_id):
    user_id_str = str(user_id)
    if user_id_str not in command_penalties:
        return None
    
    penalty_data = command_penalties[user_id_str]
    penalty_type = penalty_data.get('type')
    reason = penalty_data.get('reason', 'No reason provided')
    
    if penalty_type == 'ban':
        return f'❌ You are banned from using bot commands. Reason: {reason}'
    elif penalty_type == 'mute':
        if penalty_data['end_time'] > datetime.now().timestamp():
            time_left = penalty_data['end_time'] - datetime.now().timestamp()
            return f'🔇 You are temporarily muted from using bot commands. Time left: {format_duration(int(time_left))}. Reason: {reason}'
    
    return None

@bot.tree.interaction_check
async def interaction_check(interaction: discord.Interaction) -> bool:
    if interaction.user.bot:
        return True
    
    if is_bot_owner(interaction.user.id):
        return True
    
    if is_command_banned(interaction.user.id):
        message = get_command_penalty_message(interaction.user.id)
        await interaction.response.send_message(message, ephemeral=True)
        return False
    
    if is_command_muted(interaction.user.id):
        message = get_command_penalty_message(interaction.user.id)
        await interaction.response.send_message(message, ephemeral=True)
        return False
    
    return True

@tasks.loop(seconds=30)
async def check_mutes():
    now = datetime.now().timestamp()
    to_remove = []
    
    for key, mute_data in active_mutes.items():
        if mute_data['end_time'] <= now:
            guild_id, user_id = key.split('-')
            try:
                guild = bot.get_guild(int(guild_id))
                if guild:
                    member = await guild.fetch_member(int(user_id))
                    if member and member.is_timed_out():
                        await member.timeout(None)
            except Exception as e:
                print(f'Error unmuting user: {e}')
            to_remove.append(key)
    
    for key in to_remove:
        del active_mutes[key]
    
    if to_remove:
        save_data()

@tasks.loop(seconds=30)
async def check_protections():
    now = datetime.now().timestamp()
    to_remove = []
    
    for key, protection_data in protections.items():
        # Skip infinite protections
        if protection_data.get('infinite', False):
            continue
        
        if protection_data['end_time'] <= now:
            to_remove.append(key)
    
    for key in to_remove:
        del protections[key]
    
    if to_remove:
        save_data()

@tasks.loop(seconds=30)
async def check_command_penalties():
    now = datetime.now().timestamp()
    to_remove = []
    
    for user_id, penalty_data in command_penalties.items():
        if penalty_data.get('type') == 'mute' and penalty_data.get('end_time', 0) <= now:
            to_remove.append(user_id)
    
    for user_id in to_remove:
        del command_penalties[user_id]
    
    if to_remove:
        save_data()

@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user.name}')
    print(f'Bot Owner: {config["bot_owner"] or "Not set - first user to use /setbotowner will become the bot owner"}')
    
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'Failed to sync commands: {e}')
    
    check_mutes.start()
    check_protections.start()
    check_command_penalties.start()

@bot.event
async def on_member_join(member):
    if config['welcome_dm'].get(str(member.guild.id), False):
        try:
            await member.send(f'Hey there! Welcome to {member.guild.name}!')
        except Exception as e:
            print(f'Could not send welcome DM: {e}')

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    
    # Check if user is AFK and returning
    user_key = f'{message.guild.id}-{message.author.id}'
    if user_key in afk_users:
        afk_data = afk_users[user_key]
        del afk_users[user_key]
        save_data()
        await message.channel.send(f'{message.author.mention} is back! Welcome back :)')
    
    # Check if message mentions AFK users
    for mention in message.mentions:
        mention_key = f'{message.guild.id}-{mention.id}'
        if mention_key in afk_users:
            afk_data = afk_users[mention_key]
            afk_time = datetime.now().timestamp() - afk_data['timestamp']
            time_str = format_duration(int(afk_time))
            await message.channel.send(f'{mention.mention} is AFK: {afk_data["reason"]} - {time_str} ago')
    
    new_level = add_xp(message.guild.id, message.author.id)
    
    # Send level-up notification
    if new_level is not None:
        # Bot owner shows infinity level instead of actual level
        if is_bot_owner(message.author.id):
            await message.channel.send(f'🎉 {message.author.mention} has leveled up to **Level ∞**!')
        else:
            await message.channel.send(f'🎉 {message.author.mention} has leveled up to **Level {new_level}**!')
    
    prefix = get_prefix(message.guild.id)
    
    if message.content.startswith(prefix):
        ctx = await bot.get_context(message)
        ctx.prefix = prefix
        await bot.invoke(ctx)

@bot.tree.command(name='setbotowner', description='Claim bot ownership (first use only)')
async def setbotowner(interaction: discord.Interaction):
    if config['bot_owner']:
        return await interaction.response.send_message('Bot owner has already been set!', ephemeral=True)
    
    config['bot_owner'] = str(interaction.user.id)
    save_data()
    await interaction.response.send_message(f'✅ {interaction.user.mention} is now the bot owner!')

@bot.tree.command(name='help', description='Show all available commands')
async def help_command(interaction: discord.Interaction):
    prefix = '/'
    
    embed = discord.Embed(
        title='📚 Bot Commands',
        description='All commands use slash commands (/)',
        color=0x5865F2
    )
    
    embed.add_field(
        name='**Permission Management**',
        value='/setbotowner - Claim bot ownership (First use only)\n'
              '/addowner <user> - Add server owner (Bot Owner only)\n'
              '/removeowner <user> - Remove server owner (Bot Owner only)\n'
              '/addadmin <user> - Add server admin (Owner+)\n'
              '/removeadmin <user> - Remove server admin (Owner+)\n'
              '/newprefix <prefix> - Change server prefix (Admin+)',
        inline=False
    )
    
    embed.add_field(
        name='**Leveling System**',
        value='/levelstats - View your level and progress\n'
              '/levelboard - View top 10 users by level',
        inline=False
    )
    
    embed.add_field(
        name='**Moderation Commands**',
        value='/mute <user> <duration> [reason] - Timeout user\n'
              '/unmute <user> - Remove timeout from user\n'
              '/ban <user> [reason] - Ban user\n'
              '/unban <user_id> - Unban user by ID\n'
              '/kick <user> [reason] - Kick user\n'
              '/warn <user> <reason> - Warn user\n'
              '/viewwarns <user> - View user warnings\n'
              '/delwarn <user> <warn_id> - Delete a warning\n'
              '/protection <user> <duration> - Protect user from warnings',
        inline=False
    )
    
    embed.add_field(
        name='**Command Penalties (Bot Owner)**',
        value='/commandban <user> [reason] - Ban from using commands\n'
              '/commandunban <user> - Unban from commands\n'
              '/commandmute <user> <duration> [reason] - Mute from commands\n'
              '/commandunmute <user> - Unmute from commands\n'
              '/commandwarn <user> [reason] - Warn about command usage',
        inline=False
    )
    
    embed.add_field(
        name='**Fun Commands**',
        value='/say <message> - Make bot say something\n'
              '/sayembed <title> <description> - Send embed message\n'
              '/slap <user> - Slap a user\n'
              '/punch <user> - Punch a user',
        inline=False
    )
    
    embed.add_field(
        name='**Game Commands**',
        value='/truthordare - Random truth or dare\n'
              '/joke - Random joke\n'
              '/meme - Random meme\n'
              '/8ball <question> - Ask the magic 8-ball\n'
              '/rps <choice> - Rock paper scissors\n'
              '/coinflip - Flip a coin\n'
              '/rolldice [sides] - Roll a dice\n'
              '/trivia - Trivia question\n'
              '/wouldyourather - Would you rather\n'
              '/neverhaveiever - Never have I ever\n'
              '/roast <user> - Roast someone\n'
              '/compliment <user> - Compliment someone\n'
              '/pickupline - Random pickup line',
        inline=False
    )
    
    embed.add_field(
        name='**Gambling & Economy**',
        value='/balance - Check your coin balance\n'
              '/gamble <amount> - Gamble coins (interactive)\n'
              '/roulette <amount> <bet> - Roulette betting game\n'
              '/factory - Manage your factory/idle game\n'
              '/shop - View the shop\n'
              '/buy <item> - Buy an item from the shop\n'
              '/daily - Claim your daily coins',
        inline=False
    )
    
    embed.add_field(
        name='**Utility Commands**',
        value='/poll <question> <options> - Create a poll\n'
              '/afk [reason] - Set yourself as AFK\n'
              '/addit - Toggle welcome DM system (Admin+)\n'
              '/beta - Display bot beta status',
        inline=False
    )
    
    embed.set_footer(text='Enjoy the server!')
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='newprefix', description='Change server prefix (Admin+)')
@app_commands.describe(new_prefix='The new prefix to use')
async def newprefix(interaction: discord.Interaction, new_prefix: str):
    if not is_admin(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('You need to be an admin to use this command.', ephemeral=True)
    
    config['prefixes'][str(interaction.guild.id)] = new_prefix
    save_data()
    await interaction.response.send_message(f'✅ Prefix changed to `{new_prefix}`')

@bot.tree.command(name='addowner', description='Add server owner (Bot Owner only)')
@app_commands.describe(user='The user to add as owner')
async def addowner(interaction: discord.Interaction, user: discord.Member):
    if not is_bot_owner(interaction.user.id):
        return await interaction.response.send_message('Only the bot owner can add owners.', ephemeral=True)
    
    guild_id = str(interaction.guild.id)
    user_id = str(user.id)
    
    if guild_id not in config['owners']:
        config['owners'][guild_id] = []
    
    if user_id not in config['owners'][guild_id]:
        config['owners'][guild_id].append(user_id)
        save_data()
        await interaction.response.send_message(f'✅ {user.name} has been added as an owner.')
    else:
        await interaction.response.send_message(f'{user.name} is already an owner.', ephemeral=True)

@bot.tree.command(name='addadmin', description='Add server admin (Owner+)')
@app_commands.describe(user='The user to add as admin')
async def addadmin(interaction: discord.Interaction, user: discord.Member):
    if not is_owner(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('Only owners can add admins.', ephemeral=True)
    
    guild_id = str(interaction.guild.id)
    user_id = str(user.id)
    
    if guild_id not in config['admins']:
        config['admins'][guild_id] = []
    
    if user_id not in config['admins'][guild_id]:
        config['admins'][guild_id].append(user_id)
        save_data()
        await interaction.response.send_message(f'✅ {user.name} has been added as an admin.')
    else:
        await interaction.response.send_message(f'{user.name} is already an admin.', ephemeral=True)

@bot.tree.command(name='removeadmin', description='Remove server admin (Owner+)')
@app_commands.describe(user='The user to remove as admin')
async def removeadmin(interaction: discord.Interaction, user: discord.Member):
    if not is_owner(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('Only owners can remove admins.', ephemeral=True)
    
    guild_id = str(interaction.guild.id)
    user_id = str(user.id)
    
    if guild_id in config['admins'] and user_id in config['admins'][guild_id]:
        config['admins'][guild_id].remove(user_id)
        save_data()
        await interaction.response.send_message(f'✅ {user.name} has been removed as an admin.')
    else:
        await interaction.response.send_message(f'{user.name} is not an admin.', ephemeral=True)

@bot.tree.command(name='removeowner', description='Remove server owner (Bot Owner only)')
@app_commands.describe(user='The user to remove as owner')
async def removeowner(interaction: discord.Interaction, user: discord.Member):
    if not is_bot_owner(interaction.user.id):
        return await interaction.response.send_message('Only the bot owner can remove owners.', ephemeral=True)
    
    guild_id = str(interaction.guild.id)
    user_id = str(user.id)
    
    if guild_id in config['owners'] and user_id in config['owners'][guild_id]:
        config['owners'][guild_id].remove(user_id)
        save_data()
        await interaction.response.send_message(f'✅ {user.name} has been removed as an owner.')
    else:
        await interaction.response.send_message(f'{user.name} is not an owner.', ephemeral=True)

@bot.tree.command(name='levelstats', description='View your level and progress')
async def levelstats(interaction: discord.Interaction):
    badge = get_user_badge(interaction.guild.id, interaction.user.id)
    badge_text = f' {badge}' if badge else ''
    
    if is_bot_owner(interaction.user.id):
        await interaction.response.send_message(
            f'📊 **Your Level Stats**{badge_text}\n'
            f'Level: **∞ (Infinity)**\n'
            f'Total Messages: **∞**\n'
            f'Progress: **MAX LEVEL**'
        )
        return
    
    key = f'{interaction.guild.id}-{interaction.user.id}'
    user_data = levels.get(key, {'xp': 0})
    level_data = get_level_from_xp(user_data['xp'])
    
    await interaction.response.send_message(
        f'📊 **Your Level Stats**{badge_text}\n'
        f'Level: **{level_data["level"]}**\n'
        f'Total Messages: **{user_data["xp"]}**\n'
        f'Progress: **{level_data["messages_in_level"]}/{level_data["messages_needed"]}** messages to next level'
    )

@bot.tree.command(name='levelboard', description='View top 10 users by level')
async def levelboard(interaction: discord.Interaction):
    guild_levels = []
    
    for key, data in levels.items():
        if key.startswith(str(interaction.guild.id)):
            user_id = key.split('-')[1]
            level_data = get_level_from_xp(data['xp'])
            guild_levels.append({
                'user_id': user_id,
                'level': level_data['level'],
                'xp': data['xp']
            })
    
    guild_levels.sort(key=lambda x: x['xp'], reverse=True)
    guild_levels = guild_levels[:10]
    
    leaderboard = '🏆 **Level Leaderboard**\n\n'
    
    if config['bot_owner']:
        try:
            bot_owner = await bot.fetch_user(int(config['bot_owner']))
            badge = get_user_badge(interaction.guild.id, config['bot_owner'])
            badge_text = f' {badge}' if badge else ''
            leaderboard += f'1. {bot_owner.name} - Level **∞** (∞ messages){badge_text}\n'
        except:
            pass
    
    if not guild_levels:
        if config['bot_owner']:
            await interaction.response.send_message(leaderboard)
        else:
            await interaction.response.send_message('No level data available yet!')
        return
    
    for i, data in enumerate(guild_levels):
        if data['user_id'] == config['bot_owner']:
            continue
        try:
            user = await bot.fetch_user(int(data['user_id']))
            badge = get_user_badge(interaction.guild.id, data['user_id'])
            badge_text = f' {badge}' if badge else ''
            position = i + 2 if config['bot_owner'] else i + 1
            leaderboard += f'{position}. {user.name} - Level **{data["level"]}** ({data["xp"]} messages){badge_text}\n'
        except:
            pass
    
    await interaction.response.send_message(leaderboard)

