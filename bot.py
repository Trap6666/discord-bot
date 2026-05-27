import discord
from discord.ext import commands
import os
import time

TOKEN = os.environ.get('DISCORD_TOKEN')
STAFF_ROLE_ID = 1508608045826048011
RECRUITMENT_CHANNEL_ID = 1509288416435503155
STAFF_FORMS_CHANNEL_ID = 1509288578763591740
ACCEPTED_CATEGORY_ID = 1509288878857519386

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

# =================== מערכת עזרה ===================

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

# =================== מערכת גיוסים ===================

class RecruitmentModal(discord.ui.Modal, title='מיון לצבא ההגנה לישראל'):
    age = discord.ui.TextInput(
        label='הגיל שלך',
        placeholder='לדוגמה: 18',
        max_length=3
    )
    unit = discord.ui.TextInput(
        label='לאיזה יחידה תרצה להתקבל',
        placeholder='לדוגמה: חיל רגלים',
        max_length=100
    )
    reason = discord.ui.TextInput(
        label='למה דווקא אותך ולא מישהו אחר',
        style=discord.TextStyle.paragraph,
        placeholder='תאר את עצמך...',
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        staff_forms_channel = interaction.guild.get_channel(STAFF_FORMS_CHANNEL_ID)

        embed = discord.Embed(
            title='📋 טופס מיון חדש',
            color=discord.Color.blue()
        )
        embed.add_field(name='👤 מגיש הטופס', value=interaction.user.mention, inline=False)
        embed.add_field(name='🎂 גיל', value=self.age.value, inline=True)
        embed.add_field(name='🎖️ יחידה מבוקשת', value=self.unit.value, inline=True)
        embed.add_field(name='💬 למה אותך', value=self.reason.value, inline=False)
        embed.set_footer(text=f'ID: {interaction.user.id}')

        view = StaffDecisionView(
            applicant=interaction.user,
            age=self.age.value,
            unit=self.unit.value,
            reason=self.reason.value
        )

        await staff_forms_channel.send(embed=embed, view=view)
        await interaction.response.send_message('✅ הטופס שלך נשלח בהצלחה! המתן לתגובת הצוות.', ephemeral=True)


class StaffDecisionView(discord.ui.View):
    def __init__(self, applicant, age, unit, reason):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.age = age
        self.unit = unit
        self.reason = reason

    @discord.ui.button(label='✅ קבלה', style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message('❌ רק צוות יכול להשתמש בכפתורים אלו!', ephemeral=True)
            return

        category = interaction.guild.get_channel(ACCEPTED_CATEGORY_ID)

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            self.applicant: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        channel = await interaction.guild.create_text_channel(
            name=f'מיון-{self.applicant.name}',
            category=category,
            overwrites=overwrites
        )

        await channel.send(
            f'{self.applicant.mention} כל הכבוד! 🎉\n'
            f'עברת את שלב מיוני הטפסים.\n'
            f'תצטרך לקבוע עכשיו שיחה עם צוות על מנת לעבור את שלב ב.'
        )

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message(f'✅ התקבל! נפתח חדר: {channel.mention}', ephemeral=True)

    @discord.ui.button(label='❌ דחייה', style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message('❌ רק צוות יכול להשתמש בכפתורים אלו!', ephemeral=True)
            return

        try:
            await self.applicant.send(
                '❌ טופס המיון שלך נדחה.\n'
                'אם תרצה מידע נוסף, אתה מוזמן לפתוח טיקט.'
            )
        except:
            pass

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.send_message('❌ הטופס נדחה והמשתמש קיבל הודעה.', ephemeral=True)


class RecruitmentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='מיון', style=discord.ButtonStyle.primary, emoji='📋')
    async def start_recruitment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RecruitmentModal())


@bot.command(name='גיוס')
async def recruitment(ctx):
    if ctx.channel.id != RECRUITMENT_CHANNEL_ID:
        await ctx.send('❌ פקודה זו יכולה לשמש רק בערוץ הגיוסים!', ephemeral=True)
        return

    embed = discord.Embed(
        title='🇮🇱 גיוסים לצבא הגנה לישראל',
        description='זוהי מערכת גיוסים לצבא הגנה לישראל\nלחצו על הכפתור למטה כדי להתחיל במיונים.',
        color=discord.Color.blue()
    )

    await ctx.message.delete()
    await ctx.send(embed=embed, view=RecruitmentView())


bot.run(TOKEN)