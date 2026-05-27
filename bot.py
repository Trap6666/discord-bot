import discord
from discord.ext import commands
import os

TOKEN = os.environ.get('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ הבוט {bot.user} מחובר ועובד!')

@bot.command()
async def היי(ctx):
    await ctx.send(f'היי {ctx.author.name}! 👋')

bot.run(TOKEN)