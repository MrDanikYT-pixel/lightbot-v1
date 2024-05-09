# by mrdan__(476046299691745300)
# oficial server: https://discord.gg/2e5SMn73Hw
import asyncio
import hikari
import lightbulb
import aiosqlite as sqlite3
import info as botinfo
from datetime import datetime
from info import error_color, global_color
from functions import async_createdb
import functions
from functions import gen
import random
import generator
bot_plugin = lightbulb.Plugin(
    "Инструменты",
    f"Сделал {botinfo.developer}"
)

aiosqlite = sqlite3
token_regex = botinfo.regex["token"]


@functions.command("generate", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def generate(
        ctx: lightbulb.Context,
        text: str,
        minp: int, maxp: int,
        maxw: int, minw: int,
        start_word: str,
        msgs_min_len: int,
        msgs_limit: int,
        version: str
        ) -> None:
    if minp is None:
        minp = 2
    if maxp is None:
        maxp = 14
    if minw is None:
        minw = 3
    if maxw is None:
        maxw = 9
    if msgs_min_len is None:
        msgs_min_len = 5
    if msgs_limit is None:
        msgs_limit = None
    if version == "Auto":
        version == "auto"
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        r_mode = (await functions.Setting(db, "read_content").get('False'))[0]
        if r_mode != 'False':
            embed = hikari.Embed(
                description="Что то случилось",
                color=error_color
            )
            if text is None:
                await gen(sql, ctx, msgs_limit, lenght=msgs_min_len)
                messages = await sql.fetchall()
                if len(messages) >= 29:
                    combined_message = await generator.async_combine_common_words(" ||__|| ".join([message[0] for message in messages]), version=version, return_version=True, minp=minp, maxp=maxp, minw=minw, maxw=maxw, start_word=start_word)
                    if combined_message:
                        embed = hikari.Embed(
                            title="Генерация",
                            description=combined_message[0],
                            color=global_color
                        )
                        embed.set_footer(f"Использовано сообщений: {len(messages)} \n{f'Версия генератора: {combined_message[1]}' if isinstance(combined_message, tuple) else ''}")
                else:
                    embed = hikari.Embed(
                        description=f"""
        Я пока не могу генерировать сообщения. В базе данных у меня меньше 30 сообщений.
        У вас {len(messages)} сообщений.
                        """,
                        color=error_color
                    )
            else:
                combined_message = await generator.async_combine_common_words(text, version=version, minp=minp, maxp=maxp, minw=minw, maxw=maxw, start_word=start_word)
                if combined_message:
                    embed = hikari.Embed(
                        title="Генерация",
                        description=combined_message,
                        color=global_color
                    )
        else:
            embed = hikari.Embed(
                description="Читание контента сообщений выключено!",
                color=error_color
            )
            embed.set_footer("Чтобы включить напишите /switch read_msg_content")
    await ctx.respond(embed=embed)


@functions.command("who_say_it", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def who_say_it(
        ctx: lightbulb.Context, time: int
        ) -> None:
    if time is None:
        time = 30
    view = None
    correct_member = "неизвестный"
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        r_mode = (await functions.Setting(db, "read_content").get('False'))[0]
        if r_mode != 'False':
            async def get(len: int = 30):
                await gen(sql, ctx, 5000, "ORDER BY id DESC", False, len, False, select="content, member_id, message_id, channel_id")
                result = await sql.fetchall()
                return result
            result = await get()
            if len(result) < 1:
                result = await get(0)
            if len(result) < 1:
                embed = hikari.Embed(
                    description="На этом сервере нет сообщений!",
                    color=error_color
                )
                await ctx.respond(embed)
            else:
                users = [user[1] for user in result]
                users = list(dict.fromkeys(users))
                _users = []
                for x in users:
                    member = ctx.app.cache.get_member(ctx.guild_id, x)
                    if member is None:
                        for y in result:
                            if y[1] == x:
                                result: list = result
                                result.remove(y)
                        continue
                    _users.append(member)
                users = _users
                if len(users) > 1:
                    orig_result = result
                    result = random.choice(orig_result)
                    correct_member = ctx.app.cache.get_member(ctx.guild_id, result[1])
                    i = 0
                    while correct_member not in users:
                        result = random.choice(orig_result)
                        correct_member = ctx.app.cache.get_member(ctx.guild_id, result[1])
                        i += 1
                        if i >= 10:
                            await ctx.respond(hikari.Embed(
                                description="Попробуйте ещё раз ввести команду",
                                color=error_color
                            ))
                            break
                    if correct_member in users:
                        users.remove(correct_member)
                    choices = random.sample(users, k=min(4, len(users)))
                    correct = random.randint(0, len(choices))
                    choices.insert(correct, correct_member)
                    rslt = result[0]
                    rslt = token_regex.sub("**Токен скрыт**", rslt)
                    output = ""
                    for i, x in enumerate(choices, start=1):
                        x: hikari.Member = x
                        member_name = x.nickname or x.display_name or x.global_name or x.username
                        output += f"**{i}\\.** **{member_name}**\n"
                    embed = hikari.Embed(
                        title="Кто написал это?",
                        description=rslt,
                        color=global_color
                    )
                    embed.add_field("Варианты ответа", output)
                    embed.set_footer(f"Через {time} секунд покажется результат")
                    view = functions.Views.WhoSayIt(choices, correct, timeout=time+10)
                    msg = await ctx.respond(embed, flags=hikari.MessageFlag.LOADING, components=view)
                    ctx.app.d.miru.start_view(view)
                else:
                    embed = hikari.Embed(
                        description="Слишком мало участников писало в последнее время.",
                        color=error_color
                    )
                    await ctx.respond(embed)
    if view is not None:
        await asyncio.sleep(time)
        await view.vstop()
        if isinstance(correct_member, hikari.Member):
            member_name = correct_member.nickname or correct_member.display_name or correct_member.global_name or correct_member.username
        embed = hikari.Embed(
            title="Кто написал это?",
            description=(
                rslt +
                f"\n\nЭто написал **{member_name}** \n https://discord.com/channels/{ctx.guild_id}/{result[3]}/{result[2]}"
            ),
            color=0x30FF30
        )
        andmore = 0
        if len(view.winners) > 10:
            view.winners = view.winners[:10]
            andmore = view.winners - 10
        output = ''.join([f'**{i}\\.** <@{x}>\n' for i, x in enumerate(view.winners, 1)]) if len(view.winners) > 0 else 'Никто'
        if andmore > 0:
            output += f"И ещё {andmore} человек"
        embed.add_field("Угадали", f"{output}")
        try:
            await msg.edit(embed=embed, components=view)
        except hikari.NotFoundError:
            pass
        except hikari.ForbiddenError:
            try:
                await ctx.respond(embed, components=view)
            except hikari.ForbiddenError:
                pass
    elif r_mode == 'False':
        embed = hikari.Embed(
            description="Читание контента сообщений выключено!",
            color=error_color
        )
        embed.set_footer("Чтобы включить напишите /switch read_msg_content")
        await ctx.respond(embed)


@functions.command("random_answer", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def random_answer(
        ctx: lightbulb.Context,
        text: str
        ) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        r_mode = (await functions.Setting(db, "read_content").get('False'))[0]
        if text is None:
            text = "Нет"
        embed = hikari.Embed(
            description="Что то случилось",
            color=error_color
        )
        if r_mode != 'False':
            await gen(sql, ctx, 10000)
            messages = await sql.fetchall()
            text2 = " ||__|| ".join([message[0] for message in messages])
        else:
            messages = ['']
            text2 = ''
        default_answers = ["да", "нет", "возможно да", "возможно нет", "не возможно",
                           "возможно", "однозначно нет", "может быть"]
        if len(text2) < 120:
            combined_message = "**Вопрос:** \n"+text+"\n**Ответ:** \n"
            combined_message += random.choice(default_answers)
        else:
            combined_message = "**Вопрос:** \n"+text+"\n**Ответ:** \n"
            start = await generator.async_combine_common_words(text2, 0, 2, 0, 3)
            combined_message += await generator.async_combine_common_words(
                text2, 5, 8, 1, 5,
                start_word=start+random.choice(default_answers)
                )
        embed = hikari.Embed(
            title="Рандомный ответ",
            description=combined_message,
            color=global_color
        )
        if r_mode == 'False':
            embed.set_footer("Читание контента сообщений выключено")

        await ctx.respond(embed=embed)


@functions.command("day_quote", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def day_quote(
        ctx: lightbulb.Context,
        ) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        r_mode = (await functions.Setting(db, "read_content").get('False'))[0]
        if r_mode != 'False':
            settings = functions.Setting(db, "day_quote")
            result = await settings.get(("", str(datetime.now().day-1)))
            value = result[0]
            day = result[1]
            today_day = str(datetime.now().day)
            embed = hikari.Embed(
                description="Что то случилось",
                color=error_color
            )
            await gen(sql, ctx, 6000)

            messages = await sql.fetchall()
            if len(messages) >= 29:
                if day != today_day:
                    combined_message = await generator.async_combine_common_words(
                        " ||__|| ".join([message[0] for message in messages]), minp=10, maxp=22, minw=3, maxw=6
                        )
                    value = combined_message
                    await settings.set(value=value, value_2=today_day)
                    await db.commit()

                if value:
                    embed = hikari.Embed(
                        title="Цитата дня",
                        description=value,
                        color=global_color
                    )
            else:
                embed = hikari.Embed(
                    description=(
                        "Я пока не могу генерировать сообщения. В базе данных у меня меньше 30 сообщений." +
                        f"\nУ вас {len(messages)} сообщений."
                    ),
                    color=error_color
                )
        else:
            embed = hikari.Embed(
                description="Читание контента сообщений выключено!",
                color=error_color
            )
            embed.set_footer("Чтобы включить напишите /switch read_msg_content")
    await ctx.respond(embed=embed)


@functions.command("rep", bot_plugin)
@functions.slash_command_group
async def rep(ctx: lightbulb.Context):
    ...


@rep.child
@functions.command("rep give", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def rep_give(
        ctx: lightbulb.Context,
        member: hikari.Member
        ) -> None:
    if member.id == ctx.author.id:
        embed = hikari.Embed(
            description="Вы не можете выдать себе репутацию!",
            color=error_color
        )
    else:
        async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
            sql = await db.cursor()
            await async_createdb(ctx.guild_id, sql, db)
            rep = functions.Reputation()
            result = await rep.add(db, sql, ctx, member)
            rep_count = await rep.get(db, sql, member)
            await db.commit()
            if result.succes:
                embed = hikari.Embed(
                    description=f"Репутации у {member.mention} теперь **{rep_count}**. \nВы дали ему/ей 1 репутацию",
                    color=global_color
                )
            else:
                embed = hikari.Embed(
                    description=result.text,
                    color=error_color
                )
    await ctx.respond(embed)


@rep.child
@functions.command("rep take", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def rep_take(
        ctx: lightbulb.Context,
        member: hikari.Member
        ) -> None:
    if member.id == ctx.author.id:
        embed = hikari.Embed(
            description="Вы не можете забрать у себя репутацию!",
            color=error_color
        )
    else:
        async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
            sql = await db.cursor()
            await async_createdb(ctx.guild_id, sql, db)
            rep = functions.Reputation()
            result = await rep.sub(db, sql, ctx, member)
            rep_count = await rep.get(db, sql, member)
            await db.commit()
            if result.succes:
                embed = hikari.Embed(
                    description=f"Репутации у {member.mention} теперь **{rep_count}**.\nВы забрали у него 1 репутацию",
                    color=global_color
                )
            else:
                embed = hikari.Embed(
                    description=result.text,
                    color=error_color
                )
    await ctx.respond(embed)


@rep.child
@functions.command("rep get", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def rep_get(
        ctx: lightbulb.Context,
        member: hikari.Member
        ) -> None:
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        rep = functions.Reputation()
        _member = member or ctx.author
        result = await rep.get(db, sql, _member)
        embed = hikari.Embed(
            title="Репутация",
            description=f"**Участник {_member.mention} имеет:** {result} репутации",
            color=global_color
        )
        embed.set_thumbnail(_member.avatar_url)
    await ctx.respond(embed)


@rep.child
@functions.command("rep leaders", bot_plugin)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def rep_leaders(
        ctx: lightbulb.Context,
        page: int
        ) -> None:
    if page is None:
        page = 1
    page = max(1, page)
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        await sql.execute("SELECT member_id, rep_count FROM rep ORDER BY rep_count DESC")
        results = await sql.fetchall()
        if results is not None:
            embed = hikari.Embed(
                title="Лидеры по репутации на этом сервере",
                description="",
                color=global_color
            )
            elements = []
            for result in results:
                if str(result[1]) != "0":
                    member_id = result[0]
                    member = ctx.app.cache.get_member(ctx.guild_id, member_id)
                    if member is None:
                        member = ctx.get_guild().get_member(member_id)
                    if member is not None:
                        if not member.is_bot and not member.is_system:
                            member_name = member.nickname or member.display_name or member.username
                            elements.append(f"**{member_name}**: {result[1]}")
            view = functions.Views.Pages(elements, ctx, embed, 10, page, ctx.author.id, timeout=60)
        else:
            embed = hikari.Embed(
                description="На этом сервере у всех репутация 0!",
                color=error_color
            )
    if view is not None:
        await view.generate_list()
        ctx.app.d.miru.start_view(view)


@functions.command("put_emoji_if", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def put_emoji_if(
        ctx: lightbulb.Context
        ) -> None:
    sended = False
    async with sqlite3.connect(f'../db/{ctx.guild_id}database.sqlite') as db:
        sql = await db.cursor()
        await async_createdb(ctx.guild_id, sql, db)
        r_mode = (await functions.Setting(db, "read_content").get('False'))[0]
        if r_mode != 'False':
            embed = hikari.Embed(
                description="Что то случилось",
                color=error_color
            )
            text = None
            if text is None:
                await gen(sql, ctx)
                messages = await sql.fetchall()
                await gen(sql, ctx)
                messages2 = await sql.fetchall()
                if len(messages) >= 29:
                    combined_message = await generator.async_combine_common_words(" ||__|| ".join([message[0] for message in messages]))
                    combined_message2 = await generator.async_combine_common_words(" ||__|| ".join([messag[0] for messag in messages2]))
                    desc = ""
                    if combined_message and combined_message2:
                        desc += f"\n**Ставь ✅ если:** {combined_message}\n"
                        desc += f"\n**Ставь ❌ если:** {combined_message2}\n"
                        embed = hikari.Embed(
                            title="Генерация",
                            description=desc,
                            color=global_color
                        )
                        msg = await ctx.respond(embed=embed)
                        message = await msg.message()
                        sended = True
                else:
                    embed = hikari.Embed(
                        description=(
                            "Я пока не могу генерировать сообщения. В базе данных у меня меньше 30 сообщений." +
                            f"\nУ вас {len(messages)} сообщений."
                        ),
                        color=error_color
                    )
        else:
            embed = hikari.Embed(
                description="Читание контента сообщений выключено!",
                color=error_color
            )
            embed.set_footer("Чтобы включить напишите /switch read_msg_content")
            await ctx.respond(embed)
    if r_mode != 'False':
        if not sended:
            await ctx.respond(embed=embed)
        if sended:
            try:
                await asyncio.sleep(1)
                await message.add_reaction("✅")
                await asyncio.sleep(1)
                await message.add_reaction("❌")
            except hikari.NotFoundError:
                ...
            except hikari.ForbiddenError:
                ...


@functions.command("encrypt", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def encrypt(
        ctx: lightbulb.Context,
        text: str, key: str
        ) -> None:
    if key is None:
        key = "idealight0000000"
    lenght = len(key.encode('utf-8'))
    if lenght not in [16, 24, 32]:
        embed = hikari.Embed(
            description=f"Ключ шифрования должен быть в длину: 16, 24 или 32 байтов (у вас {lenght})",
            color=error_color
        )
    else:
        result = await functions.async_run(functions.Crypt.encrypt, key, text)
        if result is None:
            result = "Не удалось зашифровать"
        embed = hikari.Embed(
            description=f"**Ваш зашифрованный текст:** ```{result}```",
            color=global_color
        )
    await ctx.respond(embed)


@functions.command("decrypt", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def decrypt(
        ctx: lightbulb.Context,
        text: str, key: str
        ) -> None:
    if key is None:
        key = "idealight0000000"
    if len(key) not in [16, 24, 32]:
        embed = hikari.Embed(
            description="Ключ шифрования должен быть в длину: 16, 24 или 32 байтов",
            color=error_color
        )
    else:
        try:
            result = await functions.async_run(functions.Crypt.decrypt, key, text)
        except functions.BinasciiError:
            result = "Не удалось расшифровать"
        except ValueError as e:
            result = f"Ошибка: {e.args[0]}"
        if result is None:
            result = "Не удалось расшифровать"
        embed = hikari.Embed(
            description=f"**Ваш расшифрованный текст:** ```{result}```",
            color=global_color
        )
    await ctx.respond(embed)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(bot_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(bot_plugin)
