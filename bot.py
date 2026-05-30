import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime

TOKEN = os.environ.get('DISCORD_TOKEN')
GUILD_ID = 1508162182909526127
STAFF_ROLE_ID = 1508608045826048011
RECRUITMENT_CHANNEL_ID = 1509288416435503155
STAFF_FORMS_CHANNEL_ID = 1509288578763591740
ACCEPTED_CATEGORY_ID = 1509288878857519386
TRANSCRIPT_CHANNEL_ID = 1509323770895138967
RESULTS_CHANNEL_ID = 1509946894166786058

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():
    bot.add_view(RecruitmentView())
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f'✅ הבוט {bot.user} מחובר! סונכרנו {len(synced)} פקודות.')
        for cmd in synced:
            print(f'  - {cmd.name}')
    except Exception as e:
        print(f'שגיאה בסנכרון: {e}')
@bot.command()
async def היי(ctx):
    await ctx.send(f'היי {ctx.author.name}! 👋')

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


class ArmySelectView(discord.ui.View):
    def __init__(self, action, applicant, form_data, original_message):
        super().__init__(timeout=60)
        self.action = action
        self.applicant = applicant
        self.form_data = form_data
        self.original_message = original_message

    @discord.ui.button(label='טאליבאן ☪️', style=discord.ButtonStyle.grey)
    async def taliban(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle(interaction, 'taliban')

    @discord.ui.button(label='יחידת הריינג\'רים 75 🇺🇸', style=discord.ButtonStyle.grey)
    async def rangers(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle(interaction, 'rangers')

    async def handle(self, interaction: discord.Interaction, army: str):
        results_channel = interaction.guild.get_channel(RESULTS_CHANNEL_ID)

        if self.action == 'accept':
            if army == 'taliban':
                msg = f"{self.applicant.mention} **- 🟢 Your application for the Taliban army has been approved. Please check the Stage 2 room that has opened for you to proceed.**"
            else:
                msg = f"{self.applicant.mention} **- 🟢 Your application for the U.S Army has been approved. Please check the Stage 2 room that has opened for you to proceed.**"

            await results_channel.send(msg)

            category = interaction.guild.get_channel(ACCEPTED_CATEGORY_ID)
            staff_role = interaction.guild.get_role(STAFF_ROLE_ID)

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

            close_view = CloseInterviewView(
                applicant=self.applicant,
                opened_by=interaction.user,
                form_data=self.form_data
            )

            await channel.send(
                f'{self.applicant.mention} כל הכבוד! 🎉\n'
                f'עברת את שלב מיוני הטפסים.\n'
                f'תצטרך לקבוע עכשיו שיחה עם צוות על מנת לעבור את שלב ב.',
                view=close_view
            )

            original_embed = self.original_message.embeds[0]
            original_embed.set_field_at(
                original_embed.fields.index(next(f for f in original_embed.fields if f.name == '📊 סטטוס')),
                name='📊 סטטוס', value='✅ התקבל', inline=True
            )
            original_embed.set_field_at(
                original_embed.fields.index(next(f for f in original_embed.fields if f.name == '👤 טופל על ידי')),
                name='👤 טופל על ידי', value=interaction.user.mention, inline=True
            )
            original_embed.color = discord.Color.green()

            disabled_view = StaffDecisionView.__new__(StaffDecisionView)
            discord.ui.View.__init__(disabled_view, timeout=None)
            for item in StaffDecisionView(self.applicant, '', '', '', '', '').children:
                item.disabled = True
                disabled_view.add_item(item)

            await self.original_message.edit(embed=original_embed, view=disabled_view)
            await interaction.response.edit_message(content=f'✅ התקבל! נפתח חדר: {channel.mention}', view=None)

        else:
            if army == 'taliban':
                msg = f"{self.applicant.mention} **- 🔴 Your application for the Taliban army has been denied. If you would like to receive more information, please open a ticket.**"
            else:
                msg = f"{self.applicant.mention} **- 🔴 Your application for the U.S. Army has been denied. If you would like to receive more information, please open a ticket.**"

            await results_channel.send(msg)

            original_embed = self.original_message.embeds[0]
            original_embed.set_field_at(
                original_embed.fields.index(next(f for f in original_embed.fields if f.name == '📊 סטטוס')),
                name='📊 סטטוס', value='❌ נדחה', inline=True
            )
            original_embed.set_field_at(
                original_embed.fields.index(next(f for f in original_embed.fields if f.name == '👤 טופל על ידי')),
                name='👤 טופל על ידי', value=interaction.user.mention, inline=True
            )
            original_embed.color = discord.Color.red()

            disabled_view = StaffDecisionView.__new__(StaffDecisionView)
            discord.ui.View.__init__(disabled_view, timeout=None)
            for item in StaffDecisionView(self.applicant, '', '', '', '', '').children:
                item.disabled = True
                disabled_view.add_item(item)

            await self.original_message.edit(embed=original_embed, view=disabled_view)
            await interaction.response.edit_message(content='❌ הטופס נדחה והמשתמש קיבל הודעה.', view=None)


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

        form_data = {
            'first_name': self.first_name,
            'army_choice': self.army_choice,
            'steam_link': self.steam_link,
            'age': self.age,
            'availability': self.availability
        }

        army_view = ArmySelectView(
            action='accept',
            applicant=self.applicant,
            form_data=form_data,
            original_message=interaction.message
        )
        await interaction.response.send_message('⚔️ לאיזה צבא התקבל המועמד?', view=army_view, ephemeral=True)

    @discord.ui.button(label='❌ דחייה', style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message('❌ רק צוות יכול להשתמש בכפתורים אלו!', ephemeral=True)
            return

        form_data = {
            'first_name': self.first_name,
            'army_choice': self.army_choice,
            'steam_link': self.steam_link,
            'age': self.age,
            'availability': self.availability
        }

        army_view = ArmySelectView(
            action='reject',
            applicant=self.applicant,
            form_data=form_data,
            original_message=interaction.message
        )
        await interaction.response.send_message('⚔️ לאיזה צבא שייך המועמד שנדחה?', view=army_view, ephemeral=True)


class RecruitmentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='הגש מועמדות', style=discord.ButtonStyle.primary, emoji='📋', custom_id='recruitment_button')
    async def start_recruitment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())


@bot.tree.command(name='גיוס', description='שליחת הודעת גיוס עם כפתור הגשת מועמדות')
@discord.app_commands.default_permissions(administrator=True)
async def recruitment(interaction: discord.Interaction):
    embed = discord.Embed(
        title='⚔️ טפסי הצטרפות',
        description='ברוכים הבאים למערכת ההצטרפות!\nלחצו על הכפתור למטה כדי להגיש מועמדות.',
        color=discord.Color.dark_blue()
   )
    embed.add_field(name='יחידת הריינג\'רים 75', value='כוח עילית אמריקאי', inline=True)
    embed.add_field(name='☪️ טאליבאן', value='כוחות הטאליבאן', inline=True)
    embed.set_footer(text='גיל מינימלי: 15 | זמינות: 1-10')

    await interaction.response.send_message('✅המערכת הופעלה בהצלחה', ephemeral=True)
    await interaction.channel.send(embed=embed, view=RecruitmentView())

@bot.tree.command(name='setup', description='הגדרת מערכת הגיוסים')
@discord.app_commands.default_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    await interaction.response.send_message('⚙️ מתחילים בהגדרת המערכת! אנא ענה על השאלות הבאות.\n\nשלח את ה־**mention** של רול הצוות (לדוגמה: @צוות)', ephemeral=True)

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        # רול צוות
        msg = await bot.wait_for('message', check=check, timeout=60)
        if not msg.role_mentions:
            await interaction.followup.send('❌ לא זוהה רול, נסה שוב עם /setup', ephemeral=True)
            return
        staff_role_id = msg.role_mentions[0].id
        await msg.delete()

        # צ'אט גיוסים
        await interaction.followup.send('✅ רול צוות נשמר!\n\nעכשיו שלח **mention** של צ\'אט הגיוסים (לדוגמה: #גיוסים)', ephemeral=True)
        msg = await bot.wait_for('message', check=check, timeout=60)
        if not msg.channel_mentions:
            await interaction.followup.send('❌ לא זוהה צ\'אט, נסה שוב עם /setup', ephemeral=True)
            return
        recruitment_channel_id = msg.channel_mentions[0].id
        await msg.delete()

        # צ'אט טפסים
        await interaction.followup.send('✅ צ\'אט גיוסים נשמר!\n\nעכשיו שלח **mention** של צ\'אט הטפסים לצוות (לדוגמה: #טפסים)', ephemeral=True)
        msg = await bot.wait_for('message', check=check, timeout=60)
        if not msg.channel_mentions:
            await interaction.followup.send('❌ לא זוהה צ\'אט, נסה שוב עם /setup', ephemeral=True)
            return
        staff_forms_channel_id = msg.channel_mentions[0].id
        await msg.delete()

        # קטגוריה
        await interaction.followup.send('✅ צ\'אט טפסים נשמר!\n\nעכשיו שלח את ה־**ID** של הקטגוריה לחדרי מיון', ephemeral=True)
        msg = await bot.wait_for('message', check=check, timeout=60)
        try:
            accepted_category_id = int(msg.content.strip())
        except ValueError:
            await interaction.followup.send('❌ ID לא תקין, נסה שוב עם /setup', ephemeral=True)
            return
        await msg.delete()

        # צ'אט תמלולים
        await interaction.followup.send('✅ קטגוריה נשמרה!\n\nעכשיו שלח **mention** של צ\'אט התמלולים (לדוגמה: #תמלולים)', ephemeral=True)
        msg = await bot.wait_for('message', check=check, timeout=60)
        if not msg.channel_mentions:
            await interaction.followup.send('❌ לא זוהה צ\'אט, נסה שוב עם /setup', ephemeral=True)
            return
        transcript_channel_id = msg.channel_mentions[0].id
        await msg.delete()

        # צ'אט תוצאות
        await interaction.followup.send('✅ צ\'אט תמלולים נשמר!\n\nעכשיו שלח **mention** של צ\'אט התוצאות (לדוגמה: #תוצאות)', ephemeral=True)
        msg = await bot.wait_for('message', check=check, timeout=60)
        if not msg.channel_mentions:
            await interaction.followup.send('❌ לא זוהה צ\'אט, נסה שוב עם /setup', ephemeral=True)
            return
        results_channel_id = msg.channel_mentions[0].id
        await msg.delete()

        # שמירת ההגדרות
        global STAFF_ROLE_ID, RECRUITMENT_CHANNEL_ID, STAFF_FORMS_CHANNEL_ID, ACCEPTED_CATEGORY_ID, TRANSCRIPT_CHANNEL_ID, RESULTS_CHANNEL_ID
        STAFF_ROLE_ID = staff_role_id
        RECRUITMENT_CHANNEL_ID = recruitment_channel_id
        STAFF_FORMS_CHANNEL_ID = staff_forms_channel_id
        ACCEPTED_CATEGORY_ID = accepted_category_id
        TRANSCRIPT_CHANNEL_ID = transcript_channel_id
        RESULTS_CHANNEL_ID = results_channel_id

        await interaction.followup.send(
            '✅ **ההגדרות נשמרו בהצלחה!**\n\n'
            f'👮 רול צוות: <@&{staff_role_id}>\n'
            f'📢 צ\'אט גיוסים: <#{recruitment_channel_id}>\n'
            f'📋 צ\'אט טפסים: <#{staff_forms_channel_id}>\n'
            f'🗂️ קטגוריה: {accepted_category_id}\n'
            f'📄 צ\'אט תמלולים: <#{transcript_channel_id}>\n'
            f'📊 צ\'אט תוצאות: <#{results_channel_id}>\n\n'
            f'עכשיו תוכל להריץ **/גיוס** לשליחת הודעת הגיוס!',
            ephemeral=True
        )

    except asyncio.TimeoutError:
        await interaction.followup.send('❌ פג הזמן! נסה שוב עם /setup', ephemeral=True)

bot.run(TOKEN)