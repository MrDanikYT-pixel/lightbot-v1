import asyncio
import random
import time

import aiosqlite
import extensions.unique.idealight_files.afunctions as afunctions
from .afunctions import StatusType, Food
import hikari
import lightbulb
import functions
from functions import ceil
import info
import os
import emoji
import logging
from info import global_color, error_color

server = afunctions.server

bot_plugin = lightbulb.Plugin(
    "Уникальные функции IdeaLight",
    f"Сделал {info.developer}",
    default_enabled_guilds=server
)

FOOD: dict[str, Food] = {
    "Пицца": Food(25, 13, 3),
    "Бургер": Food(14, 8, 2),
    "Суши": Food(12, 7, 1),
    "Паста": Food(15, 3, 9),
    "Яблоко": Food(8, 2, 2),
    "Борщ": Food(17, 15, 10),
    "Шаурма": Food(17, 13, 7),
    "Шашлыки": Food(20, 15, 7),
    "Банан": Food(8, 2, 1),
    "Вода": Food(13, 0, 13),
    "Энергетик": Food(14, 0, 11),
    "Кола": Food(11, 0, 6),
    "Чай": Food(12, 0, 10),
    "Мясо": Food(16, 12, 2)
}

database = '../db/idealight.sqlite'
character_engine = None
__filename__ = os.path.basename(__file__)
filename = os.path.splitext(__filename__)[0]
main_logger = logging.getLogger(f"{__package__.split('.')[-1]}.{filename}")


@bot_plugin.listener(hikari.StartingEvent)
async def starting(event: hikari.StartingEvent) -> None:
    await initialize_settings()


@bot_plugin.listener(hikari.StartedEvent)
async def on_start(event: hikari.StartedEvent) -> None:
    asyncio.create_task(on_started(event))


async def on_started(event: hikari.StartedEvent) -> None:
    global character_engine
    character_engine = afunctions.CharacterEngine(db_path=database, tpm=6, app=event.app, webhook_log=os.environ["CHARACTERS_WEBHOOK"])
    await character_engine.start_timer()


async def initialize_settings() -> None:
    async with aiosqlite.connect(database) as db:
        currency_symbol = functions.Setting(db, "currency_symbol")
        await currency_symbol.get("$")
        tick_speed = functions.Setting(db, "tick_speed")
        await tick_speed.get("5")
        await db.commit()


@functions.command("bank", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def bank(ctx: lightbulb.Context):
    ...


@bank.child
@functions.command("bank withdraw")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def bank_withdraw(ctx: lightbulb.Context, amount: float):
    async with aiosqlite.connect(database) as db:
        embed = hikari.Embed(
            description="Произошла непредвиденная ошибка!",
            color=error_color
        )
        sql = await db.cursor()
        economy = afunctions.Economy(db, sql)
        bank = economy.bank
        balances = economy.balance
        if ctx.member is None:
            raise TypeError
        member_balance = await balances.get(ctx.member.id)
        member_bank = await bank.get(ctx.member.id)
        currency_symbol_setting = functions.Setting(db, "currency_symbol")
        currency_symbol = (await currency_symbol_setting.get("$"))[0]
        if member_bank.issucces and member_balance.issucces:
            amount = min(member_bank.data, amount)
            status = await bank.sub(ctx.member.id, amount)
            status2 = await balances.add(ctx.member.id, amount*0.9)
            if status.issucces and status2.issucces:
                member_balance = (await balances.get(ctx.member.id)).data
                member_bank = (await bank.get(ctx.member.id)).data
                embed = hikari.Embed(
                    description=(
                        f"**Вы забрали из банка:** {amount}{currency_symbol}" +
                        f"\n**Вы получили:** {amount*0.9}{currency_symbol} (-10%)"
                        "\n**У вас теперь на балансе:**" +
                        f"\n- **В банке:** {member_bank}{currency_symbol}"
                        f"\n- **В кошельке:** {member_balance}{currency_symbol}"
                    ),
                    color=global_color
                )
        else:
            if member_balance == StatusType.CHARACTER_DOESNT_EXISTS:
                embed = hikari.Embed(
                    description="У вас нет своего персонажа!",
                    color=error_color
                )
        await db.commit()
    await ctx.respond(embed)


@bank.child
@functions.command("bank deposit")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def bank_deposit(ctx: lightbulb.Context, amount: float):
    async with aiosqlite.connect(database) as db:
        embed = hikari.Embed(
            description="Произошла непредвиденная ошибка!",
            color=error_color
        )
        sql = await db.cursor()
        economy = afunctions.Economy(db, sql)
        bank = economy.bank
        balances = economy.balance
        if ctx.member is None:
            raise TypeError
        member_balance = await balances.get(ctx.member.id)
        currency_symbol_setting = functions.Setting(db, "currency_symbol")
        currency_symbol = (await currency_symbol_setting.get("$"))[0]
        if member_balance.issucces:
            amount = min(member_balance.data, amount)
            status = await bank.add(ctx.member.id, amount)
            status2 = await balances.sub(ctx.member.id, amount)
            if status.issucces and status2.issucces:
                member_balance = (await balances.get(ctx.member.id)).data
                member_bank = (await bank.get(ctx.member.id)).data
                embed = hikari.Embed(
                    description=(
                        f"**Вы положили в банк:** {amount}{currency_symbol}\n" +
                        "**У вас теперь на балансе:**" +
                        f"\n- **В банке:** {member_bank}\n- **В кошельке:** {member_balance}"
                    ),
                    color=global_color
                )
        else:
            if member_balance == StatusType.CHARACTER_DOESNT_EXISTS:
                embed = hikari.Embed(
                    description="У вас нет своего персонажа!",
                    color=error_color
                )
            else:
                ...
        await db.commit()
    await ctx.respond(embed)


@bank.child
@functions.command("bank balance")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def bank_balance(ctx: lightbulb.Context, member: hikari.Member | None):
    member = member or ctx.member
    if member is None:
        raise TypeError
    async with aiosqlite.connect(database) as db:
        sql = await db.cursor()
        bank = afunctions.Economy(db, sql).bank
        balance = await bank.get(member.id)
        currency_symbol_setting = functions.Setting(db, "currency_symbol")
        currency_symbol = (await currency_symbol_setting.get("$"))[0]
        if balance.issucces:
            top = await bank.top()
            if top.issucces:
                index_of_value = next((i for i, v in enumerate(top.data) if v[0] == member.id), None)
            else:
                index_of_value = None
            embed = hikari.Embed(
                title="Банк",
                description=(
                    f"**Баланс:** {balance.data}{currency_symbol}\n" +
                    f"**Место в топе:** {index_of_value+1 if isinstance(index_of_value, int) else 'неизвестно'}"
                ),
                color=global_color
            )
            member_nickname = member.nickname or member.display_name or member.username
            embed.set_author(name=f"{member_nickname}({member.id})")
            embed.set_thumbnail(member.avatar_url)
        else:
            embed = hikari.Embed(
                description="Произошла непредвиденная ошибка!",
                color=error_color
            )
    await ctx.respond(embed=embed)


@functions.command("new_character", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def new_character(ctx: lightbulb.Context, name: str) -> None:
    succes_embed = hikari.Embed(
        description="Персонаж с именем `{}` создан!",
        color=global_color
    )
    msg = None
    if ctx.member is None:
        raise TypeError
    async with aiosqlite.connect(database) as db:
        sql = await db.cursor()
        characters = afunctions.Economy(db, sql).characters
        create = await characters.create_new(name, ctx.member.id)
        character: afunctions.Character = create.data
        if create.issucces:
            embed = succes_embed
            if embed.description is None:
                embed.description = ""
            embed.description = embed.description.format(f"{character.name}")
        elif create == StatusType.CONFIRMATION_REQUIRED:
            view = functions.Views.Confirmation(timeout=15)
            embed = hikari.Embed(
                description=f"У вас уже существует персонаж! \nВы хотите сбросить `{character.name}`?",
                color=error_color
            )
            msg = await ctx.respond(embed, components=view)
            ctx.app.d.miru.start_view(view)
            await view.wait()
            view = view.clear_items()
            if view.confirmed:
                create = await characters.create_new(name, ctx.member.id, confirm_reset=True)
                new_character = create.data
                embed = succes_embed
                if embed.description is None:
                    embed.description = ""
                embed.description = embed.description.format(f"{new_character.name}")
            else:
                embed = hikari.Embed(
                    description="Сброс персонажа отменен",
                    color=error_color
                )
        elif create == StatusType.TOO_NEW_A_CHARACTER:
            embed = hikari.Embed(
                description="Чтобы пересоздать персонажа прошлый должен быть создан больше чем 3 часа назад!",
                color=error_color
            )
        await db.commit()
    if msg is not None:
        await msg.edit(embed, components=view)
    else:
        await ctx.respond(embed)


@functions.command("character", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def character(ctx: lightbulb.Context, member: hikari.Member | None) -> None:
    member = member or ctx.member
    if member is None:
        raise TypeError
    async with aiosqlite.connect(database) as db:
        sql = await db.cursor()
        characters = afunctions.Economy(db, sql).characters
        get_character = await characters.get(user_id=member.id)
        currency_symbol_setting = functions.Setting(db, "currency_symbol")
        currency_symbol = (await currency_symbol_setting.get("$"))[0]
        if get_character.issucces:
            character = get_character.data

            hunger_progress_bar = functions.generate_progress_bar(ceil(character.hunger)/100, 14, emoji.ProgressBar.Orange)
            energy_progress_bar = functions.generate_progress_bar(ceil(character.energy)/100, 14, emoji.ProgressBar.Blue)

            description = (
                f"**Имя персонажа:** {character.name}\n" +
                f"**Баланс:** {character.balance}{currency_symbol}\n" +
                f"**Создан:** <t:{int(character.created_at)}:R>"
            )
            embed = hikari.Embed(
                description="",
                color=global_color
            )
            embed.add_field("Инфа", description)
            embed.add_field("Голод", f"{character.hunger:.2f}/100\n{hunger_progress_bar}", inline=False)
            embed.add_field("Энергия", f"{character.energy:.2f}/100\n{energy_progress_bar}", inline=False)
            member_nickname = member.nickname or member.display_name or member.username
            embed.set_author(name=f"{member_nickname}({member.id})", icon=member.avatar_url)
            embed.set_thumbnail(character.avatar)
            embed.set_footer(f"ID: {character.character_id}")
        elif get_character == StatusType.CHARACTER_DOESNT_EXISTS:
            embed = hikari.Embed(
                description=f"У участника {member.mention} нет своего персонажа!",
                color=error_color
            )
    await ctx.respond(embed)


@functions.command("pay", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def pay(ctx: lightbulb.Context, member: hikari.Member, amount: int):
    member = member or ctx.member
    async with aiosqlite.connect(database) as db:
        embed = hikari.Embed(
            description="Произошла непредвиденная ошибка!",
            color=error_color
        )
        sql = await db.cursor()
        economy = afunctions.Economy(db, sql)
        characters = economy.characters
        get_member_balance = await economy.balance.get(ctx.member.id)
        get_character = await characters.get(user_id=member.id)
        currency_symbol_setting = functions.Setting(db, "currency_symbol")
        currency_symbol = (await currency_symbol_setting.get("$"))[0]
        if get_character.issucces and get_member_balance.issucces:
            member_balance = get_member_balance.data

            if member_balance-amount < 0:
                embed = hikari.Embed(
                    description="Недостаточно средств",
                    color=error_color
                )
            else:
                author_sub = await economy.balance.sub(ctx.member.id, amount)
                send_to = await economy.balance.add(member.id, amount*0.9)
                if send_to.issucces and author_sub.issucces:
                    embed = hikari.Embed(
                        description=(
                            f"**Вы отправили:** {amount}{currency_symbol}\n" +
                            f"**Получатель:** {member.mention}\n" +
                            f"**Получатель получил:** {amount*0.9}{currency_symbol} (-10%)"
                        ),
                        color=global_color
                    )
            await db.commit()
        elif get_character == StatusType.CHARACTER_DOESNT_EXISTS:
            embed = hikari.Embed(
                description=f"У участника {member.mention} нет своего персонажа!",
                color=error_color
            )
        elif get_member_balance == StatusType.CHARACTER_DOESNT_EXISTS:
            embed = hikari.Embed(
                description="У вас нету своего персонажа!",
                color=error_color
            )
    await ctx.respond(embed)


@functions.command("eat", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def eat(ctx: lightbulb.Context, food: str) -> None:
    if food not in FOOD:
        embed = hikari.Embed(
            description="Еду которую вы выбрали нету в магазине!",
            color=error_color
        )
        await ctx.respond(embed)
        return
    async with aiosqlite.connect(database) as db:
        embed = hikari.Embed(
            description="Произошла непредвиденная ошибка!",
            color=error_color
        )
        sql = await db.cursor()
        selected_food = FOOD[food]
        economy = afunctions.Economy(db, sql)
        get_member_balance = await economy.balance.get(ctx.member.id)
        currency_symbol_setting = functions.Setting(db, "currency_symbol")
        currency_symbol = (await currency_symbol_setting.get("$"))[0]
        if get_member_balance.issucces:
            member_balance = get_member_balance.data
            if member_balance-selected_food.cost < 0:
                embed = hikari.Embed(
                    description="Недостаточно средств",
                    color=error_color
                )
            else:
                await economy.balance.sub(ctx.member.id, selected_food.cost)
                member_character = (await economy.characters.get(user_id=ctx.member.id)).data
                await economy.characters.eat(selected_food, member_character)
                member_character = (await economy.characters.get(user_id=ctx.member.id)).data
                embed = hikari.Embed(
                    description=(f"Ваш персонаж сьел `{food}`\n" +
                                 "**Теперь у вас**\n" +
                                 f"- **{member_character.hunger:.2f}/100** голода (+{selected_food.hunger})\n" +
                                 f"- **{member_character.energy:.2f}/100** энергии (+{selected_food.energy})\n" +
                                 f"- **{member_character.balance}{currency_symbol}** на балансе (-{selected_food.cost}{currency_symbol})"),
                    color=global_color
                )
                await db.commit()
        elif get_member_balance == StatusType.CHARACTER_DOESNT_EXISTS:
            embed = hikari.Embed(
                description="У вас нету персонажа",
                color=error_color
            )
    await ctx.respond(embed)


@eat.autocomplete("food")
async def eat_autocomplete(option: hikari.AutocompleteInteractionOption, interaction: hikari.AutocompleteInteraction):
    async with aiosqlite.connect(database) as db:
        currency_symbol_setting = functions.Setting(db, "currency_symbol")
        currency_symbol = (await currency_symbol_setting.get("$"))[0]
    options: list[hikari.CommandChoice] = []
    for x in FOOD.keys():
        if len(option.value) == 0 or option.value in str(x).lower():
            options.append(hikari.CommandChoice(name=f"{x}: +{FOOD[x].hunger} голода, +{FOOD[x].energy} энергии и -{FOOD[x].cost}{currency_symbol}", value=x))

    return options
    return list(FOOD.keys())


@functions.command("sleep", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def sleep(ctx: lightbulb.Context, hours: int, minutes: int):
    minutes = minutes or 0
    async with aiosqlite.connect(database) as db:
        embed = hikari.Embed(
            description="Произошла непредвиденная ошибка!",
            color=error_color
        )
        sql = await db.cursor()
        economy = afunctions.Economy(db, sql)
        characters = economy.characters
        get_character = await characters.get(user_id=ctx.member.id)
        if get_character.issucces:
            character = get_character.data
            passed = time.time()-character.last_sleep
            if character.is_sleeping:
                remaining = character.sleep_until-time.time()
                hours = str(round(remaining // 3600)).zfill(2)
                minutes = str(round((remaining % 3600) // 60)).zfill(2)
                seconds = str(round((remaining % 3600) % 60)).zfill(2)
                embed = hikari.Embed(
                    description=f"Вы сейчас спите! До конца сна осталось `{hours}:{minutes}:{seconds}` времени",
                    color=error_color
                )
            elif character.energy > 95:
                embed = hikari.Embed(
                    description="У вас слишком много энергии чтобы спать",
                    color=error_color
                )
            elif passed < 1*60*60:
                remaining = 1*60*60-passed
                hours = str(round(remaining // 3600)).zfill(2)
                minutes = str(round((remaining % 3600) // 60)).zfill(2)
                seconds = str(round((remaining % 3600) % 60)).zfill(2)
                embed = hikari.Embed(
                    description=f"Вы уже недавно спали, подождите `{hours}:{minutes}:{seconds}` времени",
                    color=error_color
                )
            else:
                await sql.execute(
                    "UPDATE characters SET sleep_until = ? WHERE character_id = ?",
                    (time.time()+(hours*60*60+minutes*60), character.character_id)
                )
                await db.commit()
                embed = hikari.Embed(
                    description="Вы успешно заснули",
                    color=global_color
                )
        elif get_character == StatusType.CHARACTER_DOESNT_EXISTS:
            embed = hikari.Embed(
                description="У вас нету персонажа",
                color=error_color
            )
    await ctx.respond(embed)


@functions.command("work", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def work(ctx: lightbulb.Context):
    async with aiosqlite.connect(database) as db:
        embed = hikari.Embed(
            description="Произошла непредвиденная ошибка!",
            color=error_color
        )
        sql = await db.cursor()
        economy = afunctions.Economy(db, sql)
        characters = economy.characters
        get_character = await characters.get(user_id=ctx.member.id)
        currency_symbol_setting = functions.Setting(db, "currency_symbol")
        currency_symbol = (await currency_symbol_setting.get("$"))[0]
        if get_character.issucces:
            character = get_character.data
            last_time_worked = character.last_time_worked
            passed = time.time()-last_time_worked
            if character.is_sleeping:
                remaining = character.sleep_until-time.time()
                hours = str(round(remaining // 3600)).zfill(2)
                minutes = str(round((remaining % 3600) // 60)).zfill(2)
                seconds = str(round((remaining % 3600) % 60)).zfill(2)
                embed = hikari.Embed(
                    description=f"Вы сейчас спите! До конца сна осталось `{hours}:{minutes}:{seconds}` времени",
                    color=error_color
                )
            elif character.energy < 15:
                embed = hikari.Embed(
                    description="Вы не можете работать когда у вас мало энергии",
                    color=error_color
                )
            elif passed < 10800:
                remaining = 10800-passed
                hours = str(round(remaining // 3600)).zfill(2)
                minutes = str(round((remaining % 3600) // 60)).zfill(2)
                seconds = str(round((remaining % 3600) % 60)).zfill(2)
                embed = hikari.Embed(
                    description=f"Вы уже недавно работали, подождите `{hours}:{minutes}:{seconds}` времени",
                    color=error_color
                )
            else:
                activty_points = await afunctions.Points(db, sql).get(ctx.member.id)
                earned = random.randint(15, 50)
                bonus = round((max(activty_points/2, 1)), 2)
                await economy.balance.add(ctx.member.id, earned+bonus)
                max_sub_energy = 3+(1*(100-character.hunger)/10)
                sub_energy = round(random.uniform(max_sub_energy/3, max_sub_energy), 2)
                await sql.execute(
                    "UPDATE characters SET last_time_worked = ?, energy = ? WHERE character_id = ?",
                    (time.time(), max(0, character.energy-sub_energy), character.character_id,)
                )
                await db.commit()
                embed = hikari.Embed(
                    description=(
                        f"**Вы потратили** {sub_energy} энергии\n" +
                        f"**Вы заработали** {earned}{currency_symbol} \n" +
                        f"- **бонус за активность** {bonus}{currency_symbol}\n" +
                        f"- **Всего** {earned+bonus}{currency_symbol}"
                    ),
                    color=global_color
                )
        elif get_character == StatusType.CHARACTER_DOESNT_EXISTS:
            embed = hikari.Embed(
                description="У вас нету персонажа",
                color=error_color
            )
    await ctx.respond(embed)


@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@functions.command("casino", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def casino(ctx: lightbulb.Context, bet: int):
    succes = False
    scroll = None
    won = False
    won_money = 0
    async with aiosqlite.connect(database) as db:
        embed = hikari.Embed(
            description="Произошла непредвиденная ошибка!",
            color=error_color
        )
        sql = await db.cursor()
        economy = afunctions.Economy(db, sql)
        get_member_character = await economy.characters.get(user_id=ctx.member.id)
        currency_symbol_setting = functions.Setting(db, "currency_symbol")
        currency_symbol = (await currency_symbol_setting.get("$"))[0]
        if get_member_character.issucces:
            character = get_member_character.data
            member_balance = character.balance
            if character.is_sleeping:
                remaining = character.sleep_until-time.time()
                hours = str(round(remaining // 3600)).zfill(2)
                minutes = str(round((remaining % 3600) // 60)).zfill(2)
                seconds = str(round((remaining % 3600) % 60)).zfill(2)
                embed = hikari.Embed(
                    description=f"Вы сейчас спите! До конца сна осталось `{hours}:{minutes}:{seconds}` времени",
                    color=error_color
                )
            elif member_balance-bet < 0:
                embed = hikari.Embed(
                    description="Недостаточно средств",
                    color=error_color
                )
            else:
                result = afunctions.casino("🍊🍋🍉🍓🍇🥭🍐", "🔥", bet)
                scroll = result[1]
                succes = True
                won_money = result[2]
                if result[2] == 0:
                    won = False
                    await economy.balance.sub(ctx.member.id, bet)
                else:
                    won = True
                    await economy.balance.add(ctx.member.id, result[2])
                character: afunctions.Character = (await economy.characters.get(user_id=ctx.member.id)).data
                await db.commit()
        elif get_member_character == StatusType.CHARACTER_DOESNT_EXISTS:
            embed = hikari.Embed(
                description="У вас нету персонажа",
                color=error_color
            )
    if succes:
        message: lightbulb.ResponseProxy | hikari.Message = None
        index = 1
        for x in range(len(scroll)-2):
            first_line = ''.join(scroll[index-1])
            second_line = ''.join(scroll[index])
            third_line = ''.join(scroll[index+1])
            embed = hikari.Embed(
                title="Казино",
                description=(
                    "---------" +
                    f"\n {first_line} " +
                    f"\n{second_line} <-" +
                    f"\n {third_line} \n"
                    "----------"
                ),
                color=global_color
            )
            if message is None:
                message = await ctx.respond(embed)
            else:
                message = await message.edit(embed)
            index += 1
            await asyncio.sleep(1)
        if won:
            embed.description += (f"\n\n **Вы выиграли:** {won_money}{currency_symbol}" +
                                  f"\n**На вашем балансе теперь:** {character.balance:.2f}{currency_symbol}")
        else:
            embed.color = error_color
            embed.description += (f"\n\n **Вы проиграли:** {bet}{currency_symbol}" +
                                  f"\n**На вашем балансе теперь:** {character.balance:.2f}{currency_symbol}")
        message = await message.edit(embed)
    else:
        await ctx.respond(embed)


@functions.command("inventory", bot_plugin)
@lightbulb.implements(lightbulb.SlashCommand)
async def inventory(ctx: lightbulb.Context, page: int):
    view = hikari.UNDEFINED
    async with aiosqlite.connect(database) as db:
        embed = hikari.Embed(
            description="Произошла непредвиденная ошибка!",
            color=error_color
        )
        sql = await db.cursor()
        economy = afunctions.Economy(db, sql)
        characters = economy.characters
        inventory = economy.inventory
        get_character = await characters.get(user_id=ctx.member.id)
        if get_character.issucces:
            character_inventory = await inventory.get(get_character.data)
            items = character_inventory.data.items
            elements = []
            for x in items:
                citem = items[x][0]
                citem_count = items[x][1]
                elements.append(f"**{citem.name}**: {citem_count} шт. \n{citem.description}\n")
            if len(elements) == 0:
                embed = hikari.Embed(
                    title="Ваш инвентарь",
                    description="Пусто",
                    color=error_color
                )
            else:
                embed = hikari.Embed(
                    title="Ваш инвентарь",
                    description="",
                    color=global_color
                )
                view = functions.Views.Pages(elements, ctx, embed, 10, page, ctx.author.id, timeout=60)
        elif get_character == StatusType.CHARACTER_DOESNT_EXISTS:
            embed = hikari.Embed(
                description="У вас нету персонажа",
                color=error_color
            )
    if view != hikari.UNDEFINED:
        await view.generate_list()
        ctx.app.d.miru.start_view(view)
    else:
        await ctx.respond(embed)


@bot_plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message_create(event: hikari.GuildMessageCreateEvent):
    if event.guild_id != server[0]:
        return


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(bot_plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(bot_plugin)
