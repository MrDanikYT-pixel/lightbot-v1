import json
import logging
import subprocess
import sys
import typing
import shutil
from pathlib import Path
import warnings
from Crypto.Random import get_random_bytes
import hashlib
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
import base64
import aiofiles
import aiosqlite
import colorlog
import rsa
from Crypto.Cipher import PKCS1_OAEP
import os
import pathlib
import asyncio
from asyncio import Task
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager

VERSION = 2
TRACE: typing.Final[int] = logging.DEBUG - 5
logging.addLevelName(TRACE, "TRACE_HIKARI")

_LOGGER = logging.getLogger("light.core")
work_directory = '../light/'


def prepair_temp():
    shutil.rmtree(f"{work_directory}temp", True)
    Path(f"{work_directory}temp").mkdir(parents=True, exist_ok=True)


async def check_db_integrity(db_path):
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("PRAGMA integrity_check;") as cursor:
            result = await cursor.fetchone()
            return result


def init_logging(
    flavor: typing.Union[None, str, int, typing.Dict[str, typing.Any], os.PathLike[str]],
    allow_color: bool,
    force_color: bool, *,
    other_logs: bool = False
) -> None:
    if flavor is None:
        return

    logging.logThreads = other_logs
    logging.logProcesses = other_logs
    logging.logMultiprocessing = other_logs

    warnings.simplefilter("always", DeprecationWarning)
    logging.captureWarnings(True)

    if len(logging.root.handlers) != 0:
        return

    if isinstance(flavor, str):
        path = pathlib.Path(flavor)
        if path.expanduser().exists():
            flavor = path

    if isinstance(flavor, os.PathLike):
        try:
            logging.config.fileConfig(flavor)
        except Exception as ex:
            raise RuntimeError("A problem occurred while trying to setup logging through file configuration") from ex
        return

    if isinstance(flavor, dict):
        try:
            logging.config.dictConfig(flavor)
        except Exception as ex:
            raise RuntimeError("A problem occurred while trying to setup logging through dict configuration") from ex

        if not flavor.get("incremental"):
            return

        flavor = None

    try:
        if supports_color(allow_color, force_color):
            logging.basicConfig(level=flavor, stream=sys.stdout)
            handler = logging.root.handlers[0]
            handler.setFormatter(
                colorlog.formatter.ColoredFormatter(
                    fmt=(
                        "%(log_color)s%(bold)s%(levelname)-1.1s%(thin)s "
                        "%(asctime)23.23s "
                        "%(bold)s%(name)s: "
                        "%(thin)s%(message)s%(reset)s"
                    ),
                    force_color=True,
                )
            )
        else:
            logging.basicConfig(
                level=flavor,
                stream=sys.stdout,
                format=(
                    "%(levelname)-1.1s "
                    "%(asctime)23.23s "
                    "%(name)s: "
                    "%(message)s"
                ),
            )

    except Exception as ex:
        raise RuntimeError("A problem occurred while trying to setup default logging configuration") from ex


_UNCONDITIONAL_ANSI_FLAGS: typing.Final[typing.FrozenSet[str]] = frozenset(("PYCHARM_HOSTED", "WT_SESSION"))
"""Set of env variables which always indicate that ANSI flags should be included."""


def supports_color(allow_color: bool, force_color: bool) -> bool:
    if not allow_color:
        return False

    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    clicolor = os.environ.get("CLICOLOR")
    if os.environ.get("CLICOLOR_FORCE", "0") != "0" or force_color:
        return True
    if clicolor is not None and clicolor != "0" and is_a_tty:
        return True
    if clicolor == "0":
        return False
    if os.environ.get("COLORTERM", "").casefold() in ("truecolor", "24bit"):
        return True

    plat = sys.platform
    if plat == "Pocket PC":
        return False

    if plat == "win32":
        color_support = os.environ.get("TERM_PROGRAM") in ("mintty", "Terminus")
        color_support |= "ANSICON" in os.environ
        color_support &= is_a_tty
    else:
        color_support = is_a_tty

    color_support |= bool(os.environ.keys() & _UNCONDITIONAL_ANSI_FLAGS)
    return color_support


def warn_if_not_optimized(suppress: bool) -> None:
    if __debug__ and not suppress:
        _LOGGER.warning(
            "You are running on optimization level 0 (no optimizations), which may slow down your application. "
            "For production, consider using at least level 1 optimization by passing `-O` to the python "
            "interpreter call"
        )


class SourcePortAdapter(HTTPAdapter):
    def __init__(self, port, *args, **kwargs):
        self._source_port = port
        super(SourcePortAdapter, self).__init__(*args, **kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            source_address=('', self._source_port))


def load_config(path: str, *, async_read: bool = False) -> (typing.Coroutine[typing.Any, typing.Any, dict] | dict):
    def _sync():
        with open(path, mode='r') as f:
            contents = f.read()
            config = json.loads(contents)
        return config

    async def _async():
        async with aiofiles.open(path, mode='r') as f:
            contents = await f.read()
            config = json.loads(contents)
        return config

    if async_read:
        return _async()
    return _sync()


def generate_keys() -> tuple[str, str]:
    """return (public key, private key)"""
    (public_key, private_key) = rsa.newkeys(2048)
    public_key_str = public_key.save_pkcs1().decode('utf8')
    private_key_str = private_key.save_pkcs1().decode('utf8')
    return public_key_str, private_key_str


class Procces():
    def __init__(self) -> None:
        self.process: subprocess.Popen = None
        self.command = ['python', '-O', 'bot.py']
        self.on_procces_stop = None

    def start(self):
        if self.process is not None and self.process.poll() is None:
            pass
        else:
            self.process = subprocess.Popen(self.command)

    def stop(self, wait: bool = False, wait_timeout: float | None = None):
        if self.process is not None:
            self.process.terminate()
            if wait:
                self.process.wait(wait_timeout)
            self.process = None

    async def _on_procces_stop_task_(self, func=None):
        self.on_procces_stop = func or self.on_procces_stop
        while True:
            self.check_process()
            await asyncio.sleep(1)

    async def on_procces_stop_task(self, func=None) -> Task:
        return asyncio.create_task(self._on_procces_stop_task_(func))

    def check_process(self):
        if self.process is not None and self.process.poll() is not None:
            if self.on_procces_stop is not None:
                self.on_procces_stop(self)


class App():
    def __init__(self, *, wait: bool = False, stop_kwargs: dict[str, typing.Any] = {}) -> None:
        self.process = Procces()
        self.stop_kwargs = stop_kwargs
        self.wait = wait

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.wait:
            self.process.process.wait()
        self.process.stop(**self.stop_kwargs)


def calculate_hash(file_path: str) -> str:
    with open(file_path, 'rb') as file:
        bytes = file.read()
        readable_hash = hashlib.sha256(bytes).hexdigest()
    return readable_hash


def get_last_modified_timestamp(file_path: str) -> int:
    return int(os.path.getmtime(file_path))


def get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)


def get_sqlite_files(directory: str) -> dict:
    result = {}
    for file in os.listdir(directory):
        if file.endswith('.sqlite') or file.endswith('.db'):
            file_path = os.path.join(directory, file)
            result[file] = [calculate_hash(file_path), get_last_modified_timestamp(file_path), get_file_size(file_path)]

    result = {k: v for k, v in sorted(result.items(), key=lambda item: item[1][2])}
    return result


def compare_db(offline: dict, online: dict) -> tuple[list, list]:
    download = []
    upload = []

    for file, data in offline.items():
        if file not in online:
            upload.append(file)
        elif online[file][1] > data[1] and online[file][0] != data[0]:
            download.append(file)

    for file, data in online.items():
        if file not in offline:
            download.append(file)
        elif (offline[file][1] > data[1] and offline[file][0] != data[0]):
            upload.append(file)

    return download, upload


def encrypt_file(file_path: str, public_key_str: str, temp_directory: str = "./tmp"):
    tmp_dir = Path(temp_directory)
    tmp_dir.mkdir(exist_ok=True)

    tmp_file_path = tmp_dir / Path(file_path).name
    shutil.copyfile(file_path, tmp_file_path)

    symmetric_key = get_random_bytes(16)

    with open(tmp_file_path, 'rb') as file:
        plaintext_data = file.read()

    public_key = RSA.import_key(public_key_str)
    cipher_rsa = PKCS1_OAEP.new(public_key)
    encrypted_symmetric_key = cipher_rsa.encrypt(symmetric_key)

    cipher_aes = AES.new(symmetric_key, AES.MODE_EAX)
    ciphertext, tag = cipher_aes.encrypt_and_digest(plaintext_data)

    with open(tmp_file_path, 'wb') as file:
        file.write(encrypted_symmetric_key)
        file.write(cipher_aes.nonce)
        file.write(tag)
        file.write(ciphertext)

    return str(tmp_file_path)


def decrypt_file(file_path: str, private_key_str: str):
    with open(file_path, 'rb') as file:
        encrypted_symmetric_key = file.read(256)
        nonce = file.read(16)
        tag = file.read(16)
        ciphertext = file.read()

    private_key = RSA.import_key(private_key_str)
    cipher_rsa = PKCS1_OAEP.new(private_key)
    symmetric_key = cipher_rsa.decrypt(encrypted_symmetric_key)

    cipher_aes = AES.new(symmetric_key, AES.MODE_EAX, nonce=nonce)
    plaintext_data = cipher_aes.decrypt_and_verify(ciphertext, tag)

    decrypted_file_path = file_path.replace('_encrypted', '_decrypted')
    with open(decrypted_file_path, 'wb') as file:
        file.write(plaintext_data)


def encrypt_message(message: str, public_key_str: str) -> str:
    public_key = rsa.PublicKey.load_pkcs1(public_key_str.encode('utf8'))

    encrypted_message = rsa.encrypt(message.encode('utf8'), public_key)

    encrypted_message_str = base64.b64encode(encrypted_message).decode('utf8')

    return encrypted_message_str


def decrypt_message(encrypted_message_str: str, private_key_str: str):
    try:
        private_key = rsa.PrivateKey.load_pkcs1(private_key_str.encode('utf8'))

        encrypted_message = base64.b64decode(encrypted_message_str.encode('utf8'))

        decrypted_message = rsa.decrypt(encrypted_message, private_key).decode('utf8')

        return decrypted_message
    except rsa.DecryptionError:
        return ""
