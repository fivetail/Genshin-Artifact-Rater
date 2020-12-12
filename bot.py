import rate_artifact as ra

import os
import sys

import discord
import validators
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', 0))
DEVELOPMENT = os.getenv('DEVELOPMENT', 'False') == 'True'

calls = 0

bot = commands.Bot(command_prefix='-')

@bot.event
async def on_ready():
	msg = f'{bot.user.name} has connected to {len(bot.guilds)} servers'
	print(msg)
	if CHANNEL_ID:
		channel = bot.get_channel(CHANNEL_ID)
		await channel.send(msg)

@bot.event
async def on_disconnect():
	if CHANNEL_ID:
		channel = bot.get_channel(CHANNEL_ID)
		await channel.send(user, f'{bot.user.name} disconnected after {calls} calls')

opt_to_key = {'hp': 'HP', 'atk': 'ATK', 'atk%': 'ATK%', 'er': 'Energy Recharge%', 'em': 'Elemental Mastery',
			  'phys': 'Physical DMG%', 'cr': 'CRIT Rate%', 'cd': 'CRIT DMG%', 'elem': 'Elemental DMG%',
			  'hp%': 'HP%', 'def%': 'DEF%', 'heal': 'Healing%', 'def': 'DEF', 'lvl': 'Level'}

@bot.command(name='rate')
async def rate(ctx):
	'''
	Rate an artifact against an optimal 5* artifact. Put the command and image in the same message.

	If you would like to add it to your private server use the link:
	https://discord.com/api/oauth2/authorize?client_id=774612459692621834&permissions=3072&scope=bot

	-rate <image/url> [lvl=<level>] [<stat>=<weight> ...]

	If you have any issues, please contact shrubin#1866 on discord or use the -feedback command.
	Source code available at https://github.com/shrubin/Genshin-Artifact-Rater

	Default weights

	ATK%, DMG%, Crit - 1
	ATK, EM, Recharge - 0.5
	Everything else - 0

	Options

	lvl: Compare to specified artifact level (default: <artifact_level>)
	-rate lvl=20

	<stat>: Set custom weights (valued between 0 and 1)
	-rate atk=1 er=0 atk%=0.5

	<stat> is any of HP, HP%, ATK, ATK%, ER (Recharge), EM, PHYS, CR (Crit Rate), CD (Crit Damage), ELEM (Elemental DMG%), Heal, DEF, DEF%
	'''
	global calls
	options = ctx.message.content.split()[1:]
	if options and validators.url(options[0]):
		url = options[0]
		options = options[1:]
	elif ctx.message.attachments:
		url = ctx.message.attachments[0].url
	else:
		return
	options = {opt_to_key[option.split('=')[0].lower()] : float(option.split('=')[1]) for option in options}
	suc, text = await ra.ocr(url)
	calls += 1
	if suc:
		level, results = ra.parse(text)
		if 'Level' in options:
			level = int(options['Level'])
			del options['Level']
		elif level == None:
			level = 20
		score, main_score, sub_score = ra.rate(level, results, options)

		if score <= 50:
			color = discord.Color.blue()
		elif score > 50 and score <= 75:
			color = discord.Color.purple()
		else:
			color = discord.Color.orange()

		msg = f'\n\n**{results[0][0]}: {results[0][1]}**'
		for result in results[1:]:
			msg += f'\n{result[0]}: {result[1]}'
		msg += f'\n\n**Overall Rating: {score:.2f}%**'
		msg += f'\nMain Stat Rating: {main_score:.2f}%'
		msg += f'\nSubstat Rating: {sub_score:.2f}%'

		embed = discord.Embed(color=color)
		embed.add_field(name=f'Artifact Level: +{level}', value=msg)
		embed.set_footer(text=f'Requested by {ctx.message.author}', icon_url=ctx.message.author.avatar_url)

		if not DEVELOPMENT:
			await ctx.send(embed=embed)
		elif CHANNEL_ID:
			channel = bot.get_channel(CHANNEL_ID)
			await channel.send(embed=embed)
	else:
		msg = f'OCR failed. Error: {text}'
		if 'Timed out' in text:
			msg += ', please try again in a few minutes'
		print(msg)
		if not DEVELOPMENT:
			await ctx.send(msg)
		elif CHANNEL_ID:
			channel = bot.get_channel(CHANNEL_ID)
			await channel.send(msg)

@bot.command(name='feedback')
async def feedback(ctx):
	'''
	Send feedback with issues or ideas for the bot. Up to one image can be sent.

	-feedback <message> [image]
	'''
	if CHANNEL_ID:
		channel = bot.get_channel(CHANNEL_ID)
		embed = discord.Embed()
		if ctx.message.attachments:
			embed.set_image(url=ctx.message.attachments[0].url)
		elif ctx.message.embeds:
			embed.set_image(url=ctx.message.embeds[0].url)
		else:
			embed = None
		await channel.send(f'{ctx.message.author}: {ctx.message.content}', embed=embed)

if TOKEN:
	bot.run(TOKEN)
else:
	print('Error: DISCORD_TOKEN not found')
