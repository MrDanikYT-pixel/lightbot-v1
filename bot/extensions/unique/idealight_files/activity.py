# by mrdan__(476046299691745300)
# oficial server: https://discord.gg/2e5SMn73Hw
import datetime
import logging
import time
import aiohttp
import hikari
import lightbulb
import aiosqlite
import info  # type: ignore
import extensions.unique.idealight_files.afunctions as afunctions  # type: ignore
from info import global_color  # , error_color
from nltk.tokenize import word_tokenize  # type: ignore
from nltk.probability import FreqDist  # type: ignore
from collections import Counter
from collections import defaultdict
from functions import async_createdb  # type: ignore
import functions
import dotenv
import os
import asyncio

server = afunctions.server
send_query = []

bot_plugin = lightbulb.Plugin(
    "Уникальные функции IdeaLight",
    f"Сделал {info.developer}",
    default_enabled_guilds=server
)

CHOICES = info.CHOICES

dotenv.load_dotenv()
RESULTS_WEBHOOK = os.environ["RESULTS_WEBHOOK"]

point_emoji = 'б'
__filename__ = os.path.basename(__file__)
filename = os.path.splitext(__filename__)[0]
main_logger = logging.getLogger(f"{__package__.split('.')[-1]}.{filename}")


def administrator_command(func):
    func = lightbulb.app_command_permissions(hikari.Permissions.ADMINISTRATOR)(func)
    return func


def administrator_sub_command(func):
    func = lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))(func)
    return func


@functions.command("most_active_members", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def most_active_members(ctx: lightbulb.Context, page: str) -> None:
    async with aiosqlite.connect('../db/idealight.sqlite') as db:
        sql = await db.cursor()
        result = await (await sql.execute("""SELECT user_id, points FROM points""")).fetchall()
        result = list(result)
        sorted_result = sorted(result, key=lambda x: x[1], reverse=True)
        elements = []
        for x in sorted_result:
            member = ctx.app.cache.get_user(x[0])
            if member is None:
                member = ctx.get_guild().get_member(x[0])
            member_name = "Неизвестный"
            if member is not None:
                member_name = member.global_name or member.username
            elements.append(f"<@{x[0]}>**({member_name})**: {x[1]} {point_emoji}")
        embed = hikari.Embed(
            title="Самые активные участники",
            description="",
            color=global_color
        )
    view = functions.Views.Pages(
        elements, ctx, embed, 10, page, ctx.author.id,
        timeout=60)
    await view.generate_list()
    ctx.app.d.miru.start_view(view)


@functions.command("activity_points", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def activity_points(ctx: lightbulb.Context, member: hikari.Member) -> None:
    if member is None:
        member = ctx.member
    async with aiosqlite.connect('../db/idealight.sqlite') as db:
        sql = await db.cursor()
        result = await (await sql.execute("""SELECT points FROM points WHERE user_id = ?""", (member.id,))).fetchone()
        points = 0
        if result is not None:
            points = result[0]
        embed = hikari.Embed(
            title="Баллы активности",
            description=f"**Участник:** {member.mention} \n**Количество баллов:** {points}",
            color=global_color
        )
        embed.set_thumbnail(member.avatar_url)
    await ctx.respond(embed)


@bot_plugin.listener(hikari.StartingEvent)
async def starting(event: hikari.StartingEvent):
    await initialize_settings()


@bot_plugin.listener(hikari.StartedEvent)
async def on_start(event: hikari.StartedEvent):
    asyncio.create_task(on_started(event))


async def on_started(event: hikari.StartedEvent) -> None:
    asyncio.create_task(timer())
    asyncio.create_task(send_query_timer())
    asyncio.create_task(most_msgs_time_record_timer())


async def initialize_settings() -> None:
    async with aiosqlite.connect('../db/idealight.sqlite') as db:
        most_msgs_time = functions.Setting(db, "most_msgs_time")
        if (await most_msgs_time.get("..."))[0] == "...":
            await most_msgs_time.set(value="2023-01-01")
        await db.commit()


async def most_msgs_time_record_timer() -> None:
    while True:
        async with aiosqlite.connect(f'../db/{server[0]}database.sqlite') as db:
            sql = await db.cursor()
            elements, succes, max_page, dates = await functions.most_msgs_time(server[0], db, sql)
            most_msgs_time = functions.Setting(db, "most_msgs_time")
            today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
            if succes:
                if dates[0][0] == today:
                    if (await most_msgs_time.get("..."))[0] != f"{today}":
                        await most_msgs_time.set(value=f"{today}")
                        await db.commit()
                        data = {
                            "content": ""
                        }
                        data["embeds"] = [
                            {
                                "description": f"**Кажется сегодня был побит рекорд по количество сообщений за день!** \n{dates[0][1]} сообщений",
                                "title": "Рекорд",
                                "color": global_color
                            }
                        ]
                        send_query.append(data)
        await asyncio.sleep(5)


async def send_query_timer():
    async with aiohttp.ClientSession() as session:
        while True:
            if len(send_query) > 0:
                data = send_query[0]
                send_query.remove(data)
                for x in range(10):
                    async with session.post(RESULTS_WEBHOOK, json=data) as response:
                        if response.status == 429:
                            await asyncio.sleep(5)
                        else:
                            break
            await asyncio.sleep(1)


async def analyze_time(start_date: str, end_date: str, db: aiosqlite.Connection, sql: aiosqlite.Cursor | None = None) -> dict:
    if sql is None:
        sql = await db.cursor()

    if ":" not in start_date:
        start_date = start_date.strip() + " 00:00:00"

    if ":" not in end_date:
        end_date = end_date.strip() + "23:59:59"

    async def msgs(sql: aiosqlite.Cursor, start_date: str, end_date: str, select: str = "member_id,content,timestamp") -> aiosqlite.Cursor:
        # await sql.execute(
        #     "SELECT channel_id FROM channels")
        # channels = await sql.fetchall()
        # channel_ids = tuple(x[0] for x in channels)
        # if channel_ids:
        #     channel_ids_sql = "AND (channel_id IN ({}) OR channel_id IS NULL)".format(
        #         ','.join(['?' for _ in channel_ids]))
        # else:
        #     channel_ids_sql = ""
        query = f"""SELECT {select}
                    FROM messages
                    WHERE timestamp >= ? AND timestamp < ?
                    """
        # params = (start_date, end_date) + tuple(channel_ids) if channel_ids else (start_date, end_date)
        params = (start_date, end_date)
        await sql.execute(query, params)
        return sql

    result = await (await msgs(sql, start_date=start_date, end_date=end_date)).fetchall()
    temp = [item[0] for item in result]
    topmembers = Counter(temp).most_common()

    dd = {
        "topmembers": [],
        "topwords": [],
        "status": 0,
        "msgcount": len(result),
        "membercount": len(topmembers),
        "avg_msgs_per_hour": 0,
    }

    # top members and average messages per hour
    msgs_per_hour_list = []
    for target_user_id, msgcount in topmembers:
        daily_message_count = defaultdict(int)

        for user_id, _, timestamp in result:
            if user_id == target_user_id:
                day = str(timestamp).split()[0]
                daily_message_count[day] += 1

        average_messages_per_hour = round(sum(daily_message_count.values()) / 24, 2)
        if average_messages_per_hour > 0.01:
            msgs_per_hour_list.append(average_messages_per_hour)
            dd["topmembers"].append([target_user_id, average_messages_per_hour, msgcount])

    daily_message_count = defaultdict(int)
    for user_id, _, timestamp in result:
        day = str(timestamp).split()[0]
        daily_message_count[day] += 1
    average_messages_per_hour = round(sum(daily_message_count.values()) / 24, 2)

    dd["avg_msgs_per_hour"] = average_messages_per_hour

    # top words
    messages = [c[1] for c in result]
    text = ' '.join(messages)
    tokens = word_tokenize(text, language="russian", preserve_line=True)
    tokens = list(filter(lambda token: len(token) > 2, tokens))
    fdist = FreqDist(tokens)
    most_common_word = fdist.most_common(5)
    for word, count in most_common_word:
        dd["topwords"].append([word, count])

    # status
    def addstatus(avg_msgs_more_than: int, membercount_more_than: int):
        if dd["avg_msgs_per_hour"] >= avg_msgs_more_than and dd["membercount"] >= membercount_more_than:
            dd["status"] += 1

    addstatus(2, 2)
    addstatus(10, 4)
    addstatus(30, 5)
    addstatus(50, 7)
    addstatus(90, 15)
    addstatus(200, 25)

    return dd


def calculate_percentage_difference(a, b):
    if b == 0:
        return 0

    percentage = ((a - b) / (b if b != 0 else 1)) * 100
    return percentage


async def timer() -> None:
    first_run = True
    status_names = {
        0: "Плохой",
        1: "Маленький",
        2: "Неплохой",
        3: "Хороший",
        4: "Большой",
        5: "Сумашедный",
        6: "Монстр"
    }
    status_colors = {
        0: 0xd21801,
        1: 0xff8e5c,
        2: 0xffee46,
        3: 0x8ff8fb,
        4: 0x009af2,
        5: 0x8432d6,
        6: 0x959883
    }
    main_logger.info("Timer started!")
    while True:
        start = time.perf_counter()
        async with aiosqlite.connect('../db/idealight.sqlite') as db:
            sql = await db.cursor()
            async with aiosqlite.connect(f'../db/{server[0]}database.sqlite') as db2:
                sql2 = await db2.cursor()
                await async_createdb(server[0], sql2, db2)
                today = datetime.datetime.now(datetime.timezone.utc).date()
                # date_str = "2024-01-20"

                async def msg(date_str: str):
                    sent = await (await sql.execute("""SELECT date FROM sent WHERE date = ?""", (date_str,))).fetchone()
                    _calc = await (await sql.execute("""SELECT date FROM calc WHERE date = ?""", (date_str,))).fetchone()
                    if _calc is not None and sent is not None:
                        return
                    add_points = []
                    sub_points = []
                    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    date_minus_1 = date_obj - datetime.timedelta(days=1)
                    date_minus_2 = date_obj - datetime.timedelta(days=2)
                    date_minus_3 = date_obj - datetime.timedelta(days=3)
                    date_0 = date_minus_3.strftime("%Y-%m-%d")
                    date_1 = date_minus_2.strftime("%Y-%m-%d")
                    date_2 = date_minus_1.strftime("%Y-%m-%d")
                    date_3 = date_str
                    result0 = await analyze_time(date_0, date_0, db2)
                    result1 = await analyze_time(date_1, date_1, db2)
                    result2 = await analyze_time(date_2, date_2, db2)
                    result3 = await analyze_time(date_3, date_3, db2)
                    member_top = ""
                    for i, x in enumerate(result3['topmembers'], start=1):
                        points = [x[1], 0, 0]
                        ...
                        for y in result2['topmembers']:
                            if y[0] == x[0]:
                                points[1] = y[1]/25
                                continue
                            else:
                                continue
                        ...
                        for y in result1['topmembers']:
                            if y[0] == x[0]:
                                points[2] = y[1]/25
                                continue
                            else:
                                continue
                        ...
                        points = round(sum(points) / len(points), 2)
                        add_points.append([x[0], points])
                        if i > 5:
                            continue
                        member_top += f'\n**{i}\\.** <@{x[0]}>: {x[1]} с/ч ({x[2]} всего) (+ {points} {point_emoji})'
                    ########
                    for x in result0['topmembers']:
                        skip = False
                        for y in result3["topmembers"]:
                            if x[0] == y[0]:
                                skip = True
                        if skip:
                            continue
                        ######
                        for y in result2["topmembers"]:
                            if x[0] == y[0]:
                                skip = True
                        if skip:
                            continue
                        if skip:
                            continue
                        ######
                        for y in result1["topmembers"]:
                            if x[0] == y[0]:
                                skip = True
                        if skip:
                            continue
                    # top words
                    topwords = ""
                    for i, x in enumerate(result3['topwords'], start=1):
                        topwords += f'\n**{i}\\.** {x[0]} ({x[1]} исп.)'

                    calc = round(calculate_percentage_difference(result3['avg_msgs_per_hour'], result2['avg_msgs_per_hour']))
                    calc2 = result3['membercount']-result2['membercount']
                    description = (
                        f"**Общее количество сообщений:** {result3['msgcount']}\n" +
                        f"**Топ участников:** (сообщений/час) {member_top}\n" +
                        f"**Среднее количество сообщений в час:** {result3['avg_msgs_per_hour']}\n" +
                        f"**Количество участников писало:** {result3['membercount']} (на {abs(calc2)} {'больше' if calc2 > 0 else 'меньше'} чем вчера)\n" +
                        f"**Насколько актив лучше по сравнению с вчерашним днем:** {calc}%\n\n" +
                        (f"**Топ слов:** {topwords}\n\n" if len(topwords) > 0 else '') +
                        f"**Статус актива:** {status_names[result3['status']]} ({result3['status']})\n"
                    )
                    data = {
                        "content": ""
                    }
                    data["embeds"] = [
                        {
                            "description": description,
                            "title": f"Итог {date_str}",
                            "color": status_colors[result3['status']]
                        }
                    ]
                    # last messages
                    last_messages = await (await sql2.execute("""
                            SELECT member_id, MAX(timestamp) AS last_message
                            FROM messages
                            WHERE timestamp <= ?
                            GROUP BY member_id
                        """, (f"{date_str} 23:59:59",))).fetchall()

                    for x in last_messages:
                        date1_str = str(x[1]).split()[0]
                        date2_str = date_str
                        date1 = datetime.datetime.strptime(date1_str, "%Y-%m-%d")
                        date2 = datetime.datetime.strptime(date2_str, "%Y-%m-%d")
                        delta = date2 - date1
                        days_between = delta.days
                        if days_between > 2:
                            sub_points.append((x[0], max(1, (days_between-2)/2)))
                    # send result
                    if sent is None:
                        # send_query.append(data)
                        await sql.execute("""INSERT INTO sent (date) VALUES (?)""", (date_str,))
                    if _calc is None:
                        balance = afunctions.Points(db, sql)
                        await sql.execute("""INSERT INTO calc (date) VALUES (?)""", (date_str,))
                        for x in add_points:
                            member_points = await balance.get(x[0])
                            await balance.set(x[0], member_points+x[1])
                        add_points.clear()
                        for x in sub_points:
                            member_points = await balance.get(x[0])
                            if member_points > 0:
                                await balance.set(x[0], max(member_points-x[1], 0))
                            else:
                                continue
                    await db.commit()
                if first_run:
                    all_dates = []
                    start_date = "2023-08-28"
                    start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                    delta = datetime.datetime.now(datetime.timezone.utc).today() - start_date_obj
                    days_between = delta.days
                    for i in range(1, days_between):
                        date_obj = today - datetime.timedelta(days=i)
                        all_dates.append(date_obj.strftime("%Y-%m-%d"))
                    # first_run = True
                    all_dates.reverse()
                    for x in all_dates:
                        await msg(x)
                # else:
                #     await msg((today - datetime.timedelta(days=1)).strftime("%Y-%m-%d"))
            end = time.perf_counter()
        await asyncio.sleep(max(60-(end-start), 1))


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(bot_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(bot_plugin)
