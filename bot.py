import discord
from discord.ext import commands
import os
import time

TOKEN = os.environ.get('DISCORD_TOKEN')
STAFF_ROLE_ID = 1508608045826048011

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f'✅ הבוט {bot.user} מחובר ועובד!')

@bot.command()
async def היי(ctx):
    await ctx.send(f'היי {ctx.author.name}! 👋')

class HelpButton(discord.ui.View):
    def __init__(self, voice_channel=None):
        super().__init__(timeout=None)
        self.voice_channel = voice_channel
        if voice_channel:
            button = discord.ui.Button(
                label='כניסה לשיחה',
                style=discord.ButtonStyle.green,
                emoji='🎙️'
            )
            button.callback = self.join_callback
            self.add_item(button)

    async def join_callback(self, interaction: discord.Interaction):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message('❌ רק צוות יכול להשתמש בכפתור זה!', ephemeral=True)
            return
        await interaction.response.send_message(f'🎙️ השיחה: {self.voice_channel.mention}', ephemeral=True)

help_cooldowns = {}

async def send_help(ctx):
    user_id = ctx.author.id
    now = time.time()

    if user_id in help_cooldowns:
        time_left = 45 - (now - help_cooldowns[user_id])
        if time_left > 0:
            await ctx.author.send(f'⏳ תוכל להשתמש בפקודה שוב בעוד **{int(time_left)} שניות**!')
            return

    help_cooldowns[user_id] = now

    voice_channel = None
    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel

    staff_role = ctx.guild.get_role(STAFF_ROLE_ID)
    mention = staff_role.mention if staff_role else 'צוות'

    if voice_channel:
        msg = f'🆘 {ctx.author.mention} זקוק לעזרה!\n{mention} נא לסייע.\n🎙️ נמצא בשיחה: {voice_channel.mention}'
    else:
        msg = f'🆘 {ctx.author.mention} זקוק לעזרה!\n{mention} נא לסייע.'

    view = HelpButton(voice_channel)
    await ctx.send(msg, view=view)

@bot.command(name='עזרה')
async def help_he(ctx):
    await send_help(ctx)

@bot.command(name='h')
async def help_h(ctx):
    await send_help(ctx)

@bot.command(name='help')
async def help_en(ctx):
    await send_help(ctx)

@bot.command(name='helpme')
async def help_me(ctx):
    await send_help(ctx)

bot.run(TOKEN)