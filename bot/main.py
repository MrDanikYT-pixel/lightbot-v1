import os
import secrets
import string
import time
import typing
import aioconsole
import logging
import colorama
import requests
import json
from core import encrypt_file, decrypt_file, get_sqlite_files, compare_db, generate_keys
import core
import aiofiles
import traceback
import shutil
import aiofiles.os
import aiohttp
import asyncio
from typing import Dict, Literal
import random


VERSION = 4
CORE_VERSION = 2
SERVER_VERSION = 7

session_id = None
private_key_str = None
public_key_str = None
waiting = True
error400_files = {}
config = {}
on_sync = True
app_running = False
sync_debug = None
allow_start = [False, False, False]
registered = False
server_public_key = ""
reg_ip_dict_type = Dict[Literal["token", "public_key"], str]
registered = False
reg_ip_errors = 0
before_start_sync_complete = False
force_resume_session = False
app_run_time = 0
session_timer_delay = 5
LOGGER: logging.Logger = None
port = random.randint(30000, 65536)

s = requests.Session()
s.mount('http://', core.SourcePortAdapter(port))
s.mount('https://', core.SourcePortAdapter(port))
timeout = aiohttp.ClientTimeout(300)

# with open(config_file, mode='w') as f:
#     f.write(json.dumps(stat, indent=4))


def headers(headers: dict | None = None):
    headers = headers or {}
    additional = {
        'X-Session-ID': session_id,
        "Authorization": (core.encrypt_message(config['token'], server_public_key) if len(server_public_key) > 8 else ""),
        "Version": str(VERSION),
        "Core-Version": str(CORE_VERSION)
    }
    return {**headers, **additional}


class App(core.App):
    def __init__(self, *, wait: bool = False, stop_kwargs: dict[str, typing.Any] = {}, ip: str, port: str) -> None:
        super().__init__(wait=wait, stop_kwargs=stop_kwargs)
        self.ip = f"http://{ip}:{port}"
        ip = f"http://{ip}:{port}"
        self.UPLOAD_DB = f"{ip}/UploadDB"
        self.GET_DB = f"{ip}/GetDB"
        self.GET_DB_LIST = f"{ip}/GetDBList"
        self.AVAILABLE = f"{ip}/Available"
        self.APP_IS_RUNNING = f"{ip}/AppIsRunning"
        self.APP_STOPPED = f"{ip}/AppStopped"
        self.START_SESSION = f"{ip}/StartSession"
        self.RESUME_SESSION = f"{ip}/ResumeSession"
        self.GET_PUBLIC_KEY = f"{ip}/GetPublicKey"


app: App = None
LOGGER: logging.Logger = None


async def send_file(file_path: str, url: str, session: aiohttp.ClientSession) -> bool:
    global registered
    new_file_path = encrypt_file(file_path, server_public_key, "../light/temp/encrypt")
    try:
        data = aiohttp.FormData()
        async with aiofiles.open(new_file_path, 'rb') as f:
            data.add_field('file', await f.read())
            async with session.post(url, data=data, headers=headers()) as response:
                if response.status == 404:
                    LOGGER.error(f"(404) Error uploading file: File {file_path} not found")
                    return False
                elif response.status == 400:
                    LOGGER.error(f"(400) Error uploading file: {await response.text()}")
                    if file_path not in error400_files:
                        error400_files[file_path] = 0
                    error400_files[file_path] += 1
                    return False
                elif response.status == 403:
                    registered = False
                    return False
                response.raise_for_status()
                await aiofiles.os.remove(new_file_path)
                return response
    except requests.HTTPError as e:
        LOGGER.error(f"Error uploading file: {e}")
        return False
    except Exception as e:
        LOGGER.error(f"Error uploading file: {e}")
        raise


async def receive_file(file_path: str, url: str, private_key_str: str, session: aiohttp.ClientSession, temp_decrypt_path: str = "../light/temp/decrypt") -> bool:
    global registered
    try:
        temp_file_path = os.path.join(temp_decrypt_path, os.path.basename(file_path))

        async with session.get(url, headers=headers()) as response:
            if response.status == 404:
                LOGGER.error(f"(404) Error receiving file: File {file_path} not found")
                return False
            elif response.status == 400:
                LOGGER.error(f"(400) Error receiving file: {await response.text()}")
                return False
            elif response.status == 403:
                registered = False
                return False
            response.raise_for_status()
            content = await response.read()
            if not os.path.exists(temp_decrypt_path):
                os.mkdir(temp_decrypt_path)
            async with aiofiles.open(temp_file_path, 'wb') as file:
                await file.write(content)

        decrypt_file(temp_file_path, private_key_str)

        destination_path = os.path.join("../db", os.path.basename(file_path))
        shutil.move(temp_file_path, destination_path)

        return True
    except aiohttp.ClientError as e:
        LOGGER.error(f"Error receiving file: {e}")
        return False
    except Exception as e:
        LOGGER.error(f"Error receiving file: {e}")
        raise


def on_procces_stop(process: core.Procces):
    global app_running, before_start_sync_complete
    LOGGER.error("The application process was terminated unexpectedly")
    before_start_sync_complete = False
    app_running = False
    process.stop(False)


def init(logger: str | None = "light.main", config_file: str | dict = "server.json") -> App:
    global app
    global LOGGER
    global config
    if isinstance(config_file, dict):
        config = config_file
    else:
        config = core.load_config(config_file)

    if logger is not None:
        core.init_logging("INFO", True, True)
        LOGGER = logging.getLogger(logger)
        LOGGER.info("Initialized")
        core.warn_if_not_optimized(False)
    app = App(wait=False, stop_kwargs={"wait": True}, ip=config['ip'], port=config['port'])
    app.process.command = config['command']
    app.process.on_procces_stop = on_procces_stop

    return app


async def sync_timer(time: int = 30):
    global on_sync, before_start_sync_complete
    error_count = 0
    error_msg = False
    if not registered:
        on_sync = False
        for x in range(time):
            if registered:
                break
            await asyncio.sleep(1)
    while True:
        if registered:
            try:
                all_uploaded = 0
                all_with_error = 0
                all_downloaded = 0
                uploaded = 0
                downloaded = 0
                with_errors = 0
                old_status = False
                sync = False
                response = s.get(app.GET_DB_LIST, headers=headers())
                if response.status_code == 200:
                    response_dict = json.loads(response.content.decode().replace("'", '"'))
                    my_dict = get_sqlite_files("../db")
                    compare = compare_db(my_dict, response_dict)
                    download_from_server = compare[0]
                    _upload_to_server = compare[1]
                    upload_to_server = []
                    for x in _upload_to_server:
                        if f"../db/{x}" in error400_files:
                            if error400_files[f"../db/{x}"] > 2:
                                continue
                        upload_to_server.append(x)
                    if download_from_server == [] and upload_to_server == []:
                        pass
                    else:
                        if sync_debug or (sync_debug is None and not app_running):
                            LOGGER.info("Synchronization started")
                        on_sync = True
                        sync = True
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
                        for x in download_from_server:
                            LOGGER.debug(f"Downloading a file {x}")
                            rslt = await retry_request(receive_file, f"../db/{x}", f"{app.GET_DB}/"+x, private_key_str, session)
                            if rslt is False:
                                with_errors += 1
                                all_with_error += 1
                                if old_status is False:
                                    pass
                                else:
                                    old_status = False
                                    downloaded = 0
                                    if sync_debug or (sync_debug is None and not app_running):
                                        LOGGER.info(f"{downloaded} file{'s' if downloaded > 1 else ''} downloaded successfully")
                            else:
                                downloaded += 1
                                all_downloaded += 1
                                if old_status is False:
                                    pass
                                else:
                                    old_status = False
                                    with_errors = 0
                                    LOGGER.error(f"{downloaded} file{'s' if downloaded > 1 else ''} files not downloaded")
                        if not registered:
                            all_with_error = with_errors
                        if with_errors > 0:
                            LOGGER.error(f"{with_errors} file{'s' if with_errors > 1 else ''} files not downloaded")
                        with_errors = 0
                        for x in upload_to_server:
                            if not registered:
                                with_errors = len(upload_to_server)
                                all_with_error += with_errors
                                break
                            LOGGER.debug(f"Uploading a file {x}")
                            rslt = await retry_request(send_file, f"../db/{x}", f"{app.UPLOAD_DB}/"+x, session)
                            if rslt is False:
                                with_errors += 1
                                all_with_error += 1
                                if old_status is False:
                                    pass
                                else:
                                    old_status = False
                                    uploaded = 0
                                    if sync_debug or (sync_debug is None and not app_running):
                                        LOGGER.info(f"{uploaded} file{'s' if uploaded > 1 else ''} uploaded successfully")
                            else:
                                uploaded += 1
                                all_uploaded += 1
                                if old_status is False:
                                    pass
                                else:
                                    old_status = False
                                    with_errors = 0
                                    LOGGER.error(f"{uploaded} file{'s' if uploaded > 1 else ''} files not uploaded")
                        if sync_debug or (sync_debug is None and not app_running):
                            if uploaded > 0:
                                LOGGER.info(f"{uploaded} file{'s' if uploaded > 1 else ''} uploaded successfully")
                            if downloaded > 0:
                                LOGGER.info(f"{downloaded} file{'s' if downloaded > 1 else ''} downloaded successfully")
                            if with_errors > 0:
                                LOGGER.error(f"{with_errors} file{'s' if with_errors > 1 else ''} files not uploaded")
                    with_errors = 0
                    if sync:
                        sync = False
                        if sync_debug or (sync_debug is None and not app_running) or all_downloaded+all_uploaded > 100:
                            LOGGER.info(f"Synchronization complete (Downloaded: {all_downloaded}, Uploaded: {all_uploaded}, Errors: {all_with_error})")
                    error_count = 0
                    error_msg = False
                    before_start_sync_complete = True
            except json.decoder.JSONDecodeError as e:
                LOGGER.error(f"JSONDecodeError: {e.args[0]}")
            except aiohttp.ClientResponseError as e:
                LOGGER.error(f"ClientResponseError: {e}")
            except aiohttp.ClientError as e:
                error_count += 1
                if error_count > 5 and not error_msg:
                    error_msg = True
                    LOGGER.error(f"ConnectionError: {e}")
            except Exception as e:
                LOGGER.error("Sync error!")
                tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                print(tb_str)
            on_sync = False
        else:
            on_sync = False
        await asyncio.sleep(time)


async def retry_request(func, *args, **kwargs):
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            LOGGER.warning(f"Request failed (attempt {attempt}/{max_retries}): {e}")
            await asyncio.sleep(2 ** attempt)
    LOGGER.error(f"Request failed after {max_retries} attempts.")
    return False


async def try_to_register(public_key: str) -> bool:
    global server_public_key, registered, reg_ip_errors, session_id, session_timer_delay
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if session_id is None:
                session_id = ''
                for _ in range(32):
                    session_id += secrets.choice(string.ascii_lowercase + string.digits)
            LOGGER.debug("Trying to get the server's public key...")
            async with session.get(app.GET_PUBLIC_KEY, headers=headers()) as response:
                response.raise_for_status()
                if response.status == 200:
                    server_public_key = (await response.content.read()).decode()
                else:
                    return False
            data: reg_ip_dict_type = {}
            data["public_key"] = public_key
            _headers = {'Content-Type': 'application/json'}
            LOGGER.debug("Registering an IP address on the server...")
            async with session.post(app.START_SESSION, data=json.dumps(data), headers=headers(_headers)) as response:
                response.raise_for_status()
                if response.status == 200:
                    response_dict = json.loads((await response.content.read()).decode().replace("'", '"'))
                    session_timer_delay = response_dict["session_timeout"]
                    if "version" not in response_dict or response_dict["version"] != SERVER_VERSION:
                        LOGGER.warning("The server version is different from the one that is supported, this may cause errors and operational problems")
                    registered = True
                    return True
                else:
                    try:
                        response_dict = json.loads((await response.content.read()).decode().replace("'", '"'))
                    except Exception:
                        response_dict = {"error": (await response.content.read()).decode()}
                    LOGGER.error(response_dict["error"])
                    registered = False
                    return False
    except ConnectionRefusedError as e:
        reg_ip_errors += 1
        if reg_ip_errors == 5:
            LOGGER.error(f"Start session error: {e}")
        return False
    except aiohttp.ClientConnectionError as e:
        reg_ip_errors += 1
        if reg_ip_errors == 5:
            LOGGER.error(f"Start session error: {e}")
        return False
    except aiohttp.ClientResponseError as e:
        reg_ip_errors += 1
        if reg_ip_errors == 5:
            LOGGER.error(f"Start session error: {e}")
        return False
    except Exception as e:
        LOGGER.debug(f"Start session error: {e}")
        raise
    finally:
        if registered:
            if reg_ip_errors >= 5:
                LOGGER.info(f"{colorama.Fore.LIGHTCYAN_EX}Session started successfully after {reg_ip_errors} errors!")
            reg_ip_errors = 0


async def session_timer():
    global force_resume_session
    timer = 0
    while True:
        try:
            timer += 1
            if not registered:
                timer = -1
            if timer >= max(session_timer_delay-30, 1) or force_resume_session:
                response = s.post(app.RESUME_SESSION, headers=headers())
                if response.status_code == 200:
                    force_resume_session = False
                    timer = 0
                if str(response.status_code).startswith('4'):
                    timer = 0
                    force_resume_session = False
                else:
                    timer -= 5
        except requests.ConnectionError:
            timer -= 5
        await asyncio.sleep(1)


async def available_timer(delay: int = 1):
    global app_running, force_resume_session, on_sync, app_running, registered, app_run_time
    error_requests = 0
    error_msg = False
    last_cycle_time = 0
    allow_run = False
    with app as application:
        await application.process.on_procces_stop_task(on_procces_stop)
        while True:
            allow_run = config["do_not_turn_off_the_app_when_the_server_is_not_available"]
            start_cycle_time = time.perf_counter()
            if app_running:
                if app_running:
                    app_run_time += last_cycle_time
            try:
                if not on_sync:
                    if registered:
                        if app_running:
                            response = s.post(app.APP_IS_RUNNING, headers=headers())
                            if response.content != b'True' and response.status_code != 403:
                                app_run_time = 0
                                app_running = False
                                application.process.stop(True)
                                s.post(app.APP_STOPPED, headers=headers())
                                await asyncio.sleep(max(delay - (start_cycle_time - time.perf_counter()), 0.1) + 5)
                        else:
                            app_run_time = 0
                            response = s.get(app.AVAILABLE, headers=headers())
                        if error_msg:
                            LOGGER.info("Connection restored")
                            force_resume_session = True
                            error_msg = False
                        if response.status_code == 403:
                            registered = False
                        else:
                            boolean = False
                            if response.content == b'True':
                                boolean = True
                                if allow_start[0] and allow_start[1] and allow_start[2] and before_start_sync_complete:
                                    application.process.start()
                                    app_running = True
                            allow_start[0] = allow_start[1]
                            allow_start[1] = allow_start[2]
                            allow_start[2] = bool(boolean)
                            error_requests = 0

                    else:
                        resp = await try_to_register(public_key_str)
                        if not resp:
                            if reg_ip_errors >= 5:
                                if allow_run and not app_running:
                                    app_running = True
                                    application.process.start()
                                elif not allow_run:
                                    app_running = False
                                    application.process.stop(True)
                                    LOGGER.fatal("Cannot create a new session, the app is not allowed to run.")
                            # await asyncio.sleep(5)
            except requests.exceptions.ConnectionError:
                error_requests += 1
                if error_requests >= 15 and not error_msg:
                    if not allow_run:
                        LOGGER.fatal(f"The main server is not available{', the app is not allowed to run.' if app_running else ''}")
                        application.process.stop(False)
                        app_running = False
                    else:
                        application.process.start()
                        app_run_time = True
                    error_msg = True
            except Exception as e:
                LOGGER.error("Error!")
                tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                print(tb_str)
            await asyncio.sleep(max(delay - (start_cycle_time - time.perf_counter()), 0.1))
            last_cycle_time = time.perf_counter()-start_cycle_time


async def commands():
    global app_running
    stop = False
    cmd = ""
    with app as application:
        while not stop:
            try:
                cmd = await aioconsole.ainput("")
            except KeyboardInterrupt:
                LOGGER.warning("KeyboardInterrupt")
                stop = True
            match cmd.casefold().strip():
                case "app run":
                    app_running = True
                    application.process.start()
                case "app stop":
                    app_running = False
                    application.process.stop()
                case "exit":
                    application.process.stop()
                    exit("command")
                case "sync debug enable":
                    LOGGER.info("Enabled")
                case "sync debug disable":
                    LOGGER.info("Disabled")
                case "logger debug":
                    LOGGER.level = logging.DEBUG
                    LOGGER.debug("Logging level switched to DEBUG")
                case "logger info":
                    LOGGER.level = logging.INFO
                    LOGGER.info("Logging level switched to INFO")
                case _:
                    LOGGER.error("This command doesnt exist")


async def main_task():
    task1 = asyncio.create_task(sync_timer(30))
    task2 = asyncio.create_task(commands())
    asyncio.create_task(available_timer())
    asyncio.create_task(session_timer())
    await asyncio.gather(task1, task2)


if __name__ == "__main__":
    public_key_str, private_key_str = generate_keys()
    if CORE_VERSION != core.VERSION:
        core.init_logging("INFO", True, True)
        LOGGER = logging.getLogger("light.main")
        LOGGER.critical(f"The core version is different ({CORE_VERSION} != {core.VERSION})")
        exit()
    init("light.main", config_file=f"{core.work_directory}config.json")
    core.prepair_temp()
    try:
        asyncio.run(main_task())
    except KeyboardInterrupt:
        LOGGER.warning("KeyboardInterrupt")
        if app_running:
            s.post(app.APP_STOPPED, headers=headers())
    except SystemExit:
        LOGGER.warning("SystemExit")
        if app_running:
            s.post(app.APP_STOPPED, headers=headers())
