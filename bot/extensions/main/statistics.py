# by mrdan__(476046299691745300)
# oficial server: https://discord.gg/2e5SMn73Hw
import hikari
import lightbulb
import aiosqlite as sqlite3
import info as botinfo
from nltk.tokenize import word_tokenize
import datetime
from nltk.probability import FreqDist
from collections import Counter

import functions
from functions import gen
from info import global_color, error_color
from functions import async_createdb
import generator
import aiosqlite
bot_plugin = lightbulb.Plugin(
    "Статистика и информация",
    f"Сделал {botinfo.developer}"
)


async def r_mode(db: aiosqlite.Connection) -> bool | None:
    r_mode = (await functions.Setting(db, "read_content").get('False'))[0]
    return True if r_mode == 'True' else (False if r_mode == 'False' else None)


@functions.command("info", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def info(ctx: lightbulb.Context):
    ...


@info.child
@functions.command("info bot", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def info_bot(ctx: lightbulb.Context):
    desc = "**Версия:**"
    desc += f"\n**Бот:** `{botinfo.version}` {botinfo.version_timestamp}"
    desc += f"\n**Генератор:** `{generator.version}` {generator.version_timestamp}"
    embed = hikari.Embed(
        title="Информация о боте",
        description=desc,
        color=global_color
    )
    embed.add_field(
        name="Количество серверов",
        value=len(bot_plugin.bot.cache.get_available_guilds_view()),
        inline=True
    )
    embed.add_field(
        name="Мой сервер.",
        value=f"{botinfo.server_emoji} **[{botinfo.server_name}]({botinfo.server_invte})**",
        inline=True
    )
    embed.add_field(
        name="Мой создатель",
        value=f"`{botinfo.developer}`",
        inline=True
    )
    embed.add_field(
        name="Запущен",
        value=f"<t:{botinfo.start_time}:R>\nНа: **Python {botinfo.python_version}**",
        inline=True
    )
    embed.add_field(
        name="Дополнительно",
        value=(
            f"**Политика конфиденциальности:** [:link: Нажми]({botinfo.privacy_policy})\n" +
            f"**Условия использования:** [:link: Нажми]({botinfo.terms_of_service})"
        )
    )
    await ctx.respond(embed)


@info.child
@functions.command("info server", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def info_server(ctx: lightbulb.Context) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        desc = ""
        embed = hikari.Embed(
            title="Информация о сервере",
            description=desc,
            color=global_color
        )
        # топ 5 слов
        await gen(sql, ctx, 1000000, "ORDER BY id DESC", False, lenght=3, distinct=False)
        messages_d = await sql.fetchall()
        messages1 = [c[0] for c in messages_d]
        text = ' '.join(messages1)
        tokens = word_tokenize(text, language="russian", preserve_line=True)
        tokens = list(filter(lambda token: len(token) > 2, tokens))
        fdist = FreqDist(tokens)
        most_common_ = fdist.most_common(5)
        output = ""

        for i, (word, count) in enumerate(most_common_, start=1):
            output += f"**{i}**.{word}\n"
        if len(output) < 2:
            output = "Пусто"
        # топ 5 людей
        await sql.execute(
            "SELECT member_id FROM messages WHERE server_id = ?",
            (ctx.guild_id, ))
        users = await sql.fetchall()
        lst = [c[0] for c in users]
        count = Counter(lst)

        if len(lst) < 5:
            top_5 = Counter(lst).most_common(len(lst))
        else:
            top_5 = Counter(lst).most_common(10)
        result = []
        nums = []
        i = 0
        for element, count in top_5:
            if not i+1 > 5:
                member_id = element
                member = ctx.app.cache.get_user(member_id)
                if member is None:
                    member = ctx.get_guild().get_member(member_id)
                if member is not None:
                    if not member.is_bot and not member.is_system:
                        member_name = member.global_name or member.username
                        result.append(f"**{i+1}**. **{member_name}**: {count}")
                        i += 1
            nums.append(count)
        average = 0
        if len(nums) > 0:
            average = sum(nums) / len(nums)
        top = '\n'.join(result)
        top += f"\nСреднее число: {int(average)}"
        if len(top) < 2:
            top = "Пусто"

        await gen(sql, ctx, 10000000, "", False)
        msg_len = len(await sql.fetchall())

        # ###### #
        server = await functions.server_info(ctx)
        limit = server["configs"]["limit"]
        embed.add_field(
            name="Топ участников.",
            value=top,
            inline=True
        )
        r_mode = (await functions.Setting(db, "read_content").get('False'))[0]
        if r_mode != 'False':
            embed.add_field(
                name="Топ 5 слов.",
                value=output,
                inline=True
            )
        embed.add_field(
            name="Количество сообщений на этом сервере",
            value=f"{len(users)}",
            inline=False
        )
        if r_mode != 'False':
            embed.add_field(
                name="Доступно сообщений генератору (фильтр)",
                value=(f"Лимит {limit}" +
                       f"\n{msg_len}"),
                inline=True
            )
        expire = server['configs']['expire']
        when_expire = f"До: <t:{expire}:d> <t:{expire}:T>" if expire != -1 and expire != 0 else ""
        embed.add_field(
            name="Премиум",
            value=f"{when_expire}\n{'-' if int(server['level']) == 0 else server['level']}/3",
            inline=False
        )
        if r_mode == 'False':
            embed.add_field(
                name="Читание контента сообщений",
                value="`/switch read_msg_content`\nВыключено",
                inline=False
            )
        # embed.add_field(
        #     name="Глобальная очистка баз данных.",
        #     value=botinfo.wipe,
        #     inline=True
        # )
    await ctx.respond(embed)


@functions.command("leaders", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def leaders(ctx: lightbulb.Context, page: int) -> None:
    if page is None:
        page = 1
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        await sql.execute(
            "SELECT content, member_id FROM messages WHERE server_id = ?",
            (ctx.guild_id, ))
        users = await sql.fetchall()
        lst = [c[1] for c in users]
        count = Counter(lst)

        top = Counter(lst).most_common(len(lst))
        result = []
        nums = []
        unknown_member_msgs = 0
        for element, count in top:
            member_id = element
            member = ctx.app.cache.get_user(member_id)
            if member is None:
                member = ctx.get_guild().get_member(member_id)
            if member is not None:
                if not member.is_bot and not member.is_system:
                    member_name = member.global_name or member.username
                    result.append(f"**{member_name}**: {count}")
            else:
                unknown_member_msgs += count
            nums.append(count)
        average = 0
        if len(nums) > 0:
            average = sum(nums) / len(nums)
        embed = hikari.Embed(
            title="Топ участников.",
            description="",
            color=global_color
        )
    view = functions.Views.Pages(
        result, ctx, embed, 10, page, ctx.author.id,
        timeout=60, bottom=f"\nСообщений от неизвестных участников: {unknown_member_msgs}\nСреднее число: {int(average)}")
    await view.generate_list()
    ctx.app.d.miru.start_view(view)


@functions.command("top", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def top(
        ctx: lightbulb.Context,
        page: int, time: str
        ) -> None:
    if time not in botinfo.CHOICES["toptime"]:
        time = botinfo.CHOICES["toptime"][0]
    chch = ["all", "today", "tm", "7 days", "30 days"]
    orgtime = time
    time = chch[botinfo.CHOICES["toptime"].index(time)]
    if page is None:
        page = 1
    msg = None
    view = None
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)

        r_mode = (await functions.Setting(db, "read_content").get('False'))[0]
        if r_mode != 'False':
            args = (sql, ctx, 1000000)
            kwargs = {"random": False, "lenght": 3, "distinct": False}
            match time:
                case "all":
                    await gen(*args, "ORDER BY id DESC", **kwargs)
                    messages_d = await sql.fetchall()
                case "today":
                    await gen(*args, "AND timestamp >= date('now', 'start of day') ORDER BY id DESC", **kwargs)
                    messages_d = await sql.fetchall()
                case "tm":
                    await gen(*args, "AND timestamp >= date('now', '-1 day') AND timestamp < date('now', 'start of day') ORDER BY id DESC", **kwargs)
                    messages_d = await sql.fetchall()
                case "7 days":
                    await gen(*args, "AND timestamp >= date('now', '-7 days') ORDER BY id DESC", **kwargs)
                    messages_d = await sql.fetchall()
                case "30 days":
                    await gen(*args, "AND timestamp >= date('now', '-1 month') ORDER BY id DESC", **kwargs)
                    messages_d = await sql.fetchall()
            messages1 = [c[0] for c in messages_d]
            text = ' '.join(messages1)
            tokens = word_tokenize(text, language="russian", preserve_line=True)
            tokens = list(filter(lambda token: len(token) > 2, tokens))
            fdist = FreqDist(tokens)
            most_common_ = fdist.most_common()

            elements = []
            for word, count in most_common_:
                elements.append(f"{word} ({count} исп.)")
            embed = hikari.Embed(
                title=f"Топ 5 слов {orgtime.lower()}",
                description="",
                color=global_color
            )
            embed.set_footer("Только сообщения из разрешенных каналов на этом сервере.")
            view = functions.Views.Pages(elements, ctx, embed, 5, page, ctx.author.id, timeout=60)
        else:
            embed = hikari.Embed(
                description="Читание контента сообщений выключено!",
                color=error_color
            )
            embed.set_footer("Чтобы включить напишите /switch read_msg_content")
    if msg is None and view is None:
        await ctx.respond(embed)
    else:
        msg = await view.generate_list()
        ctx.app.d.miru.start_view(view)


@functions.command("most_msgs_time", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def most_msgs_time(ctx: lightbulb.Context, page: int) -> None:
    if page is None:
        page = 1
    view = None
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        elements, succes, max_page, dates = await functions.most_msgs_time(ctx.guild_id, db, sql)
        if succes:
            page = min(max_page, page)
            embed = hikari.Embed(
                title="Самые активные дни сервера",
                description="`/msgs time` `время` - для подробной информации",
                color=global_color
            )
            view = functions.Views.Pages(elements, ctx, embed, 5, page, ctx.author.id, timeout=60)

        else:
            embed = hikari.Embed(
                title="Самый большой актив",
                description="Не удалось получить информацию",
                color=global_color
            )
            await ctx.respond(embed)
    if view is not None:
        await view.generate_list()
        ctx.app.d.miru.start_view(view)


@functions.command("channels_top", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def channels_top(ctx: lightbulb.Context, page: int = None) -> None:
    if page is None:
        page = 1
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        await sql.execute("""SELECT COUNT(*) AS count
            FROM messages
            WHERE channel_id IS NULL
        """)
        no_channels_count = await sql.fetchone()
        no_channels_count = no_channels_count[0]
        await sql.execute("""SELECT channel_id, COUNT(channel_id) AS count
            FROM messages
            GROUP BY channel_id
            ORDER BY count DESC
            LIMIT 100
        """)
        channels = await sql.fetchall()
        channels = [(value, count) for value, count in channels if value is not None]
        elements = []
        for item in channels:
            elements.append(f'<#{item[0]}>: {item[1]} сообщений')
        bottom = ""
        if no_channels_count > 0:
            bottom += "\n### Старые версии:"
            bottom += f"\n * сообщений без канала: {no_channels_count}"
        embed = hikari.Embed(
            title="Топ 10 каналов.",
            description="",
            color=global_color
        )
    view = functions.Views.Pages(elements, ctx, embed, 10, page, ctx.author.id, timeout=60, bottom=bottom)
    await view.generate_list()
    ctx.app.d.miru.start_view(view)


@functions.command("msgs", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def msgs(ctx: lightbulb.Context) -> None:
    ...


@msgs.child
@functions.command("msgs member", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def msgs_member(ctx: lightbulb.Context, member: hikari.Member) -> None:
    if member is None:
        member = ctx.author
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        await sql.execute(
            "SELECT content, member_id FROM messages WHERE server_id = ? AND member_id = ?",
            (ctx.guild_id, member.id))
        messages = await sql.fetchall()
        await sql.execute(
            """SELECT content, member_id
            FROM messages
            WHERE server_id = ?
            AND member_id = ?
            AND timestamp >= date('now', 'start of day')
            """,
            (ctx.guild_id, member.id))
        messages_1d = await sql.fetchall()
        await sql.execute(
            """SELECT content, member_id
            FROM messages
            WHERE server_id = ?
            AND member_id = ?
            AND timestamp >= date('now', '-1 day')
            AND timestamp < date('now', 'start of day');
            """,
            (ctx.guild_id, member.id))
        messages_tm = await sql.fetchall()
        await sql.execute(
            """SELECT content, member_id
        FROM messages
        WHERE server_id = ?
        AND member_id = ?
        AND timestamp >= date('now', '-7 days')
            """,
            (ctx.guild_id, member.id))
        messages_7d = await sql.fetchall()
        await sql.execute(
            """SELECT content, member_id
        FROM messages
        WHERE server_id = ?
        AND member_id = ?
        AND timestamp >= date('now', '-1 month')
            """,
            (ctx.guild_id, member.id))
        messages_30d = await sql.fetchall()
        description = (
            f"Участник <@{member.id}> написал **{len(messages)}** сообщений.\n" +
            f"Сегодня **{len(messages_1d)}** сообщений.\n" +
            f"Вчера **{len(messages_tm)}** сообщений.\n" +
            f"За последние 7 дней **{len(messages_7d)}** сообщений.\n" +
            f"За последний месяц **{len(messages_30d)}** сообщений.\n"
        )
        if messages:
            embed = hikari.Embed(
                title="Статистика",
                description=description,
                color=global_color
            )
        else:
            embed = hikari.Embed(
                description="Этот участник ничего не писал",
                color=error_color
            )
    await ctx.respond(embed)


@msgs.child
@functions.command("msgs all", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def msgs_all(ctx: lightbulb.Context) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        embed = hikari.Embed(
            description="Что то случилось",
            color=error_color
        )
        d1_messages_succes = True
        tm_messages_succes = True
        d7_messages_succes = True
        d30_messages_succes = True
        await sql.execute(
            "SELECT COUNT(*) FROM(SELECT member_id FROM messages WHERE server_id = ?) AS uniq",
            (ctx.guild_id,))
        messages = await sql.fetchone()
        messages = messages[0]

        try:
            await sql.execute(
                """SELECT member_id
                FROM messages
                WHERE server_id = ?
                AND timestamp >= date('now', 'start of day')
                """,
                (ctx.guild_id,))
            messages_1d = await sql.fetchall()
            temp = [item[0] for item in messages_1d]
            most_active_user_1d = Counter(temp).most_common(min(1, len(temp)))[0]
        except IndexError:
            d1_messages_succes = False

        try:
            await sql.execute(
                """SELECT member_id
                FROM messages
                WHERE server_id = ?
                AND timestamp >= date('now', '-1 day')
                AND timestamp < date('now', 'start of day');
                """,
                (ctx.guild_id,))
            messages_tm = await sql.fetchall()
            temp = [item[0] for item in messages_tm]
            most_active_user_tm = Counter(temp).most_common(min(1, len(temp)))[0]
        except IndexError:
            tm_messages_succes = False

        try:
            await sql.execute(
                """SELECT member_id
            FROM messages
            WHERE server_id = ?
            AND timestamp >= date('now', '-7 days')
                """,
                (ctx.guild_id,))
            messages_7d = await sql.fetchall()
            temp = [item[0] for item in messages_7d]
            most_active_user_7d = Counter(temp).most_common(min(1, len(temp)))[0]
        except IndexError:
            d7_messages_succes = False

        try:
            await sql.execute(
                """SELECT member_id
            FROM messages
            WHERE server_id = ?
            AND timestamp >= date('now', '-1 month')
                """,
                (ctx.guild_id,))
            messages_30d = await sql.fetchall()
            temp = [item[0] for item in messages_30d]
            most_active_user_30d = Counter(temp).most_common(min(1, len(temp)))[0]
        except IndexError:
            d30_messages_succes = False
        # среднее количество

        if d30_messages_succes or d7_messages_succes:
            await sql.execute(
                """SELECT strftime('%Y-%m-%d', timestamp) AS message_day, COUNT(*) AS message_count
                FROM messages
                WHERE server_id = ?
                AND timestamp >= date('now', '-30 day')
                GROUP BY message_day;
                """,
                (ctx.guild_id,))
            messages_per_day = await sql.fetchall()
        if d7_messages_succes:
            temp = [item[1] for item in messages_per_day[-min(len(messages_per_day), 7):]]
            messages_7d1 = int(sum(temp) / len(temp))
        else:
            messages_7d1 = 0

        if d30_messages_succes:
            temp = [item[1] for item in messages_per_day]
            messages_30d1 = int(sum(temp) / len(temp))
        else:
            messages_30d1 = 0

        description = f"> Все участники написали **{messages}** сообщений.\n\n"

        if d1_messages_succes:
            description += (
                f"> **Сегодня:**\nВсе: **{len(messages_1d)}** сообщений.\n" +
                f"Самый активный участник: <@{most_active_user_1d[0]}> (Сообщений: {most_active_user_1d[1]})\n\n"
            )
        else:
            description += f"> **Сегодня**: **{len(messages_1d)}** сообщений.\n"

        if tm_messages_succes:
            description += (
                f"> **Вчера:**\nВсе: **{len(messages_tm)}** сообщений.\n" +
                f"Самый активный участник: <@{most_active_user_tm[0]}> (Сообщений: {most_active_user_tm[1]})\n\n"
            )
        else:
            description += f"> **Вчера**: **{len(messages_tm)}** сообщений.\n\n"

        if d7_messages_succes:
            description += (
                f"> **За последние 7 дней:**\nОбщее количество: **{len(messages_7d)}** сообщений.\n" +
                f"Самый активный участник: <@{most_active_user_7d[0]}> (Сообщений: {most_active_user_7d[1]})\n" +
                f"Среднее количество на день: **{messages_7d1}** сообщений.\n\n"
            )
        else:
            description += f"> **За последние 7 дней**: **{len(messages_7d)}** сообщений.\n\n"

        if d30_messages_succes:
            description += (
                f"> **За последние 30 дней:**\nОбщее количество: **{len(messages_30d)}** сообщений.\n" +
                f"Самый активный участник: <@{most_active_user_30d[0]}> (Сообщений: {most_active_user_30d[1]})\n" +
                f"Среднее количество на день: **{messages_30d1}** сообщений.\n"
            )
        else:
            description += f"> **За последние 30 дней**: **{len(messages_30d)}** сообщений.\n\n"

        if messages:
            embed = hikari.Embed(
                title="Статистика",
                description=description,
                color=global_color
            )
        else:
            embed = hikari.Embed(
                description="Пока пусто",
                color=error_color
            )
    await ctx.respond(embed)


@msgs.child
@functions.command("msgs time", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def msgs_time(ctx: lightbulb.Context, date: str) -> None:
    error = False
    try:
        if botinfo.regex["date"].fullmatch(date):
            date_object = datetime.datetime.strptime(date, "%d.%m.%Y")
        else:
            error = True
    except ValueError:
        error = True
    if not error:
        async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
            sql = await db.cursor()
            await async_createdb(ctx.guild_id, sql, db)
            embed = hikari.Embed(
                description="Что то случилось",
                color=error_color
            )
            original_date = date
            date = date_object.strftime("%Y-%m-%d")
            query = "SELECT COUNT(*) FROM messages WHERE timestamp >= ? AND timestamp < ?"
            start_date = date + ' 00:00:00'
            end_date = date + ' 23:59:59'
            await sql.execute(query, (start_date, end_date))
            _count = await sql.fetchone()
            # ## #
            await sql.execute(
                "SELECT member_id FROM messages WHERE server_id = ? AND timestamp >= ? AND timestamp < ?",
                (ctx.guild_id, start_date, end_date))
            users = await sql.fetchall()
            lst = [c[0] for c in users]
            count = Counter(lst)

            if len(lst) < 5:
                top_5 = Counter(lst).most_common(len(lst))
            else:
                top_5 = Counter(lst).most_common(5)
            result = []
            i = 0
            for element, count in top_5:
                if not i+1 > 5:
                    member_id = element
                    member = ctx.app.cache.get_user(member_id)
                    if member is None:
                        member = ctx.get_guild().get_member(member_id)
                    if member is not None:
                        if not member.is_bot and not member.is_system:
                            member_name = member.global_name or member.username
                            result.append(f"**{i+1}**. **{member_name}**: {count}")
                            i += 1
            output = "\n".join(result)
            # ## #
            await sql.execute("""SELECT COUNT(*) AS count
                FROM messages
                WHERE channel_id IS NULL  AND timestamp >= ? AND timestamp < ?
            """, (start_date, end_date))
            no_channels_count = await sql.fetchone()
            no_channels_count = no_channels_count[0]
            await sql.execute("""SELECT channel_id, COUNT(channel_id) AS count
                FROM messages
                WHERE timestamp >= ? AND timestamp < ?
                GROUP BY channel_id
                ORDER BY count DESC
                LIMIT 5;
            """, (start_date, end_date))
            channels = await sql.fetchall()
            channels = [(value, count) for value, count in channels if value is not None]
            top_5_str = '\n'.join([f'<#{item[0]}>: {item[1]} сообщений' for item in channels[:10]])
            if no_channels_count > 0:
                top_5_str += "\n### Старые версии:"
                top_5_str += f"\n * сообщений без канала: {no_channels_count}"
            # ## #
            embed = hikari.Embed(
                title="Статистика",
                description=(
                    f"**Дата:** `{original_date}`\n" +
                    f"**Количество сообщений:** {_count[0]}\n\n" +
                    f'**Топ 5 участников:**\n {output}\n' +
                    f"**Топ 5 каналов:**\n {top_5_str}"
                ),
                color=global_color
            )
    else:
        embed = hikari.Embed(
            description="Дата должна быть в формате день.месяц.год, пример: `26.10.2023`",
            color=error_color
        )
    await ctx.respond(embed)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(bot_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(bot_plugin)
