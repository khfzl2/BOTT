@bot.tree.command(name='mute', description='Timeout a user')
@app_commands.describe(
    member='The member to mute',
    duration='Duration (e.g., 10m, 1h, 2d)',
    reason='Reason for mute'
)
async def mute(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = 'No reason provided'):
    if not is_admin(interaction.guild.id, interaction.user.id) and not interaction.user.guild_permissions.moderate_members:
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
    if not is_admin(interaction.guild.id, interaction.user.id) and not interaction.user.guild_permissions.moderate_members:
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
    if not is_admin(interaction.guild.id, interaction.user.id) and not interaction.user.guild_permissions.ban_members:
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
    if not is_admin(interaction.guild.id, interaction.user.id) and not interaction.user.guild_permissions.ban_members:
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
    if not is_admin(interaction.guild.id, interaction.user.id) and not interaction.user.guild_permissions.kick_members:
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
    if not is_admin(interaction.guild.id, interaction.user.id) and not interaction.user.guild_permissions.moderate_members:
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
    if not is_admin(interaction.guild.id, interaction.user.id) and not interaction.user.guild_permissions.moderate_members:
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
    if not is_admin(interaction.guild.id, interaction.user.id) and not interaction.user.guild_permissions.moderate_members:
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
    if not is_admin(interaction.guild.id, interaction.user.id) and not interaction.user.guild_permissions.moderate_members:
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


@bot.tree.command(name='say', description='Make the bot say something (Admin+)')
@app_commands.describe(message='The message to send')
async def say(interaction: discord.Interaction, message: str):
    if not is_admin(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('You need to be an admin to use this command.', ephemeral=True)
    
    await interaction.response.send_message('Message sent!', ephemeral=True)
    await interaction.channel.send(message)

@bot.tree.command(name='sayembed', description='Send an embed message (Admin+)')
@app_commands.describe(
    title='The embed title',
    description='The embed description'
)
async def sayembed(interaction: discord.Interaction, title: str, description: str):
    if not is_admin(interaction.guild.id, interaction.user.id):
        return await interaction.response.send_message('You need to be an admin to use this command.', ephemeral=True)
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=0x5865F2
    )
    
    await interaction.response.send_message('Embed sent!', ephemeral=True)
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
    user_data = get_user_balance(interaction.guild.id, interaction.user.id)
    await interaction.response.send_message(f'💰 You have **{user_data["coins"]}** coins!')

@bot.tree.command(name='gamble', description='Gamble your coins in interactive games')
@app_commands.describe(amount='Amount of coins to gamble')
async def gamble(interaction: discord.Interaction, amount: int):
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

@bot.tree.command(name='factory', description='Manage your factory/idle game')
async def factory(interaction: discord.Interaction):
    user_data = get_user_balance(interaction.guild.id, interaction.user.id)
    
    if 'factory' not in user_data:
        user_data['factory'] = {
            'level': 1,
            'production_rate': 10,
            'last_collect': datetime.now().timestamp(),
            'total_produced': 0
        }
        save_data()
    
    factory_data = user_data['factory']
    
    now = datetime.now().timestamp()
    time_passed = now - factory_data['last_collect']
    production = int(time_passed / 60) * factory_data['production_rate']
    
    if production > 0:
        user_data['coins'] += production
        factory_data['last_collect'] = now
        factory_data['total_produced'] += production
        save_data()
    
    upgrade_cost = factory_data['level'] * 1000
    
    embed = discord.Embed(
        title='🏭 Your Factory',
        description=f'Idle coin production system',
        color=0x5865F2
    )
    
    embed.add_field(
        name='Factory Level',
        value=f'Level **{factory_data["level"]}**',
        inline=True
    )
    
    embed.add_field(
        name='Production Rate',
        value=f'**{factory_data["production_rate"]}** coins/minute',
        inline=True
    )
    
    embed.add_field(
        name='Total Produced',
        value=f'**{factory_data["total_produced"]}** coins',
        inline=True
    )
    
    embed.add_field(
        name='Collected',
        value=f'💰 **{production}** coins collected!',
        inline=False
    )
    
    embed.add_field(
        name='Upgrade Cost',
        value=f'**{upgrade_cost}** coins to upgrade to level {factory_data["level"] + 1}',
        inline=False
    )
    
    embed.set_footer(text=f'Balance: {user_data["coins"]} coins | Use /factoryupgrade to upgrade')
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='factoryupgrade', description='Upgrade your factory')
async def factoryupgrade(interaction: discord.Interaction):
    user_data = get_user_balance(interaction.guild.id, interaction.user.id)
    
    if 'factory' not in user_data:
        return await interaction.response.send_message('You don\'t have a factory yet! Use /factory to start one.', ephemeral=True)
    
    factory_data = user_data['factory']
    upgrade_cost = factory_data['level'] * 1000
    
    if user_data['coins'] < upgrade_cost:
        return await interaction.response.send_message(f'You need **{upgrade_cost}** coins to upgrade! You have **{user_data["coins"]}** coins.', ephemeral=True)
    
    user_data['coins'] -= upgrade_cost
    factory_data['level'] += 1
    factory_data['production_rate'] = factory_data['level'] * 10
    save_data()
    
    await interaction.response.send_message(
        f'✅ Factory upgraded to level **{factory_data["level"]}**!\n'
        f'New production rate: **{factory_data["production_rate"]}** coins/minute\n'
        f'Remaining balance: **{user_data["coins"]}** coins'
    )

@bot.tree.command(name='shop', description='View the shop')
async def shop(interaction: discord.Interaction):
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
    
    embed.set_footer(text='Use /buy <item number> to purchase')
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='buy', description='Buy an item from the shop')
@app_commands.describe(item='The item number to buy (1, 2, or 3)')
@app_commands.choices(item=[
    app_commands.Choice(name='1 - Custom Role Color (5000 coins)', value='1'),
    app_commands.Choice(name='2 - VIP Badge (10000 coins)', value='2'),
    app_commands.Choice(name='3 - Mystery Box (2000 coins)', value='3')
])
async def buy(interaction: discord.Interaction, item: app_commands.Choice[str]):
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

