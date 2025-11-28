import discord
from discord import app_commands, ui
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
LEVEL_BLACKLIST_FILE = DATA_DIR / 'level_blacklist.json'
GIVEAWAYS_FILE = DATA_DIR / 'giveaways.json'

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
level_blacklist = {}
giveaways = {}

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
        if LEVEL_BLACKLIST_FILE.exists():
            with open(LEVEL_BLACKLIST_FILE, 'r') as f:
                level_blacklist = json.load(f)
        if GIVEAWAYS_FILE.exists():
            with open(GIVEAWAYS_FILE, 'r') as f:
                giveaways = json.load(f)
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
        with open(LEVEL_BLACKLIST_FILE, 'w') as f:
            json.dump(level_blacklist, f, indent=2)
        with open(GIVEAWAYS_FILE, 'w') as f:
            json.dump(giveaways, f, indent=2)
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
    pattern = r'(\d+)\s*(seconds?|secs?|s|minutes?|mins?|m|hours?|hrs?|h|days?|d|weeks?|wks?|w)(?:\s|$)'
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
        elif unit.startswith('w'):
            total_seconds += value * 604800

    return total_seconds

def split_duration_and_reason(text):
    compact_pattern = r'^\d+\s*(?:seconds?|secs?|s|minutes?|mins?|m|hours?|hrs?|h|days?|d|weeks?|wks?|w)$'
    tokens = text.split()
    duration_tokens = []
    i = 0

    while i < len(tokens):
        token = tokens[i]

        if re.match(compact_pattern, token, re.IGNORECASE):
            duration_tokens.append(token)
            i += 1
        elif re.match(r'^\d+$', token):
            if i + 1 < len(tokens) and re.match(r'^(?:seconds?|secs?|s|minutes?|mins?|m|hours?|hrs?|h|days?|d|weeks?|wks?|w)$', tokens[i + 1], re.IGNORECASE):
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

def get_user_balance(guild_id, user_id):
    key = f'{guild_id}-{user_id}'
    if key not in gambling_data:
        gambling_data[key] = {
            'coins': 1000,
            'last_daily': 0,
            'items': []
        }
        save_data()
    return gambling_data[key]

class GambleView(ui.View):
    def __init__(self, interaction, amount):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.amount = amount

    @ui.button(label='Coin Flip', style=discord.ButtonStyle.primary, emoji='🪙')
    async def coinflip_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message('This is not your game!', ephemeral=True)

        user_data = get_user_balance(interaction.guild.id, interaction.user.id)
        user_choice = random.choice(['Heads', 'Tails'])
        bot_choice = random.choice(['Heads', 'Tails'])

        if user_choice == bot_choice:
            user_data['coins'] += self.amount
            save_data()
            await interaction.response.edit_message(
                content=f'🪙 **Coin Flip**\n\nYou got: **{user_choice}**\nBot got: **{bot_choice}**\n\n🎉 You won **{self.amount}** coins!\nNew balance: **{user_data["coins"]}** coins',
                view=None
            )
        else:
            user_data['coins'] -= self.amount
            save_data()
            await interaction.response.edit_message(
                content=f'🪙 **Coin Flip**\n\nYou got: **{user_choice}**\nBot got: **{bot_choice}**\n\n😢 You lost **{self.amount}** coins!\nNew balance: **{user_data["coins"]}** coins',
                view=None
            )

    @ui.button(label='Dice Roll', style=discord.ButtonStyle.primary, emoji='🎲')
    async def dice_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message('This is not your game!', ephemeral=True)

        user_data = get_user_balance(interaction.guild.id, interaction.user.id)
        user_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)

        if user_roll > bot_roll:
            user_data['coins'] += self.amount
            save_data()
            await interaction.response.edit_message(
                content=f'🎲 **Dice Roll**\n\nYou rolled: **{user_roll}**\nBot rolled: **{bot_roll}**\n\n🎉 You won **{self.amount}** coins!\nNew balance: **{user_data["coins"]}** coins',
                view=None
            )
        elif user_roll < bot_roll:
            user_data['coins'] -= self.amount
            save_data()
            await interaction.response.edit_message(
                content=f'🎲 **Dice Roll**\n\nYou rolled: **{user_roll}**\nBot rolled: **{bot_roll}**\n\n😢 You lost **{self.amount}** coins!\nNew balance: **{user_data["coins"]}** coins',
                view=None
            )
        else:
            await interaction.response.edit_message(
                content=f'🎲 **Dice Roll**\n\nYou rolled: **{user_roll}**\nBot rolled: **{bot_roll}**\n\n🤝 It\'s a tie! No coins lost or won.\nBalance: **{user_data["coins"]}** coins',
                view=None
            )

    @ui.button(label='High/Low', style=discord.ButtonStyle.primary, emoji='🎰')
    async def highlow_button(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.interaction.user.id:
            return await interaction.response.send_message('This is not your game!', ephemeral=True)

        user_data = get_user_balance(interaction.guild.id, interaction.user.id)
        number = random.randint(1, 100)

        if number >= 50:
            user_data['coins'] += self.amount
            save_data()
            await interaction.response.edit_message(
                content=f'🎰 **High/Low**\n\nThe number was: **{number}**\n\n🎉 You won **{self.amount}** coins!\nNew balance: **{user_data["coins"]}** coins',
                view=None
            )
        else:
            user_data['coins'] -= self.amount
            save_data()
            await interaction.response.edit_message(
                content=f'🎰 **High/Low**\n\nThe number was: **{number}**\n\n😢 You lost **{self.amount}** coins!\nNew balance: **{user_data["coins"]}** coins',
                view=None
            )

    async def on_timeout(self):
        await self.interaction.edit_original_response(content='Game timed out!', view=None)

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
async def interaction_check(interaction) -> bool:
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

@tasks.loop(seconds=10)
async def check_giveaways():
    now = datetime.now().timestamp()
    to_remove = []

    for giveaway_id, giveaway_data in list(giveaways.items()):
        if giveaway_data['end_time'] <= now and not giveaway_data.get('ended', False):
            try:
                guild = bot.get_guild(int(giveaway_data['guild_id']))
                if not guild:
                    continue

                channel = guild.get_channel(int(giveaway_data['channel_id']))
                if not channel or not isinstance(channel, (discord.TextChannel, discord.Thread)):
                    continue

                try:
                    message = await channel.fetch_message(int(giveaway_id))
                except:
                    to_remove.append(giveaway_id)
                    continue

                # Get all users who reacted with 🎉
                reaction = discord.utils.get(message.reactions, emoji='🎉')
                if not reaction:
                    giveaways[giveaway_id]['ended'] = True
                    save_data()
                    await channel.send(f'❌ Giveaway for **{giveaway_data["prize"]}** ended with no participants!')
                    continue

                participants = []
                async for user in reaction.users():
                    if not user.bot:
                        participants.append(user)

                if len(participants) == 0:
                    giveaways[giveaway_id]['ended'] = True
                    save_data()
                    await channel.send(f'❌ Giveaway for **{giveaway_data["prize"]}** ended with no valid participants!')
                    continue

                num_winners = min(giveaway_data['winners'], len(participants))
                winners = random.sample(participants, num_winners)

                winner_mentions = ', '.join([winner.mention for winner in winners])

                embed = discord.Embed(
                    title='🎉 Giveaway Ended!',
                    description=f'**Prize:** {giveaway_data["prize"]}',
                    color=0x00FF00
                )
                embed.add_field(name='Winners', value=winner_mentions, inline=False)
                embed.set_footer(text=f'Ended at')
                embed.timestamp = datetime.utcnow()

                await message.edit(embed=embed)
                await channel.send(f'🎊 Congratulations {winner_mentions}! You won **{giveaway_data["prize"]}**!')

                giveaways[giveaway_id]['ended'] = True
                giveaways[giveaway_id]['winners_list'] = [str(w.id) for w in winners]
                save_data()

            except Exception as e:
                print(f'Error ending giveaway {giveaway_id}: {e}')

    for giveaway_id in to_remove:
        if giveaway_id in giveaways:
            del giveaways[giveaway_id]

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
    check_giveaways.start()

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

    # Send level-up notification (check if channel is blacklisted)
    if new_level is not None:
        guild_blacklist = level_blacklist.get(str(message.guild.id), [])
        if str(message.channel.id) not in guild_blacklist:
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
        value='/addowner <user> - Add server owner (Bot Owner only)\n',
        inline=False
    )

    embed.add_field(
        name='**Leveling System**',
        value='/levelstats - View your level and progress\n'
              '/levelboard - View top 10 users by level\n'
              '/addlevels <user> <amount> or ?addlevels <@user> <amount> - Add levels to a user (Admin+)\n'
              '/removelevels <user> <amount> or ?removelevels <@user> <amount> - Remove levels from a user (Admin+)',
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

    embed.add_field(
        name='**Giveaway Commands (Admin+)**',
        value='/giveaway create <duration> <winners> <prize> <channel> - Create a giveaway\n'
              '/giveaway end <message_id> - End a giveaway early\n'
              '/giveaway reroll <message_id> - Reroll giveaway winners\n'
              '/giveaway list - List active giveaways',
        inline=False
    )

    embed.add_field(
        name='**Role Reaction Commands (Admin+)**',
        value='/addrolereact <message_id> <description> <mode> <roles> - Add role reactions/buttons\n'
              'Example (buttons): /addrolereact 123456 "Pick your roles" button "Gamer:@Gamer,Artist:@Artist"\n'
              'Example (reactions): /addrolereact 123456 "Pick your roles" reaction "🎮:@Gamer,🎨:@Artist"',
        inline=False
    )

    embed.set_footer(text='Enjoy the server!')

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='newprefix', description='Change server prefix (Admin+)')
@app_commands.describe(new_prefix='The new prefix to use')
async def newprefix(interaction: discord.Interaction, new_prefix: str):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    if not is_admin(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('You need to be an admin to use this command.', ephemeral=True)

    config['prefixes'][str(interaction.guild.id)] = new_prefix
    save_data()
    await interaction.response.send_message(f'✅ Prefix changed to `{new_prefix}`')

@bot.tree.command(name='addowner', description='Add server owner (Bot Owner only)')
@app_commands.describe(user='The user to add as owner')
async def addowner(interaction: discord.Interaction, user: discord.Member):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
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
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
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
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
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
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
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
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
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
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
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

@bot.tree.command(name='mute', description='Timeout a user')
@app_commands.describe(
    member='The member to mute',
    duration='Duration (e.g., 1m, 1h, 2d)',
    reason='Reason for mute'
)
async def mute(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = 'No reason provided'):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_member = interaction.guild.get_member(interaction.user.id)
    if not is_admin(interaction.guild.id, interaction.user.id) and (not user_member or not user_member.guild_permissions.moderate_members):
        return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

    if is_admin(interaction.guild.id, member.id):
        return await interaction.response.send_message("You can't mute a bot admin!", ephemeral=True)

    if not is_admin(interaction.guild.id, interaction.user.id) and has_staff_permissions(member):
        return await interaction.response.send_message("You can't mute someone with staff permissions.", ephemeral=True)

    duration_seconds = parse_duration(duration)

    if not duration_seconds:
        return await interaction.response.send_message('Invalid duration format. Examples: `1m`, `30s`, `1h`, `2d`', ephemeral=True)

    try:
        timeout_until = discord.utils.utcnow() + timedelta(seconds=duration_seconds)
        await member.timeout(timeout_until, reason=reason)

        key = f'{interaction.guild.id}-{member.id}'
        active_mutes[key] = {
            'end_time': (datetime.now() + timedelta(seconds=duration_seconds)).timestamp(),
            'reason': reason
        }
        save_data()

        try:
            await member.send(
                f'You have been muted in **{interaction.guild.name}**.\n'
                f'Duration: {format_duration(duration_seconds)}\n'
                f'Reason: {reason}'
            )
        except:
            pass

        await interaction.response.send_message(f'✅ Successfully muted {member.mention} for {format_duration(duration_seconds)}')
    except Exception as e:
        await interaction.response.send_message(f'Failed to mute user: {e}', ephemeral=True)

@bot.tree.command(name='unmute', description='Remove timeout from a user')
@app_commands.describe(member='The member to unmute')
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_member = interaction.guild.get_member(interaction.user.id)
    if not is_admin(interaction.guild.id, interaction.user.id) and (not user_member or not user_member.guild_permissions.moderate_members):
        return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

    try:
        await member.timeout(None)

        key = f'{interaction.guild.id}-{member.id}'
        if key in active_mutes:
            del active_mutes[key]
            save_data()

        try:
            await member.send(f'Your timeout has been removed in **{interaction.guild.name}**.')
        except:
            pass

        await interaction.response.send_message(f'✅ Successfully unmuted {member.mention}')
    except Exception as e:
        await interaction.response.send_message(f'Failed to unmute user: {e}', ephemeral=True)

@bot.tree.command(name='ban', description='Ban a user from the server')
@app_commands.describe(
    member='The member to ban',
    reason='Reason for ban'
)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = 'No reason provided'):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_member = interaction.guild.get_member(interaction.user.id)
    if not is_admin(interaction.guild.id, interaction.user.id) and (not user_member or not user_member.guild_permissions.ban_members):
        return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

    if is_admin(interaction.guild.id, member.id):
        return await interaction.response.send_message("You can't ban a bot admin!", ephemeral=True)

    if not is_admin(interaction.guild.id, interaction.user.id) and has_staff_permissions(member):
        return await interaction.response.send_message("You can't ban someone with staff permissions.", ephemeral=True)

    try:
        await member.send(
            f'You have been banned from **{interaction.guild.name}**.\n'
            f'Reason: {reason}'
        )
    except:
        pass

    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f'✅ Successfully banned {member.mention}')
    except Exception as e:
        await interaction.response.send_message(f'Failed to ban user: {e}', ephemeral=True)

@bot.tree.command(name='unban', description='Unban a user by ID')
@app_commands.describe(user_id='The ID of the user to unban')
async def unban(interaction: discord.Interaction, user_id: str):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_member = interaction.guild.get_member(interaction.user.id)
    if not is_admin(interaction.guild.id, interaction.user.id) and (not user_member or not user_member.guild_permissions.ban_members):
        return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

    try:
        user_id_int = int(user_id)
        user = await bot.fetch_user(user_id_int)
        await interaction.guild.unban(user)
        await interaction.response.send_message(f'✅ Successfully unbanned {user.name} (ID: {user_id})')
    except ValueError:
        await interaction.response.send_message('Invalid user ID. Please provide a numeric user ID.', ephemeral=True)
    except discord.NotFound:
        await interaction.response.send_message('User not found or not banned.', ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f'Failed to unban user: {e}', ephemeral=True)

@bot.tree.command(name='kick', description='Kick a user from the server')
@app_commands.describe(
    member='The member to kick',
    reason='Reason for kick'
)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = 'No reason provided'):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_member = interaction.guild.get_member(interaction.user.id)
    if not is_admin(interaction.guild.id, interaction.user.id) and (not user_member or not user_member.guild_permissions.kick_members):
        return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

    if is_admin(interaction.guild.id, member.id):
        return await interaction.response.send_message("You can't kick a bot admin!", ephemeral=True)

    if not is_admin(interaction.guild.id, interaction.user.id) and has_staff_permissions(member):
        return await interaction.response.send_message("You can't kick someone with staff permissions.", ephemeral=True)

    try:
        await member.send(
            f'You have been kicked from **{interaction.guild.name}**.\n'
            f'Reason: {reason}'
        )
    except:
        pass

    try:
        await member.kick(reason=reason)
        await interaction.response.send_message(f'✅ Successfully kicked {member.mention}')
    except Exception as e:
        await interaction.response.send_message(f'Failed to kick user: {e}', ephemeral=True)

@bot.tree.command(name='warn', description='Warn a user')
@app_commands.describe(
    member='The member to warn',
    reason='Reason for warning'
)
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_member = interaction.guild.get_member(interaction.user.id)
    if not is_admin(interaction.guild.id, interaction.user.id) and (not user_member or not user_member.guild_permissions.moderate_members):
        return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

    if member.bot:
        return await interaction.response.send_message("I cannot action on bots, but i can action on a member.", ephemeral=True)

    if is_admin(interaction.guild.id, member.id):
        return await interaction.response.send_message("You can't warn a bot admin!", ephemeral=True)

    if not is_admin(interaction.guild.id, interaction.user.id) and has_staff_permissions(member):
        return await interaction.response.send_message("You can't warn someone with staff permissions.", ephemeral=True)

    if is_protected(interaction.guild.id, member.id):
        return await interaction.response.send_message(f"{member.mention} is currently protected and cannot be warned.", ephemeral=True)

    key = f'{interaction.guild.id}-{member.id}'
    if key not in warns:
        warns[key] = []

    warn_id = max([w['id'] for w in warns[key]], default=0) + 1
    warns[key].append({
        'id': warn_id,
        'reason': reason,
        'moderator': str(interaction.user.id),
        'timestamp': datetime.now().isoformat()
    })
    save_data()

    try:
        await member.send(
            f'You have been warned in **{interaction.guild.name}**.\n'
            f'Reason: {reason}\n'
            f'Warning ID: {warn_id}\n\n'
            f'Please follow the server rules to avoid further action.'
        )
        await interaction.response.send_message(f'✅ Successfully warned {member.mention} (Warning #{warn_id})')
    except:
        await interaction.response.send_message(f'✅ Successfully warned {member.mention} (Warning #{warn_id}) (Could not send DM)')

@bot.tree.command(name='viewwarns', description='View warnings for a user')
@app_commands.describe(member='The member to check warnings for')
async def viewwarns(interaction: discord.Interaction, member: discord.Member):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_member = interaction.guild.get_member(interaction.user.id)
    if not is_admin(interaction.guild.id, interaction.user.id) and (not user_member or not user_member.guild_permissions.moderate_members):
        return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

    key = f'{interaction.guild.id}-{member.id}'
    user_warns = warns.get(key, [])

    if not user_warns:
        return await interaction.response.send_message(f'{member.mention} has no warnings.', ephemeral=True)

    embed = discord.Embed(
        title=f'⚠️ Warnings for {member.name}',
        color=0xFF9900
    )

    for warn in user_warns:
        try:
            moderator = await bot.fetch_user(int(warn['moderator']))
            mod_name = moderator.name
        except:
            mod_name = 'Unknown'

        timestamp = datetime.fromisoformat(warn['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        embed.add_field(
            name=f'Warning #{warn["id"]}',
            value=f'**Reason:** {warn["reason"]}\n**Moderator:** {mod_name}\n**Date:** {timestamp}',
            inline=False
        )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='delwarn', description='Delete a specific warning')
@app_commands.describe(
    member='The member to delete warning from',
    warn_id='The ID of the warning to delete'
)
async def delwarn(interaction: discord.Interaction, member: discord.Member, warn_id: int):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_member = interaction.guild.get_member(interaction.user.id)
    if not is_admin(interaction.guild.id, interaction.user.id) and (not user_member or not user_member.guild_permissions.moderate_members):
        return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

    key = f'{interaction.guild.id}-{member.id}'
    user_warns = warns.get(key, [])

    if not user_warns:
        return await interaction.response.send_message(f'{member.mention} has no warnings.', ephemeral=True)

    warn_found = False
    for i, warn in enumerate(user_warns):
        if warn['id'] == warn_id:
            del warns[key][i]
            save_data()
            warn_found = True
            break

    if warn_found:
        await interaction.response.send_message(f'✅ Successfully deleted warning #{warn_id} for {member.mention}')
    else:
        await interaction.response.send_message(f'Warning #{warn_id} not found for {member.mention}.', ephemeral=True)

@bot.tree.command(name='protection', description='Protect a user from warnings')
@app_commands.describe(
    member='The member to protect',
    duration='Duration (e.g., 1h, 2d, or "inf" for infinite)'
)
async def protection(interaction: discord.Interaction, member: discord.Member, duration: str):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_member = interaction.guild.get_member(interaction.user.id)
    if not is_admin(interaction.guild.id, interaction.user.id) and (not user_member or not user_member.guild_permissions.moderate_members):
        return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

    key = f'{interaction.guild.id}-{member.id}'

    if duration.lower() in ['inf', 'infinite', 'forever']:
        protections[key] = {
            'infinite': True,
            'timestamp': datetime.now().isoformat()
        }
        save_data()
        await interaction.response.send_message(f'✅ {member.mention} is now protected from warnings indefinitely.')
    else:
        duration_seconds = parse_duration(duration)

        if not duration_seconds:
            return await interaction.response.send_message('Invalid duration format. Use formats like "1h", "2d", or "inf" for infinite.', ephemeral=True)

        protections[key] = {
            'end_time': (datetime.now() + timedelta(seconds=duration_seconds)).timestamp(),
            'infinite': False,
            'timestamp': datetime.now().isoformat()
        }
        save_data()

        await interaction.response.send_message(f'✅ {member.mention} is now protected from warnings for {format_duration(duration_seconds)}.')


@bot.tree.command(name='removeprotection', description='Remove protection from a user')
@app_commands.describe(member='The member to remove protection from')
async def removeprotection(interaction: discord.Interaction, member: discord.Member):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_member = interaction.guild.get_member(interaction.user.id)
    if not is_admin(interaction.guild.id, interaction.user.id) and (not user_member or not user_member.guild_permissions.moderate_members):
        return await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)

    key = f'{interaction.guild.id}-{member.id}'

    if key not in protections:
        return await interaction.response.send_message(f'{member.mention} is not currently protected.', ephemeral=True)

    del protections[key]
    save_data()

    await interaction.response.send_message(f'✅ Protection removed from {member.mention}.')

@bot.tree.command(name='removelevelnames', description='Disable level-up notifications in a channel (Admin+)')
@app_commands.describe(channel='The text channel to disable level notifications in')
async def removelevelnames(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    if not is_admin(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('You need to be an admin to use this command.', ephemeral=True)

    guild_id = str(interaction.guild.id)
    channel_id = str(channel.id)

    if guild_id not in level_blacklist:
        level_blacklist[guild_id] = []

    if channel_id in level_blacklist[guild_id]:
        return await interaction.response.send_message(f'Level-up notifications are already disabled in {channel.mention}.', ephemeral=True)

    level_blacklist[guild_id].append(channel_id)
    save_data()

    await interaction.response.send_message(f'✅ Level-up notifications have been disabled in {channel.mention}.')

@bot.tree.command(name='purge', description='Delete messages in bulk (Admin+)')
@app_commands.describe(amount='Number of messages to delete (1-1000)')
async def purge(interaction: discord.Interaction, amount: int):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    if not is_admin(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('You need to be an admin to use this command.', ephemeral=True)

    if amount < 1 or amount > 1000:
        return await interaction.response.send_message('Please specify an amount between 1 and 1000.', ephemeral=True)

    await interaction.response.send_message(f'Purging {amount} messages...', ephemeral=True)

    try:
        if isinstance(interaction.channel, discord.TextChannel):
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f'✅ Successfully deleted {len(deleted)} messages.', ephemeral=True)
        else:
            await interaction.followup.send('This command only works in text channels.', ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f'Failed to purge messages: {e}', ephemeral=True)

@bot.tree.command(name='say', description='Make the bot say something (Admin+)')
@app_commands.describe(message='The message to send')
async def say(interaction: discord.Interaction, message: str):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    if not is_admin(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('You need to be an admin to use this command.', ephemeral=True)

    await interaction.response.send_message('Message sent!', ephemeral=True)
    if isinstance(interaction.channel, (discord.TextChannel, discord.Thread)):
        await interaction.channel.send(message)

@bot.tree.command(name='sayembed', description='Send an embed message (Admin+)')
@app_commands.describe(
    title='The embed title',
    description='The embed description'
)
async def sayembed(interaction: discord.Interaction, title: str, description: str):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    if not is_admin(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('You need to be an admin to use this command.', ephemeral=True)

    embed = discord.Embed(
        title=title,
        description=description,
        color=0x5865F2
    )

    await interaction.response.send_message('Embed sent!', ephemeral=True)
    if isinstance(interaction.channel, (discord.TextChannel, discord.Thread)):
        await interaction.channel.send(embed=embed)

@bot.tree.command(name='slap', description='Slap a user')
@app_commands.describe(member='The member to slap')
async def slap(interaction: discord.Interaction, member: discord.Member):
    actions = ['Hard', 'Lightly', 'With a fish', 'With a pillow', 'Gently', 'Violently', 
               'With a ruler', 'With love', 'Softly', 'Aggressively', 'With a newspaper',
               'With a Monitor', 'With a Chair', 'With a Table', 'With a Bed', 'With a Sofa', 'With a TV']
    action = random.choice(actions)
    await interaction.response.send_message(f'{interaction.user.mention} has slapped {action} {member.mention}! 👋')

@bot.tree.command(name='punch', description='Punch a user')
@app_commands.describe(member='The member to punch')
async def punch(interaction: discord.Interaction, member: discord.Member):
    actions = ['Hard', 'Lightly', 'Near his balls', 'With a human', '--Wait nope.. you are a femboy', 'In his mouth', 'did it hurt?', 'While farting at']
    action = random.choice(actions)
    await interaction.response.send_message(f'{interaction.user.mention} has punched {action} {member.mention}! 👊')

@bot.tree.command(name='addit', description='Toggle welcome DM system (Admin+)')
async def addit(interaction: discord.Interaction):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    if not is_admin(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('You need to be an admin+ to use this command.', ephemeral=True)

    guild_id = str(interaction.guild.id)
    config['welcome_dm'][guild_id] = not config['welcome_dm'].get(guild_id, False)
    save_data()

    status = 'enabled' if config['welcome_dm'][guild_id] else 'disabled'
    await interaction.response.send_message(f'✅ Welcome DM has been {status}.')

@bot.tree.command(name='truthordare', description='Get a random truth or dare')
async def truthordare(interaction: discord.Interaction):
    truths = [
        "What's the most embarrassing thing you've ever done?",
        "What's your biggest fear?",
        "Have you ever cheated on a test?",
        "What's the worst lie you've ever told?",
        "What's your most embarrassing childhood memory?",
        "Who was your first crush?",
        "What's something you've never told anyone?",
        "What's the meanest thing you've ever said to someone?",
        "Have you ever stolen something?",
        "What's your biggest insecurity?",
        "What's the worst date you've ever been on?",
        "Have you ever been in love?",
        "What's something you're glad your parents don't know about you?",
        "What's your most ridiculous fear?",
        "Have you ever ghosted someone?"
    ]

    dares = [
        "Do 20 pushups right now!",
        "Speak in an accent for the next 3 messages",
        "Send a message to the 10th person in your DMs",
        "Change your nickname to something embarrassing for 1 hour",
        "Post an embarrassing selfie",
        "Sing your favorite song out loud",
        "Do your best impression of someone in the server",
        "Let someone else send a message from your account",
        "Say something nice about every person online",
        "Share an embarrassing story",
        "Do the chicken dance (send a video)",
        "Speak in rhymes for the next 5 minutes",
        "Change your profile picture to something random for 1 hour",
        "Do 10 jumping jacks and send proof",
        "Tell a dad joke"
    ]

    choice = random.choice(['truth', 'dare'])

    if choice == 'truth':
        await interaction.response.send_message(f"🤔 **TRUTH**: {random.choice(truths)}")
    else:
        await interaction.response.send_message(f"😈 **DARE**: {random.choice(dares)}")

@bot.tree.command(name='joke', description='Get a random joke')
async def joke(interaction: discord.Interaction):
    jokes = [
        "Why don't scientists trust atoms? Because they make up everything!",
        "Why did the scarecrow win an award? He was outstanding in his field!",
        "Why don't eggs tell jokes? They'd crack each other up!",
        "What do you call a fake noodle? An impasta!",
        "Why did the math book look so sad? Because it had too many problems!",
        "What do you call a bear with no teeth? A gummy bear!",
        "Why can't a bicycle stand on its own? It's two tired!",
        "What do you call cheese that isn't yours? Nacho cheese!",
        "Why did the coffee file a police report? It got mugged!",
        "What's orange and sounds like a parrot? A carrot!",
        "Why don't skeletons fight each other? They don't have the guts!",
        "What did the ocean say to the beach? Nothing, it just waved!",
        "Why did the tomato turn red? Because it saw the salad dressing!",
        "What do you call a fish with no eyes? Fsh!",
        "Why did the golfer bring two pairs of pants? In case he got a hole in one!"
    ]

    await interaction.response.send_message(f"😂 {random.choice(jokes)}")

@bot.tree.command(name='meme', description='Get a random meme')
async def meme(interaction: discord.Interaction):
    memes = [
        "**67** - The legendary number! 🔥",
        "**No thoughts, head empty** 🧠❌",
        "**It's over 9000!** 💪",
        "**Is this a pigeon?** 🦋",
        "**Suffering from success** 😎",
        "**Visible confusion** 🤔",
        "**I see this as an absolute win!** 🏆",
        "**Why are you running?** 🏃",
        "**It is what it is** 🤷",
        "**Always has been** 🔫👨‍🚀",
        "**We don't do that here** ❌",
        "**You guys are getting paid?** 💰",
        "**I am once again asking...** 🙏",
        "**This is fine** 🔥☕",
        "**Big brain time** 🧠✨"
    ]

    await interaction.response.send_message(random.choice(memes))

@bot.tree.command(name='8ball', description='Ask the magic 8-ball a question')
@app_commands.describe(question='The question to ask')
async def eightball(interaction: discord.Interaction, question: str):
    responses = [
        "It is certain 🔮",
        "Without a doubt ✅",
        "Yes, definitely 💯",
        "You may rely on it 👍",
        "As I see it, yes 👀",
        "Most likely 📈",
        "Outlook good 🌟",
        "Yes ✔️",
        "Signs point to yes 👉",
        "Reply hazy, try again 🌫️",
        "Ask again later ⏰",
        "Better not tell you now 🤐",
        "Cannot predict now 🔮",
        "Concentrate and ask again 🧘",
        "Don't count on it ❌",
        "My reply is no 🚫",
        "My sources say no 📰",
        "Outlook not so good 📉",
        "Very doubtful 🤨"
    ]

    await interaction.response.send_message(f"🎱 **Question:** {question}\n**Answer:** {random.choice(responses)}")

@bot.tree.command(name='rps', description='Play rock paper scissors')
@app_commands.describe(choice='Your choice: rock, paper, or scissors')
@app_commands.choices(choice=[
    app_commands.Choice(name='Rock', value='rock'),
    app_commands.Choice(name='Paper', value='paper'),
    app_commands.Choice(name='Scissors', value='scissors')
])
async def rps(interaction: discord.Interaction, choice: app_commands.Choice[str]):
    choices = ['rock', 'paper', 'scissors']
    bot_choice = random.choice(choices)
    user_choice = choice.value

    emoji_map = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}

    result = ""
    if user_choice == bot_choice:
        result = "It's a tie!"
    elif (user_choice == 'rock' and bot_choice == 'scissors') or \
         (user_choice == 'paper' and bot_choice == 'rock') or \
         (user_choice == 'scissors' and bot_choice == 'paper'):
        result = "You win! 🎉"
    else:
        result = "I win! 😎"

    await interaction.response.send_message(f"You chose {emoji_map[user_choice]} | I chose {emoji_map[bot_choice]}\n{result}")

@bot.tree.command(name='coinflip', description='Flip a coin')
async def coinflip(interaction: discord.Interaction):
    result = random.choice(['Heads', 'Tails'])
    emoji = '🪙'
    await interaction.response.send_message(f"{emoji} The coin landed on... **{result}**!")

@bot.tree.command(name='rolldice', description='Roll a dice')
@app_commands.describe(sides='Number of sides on the dice (default: 6)')
async def rolldice(interaction: discord.Interaction, sides: int = 6):
    if sides < 2:
        return await interaction.response.send_message("Dice must have at least 2 sides!", ephemeral=True)

    if sides > 100:
        return await interaction.response.send_message("Dice can't have more than 100 sides!", ephemeral=True)

    result = random.randint(1, sides)
    await interaction.response.send_message(f"🎲 You rolled a **{result}** (out of {sides})!")

@bot.tree.command(name='trivia', description='Answer a random trivia question')
async def trivia(interaction: discord.Interaction):
    questions = [
        {"q": "What is the capital of France?", "a": "Paris", "options": ["London", "Paris", "Berlin", "Madrid"]},
        {"q": "What is 2+2?", "a": "4", "options": ["3", "4", "5", "6"]},
        {"q": "What color is the sky?", "a": "Blue", "options": ["Red", "Blue", "Green", "Yellow"]},
        {"q": "How many continents are there?", "a": "7", "options": ["5", "6", "7", "8"]},
        {"q": "What is the largest planet in our solar system?", "a": "Jupiter", "options": ["Mars", "Jupiter", "Saturn", "Earth"]},
        {"q": "Who painted the Mona Lisa?", "a": "Leonardo da Vinci", "options": ["Picasso", "Van Gogh", "Leonardo da Vinci", "Monet"]},
        {"q": "What is the speed of light?", "a": "300,000 km/s", "options": ["100,000 km/s", "200,000 km/s", "300,000 km/s", "400,000 km/s"]},
        {"q": "How many bones are in the human body?", "a": "206", "options": ["186", "196", "206", "216"]},
        {"q": "What year did World War II end?", "a": "1945", "options": ["1943", "1944", "1945", "1946"]},
        {"q": "What is the smallest country in the world?", "a": "Vatican City", "options": ["Monaco", "Vatican City", "San Marino", "Liechtenstein"]}
    ]

    question = random.choice(questions)
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(question['options'])])

    await interaction.response.send_message(
        f"🧠 **Trivia Time!**\n\n"
        f"{question['q']}\n\n"
        f"{options_text}\n\n"
        f"||Answer: {question['a']}||"
    )

@bot.tree.command(name='wouldyourather', description='Get a would you rather question')
async def wouldyourather(interaction: discord.Interaction):
    questions = [
        "Would you rather have the ability to fly or be invisible?",
        "Would you rather be able to speak all languages or play all instruments?",
        "Would you rather live forever or live a short but amazing life?",
        "Would you rather have unlimited money or unlimited free time?",
        "Would you rather travel to the past or the future?",
        "Would you rather have the power to read minds or the power to teleport?",
        "Would you rather never use the internet again or never watch TV again?",
        "Would you rather be famous or be the best friend of someone famous?",
        "Would you rather have a rewind button or a pause button for your life?",
        "Would you rather know all the mysteries of the universe or know every outcome of every choice you make?",
        "Would you rather be stuck on a broken ski lift or in a broken elevator?",
        "Would you rather have to sing everything you say or dance everywhere you go?",
        "Would you rather live in a world without music or without movies?",
        "Would you rather have super strength or super speed?",
        "Would you rather be able to talk to animals or speak all human languages?"
    ]

    await interaction.response.send_message(f"🤔 **Would You Rather...**\n\n{random.choice(questions)}")

@bot.tree.command(name='neverhaveiever', description='Get a never have I ever statement')
async def neverhaveiever(interaction: discord.Interaction):
    statements = [
        "Never have I ever stayed up all night gaming",
        "Never have I ever pretended to be sick to skip school/work",
        "Never have I ever sent a text to the wrong person",
        "Never have I ever stalked someone on social media",
        "Never have I ever laughed so hard I cried",
        "Never have I ever fallen asleep during a movie",
        "Never have I ever ghosted someone",
        "Never have I ever sung in the shower",
        "Never have I ever watched a series in one sitting",
        "Never have I ever forgotten someone's name right after meeting them",
        "Never have I ever pretended to know what someone was talking about",
        "Never have I ever searched my own name on Google",
        "Never have I ever accidentally liked an old photo while stalking someone",
        "Never have I ever said 'I'm on my way' when I haven't left yet",
        "Never have I ever faked being happy"
    ]

    await interaction.response.send_message(f"🙈 **Never Have I Ever...**\n\n{random.choice(statements)}")

@bot.tree.command(name='roast', description='Roast someone')
@app_commands.describe(member='The member to roast')
async def roast(interaction: discord.Interaction, member: discord.Member):
    roasts = [
        f"{member.mention} is like a software update. Whenever I see you, I think 'not now'.",
        f"{member.mention}, you're not stupid; you just have bad luck thinking.",
        f"I'd agree with you {member.mention}, but then we'd both be wrong.",
        f"{member.mention}, you bring everyone so much joy... when you leave the room.",
        f"I'm not saying {member.mention} is dumb, but they would lose a debate with a brick wall.",
        f"{member.mention}, you're like a cloud. When you disappear, it's a beautiful day.",
        f"If laughter is the best medicine, {member.mention}'s face must be curing the world!",
        f"{member.mention}, you're proof that evolution can go in reverse.",
        f"I would challenge {member.mention} to a battle of wits, but I see they're unarmed.",
        f"{member.mention}, you're like Monday mornings. Nobody likes you."
    ]

    await interaction.response.send_message(random.choice(roasts))

@bot.tree.command(name='compliment', description='Compliment someone')
@app_commands.describe(member='The member to compliment')
async def compliment(interaction: discord.Interaction, member: discord.Member):
    compliments = [
        f"{member.mention}, you're more fun than bubble wrap! 🎉",
        f"{member.mention}, you're like a ray of sunshine on a cloudy day! ☀️",
        f"{member.mention}, your smile is contagious! 😊",
        f"{member.mention}, you're an awesome friend! 💙",
        f"{member.mention}, you light up the room! ✨",
        f"{member.mention}, you're one of a kind! 🌟",
        f"{member.mention}, you make a bigger impact than you realize! 💪",
        f"{member.mention}, you're a gift to those around you! 🎁",
        f"{member.mention}, you're incredibly talented! 🎨",
        f"{member.mention}, you have the best laugh! 😄",
        f"{member.mention}, you're absolutely amazing! 🌈",
        f"{member.mention}, you bring out the best in people! 💫",
        f"{member.mention}, you're inspiring! 🔥",
        f"{member.mention}, you have great taste! 👌",
        f"{member.mention}, you're a legend! 🏆"
    ]

    await interaction.response.send_message(random.choice(compliments))

@bot.tree.command(name='pickupline', description='Get a random pickup line')
async def pickupline(interaction: discord.Interaction):
    lines = [
        "Are you a magician? Because whenever I look at you, everyone else disappears! ✨",
        "Do you have a map? I keep getting lost in your eyes! 🗺️",
        "Are you a parking ticket? Because you've got FINE written all over you! 🎫",
        "Is your name Google? Because you have everything I've been searching for! 🔍",
        "Do you believe in love at first sight, or should I walk by again? 👀",
        "Are you a camera? Because every time I look at you, I smile! 📸",
        "If you were a vegetable, you'd be a cute-cumber! 🥒",
        "Are you French? Because Eiffel for you! 🗼",
        "Do you have a Band-Aid? Because I just scraped my knee falling for you! 🩹",
        "Is your dad a boxer? Because you're a knockout! 🥊",
        "Are you a time traveler? Because I see you in my future! ⏰",
        "Do you like Star Wars? Because Yoda one for me! ⭐",
        "Are you a loan? Because you've got my interest! 💰",
        "If you were a triangle, you'd be acute one! 📐",
        "Are you made of copper and tellurium? Because you're Cu-Te! 🧪"
    ]

    await interaction.response.send_message(f"💘 {random.choice(lines)}")


@bot.tree.command(name='balance', description='Check your coin balance')
async def balance(interaction: discord.Interaction):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_data = get_user_balance(interaction.guild.id, interaction.user.id)
    await interaction.response.send_message(f'💰 You have **{user_data["coins"]}** coins!')

@bot.tree.command(name='gamble', description='Gamble your coins in interactive games')
@app_commands.describe(amount='Amount of coins to gamble')
async def gamble(interaction: discord.Interaction, amount: int):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    if amount <= 0:
        return await interaction.response.send_message('Please specify a valid amount to gamble!', ephemeral=True)

    user_data = get_user_balance(interaction.guild.id, interaction.user.id)

    if user_data['coins'] < amount:
        return await interaction.response.send_message(f'You don\'t have enough coins! Your balance: **{user_data["coins"]}** coins', ephemeral=True)

    view = GambleView(interaction, amount)
    await interaction.response.send_message(f'💰 Gambling **{amount}** coins! Choose a game:', view=view)

@bot.tree.command(name='roulette', description='Play roulette - bet on red, black, or a number')
@app_commands.describe(
    amount='Amount of coins to bet',
    bet='Your bet: red, black, or a number (0-36)'
)
async def roulette(interaction: discord.Interaction, amount: int, bet: str):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    if amount <= 0:
        return await interaction.response.send_message('Please specify a valid amount!', ephemeral=True)

    user_data = get_user_balance(interaction.guild.id, interaction.user.id)

    if user_data['coins'] < amount:
        return await interaction.response.send_message(f'You don\'t have enough coins! Your balance: **{user_data["coins"]}** coins', ephemeral=True)

    bet = bet.lower()

    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

    winning_number = random.randint(0, 36)

    if winning_number in red_numbers:
        winning_color = 'red'
    elif winning_number in black_numbers:
        winning_color = 'black'
    else:
        winning_color = 'green'

    won = False
    multiplier = 0

    if bet == 'red' and winning_color == 'red':
        won = True
        multiplier = 2
    elif bet == 'black' and winning_color == 'black':
        won = True
        multiplier = 2
    elif bet.isdigit() and int(bet) == winning_number:
        won = True
        multiplier = 35

    if won:
        winnings = amount * multiplier
        user_data['coins'] += winnings - amount
        save_data()
        await interaction.response.send_message(
            f'🎰 **Roulette**\n\n'
            f'The ball landed on **{winning_number}** ({winning_color})!\n'
            f'🎉 You won **{winnings}** coins!\n\n'
            f'New balance: **{user_data["coins"]}** coins'
        )
    else:
        user_data['coins'] -= amount
        save_data()
        await interaction.response.send_message(
            f'🎰 **Roulette**\n\n'
            f'The ball landed on **{winning_number}** ({winning_color})!\n'
            f'😢 You lost **{amount}** coins!\n\n'
            f'New balance: **{user_data["coins"]}** coins'
        )



@bot.tree.command(name='shop', description='View the shop')
async def shop(interaction: discord.Interaction):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    embed = discord.Embed(
        title='🛒 Shop',
        description='Buy items with your coins!',
        color=0xFFD700
    )

    embed.add_field(
        name='1. 🎨 Custom Role Color',
        value='**Price:** 5000 coins\nGet a custom colored role!',
        inline=False
    )

    embed.add_field(
        name='2. 👑 VIP Badge',
        value='**Price:** 10000 coins\nGet a special VIP badge next to your name!',
        inline=False
    )

    embed.add_field(
        name='3. 🎁 Mystery Box',
        value='**Price:** 2000 coins\nGet a random amount of bonus coins (500-5000)!',
        inline=False
    )

    embed.set_footer(text='Use /buy <item> to purchase')

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='buy', description='Buy an item from the shop')
@app_commands.describe(item='The item number to buy (1, 2, or 3)')
@app_commands.choices(item=[
    app_commands.Choice(name='1 - Custom Role Color (5000 coins)', value='1'),
    app_commands.Choice(name='2 - VIP Badge (10000 coins)', value='2'),
    app_commands.Choice(name='3 - Mystery Box (2000 coins)', value='3')
])
async def buy(interaction: discord.Interaction, item: app_commands.Choice[str]):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_data = get_user_balance(interaction.guild.id, interaction.user.id)

    if item.value == '1':
        if user_data['coins'] < 5000:
            return await interaction.response.send_message('You need 5000 coins to buy this item!', ephemeral=True)

        user_data['coins'] -= 5000
        user_data['items'].append('custom_role_color')
        save_data()
        await interaction.response.send_message('✅ You purchased a Custom Role Color! Contact an admin to set it up.')

    elif item.value == '2':
        if user_data['coins'] < 10000:
            return await interaction.response.send_message('You need 10000 coins to buy this item!', ephemeral=True)

        user_data['coins'] -= 10000
        user_data['items'].append('vip_badge')
        save_data()
        await interaction.response.send_message('✅ You purchased a VIP Badge! 👑')

    elif item.value == '3':
        if user_data['coins'] < 2000:
            return await interaction.response.send_message('You need 2000 coins to buy this item!', ephemeral=True)

        bonus = random.randint(500, 5000)
        user_data['coins'] -= 2000
        user_data['coins'] += bonus
        save_data()
        await interaction.response.send_message(f'🎁 You opened a Mystery Box and got **{bonus}** coins! New balance: **{user_data["coins"]}** coins')

@bot.tree.command(name='daily', description='Claim your daily coins')
async def daily(interaction: discord.Interaction):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_data = get_user_balance(interaction.guild.id, interaction.user.id)
    now = datetime.now().timestamp()

    if now - user_data['last_daily'] < 86400:
        time_left = 86400 - (now - user_data['last_daily'])
        await interaction.response.send_message(f'⏰ You already claimed your daily reward! Come back in {format_duration(int(time_left))}', ephemeral=True)
    else:
        user_data['coins'] += 500
        user_data['last_daily'] = now
        save_data()
        await interaction.response.send_message(f'🎁 You claimed your daily **500** coins! New balance: **{user_data["coins"]}** coins')

@bot.tree.command(name='poll', description='Create a poll')
@app_commands.describe(
    question='The poll question',
    options='Options separated by commas (e.g., "Yes, No, Maybe")'
)
async def poll(interaction: discord.Interaction, question: str, options: str):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    option_list = [opt.strip() for opt in options.split(',')]

    if len(option_list) < 2:
        return await interaction.response.send_message('Please provide at least 2 options!', ephemeral=True)

    if len(option_list) > 10:
        return await interaction.response.send_message('Maximum 10 options allowed!', ephemeral=True)

    embed = discord.Embed(
        title='📊 Poll',
        description=f'**{question}**',
        color=0x5865F2
    )

    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

    for i, option in enumerate(option_list):
        embed.add_field(name=f'{reactions[i]} Option {i+1}', value=option, inline=False)

    embed.set_footer(text=f'Poll by {interaction.user.name}')

    await interaction.response.send_message(embed=embed)

    poll_message = await interaction.original_response()

    for i in range(len(option_list)):
        await poll_message.add_reaction(reactions[i])

@bot.tree.command(name='afk', description='Set yourself as AFK')
@app_commands.describe(reason='Reason for being AFK')
async def afk(interaction: discord.Interaction, reason: str = 'AFK'):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    user_key = f'{interaction.guild.id}-{interaction.user.id}'
    afk_users[user_key] = {
        'reason': reason,
        'timestamp': datetime.now().timestamp()
    }
    save_data()

    await interaction.response.send_message(f'{interaction.user.mention} has gone AFK: {reason}')

@bot.tree.command(name='beta', description='Display bot beta status')
async def beta(interaction: discord.Interaction):
    await interaction.response.send_message(
        '🚧 **Beta Status**\n\n'
        'This bot uses modern slash commands! More updates coming your way soon!\n\n'
        '**Current Features:**\n'
        '• Slash command system (/)\n'
        '• Permission hierarchy (Bot Owner, Owner, Admin)\n'
        '• Leveling system with leaderboard\n'
        '• Moderation tools (mute, ban, kick, warn)\n'
        '• Command penalty system (command ban/mute/warn)\n'
        '• Fun commands (say, sayembed, slap, punch)\n'
        '• 13+ Game commands (truth or dare, jokes, trivia, and more!)\n'
        '• Gambling system with roulette and factory games\n'
        '• Welcome DM system\n\n'
        'Thank you for your patience! There may still be bugs and issues, so please report them to the bot owner.'
    )

@bot.tree.command(name='commandban', description='Ban a user from using bot commands (Bot Owner)')
@app_commands.describe(
    user='The user to ban from commands',
    reason='Reason for command ban'
)
async def commandban(interaction: discord.Interaction, user: discord.User, reason: str = 'No reason provided'):
    if not is_bot_owner(interaction.user.id):
        return await interaction.response.send_message('Only the bot owner can use this command.', ephemeral=True)

    user_id_str = str(user.id)
    command_penalties[user_id_str] = {
        'type': 'ban',
        'reason': reason,
        'moderator': str(interaction.user.id),
        'timestamp': datetime.now().isoformat()
    }
    save_data()

    try:
        await user.send(
            f'❌ You have been banned from using bot commands.\n'
            f'Reason: {reason}\n\n'
            f'Contact the bot owner if you believe this is a mistake.'
        )
    except:
        pass

    await interaction.response.send_message(f'✅ Successfully banned {user.mention} from using bot commands.')

@bot.tree.command(name='commandunban', description='Unban a user from using bot commands (Bot Owner)')
@app_commands.describe(user='The user to unban from commands')
async def commandunban(interaction: discord.Interaction, user: discord.User):
    if not is_bot_owner(interaction.user.id):
        return await interaction.response.send_message('Only the bot owner can use this command.', ephemeral=True)

    user_id_str = str(user.id)

    if user_id_str not in command_penalties:
        return await interaction.response.send_message(f'{user.mention} is not command banned.', ephemeral=True)

    del command_penalties[user_id_str]
    save_data()

    try:
        await user.send(
            f'✅ Your command ban has been lifted. You can now use bot commands again.'
        )
    except:
        pass

    await interaction.response.send_message(f'✅ Successfully unbanned {user.mention} from using bot commands.')

@bot.tree.command(name='commandmute', description='Temporarily mute a user from commands (Bot Owner)')
@app_commands.describe(
    user='The user to mute from commands',
    duration='Duration (e.g., 1h, 2d)',
    reason='Reason for command mute'
)
async def commandmute(interaction: discord.Interaction, user: discord.User, duration: str, reason: str = 'No reason provided'):
    if not is_bot_owner(interaction.user.id):
        return await interaction.response.send_message('Only the bot owner can use this command.', ephemeral=True)

    duration_seconds = parse_duration(duration)

    if not duration_seconds:
        return await interaction.response.send_message('Invalid duration format. Examples: `1m`, `1h`, `2d`', ephemeral=True)

    user_id_str = str(user.id)
    command_penalties[user_id_str] = {
        'type': 'mute',
        'reason': reason,
        'moderator': str(interaction.user.id),
        'timestamp': datetime.now().isoformat(),
        'end_time': (datetime.now() + timedelta(seconds=duration_seconds)).timestamp()
    }
    save_data()

    try:
        await user.send(
            f'🔇 You have been temporarily muted from using bot commands.\n'
            f'Duration: {format_duration(duration_seconds)}\n'
            f'Reason: {reason}\n\n'
            f'You will be able to use commands again after the duration expires.'
        )
    except:
        pass

    await interaction.response.send_message(f'✅ Successfully muted {user.mention} from using bot commands for {format_duration(duration_seconds)}.')

@bot.tree.command(name='commandunmute', description='Unmute a user from commands (Bot Owner)')
@app_commands.describe(user='The user to unmute from commands')
async def commandunmute(interaction: discord.Interaction, user: discord.User):
    if not is_bot_owner(interaction.user.id):
        return await interaction.response.send_message('Only the bot owner can use this command.', ephemeral=True)

    user_id_str = str(user.id)

    if user_id_str not in command_penalties or command_penalties[user_id_str].get('type') != 'mute':
        return await interaction.response.send_message(f'{user.mention} is not command muted.', ephemeral=True)

    del command_penalties[user_id_str]
    save_data()

    try:
        await user.send(
            f'✅ Your command mute has been lifted. You can now use bot commands again.'
        )
    except:
        pass

    await interaction.response.send_message(f'✅ Successfully unmuted {user.mention} from using bot commands.')

@bot.tree.command(name='commandwarn', description='Warn a user about command usage (Bot Owner)')
@app_commands.describe(
    user='The user to warn',
    reason='Reason for command warning'
)
async def commandwarn(interaction: discord.Interaction, user: discord.User, reason: str = 'No reason provided'):
    if not is_bot_owner(interaction.user.id):
        return await interaction.response.send_message('Only the bot owner can use this command.', ephemeral=True)

    try:
        await user.send(
            f'⚠️ **Command Usage Warning**\n\n'
            f'You have received a warning about your bot command usage.\n'
            f'Reason: {reason}\n\n'
            f'Please be mindful of how you use bot commands. Repeated violations may result in a command ban.'
        )
        await interaction.response.send_message(f'✅ Successfully warned {user.mention} about command usage.')
    except:
        await interaction.response.send_message(f'✅ Warning recorded for {user.mention}, but could not send DM.')

@bot.command(name='help')
async def help_prefix(ctx):
    embed = discord.Embed(
        title='📚 Bot Commands',
        description='All commands use slash commands (/) or prefix commands (?)',
        color=0x5865F2
    )

    embed.add_field(
        name='**Permission Management**',
        value='/setbotowner - Claim bot ownership (First use only)\n'
              '/addowner <user> - Add server owner (Bot Owner only)\n'
              '/removeowner <user> - Remove server owner (Bot Owner only)\n'
              '/addadmin <user> - Add server admin (Owner+)\n'
              '/removeadmin <user> - Remove server admin (Owner+)\n'
              '/newprefix <prefix> or ?newprefix <prefix> - Change server prefix (Admin+)',
        inline=False
    )

    embed.add_field(
        name='**Leveling System**',
        value='/levelstats - View your level and progress\n'
              '/levelboard - View top 10 users by level\n'
              '/addlevels <user> <amount> or ?addlevels <@user> <amount> - Add levels to a user (Admin+)\n'
              '/removelevels <user> <amount> or ?removelevels <@user> <amount> - Remove levels from a user (Admin+)',
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
              '/protection <user> <duration> or ?protection <duration> <@user> - Protect user from warnings\n'
              '/removeprotection <user> or ?removeprotection <@user> - Remove protection',
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

    embed.add_field(
        name='**Giveaway Commands (Admin+)**',
        value='/giveaway create <duration> <winners> <prize> <channel> - Create a giveaway\n'
              '/giveaway end <message_id> - End a giveaway early\n'
              '/giveaway reroll <message_id> - Reroll giveaway winners\n'
              '/giveaway list - List active giveaways',
        inline=False
    )

    embed.set_footer(text='Enjoy the server!')

    await ctx.send(embed=embed)

@bot.command(name='newprefix')
async def newprefix_prefix(ctx, new_prefix: str):
    if not is_admin(ctx.guild.id, ctx.author.id):
        return await ctx.send('You need to be an admin to use this command.')

    config['prefixes'][str(ctx.guild.id)] = new_prefix
    save_data()
    await ctx.send(f'✅ Prefix changed to `{new_prefix}`')

@bot.command(name='protection')
async def protection_prefix(ctx, duration: str, member: discord.Member):
    if not is_admin(ctx.guild.id, ctx.author.id) and not ctx.author.guild_permissions.moderate_members:
        return await ctx.send("You don't have permission to use this command.")
    if not member:
        return await ctx.send('Usage: `?protection <duration> <@user>`')
    key = f'{ctx.guild.id}-{member.id}'

    if duration.lower() in ['inf', 'infinite', 'forever']:
        protections[key] = {
            'infinite': True,
            'timestamp': datetime.now().isoformat()
        }
        save_data()
        await ctx.send(f'✅ {member.mention} is now protected from warnings indefinitely.')
    else:
        duration_seconds = parse_duration(duration)

        if not duration_seconds:
            return await ctx.send('Invalid duration format. Use formats like "1h", "2d", or "inf" for infinite.')

        protections[key] = {
            'end_time': (datetime.now() + timedelta(seconds=duration_seconds)).timestamp(),
            'infinite': False,
            'timestamp': datetime.now().isoformat()
        }
        save_data()

        await ctx.send(f'✅ {member.mention} is now protected from warnings for {format_duration(duration_seconds)}.')

@bot.command(name='removeprotection')
async def removeprotection_prefix(ctx, member: discord.Member):
    if not is_admin(ctx.guild.id, ctx.author.id) and not ctx.author.guild_permissions.moderate_members:
        return await ctx.send("You don't have permission to use this command.")
    if not member:
        return await ctx.send('Usage: `?removeprotection <@user>`')

    key = f'{ctx.guild.id}-{member.id}'

    if key not in protections:
        return await ctx.send(f'{member.mention} is not currently protected.')

    del protections[key]
    save_data()

    await ctx.send(f'✅ Protection removed from {member.mention}.')

@bot.command(name='removelevelnames')
async def removelevelnames_prefix(ctx, channel: discord.TextChannel):
    if not is_admin(ctx.guild.id, ctx.author.id):
        return await ctx.send('You need to be an admin to use this command.')

    guild_id = str(ctx.guild.id)
    channel_id = str(channel.id)

    if guild_id not in level_blacklist:
        level_blacklist[guild_id] = []

    if channel_id in level_blacklist[guild_id]:
        return await ctx.send(f'Level-up notifications are already disabled in {channel.mention}.')

    level_blacklist[guild_id].append(channel_id)
    save_data()

    await ctx.send(f'✅ Level-up notifications have been disabled in {channel.mention}.')

@bot.command(name='purge')
async def purge_prefix(ctx, amount: int):
    if not is_admin(ctx.guild.id, ctx.author.id):
        return await ctx.send('You need to be an admin to use this command.')

    if amount < 1 or amount > 1000:
        return await ctx.send('Please specify an amount between 1 and 1000.')

    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f'✅ Successfully deleted {len(deleted) - 1} messages.', delete_after=5)
    except Exception as e:
        await ctx.send(f'Failed to purge messages: {e}')

@bot.command(name='addlevels')
async def addlevels_prefix(ctx, member: discord.Member, amount: int):
    if not is_admin(ctx.guild.id, ctx.author.id):
        return await ctx.send('You need to be an admin to use this command.')

    if amount <= 0:
        return await ctx.send('Please specify a positive amount of levels to add.')

    key = f'{ctx.guild.id}-{member.id}'
    if key not in levels:
        levels[key] = {'xp': 0, 'last_message': 0}

    # Calculate XP needed for the amount of levels
    xp_to_add = 0
    for i in range(amount):
        current_level = get_level_from_xp(levels[key]['xp'] + xp_to_add)['level']
        xp_to_add += get_messages_for_level(current_level + 1)

    levels[key]['xp'] += xp_to_add
    save_data()

    new_level = get_level_from_xp(levels[key]['xp'])['level']
    await ctx.send(f'✅ Added {amount} levels to {member.mention}. They are now level {new_level}.')

@bot.command(name='removelevels')
async def removelevels_prefix(ctx, member: discord.Member, amount: int):
    if not is_admin(ctx.guild.id, ctx.author.id):
        return await ctx.send('You need to be an admin to use this command.')

    if amount <= 0:
        return await ctx.send('Please specify a positive amount of levels to remove.')

    key = f'{ctx.guild.id}-{member.id}'
    if key not in levels:
        return await ctx.send(f'{member.mention} has no levels to remove.')

    current_level = get_level_from_xp(levels[key]['xp'])['level']

    if amount > current_level:
        levels[key]['xp'] = 0
        save_data()
        return await ctx.send(f'✅ Removed all levels from {member.mention}. They are now level 0.')

    # Calculate XP to remove
    xp_to_remove = 0
    for i in range(amount):
        level_to_remove = current_level - i
        xp_to_remove += get_messages_for_level(level_to_remove)

    levels[key]['xp'] = max(0, levels[key]['xp'] - xp_to_remove)
    save_data()

    new_level = get_level_from_xp(levels[key]['xp'])['level']
    await ctx.send(f'✅ Removed {amount} levels from {member.mention}. They are now level {new_level}.')

@bot.command(name='setbotowner')
async def setbotowner_prefix(ctx):
    if config['bot_owner']:
        return await ctx.send('Bot owner has already been set!')
    config['bot_owner'] = str(ctx.author.id)
    save_data()
    await ctx.send(f'✅ {ctx.author.mention} is now the bot owner!')

@bot.command(name='addowner')
async def addowner_prefix(ctx, user: discord.Member = None):
    if not is_bot_owner(ctx.author.id):
        return await ctx.send('Only the bot owner can add owners.')
    if user is None:
        return await ctx.send('Usage: `?addowner <@user>`')
    guild_id, user_id = str(ctx.guild.id), str(user.id)
    if guild_id not in config['owners']:
        config['owners'][guild_id] = []
    if user_id not in config['owners'][guild_id]:
        config['owners'][guild_id].append(user_id)
        save_data()
        await ctx.send(f'✅ {user.name} is now an owner.')
    else:
        await ctx.send(f'{user.name} is already an owner.')

@bot.command(name='removeowner')
async def removeowner_prefix(ctx, user: discord.Member = None):
    if not is_bot_owner(ctx.author.id):
        return await ctx.send('Only the bot owner can remove owners.')
    if user is None:
        return await ctx.send('Usage: `?removeowner <@user>`')
    guild_id, user_id = str(ctx.guild.id), str(user.id)
    if guild_id in config['owners'] and user_id in config['owners'][guild_id]:
        config['owners'][guild_id].remove(user_id)
        save_data()
        await ctx.send(f'✅ {user.name} has been removed as owner.')
    else:
        await ctx.send(f'{user.name} is not an owner.')

@bot.command(name='addadmin')
async def addadmin_prefix(ctx, user: discord.Member = None):
    if not is_owner(ctx.guild.id, ctx.author.id):
        return await ctx.send('Only owners can add admins.')
    if user is None:
        return await ctx.send('Usage: `?addadmin <@user>`')
    guild_id, user_id = str(ctx.guild.id), str(user.id)
    if guild_id not in config['admins']:
        config['admins'][guild_id] = []
    if user_id not in config['admins'][guild_id]:
        config['admins'][guild_id].append(user_id)
        save_data()
        await ctx.send(f'✅ {user.name} is now an admin.')
    else:
        await ctx.send(f'{user.name} is already an admin.')

@bot.command(name='removeadmin')
async def removeadmin_prefix(ctx, user: discord.Member = None):
    if not is_owner(ctx.guild.id, ctx.author.id):
        return await ctx.send('Only owners can remove admins.')
    if user is None:
        return await ctx.send('Usage: `?removeadmin <@user>`')
    guild_id, user_id = str(ctx.guild.id), str(user.id)
    if guild_id in config['admins'] and user_id in config['admins'][guild_id]:
        config['admins'][guild_id].remove(user_id)
        save_data()
        await ctx.send(f'✅ {user.name} has been removed as admin.')
    else:
        await ctx.send(f'{user.name} is not an admin.')

@bot.command(name='levelstats')
async def levelstats_prefix(ctx):
    badge = get_user_badge(ctx.guild.id, ctx.author.id)
    badge_text = f' {badge}' if badge else ''
    if is_bot_owner(ctx.author.id):
        return await ctx.send(f'📊 **Your Level Stats**{badge_text}\nLevel: **∞**\nTotal Messages: **∞**\nProgress: **MAX LEVEL**')
    key = f'{ctx.guild.id}-{ctx.author.id}'
    user_data = levels.get(key, {'xp': 0})
    level_data = get_level_from_xp(user_data['xp'])
    await ctx.send(f'📊 **Your Level Stats**{badge_text}\nLevel: **{level_data["level"]}**\nTotal Messages: **{user_data["xp"]}**\nProgress: **{level_data["messages_in_level"]}/{level_data["messages_needed"]}** to next level')

@bot.command(name='levelboard')
async def levelboard_prefix(ctx):
    guild_levels = [{'user_id': k.split('-')[1], 'level': get_level_from_xp(v['xp'])['level'], 'xp': v['xp']} for k, v in levels.items() if k.startswith(str(ctx.guild.id))]
    guild_levels.sort(key=lambda x: x['xp'], reverse=True)
    leaderboard = '🏆 **Level Leaderboard**\n\n'
    if config['bot_owner']:
        leaderboard += f'1. {(await bot.fetch_user(int(config["bot_owner"]))).name} - Level **∞**\n'
    for i, data in enumerate(guild_levels[:10]):
        if data['user_id'] != config['bot_owner']:
            user = await bot.fetch_user(int(data['user_id']))
            leaderboard += f'{i+2}. {user.name} - Level **{data["level"]}** ({data["xp"]} messages)\n'
    await ctx.send(leaderboard)

@bot.command(name='mute')
async def mute_prefix(ctx, member: discord.Member = None, *, duration_and_reason: str = None):
    if not is_admin(ctx.guild.id, ctx.author.id) and not ctx.author.guild_permissions.moderate_members:
        return await ctx.send("You don't have permission.")
    if member is None or duration_and_reason is None:
        return await ctx.send('Usage: `?mute <@user> <duration> [reason]`')
    if is_admin(ctx.guild.id, member.id):
        return await ctx.send("You can't mute a bot admin!")
    duration_str, reason = split_duration_and_reason(duration_and_reason)
    duration_seconds = parse_duration(duration_str)
    if not duration_seconds:
        return await ctx.send('Invalid duration format.')
    try:
        await member.timeout(discord.utils.utcnow() + timedelta(seconds=duration_seconds), reason=reason)
        active_mutes[f'{ctx.guild.id}-{member.id}'] = {'end_time': (datetime.now() + timedelta(seconds=duration_seconds)).timestamp(), 'reason': reason}
        save_data()
        await ctx.send(f'✅ Muted {member.mention} for {format_duration(duration_seconds)}')
    except Exception as e:
        await ctx.send(f'Failed: {e}')

@bot.command(name='unmute')
async def unmute_prefix(ctx, member: discord.Member = None):
    if not is_admin(ctx.guild.id, ctx.author.id) and not ctx.author.guild_permissions.moderate_members:
        return await ctx.send("You don't have permission.")
    if member is None:
        return await ctx.send('Usage: `?unmute <@user>`')
    try:
        await member.timeout(None)
        if f'{ctx.guild.id}-{member.id}' in active_mutes:
            del active_mutes[f'{ctx.guild.id}-{member.id}']
            save_data()
        await ctx.send(f'✅ Unmuted {member.mention}')
    except Exception as e:
        await ctx.send(f'Failed: {e}')

@bot.command(name='ban')
async def ban_prefix(ctx, member: discord.Member = None, *, reason: str = 'No reason provided'):
    if not is_admin(ctx.guild.id, ctx.author.id) and not ctx.author.guild_permissions.ban_members:
        return await ctx.send("You don't have permission.")
    if member is None:
        return await ctx.send('Usage: `?ban <@user> [reason]`')
    if is_admin(ctx.guild.id, member.id):
        return await ctx.send("You can't ban a bot admin!")
    try:
        await member.ban(reason=reason)
        await ctx.send(f'✅ Banned {member.mention}')
    except Exception as e:
        await ctx.send(f'Failed: {e}')

@bot.command(name='unban')
async def unban_prefix(ctx, user_id: str = None):
    if not is_admin(ctx.guild.id, ctx.author.id) and not ctx.author.guild_permissions.ban_members:
        return await ctx.send("You don't have permission.")
    if user_id is None:
        return await ctx.send('Usage: `?unban <user_id>`')
    try:
        user = await bot.fetch_user(int(user_id))
        await ctx.guild.unban(user)
        await ctx.send(f'✅ Unbanned {user.name}')
    except ValueError:
        await ctx.send('Invalid user ID.')
    except Exception as e:
        await ctx.send(f'Failed: {e}')

@bot.command(name='kick')
async def kick_prefix(ctx, member: discord.Member = None, *, reason: str = 'No reason provided'):
    if not is_admin(ctx.guild.id, ctx.author.id) and not ctx.author.guild_permissions.kick_members:
        return await ctx.send("You don't have permission.")
    if member is None:
        return await ctx.send('Usage: `?kick <@user> [reason]`')
    if is_admin(ctx.guild.id, member.id):
        return await ctx.send("You can't kick a bot admin!")
    try:
        await member.kick(reason=reason)
        await ctx.send(f'✅ Kicked {member.mention}')
    except Exception as e:
        await ctx.send(f'Failed: {e}')

@bot.command(name='warn')
async def warn_prefix(ctx, member: discord.Member = None, *, reason: str = None):
    if not is_admin(ctx.guild.id, ctx.author.id) and not ctx.author.guild_permissions.moderate_members:
        return await ctx.send("You don't have permission.")
    if member is None:
        return await ctx.send('Usage: `?warn <@user> <reason>`')
    if member.bot:
        return await ctx.send("I cannot action on bots, but i can action on a member.")
    if is_admin(ctx.guild.id, member.id):
        return await ctx.send("You can't warn a bot admin!")
    if is_protected(ctx.guild.id, member.id):
        return await ctx.send(f"{member.mention} is protected from warnings.")
    key = f'{ctx.guild.id}-{member.id}'
    if key not in warns:
        warns[key] = []
    warn_id = max([w['id'] for w in warns[key]], default=0) + 1
    warns[key].append({'id': warn_id, 'reason': reason or 'No reason', 'moderator': str(ctx.author.id), 'timestamp': datetime.now().isoformat()})
    save_data()
    await ctx.send(f'✅ Warned {member.mention} (Warning #{warn_id})')

@bot.command(name='viewwarns')
async def viewwarns_prefix(ctx, member: discord.Member = None):
    if not is_admin(ctx.guild.id, ctx.author.id) and not ctx.author.guild_permissions.moderate_members:
        return await ctx.send("You don't have permission.")
    if member is None:
        return await ctx.send('Usage: `?viewwarns <@user>`')
    key = f'{ctx.guild.id}-{member.id}'
    user_warns = warns.get(key, [])
    if not user_warns:
        return await ctx.send(f'{member.mention} has no warnings.')
    msg = f'⚠️ **Warnings for {member.name}**\n'
    for warn in user_warns:
        msg += f'  #{warn["id"]}: {warn["reason"]}\n'
    await ctx.send(msg)

@bot.command(name='delwarn')
async def delwarn_prefix(ctx, member: discord.Member = None, warn_id: int = None):
    if not is_admin(ctx.guild.id, ctx.author.id) and not ctx.author.guild_permissions.moderate_members:
        return await ctx.send("You don't have permission.")
    if member is None or warn_id is None:
        return await ctx.send('Usage: `?delwarn <@user> <warn_id>`')
    key = f'{ctx.guild.id}-{member.id}'
    if key in warns:
        warns[key] = [w for w in warns[key] if w['id'] != warn_id]
        if not warns[key]:
            del warns[key]
        save_data()
        await ctx.send(f'✅ Deleted warning #{warn_id}')
    else:
        await ctx.send('Warning not found.')

@bot.command(name='say')
async def say_prefix(ctx, *, text: str = None):
    if text is None:
        return await ctx.send('Usage: `?say <message>`')
    await ctx.message.delete()
    await ctx.send(text)

@bot.command(name='sayembed')
async def sayembed_prefix(ctx, *, content: str = None):
    if content is None or '|' not in content:
        return await ctx.send('Usage: `?sayembed <title> | <description>`')
    title, description = content.split('|', 1)
    await ctx.message.delete()
    await ctx.send(embed=discord.Embed(title=title.strip(), description=description.strip(), color=0x5865F2))

@bot.command(name='slap')
async def slap_prefix(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send('Usage: `?slap <@user>`')
    actions = ['Hard', 'Lightly', 'With a Fish', 'With a Banana', 'With a Stick']
    await ctx.send(f'{ctx.author.mention} slapped {member.mention} {random.choice(actions)}! 👋')

@bot.command(name='punch')
async def punch_prefix(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send('Usage: `?punch <@user>`')
    actions = ['Hard', 'Lightly', 'With a Human']
    await ctx.send(f'{ctx.author.mention} punched {member.mention} {random.choice(actions)}! 👊')

@bot.command(name='addit')
async def addit_prefix(ctx):
    if not is_admin(ctx.guild.id, ctx.author.id):
        return await ctx.send('You need to be an admin.')
    guild_id = str(ctx.guild.id)
    config['welcome_dm'][guild_id] = not config['welcome_dm'].get(guild_id, False)
    save_data()
    status = 'enabled' if config['welcome_dm'][guild_id] else 'disabled'
    await ctx.send(f'✅ Welcome DM {status}.')

@bot.command(name='truthordare')
async def truthordare_prefix(ctx):
    truths = ["What's your biggest fear?", "Have you ever cheated?", "What's your biggest secret?"]
    dares = ["Do 20 pushups!", "Send a selfie!", "Sing a song!"]
    choice = random.choice(['truth', 'dare'])
    msg = f"🤔 **TRUTH**: {random.choice(truths)}" if choice == 'truth' else f"😈 **DARE**: {random.choice(dares)}"
    await ctx.send(msg)

@bot.command(name='joke')
async def joke_prefix(ctx):
    jokes = ["Why don't scientists atoms? They make up everything!", "Why did the scarecrow win an award? He was outstanding in his field!"]
    await ctx.send(f"😂 {random.choice(jokes)}")

@bot.command(name='meme')
async def meme_prefix(ctx):
    memes = ["**67** - Legend!", "**No thoughts, head empty** 🧠❌", "**It's over 9000!** 💪"]
    await ctx.send(random.choice(memes))

@bot.command(name='8ball')
async def eightball_prefix(ctx, *, question: str = None):
    if question is None:
        return await ctx.send('Usage: `?8ball <question>`')
    responses = ["It is certain", "Without a doubt", "Yes, definitely", "Don't count on it", "Very doubtful"]
    await ctx.send(f"🎱 {random.choice(responses)}")

@bot.command(name='rps')
async def rps_prefix(ctx, choice: str = None):
    if choice is None or choice.lower() not in ['rock', 'paper', 'scissors']:
        return await ctx.send('Usage: `?rps <rock/paper/scissors>`')
    choices = ['rock', 'paper', 'scissors']
    bot_choice = random.choice(choices)
    user_choice = choice.lower()
    if (user_choice == 'rock' and bot_choice == 'scissors') or (user_choice == 'paper' and bot_choice == 'rock') or (user_choice == 'scissors' and bot_choice == 'paper'):
        result = "You win! 🎉"
    elif user_choice == bot_choice:
        result = "It's a tie!"
    else:
        result = "I win! 😎"
    await ctx.send(f"You: {user_choice} | Me: {bot_choice}\n{result}")

@bot.command(name='coinflip')
async def coinflip_prefix(ctx):
    result = random.choice(['Heads', 'Tails'])
    await ctx.send(f"🪙 The coin landed on... **{result}**!")

@bot.command(name='rolldice')
async def rolldice_prefix(ctx, sides: int = 6):
    if sides < 2 or sides > 100:
        return await ctx.send('Sides must be between 2 and 100!')
    result = random.randint(1, sides)
    await ctx.send(f"🎲 You rolled a **{result}** (out of {sides})!")

@bot.command(name='trivia')
async def trivia_prefix(ctx):
    q = {"q": "What is the capital of France?", "a": "Paris"}
    await ctx.send(f"🧠 {q['q']}\n||Answer: {q['a']}||")

@bot.command(name='wouldyourather')
async def wouldyourather_prefix(ctx):
    questions = ["Would you rather fly or be invisible?", "Would you rather have unlimited money or time?"]
    await ctx.send(f"🤔 {random.choice(questions)}")

@bot.command(name='neverhaveiever')
async def neverhaveiever_prefix(ctx):
    statements = ["Never have I ever stayed up all night", "Never have I ever ghosted someone"]
    await ctx.send(f"🙈 {random.choice(statements)}")

@bot.command(name='roast')
async def roast_prefix(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send('Usage: `?roast <@user>`')
    roasts = [f"{member.mention} is like a software update. Not now.", f"{member.mention}, you bring joy when you leave the room."]
    await ctx.send(random.choice(roasts))

@bot.command(name='compliment')
async def compliment_prefix(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send('Usage: `?compliment <@user>`')
    compliments = [f"{member.mention}, you're awesome! 💙", f"{member.mention}, you light up the room! ✨"]
    await ctx.send(random.choice(compliments))

@bot.command(name='pickupline')
async def pickupline_prefix(ctx):
    lines = ["Are you a magician? Everyone else disappears when I look at you! ✨", "Do you have a map? I'm lost in your eyes!"]
    await ctx.send(f"💘 {random.choice(lines)}")

@bot.command(name='balance')
async def balance_prefix(ctx):
    user_data = get_user_balance(ctx.guild.id, ctx.author.id)
    await ctx.send(f'💰 You have **{user_data["coins"]}** coins!')

@bot.command(name='gamble')
async def gamble_prefix(ctx, amount: int = None):
    if amount is None or amount <= 0:
        return await ctx.send('Usage: `?gamble <amount>`')
    user_data = get_user_balance(ctx.guild.id, ctx.author.id)
    if user_data['coins'] < amount:
        return await ctx.send(f'You need more coins! Balance: **{user_data["coins"]}**')
    if random.random() > 0.5:
        user_data['coins'] += amount
        save_data()
        await ctx.send(f'🎉 You won **{amount}** coins! Balance: **{user_data["coins"]}**')
    else:
        user_data['coins'] -= amount
        save_data()
        await ctx.send(f'😢 You lost **{amount}** coins! Balance: **{user_data["coins"]}**')

@bot.command(name='roulette')
async def roulette_prefix(ctx, amount: int = None, bet: str = None):
    if amount is None or bet is None:
        return await ctx.send('Usage: `?roulette <amount> <red/black/number>`')
    user_data = get_user_balance(ctx.guild.id, ctx.author.id)
    if user_data['coins'] < amount:
        return await ctx.send(f'Insufficient coins!')
    red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    winning_number = random.randint(0, 36)
    winning_color = 'red' if winning_number in red_numbers else 'black' if winning_number != 0 else 'green'
    won = (bet == 'red' and winning_color == 'red') or (bet == 'black' and winning_color == 'black') or (bet.isdigit() and int(bet) == winning_number)
    if won:
        winnings = amount * (35 if bet.isdigit() else 2)
        user_data['coins'] += winnings - amount
        save_data()
        await ctx.send(f'🎰 Ball landed on **{winning_number}** ({winning_color})!\n🎉 You won **{winnings}** coins!')
    else:
        user_data['coins'] -= amount
        save_data()
        await ctx.send(f'🎰 Ball landed on **{winning_number}** ({winning_color})!\n😢 You lost **{amount}** coins!')

@bot.command(name='shop')
async def shop_prefix(ctx):
    msg = '🛒 **Shop**\n1. Custom Role Color - 5000 coins\n2. VIP Badge - 10000 coins\n3. Mystery Box - 2000 coins\nUse `?buy <item>`'
    await ctx.send(msg)

@bot.command(name='buy')
async def buy_prefix(ctx, item: str = None):
    if item is None:
        return await ctx.send('Usage: `?buy <item number>`')
    user_data = get_user_balance(ctx.guild.id, ctx.author.id)
    if item == '1':
        if user_data['coins'] < 5000:
            return await ctx.send('Need 5000 coins!')
        user_data['coins'] -= 5000
        save_data()
        await ctx.send('✅ Purchased Custom Role Color!')
    elif item == '3':
        if user_data['coins'] < 2000:
            return await ctx.send('Need 2000 coins!')
        bonus = random.randint(500, 5000)
        user_data['coins'] -= 2000 + bonus
        save_data()
        await ctx.send(f'🎁 Got **{bonus}** coins!')

@bot.command(name='daily')
async def daily_prefix(ctx):
    user_data = get_user_balance(ctx.guild.id, ctx.author.id)
    now = datetime.now().timestamp()
    if now - user_data['last_daily'] < 86400:
        time_left = 86400 - (now - user_data['last_daily'])
        await ctx.send(f'⏰ Come back in {format_duration(int(time_left))}')
    else:
        user_data['coins'] += 500
        user_data['last_daily'] = now
        save_data()
        await ctx.send(f'🎁 +500 coins! Balance: **{user_data["coins"]}**')

@bot.command(name='poll')
async def poll_prefix(ctx, *, content: str = None):
    if content is None or '|' not in content:
        return await ctx.send('Usage: `?poll <question> | <option1>, <option2>`')
    question, options_str = content.split('|', 1)
    options = [o.strip() for o in options_str.split(',')]
    if len(options) < 2 or len(options) > 10:
        return await ctx.send('Need 2-10 options!')
    msg = f"📊 **{question.strip()}**\n"
    for i, opt in enumerate(options):
        msg += f"{i+1}. {opt}\n"
    await ctx.send(msg)

@bot.command(name='afk')
async def afk_prefix(ctx, *, reason: str = 'AFK'):
    user_key = f'{ctx.guild.id}-{ctx.author.id}'
    afk_users[user_key] = {'reason': reason, 'timestamp': datetime.now().timestamp()}
    save_data()
    await ctx.send(f'{ctx.author.mention} is now AFK: {reason}')

@bot.command(name='beta')
async def beta_prefix(ctx):
    msg = '🚧 **Beta Status**\nBot uses slash commands (/)!\n✨ Modern and fast!'
    await ctx.send(msg)

@bot.command(name='commandban')
async def commandban_prefix(ctx, user: discord.User = None, *, reason: str = 'No reason'):
    if not is_bot_owner(ctx.author.id):
        return await ctx.send('Only bot owner!')
    if user is None:
        return await ctx.send('Usage: `?commandban <@user> [reason]`')
    key = f'{ctx.guild.id}-{user.id}'
    command_penalties[key] = {'type': 'ban', 'reason': reason, 'timestamp': datetime.now().isoformat()}
    save_data()
    await ctx.send(f'✅ {user.mention} banned from commands!')

@bot.command(name='commandunban')
async def commandunban_prefix(ctx, user: discord.User = None):
    if not is_bot_owner(ctx.author.id):
        return await ctx.send('Only bot owner!')
    if user is None:
        return await ctx.send('Usage: `?commandunban <@user>`')
    key = f'{ctx.guild.id}-{user.id}'
    if key in command_penalties:
        del command_penalties[key]
        save_data()
        await ctx.send(f'✅ {user.mention} unbanned!')
    else:
        await ctx.send('User not banned.')

@bot.command(name='commandmute')
async def commandmute_prefix(ctx, user: discord.User = None, duration: str = None, *, reason: str = 'No reason'):
    if not is_bot_owner(ctx.author.id):
        return await ctx.send('Only bot owner!')
    if user is None or duration is None:
        return await ctx.send('Usage: `?commandmute <@user> <duration> [reason]`')
    seconds = parse_duration(duration)
    if not seconds:
        return await ctx.send('Invalid duration!')
    key = f'{ctx.guild.id}-{user.id}'
    command_penalties[key] = {'type': 'mute', 'end_time': (datetime.now() + timedelta(seconds=seconds)).timestamp(), 'reason': reason}
    save_data()
    await ctx.send(f'✅ {user.mention} muted for {format_duration(seconds)}!')

@bot.command(name='commandunmute')
async def commandunmute_prefix(ctx, user: discord.User = None):
    if not is_bot_owner(ctx.author.id):
        return await ctx.send('Only bot owner!')
    if user is None:
        return await ctx.send('Usage: `?commandunmute <@user>`')
    key = f'{ctx.guild.id}-{user.id}'
    if key in command_penalties and command_penalties[key].get('type') == 'mute':
        del command_penalties[key]
        save_data()
        await ctx.send(f'✅ {user.mention} unmuted!')
    else:
        await ctx.send('Not muted.')

@bot.command(name='commandwarn')
async def commandwarn_prefix(ctx, user: discord.User = None, *, reason: str = 'No reason'):
    if not is_bot_owner(ctx.author.id):
        return await ctx.send('Only bot owner!')
    if user is None:
        return await ctx.send('Usage: `?commandwarn <@user> [reason]`')
    key = f'{ctx.guild.id}-{user.id}'
    if key not in command_penalties:
        command_penalties[key] = {'type': 'warns', 'count': 0}
    command_penalties[key]['count'] = command_penalties[key].get('count', 0) + 1
    save_data()
    await ctx.send(f'⚠️ {user.mention} warned! ({command_penalties[key]["count"]} warnings)')


# Giveaway Commands
giveaway_group = app_commands.Group(name='giveaway', description='Giveaway management commands')

@giveaway_group.command(name='create', description='Create a giveaway (Admin+)')
@app_commands.describe(
    duration='Duration (e.g., 1h, 2d, 1w)',
    winners='Number of winners',
    prize='Prize description',
    channel='Channel to post the giveaway in'
)
async def giveaway_create(interaction: discord.Interaction, duration: str, winners: int, prize: str, channel: discord.TextChannel):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    if not is_admin(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('You need to be an admin to use this command.', ephemeral=True)

    if winners < 1:
        return await interaction.response.send_message('Number of winners must be at least 1!', ephemeral=True)

    duration_seconds = parse_duration(duration)
    if not duration_seconds:
        return await interaction.response.send_message('Invalid duration format. Examples: `1h`, `2d`, `1w`', ephemeral=True)

    end_time = datetime.now() + timedelta(seconds=duration_seconds)

    embed = discord.Embed(
        title='🎉 GIVEAWAY 🎉',
        description=f'**Prize:** {prize}\n\n'
                    f'**Winners:** {winners}\n'
                    f'**Hosted by:** {interaction.user.mention}\n\n'
                    f'React with 🎉 to enter!',
        color=0xFF00FF
    )
    embed.set_footer(text=f'Ends at')
    embed.timestamp = end_time

    await interaction.response.send_message(f'✅ Giveaway created in {channel.mention}!', ephemeral=True)

    message = await channel.send(embed=embed)
    await message.add_reaction('🎉')

    giveaways[str(message.id)] = {
        'guild_id': str(interaction.guild.id),
        'channel_id': str(channel.id),
        'prize': prize,
        'winners': winners,
        'host_id': str(interaction.user.id),
        'end_time': end_time.timestamp(),
        'ended': False
    }
    save_data()

@giveaway_group.command(name='end', description='End a giveaway early (Admin+)')
@app_commands.describe(message_id='The message ID of the giveaway')
async def giveaway_end(interaction: discord.Interaction, message_id: str):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    if not is_admin(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('You need to be an admin to use this command.', ephemeral=True)

    if message_id not in giveaways:
        return await interaction.response.send_message('Giveaway not found!', ephemeral=True)

    giveaway_data = giveaways[message_id]

    if giveaway_data.get('ended', False):
        return await interaction.response.send_message('This giveaway has already ended!', ephemeral=True)

    try:
        channel = interaction.guild.get_channel(int(giveaway_data['channel_id']))
        if not channel or not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return await interaction.response.send_message('Giveaway channel not found!', ephemeral=True)

        message = await channel.fetch_message(int(message_id))

        reaction = discord.utils.get(message.reactions, emoji='🎉')
        if not reaction:
            giveaways[message_id]['ended'] = True
            save_data()
            await interaction.response.send_message('❌ No participants in this giveaway!', ephemeral=True)
            return

        participants = []
        async for user in reaction.users():
            if not user.bot:
                participants.append(user)

        if len(participants) == 0:
            giveaways[message_id]['ended'] = True
            save_data()
            await interaction.response.send_message('❌ No valid participants in this giveaway!', ephemeral=True)
            return

        num_winners = min(giveaway_data['winners'], len(participants))
        winners = random.sample(participants, num_winners)

        winner_mentions = ', '.join([winner.mention for winner in winners])

        embed = discord.Embed(
            title='🎉 Giveaway Ended!',
            description=f'**Prize:** {giveaway_data["prize"]}',
            color=0x00FF00
        )
        embed.add_field(name='Winners', value=winner_mentions, inline=False)
        embed.set_footer(text=f'Ended early by {interaction.user.name}')
        embed.timestamp = datetime.utcnow()

        await message.edit(embed=embed)
        await channel.send(f'🎊 Congratulations {winner_mentions}! You won **{giveaway_data["prize"]}**!')

        giveaways[message_id]['ended'] = True
        giveaways[message_id]['winners_list'] = [str(w.id) for w in winners]
        save_data()

        await interaction.response.send_message('✅ Giveaway ended successfully!', ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f'Failed to end giveaway: {e}', ephemeral=True)

@giveaway_group.command(name='reroll', description='Reroll giveaway winners (Admin+)')
@app_commands.describe(message_id='The message ID of the giveaway')
async def giveaway_reroll(interaction: discord.Interaction, message_id: str):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    if not is_admin(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('You need to be an admin to use this command.', ephemeral=True)

    if message_id not in giveaways:
        return await interaction.response.send_message('Giveaway not found!', ephemeral=True)

    giveaway_data = giveaways[message_id]

    if not giveaway_data.get('ended', False):
        return await interaction.response.send_message('This giveaway has not ended yet!', ephemeral=True)

    try:
        channel = interaction.guild.get_channel(int(giveaway_data['channel_id']))
        if not channel or not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return await interaction.response.send_message('Giveaway channel not found!', ephemeral=True)

        message = await channel.fetch_message(int(message_id))

        reaction = discord.utils.get(message.reactions, emoji='🎉')
        if not reaction:
            return await interaction.response.send_message('❌ No participants to reroll!', ephemeral=True)

        participants = []
        previous_winners = giveaway_data.get('winners_list', [])

        async for user in reaction.users():
            if not user.bot and str(user.id) not in previous_winners:
                participants.append(user)

        if len(participants) == 0:
            return await interaction.response.send_message('❌ No new participants available for reroll!', ephemeral=True)

        num_winners = min(giveaway_data['winners'], len(participants))
        new_winners = random.sample(participants, num_winners)

        winner_mentions = ', '.join([winner.mention for winner in new_winners])

        await channel.send(f'🔄 **Giveaway Rerolled!**\n🎊 New winner(s): {winner_mentions} for **{giveaway_data["prize"]}**!')

        giveaways[message_id]['winners_list'].extend([str(w.id) for w in new_winners])
        save_data()

        await interaction.response.send_message('✅ Giveaway rerolled successfully!', ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f'Failed to reroll giveaway: {e}', ephemeral=True)

@giveaway_group.command(name='list', description='List all active giveaways')
async def giveaway_list(interaction: discord.Interaction):
    if not interaction.guild:
        return await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
    active_giveaways = []

    for message_id, giveaway_data in giveaways.items():
        if not giveaway_data.get('ended', False) and giveaway_data['guild_id'] == str(interaction.guild.id):
            channel = interaction.guild.get_channel(int(giveaway_data['channel_id']))
            if channel:
                time_left = giveaway_data['end_time'] - datetime.now().timestamp()
                if time_left > 0:
                    active_giveaways.append(
                        f'**{giveaway_data["prize"]}** in {channel.mention}\n'
                        f'Winners: {giveaway_data["winners"]} | Ends in: {format_duration(int(time_left))}\n'
                        f'Message ID: `{message_id}`'
                    )

    if not active_giveaways:
        return await interaction.response.send_message('No active giveaways in this server!', ephemeral=True)

    embed = discord.Embed(
        title='🎉 Active Giveaways',
        description='\n\n'.join(active_giveaways),
        color=0xFF00FF
    )

    await interaction.response.send_message(embed=embed)

bot.tree.add_command(giveaway_group)


if __name__ == '__main__':
    load_data()

    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print('ERROR: DISCORD_BOT_TOKEN environment variable is not set!')
        exit(1)

    bot.run(token)