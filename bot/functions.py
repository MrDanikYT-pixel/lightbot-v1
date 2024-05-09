from collections import Counter
from typing import Any, OrderedDict
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import dotenv
import colorama
import datetime
import aiosqlite
import lightbulb
import hikari
import pytz
import commands
import asyncio
import functools
import emoji
import random
import re
import pickle
import zipfile
import io
import os
import time
import info
import traceback
import miru
import aiohttp
from PIL import Image, ImageDraw
import numpy as np
import logging
dotenv.load_dotenv()

premium_code_key = "idealightmrdannw"
__filename__ = os.path.basename(__file__)
filename = os.path.splitext(__filename__)[0]
logger = logging.getLogger(f"{__package__.split('.')[-1]}.{filename}")


async def async_run(func, *args, **kwargs) -> str:
    loop = asyncio.get_running_loop()
    partial_func = functools.partial(func, **kwargs)
    _func = await loop.run_in_executor(None, partial_func, *args)
    return _func


def only_guild_command(bot_plugin: lightbulb.BotApp | lightbulb.Plugin):
    def decorator(func: lightbulb.CommandLike):
        func = lightbulb.app_command_permissions(dm_enabled=False)(func)
        func = bot_plugin.command(func)
        return func
    return decorator


def ceil(num: float) -> int:
    if num.is_integer():
        return int(num)
    else:
        _num = int(num)
        return int(_num + 1)


class Crypt:
    @staticmethod
    def encrypt(key, message) -> str:
        cipher = AES.new(key.encode('utf-8'), AES.MODE_EAX)
        nonce = cipher.nonce
        padded_message = pad(message.encode('utf-8'), AES.block_size)
        ciphertext, tag = cipher.encrypt_and_digest(padded_message)
        text = nonce + ciphertext + tag
        text_base64 = base64.b64encode(text)
        return text_base64.decode('utf-8')

    @staticmethod
    def decrypt(key, ciphertext_base64) -> str | None:
        ciphertext = base64.b64decode(ciphertext_base64)
        nonce = ciphertext[:16]
        tag = ciphertext[-16:]
        ciphertext = ciphertext[16:-16]
        cipher = AES.new(key.encode('utf-8'), AES.MODE_EAX, nonce=nonce)
        plaintext = cipher.decrypt(ciphertext)
        try:
            cipher.verify(tag)
            unpadded_text_bytes = unpad(plaintext, AES.block_size)
            return unpadded_text_bytes.decode('utf-8')
        except ValueError:
            return None


class AsyncCrypt(Crypt):
    @staticmethod
    async def encrypt(key, message):
        await async_run(Crypt.encrypt, key, message)

    @staticmethod
    async def decrypt(key, ciphertext_base64):
        await async_run(Crypt.decrypt, key, ciphertext_base64)


class crypt(Crypt):
    ...


class Setting:
    def __init__(self, db: aiosqlite.Connection, key: str) -> None:
        self.db = db
        self.key = key

    async def get(self, default: str | tuple | None = None) -> tuple[str, str] | tuple[str, None] | tuple[None, str] | tuple[None, None]:
        key = self.key
        sql = await self.db.cursor()
        result = await (await sql.execute("SELECT value, value_2 FROM settings WHERE key = ?", (key, ))).fetchone()
        if result is None:
            if isinstance(default, str):
                await sql.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?)", (key, default)
                )
                result = (default, None)
            elif isinstance(default, tuple):
                await sql.execute(
                    "INSERT INTO settings (key, value, value_2) VALUES (?, ?, ?)", (key, default[0], default[1])
                )
                result = default
        if result is None:
            result = (None, None)
        return result

    async def set(self, *, value: str | None = None, value_2: str | None = None):
        key = self.key
        sql = await self.db.cursor()
        result = await (await sql.execute("SELECT value, value_2 FROM settings WHERE key = ?", (key, ))).fetchone()
        valuem = value_2 if value is None else value
        if result is None:
            if value_2 is None or value is None:
                await sql.execute(
                    f"INSERT INTO settings (key, {'value_2' if value is None else 'value'}) VALUES (?, ?)", (key, valuem)
                )
            else:
                await sql.execute(
                    "INSERT INTO settings (key, value, value_2) VALUES (?, ?, ?)", (key, value, value_2)
                )
        else:
            if value_2 is None or value is None:
                await sql.execute(
                    f"UPDATE settings SET {'value_2' if value is None else 'value'} = ? WHERE key = ?", (valuem, key)
                )
            else:
                await sql.execute(
                    "UPDATE settings SET value = ?, value_2 = ? WHERE key = ?", (value, value_2, key)
                )


class BlobVars:
    def __init__(self, db: aiosqlite.Connection, key: str) -> None:
        self.db = db
        self.key = key

    async def get(self, default: list | tuple | frozenset | set | dict | None = None) -> Any:
        key = self.key
        sql = await self.db.cursor()
        result = await (await sql.execute("SELECT value FROM blobvars WHERE key = ?", (key, ))).fetchone()
        if result is None and default is not None:
            bts = pickle.dumps(default)
            await sql.execute(
                "INSERT INTO blobvars (key, value) VALUES (?, ?)", (key, bts)
            )
            result = default
        if isinstance(result, tuple):
            result = result[0]
        if isinstance(result, bytes):
            result = pickle.loads(result)
        return result

    async def set(self, value: list | tuple | frozenset | set | dict):
        key = self.key
        sql = await self.db.cursor()
        bts = pickle.dumps(value)
        result = await (await sql.execute("SELECT value FROM blobvars WHERE key = ?", (key, ))).fetchone()
        if result is None:
            await sql.execute(
                "INSERT INTO blobvars (key, value) VALUES (?, ?)", (key, bts)
            )
        else:
            await sql.execute(
                "UPDATE blobvars SET value = ? WHERE key = ?", (bts, key)
            )


def log(text: str, type: str = "I", color: str | tuple = colorama.Fore.GREEN, program: str = "main.info", *print_args, **print_kwds):
    if isinstance(color, str):
        color = (color, color)
    _log = color[0] + colorama.Style.BRIGHT + f"{type} {str(datetime.datetime.now())[:23]} {color[1]}{program}{color[0]}: {text}"
    _log += colorama.Fore.RESET
    print(_log, *print_args, **print_kwds)


async def _async_read_premium_(gid: int):
    for x in range(20):
        try:
            async with aiosqlite.connect("../db/premium.db") as db:
                sql = await db.cursor()
                await sql.execute("""
                    CREATE TABLE IF NOT EXISTS blobvars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    value BLOB NOT NULL
                    )
                """)
                b = BlobVars(db, gid)
                server = await b.get({"level": 0, "configs": {}})
            return server
        except aiosqlite.DatabaseError:
            continue


async def _server_info_(gid, p):
    default = info.server_default_config
    default_server_dict = {"level": 0, "configs": default}
    server_dict = {"level": p["level"], "configs": p["configs"]}
    for key in default:
        if key not in server_dict["configs"]:
            server_dict["configs"][key] = default[key]
    expire = server_dict["configs"]['expire']
    if expire != -1 and expire < int(time.time()):
        server_dict = default_server_dict
    return server_dict


async def server_info(ctx: lightbulb.Context | None, guild_id: int | None = None) -> dict:
    gid = guild_id or ctx.guild_id
    p = await _async_read_premium_(gid)
    server_dict = await _server_info_(gid, p)
    return server_dict


async def vip_server(ctx: lightbulb.Context | None, guild_id: int | None = None) -> bool:
    result = await server_info(ctx, guild_id)
    if result["level"] > 0:
        return True
    else:
        return False


async def gen(
        sql: aiosqlite.Cursor, ctx: lightbulb.Context | hikari.MessageCreateEvent,
        limit: int = None, additional: str = "", random: bool = True,
        lenght: int = 5, distinct: bool = True, select: str = "content") -> aiosqlite.Cursor:
    if limit is None:
        limit = (await server_info(ctx))["configs"]["limit"]
    randm = "ORDER BY RANDOM()"
    if not random:
        randm = ""
    await sql.execute(
        "SELECT channel_id FROM channels WHERE server_id = ?",
        (ctx.guild_id, ))
    channels = await sql.fetchall()
    channel_ids = tuple(x[0] for x in channels)
    if channel_ids:
        channel_ids_sql = "AND (channel_id IN ({}) OR channel_id IS NULL)".format(
            ','.join(['?' for _ in channel_ids]))
    else:
        channel_ids_sql = ""
    query = f"""SELECT {'DISTINCT' if distinct else ''} {select}
                FROM messages
                WHERE server_id = ?
                AND length(content) >= {lenght}
                {channel_ids_sql}
                {additional}
                {randm}
                LIMIT   {limit}"""
    params = (ctx.guild_id,) + tuple(channel_ids) if channel_ids else (ctx.guild_id,)
    await sql.execute(query, params)
    return sql


def slash_command_group(func) -> lightbulb.CommandLike:
    func = lightbulb.implements(lightbulb.SlashCommandGroup)(func)
    return func


def transform_command(command: commands.Command):
    options_list = []
    cmd_name = command.name.split()[-1]
    command_info = [cmd_name, command.description, command.auto_defer, command.ephemeral, command.guilds, command.kwargs]
    for argument in command.arguments:
        modifier = lightbulb.OptionModifier.NONE
        if argument.type:
            modifier = lightbulb.OptionModifier.CONSUME_REST
        option = (
            argument.name,
            argument.description,
            modifier,
            argument.type,
            argument.required,
            argument.length[1],
            argument.length[0],
            argument.other,
            argument.range[1],
            argument.range[0]
        )
        options_list.append(option)
    return options_list, command_info


def cmd(commad: str):
    return commands.d[commad]


def empty_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def command(command: commands.Command | str, app: lightbulb.BotApp | lightbulb.Plugin):
    try:
        if isinstance(command, str):
            command = cmd(command)
    except KeyError:
        logger.critical(f"Команды \"{command}\" не существует!")
        return empty_decorator
    options_list, command_info = transform_command(command)

    def decorator(func):
        if command_info[4] is None:
            func = lightbulb.command(command_info[0], command_info[1], pass_options=True, auto_defer=command_info[2], ephemeral=command_info[3], **command_info[5])(func)
        else:
            func = lightbulb.command(command_info[0], command_info[1], pass_options=True, auto_defer=command_info[2], ephemeral=command_info[3], guilds=command_info[4], **command_info[5])(func)
        for option_args in options_list:
            option_name, option_description, option_modifier, option_type, option_required, option_max_length, option_min_length, option_other, option_max, option_min = option_args
            option = lightbulb.option(
                option_name,
                option_description,
                modifier=option_modifier,
                type=option_type,
                required=option_required,
                max_length=option_max_length,
                min_length=option_min_length,
                max_value=option_max,
                min_value=option_min,
                **option_other
            )
            func = option(func)
        func = lightbulb.app_command_permissions(dm_enabled=False)(func)
        func = app.command(func)
        return func
    return decorator


async def async_createdb(
        server_id: int,
        sql: aiosqlite.Cursor,
        db: aiosqlite.Connection) -> None:
    await sql.executescript("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            server_id INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS rep (
            member_id INTEGER PRIMARY KEY,
            rep_count INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS who_set_rep (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member INTEGER NOT NULL,
            member2 INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ignore_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL,
            server_id INTEGER NOT NULL,
            reason TEXT
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            server_id INTEGER,
            member_id INTEGER,
            message_id INTEGER,
            timestamp DATETIME,
            channel_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT,
            value TEXT,
            value_2 TEXT
        );

        CREATE TABLE IF NOT EXISTS blobvars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            value BLOB NOT NULL
        );

        CREATE TABLE IF NOT EXISTS rank(
            member_id INTEGER PRIMARY KEY,
            xp INTEGER NOT NULL DEFAULT 0,
            xp_cooldown INTEGER NOT NULL DEFAULT 0
        );
    """)
    await db.commit()


async def most_msgs_time(
        guild_id: hikari.Snowflake | int, db: aiosqlite.Connection, sql: aiosqlite.Cursor | None = None
        ) -> tuple[list, bool, int, list]:
    sql = sql or (await db.cursor())
    await async_createdb(guild_id, sql, db)
    results = await (await sql.execute(
        """
            SELECT member_id, timestamp
            FROM messages
            WHERE timestamp IS NOT NULL
        """
    )).fetchall()

    succes = False
    elements = []
    dates = []
    grouped_by_day = {}
    for member_id, timestamp in results:
        day = str(timestamp).split()[0]
        if day not in grouped_by_day:
            grouped_by_day[day] = []
        grouped_by_day[day].append((member_id, timestamp))

    sorted_days = sorted(grouped_by_day.items(), key=lambda x: len(x[1]), reverse=True)
    grouped_by_day_ordered = OrderedDict(sorted_days)

    if results:
        succes = True
        max_page = ceil(len(grouped_by_day) / 5)
        for x in grouped_by_day_ordered.keys():
            element = ""
            date_str: str = x
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            timezone = datetime.timezone.utc
            start_time = date.replace(hour=0, minute=0, second=0, tzinfo=timezone)
            end_time = date.replace(hour=23, minute=59, second=59, tzinfo=timezone)
            messages: list = grouped_by_day[x]
            message_count = len(messages)
            d = dict(Counter(elem[0] for elem in messages))
            member_top = sorted(d.items(), key=lambda item: item[1], reverse=True)
            if member_top:
                first_message = datetime.datetime.strptime(messages[0][1], '%Y-%m-%d %H:%M:%S').astimezone(timezone)
                last_message = datetime.datetime.strptime(messages[len(messages)-1][1], '%Y-%m-%d %H:%M:%S').astimezone(timezone)
                start_discord_timestamp = f'<t:{int(first_message.timestamp())}:f>'
                end_discord_timestamp = f'<t:{int(last_message.timestamp())}:f>'

                dates.append((str(date_str[0]).split()[0], message_count))
                element += f"{start_discord_timestamp} - {end_discord_timestamp}: {message_count} сообщений\n"
                element += f"**Самый активный участник:** <@{member_top[0][0]}> ({member_top[0][1]} сообщений)\n\n"
            else:
                start_discord_timestamp = f'<t:{int(start_time.timestamp())}:f>'
                end_discord_timestamp = f'<t:{int(end_time.timestamp())}:f>'

                element += f"{start_discord_timestamp} - {end_discord_timestamp}: {message_count} сообщений\n"
            elements.append(element)
    return (elements, succes, max_page, dates)


async def old_most_msgs_time(
        guild_id: hikari.Snowflake | int, db: aiosqlite.Connection, sql: aiosqlite.Cursor | None = None
        ) -> tuple[list, bool, int, list]:
    sql = sql or (await db.cursor())
    await async_createdb(guild_id, sql, db)
    await sql.execute("""
        SELECT strftime('%Y-%m-%d', timestamp) AS date, COUNT(*) AS message_count
        FROM messages
        WHERE timestamp IS NOT NULL
        GROUP BY date
        ORDER BY message_count DESC
    """)
    results = await sql.fetchall()
    succes = False
    dates = []
    elements = []
    max_page = 0
    utc = pytz.timezone('UTC')

    if results:
        succes = True
        max_page = ceil(len(results) / 5)
        for i, result in enumerate(results, start=1):
            element = ""
            date_str = result[0]
            message_count = result[1]
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            date_utc = utc.localize(date)

            start_time = date_utc.replace(hour=0, minute=0, second=0)
            end_time = date_utc.replace(hour=23, minute=59, second=59)

            await sql.execute("""
                SELECT member_id, COUNT(*) AS message_count
                FROM messages
                WHERE timestamp BETWEEN :start_time AND :end_time
                GROUP BY member_id
                ORDER BY message_count DESC
                LIMIT 1
            """, {'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'), 'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S')})
            most_active_member = await sql.fetchone()

            if most_active_member:
                member_id = most_active_member[0]
                msg_count2 = most_active_member[1]

                await sql.execute("""
                    SELECT MIN(timestamp) AS first_message, MAX(timestamp) AS last_message
                    FROM messages
                    WHERE timestamp BETWEEN :start_time AND :end_time
                """, {'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'), 'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S')})
                first_last_messages = await sql.fetchone()
                first_message = datetime.datetime.strptime(first_last_messages[0], '%Y-%m-%d %H:%M:%S')
                last_message = datetime.datetime.strptime(first_last_messages[1], '%Y-%m-%d %H:%M:%S')

                first_message_utc = pytz.utc.localize(first_message)
                last_message_utc = pytz.utc.localize(last_message)

                start_discord_timestamp = f'<t:{int(first_message_utc.timestamp())}:f>'
                end_discord_timestamp = f'<t:{int(last_message_utc.timestamp())}:f>'

                dates.append((str(first_last_messages[0]).split()[0], message_count))
                element += f"{start_discord_timestamp} - {end_discord_timestamp}: {message_count} сообщений\n"
                element += f"**Самый активный участник:** <@{member_id}> ({msg_count2} сообщений)\n\n"
            else:
                start_discord_timestamp = f'<t:{int(start_time.timestamp())}:f>'
                end_discord_timestamp = f'<t:{int(end_time.timestamp())}:f>'

                element += f"{start_discord_timestamp} - {end_discord_timestamp}: {message_count} сообщений\n"
            elements.append(element)
    return (elements, succes, max_page, dates)


class Reputation:
    def __init__(self) -> None:
        pass

    class Status:
        def __init__(self, succes: bool, *, text: str | None = None) -> None:
            self.succes = succes
            self.text = text

    async def get(self, db: aiosqlite.Connection, sql: aiosqlite.Cursor, member: hikari.User | hikari.Member | lightbulb.Context, *, commit: bool = True) -> int:
        if isinstance(member, lightbulb.Context):
            id = member.author.id
        else:
            id = member.id
        rep = await (await sql.execute("SELECT rep_count FROM rep WHERE member_id = ?", (id,))).fetchone()
        rep = rep if rep is None else rep[0]
        if rep is None:
            await sql.execute("INSERT INTO rep (member_id) VALUES (?)", (id,))
            if commit:
                await db.commit()
        return rep

    async def add(self, db: aiosqlite.Connection, sql: aiosqlite.Cursor, ctx: lightbulb.Context, member: hikari.User | hikari.Member, *, commit: bool = True) -> Status:
        await self.get(db, sql, member, commit=False)
        await sql.execute("SELECT member2 FROM who_set_rep WHERE member = ? AND member2 = ?", (ctx.author.id, member.id))
        result = await sql.fetchone()
        if result is not None:
            return self.Status(False, text="Вы уже выдавали ему репутацию")
        else:
            await sql.execute("INSERT INTO who_set_rep (member, member2) VALUES (?, ?)", (ctx.author.id, member.id))
            await sql.execute("UPDATE rep SET rep_count = rep_count + ? WHERE member_id = ?", (1, member.id))
            if commit:
                await db.commit()
            return self.Status(True)

    async def sub(self, db: aiosqlite.Connection, sql: aiosqlite.Cursor, ctx: lightbulb.Context, member: hikari.User | hikari.Member, *, commit: bool = True) -> Status:
        await self.get(db, sql, member, commit=False)
        await sql.execute("SELECT member2 FROM who_set_rep WHERE member = ? AND member2 = ?", (ctx.author.id, member.id))
        result = await sql.fetchone()
        if result is None:
            return self.Status(False, text="Вы не давали репутацию ему!")
        else:
            await sql.execute("DELETE FROM who_set_rep WHERE member = ? AND member2 = ?", (ctx.author.id, member.id))
            await sql.execute("UPDATE rep SET rep_count = rep_count - ? WHERE member_id = ?", (1, member.id))
            if commit:
                await db.commit()
            return self.Status(True)


def generate_random_nickname(length) -> tuple[str, str, str]:
    """
    Возращает в tuple (полностью)
    """
    pattern = r'^[0-9a-z.#]+$'
    length = max(length, 12)
    regex_pattern = re.compile(pattern)
    vowels = 'aeiou'
    consonants = 'bcdfghjklmnpqrstvwxyz'
    nickname = ''

    while not regex_pattern.match(nickname):
        nickname = ''
        vowel_count = 0
        consonant_count = 0
        last_vowel = ''

        while len(nickname) < length:
            rand = random.randint(1, 2)

            if rand == 1:
                if vowel_count >= 2:
                    continue
                else:
                    vowel = random.choice([v for v in vowels if v != last_vowel])
                    last_vowel = vowel
                    vowel_count += 1
                    consonant_count = 0
                    nickname += vowel
            elif rand == 2:
                if consonant_count >= 1:
                    continue
                else:
                    consonant_count += 1
                    vowel_count = 0
                    nickname += random.choice(consonants)

        for _ in range(int(length/20)):
            index = random.randint(2, length-6)
            symbol = "."
            nickname = nickname[:index] + symbol + nickname[index+1:]
        index = length-5
        nickname = nickname[:length-4]
        discriminant = ""
        for x in range(4):
            discriminant += random.choice("0123456789")
        full = f"{nickname}#{discriminant}"

    return full, nickname, discriminant


class Modals:
    class Example(miru.Modal):
        name = miru.TextInput(label="Name", placeholder="Type your name!", required=True)
        bio = miru.TextInput(label="Biography", value="Pre-filled content!", style=hikari.TextInputStyle.PARAGRAPH)

        # The callback function is called after the user hits 'Submit'
        async def callback(self, ctx: miru.ModalContext) -> None:
            # You can also access the values using ctx.values, Modal.values, or use ctx.get_value_by_id()
            await ctx.respond(f"Your name: `{self.name.value}`\nYour bio: ```{self.bio.value}```")


class Views:
    class Example(miru.View):

        @miru.text_select(
            placeholder="Select me!",
            options=[
                miru.SelectOption(label="Option 1"),
                miru.SelectOption(label="Option 2"),
            ]
        )
        async def basic_select(self, ctx: miru.ViewContext, select: miru.TextSelect) -> None:
            await ctx.respond(f"You've chosen {select.values[0]}!")

        @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
        async def basic_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            await ctx.respond("You clicked me!")

        @miru.button(label="Stop me!", style=hikari.ButtonStyle.DANGER)
        async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            self.stop()

    class Confirmation(miru.View):
        def __init__(self, *, timeout: float | int | datetime.timedelta | None = 120, autodefer: bool | miru.AutodeferOptions = True) -> None:
            super().__init__(timeout=timeout, autodefer=autodefer)
            self.confirmed = False

        @miru.button(label="", style=hikari.ButtonStyle.SUCCESS, emoji=emoji.Confirmation.confirm)
        async def confirm_button(self, ctx: miru.ViewContext, button: miru.Button):
            self.confirmed = True
            self.stop()

        @miru.button(label="", style=hikari.ButtonStyle.DANGER, emoji=emoji.Confirmation.cancel)
        async def cancel_button(self, ctx: miru.ViewContext, button: miru.Button):
            self.confirmed = False
            self.stop()

    class RankSetting(miru.View):
        def __init__(self, ctx: lightbulb.Context, ignored_roles: tuple = (), *, timeout: float | int | datetime.timedelta | None = 120, autodefer: bool = True) -> None:
            super().__init__(timeout=timeout, autodefer=autodefer)
            self.ctx = ctx
            self._ignored_roles = ignored_roles
            self.ignored_roles = []

        @miru.role_select(
            placeholder="Игнорируемые роли", min_values=0, max_values=25, custom_id="ignore_roles"
        )
        async def role_select(self, ctx: miru.ViewContext, select: miru.RoleSelect) -> None:
            self.ignored_roles = select.values
            print(select.values)

        @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
        async def basic_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            await ctx.respond("You clicked me!")

        @miru.button(label="Stop me!", style=hikari.ButtonStyle.DANGER)
        async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            self.stop()

        async def start(self, message: hikari.SnowflakeishOr[hikari.PartialMessage] | None = None) -> None:
            for x in self._ignored_roles:
                role = self.ctx.get_guild().get_role(x)
                self.ignored_roles.append(role)
            self.ignored_roles = tuple(self.ignored_roles)
            for x in self.children:
                if x.custom_id == "ignore_roles":
                    x: miru.RoleSelect = x
                    x.values = self.ignored_roles
            return await super().start(message)

    class WhoSayIt(miru.View):
        @miru.button(label="", style=hikari.ButtonStyle.SECONDARY, emoji=emoji.Numbers.num1, custom_id="1")
        async def num1(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            await self.check_correct(ctx.user.id, 0, ctx)

        @miru.button(label="", style=hikari.ButtonStyle.SECONDARY, emoji=emoji.Numbers.num2, custom_id="2")
        async def num2(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            await self.check_correct(ctx.user.id, 1, ctx)

        @miru.button(label="", style=hikari.ButtonStyle.SECONDARY, emoji=emoji.Numbers.num3, custom_id="3")
        async def num3(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            await self.check_correct(ctx.user.id, 2, ctx)

        @miru.button(label="", style=hikari.ButtonStyle.SECONDARY, emoji=emoji.Numbers.num4, custom_id="4")
        async def num4(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            await self.check_correct(ctx.user.id, 3, ctx)

        @miru.button(label="", style=hikari.ButtonStyle.SECONDARY, emoji=emoji.Numbers.num5, custom_id="5")
        async def num5(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            await self.check_correct(ctx.user.id, 4, ctx)

        def disable_buttons(self):
            children = list(self.children)
            children.reverse()
            for item in children:
                id = int(item.custom_id)
                if id > len(self.options):
                    self.remove_item(item)

        async def vstop(self):
            self.clear_items()
            self.stop()

        async def check_correct(self, user: int, option: int, ctx: miru.ViewContext):
            embed = hikari.Embed(
                title="Успешно!",
                description=f"Теперь ждите пока пройдет {self.timeout-10} секунд.",
                color=info.global_color
            )
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            if option == self.correct_option:
                self.winners.append(int(user))
            self.clicked.append(int(user))

        async def view_check(self, ctx: miru.ViewContext) -> bool:
            if ctx.user.id in self.clicked:
                embed = hikari.Embed(
                    title="Ошибка!",
                    description="Вы уже выбрали вариант!",
                    color=info.error_color
                )
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return False
            else:
                return True

        def __init__(self, options: list, correct_option: int, *, timeout: float | int | datetime.timedelta | None = 40, autodefer: bool = True) -> None:
            super().__init__(timeout=timeout, autodefer=autodefer)
            self.options = options
            self.correct_option = correct_option
            self.winners = []
            self.clicked = []
            self.disable_buttons()

    class ReadMsgContent(miru.View):
        def __init__(self, *, timeout: float | int | datetime.timedelta | None = 120, autodefer: bool = True) -> None:
            super().__init__(timeout=timeout, autodefer=autodefer)
            self.select: miru.TextSelect = None

        @miru.text_select(
            placeholder="Время",
            options=[
                miru.SelectOption(label="7 дней", value="7"),
                miru.SelectOption(label="30 дней", value="30"),
                miru.SelectOption(label="60 дней", value="60"),
                miru.SelectOption(label="120 дней", value="120"),
                miru.SelectOption(label="1 год", value="365"),
                miru.SelectOption(label="Не удалять", value="0"),
            ],
        )
        async def basic_select(self, ctx: miru.ViewContext, select: miru.TextSelect) -> None:
            self.select = select

        @miru.button(label="Выбрать", style=hikari.ButtonStyle.SUCCESS)
        async def basic_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            select = self.select
            eph = hikari.MessageFlag.EPHEMERAL
            if select is None:
                embed = hikari.Embed(
                    title="Ошибка!",
                    description="Вы не выбрали время!",
                    color=info.error_color
                )

                await ctx.respond(embed, flags=eph)
            else:
                self.stop()

    class Pages(miru.View):
        def __init__(self, elements: list, ctx: lightbulb.Context, embed: hikari.Embed, elements_per_page: int = 5,
                     start_page: int = 1, user_id: int | hikari.Snowflake | None = None, bottom: str = "",
                     timeout: float | int | datetime.timedelta | None = None, autodefer: bool = True, exit_button: bool = True,
                     show_page_number: bool = True):
            super().__init__(timeout=timeout, autodefer=autodefer)
            self._elements: list = elements
            if start_page is None:
                start_page = 1
            self._start_page: int = start_page
            self._ctx = ctx
            self._elements_per_page = elements_per_page
            self._embed = embed
            self._embed_description = embed.description
            self._msg: lightbulb.ResponseProxy = None
            self._max_pages: int = ceil(len(elements)/elements_per_page)
            self._current_page: int = min(start_page, self._max_pages)
            self._user_id: int | hikari.Snowflake | None = user_id
            self.error_embed = hikari.Embed(
                title="Ошибка",
                description="",
                color=info.error_color
            )
            self.exit_button = exit_button
            self._bottom = bottom
            self._show_page_number = show_page_number

        def set_page(self, page: int) -> bool:
            if page < 1:
                page = 1
            if page > self._max_pages:
                page = self._max_pages
            self._current_page = page

        @miru.button(label="", style=hikari.ButtonStyle.SECONDARY, custom_id="first", emoji=emoji.Pages.first)
        async def firstpage(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            self.set_page(1)
            await self.generate_list()

        @miru.button(label="", style=hikari.ButtonStyle.SECONDARY, custom_id="previous", emoji=emoji.Pages.previous)
        async def previouspage(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            self.set_page(self._current_page-1)
            await self.generate_list()

        @miru.button(label="", style=hikari.ButtonStyle.SECONDARY, custom_id="next", emoji=emoji.Pages.next)
        async def nextpage(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            self.set_page(self._current_page+1)
            await self.generate_list()

        @miru.button(label="", style=hikari.ButtonStyle.SECONDARY, custom_id="last", emoji=emoji.Pages.last)
        async def lastpage(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            self.set_page(self._max_pages)
            await self.generate_list()

        @miru.button(label="", style=hikari.ButtonStyle.DANGER, custom_id="delete", emoji=emoji.Pages.delete)
        async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            self.stop()
            if self._msg is not None:
                try:
                    await self._msg.delete()
                except Exception:
                    ...

        async def generate_list(self) -> lightbulb.ResponseProxy | hikari.Message:
            page = self._current_page
            epp = self._elements_per_page
            elements = self._elements
            embed = self._embed
            max_page = self._max_pages
            output = f"{self._embed_description}\nСтраница: {page}/{max_page}\n\n"
            if len(elements) != 0:
                for i, result in enumerate(elements, start=1):
                    if i < page*epp+1 and i > page*epp-epp:
                        if self._show_page_number:
                            output += f"**{i}**. {result}\n"
                        else:
                            output += f"{result}\n"
            else:
                output += "Пусто"
            output += self._bottom
            embed.description = output
            await self.disable_buttons()
            if self._msg is None:
                self._msg = await self._ctx.respond(embed, components=self)
            else:
                try:
                    self._msg = await self._msg.edit(embed, components=self)
                except Exception:
                    self._msg = await self._ctx.respond(embed, components=self)
            return self._msg

        async def view_check(self, ctx: miru.ViewContext) -> bool:
            if not ctx.user.id == self._user_id:
                error_embed1 = self.error_embed
                error_embed1.description = "Данное взаимодействие доступно только участнику, запросившему эту команду."
                await ctx.respond(error_embed1, flags=hikari.MessageFlag.EPHEMERAL)
            return ctx.user.id == self._user_id

        async def on_timeout(self) -> None:
            self.clear_items()
            msg = self._msg
            try:
                if isinstance(msg, lightbulb.ResponseProxy):
                    msg = await self._msg.message()
                await msg.edit(msg.content, components=self)
            except hikari.NotFoundError:
                ...

        # async def compact(self):
        #     for item in self.children:
        #         id = item.custom_id
        #         if id == "first" or id == "previous":
        #             item.row = 1
        #         elif id == "next" or id == "last":
        #             item.row = 2
        #         elif id == "delete":
        #             item.row = 3
        #             item.width = 2

        async def disable_buttons(self):
            for item in self.children:
                id = item.custom_id
                if id == "first" or id == "previous":
                    if self._current_page-1 < 1:
                        item.disabled = True
                    else:
                        item.disabled = False
                elif id == "next" or id == "last":
                    if self._current_page+1 > self._max_pages:
                        item.disabled = True
                    else:
                        item.disabled = False
                elif id == "delete":
                    if not self.exit_button:
                        self.remove_item(item)


class InfoSystem:
    def __init__(self, webhook: str, db: aiosqlite.Connection | None = None) -> None:
        self.webhook = webhook
        self.db = db

    async def send_bug(self, guild_id: int, user_id: int, user_name: str, description: str, short_desc: str, steps: str | None = ""):
        try:
            data = {
                "content": f"<@{info.developer_id}>",
                "username": 'BUG',
                "avatar_url": "https://media.discordapp.net/attachments/1167862813423845456/1167862858583920790/IDEALIGHT_in_programm.png"
            }
            bug_info = ""
            bug_info += f"**Сервер:** {guild_id}\n"
            bug_info += f"**Айди участника:** {user_id}\n"
            bug_info += f"**Имя участника:** `{user_name}`\n"
            description = f"\nВремя: <t:{int(time.time())}:R>\n{description}"
            bug_info += f"**Описание:** {description}\n"
            bug_info += f"**Короткое описание:** {short_desc}\n"
            bug_info += f"**Шаги:** {steps}\n"
            data["embeds"] = [
                {
                    "description": bug_info,
                    "title": "Новый баг",
                    "color": info.global_color
                }
            ]
            if not info.beta:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.webhook, json=data) as response:
                        response: aiohttp.ClientResponse = response
        except Exception as e:
            tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            print(tb_str)

        async def add_bug(db: aiosqlite.Connection):
            sql = await db.cursor()
            await sql.execute(
                """INSERT INTO bugs (guild_id, user_id, user_name, description, short_desc, steps)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (guild_id, user_id, user_name,
                 f"{description}", short_desc, steps)
            )
            await db.commit()
        if self.db is None:
            async with aiosqlite.connect('../db/database.sqlite') as db:
                await add_bug(db)
        else:
            await add_bug(self.db)
        if not info.beta:
            return response.status
        else:
            return 000


async def zip_backup(src_dir: str = "../db/", dst_zip: str = None, backup_folder: str = '../backups/'):
    if not src_dir:
        print("Please give at least the Source Directory")
        raise ValueError

    if dst_zip is None or not dst_zip:
        dst_zip = src_dir
    elif dst_zip.isspace():
        dst_zip = src_dir

    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    dst_zip = os.path.join(backup_folder, dst_zip)

    with zipfile.ZipFile(dst_zip + '.zip', 'w') as myzip:
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), src_dir)
                myzip.write(os.path.join(root, file), arcname=rel_path)


class LevelCalculation:
    def __init__(self, formula_multiplier: int = 1) -> None:
        self.start_xp = 0
        self.start_1st = 100
        self.start_level = 0
        self.max_level = 999
        self.formula_multiplier = formula_multiplier
        self.max_xp = None

    async def formula(self, level: int) -> int:
        if level == self.start_level:
            return self.start_xp
        level -= 1
        return (5 * level ** 2 + 50 * level + self.start_1st) * self.formula_multiplier

    async def xp_from_previous(self, level: int) -> int:
        if level == self.start_level:
            return self.start_xp
        return (await self.formula(level))

    async def xp_all(self, level: int) -> int:
        return sum([(await self.formula(level2)) for level2 in range(self.start_level, level + 1)])

    async def xp_to_next(self, level: int) -> int:
        if level == self.max_level:
            return 0
        return (await self.formula(level+1))

    async def get_properties(self, level: int):
        return level, (await self.xp_all(level)), (await self.xp_from_previous(level)), (await self.xp_to_next(level))


async def get_level_xp(xp: int) -> int:
    lvlcalc = LevelCalculation()
    level = lvlcalc.start_level
    xp_all = await lvlcalc.xp_all(level)
    while xp_all <= xp:
        level += 1
        xp_all += await lvlcalc.xp_from_previous(level)
    return level - 1


async def get_xp(id: int, db: aiosqlite.Connection) -> int:
    sql = await db.cursor()
    await sql.execute(
        """SELECT xp FROM rank WHERE member_id = ?""",
        (id,)
    )
    result = await sql.fetchone()
    if result is None:
        await sql.execute(
            """INSERT INTO rank (member_id) VALUES (?)""",
            (id,)
        )
        await db.commit()
        await sql.execute(
            """SELECT xp FROM rank WHERE member_id = ?""",
            (id,)
        )
        result = await sql.fetchone()
    return result[0]


async def generate_card(
        member: hikari.Member, level: int, total_xp: int, xp_to_next: int,
        level_xp: int, rank: int, rep: int | None = None, *,
        card: str = "default", text_color: tuple = (255, 255, 255),
        progress_bar_color: tuple = (50, 240, 50), resolution_multiplier: int = 1.3) -> hikari.Bytes:
    rm = resolution_multiplier
    fonts = info.Fonts()

    async def circle_crop(img):
        npImage = np.array(img)
        h, w = img.size

        alpha = Image.new('L', img.size, 0)
        draw = ImageDraw.Draw(alpha)
        draw.pieslice([0, 0, h, w], 0, 360, fill=255)

        npAlpha = np.array(alpha)

        npImage = np.dstack((npImage, npAlpha))

        img = Image.fromarray(npImage, 'RGBA')

        return img
    image = Image.new('RGBA', (int(900 * rm), int(200 * rm)))
    draw = ImageDraw.Draw(image)

    level = level
    total_exp = total_xp
    experience = total_xp - level_xp
    next_level_experience = xp_to_next
    nickname = member.global_name or member.username or "User"

    card_template = Image.open('./resources/card.png').convert("RGBA").resize((int(900 * rm), int(200 * rm)))
    image.paste(card_template, (0, 0), card_template)

    progress_width = int(675 * rm)
    progress_height = int(30 * rm)
    progress_x = int(200 * rm)
    progress_y = int(135 * rm)
    progress = min((experience / next_level_experience) * progress_width, progress_width)

    draw.rounded_rectangle(
        [(progress_x - int(5 * rm), progress_y - int(5 * rm)),
         (progress_x + progress_width + int(5 * rm), progress_y + progress_height + int(5 * rm))],
        fill=(200, 200, 200), radius=int(25 * rm))
    draw.rounded_rectangle(
        [(progress_x, progress_y),
         (progress_x + progress, progress_y + progress_height)],
        fill=progress_bar_color, radius=int(25 * rm))

    avatar_url = str(member.avatar_url or member.display_avatar_url)
    avatar = Image.open('./resources/User.png').convert("RGB") if avatar_url is None else None

    try:
        if avatar_url is not None:
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    image_data = await resp.read()

            avatar = Image.open(io.BytesIO(image_data)).convert("RGB")

        avatar = await circle_crop(avatar)
        avatar = avatar.resize((int(150 * rm), int(150 * rm)))
        draw.ellipse(((int(20 * rm), int(20 * rm)), (int(180 * rm), int(180 * rm))), fill=(200, 200, 200))
        image.paste(avatar, (int(25 * rm), int(25 * rm)), avatar)
    except ValueError:
        pass

    text = f'{nickname}'
    font_big = fonts.bigfont
    font_big.size = int(font_big.size * rm)
    draw.text((int(200 * rm), int(30 * rm)), text, font=font_big, fill=text_color)

    font_mini = fonts.minifont
    font_big_bold = fonts.verybigfont_bold
    font_mini.size = int(font_mini.size * rm)
    font_big_bold.size = int(font_big_bold.size * rm)
    x = int(200 * rm)
    y = int((100 + (24 * rm)) * rm) - font_mini.size
    text = 'ур '
    draw.text((x, y), text, font=font_mini, fill=text_color)
    x += draw.textlength(text, font_mini)
    text = f'{level}'
    draw.text((x, y - font_big_bold.size + font_mini.size), text, font=font_big_bold, fill=text_color)
    x += draw.textlength(text, font_big_bold)
    text = ' ранг '
    draw.text((x, y), text, font=font_mini, fill=text_color)
    x += draw.textlength(text, font_mini)
    text = f'#{rank}'
    draw.text((x, y - font_big_bold.size + font_mini.size), text, font=font_big_bold, fill=text_color)
    x += draw.textlength(text, font_big_bold)

    font_bold = fonts.font_bold
    font = fonts.font
    font_bold.size = int(font_bold.size * rm)
    font.size = int(font.size * rm)
    x = progress_x + progress_width
    y = int(100 * rm) - font_bold.size
    y2 = int((100 + (24 * rm)) * rm) - font_bold.size
    x2 = progress_x + progress_width

    if rep is not None:
        y3 = y2 - (font.size * 2)
        x3 = x2

        rep_icon = Image.open('./resources/Rep.png').convert("RGBA")
        rep_icon = rep_icon.resize((font.size, font.size))
        image.paste(rep_icon, (x3 - font.size, y3), rep_icon)
        x3 -= font.size * 2
        text = str(rep)
        draw.text((x3, y3), text, font=font, fill=text_color)

    text = f"{total_exp} EXP"
    x2 -= draw.textlength(text, font)
    draw.text((x2, y), text, font=font, fill=text_color)

    text1 = f'{experience} '
    x -= draw.textlength(text1, font_bold)
    text2 = f'/ {next_level_experience}'
    x -= draw.textlength(text2, font)

    draw.text((x, y2), text1, font=font_bold, fill=text_color)
    x += draw.textlength(text1, font_bold)
    draw.text((x, y2), text2, font=font, fill=text_color)
    x += draw.textlength(text2, font)

    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')

    image = None
    draw = None
    return hikari.Bytes(img_bytes.getvalue(), "image.png")


def generate_progress_bar(progress: float, length: int, theme: emoji.ProgressBarTheme):
    if not (0 <= progress <= 1):
        raise ValueError("Progress must be between 0 and 1.")

    filled_length = int(length * progress)
    empty_length = length - filled_length

    segments = [theme.filled_center] * filled_length + [theme.empty_center] * empty_length

    segments[0] = theme.filled_left if segments[0] == theme.filled_center else theme.empty_left
    segments[-1] = theme.filled_right if segments[-1] == theme.filled_center else theme.empty_right
    progress_bar = ''.join(segments)

    return progress_bar


if __name__ == "__main__":
    async def premium():
        code = input("Code: ")
        if "server:" in code:
            code = code.replace("server:", "")
        if not code.startswith('g'):
            decrypted = Crypt.decrypt(premium_code_key, code).split(".")
        else:
            code = code.replace("g", "")
            decrypted = [code, 0, 0, "None"]
        print(f"Owner id: {decrypted[1]}")
        print(f"Key author: {decrypted[2]}")
        print(f"Key author username: {decrypted[3]}")
        print(f"Server: {decrypted[0]}")
        gid = int(decrypted[0])
        print((await server_info(None, gid)))
        limit = int(input("Limit:"))
        level = int(input("level:"))
        expire = int(input("expire:"))
        dexpire = -1 if expire == -1 else int(time.time())+expire
        async with aiosqlite.connect("../db/premium.db") as db:
            await BlobVars(db, gid).set({"level": level, "configs": {"limit": limit, "expire": dexpire}})
            await db.commit()
        print((await server_info(None, gid)))
    asyncio.run(premium())
