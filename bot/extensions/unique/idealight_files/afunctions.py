import asyncio
import functools
import random
import time
import typing

import aiohttp
import functions
import aiosqlite
import hikari
import info
import enum
import sqlite3
import urllib.parse as parse
from typing import Generic, Iterable, TypeVar

T = TypeVar("T")
server = info.developer_server


class Points:
    def __init__(self, db: aiosqlite.Connection, sql: aiosqlite.Cursor | None = None) -> None:
        self.db = db
        self.sql = sql

    async def get(self, user_id: hikari.Snowflake | int) -> int:
        db = self.db
        sql = self.sql or (await db.cursor())
        points = await (await sql.execute("""SELECT points FROM points WHERE user_id = ?""", (user_id,))).fetchone()
        if points is None:
            return 0
        else:
            return int(points[0])

    async def set(self, user_id: hikari.Snowflake | int, points: int):
        db = self.db
        sql = self.sql or (await db.cursor())
        _points = await (await sql.execute("""SELECT points FROM points WHERE user_id = ?""", (user_id,))).fetchone()
        if _points is None:
            await sql.execute("""INSERT INTO points (user_id, points) VALUES (?, ?)""", (user_id, points))
        else:
            await sql.execute("""UPDATE points SET points = ? WHERE user_id = ?""", (points, user_id))


class Food:
    def __init__(self, cost: float, hunger: float, energy: float, hapiness: float = 0, name: str = "") -> None:
        self.cost = cost
        self.hunger = hunger
        self.energy = energy
        self.hapiness = hapiness
        self.name = name


class Character:
    def __init__(
            self, character_id: int, user_id: int, balance: float | int = 0,
            hunger: float | int = 100, energy: int = 100, auto_mode: bool | int = False, name: str | None = None,
            avatar: str | None = None, last_time_worked: int = 0, created_at: float | int = 0,
            last_sleep: float | int = int(time.time()), sleep_until: int | float | None = None,
            hunger_notif: int = 0, sleep_notif: int = 0
            ) -> None:
        if isinstance(auto_mode, int):
            if auto_mode == 1:
                auto_mode = True
            else:
                auto_mode = False
        self.character_id = character_id
        self.user_id = user_id
        self.balance = balance
        self.hunger = hunger
        self.energy = energy
        self.auto_mode = auto_mode if isinstance(auto_mode, bool) else (True if auto_mode == 1 else False)
        self.last_time_worked = last_time_worked
        self.name = name or (functions.generate_random_nickname(random.randint(5, 14))[1].capitalize())
        self.created_at = float(created_at)
        self.last_sleep = last_sleep
        self.sleep_until = sleep_until
        self.hunger_notif = hunger_notif
        self.sleep_notif = sleep_notif

        if sleep_until is None:
            self.is_sleeping = False
        else:
            self.is_sleeping = False
            if sleep_until > time.time():
                self.is_sleeping = True

        if avatar is not None:
            self.avatar = avatar
        else:
            seed = f'{self.name}{self.user_id}'
            _random = random.Random(seed)

            # def generate_hex_color():
            #     return '{:06x}'.format(_random.randint(0, 0xFFFFFF))

            # hex_colors = [generate_hex_color() for _ in range(3)]
            # hex_colors_str = ','.join(hex_colors)

            self.avatar = (f"https://api.dicebear.com/8.x/personas/png?seed={parse.quote_plus(seed)}" +
                           f"&radius=15&backgroundType=solid&size=256&shapeRotation={_random.randint(-20, 20)}")

    def get_tuple(self) -> tuple:
        return self.character_id, self.user_id, self.balance, self.hunger, self.energy, self.auto_mode


@typing.final
class StatusType(int, enum.Flag):
    SUCCES = 0

    CHARACTER_DOESNT_EXISTS = 1

    CONFIRMATION_REQUIRED = 2

    UNKNOWN_ERROR = 3

    TOO_NEW_A_CHARACTER = 4

    NO_CONNECTION_TO_THE_DATABASE = 5

    UNKNOW_APP = 6

    NO_SUCH_ITEM = 7

    NO_ACTION = 8


class EconomyStatus(Generic[T]):
    def __init__(self, issucces: bool, message: StatusType | int | None = None, data: T = None) -> None:
        self.issucces = issucces
        self.message = message or (StatusType.SUCCES if issucces else StatusType.UNKNOWN_ERROR)
        self.data = data

    def __eq__(self, other):
        if isinstance(other, (int, StatusType)):
            return self.message == other
        elif isinstance(other, EconomyStatus):
            return self.message == other.message
        else:
            return False


class ItemType(int, enum.Flag):
    NONE = 0
    INVENTORY = 1


class ItemAction:
    def __init__(self, id: int) -> None:
        self.id = id

    async def add(self, character: Character, db: aiosqlite.Connection | None = None, app: hikari.RESTAware | None = None) -> EconomyStatus[None]:
        return EconomyStatus(True, StatusType.NO_ACTION)

    async def delete(self, character: Character, db: aiosqlite.Connection | None = None, app: hikari.RESTAware | None = None) -> EconomyStatus[None]:
        return EconomyStatus(True, StatusType.NO_ACTION)

    async def on_death(self, character: Character, db: aiosqlite.Connection | None = None, app: hikari.RESTAware | None = None) -> EconomyStatus[None]:
        return EconomyStatus(True, StatusType.NO_ACTION)

    async def use(self, character: Character, db: aiosqlite.Connection | None = None, app: hikari.RESTAware | None = None) -> EconomyStatus[None]:
        return EconomyStatus(False, StatusType.NO_ACTION)


class Item:
    def __init__(self, name: str, description: str, id: int = 0, action: ItemAction | None = None, type: ItemType | int = ItemType.NONE) -> None:
        self.name = name
        self.description = description
        self.action = action or ItemAction(id)
        self.type = type
        self.id = id
        self.unknown = True


class InventoryItemAction(ItemAction):
    def __init__(self, id: int) -> None:
        super().__init__(id)

    async def add(self, character: Character, db: aiosqlite.Connection | None = None, app: hikari.RESTAware | None = None) -> EconomyStatus[None]:
        if db is None:
            return EconomyStatus(False, StatusType.NO_CONNECTION_TO_THE_DATABASE)
        sql = await db.cursor()
        await sql.execute(
            "SELECT count FROM inventory WHERE character_id = ? AND item_id = ?",
            (character.character_id, self.id)
        )
        char_item = await sql.fetchone()
        if char_item is None:
            await sql.execute(
                "INSERT INTO inventory (character_id, item_id, count) VALUES (?, ?, ?)",
                (character.character_id, self.id, 1)
            )
        else:
            await sql.execute(
                "UPDATE inventory SET count = ? WHERE character_id = ? AND item_id = ?",
                (char_item[0]+1, character.character_id, self.id)
            )
        return EconomyStatus(True)

    async def delete(self, character: Character, db: aiosqlite.Connection | None = None, app: hikari.RESTAware | None = None) -> EconomyStatus[None]:
        if db is None:
            return EconomyStatus(False, StatusType.NO_CONNECTION_TO_THE_DATABASE)
        sql = await db.cursor()
        await sql.execute(
            "SELECT count FROM inventory WHERE character_id = ? AND item_id = ?",
            (character.character_id, self.id)
        )
        char_item = await sql.fetchone()
        if char_item is None:
            return EconomyStatus(False, StatusType.NO_SUCH_ITEM)
        else:
            if char_item[0] <= 0:
                return EconomyStatus(False, StatusType.NO_SUCH_ITEM)
            await sql.execute(
                "UPDATE inventory SET count = ? WHERE character_id = ? AND item_id = ?",
                (char_item[0]-1, character.character_id, self.id)
            )
        return EconomyStatus(True)


class InventoryItem(Item):
    def __init__(self, name: str, description: str, id: int) -> None:
        super().__init__(name, description, id, InventoryItemAction(id), type=ItemType.INVENTORY)
        self.unknown = False


class RoleItem(Item):
    ...


class ItemStore:
    def __init__(self, sql_result: list[tuple] | None = None) -> None:
        self.items: dict[int, Item] = {}
        if sql_result is not None:
            self.load_from_result(sql_result)

    def load_from_result(self, result: list[tuple]) -> None:
        items = {}
        for x in result:
            if x[3] == ItemType.INVENTORY:
                items[x[0]] = InventoryItem(x[1], x[2], x[0])
        self.items = items

    @staticmethod
    async def get_from_sql(sql: aiosqlite.Cursor) -> list[tuple]:
        result = await (await sql.execute(
                "SELECT item_id, name, description, type, type_extra FROM item_store"
            )).fetchall()
        return list(result)

    @staticmethod
    async def add_item_to_item_store(sql: aiosqlite.Cursor, item: Item, id: int | None = None) -> None:
        await sql.execute(
                f"""
                INSERT INTO item_store ({'item_id,' if id is not None else ''}name, description, type)
                VALUES ({'?, ' if id is not None else ''}?, ?, ?)""",
                ((id,) if id is not None else tuple([])) + (item.name, item.description, item.type)
            )


class CharacterInventory:
    def __init__(self, character: Character, items: dict[int, tuple[Item, int]] = {}) -> None:
        self.items = items
        self.character = character

    def set(self, item: Item, count: int = 1) -> None:
        self.items[item.id] = (item, count)

    def remove(self, item: Item) -> None:
        if self.items[item.id][1] > 1:
            self.items[item.id][1] -= 1
        else:
            del self.items[item.id]

    def find_by_id(self, id: int) -> tuple[Item, int] | None:
        if id in self.items:
            return self.items[id]
        else:
            return None

    def __contains__(self, item_or_id: Item | int) -> bool:
        if isinstance(item_or_id, int):
            return item_or_id in self.items
        elif isinstance(item_or_id, Item):
            return item_or_id.id in self.items
        else:
            return False


class Economy:
    def __init__(self, db: aiosqlite.Connection, sql: aiosqlite.Cursor | None = None) -> None:
        self.balance = self.Balance(db, sql)
        self.characters = self.Characters(db, sql)
        self.bank = self.Bank(db, sql)
        self.inventory = self.Inventory(db, sql)

    class Inventory:
        def __init__(self, db: aiosqlite.Connection, sql: aiosqlite.Cursor | None = None) -> None:
            self._db = db
            self._sql = sql

        async def get(self, character: Character) -> EconomyStatus[CharacterInventory | None]:
            db = self._db
            self._sql = self._sql or (await db.cursor())
            sql = self._sql
            inventory: list[tuple] = await (await sql.execute(
                "SELECT item_id, count FROM inventory WHERE character_id = ? AND count != 0",
                (character.character_id,)
            )).fetchall()
            item_store = ItemStore(await ItemStore.get_from_sql(sql))
            character_inventory = CharacterInventory(character)
            for x in inventory:
                character_inventory.set(item_store.items[x[0]])
            return EconomyStatus(True, data=character_inventory)

        async def get_item(self, id: int) -> EconomyStatus[Item | None]:
            db = self._db
            self._sql = self._sql or (await db.cursor())
            sql = self._sql
            item_store = ItemStore(await ItemStore.get_from_sql(sql))
            if id in item_store:
                return EconomyStatus(True, data=item_store.items[id])
            else:
                return EconomyStatus(False, StatusType.NO_SUCH_ITEM)

    class Bank:
        def __init__(self, db: aiosqlite.Connection, sql: aiosqlite.Cursor | None = None) -> None:
            self._db = db
            self._sql = sql

        async def top(self) -> EconomyStatus[Iterable[aiosqlite.Row]]:
            db = self._db
            self._sql = self._sql or (await db.cursor())
            sql = self._sql
            top = await (await sql.execute("""SELECT user_id, balance FROM bank ORDER BY balance DESC""")).fetchall()
            return EconomyStatus(True, data=top)

        async def get(self, user_id: hikari.Snowflake | int) -> EconomyStatus[int]:
            db = self._db
            self._sql = self._sql or (await db.cursor())
            sql = self._sql
            balance = await (await sql.execute("""SELECT balance FROM bank WHERE user_id = ?""", (user_id,))).fetchone()
            if balance is None:
                return EconomyStatus(True, data=0)
            else:
                return EconomyStatus(True, data=round(balance[0], 2))

        async def set(self, user_id: hikari.Snowflake | int, amount: int) -> EconomyStatus[bool]:
            db = self._db
            self._sql = self._sql or (await db.cursor())
            sql = self._sql
            balance = await (await sql.execute("""SELECT balance FROM bank WHERE user_id = ?""", (user_id,))).fetchone()
            if balance is None:
                await sql.execute("""INSERT INTO bank (user_id, balance) VALUES (?, ?)""", (user_id, amount))
                return EconomyStatus(True)
            else:
                await sql.execute("""UPDATE bank SET balance = ? WHERE user_id = ?""", (amount, user_id))
                return EconomyStatus(True)

        async def add(self, user_id: hikari.Snowflake | int, amount: int) -> EconomyStatus[bool | int | None]:
            current_balance = await self.get(user_id)
            if current_balance.issucces:
                status = await self.set(user_id, current_balance.data+amount)
                return status
            else:
                return current_balance

        async def sub(self, user_id: hikari.Snowflake | int, amount: int) -> EconomyStatus[bool | int | None]:
            current_balance = await self.get(user_id)
            if current_balance.issucces:
                status = await self.set(user_id, current_balance.data-amount)
                return status
            else:
                return current_balance

    class Characters:
        def __init__(self, db: aiosqlite.Connection, sql: aiosqlite.Cursor | None = None) -> None:
            self._db = db
            self._sql = sql

        async def eat(self, food: Food, character: Character) -> None:
            db = self._db
            self._sql = self._sql or (await db.cursor())
            sql = self._sql
            await sql.execute(
                "UPDATE characters SET hunger = ?, energy = ? WHERE character_id = ?",
                (min(100, character.hunger+food.hunger), min(100, character.energy+food.energy), character.character_id)
            )

        async def get(self, *, user_id: hikari.Snowflake | int | None = None, character_id: int | None = None) -> EconomyStatus[Character | None]:
            db = self._db
            self._sql = self._sql or (await db.cursor())
            sql = self._sql

            if (user_id is None and character_id is not None) or (user_id is not None and character_id is None):
                result = await (await sql.execute(
                    f"""
                    SELECT character_id, user_id, balance, hunger, energy, auto_mode, name, avatar, last_time_worked, STRFTIME('%s', created_at),
                           last_sleep, sleep_until, hunger_notif, sleep_notif
                    FROM characters
                    WHERE {'character_id' if character_id is not None else 'user_id'} = ?
                    AND deleted_at = ?
                    """,
                    ((character_id if character_id is not None else user_id), 0)
                )).fetchone()
            else:
                if user_id is not None and character_id is not None:
                    raise ValueError("user_id or character_id must be None")
                if user_id is None and character_id is None:
                    raise ValueError("user_id or character_id must not be None")

            if result is None:
                return EconomyStatus(False, message=StatusType.CHARACTER_DOESNT_EXISTS)

            data = Character(*result)

            return EconomyStatus(True, data=data)

        async def create_new(self, name: str, user_id: hikari.Snowflake | int, confirm_reset: bool = False) -> EconomyStatus[Character | None]:
            db = self._db
            self._sql = self._sql or (await db.cursor())
            sql = self._sql

            result = await self.get(user_id=user_id)
            deleted = False

            if result.issucces:
                character: Character = result.data
                if time.time()-character.created_at < 10800:
                    return EconomyStatus(False, StatusType.TOO_NEW_A_CHARACTER, data=character)
                if not confirm_reset:
                    return EconomyStatus(False, StatusType.CONFIRMATION_REQUIRED, data=character)
                await sql.execute("UPDATE characters SET deleted_at = ? WHERE character_id = ?", (int(time.time()), character.character_id,))
                deleted = True

            character = Character(0, 0, name=name)
            query = f"""
                INSERT INTO characters (user_id, name, last_sleep{', balance' if deleted else ''})
                VALUES (?, ?, ?{', ?' if deleted else ''})
                """
            parameters = (user_id, character.name, int(time.time()))
            if deleted:
                parameters = parameters + (0,)
            await sql.execute(query, parameters)
            return EconomyStatus(True, data=(await self.get(user_id=user_id)).data)

    class Balance:
        def __init__(self, db: aiosqlite.Connection, sql: aiosqlite.Cursor | None = None) -> None:
            self._db = db
            self._sql = sql

        async def get(self, user_id: hikari.Snowflake | int) -> EconomyStatus[int]:
            db = self._db
            self._sql = self._sql or (await db.cursor())
            sql = self._sql
            balance = await (await sql.execute("""SELECT balance FROM characters WHERE user_id = ? AND deleted_at = ?""", (user_id, 0))).fetchone()
            if balance is None:
                return EconomyStatus(False, message=StatusType.CHARACTER_DOESNT_EXISTS, data=0)
            else:
                return EconomyStatus(True, data=max(round(balance[0], 2), 0))

        async def set(self, user_id: hikari.Snowflake | int, amount: int) -> EconomyStatus[None]:
            db = self._db
            self._sql = self._sql or (await db.cursor())
            sql = self._sql
            balance = await (await sql.execute("""SELECT balance FROM characters WHERE user_id = ? AND deleted_at = ?""", (user_id, 0))).fetchone()
            if balance is None:
                return EconomyStatus(False, message=StatusType.CHARACTER_DOESNT_EXISTS)
            else:
                await sql.execute("""UPDATE characters SET balance = ? WHERE user_id = ? AND deleted_at = ?""", (max(amount, 0), user_id, 0))
                return EconomyStatus(True)

        async def add(self, user_id: hikari.Snowflake | int, amount: int) -> EconomyStatus[int | None]:
            current_balance = await self.get(user_id)
            if current_balance.issucces:
                status = await self.set(user_id, current_balance.data+amount)
                return status
            else:
                return current_balance

        async def sub(self, user_id: hikari.Snowflake | int, amount: int) -> EconomyStatus[int | None]:
            current_balance = await self.get(user_id)
            if current_balance.issucces:
                status = await self.set(user_id, current_balance.data-amount)
                return status
            else:
                return current_balance


class CharacterEngine:
    class ErrorMessages(enum.StrEnum):
        ITS_TOO_LITTLE_TPM = "Слишком мало тиков в минуту!"

    def __init__(self, *, db_path: str, tpm: int = 6, app: hikari.RESTAware, webhook_log: str | None = None) -> None:
        self.tpm = tpm
        self.db_path = db_path
        self.stop_timer: bool = False
        self.cycle_time = []
        self.last_cycle_time = 60/tpm
        self.webhook_log = webhook_log
        self.timer_task: asyncio.Task | None = None
        self.send_query = []
        self.send_query_task: asyncio.Task | None = None
        self.tick_count = 0
        self.tpm_history = []
        self.last_tick_notif = (0, 6)
        self.app = app

    async def start_timer(self) -> tuple[asyncio.Task]:
        self.timer_task = asyncio.create_task(self.timer())
        self.send_query_task = asyncio.create_task(self.send_query_timer())
        return (self.timer_task, self.send_query_task)

    async def send_query_timer(self) -> None:
        async with aiohttp.ClientSession() as session:
            while True:
                if len(self.send_query) > 0:
                    data = self.send_query[0]
                    self.send_query.remove(data)
                    for x in range(10):
                        async with session.post(self.webhook_log, json=data) as response:
                            if response.status == 429:
                                await asyncio.sleep(5)
                            else:
                                break
                await asyncio.sleep(1)

    async def timer(self):
        while True:
            if self.stop_timer:
                self.stop_timer = True
                break
            start = time.perf_counter()
            self.tick_count += 1
            tpm = self.tpm
            tick_delay = 60/tpm
            if len(self.cycle_time) > 25:
                tick_delay += max((sum(self.cycle_time[-25:])/min(len(self.cycle_time), 25))-tick_delay, 0)
            original_tick_delay = 60/tpm

            # start of cycle

            db_path = self.db_path
            async with aiosqlite.connect(db_path) as db:
                sql = await db.cursor()
                results = await (await sql.execute(
                    """
                    SELECT character_id, user_id, balance, hunger, energy, auto_mode, name, avatar, last_time_worked, STRFTIME('%s', created_at),
                           last_sleep, sleep_until, hunger_notif, sleep_notif
                    FROM characters WHERE deleted_at = 0
                    """
                    )).fetchall()
                characters: list[Character] = []
                for result in results:
                    characters.append(Character(*result))
                query = """
                UPDATE characters
                SET hunger = ?, energy = ?, last_sleep = ?, deleted_at = ?, sleep_notif = ?, hunger_notif = ?
                WHERE character_id = ?
                """

                def calc(every: int, hours: float = 24.0) -> float:
                    return every / (hours*60*60/self.last_cycle_time)

                change_list = []
                for character in characters:
                    if character.hunger < 1:
                        data = {
                            "content": f"<@{character.user_id}>"
                        }
                        data["embeds"] = [
                            {
                                "description": "**Ваш персонаж умер от голода!**",
                                "color": info.error_color
                            }
                        ]
                        self.send_query.append(data)
                        change_list.append((
                            character.hunger, character.energy, character.last_sleep,
                            int(time.time()),
                            character.sleep_notif, character.hunger_notif,
                            character.character_id
                        ))
                    elif character.is_sleeping:
                        change_list.append((
                            max(0, character.hunger-calc(5)), min(100, character.energy+calc(50, 3)),
                            time.time(), 0,
                            character.sleep_notif, character.hunger_notif,
                            character.character_id
                        ))
                    else:
                        data = {
                            "content": f"<@{character.user_id}>",
                            "embeds": []
                        }
                        last_sleep = character.last_sleep
                        if character.hunger < 25 and time.time()-character.hunger_notif > 24*60*60:
                            character.hunger_notif = int(time.time())
                            data["embeds"].append(
                                {
                                    "description": "**Ваш персонаж очень голоден!**",
                                    "color": info.error_color
                                }
                            )
                        if time.time()-last_sleep > 36*60*60 and time.time()-character.sleep_notif > 36*60*60:
                            character.sleep_notif = int(time.time())
                            data["embeds"].append(
                                {
                                    "description": "**Ваш персонаж уже не спал больше 36 часов!**",
                                    "color": info.error_color
                                }
                            )
                        if len(data["embeds"]) > 0:
                            self.send_query.append(data)
                        sub_energy = max(0, character.energy-calc(5))
                        if time.time()-last_sleep > 36*60*60:
                            sub_energy = max(0, character.energy-calc(100))
                        change_list.append((
                            max(0, character.hunger-calc(25)), sub_energy,
                            character.last_sleep, 0,
                            character.sleep_notif, character.hunger_notif,
                            character.character_id
                        ))

                await sql.executemany(query, change_list)
                await db.commit()

            # end of cycle

            end = time.perf_counter()
            cycle_time = end-start
            self.cycle_time.append(cycle_time)
            await asyncio.sleep(max(tick_delay-cycle_time, 0))
            self.last_cycle_time = time.perf_counter()-start

            self.tpm_history.append(60/self.last_cycle_time)
            self.tpm_history = self.tpm_history[-100:]
            # print(tpm, (sum(self.tpm_history[-10:]) / 10), round(60/self.last_cycle_time, 5), round(self.last_cycle_time, 5), round(tick_delay, 5), self.tick_count)

            if len(self.tpm_history) > 10 and (sum(self.tpm_history[-10:]) / 10) < 1:
                data = {
                    "content": f"<@{info.developer_id}>"
                }
                data["embeds"] = [
                    {
                        "description": self.ErrorMessages.ITS_TOO_LITTLE_TPM,
                        "title": "Системное оповещение",
                        "color": info.error_color
                    },
                    {
                        "description": (
                            f"**Количество тиков с момента запуска:** {self.tick_count}\n" +
                            f"**Длительность прошлого тика:** {round(self.last_cycle_time*1000)}/{round(original_tick_delay*1000)} мс\n" +
                            f"**Тиков в минуту:** {round(sum(self.tpm_history[-10:]) / 10, 2)}/{tpm}"
                        ),
                        "color": info.error_color
                    }
                ]
                self.send_query.append(data)


def casino(standart_emoji: tuple[str] | str, jackpot_emoji: str, bet: int) -> tuple[list[str], list[list], int]:
    if isinstance(standart_emoji, str):
        standart_emoji = tuple(standart_emoji)
    won_money = 0
    min_random = 0
    max_random = len(standart_emoji)
    random_list = []
    random_func = functools.partial(random.randint, min_random, max_random)
    for x in range(random.randint(7, 11)):
        result_int = [random_func(), random_func(), random_func()]
        result_emoji = []
        for x in result_int:
            result_emoji.append(standart_emoji[x] if x < len(standart_emoji) else jackpot_emoji)
        random_list.append(result_emoji)

    last = random_list[len(random_list)-2]
    if last[0] == jackpot_emoji and last[0] == last[1] == last[2]:
        won_money = bet*5
        print(last)
    elif last[0] == last[1] == last[2]:
        won_money = bet*2
    elif last[0] == last[1] or last[1] == last[2]:
        won_money = bet*1.5

    return last, random_list, won_money


def initialize_database(database: str = '../db/idealight.sqlite'):
    with sqlite3.connect(database) as db:
        sql = db.cursor()

        sql.executescript("""
            CREATE TABLE IF NOT EXISTS sent (
                date TEXT PRIMARY KEY
            );
            CREATE TABLE IF NOT EXISTS calc (
                date TEXT PRIMARY KEY
            );
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type INTEGER,
                value TEXT,
                reason TEXT
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                value_2 TEXT
            );
            CREATE TABLE IF NOT EXISTS points (
                user_id INTEGER PRIMARY KEY,
                points INTEGER
            );
            CREATE TABLE IF NOT EXISTS characters (
                character_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                balance REAL DEFAULT 100,
                hunger REAL DEFAULT 100,
                energy REAL DEFAULT 100,
                auto_mode INTEGER DEFAULT 0,
                name TEXT NOT NULL,
                avatar TEXT,
                deleted_at INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_sleep INTEGER NOT NULL,
                hapiness REAL DEFAULT 100,
                last_time_worked INTEGER DEFAULT 0,
                sleep_until INTEGER,
                hunger_notif INTEGER DEFAULT 0,
                sleep_notif INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS item_store (
                item_id INTEGER PRIMARY KEY UNIQUE,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                type INTEGER DEFAULT 1,
                type_extra TEXT
            );
            CREATE TABLE IF NOT EXISTS inventory (
                character_id INTEGER,
                item_id INTEGER NOT NULL,
                count INTEGER NOT NULL,
                FOREIGN KEY (character_id) REFERENCES characters(character_id),
                FOREIGN KEY (item_id) REFERENCES item_store(item_id)
            );
            CREATE TABLE IF NOT EXISTS bank (
                user_id INTEGER PRIMARY KEY NOT NULL,
                balance REAL DEFAULT 0
            )

            """)
