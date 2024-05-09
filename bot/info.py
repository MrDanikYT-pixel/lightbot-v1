from lastchanges import lll as last_changes, blocklll
import os
import sys
import re
import time
from PIL import ImageFont
start_time2 = time.time()
start_time = int(time.time())

developer = "mrdan__"
developer_id = 476046299691745300
developer_server = (488281306757595147,)
results_of_the_day = 1217885452204507247
vip_servers = (488281306757595147,)
server_invte = "https://discord.gg/2e5SMn73Hw"
server_emoji = "<:idealight:1220137410331938939>"
server_name = "IdeaLight"
version = "1.6.1.2"
current = "1.6.1"
version_timestamp = "<t:1715265480:R>"
_prefix = "%"
_beta_prefix = "()"
beta = False
privacy_policy = "https://idealight.gitbook.io/lightbot/privacy-policy"
terms_of_service = "https://idealight.gitbook.io/lightbot/terms-of-service"
server_default_config = {"limit": 6000, "expire": 0}
XP_COOLDOWN = 60


class Fonts:
    def __init__(self) -> None:
        self.minifont = ImageFont.truetype('./resources/Roboto.ttf', size=19)
        self.minifont_bold = ImageFont.truetype('./resources/Roboto Bold.ttf', size=19)
        self.font = ImageFont.truetype('./resources/Roboto.ttf', size=24)
        self.font_bold = ImageFont.truetype('./resources/Roboto Bold.ttf', size=24)
        self.bigfont = ImageFont.truetype('./resources/Roboto.ttf', size=int(self.font.size * 1.5))
        self.bigfont_bold = ImageFont.truetype('./resources/Roboto Bold.ttf', size=int(self.font.size * 1.5))
        self.verybigfont_bold = ImageFont.truetype('./resources/Roboto Bold.ttf', size=int(self.font.size * 1.7))
        self.verybigfont = ImageFont.truetype('./resources/Roboto.ttf', size=int(self.font.size * 1.7))


regex = {
    "token": re.compile(r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}"),
    "url": re.compile(r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"),
    "date": re.compile(r'\b\d{2}.\d{2}.\d{4}\b'),
    "num": re.compile(r'\d+')
}

__full_version = sys.version
__version_parts = __full_version.split(' ')
python_version = __version_parts[0]

if os.path.exists('../betastatus.py'):
    beta = True
    version = "beta"
    current = "beta"
    vip_servers = developer_server
else:
    beta = False


def prefix() -> str:
    if beta:
        return _beta_prefix
    else:
        return _prefix


wipe = "<t:1683028800:R>"
premium_color = 0x2cd146
global_color = 0x4ffef7
error_color = 0xB22222
help_info_color = 0x92f1d7

premium_cost = """
\n**Цены:**
* **1 Уровень**
 * 1 месяц - 3 $
 * 6 месяцев - 4 $
 * Навсегда - 6 $
* **2 уровень**
 * 1 месяц - 1.5 $
 * 6 месяцев 2 $
 * Навсегда - 2.5 $
* **3 уровень**
 * 1 месяц - 0.25 $
 * 6 месяцев - 0.50 $
 * Навсегда - 1 $

**С 1 и 2 уровнем премиум вы сможете попросить у разработчика уникальные команды себе**

**Если вы не получили премиум в течении 48 часов зайдите на сервер поддержки или напишите разработчику в лс**
"""


user_default_settings = {
    "read_msg_content": {"value": "1"},
    "mention_to_generate": {"value": "1"}
}

CHOICES = {
    "switch": ["Включить", "Выключить"],
    "toptime": ["За все время", "За сегодня", "За вчера", "За последние 7 дней", "За последние 30 дней"]
}


def get_version_info(version: str = current):
    version = version.replace("beta ", "")
    if version != current and version in blocklll:
        return None, None
    elif version in last_changes:
        return last_changes[version], list(last_changes.keys())
    else:
        return None, None
