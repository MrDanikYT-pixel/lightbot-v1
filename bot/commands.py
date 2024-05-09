import hikari
import generator
import info


class Argument:
    def __init__(
            self, name: str, description: str, type: str, required: bool, *,
            range: tuple[float | int | None] = (None, None), length: tuple[int | None] = (None, None), **args):
        self.name, self.description, self.type = name, description, type
        self.required, self.range, self.length = required, range, length
        self.other = args


class Category:
    def __init__(self, id: str, name: str) -> None:
        self.id = id
        self.name = name


class Categories:
    def __init__(self) -> None:
        self.categories: list[Category] = []

    def add(self, id, name):
        self.categories.append(Category(id, name))
        return self

    def rem(self, id: str):
        for x in self.categories:
            if x.id == id:
                self.categories.remove(x)
        return self

    def get(self, id: str) -> Category | None:
        for x in range(len(self.categories)):
            if self.categories[x].id == id:
                return self.categories[x]
        raise KeyError(f"'{id}' не категория!")

    def dict(self) -> tuple[dict[str, list], dict[str, list]]:
        dict = {}
        keys = {}
        for x in self.categories:
            dict[x.name] = []
            keys[x.id] = x.name
        return (dict, keys)


categories = Categories()
categories.add("settings", "🛠Настройки")
categories.add("statistics", "📉Статистика и инфо")
categories.add("utilities", "🧱Инструменты")
categories.add("fun", "😃Фан")
categories.add("premium", "⭐Премиум")
categories.add("unique", f"🔥Уникальное (есть только на основном сервере {info.server_emoji})")
page = Argument("page", "Страница", int, False, range=(1, 100000))

generator_versions = list(generator.GeneratorVersions().versions.keys())


class Command:
    def __init__(self, name: str, description: str, arguments: list[Argument], auto_defer: bool = True, ephemeral=False, category: str | None = None, *, guilds: tuple | None = None, **kwargs):
        self.name = name
        self.description = description
        if info.beta:
            self.description += ' "Бета"'
        self.arguments = arguments
        self.auto_defer = auto_defer
        self.ephemeral = ephemeral
        self.guilds = guilds
        self.kwargs = kwargs
        if category is not None:
            self.category = categories.get(category)
        else:
            self.category = None


generator_info = f'Режим генератора (По умолчанию: {generator.default_mode})'
d: dict[str, Command] = {
    "help": Command(
        "help",
        "Помощь",
        [Argument("command", "Название команды", str, False)],
        ephemeral=True
    ),

    # Настройки
    "clear_db": Command(
        "clear_db",
        "Удаляет сообщения всех или конкретного пользователя из базы данных",
        [Argument("member", "Пользователь, чьи сообщения будут удалены из базы данных", hikari.Member, False)],
        ephemeral=True,
        category="settings"
    ),

    "delete_from_db": Command(
        "delete_from_db",
        "Удаляет сообщение из базы данных",
        [Argument("message_id", "Ссылка на сообщение или его ID для удаления из базы данных", str, True)],
        ephemeral=True,
        category="settings"
    ),

    "switch": Command(
        "switch",
        "Настройки бота на сервере",
        []
    ),

    "switch generator_mode": Command(
        "switch generator_mode",
        "Изменяет режим генератора",
        [Argument("mode", generator_info, str, True, choices=generator.modes_desc)],
        ephemeral=True,
        category="settings"
    ),

    "switch read_msg_content": Command(
        "switch read_msg_content",
        "Позволяет боту не читать контент сообщений, но собирать статистику об их количестве",
        [Argument("mode", "Режим записи контента в базу данных", str, True, choices=["Включить", "Выключить", "Инфо"])],
        ephemeral=True,
        category="settings"
    ),

    "switch random_msgs": Command(
        "switch random_msgs",
        "Управляет случайными генерациями при активности в чате",
        [Argument("mode", "Включить или включить генерацию после рандомного сообщения в чате", str, True, choices=["Включить", "Выключить"])],
        ephemeral=True,
        category="settings"
    ),

    "switch mention_to_generate": Command(
        "switch mention_to_generate",
        "Отключает/Включает генерацию при упоминании бота",
        [Argument("mode", "Выбрать будет ли бот генерировать при упоминании", str, True, choices=["Включить", "Выключить"])],
        ephemeral=True,
        category="settings"
    ),

    "ignored_members list": Command(
        "ignored_members list",
        "Отправляет чёрный список пользователей",
        [page],
        category="settings"
    ),

    "ignored_members": Command(
        "ignored_members",
        "Черный список участников.",
        []
    ),

    "ignored_members check": Command(
        "ignored_members check",
        "Отправляет информацию, находится ли пользователь в чёрном списке",
        [Argument("member", "Пользователь для получения информации о его нахождении в чёрном списке", hikari.Member, True)],
        ephemeral=True,
        category="settings"
    ),

    "ignored_members remove": Command(
        "ignored_members remove",
        "Удаляет пользователя из чёрного списка",
        [Argument("member", "Пользователь для удаления из чёрного списка", hikari.Member, True)],
        ephemeral=True,
        category="settings"
    ),

    "ignored_members add": Command(
        "ignored_members add",
        "Добавляет пользователя в чёрный список",
        [Argument("member", "Пользователь для добавления в чёрный список", hikari.Member, True),
         Argument("reason", "Причина добавления пользователя в чёрный список", str, False, length=(0, 70))],
        ephemeral=True,
        category="settings"
    ),

    "ignored_members clear": Command(
        "ignored_members clear",
        "Очищает чёрный список пользователей",
        [],
        ephemeral=True,
        category="settings"
    ),

    "allowed_channels": Command(
        "allowed_channels",
        "Белый список каналов где будет работать генерация и читание контента сообщений.",
        []
    ),

    "allowed_channels list": Command(
        "allowed_channels list",
        "Отправляет белый список каналов",
        [page],
        "list",
        category="settings"
    ),

    "allowed_channels add": Command(
        "allowed_channels add",
        "Добавляет канал в белый список",
        [Argument("channel", "Канал для добавления в белый список", hikari.TextableGuildChannel, True, channel_types=[hikari.ChannelType.GUILD_TEXT])],
        "add",
        ephemeral=True,
        category="settings"
    ),

    "allowed_channels remove": Command(
        "allowed_channels remove",
        "Удаляет канал из белого списка",
        [Argument("channel", "Канал для удаления из белого списка", hikari.TextableGuildChannel, True, channel_types=[hikari.ChannelType.GUILD_TEXT])],
        "remove",
        ephemeral=True,
        category="settings"
    ),

    "allowed_channels clear": Command(
        "allowed_channels clear",
        "Очищает белый список каналов",
        [],
        "clear",
        ephemeral=True,
        category="settings"
    ),
    # ## #
    # Статистика
    "info": Command(
        "info",
        "Информация о боте или сервере",
        []
    ),

    "info server": Command(
        "info server",
        "Отправляет ифнормацию о сервере",
        [],
        auto_defer=True,
        category="statistics"
    ),

    "info bot": Command(
        "info bot",
        "Отправляет ифнормацию о боте",
        [],
        auto_defer=True,
        category="statistics"
    ),

    "leaders": Command(
        "leaders",
        "Отправляет лидерборд пользователей по количеству сообщений",
        [page],
        auto_defer=True,
        category="statistics"
    ),

    "top": Command(
        "top",
        "Отправляет лидерборд самых частых слов в сообщениях",
        [page, Argument("time", "Выбрать за какое время будет топ", str, False, choices=info.CHOICES["toptime"])],
        auto_defer=True,
        category="statistics"
    ),

    "most_msgs_time": Command(
        "most_msgs_time",
        "Отправляет время и дату самого большого актива и его самого полезного пользователя",
        [page],
        auto_defer=True,
        category="statistics"
    ),

    "msgs": Command(
        "msgs",
        "Сколько написал(и) сообщений участник или все участники",
        []
    ),

    "msgs member": Command(
        "msgs member",
        "Отправляет статистику пользователя по сообщениям за всё время и последние дни",
        [Argument("member", "Пользователь для получения его статистики", hikari.Member, False)],
        auto_defer=True,
        category="statistics"
    ),

    "msgs all": Command(
        "msgs all",
        "Общая статистика сообщений всех пользователей за всё время или в последние дни",
        [],
        auto_defer=True,
        category="statistics"
    ),

    "msgs time": Command(
        "msgs time",
        "Общая статистика сообщений всех пользователей за всё определенное время",
        [Argument("date", "Дата для получения статистики", str, True)],
        auto_defer=True,
        category="statistics"
    ),

    "channels_top": Command(
        "channels_top",
        "Отправляет лидерборд каналов по количеству сообщений",
        [page],
        auto_defer=True,
        category="statistics"
    ),

    "version_info": Command(
        "version_info",
        "Отправляет информацию о последней или конкретной версии бота",
        [Argument("version", "Версия, о которой будет получена информация", str, False)],
        ephemeral=True,
        category="statistics"
    ),

    "report_bug": Command(
        "report_bug",
        "Оповещает разработчиков бота о баге",
        [Argument("short_desc", "Краткое описание бага", str, True),
         Argument("text", "Развёрнутое описание бага", str, True, length=(8, 72)),
         Argument("steps", "Шаги, при которых вы получили баг", str, False, length=(8, 512))],
        ephemeral=True,
        category="utilities"
    ),
    # ## #
    # Утилиты
    "support_me": Command(
        "support_me",
        "Отправляет ссылку на денежную поддержку автора бота",
        [],
        ephemeral=True,
        category="utilities"
    ),

    "send_idea": Command(
        "send_idea",
        "Оповещает разработчиков бота о вашей идее",
        [Argument("text", "Развёрнутое описание идеи", str, True)],
        auto_defer=True,
        category="utilities"
    ),

    "encrypt": Command(
        "encrypt",
        "Зашифровать текст",
        [Argument("text", "Текст для шифрования", str, True),
         Argument("key", "Ключ шифрования", str, False, length=(4, 128))],
        ephemeral=True,
        category="utilities"
    ),

    "decrypt": Command(
        "decrypt",
        "Расшифровать текст",
        [Argument("text", "Зашифрованный текст", str, True),
         Argument("key", "Ключ шифрования", str, False, length=(4, 128))],
        ephemeral=True,
        category="utilities"
    ),

    "rep": Command(
        "rep",
        "Репутация участников на вашем сервере",
        []
    ),

    "rep give": Command(
        "rep give",
        "Выдать участнику репутацию",
        [Argument("member", "Участник которому вы дадите репутации", hikari.Member, True)],
        category="utilities"
    ),

    "rep take": Command(
        "rep take",
        "Забрать репутацию у участнику если вы ему дали",
        [Argument("member", "Участник у которого вы хотите забрать репутацию", hikari.Member, True)],
        category="utilities"
    ),

    "rep get": Command(
        "rep get",
        "Показывает репутацию участника",
        [Argument("member", "Участник у которого вы хотите посмотреть репутацию", hikari.Member, False)],
        category="utilities"
    ),

    "rep leaders": Command(
        "rep leaders",
        "Лидеры по репутации",
        [page],
        category="utilities"
    ),

    # ## #
    # Фан
    "generate": Command(
        "generate",
        "Генерирует текст из сообщений в чате или конкретных текстов",
        [Argument("text", 'Тексты для генерации из них (разделитель "||__||")', str, False),
         Argument("minp", "Минимальное количество фраз (Стандарт: 2)", int, False, range=(1, 6)),
         Argument("maxp", "Максимальное количество фраз (Стандарт: 14)", int, False, range=(6, 20)),
         Argument("minw", "Минимальное количество слов в фразе (Стандарт: 3)", int, False, range=(1, 5)),
         Argument("maxw", "Максимальное количество слов в фразе (Стандарт: 9)", int, False, range=(5, 15)),
         Argument("start_word", "Начальное слово", str, False, length=(1, 22)),
         Argument("msgs_min_len", "Минимальная длина сообщений которые получает генератор (Стандарт: 5)", int, False, range=(1, 32)),
         Argument("msgs_limit", "Лимит сообщений который получить генератор (Стандарт: 6000)", int, False, range=(30, 6000)),
         Argument("version", "Версия генератора которая будет использоватся для генерации (OP - оптимизирован, AD - адаптирован)", str, False, choices=generator_versions)],
        auto_defer=True,
        category="fun"
    ),

    "random_answer": Command(
        "random_answer",
        "Отправляет сгенерированный ответ на вопрос",
        [Argument("text", "Вопрос, который будет задан генератору", str, False)],
        auto_defer=True,
        category="fun"
    ),

    "day_quote": Command(
        "day_quote",
        "Отправляет цитату дня",
        [],
        auto_defer=True,
        category="fun"
    ),

    "put_emoji_if": Command(
        "put_emoji_if",
        'Отправляет опрос в формате "Да/Нет" со сгенерированными текстами',
        [],
        auto_defer=True,
        category="fun"
    ),

    "who_say_it": Command(
        "who_say_it",
        'Мини-игра "Кто написал это сообщение?"',
        [Argument("time", "Время через которое покажет кто написал (в секундах)", int, False, range=(10, 300))],
        auto_defer=True,
        category="fun"
    ),
    # Premium
    "block_reactions": Command(
        "block_reactions",
        "Блокировка установки эмодзи в определенном канале.",
        []
    ),

    "block_reactions add_channel": Command(
        "block_reactions add_channel",
        "Добавляет канал где будут блокироваться эмодзи *Премиум 1*",
        [Argument("channel", "Канал", hikari.TextableGuildChannel, True)],
        ephemeral=True,
        category="premium"
    ),

    "block_reactions rem_channel": Command(
        "block_reactions rem_channel",
        "Удаляет канал где будут блокироваться эмодзи *Премиум 1*",
        [Argument("channel", "Канал", hikari.TextableGuildChannel, True)],
        ephemeral=True,
        category="premium"
    ),

    "block_reactions channel_list": Command(
        "block_reactions channel_list",
        "Список каналов где блокируються эмодзи *Премиум 1*",
        [page],
        category="premium"
    ),

    "block_reactions add_role": Command(
        "block_reactions add_role",
        "Разрешает роль в канале где блокируються эмодзи *Премиум 1*",
        [Argument("channel", "Канал", hikari.TextableGuildChannel, True),
         Argument("role", "Роль", hikari.Role, True)],
        ephemeral=True,
        category="premium"
    ),
    "block_reactions rem_role": Command(
        "block_reactions rem_role",
        "Убирает разрешенную роль *Премиум 1*",
        [Argument("channel", "Канал", hikari.TextableGuildChannel, True),
         Argument("role", "Роль", hikari.Role, True)],
        ephemeral=True,
        category="premium"
    ),

    "block_reactions role_list": Command(
        "block_reactions role_list",
        "Список разрешенных ролей в канале *Премиум 1*",
        [Argument("channel", "Канал", hikari.TextableGuildChannel, True), page],
        category="premium"
    ),

    "del_thread_create_msg": Command(
        "del_thread_create_msg",
        "Включает/выключает удаление сообщения \"`ник` создал ветку\" *Премиум 2*",
        [Argument("mode", "Режим", str, True, choices=["Включить", "Выключить"])],
        ephemeral=True,
        category="premium"
    ),

    "del_pin_add_msg": Command(
        "del_pin_add_msg",
        "Включает/выключает удаление сообщения \"`ник` прикрепил сообщение\" *Премиум 2*",
        [Argument("mode", "Режим", str, True, choices=["Включить", "Выключить"])],
        ephemeral=True,
        category="premium"
    ),
    # ## #
    "most_active_members": Command(
        "most_active_members",
        "Самые активные участники этого сервера",
        [page],
        ephemeral=False,
        category="unique"
    ),
    "activity_points": Command(
        "activity_points",
        "Сколько баллов активности у участника",
        [Argument("member", "Участник у которого вы хотите посмотреть количество баллов", hikari.Member, False)],
        ephemeral=False,
        category="unique"
    ),
    # Activity
    # "character": Command(
    #     "character",
    #     "Статус персонажа и количество денег",
    #     [Argument("member", "Укажите у кого вы хотите посмотреть персонажа", hikari.Member, False)],
    #     ephemeral=False,
    #     category="unique"
    # ),
    # "new_character": Command(
    #     "new_character",
    #     "Создать нового персонажа",
    #     [Argument("name", "Имя нового персонажа (имя нельзя будет сменить)", str, False)],
    #     ephemeral=True,
    #     category="unique"
    # ),
    # "bank balance": Command(
    #     "bank balance",
    #     "Посмотреть баланс в банке участника",
    #     [Argument("member", "Участник у которого вы хотите посмотреть баланс в банке", str, False)],
    #     ephemeral=False,
    #     category="unique"
    # ),
    # "bank deposit": Command(
    #     "bank deposit",
    #     "Положить деньги в банк",
    #     [Argument("amount", "Сколько вы хотите положить денег в банк", float, True, range=(0, 2**16))],
    #     ephemeral=False,
    #     category="unique"
    # ),
    # "bank withdraw": Command(
    #     "bank withdraw",
    #     "Вывести из банка",
    #     [Argument("amount", "Сколько вы хотите вывести денег из банка", float, True, range=(0, 2**16))],
    #     ephemeral=False,
    #     category="unique"
    # ),
    # "eat": Command(
    #     "eat",
    #     "Купить и сразу сьесть еду",
    #     [Argument("food", "Что вы хотите сьесть", str, True, autocomplete=True)],
    #     ephemeral=False,
    #     category="unique"
    # ),
    # "work": Command(
    #     "work",
    #     "Заработать деньги на работе",
    #     [],
    #     ephemeral=False,
    #     category="unique"
    # ),
    # "casino": Command(
    #     "casino",
    #     "Покрутить казино",
    #     [Argument("bet", "Ваша ставка", int, True, range=(25, 2**16))],
    #     ephemeral=False,
    #     category="unique"
    # ),
    # "pay": Command(
    #     "pay",
    #     "Отправить деньги другому человеку",
    #     [Argument("member", "Участник которому вы хотите отправить деньги", hikari.Member, True),
    #      Argument("amount", "Количество денег которые вы хотите отправить участнику", int, True, range=(5, 2**16))],
    #     ephemeral=False,
    #     category="unique"
    # ),
    # "sleep": Command(
    #     "sleep",
    #     "Поспать (3 часа сна = +50 энергии)",
    #     [Argument("hours", "Сколько часов персонаж будет спать", int, True, range=(0, 10)),
    #      Argument("minutes", "Сколько минут будет спать персонаж", int, False, range=(0, 59))],
    #     ephemeral=False,
    #     category="unique"
    # ),
    # "inventory": Command(
    #     "inventory",
    #     "Посмотреть свой инвентарь",
    #     [page],
    #     ephemeral=True,
    #     category="unique"
    # )
    # Rank
    # "rank": Command(
    #     "rank",
    #     "akdawiudhwafyugwad",
    #     [Argument("member", "adawdawd", hikari.Member, False)],
    #     ephemeral=True,
    #     category="premium"
    # ),

    # "leaderboard": Command(
    #     "leaderboard",
    #     "akdawiudhwafyugwad",
    #     [page],
    #     ephemeral=True,
    #     category="premium"
    # ),

    # "rank_settings": Command(
    #     "rank_settings",
    #     "awdawdawd",
    #     [],
    #     ephemeral=True
    # )
}

types_translation = {
    hikari.TextableGuildChannel: "текстовый канал",
    hikari.Member: "участник",
    str: "строка",
    int: "число",
    float: "не целое число",
    hikari.User: "пользователь",
    hikari.GuildChannel: "канал",
    hikari.GuildNewsChannel: "канал новостей",
    hikari.GuildVoiceChannel: "войс",
    hikari.Role: "роль"
}


def to_cmds():
    dict, ids = categories.dict()
    for x in d:
        command: Command = d[x]
        if command.category is not None:
            dict[ids[command.category.id]].append(command.name)
    return dict


def cmd_description(command_name: str):
    if command_name in d:
        command = d[command_name]
        return command.description
    else:
        return None


def arg_description(command_name: str, argument_name: str):
    if command_name in d:
        command = d[command_name]
        for argument in command.arguments:
            if argument.name == argument_name:
                return argument.description


def generate_help(command_name, color):
    if command_name in d:
        command = d[command_name]
        help_text = f"**Команда:** `{command.name}`\n\n{command.description}\n\n**Аргументы:**\n"

        if len(command.arguments) > 0:
            for argument in command.arguments:
                help_text += f"- **{argument.name}** ({types_translation.get(argument.type, argument.type)})"
                help_text += " (Обязательный)" if argument.required else ""
                help_text += f"\n - {argument.description}\n"

                if argument.range != (None, None):
                    help_text += f" - Диапазон: {argument.range[0]} - {argument.range[1]}\n"

                if argument.length != (None, None):
                    help_text += f" - Длина: {argument.length[0]} - {argument.length[1]}\n"
        else:
            help_text += "Отсутствуют"

        embed = hikari.Embed(
            title=f"Помощь по команде {command_name}",
            description=help_text,
            color=color
        )
        return embed
    else:
        return "Команда не найдена"
