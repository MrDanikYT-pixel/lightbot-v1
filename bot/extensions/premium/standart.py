# by mrdan__(476046299691745300)
# oficial server: https://discord.gg/2e5SMn73Hw
import hikari
import lightbulb
import aiosqlite as sqlite3
import info as botinfo
from info import error_color
from info import premium_color as global_color
from functions import async_createdb
import functions
import asyncio


bot_plugin = lightbulb.Plugin(
    "Инструменты",
    f"Сделал {botinfo.developer}"
)

aiosqlite = sqlite3
CHOICES = botinfo.CHOICES
token_regex = botinfo.regex["token"]

notvip = hikari.Embed(title="Ошибка!", description="Ваш сервер не имеет уровень премиума `{}`", color=error_color)


def administrator_command(func):
    func = lightbulb.app_command_permissions(hikari.Permissions.ADMINISTRATOR)(func)
    return func


def administrator_sub_command(func):
    func = lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))(func)
    return func


def nvrespond(ctx: lightbulb.Context, lvl: int):
    notvip.description = notvip.description.format(str(lvl))
    return ctx.respond(notvip)


@bot_plugin.listener(hikari.MessageCreateEvent)
async def message_create_event(event: hikari.MessageCreateEvent):
    if isinstance(event, hikari.DMMessageCreateEvent):
        return
    vl = (await functions.server_info(None, guild_id=event.message.guild_id))["level"]
    if vl > 2 or vl == 0:
        return
    if event.message.author.is_bot:
        return
    guild_id = event.message.guild_id
    delete = False
    async with sqlite3.connect(f'../db/{guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(guild_id, sql, db)
        delete_pin_message = await functions.Setting(db, "delete_pin_message").get("0")
        delete_thread_message = await functions.Setting(db, "delete_thread_message").get("0")
    if event.message.type == 18 and not event.message.author.is_system:
        if delete_thread_message[0] == "1":
            delete = True
        if delete:
            try:
                await event.message.delete()
            except Exception:
                embed = hikari.Embed(
                    description=(f"Не удалось удалить сообщение https://discord.com/channels/{event.message.guild_id}/{event.channel_id}/{event.message_id}\n" +
                                 "У бота должно быть право \"Управление сообщениями\""),
                    color=error_color
                )
                embed.set_footer("Это сообщение будет удалено автоматически через 2 минуты")
                msg = await event.app.rest.create_message(event.channel_id, embed=embed)
                await asyncio.sleep(120)
                try:
                    await msg.delete()
                except Exception:
                    ...

    elif event.message.type == hikari.MessageType.CHANNEL_PINNED_MESSAGE and not event.message.author.is_system:
        delete = False
        if delete_pin_message[0] == "1":
            delete = True
        if delete:
            try:
                await event.message.delete()
            except Exception:
                embed = hikari.Embed(
                    description=(f"Не удалось удалить сообщение https://discord.com/channels/{event.message.guild_id}/{event.channel_id}/{event.message_id}\n" +
                                 "У бота должно быть право \"Управление сообщениями\""),
                    color=error_color
                )
                embed.set_footer("Это сообщение будет удалено автоматически через 2 минуты")
                msg = await event.app.rest.create_message(event.channel_id, embed=embed)
                await asyncio.sleep(120)
                try:
                    await msg.delete()
                except Exception:
                    ...


@bot_plugin.listener(hikari.GuildReactionAddEvent)
async def reaction_add_event(event: hikari.GuildReactionAddEvent):
    vl = (await functions.server_info(None, guild_id=event.guild_id))["level"]
    if vl > 1 or vl == 0:
        return
    roles = event.member.role_ids
    channel = event.channel_id
    exists = False
    channel_roles = []
    async with sqlite3.connect(f'../db/{event.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(event.guild_id, sql, db)
        bchannels = functions.BlobVars(db, "channels")
        channels: dict = await bchannels.get({})
        if channel in channels:
            exists = True
            channel_roles = channels[channel]
    if exists:
        if set(roles).intersection(channel_roles):
            ...
        else:
            await asyncio.sleep(0.25)
            try:
                await event.app.rest.delete_reaction(event.channel_id, event.message_id, event.member.user, event.emoji_name, event.emoji_id)
            except Exception:
                try:
                    await event.app.rest.delete_reaction(event.channel_id, event.message_id, event.member.user, event.emoji_name)
                except Exception:
                    embed = hikari.Embed(
                        description=(f"Не удалось удалить реакцию у сообщения https://discord.com/channels/{event.guild_id}/{event.channel_id}/{event.message_id}\n" +
                                     "У бота должно быть право \"Управление сообщениями\""),
                        color=error_color
                    )
                    embed.set_footer("Это сообщение будет удалено автоматически через 2 минуты")
                    msg = await event.app.rest.create_message(channel, embed=embed)
                    await asyncio.sleep(120)
                    try:
                        await msg.delete()
                    except Exception:
                        ...


allowed_channels = [hikari.ChannelType.GUILD_TEXT, hikari.ChannelType.GUILD_NEWS]


@administrator_command
@functions.command("del_thread_create_msg", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def thread_create_msg(ctx: lightbulb.Context, mode: str):
    vl = (await functions.server_info(ctx))["level"]
    if vl > 2 or vl == 0:
        await nvrespond(ctx, 2)
        return
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        if CHOICES["switch"].index(mode) == 0:
            mode = "1"
        else:
            mode = "0"
        delete_thread_message = functions.Setting(db, "delete_thread_message")
        wmode = await delete_thread_message.get("0")
        if wmode == mode:
            embed = hikari.Embed(
                description=f"Удаление сообщений \"`ник` создал ветку\" уже {'включено' if mode == '1' else 'выключено'}",
                color=error_color
            )
        else:
            await delete_thread_message.set(value=mode)
            await db.commit()
            embed = hikari.Embed(
                description=f"Удаление сообщений \"`ник` создал ветку\" {'включено' if mode == '1' else 'выключено'}",
                color=global_color
            )
    await ctx.respond(embed)


@administrator_command
@functions.command("del_pin_add_msg", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def del_pin_add_msg(ctx: lightbulb.Context, mode: str):
    vl = (await functions.server_info(ctx))["level"]
    if vl > 2 or vl == 0:
        await nvrespond(ctx, 2)
        return
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        if CHOICES["switch"].index(mode) == 0:
            mode = "1"
        else:
            mode = "0"
        delete_thread_message = functions.Setting(db, "delete_pin_message")
        wmode = await delete_thread_message.get("0")
        if wmode == mode:
            embed = hikari.Embed(
                description=f"Удаление сообщений \"`ник` закрепил сообщение\" уже {'включено' if mode == '1' else 'выключено'}",
                color=error_color
            )
        else:
            await delete_thread_message.set(value=mode)
            await db.commit()
            embed = hikari.Embed(
                description=f"Удаление сообщений \"`ник` закрепил сообщение\" {'включено' if mode == '1' else 'выключено'}",
                color=global_color
            )
    await ctx.respond(embed)


@administrator_command
@functions.command("block_reactions", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def block_reactions(ctx: lightbulb.Context) -> None:
    ...


@block_reactions.child
@administrator_command
@functions.command("block_reactions add_channel", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def block_reactions_add_channel(ctx: lightbulb.Context, channel: hikari.TextableGuildChannel):
    vl = (await functions.server_info(ctx))["level"]
    if vl > 1 or vl == 0:
        await nvrespond(ctx, 1)
        return
    if channel.type not in allowed_channels:
        embed = hikari.Embed(
            description="Выберите текстовый канал!",
            color=error_color
        )
        await ctx.respond(embed)
        return
    cid = int(channel.id)
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        bchannels = functions.BlobVars(db, "channels")
        channels: dict = await bchannels.get({})
        if cid in channels:
            embed = hikari.Embed(
                description="Этот канал уже добавлен!",
                color=error_color
            )
        else:
            embed = hikari.Embed(
                description=f"Канал {channel.mention} добавлен в список",
                color=global_color
            )
            channels[cid] = []
            await bchannels.set(channels)
            await db.commit()
    await ctx.respond(embed)


@block_reactions.child
@administrator_command
@functions.command("block_reactions rem_channel", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def block_reactions_rem_channel(ctx: lightbulb.Context, channel: hikari.TextableGuildChannel):
    vl = (await functions.server_info(ctx))["level"]
    if vl > 1 or vl == 0:
        await nvrespond(ctx, 1)
        return
    if channel.type not in allowed_channels:
        embed = hikari.Embed(
            description="Выберите текстовый канал!",
            color=error_color
        )
        await ctx.respond(embed)
        return
    cid = int(channel.id)
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        bchannels = functions.BlobVars(db, "channels")
        channels: dict = await bchannels.get({})
        if cid not in channels:
            embed = hikari.Embed(
                description="Этого канала нету в списке!",
                color=error_color
            )
        else:
            embed = hikari.Embed(
                description=f"Канал {channel.mention} удален из списка",
                color=global_color
            )
            del channels[cid]
            await bchannels.set(channels)
            await db.commit()
    await ctx.respond(embed)


@block_reactions.child
@administrator_command
@functions.command("block_reactions channel_list", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def block_reactions_channel_list(ctx: lightbulb.Context, page: int):
    vl = (await functions.server_info(ctx))["level"]
    if vl > 1 or vl == 0:
        await nvrespond(ctx, 1)
        return
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        bchannels = functions.BlobVars(db, "channels")
        channels: dict = await bchannels.get({})
        elements = []
        for index in range(len(channels)):
            elements.append(f"<#{list(channels.keys())[index]}>")
        embed = hikari.Embed(
            title="Список каналов",
            description="",
            color=global_color
        )
        view = functions.Views.Pages(elements, ctx, embed, 10, page, ctx.author.id, timeout=60)
    if view is not None:
        await view.generate_list()
        ctx.app.d.miru.start_view(view)


@block_reactions.child
@administrator_command
@functions.command("block_reactions add_role", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def block_reactions_add_role(ctx: lightbulb.Context, channel: hikari.TextableGuildChannel, role: hikari.Role):
    vl = (await functions.server_info(ctx))["level"]
    if vl > 1 or vl == 0:
        await nvrespond(ctx, 1)
        return
    if channel.type not in allowed_channels:
        embed = hikari.Embed(
            description="Выберите текстовый канал!",
            color=error_color
        )
        await ctx.respond(embed)
        return
    cid = int(channel.id)
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        bchannels = functions.BlobVars(db, "channels")
        channels: dict = await bchannels.get({})
        if cid not in channels:
            embed = hikari.Embed(
                description="Канал не добавлен",
                color=error_color
            )
        else:
            roles = list(channels[cid])
            if role.id in roles:
                embed = hikari.Embed(
                    description=f"Роль {role.mention} в канале {channel.mention} уже разрешена",
                    color=error_color
                )
            else:
                embed = hikari.Embed(
                    description=f"Роль {role.mention} в канале {channel.mention} разрешена",
                    color=global_color
                )
                roles.append(role.id)
                channels[cid] = roles
                await bchannels.set(channels)
                await db.commit()
    await ctx.respond(embed)


@block_reactions.child
@administrator_command
@functions.command("block_reactions rem_role", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def block_reactions_rem_role(ctx: lightbulb.Context, channel: hikari.TextableGuildChannel, role: hikari.Role):
    vl = (await functions.server_info(ctx))["level"]
    if vl > 1 or vl == 0:
        await nvrespond(ctx, 1)
        return
    if channel.type not in allowed_channels:
        embed = hikari.Embed(
            description="Выберите текстовый канал!",
            color=error_color
        )
        await ctx.respond(embed)
        return
    cid = int(channel.id)
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        bchannels = functions.BlobVars(db, "channels")
        channels: dict = await bchannels.get({})
        if cid not in channels:
            embed = hikari.Embed(
                description="Канал не добавлен",
                color=error_color
            )
        else:
            roles = list(channels[cid])
            if role.id not in roles:
                embed = hikari.Embed(
                    description=f"Роль {role.mention} в канале {channel.mention} не разрешена",
                    color=error_color
                )
            else:
                embed = hikari.Embed(
                    description=f"Роль {role.mention} в канале {channel.mention} больше не разрешена",
                    color=global_color
                )
                roles.remove(role.id)
                channels[cid] = roles
                await bchannels.set(channels)
                await db.commit()
    await ctx.respond(embed)


@block_reactions.child
@administrator_command
@functions.command("block_reactions role_list", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def block_reactions_role_list(ctx: lightbulb.Context, channel: hikari.TextableGuildChannel, page: int):
    vl = (await functions.server_info(ctx))["level"]
    if vl > 1 or vl == 0:
        await nvrespond(ctx, 1)
        return
    cid = channel.id
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        bchannels = functions.BlobVars(db, "channels")
        channels: dict = await bchannels.get({})
        elements = []
        if cid not in channels:
            embed = hikari.Embed(
                description="Канал не добавлен",
                color=error_color
            )
            await ctx.respond(embed)
        else:
            roles = list(channels[cid])
            for index in range(len(roles)):
                elements.append(f"<@&{roles[index]}>")
            embed = hikari.Embed(
                title="Список разрешенных ролей в канале",
                description="",
                color=global_color
            )
            view = functions.Views.Pages(elements, ctx, embed, 10, page, ctx.author.id, timeout=60)
    if view is not None:
        await view.generate_list()
        ctx.app.d.miru.start_view(view)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(bot_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(bot_plugin)
