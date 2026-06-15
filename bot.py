import discord
from discord.ext import commands
import os
import aiohttp
import json
import asyncio
from datetime import datetime
from typing import Optional

TOKEN = os.environ.get('DISCORD_TOKEN')
FIVEM_IP = '88.214.55.234'
FIVEM_PORT = 30120
PLAYER_LIST_CHANNEL_ID = 1503477897959047374
US_ROLE_ID = 1503477897443282962
TALIBAN_ROLE_ID = 1503477897451798662
CONFIG_FILE = 'guild_configs.json'


def load_configs():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return {}


def save_configs():
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({str(k): v for k, v in guild_configs.items()}, f, ensure_ascii=False, indent=2)


guild_configs = load_configs()


def get_config(guild_id):
    return guild_configs.get(guild_id)


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
        synced = await bot.tree.sync()
        print(f'✅ הבוט {bot.user} מחובר! סונכרנו {len(synced)} פקודות גלובליות.')
        for cmd in synced:
            print(f'  - {cmd.name}')
    except Exception as e:
        print(f'שגיאה בסנכרון: {e}')
    bot.loop.create_task(update_status())
    bot.loop.create_task(update_player_list())


async def update_status():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'http://{FIVEM_IP}:{FIVEM_PORT}/players.json',
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={'User-Agent': 'Mozilla/5.0'},
                    ssl=False
                ) as resp:
                    if resp.status == 200:
                        players = await resp.json()
                        count = len(players)
                    else:
                        count = 0
        except Exception as e:
            print(f'שגיאת FiveM: {e}')
            count = 0

        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name=f'WestSide MilSim | {count} שחקנים'
            )
        )
        await asyncio.sleep(60)


async def update_player_list():
    await bot.wait_until_ready()
    message_id = None

    while not bot.is_closed():
        try:
            for guild in bot.guilds:
                channel = guild.get_channel(PLAYER_LIST_CHANNEL_ID)
                if not channel:
                    continue

                us_role = guild.get_role(US_ROLE_ID)
                taliban_role = guild.get_role(TALIBAN_ROLE_ID)

                us_members = [m.display_name for m in guild.members if us_role in m.roles]
                taliban_members = [m.display_name for m in guild.members if taliban_role in m.roles]

                embed = discord.Embed(
                    title='🎮 רשימת שחקנים פעילים',
                    color=0x000000,
                    timestamp=datetime.utcnow()
                )

                us_value = '\n'.join([f'• {name}' for name in us_members[:30]]) if us_members else 'אין שחקנים'
                if len(us_members) > 30:
                    us_value += f'\n... ועוד {len(us_members) - 30}'
                us_value = us_value[:1024]

                taliban_value = '\n'.join([f'• {name}' for name in taliban_members[:30]]) if taliban_members else 'אין שחקנים'
                if len(taliban_members) > 30:
                    taliban_value += f'\n... ועוד {len(taliban_members) - 30}'
                taliban_value = taliban_value[:1024]

                embed.add_field(
                    name=f'🇺🇸 יחידת הריינג\'רים 75 ({len(us_members)})',
                    value=us_value,
                    inline=True
                )
                embed.add_field(
                    name=f'☪️ טאליבאן ({len(taliban_members)})',
                    value=taliban_value,
                    inline=True
                )
                embed.set_footer(text='מתעדכן כל 2 דקות')

                if message_id:
                    try:
                        msg = await channel.fetch_message(message_id)
                        await msg.edit(embed=embed)
                    except:
                        msg = await channel.send(embed=embed)
                        message_id = msg.id
                else:
                    msg = await channel.send(embed=embed)
                    message_id = msg.id

        except Exception as e:
            print(f'שגיאת player list: {e}')

        await asyncio.sleep(120)


@bot.command()
async def היי(ctx):
    await ctx.send(f'היי {ctx.author.name}! 👋')


class ApplicationModal1(discord.ui.Modal, title='טופס הגשת מועמדות - חלק א'):
    name = discord.ui.TextInput(
        label='מה השם שלך?',
        placeholder='לדוגמה: דוד',
        max_length=50
    )
    steam_link = discord.ui.TextInput(
        label='קישור למשתמש סטים שלך',
        placeholder='https://steamcommunity.com/id/...',
        max_length=200
    )
    age = discord.ui.TextInput(
        label='בן כמה אתה?',
        placeholder='לדוגמה: 18',
        max_length=3
    )
    army_choice = discord.ui.TextInput(
        label='לאיזה ארגון תרצה להגיש מועמדות?',
        placeholder='טאליבאן / יחידת הריינג\'רים 75',
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        view = Part2ButtonView(
            name=self.name.value,
            steam_link=self.steam_link.value,
            age=self.age.value,
            army_choice=self.army_choice.value
        )
        await interaction.response.send_message(
            '✅ חלק א\' התקבל! לחץ על הכפתור להמשיך לחלק ב\'.',
            view=view,
            ephemeral=True
        )


class Part2ButtonView(discord.ui.View):
    def __init__(self, name, steam_link, age, army_choice):
        super().__init__(timeout=300)
        self.name = name
        self.steam_link = steam_link
        self.age = age
        self.army_choice = army_choice

    @discord.ui.button(label='המשך לחלק ב\' ←', style=discord.ButtonStyle.primary)
    async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ApplicationModal2(
                name=self.name,
                steam_link=self.steam_link,
                age=self.age,
                army_choice=self.army_choice
            )
        )


class ApplicationModal2(discord.ui.Modal, title='טופס הגשת מועמדות - חלק ב'):
    def __init__(self, name, steam_link, age, army_choice):
        super().__init__()
        self.name_val = name
        self.steam_link_val = steam_link
        self.age_val = age
        self.army_choice_val = army_choice

    experience = discord.ui.TextInput(
        label='האם יש לך ניסיון קודם בשרתי מילסים?',
        placeholder='אם כן, פרט...',
        style=discord.TextStyle.long,
        max_length=1000
    )
    why_join = discord.ui.TextInput(
        label='למה אתה רוצה להצטרף לשרת?',
        placeholder='כתוב כאן...',
        style=discord.TextStyle.long,
        max_length=1000
    )
    about = discord.ui.TextInput(
        label='ספר לנו על עצמך',
        placeholder='כתוב כאן...',
        style=discord.TextStyle.long,
        max_length=1000
    )
    rules = discord.ui.TextInput(
        label='מהם החוקים RDM - VDM - MG - NITRP?',
        placeholder='הסבר כל חוק...',
        style=discord.TextStyle.long,
        max_length=1000
    )
    notes = discord.ui.TextInput(
        label='הערות (לא חובה)',
        placeholder='אם יש משהו נוסף שתרצה להוסיף...',
        style=discord.TextStyle.long,
        max_length=500,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        config = get_config(interaction.guild.id)
        if not config:
            await interaction.response.send_message(
                '❌ המערכת לא הוגדרה בשרת הזה! בקש מאדמין להריץ /setup',
                ephemeral=True
            )
            return

        staff_forms_channel = interaction.guild.get_channel(config['staff_forms_channel_id'])
        if staff_forms_channel is None:
            await interaction.response.send_message(
                '❌ ערוץ הטפסים לא נמצא! בקש מאדמין להריץ /setup מחדש.',
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title='📋 טופס מועמדות חדש',
            color=0x000000,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name='👤 מגיש הטופס', value=interaction.user.mention, inline=False)
        embed.add_field(name='📝 שם', value=self.name_val, inline=True)
        embed.add_field(name='⚔️ ארגון מבוקש', value=self.army_choice_val, inline=True)
        embed.add_field(name='🎂 גיל', value=self.age_val, inline=True)
        embed.add_field(name='🎮 קישור סטים', value=self.steam_link_val, inline=False)
        embed.add_field(name='🎖️ ניסיון במילסים', value=self.experience.value, inline=False)
        embed.add_field(name='❓ למה להצטרף', value=self.why_join.value, inline=False)
        embed.add_field(name='📖 על עצמו', value=self.about.value, inline=False)
        embed.add_field(name='📜 ידע בחוקים', value=self.rules.value, inline=False)
        embed.add_field(name='📌 הערות', value=self.notes.value if self.notes.value else 'אין', inline=False)
        embed.add_field(name='📊 סטטוס', value='⏳ ממתין לטיפול', inline=True)
        embed.add_field(name='👤 טופל על ידי', value='טרם טופל', inline=True)
        embed.set_footer(text=f'ID: {interaction.user.id}')

        view = StaffDecisionView(
            applicant=interaction.user,
            first_name=self.name_val,
            army_choice=self.army_choice_val,
            steam_link=self.steam_link_val,
            age=self.age_val,
            availability=f'ניסיון: {self.experience.value}'
        )

        staff_role = interaction.guild.get_role(config['staff_role_id'])
        await staff_forms_channel.send(content=staff_role.mention if staff_role else '', embed=embed, view=view)
        await interaction.response.send_message(
            '✅ הטופס שלך נשלח בהצלחה!\nאנא המתן לתגובת הצוות.',
            ephemeral=True
        )


class RejectionReasonView(discord.ui.View):
    def __init__(self, applicant, form_data, original_message, army):
        super().__init__(timeout=60)
        self.applicant = applicant
        self.form_data = form_data
        self.original_message = original_message
        self.army = army

    async def send_rejection(self, interaction: discord.Interaction, reason_text: str):
        config = get_config(interaction.guild.id)
        results_channel = interaction.guild.get_channel(config['results_channel_id'])

        if self.army == 'taliban':
            unit = "Taliban <:taliban6763730_1280:1507845143464771674>"
        else:
            unit = "Rangers <:3swd845:1507845088003362856>"

        msg = f"{self.applicant.mention} 🔴 The application you submitted to the {unit} {reason_text}"

        if results_channel:
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

        disabled_view = discord.ui.View(timeout=None)
        for item in StaffDecisionView(self.applicant, '', '', '', '', '').children:
            item.disabled = True
            disabled_view.add_item(item)

        await self.original_message.edit(embed=original_embed, view=disabled_view)
        await interaction.response.edit_message(content='❌ הטופס נדחה והמשתמש קיבל הודעה.', view=None)

    @discord.ui.button(label='📋 הטופס סגור', style=discord.ButtonStyle.grey)
    async def closed_forms(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_rejection(interaction, 'has been rejected due to Temporarily Closed Forms.')

    @discord.ui.button(label='📝 חוסר בפרטים', style=discord.ButtonStyle.grey)
    async def lack_of_details(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_rejection(interaction, 'has been rejected due to a lack of detailed information.')

    @discord.ui.button(label='📜 חוסר ידע בחוקים', style=discord.ButtonStyle.grey)
    async def lack_of_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_rejection(interaction, 'has been rejected due to lack of rules knowledge.')


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
        config = get_config(interaction.guild.id)
        if not config:
            await interaction.response.send_message('❌ המערכת לא הוגדרה בשרת הזה!', ephemeral=True)
            return

        results_channel = interaction.guild.get_channel(config['results_channel_id'])

        if self.action == 'accept':
            if army == 'taliban':
                msg = f"{self.applicant.mention} 🟢 Your application for the Taliban <:taliban6763730_1280:1507845143464771674> has been approved. Please check the Phase B room that has opened for you to proceed."
            else:
                msg = f"{self.applicant.mention} 🟢 Your application for the Rangers <:3swd845:1507845088003362856> has been approved. Please check the Phase B room that has opened for you to proceed."

            if results_channel:
                await results_channel.send(msg)

            category = interaction.guild.get_channel(config['accepted_category_id'])
            staff_role = interaction.guild.get_role(config['staff_role_id'])

            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                self.applicant: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

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

            disabled_view = discord.ui.View(timeout=None)
            for item in StaffDecisionView(self.applicant, '', '', '', '', '').children:
                item.disabled = True
                disabled_view.add_item(item)

            await self.original_message.edit(embed=original_embed, view=disabled_view)
            await interaction.response.edit_message(content=f'✅ התקבל! נפתח חדר: {channel.mention}', view=None)

        else:
            reason_view = RejectionReasonView(
                applicant=self.applicant,
                form_data=self.form_data,
                original_message=self.original_message,
                army=army
            )
            await interaction.response.edit_message(content='❌ מה סיבת הדחייה?', view=reason_view)


class CloseInterviewView(discord.ui.View):
    def __init__(self, applicant, opened_by, form_data):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.opened_by = opened_by
        self.form_data = form_data

    @discord.ui.button(label='🔒 סגירת מיון', style=discord.ButtonStyle.red)
    async def close_interview(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = get_config(interaction.guild.id)
        if not config:
            await interaction.response.send_message('❌ המערכת לא הוגדרה בשרת הזה!', ephemeral=True)
            return

        staff_role = interaction.guild.get_role(config['staff_role_id'])
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

        transcript_channel = interaction.guild.get_channel(config['transcript_channel_id'])

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
        embed.add_field(name='🎖️ ניסיון', value=self.form_data['availability'], inline=False)

        transcript_text = '\n'.join(messages) if messages else 'אין הודעות'
        if len(transcript_text) > 1000:
            transcript_text = transcript_text[:1000] + '...'
        embed.add_field(name='📝 תמלול שיחה', value=f'```{transcript_text}```', inline=False)

        if transcript_channel:
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
        config = get_config(interaction.guild.id)
        if not config:
            await interaction.response.send_message('❌ המערכת לא הוגדרה בשרת הזה!', ephemeral=True)
            return

        staff_role = interaction.guild.get_role(config['staff_role_id'])
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
        config = get_config(interaction.guild.id)
        if not config:
            await interaction.response.send_message('❌ המערכת לא הוגדרה בשרת הזה!', ephemeral=True)
            return

        staff_role = interaction.guild.get_role(config['staff_role_id'])
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

    @discord.ui.button(label='הגש מועמדות', style=discord.ButtonStyle.danger, emoji='📋', custom_id='recruitment_button')
    async def start_recruitment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal1())


@bot.tree.command(name='גיוס', description='שליחת הודעת גיוס עם כפתור הגשת מועמדות')
@discord.app_commands.default_permissions(administrator=True)
async def recruitment(interaction: discord.Interaction):
    config = get_config(interaction.guild.id)
    if not config:
        await interaction.response.send_message(
            '❌ המערכת לא הוגדרה בשרת הזה! הרץ קודם /setup',
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title='🪖 הצטרפות לשרת',
        description=(
            '**מעוניינים להצטרף?** לחץ על הכפתור שמתחת ומלאו טופס קצר.\n'
            'לאחר אישור הטופס, יקבע עבורכם שיחת מיון עם צוות.\n\n'
            '━━━━━━━━━━━━━━━━━━━━━━\n\n'
            '**📋 תנאי קבלה:**\n'
            '🎙️ חובה מיקרופון עובד ותקין.\n'
            '🧠 ידע קודם ורלוונטי במערכת המילסים.\n'
            '📝 טפסים שיימצאו בלתי רציניים, חסרי השקעה או שאינם עומדים בסטנדרטים של הצוות ייפסלו.\n'
            '🚫 חל איסור מוחלט על השתייכות מקבילה בשרתים אחרים מאותו הסוג.\n'
            '⏰ זמן הטיפול המשוער הינו עד 24 שעות ממועד ההגשה.\n\n'
            '━━━━━━━━━━━━━━━━━━━━━━'
        ),
        color=0x000000
    )
    embed.add_field(name='🇺🇸 הריינג\'רים 75', value='כוח עילית אמריקאי', inline=True)
    embed.add_field(name='☪️ טאליבאן', value='כוחות הטאליבאן', inline=True)
    embed.add_field(name='\u200b', value='━━━━━━━━━━━━━━━━━━━━━━', inline=False)
    embed.set_footer(text='WestSide MilSim [BETA]')
    embed.set_image(url='https://i.postimg.cc/cHBFR3zw/Code-Generated-Image-2.gif')

    await interaction.response.send_message('✅ המערכת הופעלה בהצלחה', ephemeral=True)
    await interaction.channel.send(embed=embed, view=RecruitmentView())


@bot.tree.command(name='setup', description='הגדרת מערכת הגיוסים')
@discord.app_commands.default_permissions(administrator=True)
async def setup(
    interaction: discord.Interaction,
    staff_role: discord.Role,
    recruitment_channel: discord.TextChannel,
    staff_forms_channel: discord.TextChannel,
    accepted_category: str,
    transcript_channel: discord.TextChannel,
    results_channel: discord.TextChannel,
    invite_channel: Optional[discord.TextChannel] = None
):
    try:
        category_id = int(accepted_category)
        category = interaction.guild.get_channel(category_id)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message('❌ קטגוריה לא נמצאה! בדוק את ה־ID.', ephemeral=True)
            return
    except ValueError:
        await interaction.response.send_message('❌ ID קטגוריה לא תקין!', ephemeral=True)
        return

    guild_configs[interaction.guild.id] = {
        'staff_role_id': staff_role.id,
        'recruitment_channel_id': recruitment_channel.id,
        'staff_forms_channel_id': staff_forms_channel.id,
        'accepted_category_id': category_id,
        'transcript_channel_id': transcript_channel.id,
        'results_channel_id': results_channel.id,
        'invite_channel_id': invite_channel.id if invite_channel else None,
    }
    save_configs()

    invite_text = invite_channel.mention if invite_channel else 'לא הוגדר'

    await interaction.response.send_message(
        '✅ **ההגדרות נשמרו בהצלחה לשרת הזה!**\n\n'
        f'👮 רול צוות: {staff_role.mention}\n'
        f'📢 צ\'אט גיוסים: {recruitment_channel.mention}\n'
        f'📋 צ\'אט טפסים: {staff_forms_channel.mention}\n'
        f'🗂️ קטגוריה: {category.name}\n'
        f'📄 צ\'אט תמלולים: {transcript_channel.mention}\n'
        f'📊 צ\'אט תוצאות: {results_channel.mention}\n'
        f'🔗 צ\'אט הזמנות: {invite_text}\n\n'
        f'עכשיו תוכל להריץ **/גיוס** לשליחת הודעת הגיוס!',
        ephemeral=True
    )


@bot.tree.command(name='unsetup', description='איפוס הגדרות מערכת הגיוסים')
@discord.app_commands.default_permissions(administrator=True)
async def unsetup(interaction: discord.Interaction):
    if interaction.guild.id in guild_configs:
        del guild_configs[interaction.guild.id]
        save_configs()

    await interaction.response.send_message(
        '✅ כל ההגדרות אופסו בהצלחה לשרת הזה!\nתוכל להגדיר מחדש עם **/setup**',
        ephemeral=True
    )


@bot.tree.command(name='invite', description='שליחת קישור הצטרפות לשחקן')
@discord.app_commands.default_permissions(manage_roles=True)
async def invite(interaction: discord.Interaction, שחקן: discord.Member):
    config = get_config(interaction.guild.id)
    if not config or not config.get('invite_channel_id'):
        await interaction.response.send_message(
            '❌ ערוץ ההזמנות לא הוגדר בשרת הזה! הרץ /setup והגדר אותו.',
            ephemeral=True
        )
        return

    try:
        channel = interaction.guild.get_channel(config['invite_channel_id'])
        if not channel:
            await interaction.response.send_message('❌ לא נמצא הצ\'אט!', ephemeral=True)
            return

        invite_link = await channel.create_invite(
            max_uses=1,
            unique=True,
            reason=f'Invite נשלח על ידי {interaction.user} ל־{שחקן}'
        )

        try:
            await שחקן.send(
                f'👋 היי {שחקן.name}!\n'
                f'🔗 קישור: {invite_link.url}\n\n'
                f'⚠️ הקישור תקף לשימוש אחד בלבד!'
            )
            await interaction.response.send_message(f'✅ הקישור נשלח ל־{שחקן.mention} בהצלחה!', ephemeral=True)
        except:
            await interaction.response.send_message(f'❌ לא ניתן לשלוח הודעה פרטית ל־{שחקן.mention}!', ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f'❌ שגיאה: {e}', ephemeral=True)


bot.run(TOKEN)