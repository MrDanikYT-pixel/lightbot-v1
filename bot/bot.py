import info
from time import time
import asyncio
import itertools
import os
import aiosqlite as sqlite3
import hikari
import lightbulb
import aiohttp
import dotenv
import aiofiles
import random
import re
import colorama
import traceback

import commands as cmds
from functions import gen
import functions
from generator import async_combine_common_words
import generator
from functions import async_createdb
from info import error_color, global_color
from datetime import datetime, timedelta
import glob
import time as otime
import logging
import json
import miru

# import nltk
# nltk.download("punkt")
dotenv.load_dotenv()
sdc_last_send = {"servers": 0, "succes": False}

beta = info.beta

token = ""
if beta:
    token = os.environ["BETA_BOT_TOKEN"]
else:
    token = os.environ["BOT_TOKEN"]

intents = hikari.Intents.ALL
intents &= ~hikari.Intents.GUILD_PRESENCES


bot = lightbulb.BotApp(
    token,
    intents=intents,
    prefix=info.prefix(),
    banner=None,
    owner_ids=info.developer_id,
    help_class=None,
    ignore_bots=True
)
bot.d.miru = miru.Client(bot, ignore_unknown_interactions=True)

SDC_TOKEN = os.environ["SDC_TOKEN"]
url_regex = info.regex["url"]
token_regex = info.regex["token"]

guild_count = 0


__filename__ = os.path.basename(__file__)
filename = os.path.splitext(__filename__)[0]
main_logger = logging.getLogger(f"{filename}")


@bot.listen(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:
    have_bug_report = False

    async def addbug(desc, short):
        ctx = event.context
        await functions.InfoSystem(os.environ["IDEAS_WEBHOOK"]).send_bug(ctx.guild_id, ctx.user.id, ctx.user.username, desc, short)
    try:
        try:
            originalexc = event.exception.original
        except AttributeError:
            originalexc = "No info"
        if isinstance(event.exception, lightbulb.CommandInvocationError) and not isinstance(event.exception.original, sqlite3.OperationalError):
            if not isinstance(event.exception, aiohttp.ClientConnectionError) and not isinstance(event.exception, hikari.UnauthorizedError):
                if not isinstance(event.exception, hikari.NotFoundError):
                    cn = event.context.command.name
                    try:
                        await event.context.respond(
                            hikari.Embed(
                                title="Ошибка",
                                description=(f"Что-то пошло не так во время вызова команды `{cn}`." +
                                             "\n\nНапишите `report_bug` для того чтобы я узнал об этой ошибке"),
                                color=error_color
                            ))
                        e = event.exception
                        tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                        await addbug(str(originalexc)+"\n"+str("```py\n" + tb_str + "\n```"), str(event.exception))
                        have_bug_report = True
                        raise event.exception
                    except hikari.NotFoundError:
                        pass

        exception = event.exception.__cause__ or event.exception

        if isinstance(exception, lightbulb.NotOwner):
            await event.context.respond(hikari.Embed(
                title="Ошибка",
                description="Вы не являетесь владельцем этого бота.",
                color=error_color
            ))
        elif isinstance(exception, lightbulb.CommandIsOnCooldown):
            cl = f"{exception.retry_after:.2f} секунд"
            await event.context.respond(hikari.Embed(
                title="Ошибка",
                description=(
                    "Эта команда не может быть выполнена в данный момент.\n" +
                    f"Пожалуйста, повторите попытку через `{cl}` времени."
                ),
                color=error_color
            ))
        elif isinstance(exception, lightbulb.MissingRequiredPermission):
            ep = exception.missing_perms
            ep = str(ep).replace("ADMINISTRATOR", "администратора")
            await event.context.respond(hikari.Embed(
                title="Ошибка",
                description=f"У вас нет прав {ep}.",
                color=error_color
            ))
        elif isinstance(exception, lightbulb.NotEnoughArguments):
            await event.context.respond(hikari.Embed(
                title="Ошибка",
                description="Вы пропустили один из аргументов.",
                color=error_color
            ))
        elif isinstance(exception, hikari.ForbiddenError):
            await event.context.respond(hikari.Embed(
                title="Ошибка",
                description=f"{exception}",
                color=error_color
            ))
        elif isinstance(exception, sqlite3.OperationalError):
            if int(exception.sqlite_errorcode) != 6:
                await event.context.respond(
                    hikari.Embed(
                        title="Ошибка",
                        description=(f"Что-то пошло не так во время вызова команды `{cn}`." +
                                     "\n\nНапишите `report_bug` для того чтобы я узнал об этой ошибке"),
                        color=error_color
                    ))
                e = event.exception
                tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            else:
                await event.context.respond(hikari.Embed(
                    title="Ошибка",
                    description="Не удалось выполнить команду, попробуйте ещё раз.\n`Если это не в первый раз напишите /report_bug.`",
                    color=error_color
                ))
        elif isinstance(exception, aiohttp.ClientConnectionError):
            pass
        elif isinstance(exception, lightbulb.errors.CommandNotFound):
            pass
        elif isinstance(exception, hikari.NotFoundError):
            pass
        elif not have_bug_report:
            e = event.exception
            tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            if 'Invalid Webhook Token' not in tb_str:
                await addbug(str(originalexc)+"\n"+str("```py\n" + tb_str + "\n```"), str(event.exception))
            raise exception
    except hikari.UnauthorizedError as e:
        if not have_bug_report:
            tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            if 'Invalid Webhook Token' not in tb_str:
                await addbug(str(originalexc)+"\n"+str("```py\n" + tb_str + "\n```"), str(event.exception))
        raise e


def generate_help_text(commands):
    help_text = ""
    for category, command_list in commands.items():
        help_text += f"\n\n**{category}:**\n"
        temp = []
        comment = ""
        group_commands = []
        for command in command_list:
            command: str = str(command)
            try:
                next_command = str(command_list[list(command_list).index(command)+1]).split()[0]
            except IndexError:
                next_command = ""
            if command.startswith("\\") and command.endswith("\\"):
                comment = command.replace("\\", "") + "\n"
            else:
                words = command.split()
                if len(words) >= 2:
                    if group_commands and words[0] != group_commands[0].split()[0]:
                        if len(group_commands) > 2:
                            temp.append(f"`{group_commands[0].split()[0]}: <{', '.join(group_commands[1:])}>`")
                        else:
                            temp.append(f"`{group_commands[0]}`")
                        group_commands = []
                    if next_command == words[0] or len(group_commands) >= 2:
                        if len(group_commands) == 0:
                            group_commands.append(words[0])
                        group_commands.append(' '.join(words[1:]))
                    else:
                        group_commands.append(command)
                else:
                    if group_commands:
                        if len(group_commands) > 2:
                            temp.append(f"`{group_commands[0].split()[0]}: <{', '.join(group_commands[1:])}>`")
                        else:
                            temp.append(f"`{group_commands[0]}`")
                        group_commands = []
                    temp.append(f"`{command}`")
        if group_commands:
            if len(group_commands) > 2:
                temp.append(f"`{group_commands[0].split()[0]}: <{', '.join(group_commands[1:])}>`")
            else:
                temp.append(f"`{group_commands[0]}`")
        help_text += comment + ', '.join(temp)

    return help_text


@functions.command("help", bot)
@lightbulb.implements(lightbulb.SlashCommand)
async def help(ctx: lightbulb.Context, command: str) -> None:
    commands = cmds.to_cmds()
    commands_help = "Только `/` команды"
    commands_help += generate_help_text(commands)
    commands_help += '\n\n"`/help` `<название команды>`" - дополнительная информация о команде'
    commands_help += '\n\n`Команда: <а, б, в>` - это варианты команд, которые можно использовать, например: `/команда а` или `/команда в`.'
    commands_help += '\n\n*У разработчика можно просить сделать уникальные команды для вашего сервера по типу экономики или что вы попросите за 1 и 2 уровень премиума*'
    embed = hikari.Embed(
        title="Помощь",
        description=commands_help,
        color=info.help_info_color
    )
    command_list = list(itertools.chain.from_iterable(commands.values()))
    if command:
        if command in command_list:
            embed = functions.commands.generate_help(command, color=info.help_info_color)
    embed.set_footer(f"Количество команд: {len(command_list)}")
    await ctx.respond(embed)


@bot.listen(lightbulb.SlashCommandCompletionEvent)
async def on_command(event: lightbulb.SlashCommandCompletionEvent):
    command = f"{event.command.name}"
    async with aiofiles.open('../statistics.json', mode='r') as f:
        contents = await f.read()
        stat = json.loads(contents)
        if command not in stat:
            stat[command] = 1
        else:
            stat[command] += 1
    async with aiofiles.open('../statistics.json', mode='w') as f:
        await f.write(json.dumps(stat, indent=4))


# @bot.listen(lightbulb.events.CommandInvocationEvent)
# async def on_command2(event: lightbulb.events.CommandInvocationEvent):
#     print("invocation")


# @bot.listen(hikari.StartingEvent)
# async def on_starting(event: hikari.StartingEvent):
#     logger = logging.getLogger(f"{filename}.on_starting")
#     logger.info(f"{colorama.Fore.LIGHTYELLOW_EX}Создание бэкапа папки db")
#     await functions.zip_backup("../db/", f"db-{int(time())}")
#     logger.info(f"{colorama.Fore.LIGHTYELLOW_EX}Бэкап наверное успешно создан")


@bot.listen(hikari.StartedEvent)
async def on_start(event: hikari.StartedEvent):
    asyncio.create_task(when_started(event))


async def when_started(event: hikari.StartedEvent):
    logger = logging.getLogger(f"{filename}.on_start")
    await asyncio.sleep(1)
    # bot.unload_extensions(*bot.extensions)
    guild_count = len(bot.cache.get_available_guilds_view())
    logger.info(f"Бот запущен! Количество серверов: {colorama.Fore.LIGHTGREEN_EX}{guild_count}")
    if not beta:
        asyncio.create_task(sdc_timer())
        logger.info("SDC Bots api таймер запущен")
    asyncio.create_task(db_timer())


async def db_timer():
    logger = logging.getLogger(f"{filename}.db_timer")
    await asyncio.sleep(5)
    while True:
        tim = otime.perf_counter()
        db_files = glob.glob('../db/*.sqlite')
        undefined_db = 0
        db_servers = [info.regex["num"].findall(s) for s in db_files]
        db_servers = [str(i) for r in db_servers for i in r if r]
        avaiable_guilds = bot.cache.get_available_guilds_view()
        bot_servers = []
        for x in avaiable_guilds:
            bot_servers.append(str(int(x)))
        db_with_not_guild = 0
        time_for_db = []

        for db_file in db_files:
            tim3 = otime.perf_counter()
            current_guild = re.sub(r'\D+', '', db_file)
            if current_guild not in db_servers:
                undefined_db += 1
                continue
            async with sqlite3.connect(db_file) as db:
                sql = await db.cursor()

                setting = functions.Setting(db, "delete_after")
                delete_after = (await setting.get("0"))[0]
                if current_guild not in bot_servers:
                    if delete_after != '30' or delete_after != '7':
                        await setting.set(value='30')
                    db_with_not_guild += 1
                if delete_after != "0":
                    thirty_days_ago = datetime.now() - timedelta(days=int(delete_after))

                    thirty_days_ago_str = thirty_days_ago.strftime('%Y-%m-%d %H:%M:%S')
                    await sql.execute(f"""
                        UPDATE messages
                        SET content = ''
                        WHERE timestamp < '{thirty_days_ago_str}' OR timestamp IS NULL
                    """)

                    await db.commit()
            time_for_db.append(otime.perf_counter()-tim3)
        tim2 = otime.perf_counter()-tim
        if tim2 >= 1:
            inf = f"{round(tim2, 3)} сек"
        else:
            inf = f"{round(tim2*1000, 1)} мс"
        min_value = round(min(time_for_db)*1000, 5)
        max_value = round(max(time_for_db)*1000, 5)
        average_value = round((sum(time_for_db) / len(time_for_db))*1000, 5)
        dbinfo = f"обработанно {len(db_files)-undefined_db} (без сервера: {db_with_not_guild}) | время на каждое бд min/max/avg: {min_value}/{max_value}/{average_value} мс"
        logger.info(f"{colorama.Fore.LIGHTCYAN_EX}Очистка баз данных прошла успешно! Время: {inf}")
        logger.info(f"{colorama.Fore.LIGHTCYAN_EX}{dbinfo}")
        await asyncio.sleep(21600)


async def sdc_timer():
    global sdc_last_send
    logger = logging.getLogger(f"{filename}.sdc_timer")
    id = int(bot.get_me().id)
    url = f'https://api.server-discord.com/v2/bots/{id}/stats'
    while True:
        guild_count = len(bot.cache.get_available_guilds_view())
        headers = {
            'Authorization': f"{SDC_TOKEN}"
        }

        data = {
            'servers': max(guild_count, 1),
            'shards': max(int(bot.shard_count), 1),
        }
        if sdc_last_send["servers"] != guild_count or not sdc_last_send["succes"]:
            sdc_last_send["servers"] = guild_count
            async with aiohttp.ClientSession() as session:
                async with session.post(url=url, headers=headers, data=data) as response:
                    r: aiohttp.ClientResponse = response
                    text = (await r.text())
                    xjson = None
                    try:
                        xjson = json.loads(text)
                    except json.JSONDecodeError:
                        ...
            error = False
            error_msg = "Нет информации"
            error_code = "400"
            if xjson is not None:
                if "status" not in xjson:
                    if "error" in xjson:
                        tmp = xjson["error"]
                        if "message" in tmp:
                            error_msg = tmp["message"]
                        if "code" in tmp:
                            error_code = str(tmp["code"])
                        tmp = None
                        error = True
            sdc_last_send["succes"] = False
            if r.status == 200 and not error:
                logger.info(
                    f"{colorama.Fore.LIGHTBLUE_EX} Статистика успешно отправлена на SDC (Серверов: {guild_count})")
                sdc_last_send["succes"] = True
            elif error:
                logger.error(
                    f"Ошибка отправки статистики на SDC (Код: {error_code})\nСообщение: {error_msg}")
            elif r.status == 429:
                logger.error(
                    f"Ошибка отправки статистики на SDC (Код: {r.status})\nОжидание 30 минут")
                await asyncio.sleep(1500)
            else:
                logger.error(
                    f"Ошибка отправки статистики на SDC (Код: {r.status})")
        await asyncio.sleep(300)


@bot.listen(hikari.GuildJoinEvent)
async def on_guild_join(event: hikari.GuildJoinEvent):
    guild_count = len(bot.cache.get_available_guilds_view())
    logger = logging.getLogger(f"{filename}.on_guild_join")
    logger.info(
        f"{colorama.Fore.LIGHTBLUE_EX} Бота добавили на сервер. ID:{event.guild.id} (Серверов: {guild_count})")


@bot.listen(hikari.GuildLeaveEvent)
async def on_guild_remove(event: hikari.GuildLeaveEvent) -> None:
    guild_count = len(bot.cache.get_available_guilds_view())
    logger = logging.getLogger(f"{filename}.on_guild_remove")
    logger.info(
        f"{colorama.Fore.LIGHTBLUE_EX} Бота удалили из сервера. ID:{event.guild_id} (Серверов: {guild_count})")


@bot.listen(hikari.GuildChannelDeleteEvent)
async def on_channel_delete(event: hikari.GuildChannelDeleteEvent):
    channel = event.channel_id
    async with sqlite3.connect(f'../db/{event.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(event.guild_id, sql, db)
        result = await (await sql.execute("SELECT * FROM messages WHERE server_id = ? AND  channel_id = ?", (event.guild_id, channel))).fetchone()
        if result is not None:
            await sql.execute("DELETE FROM messages WHERE server_id = ? AND channel_id = ?", (event.guild_id, channel))
            await db.commit()


@bot.listen(hikari.GuildMessageDeleteEvent)
async def on_message_delete(event: hikari.GuildMessageDeleteEvent):
    message = event.old_message
    if message is not None:
        async with sqlite3.connect(f'../db/{event.guild_id}database.sqlite') as db:
            sql = await db.cursor()
            await async_createdb(event.guild_id, sql, db)
            result = await (await sql.execute("SELECT * FROM messages WHERE server_id = ? AND  message_id = ?", (event.guild_id, message.id))).fetchone()

            if result is not None:
                await sql.execute("DELETE FROM messages WHERE server_id = ? AND message_id = ?", (event.guild_id, message.id))
                await db.commit()


@bot.listen(hikari.GuildMessageUpdateEvent)
async def on_message_update(event: hikari.GuildMessageUpdateEvent):
    message = event.message
    async with sqlite3.connect(f'../db/{message.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(message.guild_id, sql, db)
        r_mode = (await functions.Setting(db, "read_content").get('False'))[0]
        if r_mode != 'False':
            if event.content is not None and not isinstance(event.content, hikari.UndefinedType):
                if token_regex.search(event.content):
                    content = ""
                contentt = event.content.lower()
                content = contentt.replace("\"", "")
                content = content.replace("'", "")
                content = content.replace("*", "")
                content = content.replace("~~", "")
                content = content.replace("||", "")
                content = content.replace("__", "")
                content = url_regex.sub("<...>", content)
                if not len(content) > 0:
                    content = ""
                english_chars = re.findall(r'[a-zA-Z]', content)
                percent_english = len(english_chars) / len(content) * 100
                if not percent_english <= 20:
                    content = ""
            else:
                content = ""
            result = await (await sql.execute("SELECT * FROM messages WHERE server_id = ? AND  message_id = ?", (message.guild_id, message.id))).fetchone()
            if result is not None:
                await sql.execute(
                    "UPDATE messages SET content = ? WHERE server_id = ? AND message_id = ?", (str(message.content), message.guild_id, message.id)
                )
                await db.commit()


@bot.listen(hikari.GuildMessageCreateEvent)
async def on_message_create(event: hikari.GuildMessageCreateEvent):
    ignore_content = False
    if isinstance(event, hikari.DMMessageCreateEvent):
        return
    if event.author.is_bot:
        return

    async def embed_error():
        try:
            await event.message.respond("Ошибка прав: дайте мне право \"Встраивать ссылки\"")
        except hikari.ForbiddenError:
            pass

    async with sqlite3.connect(f'../db/{event.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(event.guild_id, sql, db)
        r_mode = (await functions.Setting(db, "read_content").get('False'))[0]
        message_id = event.message.id
        if event.content is not None:
            if token_regex.search(event.content):
                ignore_content = True
            contentt = event.content.lower()
            content = contentt.replace("\"", "")
            content = content.replace("'", "")
            content = content.replace("*", "")
            content = content.replace("~~", "")
            content = content.replace("||", "")
            content = content.replace("__", "")
            content = url_regex.sub("<...>", content)
            if not len(content) > 0:
                content = ""
        else:
            content = str(event.content)
        mentions = event.message.user_mentions_ids
        await sql.execute(
            "SELECT channel_id FROM channels WHERE server_id = ?",
            (event.guild_id, ))
        channels = await sql.fetchall()
        channel_ids = tuple(x[0] for x in channels)
        await sql.execute(
            "SELECT member_id FROM ignore_members WHERE server_id = ?",
            (event.guild_id, ))
        i_members = await sql.fetchall()
        i_member_ids = tuple(x[0] for x in i_members)
        ignore_content = False
        cur_channel = event.get_channel()
        # ######## #
        if event.author.id in i_member_ids:
            ignore_content = True
        if len(channels) > 0:
            pass
        elif cur_channel:
            if cur_channel.is_nsfw:
                ignore_content = True
        # ######## #
        if content:
            if len(content) > 1000:
                ignore_content = True
            english_chars = re.findall(r'[a-zA-Z]', content)
            percent_english = len(english_chars) / len(content) * 100
            if not percent_english <= 20:
                ignore_content = True
            cmd = """
            INSERT INTO messages (
                content, server_id, member_id, message_id, timestamp, channel_id
            )
            VALUES (?, ?, ?, ?, DATETIME('now'), ?)
            """
            if channel_ids != (0,) and r_mode != 'False' and not ignore_content:
                cmd_content = (
                    content, event.guild_id, event.author.id, message_id, event.channel_id
                )
            else:
                cmd_content = (
                    "", event.guild_id, event.author.id, message_id, event.channel_id
                )

            await sql.execute(cmd, cmd_content)
            m_mode = (await functions.Setting(db, "generator_mode").get(generator.default_mode))[0]
            g_mode = (await functions.Setting(db, "random_msgs").get("True"))[0]
            mn_mode = (await functions.Setting(db, "mention_to_generate").get("True"))[0]
            if g_mode == "True":
                random1 = random.randint(1, 100)
            else:
                random1 = -1
            if (m_mode in list(generator.modes_versions.keys()) or m_mode == "Random") and not m_mode == "off":
                if (random1 == 50) or (bot.get_me().id in mentions) and mn_mode != 'False':
                    limit = None
                    if m_mode == "Random":
                        limit = 45
                    await gen(sql, event, limit)
                    messages = await sql.fetchall()
                    if len(messages) >= 29:
                        if m_mode in list(generator.modes_versions.keys()):
                            combined_message = await async_combine_common_words(
                                " ||__|| ".join([message[0] for message in messages]),
                                2, 14, 3, 9, 22, version=generator.modes_versions[m_mode]
                            )
                        else:
                            combined_message = generator.random_words(" ".join([message[0] for message in messages]))
                        if combined_message:
                            try:
                                embed = hikari.Embed(
                                        description=combined_message,
                                        color=global_color
                                    )
                                await event.message.respond(embed)
                            except hikari.ForbiddenError:
                                await embed_error()
                    elif random1 != 50:
                        try:
                            if r_mode != 'False':
                                await event.message.respond(hikari.Embed(
                                    description=(
                                        "Я пока не могу генерировать сообщения. В базе данных у меня меньше 30 сообщений.\n" +
                                        f"У вас {len(messages)} сообщений.\n" +
                                        "Вы можете посмотреть в `info server` сколько доступно сообщений генератору\n"),
                                    color=global_color
                                            ))
                        except hikari.ForbiddenError:
                            await embed_error()
            elif m_mode not in generator.modes:
                await functions.Setting(db, "generator_mode").set(value=generator.default_mode)
        r_setting = functions.Setting(db, "read_content")
        n_setting = functions.Setting(db, "read_system")
        n_val = await n_setting.get('0')
        if n_val[0] == '0':
            await r_setting.set(value='False')
            await n_setting.set(value='1')
            text = ("Читание контента сообщений выключено\n" +
                    "Если вы администратор сервера и вам надо функции по типу генерации текста и т.д.\n" +
                    "Напишите `/switch read_msg_content mode:Включить`\n\n" +
                    "Если же вы обычный участник то сообщите любому участнику который имеет права администратора на этом сервере")
            embed = hikari.Embed(
                title="Информация",
                description=text,
                color=info.help_info_color
            )
            try:
                await event.message.respond(embed)
            except hikari.ForbiddenError:
                try:
                    await event.message.respond(text)
                except hikari.ForbiddenError:
                    ...
        # vl = (await functions.server_info(event))["level"]
        # if vl > 3 or vl == 0:
        #     ...
        # else:
        #     enabled = (await functions.Setting(db, "rank").get("False"))[0]
        #     if enabled != 'False':
        #         config = await functions.BlobVars(db, "rank").get({"min": 15, "max": 25, "mm": 1, "cooldown": 60})
        #         await functions.get_xp(event.author.id, db)
        #         lvlcalc = functions.LevelCalculation(config["mm"])
        #         if not event.member.is_bot:
        #             is_pass = False
        #             if event.message.content is not None:
        #                 if len(event.message.content) in range(3, 101):
        #                     is_pass = True
        #             else:
        #                 if len(event.message.attachments) > 0:
        #                     is_pass = True
        #             if is_pass:
        #                 await sql.execute(
        #                     "SELECT xp_cooldown FROM rank WHERE member_id = ?",
        #                     (event.author.id,)
        #                 )
        #                 xp_cooldown = await sql.fetchone()
        #                 xp_cooldown = xp_cooldown[0]
        #                 if (xp_cooldown) <= int(time()):
        #                     await sql.execute(
        #                         "SELECT xp FROM rank WHERE member_id = ?",
        #                         (event.author.id,)
        #                     )
        #                     user_xp = await sql.fetchone()
        #                     user_xp = user_xp[0]
        #                     max_xp = await lvlcalc.xp_all(120)
        #                     if user_xp < max_xp:
        #                         xp = await functions.get_xp(event.author.id, db)
        #                         xp = random.randint(config["min"], config["max"])
        #                         if user_xp + xp > max_xp:
        #                             total_xp = max_xp
        #                         else:
        #                             total_xp = user_xp + xp
        #                         level1 = (await functions.get_level_xp(user_xp))
        #                         level2 = (await functions.get_level_xp(total_xp))
        #                         await sql.execute(
        #                             """
        #                             UPDATE rank SET xp = ? WHERE member_id = ?
        #                             """,
        #                             (total_xp, event.author.id)
        #                         )
        #                         await sql.execute(
        #                             """
        #                             UPDATE rank SET xp_cooldown = ? WHERE member_id = ?
        #                             """,
        #                             (int(time())+config["cooldown"], event.author.id)
        #                         )
        #                         if level1 < level2:
        #                             await event.get_channel().send(embed=hikari.Embed(
        #                                 title='Новый уровень',
        #                                 description=f'{event.member.mention} достиг **{level2} уровня**!\n',
        #                                 color=global_color
        #                                 ))
        await db.commit()


extension_folders = ['main', 'premium']
unique_extensions = []

for x in extension_folders:
    bot.load_extensions_from(f"./extensions/{x}", must_exist=True)
for x in unique_extensions:
    bot.load_extensions_from(f"./extensions/unique/{x}", must_exist=True)
bot.load_extensions_from("./extensions/unique/")

if info.beta:
    main_logger.warning("Режим тестирования включен!")
main_logger.info(f"Время инициализации: {round((time()-info.start_time2), 3)} сек.")
if not beta:
    bot.run(shard_count=2)
else:
    bot.run()
