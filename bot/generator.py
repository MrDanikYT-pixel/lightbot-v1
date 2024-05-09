import nltk
import random
import re
import warnings
import asyncio
import functools
import trio
warnings.filterwarnings("ignore", category=DeprecationWarning)

mention_regex = re.compile(r"<@!?(\d{18}|\d{19})>|<@&(\d{18}|\d{19})>")
url_regex = re.compile(r"[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)")

version = "1.3"
version_timestamp = "<t:1698617580:R>"
modes_versions = {"Generate Latest": version, "Generate V1.2": "1.2.6.1", "Generate V1.0": "1.0.2 AD"}
modes = ["Random", "Generate Latest", "Generate V1.2", "Generate V1.0", "off"]

modes_desc = [
    "Random - Рандомные, несвязанные слова из чата",
    "Generate Latest - Генерация рандомного текста из сообщений в чате с помощью алгоритма",
    "Generate V1.2 - Алгоритм версии 1.2.6.1",
    "Generate V1.0 - Алгоритм версии 1.0.2 AD",
    "off - Выключить генерацию"
]
default_mode = "Generate Latest"
if len(modes_desc) != len(modes):
    raise ValueError("modes != modes_desc")
if default_mode not in modes:
    raise ValueError("default_mode not in modes")


async def async_run(func, *args, **kwargs) -> str:
    loop = asyncio.get_running_loop()
    partial_func = functools.partial(func, **kwargs)
    _func = await loop.run_in_executor(None, partial_func, *args)
    return _func


class GeneratorVersions:
    def __init__(self) -> None:
        self.versions = {version: self.default, "1.2.6.1": self.v12, "1.1.14 OP AD 👎": self.v11, "1.0.2 AD": self.v10}

    async def default(
        self,
        text: str,
        minp: int = 2, maxp: int = 14,
        minw: int = 3, maxw: int = 9,
        max_word_len: int = 22,
        delete_mention: bool = False,
        delete_url: bool = True,
        replace_url_to: str = "",
        start_word: str = None,
        split_symbol: str = ","
    ) -> str:
        """Текущий генератор (1.3)"""
        if delete_url:
            text = url_regex.sub(replace_url_to, text)
        tokens1 = nltk.word_tokenize(text, language="russian", preserve_line=True)
        tokens = list(map(lambda word: word[:min(len(word), max_word_len)], tokens1))
        start_words = [
            word for word in tokens
        ]
        phrases = []
        prev_word = None
        prev_prev_word = None
        prev_prev_prev_word = None
        used_phrases = set()
        while len(phrases) < random.randint(minp, maxp):
            phrase = []
            if not len(phrases) > 0 and start_word is not None and not len(phrase) > 0:
                phrase = [start_word]
            while len(phrase) < random.randint(minw, maxw):
                if not phrase:
                    if prev_word and prev_prev_word and prev_prev_prev_word:
                        next_words = [
                            tokens[j + 1] for j in range(len(tokens) - 1)
                            if tokens[j] == prev_word and tokens[j - 1] == prev_prev_word and tokens[j - 2] == prev_prev_prev_word
                        ]
                        if not next_words:
                            next_words = [
                                tokens[j + 1] for j in range(len(tokens) - 1)
                                if tokens[j] == prev_word and tokens[j - 1] == prev_prev_word
                            ]
                            if not next_words:
                                next_words = [
                                    tokens[j + 1] for j in range(len(tokens) - 1)
                                    if tokens[j] == prev_word
                                ]
                    elif prev_word and prev_prev_word:
                        next_words = [
                            tokens[j + 1] for j in range(len(tokens) - 1)
                            if tokens[j] == prev_word and tokens[j - 1] == prev_prev_word
                        ]
                        if not next_words:
                            next_words = [
                                tokens[j + 1] for j in range(len(tokens) - 1)
                                if tokens[j] == prev_word
                            ]
                    elif prev_word:
                        next_words = [
                            tokens[j + 1] for j in range(len(tokens) - 1)
                            if tokens[j] == prev_word
                        ]
                    else:
                        next_words = start_words

                    if next_words:
                        next_word = random.choice(list(nltk.FreqDist(next_words).keys()))
                        if next_word in phrase:
                            next_word = random.choice(start_words)
                        for i in range(100):
                            if next_word == "||__||":
                                next_word = random.choice(list(nltk.FreqDist(next_words).keys()))
                            else:
                                break
                    else:
                        next_word = random.choice(start_words)
                    phrase.append(next_word)
                    prev_prev_prev_word = prev_prev_word
                    prev_prev_word = prev_word
                    prev_word = next_word

                else:
                    prev_word = phrase[-1]
                    if prev_prev_word and prev_prev_prev_word:
                        next_words = [
                            tokens[j + 1] for j in range(len(tokens) - 1)
                            if tokens[j] == prev_word and tokens[j - 1] == prev_prev_word and tokens[j - 2] == prev_prev_prev_word
                        ]
                        if not next_words:
                            next_words = [
                                tokens[j + 1] for j in range(len(tokens) - 1)
                                if tokens[j] == prev_word and tokens[j - 1] == prev_prev_word
                            ]
                            if not next_words:
                                next_words = [
                                    tokens[j + 1] for j in range(len(tokens) - 1)
                                    if tokens[j] == prev_word
                                ]
                    elif prev_prev_word:
                        next_words = [
                            tokens[j + 1] for j in range(len(tokens) - 1)
                            if tokens[j] == prev_word and tokens[j - 1] == prev_prev_word
                        ]
                        if not next_words:
                            next_words = [
                                tokens[j + 1] for j in range(len(tokens) - 1)
                                if tokens[j] == prev_word
                            ]
                    else:
                        next_words = [
                            tokens[j + 1] for j in range(len(tokens) - 1)
                            if tokens[j] == prev_word
                        ]

                    if next_words:
                        next_word = random.choice(list(nltk.FreqDist(next_words).keys()))
                        if next_word in phrase:
                            next_word = random.choice(start_words)
                        for i in range(100):
                            if next_word == "||__||":
                                next_word = random.choice(list(nltk.FreqDist(next_words).keys()))
                            else:
                                break
                    else:
                        next_word = random.choice(start_words)
                    phrase.append(next_word)
                    prev_prev_prev_word = prev_prev_word
                    prev_prev_word = prev_word
                    prev_word = next_word
            new_phrase = ' '.join(phrase)
            if new_phrase not in used_phrases:
                used_phrases.add(new_phrase)
                phrases.append(new_phrase + " ")
        combined_text = ''.join(phrases)
        combined_text = re.sub(r'<:([^:]+):(\d+):>', r'\1:\2', combined_text)
        combined_text = re.sub(
            r'(?<=\w)\s+([^\w\s])|([^\w\s])\s+(?=\w)', r'\1\2', combined_text
        )
        combined_text = combined_text.replace("< ", "<").replace(" >", ">")
        if delete_mention:
            combined_text = mention_regex.sub(" @упоминание ", combined_text)
        combined_text = combined_text.replace("||__||", f"{split_symbol} ").replace(f" {split_symbol} ", f"{split_symbol} ").replace(f"{split_symbol} {split_symbol} ", f"{split_symbol} ")
        combined_text = re.sub(r'([!@#$%^&*()\[\]{};:\'",<.>/?`~]),', r'\1', combined_text)
        combined_text = re.sub(r'(<[^>]*>)|<|>', r'\1', combined_text)
        combined_text = combined_text.replace("<", " <").replace("  <", " <")
        combined_text = combined_text.replace(">", "> ").replace(">  ", "> ")
        combined_text = combined_text.replace("<: ", "<:").replace("<a: ", "<a:")
        combined_text = re.sub(r'<@ ?(\d+)>', r'<@\1>', combined_text)
        combined_text = re.sub(r'<@&(\d+)>', r'<@&\1>', combined_text)
        combined_text = re.sub(r'<#(\d+)>', r'<#\1>', combined_text)
        combined_text = re.sub(r'<@!(\d+)>', r'<@!\1>', combined_text)
        combined_text = combined_text.strip()
        if combined_text.endswith(','):
            combined_text = combined_text[:-1] + '.'

        return combined_text.replace(f"{split_symbol} {split_symbol} ", f"{split_symbol} ")

###################################################################################################################################

    async def v12(
        self, text: str, minp: int = 2, maxp: int = 14, minw: int = 3, maxw: int = 9,
        max_word_len: int = 22, delete_mention: bool = False, delete_url: bool = True,
        replace_url_to: str = "", start_word: str = None, split_symbol: str = ","
    ) -> str:
        if delete_url:
            text = url_regex.sub(replace_url_to, text)
        tokens1 = nltk.word_tokenize(text, language="russian", preserve_line=True)
        tokens = list(map(lambda word: word[:min(len(word), max_word_len)], tokens1))
        start_words = [
            word for word in tokens
            # if not any(c.isdigit() for c in word)
        ]
        phrases = []
        prev_word = None
        prev_prev_word = None
        used_phrases = set()
        while len(phrases) < random.randint(minp, maxp):
            phrase = []
            if not len(phrases) > 0 and start_word is not None and not len(phrase) > 0:
                phrase = [start_word]
            while len(phrase) < random.randint(minw, maxw):
                if not phrase:
                    if prev_word and prev_prev_word:
                        next_words = [
                            tokens[j+1] for j in range(len(tokens)-1)
                            if tokens[j] ==
                            prev_word and tokens[j-1] == prev_prev_word
                        ]
                    elif prev_word:
                        next_words = [
                            tokens[j+1] for j in range(len(tokens)-1)
                            if tokens[j] == prev_word
                        ]
                    else:
                        next_words = start_words
                    if next_words:
                        next_word = random.choice(list(nltk.FreqDist(next_words).keys()))
                        if next_word in phrase:
                            next_word = random.choice(start_words)
                        for i in range(100):
                            if next_word == "||__||":
                                next_word = random.choice(list(nltk.FreqDist(next_words).keys()))
                            else:
                                break
                    else:
                        next_word = random.choice(start_words)
                    phrase.append(next_word)
                    prev_prev_word = prev_word
                    prev_word = next_word

                else:
                    prev_word = phrase[-1]
                    if prev_prev_word:
                        next_words = [
                            tokens[j+1] for j in range(len(tokens)-1)
                            if tokens[j] == prev_word
                            and tokens[j-1] == prev_prev_word
                        ]
                    else:
                        next_words = [
                            tokens[j+1] for j in range(len(tokens)-1)
                            if tokens[j] == prev_word
                        ]
                    if next_words:
                        next_word = random.choice(list(nltk.FreqDist(next_words).keys()))
                        if next_word in phrase:
                            next_word = random.choice(start_words)
                        for i in range(100):
                            if next_word == "||__||":
                                next_word = random.choice(list(nltk.FreqDist(next_words).keys()))
                            else:
                                break
                    else:
                        next_word = random.choice(start_words)
                    phrase.append(next_word)
                    prev_prev_word = prev_word
                    prev_word = next_word
            new_phrase = ' '.join(phrase)
            if new_phrase not in used_phrases:
                used_phrases.add(new_phrase)
                phrases.append(new_phrase+" ")
        combined_text = ''.join(phrases)
        combined_text = re.sub(r'<:([^:]+):(\d+):>', r'\1:\2', combined_text)
        combined_text = re.sub(
            r'(?<=\w)\s+([^\w\s])|([^\w\s])\s+(?=\w)', r'\1\2', combined_text
        )
        combined_text = combined_text.replace("< ", "<").replace(" >", ">")
        if delete_mention:
            combined_text = mention_regex.sub(" @упоминание ", combined_text)
        combined_text = combined_text.replace("||__||", f"{split_symbol} ").replace(f" {split_symbol} ", f"{split_symbol} ").replace(f"{split_symbol} {split_symbol} ", f"{split_symbol} ")
        combined_text = re.sub(r'([!@#$%^&*()\[\]{};:\'",<.>/?`~]),', r'\1', combined_text)
        combined_text = re.sub(r'(<[^>]*>)|<|>', r'\1', combined_text)
        combined_text = combined_text.replace("<", " <").replace("  <", " <")
        combined_text = combined_text.replace(">", "> ").replace(">  ", "> ")
        combined_text = combined_text.replace("<: ", "<:").replace("<a: ", "<a:")
        combined_text = re.sub(r'<@ ?(\d+)>', r'<@\1>', combined_text)
        combined_text = re.sub(r'<@&(\d+)>', r'<@&\1>', combined_text)
        combined_text = re.sub(r'<#(\d+)>', r'<#\1>', combined_text)
        combined_text = re.sub(r'<@!(\d+)>', r'<@!\1>', combined_text)
        if combined_text.endswith(','):
            combined_text = combined_text[:-1] + '.'

        return combined_text.replace(f"{split_symbol} {split_symbol} ", f"{split_symbol} ")

###################################################################################################################################

    async def v11(
            self,
            text: str, minp: int = 2, maxp: int = 14, minw: int = 3, maxw: int = 9,
            max_word_len: int = 22, delete_mention: bool = False, delete_url: bool = True,
            replace_url_to: str = "", start_word: str = "",
            split_symbol: None = None) -> str:
        text = text.replace("||__||", "")
        if delete_url:
            text = url_regex.sub(replace_url_to, text)
        tokens1 = nltk.word_tokenize(text, language="russian", preserve_line=True)
        tokens = list(map(lambda word: word[:min(len(word), max_word_len)], tokens1))

        start_words = [
            word for word in tokens
            if not any(c.isdigit() for c in word)
        ]
        phrases = []
        prev_word = None
        prev_prev_word = None
        used_phrases = set()
        while len(phrases) < random.randint(minp, maxp):
            phrase = []
            if not len(phrases) > 0 and start_word is not None and not len(phrase) > 0:
                phrase = [start_word]
            while len(phrase) < random.randint(minw, maxw):
                if not phrase:
                    if prev_word and prev_prev_word:
                        next_words = [
                            tokens[j+1] for j in range(len(tokens)-1)
                            if tokens[j] ==
                            prev_word and tokens[j-1] == prev_prev_word
                        ]
                    elif prev_word:
                        next_words = [
                            tokens[j+1] for j in range(len(tokens)-1)
                            if tokens[j] == prev_word
                        ]
                    else:
                        next_words = start_words
                    if next_words:
                        next_word = nltk.FreqDist(next_words).most_common(1)[0][0]
                    else:
                        next_word = random.choice(start_words)
                    phrase.append(next_word)
                    prev_prev_word = prev_word
                    prev_word = next_word
                else:
                    prev_word = phrase[-1]
                    if prev_prev_word:
                        next_words = [
                            tokens[j+1] for j in range(len(tokens)-1)
                            if tokens[j] == prev_word
                            and tokens[j-1] == prev_prev_word
                        ]
                    else:
                        next_words = [
                            tokens[j+1] for j in range(len(tokens)-1)
                            if tokens[j] == prev_word
                        ]
                    if next_words:
                        next_word = nltk.FreqDist(next_words).most_common(1)[0][0]
                    else:
                        next_word = random.choice(start_words)
                    phrase.append(next_word)
                    prev_prev_word = prev_word
                    prev_word = next_word
            new_phrase = ' '.join(phrase)
            if new_phrase not in used_phrases:
                used_phrases.add(new_phrase)
                phrases.append(new_phrase+" ")
        combined_text = ''.join(phrases)
        combined_text = re.sub(r'<:([^:]+):(\d+):>', r'\1:\2', combined_text)
        combined_text = re.sub(
            r'(?<=\w)\s+([^\w\s])|([^\w\s])\s+(?=\w)', r'\1\2', combined_text
        )
        combined_text = re.sub(r'<@ ?(\d+)>', r'<@\1>', combined_text)
        combined_text = re.sub(r'<@&(\d+)>', r'<@&\1>', combined_text)
        combined_text = re.sub(r'<#(\d+)>', r'<#\1>', combined_text)
        combined_text = re.sub(r'<@!(\d+)>', r'<@!\1>', combined_text)
        combined_text = combined_text.replace("< ", "<").replace(" >", ">")
        if delete_mention:
            combined_text = mention_regex.sub(" @упоминание ", combined_text)

        return combined_text

###################################################################################################################################

    async def v10(
            self,
            text: str, minp: int = 2, maxp: int = 14, minw: int = 3, maxw: int = 9,
            max_word_len: int = 22, delete_mention: None = None, delete_url: bool = True,
            replace_url_to: str = "", start_word: str = "",
            split_symbol: None = None) -> str:
        text = text.replace("||__||", "")
        if delete_url:
            text = url_regex.sub(replace_url_to, text)
        tokens = nltk.word_tokenize(text, language="russian")
        tokens = list(map(lambda word: word[:min(len(word), max_word_len)], tokens))
        start_words = [word for word in tokens if not any(c.isdigit() for c in word)]
        phrases = []

        for i in range(random.randint(minp, maxp)):
            phrase = []
            if not len(phrases) > 0 and start_word is not None and not len(phrase) > 0:
                phrase = [start_word]
            while len(phrase) < random.randint(minw, maxw):
                if not phrase:
                    word = random.choice(start_words)
                else:
                    prev_word = phrase[-1]
                    next_words = [tokens[j+1] for j in range(len(tokens)-1) if tokens[j] == prev_word]
                    if next_words:
                        next_word = max(set(next_words), key=next_words.count)
                    else:
                        next_word = random.choice(start_words)
                    word = next_word
                phrase.append(word)

            phrases.append(' '.join(phrase))

        combined_text = ' '.join(phrases)
        if delete_mention:
            combined_text = mention_regex.sub(" @упоминание ", combined_text)

        return combined_text


async def async_combine_common_words(text: str, *args, version: str = "auto", return_version: bool = False, **kwargs) -> str | tuple:
    """Для разделения сообщений используйте ||__||"""
    text = text.strip()
    generator = GeneratorVersions()
    generator_version: str = globals()["version"]
    if version is None or version == "auto":
        version = generator_version
    if version not in generator.versions:
        print(f"Версии генератора {version} не существует")
        return f"Версии генератора {version} не существует"
    if return_version:
        return ((await generator.versions[version](text, *args, **kwargs)), version)
    else:
        return await generator.versions[version](text, *args, **kwargs)


def random_words(text: str):
    tokens = nltk.word_tokenize(text)
    random_tokens = random.sample(tokens, random.randint(10, 20))
    random_words = " ".join([token.lower() for token in random_tokens if token.isalpha()])
    return random_words


def combine_common_words(*args, **kwargs) -> str:
    result = trio.run(async_combine_common_words, *args, **kwargs)
    return result
