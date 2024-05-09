def emoji(id: int | str, name: str = "emoji") -> str:
    return f"<:{name}:{id}>"


class Pages:
    first = "<:doubleleft:1220137990907756594>"
    previous = "<:left:1220137997643550730>"
    next = "<:right:1220137999199768686>"
    last = "<:doubleright:1220137992300138496>"
    delete = "<:close:1220139045443735583>"


class Numbers:
    num0 = "<:0_:1220140245169995817>"
    num1 = "<:1_:1220140485700485251>"
    num2 = "<:2_:1220140249565364374>"
    num3 = "<:3_:1220140243416645683>"
    num4 = "<:4_:1220140253558341813>"
    num5 = "<:5_:1220140250983305246>"
    num6 = "<:6_:1220140248139300924>"
    num7 = "<:7_:1220140252245659819>"
    num8 = "<:8_:1220140241864622161>"
    num9 = "<:9_:1220140246730145792>"


class Confirmation:
    confirm = "<:confirm:1220458380074684426>"
    cancel = "<:close:1220139045443735583>"


class ProgressBarTheme:
    filled_right = ...
    filled_left = ...
    filled_center = ...
    empty_right = ...
    empty_left = ...
    empty_center = ...


class ProgressBar:
    class Blue(ProgressBarTheme):
        filled_right = emoji(1220514602773909654)
        filled_center = emoji(1220514611003129977)
        filled_left = emoji(1220514604212293752)
        empty_right = emoji(1220514605399277678)
        empty_center = emoji(1220514609350578226)
        empty_left = emoji(1220514606649315478)

    class Orange(ProgressBarTheme):
        filled_right = emoji(1220515079557091418)
        filled_center = emoji(1220515086972616776)
        filled_left = emoji(1220515081109110894)
        empty_right = emoji(1220515082451161240)
        empty_center = emoji(1220515085366198273)
        empty_left = emoji(1220515084107776060)
