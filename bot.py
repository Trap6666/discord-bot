import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime

TOKEN = os.environ.get('DISCORD_TOKEN')
STAFF_ROLE_ID = 1508608045826048011
RECRUITMENT_CHANNEL_ID = 1509288416435503155
STAFF_FORMS_CHANNEL_ID = 1509288578763591740
ACCEPTED_CATEGORY_ID = 1509288878857519386
TRANSCRIPT_CHANNEL_ID = 1509323770895138967

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():
    bot.add_view(RecruitmentView())
    print(f'✅ הבוט {bot.user} מחובר ועובד!')

@bot.command()
async def היי(ctx):
    await ctx.send(f'היי {ctx.author.name}! 👋')

# =================== מערכת טפסים ===================

class ApplicationModal(discord.ui.Modal, title='טופס הגשת מועמדות'):
    first_name = discord.ui.TextInput(
        label='השם הפרטי שלך',
        placeholder='לדוגמה: דוד',
        max_length=50
    )
    army_choice = discord.ui.TextInput(
        label='לאיזה צבא אתה רוצה להגיש מועמדות?',
        placeholder='טאליבאן / יחידת הריינג\'רים 75',
        max_length=50
    )
    steam_link = discord.ui.TextInput(
        label='קישור לפרופיל הסטים שלך',
        placeholder='https://steamcommunity.com/id/...',
        max_length=200
    )
    age = discord.ui.TextInput(
        label='בן כמה אתה? (15+)',
        placeholder='לדוגמה: 18',
        max_length=3
    )
    availability = discord.ui.TextInput(
        label='מה הזמינות שלך? (1-10)',
        placeholder='לדוגמה: 8',
        max_length=2
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            age_int = int(self.age.value)
            if age_int < 15:
                await interaction.response.send_message('❌ גיל מינימלי להגשה הוא 15!', ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message('❌ אנא הכנס גיל תקין!', ephemeral=True)
            return

        try:
            avail_int = int(self.availability.value)
            if avail_int < 1 or avail_int > 10:
                await interaction.response.send_message('❌ זמינות חייבת להיות בין 1 ל־10!', ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message('❌ אנא הכנס זמינות תקינה בין 1 ל־10!', ephemeral=True)
            return

        staff_forms_channel = interaction.guild.get_channel(STAFF_FORMS_CHANNEL_ID)

        color = discord.Color.green() if 'טאליבאן' in self.army_choice.value else discord.Color.blue()

        embed = discord.Embed(
            title='📋 טופס מועמדות חדש',
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name='👤 מגיש הטופס', value=interaction.user.mention, inline=False)
        embed.add_field(name='📝 שם פרטי', value=self.first_name.value, inline=True)
        embed.add_field(name='⚔️ צבא מבוקש', value=self.army_choice.value, inline=True)
        embed.add_field(name='🎮 קישור סטים', value=self.steam_link.value, inline=False)
        embed.add_field(name='🎂 גיל', value=self.age.value, inline=True)
        embed.add_field(name='⏰ זמינות', value=f'{self.availability.value}/10', inline=True)
        embed.add_field(name='📊 סטטוס', value='⏳ ממתין לטיפול', inline=True)
        embed.add_field(name='👤 טופל על ידי', value='טרם טופל', inline=True)
        embed.set_footer(text=f'ID: {interaction.user.id}')

        view = StaffDecisionView(
            applicant=interaction.user,
            first_name=self.first_name.value,
            army_choice=self.army_choice.value,
            steam_link=self.steam_link.value,
            age=self.age.value,
            availability=self.availability.value
        )

        await staff_forms_channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            '✅ הטופס שלך נשלח בהצלחה!\nאנא המתן לתגובת הצוות.',
            ephemeral=True
        )


class CloseInterviewView(discord.ui.View):
    def __init__(self, applicant, opened_by, form_data):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.opened_by = opened_by
        self.form_data = form_data

    @discord.ui.button(label='🔒 סגירת מיון', style=discord.ButtonStyle.red)
    async def close_interview(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message('❌ רק צוות יכול לסגור מיון!', ephemeral=True)
            return

        await interaction.response.send_message(
            f'🔒 {interaction.user.mention} סגר את המיון, המיון נסגר עוד 10 שניות.'
        )

        messages = []
        async for message in interaction.channel.history(limit=500, oldest_first=True):
            timestamp = message.created_at.strftime('%d/%m/%Y %H:%M:%S')
            messages.append(f'[{timestamp}] {message.author.display_name}: {message.content}')

        transcript_channel = interaction.guild.get_channel(TRANSCRIPT_CHANNEL_ID)

        embed = discord.Embed(
            title=f'📄 תמלול מיון — {self.applicant.display_name}',
            color=discord.Color.dark_blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name='👤 מועמד', value=self.applicant.mention, inline=True)
        embed.add_field(name='📋 פתח המיון', value=self.opened_by.mention, inline=True)
        embed.add_field(name='🔒 סגר המיון', value=interaction.user.mention, inline=True)
        embed.add_field(name='📝 שם פרטי', value=self.form_data['first_name'], inline=True)
        embed.add_field(name='⚔️ צבא מבוקש', value=self.form_data['army_choice'], inline=True)
        embed.add_field(name='🎮 קישור סטים', value=self.form_data['steam_link'], inline=False)
        embed.add_field(name='🎂 גיל', value=self.form_data['age'], inline=True)
        embed.add_field(name='⏰ זמינות', value=f"{self.form_data['availability']}/10", inline=True)

        transcript_text = '\n'.join(messages) if messages else 'אין הודעות'
        if len(transcript_text) > 1000:
            transcript_text = transcript_text[:1000] + '...'
        embed.add_field(name='📝 תמלול שיחה', value=f'```{transcript_text}```', inline=False)

        await transcript_channel.send(embed=embed)

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

        await asyncio.sleep(10)
        await interaction.channel.delete()


class StaffDecisionView(discord.ui.View):
    def __init__(self, applicant, first_name, army_choice, steam_link, age, availability):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.first_name = first_name
        self.army_choice = army_choice
        self.steam_link = steam_link
        self.age = age
        self.availability = availability

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

        form_data = {
            'first_name': self.first_name,
            'army_choice': self.army_choice,
            'steam_link': self.steam_link,
            'age': self.age,
            'availability': self.availability
        }

        close_view = CloseInterviewView(
            applicant=self.applicant,
            opened_by=interaction.user,
            form_data=form_data
        )

        await channel.send(
            f'{self.applicant.mention} כל הכבוד! 🎉\n'
            f'עברת את שלב מיוני הטפסים.\n'
            f'תצטרך לקבוע עכשיו שיחה עם צוות על מנת לעבור את שלב ב.',
            view=close_view
        )

        original_embed = interaction.message.embeds[0]
        original_embed.set_field_at(
            original_embed.fields.index(next(f for f in original_embed.fields if f.name == '📊 סטטוס')),
            name='📊 סטטוס', value='✅ התקבל', inline=True
        )
        original_embed.set_field_at(
            original_embed.fields.index(next(f for f in original_embed.fields if f.name == '👤 טופל על ידי')),
            name='👤 טופל על ידי', value=interaction.user.mention, inline=True
        )
        original_embed.color = discord.Color.green()

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(embed=original_embed, view=self)
        await interaction.response.send_message(f'✅ התקבל! נפתח חדר: {channel.mention}', ephemeral=True)

    @discord.ui.button(label='❌ דחייה', style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message('❌ רק צוות יכול להשתמש בכפתורים אלו!', ephemeral=True)
            return

        try:
            await self.applicant.send(
                '❌ טופס המועמדות שלך נדחה.\n'
                'אם תרצה מידע נוסף, אתה מוזמן לפתוח טיקט.'
            )
        except:
            pass

        original_embed = interaction.message.embeds[0]
        original_embed.set_field_at(
            original_embed.fields.index(next(f for f in original_embed.fields if f.name == '📊 סטטוס')),
            name='📊 סטטוס', value='❌ נדחה', inline=True
        )
        original_embed.set_field_at(
            original_embed.fields.index(next(f for f in original_embed.fields if f.name == '👤 טופל על ידי')),
            name='👤 טופל על ידי', value=interaction.user.mention, inline=True
        )
        original_embed.color = discord.Color.red()

        for item in self.children:
            item.disabled = True
        await interaction.message.edit(embed=original_embed, view=self)
        await interaction.response.send_message('❌ הטופס נדחה והמשתמש קיבל הודעה.', ephemeral=True)


class RecruitmentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='הגש מועמדות', style=discord.ButtonStyle.primary, emoji='📋')
    async def start_recruitment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())


@bot.command(name='גיוס')
async def recruitment(ctx):
    if ctx.channel.id != RECRUITMENT_CHANNEL_ID:
        await ctx.send('❌ פקודה זו יכולה לשמש רק בערוץ הגיוסים!', ephemeral=True)
        return

    embed = discord.Embed(
        title='⚔️ טפסי הצטרפות',
        description='ברוכים הבאים למערכת ההצטרפות!\nלחצו על הכפתור למטה כדי להגיש מועמדות.',
        color=discord.Color.dark_blue()
    )
    embed.add_field(name='🇺🇸 יחידת הריינג\'רים 75', value='כוח עילית אמריקאי', inline=True)
    embed.add_field(name='☪️ טאליבאן', value='כוחות הטאליבאן', inline=True)
    embed.set_footer(text='גיל מינימלי: 15 | זמינות: 1-10')

    await ctx.message.delete()
    await ctx.send(embed=embed, view=RecruitmentView())


bot.run(TOKEN)