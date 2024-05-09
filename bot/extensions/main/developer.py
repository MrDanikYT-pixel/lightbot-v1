# by mrdan__(476046299691745300)
# oficial server: https://discord.gg/2e5SMn73Hw
import hikari
import lightbulb
import aiosqlite as sqlite3
import info as botinfo
import sqlite3 as sql3
from info import global_color, error_color
import functions

import aiohttp
import dotenv
import os

bot_plugin = lightbulb.Plugin(
    "Связь с разработчиком",
    f"Сделал {botinfo.developer}"
)
dotenv.load_dotenv()
ideas_webhook = os.environ["IDEAS_WEBHOOK"]
with sql3.connect('../db/database.sqlite') as db:
    sql = db.cursor()

    sql.execute("""CREATE TABLE IF NOT EXISTS bugs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id        INTEGER NOT NULL,
            user_id      INTEGER NOT NULL,
            user_name    TEXT    NOT NULL,
            description  TEXT    NOT NULL,
            short_desc  TEXT,
            steps        TEXT
        )""")
    sql.execute("""CREATE TABLE IF NOT EXISTS block_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER,
            type TEXT
        )""")
    sql.execute("""CREATE TABLE IF NOT EXISTS block_guilds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            type TEXT
        )""")


@functions.command("send_idea", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def send_idea(
        ctx: lightbulb.Context,
        text: str,
        ) -> None:
    async with sqlite3.connect('../db/database.sqlite') as db:
        sql = await db.cursor()
        await sql.execute(
            """SELECT type FROM block_users WHERE member_id = ?""",
            (ctx.author.id,)
        )
        block_users = await sql.fetchone()
        await sql.execute(
            """SELECT type FROM block_guilds WHERE guild_id = ?""",
            (ctx.guild_id,)
        )
        block_guilds = await sql.fetchone()
        blocked = False
        srv_block = False
        usr_block = False
        if block_users:
            block_users_type = block_users[0]
            if block_users_type in ['all', 'ideas']:
                blocked = True
                usr_block = True
        if block_guilds:
            block_guilds_type = block_guilds[0]
            if block_guilds_type in ['all', 'ideas']:
                blocked = True
                srv_block = True
    if not blocked:
        data = {
            "content": None,
            "username": f'{ctx.author.username}({ctx.author.id})',
            "avatar_url": str(ctx.author.avatar_url)
        }
        data["embeds"] = [
            {
                "description": str(text),
                "title": "Новая идея",
                "color": 16416801
            }
        ]
        async with aiohttp.ClientSession() as session:
            async with session.post(ideas_webhook, json=data) as response:
                response: aiohttp.ClientResponse = response
        if response.status == 204:
            embed = hikari.Embed(
                description="Ваша идея была отправлена на сервер Idealight",
                color=global_color
            )
        else:
            embed = hikari.Embed(
                description=f"Не удалось отправить идею на сервер IdeaLight. (Код: {response.status})",
                color=error_color
            )
    else:
        if usr_block:
            embed = hikari.Embed(
                description='Вы заблокированы!',
                color=error_color
            )
        if srv_block:
            embed = hikari.Embed(
                description='Этот сервер заблокированы!',
                color=error_color
            )
    await ctx.respond(embed)


@functions.command("report_bug", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def report_bug(
        ctx: lightbulb.Context,
        text: str,
        short_desc: str,
        steps: str
        ) -> None:
    text = str(ctx.options.text).replace('\\n', '\n')
    short_desc = ctx.options.short_desc
    steps = ctx.options.steps
    if steps is None:
        steps = ''
    async with sqlite3.connect('../db/database.sqlite') as db:
        sql = await db.cursor()
        await sql.execute(
            """SELECT type FROM block_users WHERE member_id = ?""",
            (ctx.author.id,)
        )
        block_users = await sql.fetchone()
        await sql.execute(
            """SELECT type FROM block_guilds WHERE guild_id = ?""",
            (ctx.guild_id,)
        )
        block_guilds = await sql.fetchone()
        blocked = False
        srv_block = False
        usr_block = False
        if block_users:
            block_users_type = block_users[0]
            if block_users_type in ['all', 'ideas']:
                blocked = True
                usr_block = True
        if block_guilds:
            block_guilds_type = block_guilds[0]
            if block_guilds_type in ['all', 'ideas']:
                blocked = True
                srv_block = True
        if not blocked:
            await functions.InfoSystem(os.environ["IDEAS_WEBHOOK"], db).send_bug(ctx.guild_id, ctx.author.id, ctx.author.username, text, short_desc, steps)
            embed = hikari.Embed(
                description='Баг репорт успешно отправлен!',
                color=global_color
            )
        else:
            if usr_block:
                embed = hikari.Embed(
                    description='Вы заблокированы!',
                    color=error_color
                )
            if srv_block:
                embed = hikari.Embed(
                    description='Этот сервер заблокированы!',
                    color=error_color
                )
        await ctx.respond(embed)


@functions.command("support_me", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def support_me(ctx: lightbulb.Context):
    desc = ""
    link = 'https://www.donationalerts.com/r/mrdan0089'
    desc += f"\n**Ссылка на мой DonationAlerts:** **{link}**"
    crypt = functions.Crypt()
    key = crypt.encrypt(functions.premium_code_key, f"{ctx.guild_id}.{ctx.get_guild().owner_id}.{ctx.author.id}.{ctx.author.username}")
    desc += f"\nВставьте в сообщение это: ```\nserver:{key}\n``` \n*Этот текст имеет информацию об сервере на котором была выполнена команда*"
    desc += "\n**Есть 3 уровня премиума**"
    desc += "\n**1\\.** Самый высокий и доступны все премиум функции"
    desc += "\n**2\\.** Средний и доступно меньше премиум функций"
    desc += "\n**3\\.** Меньше всего премиум функций доступно"
    desc += botinfo.premium_cost
    embed = hikari.Embed(
        description=desc,
        color=botinfo.premium_color
    )
    await ctx.respond(embed)


@lightbulb.option(
    "id", "Айди бага",
    modifier=lightbulb.OptionModifier.CONSUME_REST,
    type=int, required=False
)
@lightbulb.option(
    "action_id", "Что то",
    modifier=lightbulb.OptionModifier.CONSUME_REST,
    type=str, required=False, choices=("delete", "bugs")
)
@lightbulb.command(
    "bugs", "Не важно",
    pass_options=True,
    guilds=botinfo.developer_server
)
@lightbulb.implements(lightbulb.SlashCommand)
async def bugs(ctx: lightbulb.Context, id: int, action_id: str):
    view = None
    if ctx.guild_id in botinfo.developer_server and ctx.author.id == botinfo.developer_id:
        async with sqlite3.connect('../db/database.sqlite') as db:
            sql = await db.cursor()
            embed = hikari.Embed(
                title="Чет случилась",
                description="хз че",
                color=error_color
            )
            if action_id is None or action_id == "bugs":
                if id is None:
                    await sql.execute(
                        """SELECT id, short_desc, user_name
                        FROM bugs
                        """
                    )
                    bug_list = await sql.fetchall()
                    output_list = []
                    if bug_list:
                        for bid, name, user_name in bug_list:
                            output_list.append(f"**{bid}**: `{user_name}` - {name}")
                    embed = hikari.Embed(
                        title="Баги",
                        description="",
                        color=global_color
                    )
                    view = functions.Views.Pages(output_list, ctx, embed, 10, 1, ctx.user.id, show_page_number=False)
                else:
                    await sql.execute(
                        """SELECT guild_id, user_id, user_name, description, short_desc, steps
                        FROM bugs
                        WHERE id = ?
                        """, (id,)
                    )
                    bug = await sql.fetchone()
                    bug_info = ""
                    if bug:
                        bug_info += f"**Сервер:** {bug[0]}\n"
                        bug_info += f"**Айди участника:** {bug[1]}\n"
                        bug_info += f"**Имя участника:** `{bug[2]}`\n"
                        bug_info += f"**Описание:** {bug[3]}\n"
                        bug_info += f"**Короткое описание:** {bug[4]}\n"
                        bug_info += f"**Шаги:** {bug[5]}\n"
                    embed = hikari.Embed(
                        title=f"Баг под айди: {id}",
                        description=bug_info,
                        color=global_color
                    )
            elif action_id == "delete" and id is not None:
                await sql.execute(
                    """SELECT guild_id
                    FROM bugs
                    WHERE id = ?
                    """, (id,)
                )
                bug = await sql.fetchone()
                if bug:
                    await sql.execute(
                        "DELETE FROM bugs WHERE id = ?", (id,)
                    )
                    await db.commit()
                    embed = hikari.Embed(
                        description="Баг удален",
                        color=global_color
                    )
            await db.commit()
        if view is not None:
            await view.generate_list()
            ctx.app.d.miru.start_view(view)
        else:
            await ctx.respond(embed)
    else:
        await ctx.respond("низя")


@lightbulb.option(
    "member_id", "Участник",
    modifier=lightbulb.OptionModifier.CONSUME_REST,
    type=str, required=True
)
@lightbulb.command(
    "unblock_user", "Не важно",
    pass_options=True,
    guilds=botinfo.developer_server
)
@lightbulb.implements(lightbulb.SlashCommand)
async def unblock_user(ctx: lightbulb.Context, member_id: str):
    if ctx.guild_id in botinfo.developer_server and ctx.author.id == botinfo.developer_id:
        member_id = int(member_id)
        async with sqlite3.connect('../db/database.sqlite') as db:
            sql = await db.cursor()
            await sql.execute(
                """SELECT type FROM block_users WHERE member_id = ?""",
                (member_id, )
            )
            _type = await sql.fetchone()
            if _type:
                await sql.execute(
                    "DELETE FROM block_users WHERE member_id = ?",
                    (member_id, )
                )
            await db.commit()
            await ctx.respond("Пользователь разблокирован")
    else:
        await ctx.respond("низя")


@lightbulb.option(
    "member_id", "Участник",
    modifier=lightbulb.OptionModifier.CONSUME_REST,
    type=str, required=True
)
@lightbulb.option(
    "ban_type", "тип",
    modifier=lightbulb.OptionModifier.CONSUME_REST,
    type=str, required=True
)
@lightbulb.command(
    "block_user", "Не важно",
    pass_options=True,
    guilds=botinfo.developer_server
)
@lightbulb.implements(lightbulb.SlashCommand)
async def block_user(ctx: lightbulb.Context, member_id: str, ban_type: str):
    if ctx.guild_id in botinfo.developer_server and ctx.author.id == botinfo.developer_id:
        member_id = int(member_id)
        async with sqlite3.connect('../db/database.sqlite') as db:
            sql = await db.cursor()
            await sql.execute(
                """SELECT type FROM block_users WHERE member_id = ?""",
                (member_id, )
            )
            _type = await sql.fetchone()
            if _type:
                await sql.execute(
                    "UPDATE block_users SET member_id = ? AND type = ? WHERE member_id = ?",
                    (member_id, ban_type, member_id)
                )
            else:
                await sql.execute(
                    "INSERT INTO block_users (member_id, type) VALUES (?, ?)",
                    (member_id, ban_type)
                )
            await db.commit()
            await ctx.respond("Пользователь заблокирован")
    else:
        await ctx.respond("низя")


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(bot_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(bot_plugin)
