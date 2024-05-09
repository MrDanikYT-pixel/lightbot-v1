# by mrdan__(476046299691745300)
# oficial server: https://discord.gg/2e5SMn73Hw
import hikari
import lightbulb
import aiosqlite as sqlite3
import info as botinfo
from info import global_color, error_color
from functions import async_createdb
import generator
import functions
bot_plugin = lightbulb.Plugin(
    "Настройки бота",
    f"Сделал {botinfo.developer}"
)

CHOICES = botinfo.CHOICES


def administrator_command(func):
    func = lightbulb.app_command_permissions(hikari.Permissions.ADMINISTRATOR)(func)
    return func


def administrator_sub_command(func):
    func = lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))(func)
    return func


@administrator_command
@functions.command("switch", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def switch(ctx: lightbulb.Context) -> None:
    ...


@switch.child
@administrator_command
@functions.command("switch generator_mode", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def generator_mode(ctx: lightbulb.Context, mode: str) -> None:
    mode = generator.modes[generator.modes_desc.index(mode)]
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        error = False
        if mode is None:
            error = True
        elif mode not in generator.modes:
            error = True
        key = "generator_mode"
        settings = functions.Setting(db, key)
        m_mode = await settings.get("")
        if not error:
            if not m_mode[0] == mode:
                await settings.set(value=mode)
                await db.commit()
                embed = hikari.Embed(
                    description=f"Теперь режим генератора `{mode}`",
                    color=global_color
                )
            else:
                embed = hikari.Embed(
                    description="Вы уже установили этот режим",
                    color=error_color
                )
        else:
            embed = hikari.Embed(
                title="Инфо",
                description=(
                    "Режим генерации ответа при упоминании бота или при получении случайного сообщения. \n" +
                    "\n**Доступные режимы:**" +
                    "\nRandom - случайные слова." +
                    "\nGenerate - из всех сообщений в чате." +
                    "\noff - Отключить"
                ),
                color=0x01FF10
            )
        await ctx.respond(embed, flags=64)


@switch.child
@administrator_command
@functions.command("switch random_msgs", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def switch_random_msgs(ctx: lightbulb.Context, mode: str) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        error = False
        if mode is None:
            error = True
        if CHOICES["switch"].index(mode) == 0:
            mode = True
        else:
            mode = False
        settings = functions.Setting(db, "random_msgs")
        m_mode = await settings.get("")
        if not error:
            if not m_mode[0] == str(mode):
                await settings.set(value=str(mode))
                await db.commit()
                if mode:
                    embed = hikari.Embed(
                        description="Случайные сообщения включены!",
                        color=global_color
                    )
                else:
                    embed = hikari.Embed(
                        description="Случайные сообщения выключены!",
                        color=global_color
                    )
            else:
                embed = hikari.Embed(
                    description="У вас уже стоит такая настройка",
                    color=error_color
                )
        else:
            embed = hikari.Embed(
                title="Инфо",
                description=(
                    '`Включить` - чтобы включить случайные сообщения\n' +
                    "`Выключить` - чтобы выключить случайные сообщения"
                ),
                color=0x01FF10
            )
        await ctx.respond(embed)


@switch.child
@administrator_command
@functions.command("switch mention_to_generate", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def switch_mention_to_generate(ctx: lightbulb.Context, mode: str) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        error = False
        if mode is None:
            error = True
        if CHOICES["switch"].index(mode) == 0:
            mode = True
        else:
            mode = False
        settings = functions.Setting(db, "mention_to_generate")
        m_mode = await settings.get("")
        if not error:
            if not m_mode[0] == str(mode):
                await settings.set(value=str(mode))
                await db.commit()
                if mode:
                    embed = hikari.Embed(
                        description="Теперь при упоминании LightBot-а ничего не будет происходить!",
                        color=global_color
                    )
                else:
                    embed = hikari.Embed(
                        description="Теперь при упоминании LightBot-а он будет генерировать",
                        color=global_color
                    )
            else:
                embed = hikari.Embed(
                    description="У вас уже стоит такая настройка",
                    color=error_color
                )
        else:
            embed = hikari.Embed(
                title="Инфо",
                description=(
                    '`Включить` - чтобы включить генерацию при упоминании\n' +
                    "`Выключить` - чтобы выключить"
                ),
                color=0x01FF10
            )
        await ctx.respond(embed)


@switch.child
@administrator_command
@functions.command("switch read_msg_content", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def read_msg_content(
            ctx: lightbulb.Context, mode: str
        ) -> None:
    selected_value = ""

    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        error = False
        if mode is None:
            error = True
        if mode not in CHOICES["switch"]:
            mode = None
        elif CHOICES["switch"].index(mode) == 0:
            mode = True
        else:
            mode = False
        settings = functions.Setting(db, "read_content")
        m_mode = await settings.get("")
        if not error:
            if mode is not None:
                if (mode or not m_mode[0] == str(mode)):
                    await settings.set(value=str(mode))
                    if not mode:
                        embed = hikari.Embed(
                            description="Теперь бот не записывает сообщения из чата!",
                            color=global_color
                        )
                        await db.commit()
                    else:
                        title = "Как долго контент сообщения может хранится в базе данных, прежде чем будет удаленным?"
                        delete_after = functions.Setting(db, "delete_after")
                        embed = hikari.Embed(
                            title=title,
                            description="**Если ничего не выбрать автоматически установится 30 дней**",
                            color=global_color
                        )
                        view = functions.Views.ReadMsgContent(timeout=120, autodefer=True)
                        msg = await ctx.respond(embed, components=view)
                        ctx.app.d.miru.start_view(view)
                        await view.wait()
                        values = None
                        if view.select is not None:
                            values = view.select.values[0]
                        selected_value = values or "30"
                        view.clear_items()
                        await delete_after.set(value=selected_value)
                        if selected_value != "0":
                            embed = hikari.Embed(
                                title=title,
                                description=(f"### Выбрано: \n**Весь контент сообщений которым больше чем {selected_value} дн. будет удалятся**\n\n" +
                                             "В течении следующих 6 часов будет удален контент сообщений"),
                                color=global_color
                            )
                        else:
                            embed = hikari.Embed(
                                title=title,
                                description="### Выбрано: \n**Контент сообщения никогда не будет удалятся**",
                                color=global_color
                            )
                        await msg.edit(embed, components=view)
                        await delete_after.set(value=selected_value)
                        n_setting = functions.Setting(db, "read_system")
                        await n_setting.set(value='1')
                        await db.commit()

                        embed = hikari.Embed(
                            description="Теперь бот записывает **все** сообщения из чата!",
                            color=global_color
                        )
                else:
                    embed = hikari.Embed(
                        description="У вас уже стоит такая настройка",
                        color=error_color
                    )
            else:
                read_content = (await settings.get('False'))[0]
                if read_content != 'False':
                    delete_after = (await functions.Setting(db, "delete_after").get('0'))[0]
                    if delete_after == "0":
                        delete_after = "Никогда"
                    else:
                        delete_after = f"{delete_after} дней"
                else:
                    delete_after = None
                dl = f"**Через сколько удалять контент сообщения в боте:** {delete_after}\n" if delete_after is not None else ""
                text = f"{dl}**Читание контента сообщений:** {'Разрешено' if read_content != 'False' else 'Запрещенно'}"
                embed = hikari.Embed(
                    title="Инфо",
                    description=text,
                    color=global_color
                )
        else:
            embed = hikari.Embed(
                title="Инфо",
                description=(
                    '`Включить` - чтобы включить запись сообщений\n' +
                    "`Выключить` - чтобы выключить запись сообщений"
                ),
                color=0x01FF10
            )
        await ctx.respond(embed)


@administrator_command
@functions.command("delete_from_db", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def delete_from_db(ctx: lightbulb.Context, message_id: str) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        if "/" in message_id:
            url = message_id.split("/")
            message_id = int(url[-1])
        elif message_id.isdigit():
            message_id = int(message_id)
        else:
            embed = hikari.Embed(
                description="В аргументе не найдена ссылка или айди сообщения",
                color=error_color
            )
            await ctx.respond(embed)
            return
        await sql.execute(
            "SELECT content FROM messages WHERE server_id=? AND message_id = ?",
            (ctx.guild_id, message_id)
        )
        if await sql.fetchone() is not None:
            await sql.execute(
                "DELETE FROM messages WHERE server_id=? AND message_id = ?",
                (ctx.guild_id, message_id)
            )
            await db.commit()
            embed = hikari.Embed(
                description="Это сообщение удалено из базы данных",
                color=global_color
            )
        else:
            embed = hikari.Embed(
                description="Этого сообщения в базе данных нет",
                color=error_color
            )
        await ctx.respond(embed, flags=64)


@administrator_command
@functions.command("clear_db", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def clear_db(ctx: lightbulb.Context, member: hikari.Member) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        try:
            if member is not None:
                await sql.execute(
                    "DELETE FROM messages WHERE server_id=? AND member_id = ?",
                    (ctx.guild_id, member.id)
                )
                await db.commit()
                embed = hikari.Embed(
                    description=f"Все сообщения от <@{member.id}> очищенны!",
                    color=global_color
                )
            else:
                await sql.execute(
                    "DELETE FROM messages WHERE server_id=?", (ctx.guild_id,)
                )
                await db.commit()
                embed = hikari.Embed(
                    description="Все сообщения из вашей базы данных удаленны!",
                    color=global_color
                )
            await ctx.respond(embed, flags=64)
        except sqlite3.Error:
            embed = hikari.Embed(
                description="Произошла ошибка во время запроса к базе данных.",
                color=error_color
            )
            await ctx.respond(embed, flags=64)


@administrator_command
@lightbulb.command("allowed_channels", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def allowed_channels(ctx: lightbulb.Context) -> None:
    pass


@allowed_channels.child
@functions.command("allowed_channels list", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def allowed_channels_list(
            ctx: lightbulb.Context, page: int
        ) -> None:
    if page is None:
        page = 1
    view = None
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        try:
            await sql.execute(
                "SELECT channel_id FROM channels WHERE server_id = ?",
                (ctx.guild_id, ))
            channels = await sql.fetchall()
            elements = []
            if channels is not None:
                for channel in channels:
                    elements.append(f"<#{int(channel[0])}>({int(channel[0])})")
            embed = hikari.Embed(
                title="Белый список каналов",
                description="",
                color=global_color
            )
            embed.set_footer("Каналы где разрешено боту читать сообщения.")
            view = functions.Views.Pages(elements, ctx, embed, 10, page, ctx.author.id, timeout=60)
        except sqlite3.Error:
            embed = hikari.Embed(
                description="Произошла ошибка во время запроса к базе данных.",
                color=error_color
            )
            await ctx.respond(embed)
    if view is not None:
        await view.generate_list()
        ctx.app.d.miru.start_view(view)


@allowed_channels.child
@functions.command("allowed_channels add", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def add_allowed_channel(
            ctx: lightbulb.Context,
            channel: hikari.TextableGuildChannel
        ) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        channel = ctx.get_guild().get_channel(ctx.options.channel.id)
        await sql.execute(
            "SELECT channel_id FROM channels WHERE server_id = ?",
            (ctx.guild_id, ))
        channels = await sql.fetchall()
        channel_ids = [c[0] for c in channels]
        if not channel:
            embed = hikari.Embed(
                description="На сервере нет такого канала.",
                color=error_color
            )
            embed.set_footer("Укажите канал или его ID!")
            await ctx.respond(embed, flags=64)
            return
        try:
            if channel.id not in channel_ids:
                await sql.execute("""
                INSERT INTO channels (channel_id, server_id) VALUES (?, ?)
                """, (channel.id, ctx.guild_id))
                await db.commit()
                embed = hikari.Embed(
                    description=f"""
                    Канал <#{channel.id}> добавлен в белый список.
                    Убедитесь что у бота есть права отправлять и читать сообщения!
                    """,
                    color=global_color
                )
                await ctx.respond(embed, flags=64)
            else:
                embed = hikari.Embed(
                    description="Этот канал и так доступный",
                    color=error_color
                )
                await ctx.respond(embed, flags=64)
        except sqlite3.Error:
            embed = hikari.Embed(
                description="Произошла ошибка во время запроса к базе данных",
                color=error_color
            )
            await ctx.respond(embed, flags=64)


@allowed_channels.child
@functions.command("allowed_channels remove", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def rem_allowed_channel(
            ctx: lightbulb.Context,
            channel: hikari.TextableGuildChannel
        ) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        channel = ctx.get_guild().get_channel(ctx.options.channel.id)
        if not channel:
            embed = hikari.Embed(
                description="На сервере нет такого канала.",
                color=error_color
            )
            embed.set_footer("Укажите канал или его ID!")
            await ctx.respond(embed, flags=64)
        else:
            try:
                await sql.execute(
                    "SELECT channel_id FROM channels WHERE server_id = ?",
                    (ctx.guild_id, ))
                channels = await sql.fetchall()
                channel_ids = [c[0] for c in channels]

                if channel.id in channel_ids:
                    await sql.execute("""
                    DELETE FROM channels
                    WHERE channel_id = ? and server_id = ?;
                    """, (channel.id, ctx.guild_id))
                    await db.commit()
                    embed = hikari.Embed(
                        description=f"""
                        Канал <#{channel.id}> удален из белого списка.
                        """,
                        color=global_color
                    )
                    await ctx.respond(embed, flags=64)
                else:
                    embed = hikari.Embed(
                        description="Этот канал и так не доступный",
                        color=error_color
                    )
                    await ctx.respond(embed, flags=64)
            except sqlite3.Error:
                embed = hikari.Embed(
                    description="Произошла ошибка во время запроса к базе данных.",
                    color=error_color
                )
                await ctx.respond(embed, flags=64)


@allowed_channels.child
@functions.command("allowed_channels clear", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def clear_allowed_channels(
            ctx: lightbulb.Context
        ) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        try:
            await sql.execute("""
            DELETE FROM channels
            WHERE server_id = ?;
            """, (ctx.guild_id,))
            await db.commit()
            embed = hikari.Embed(
                description="""
                Белый список удалён! Теперь бот читает во всех доступных каналах.
                """,
                color=global_color
            )
            await ctx.respond(embed, flags=64)
        except sqlite3.Error:
            embed = hikari.Embed(
                description="Произошла ошибка во время запроса к базе данных.",
                color=error_color
            )
            await ctx.respond(embed, flags=64)


###################################


@administrator_command
@functions.command("ignored_members", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def ignored_members(ctx: lightbulb.Context) -> None:
    pass


@ignored_members.child
@functions.command("ignored_members list", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def ignored_members_list(
            ctx: lightbulb.Context, page: int
        ) -> None:
    if page is None:
        page = 1
    view = None
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        try:
            await sql.execute(
                "SELECT member_id FROM ignore_members WHERE server_id = ? ORDER BY id DESC",
                (ctx.guild_id, ))
            members = await sql.fetchall()
            if members is None:
                members = []
            elements = []
            for member in members:
                elements.append(f"<@{int(member[0])}>({int(member[0])})\n")
            embed = hikari.Embed(
                title="Черный список участников.",
                description="",
                color=global_color
            )
            view = functions.Views.Pages(elements, ctx, embed, 10, page, ctx.author.id, timeout=60)
        except sqlite3.Error:
            embed = hikari.Embed(
                description="Произошла ошибка во время запроса к базе данных.",
                color=error_color
            )
            await ctx.respond(embed)
    if view is not None:
        await view.generate_list()
        ctx.app.d.miru.start_view(view)


@ignored_members.child
@functions.command("ignored_members add", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def ignore_member(
            ctx: lightbulb.Context,
            member: hikari.Member,
            reason: str
        ) -> None:
    if not reason:
        reason = "Нет причины"
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        await sql.execute(
            "SELECT member_id FROM ignore_members WHERE server_id = ?",
            (ctx.guild_id, ))
        members = await sql.fetchall()
        member_ids = [c[0] for c in members]
        if not member:
            embed = hikari.Embed(
                description="На сервере нет такого участника.",
                color=error_color
            )
            embed.set_footer("Укажите участника или его ID!")
            await ctx.respond(embed, flags=64)
            return
        try:
            if member.id not in member_ids:
                await sql.execute("""
                INSERT INTO ignore_members (member_id, server_id, reason) VALUES (?, ?, ?)
                """, (member.id, ctx.guild_id, reason))
                await db.commit()
                embed = hikari.Embed(
                    description=f"Участник {member.username} добавлен в черный список.",
                    color=global_color
                )
                await ctx.respond(embed, flags=64)
            else:
                embed = hikari.Embed(
                    description="Этот участник уже в черном списке.",
                    color=error_color
                )
                await ctx.respond(embed, flags=64)
        except sqlite3.Error:
            embed = hikari.Embed(
                description="Произошла ошибка во время запроса к базе данных",
                color=error_color
            )
            await ctx.respond(embed, flags=64)


@ignored_members.child
@functions.command("ignored_members remove", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def not_ignore_member(
            ctx: lightbulb.Context,
            member: hikari.Member
        ) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        if not member:
            embed = hikari.Embed(
                description="На сервере нет такого участника.",
                color=error_color
            )
            embed.set_footer("Укажите участника или его ID!")
            await ctx.respond(embed, flags=64)
        else:
            try:
                await sql.execute(
                    "SELECT member_id FROM ignore_members WHERE server_id = ?",
                    (ctx.guild_id, ))
                members = await sql.fetchall()
                member_ids = [c[0] for c in members]

                if member.id in member_ids:
                    await sql.execute("""
                    DELETE FROM ignore_members
                    WHERE member_id = ? and server_id = ?;
                    """, (member.id, ctx.guild_id))
                    await db.commit()
                    embed = hikari.Embed(
                        description=f"""
                        Участник {member.username} удален из черного списка.
                        """,
                        color=global_color
                    )
                    await ctx.respond(embed, flags=64)
                else:
                    embed = hikari.Embed(
                        description="Этот участник не в черном списке",
                        color=error_color
                    )
                    await ctx.respond(embed, flags=64)
            except sqlite3.Error:
                embed = hikari.Embed(
                    title="Ошибка",
                    description="Произошла ошибка во время запроса к базе данных.",
                    color=error_color
                )
                await ctx.respond(embed, flags=64)


@ignored_members.child
@functions.command("ignored_members check", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def ignored_member(
            ctx: lightbulb.Context,
            member: hikari.Member
        ) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        try:
            await sql.execute(
                "SELECT member_id, reason FROM ignore_members WHERE server_id = ? AND member_id = ?",
                (ctx.guild_id, member.id))
            memberr = await sql.fetchone()
            if memberr:
                embed = hikari.Embed(
                    title="Да",
                    description=(
                        f"Участник {member.user.mention} в черном списке" +
                        f"\nПричина: {memberr[1]}"
                    ),
                    color=global_color
                )
            else:
                embed = hikari.Embed(
                    title="Нет",
                    description=f"Участник {member.user.mention} не в черном списке",
                    color=global_color
                )
        except sqlite3.Error:
            embed = hikari.Embed(
                description="Произошла ошибка во время запроса к базе данных.",
                color=error_color
            )
        await ctx.respond(embed)


@ignored_members.child
@functions.command("ignored_members clear", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def clear_ignored_members(
            ctx: lightbulb.Context
        ) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        try:
            await sql.execute("""
            DELETE FROM ignore_members
            WHERE server_id = ?;
            """, (ctx.guild_id,))
            await db.commit()
            embed = hikari.Embed(
                description="""
                Черный список удалён! Теперь бот читает сообщения всех участников.
                """,
                color=global_color
            )
            await ctx.respond(embed, flags=64)
        except sqlite3.Error:
            embed = hikari.Embed(
                description="Произошла ошибка во время запроса к базе данных.",
                color=error_color
            )
            await ctx.respond(embed, flags=64)


#########################################


@functions.command("version_info", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def version_info(
        ctx: lightbulb.Context,
        version: str
        ) -> None:
    version = ctx.options.version
    last_changes = ''
    if version:
        last_changes, versions = botinfo.get_version_info(version)
    else:
        last_changes, versions = botinfo.get_version_info()
        version = botinfo.current
    if last_changes:
        embed = hikari.Embed(
            title=f"Информация о версии `{version}`",
            description=last_changes,
            color=global_color
        )
        vers = []
        for x in range(len(versions)):
            if x > len(versions)-8:
                vers.append(f"`{versions[x]}`")
        if versions:
            vers.reverse()
            embed.add_field(
                name="Последние версии",
                value=', '.join(vers)
            )
    else:
        embed = hikari.Embed(
            description=f"Не удалось получить данные о версии `{version}`",
            color=error_color
        )
    await ctx.respond(embed)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(bot_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(bot_plugin)
