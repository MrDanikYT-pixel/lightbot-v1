# from flask import Flask, request, send_file
import quart_flask_patch
import asyncio
import os
from core import get_sqlite_files, encrypt_file, decrypt_file, generate_keys
import core
from quart import Quart, abort, request, send_file, jsonify
import main
# import aiofiles.os
import shutil
import time
import aiosqlite
from typing import Union, Dict, List, Literal
import logging

start_time = time.time()

app = Quart(__name__)
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024

VERSION = 7
CORE_VERSION = 2
MIN_CLIENT_VERSION = 4

working_files = {}
sessions_dict_type = Dict[Literal['id', 'keys', 'priority'], Union[List, Dict[str, str], Dict[str, int]]]
sessions: sessions_dict_type = {"id": [], "keys": {}, "priority": {}}
id_keys = {}
waiting = {}
running_on = [9999, 0]
wait_to_stop = 0
timer_delay = 5

config = core.load_config(f"{core.work_directory}config.json")
mainapp = main.init(None, config)
LOGGER: logging = None


class Flask(quart_flask_patch.Flask):
    ...


def del_session(session_id: str, reason: str = "no reason"):
    priority = "unknown"
    if session_id in sessions['id']:
        sessions['id'].remove(session_id)
    if session_id in sessions['keys']:
        del sessions['keys'][session_id]
    if session_id in sessions['priority']:
        priority = str(sessions['priority'][session_id])
        del sessions['priority'][session_id]
    if session_id in id_keys:
        del id_keys[session_id]
    if session_id in waiting:
        for x in waiting.keys():
            if waiting[x][0] != session_id:
                continue
            del waiting[x]
    LOGGER.info(f"Session {session_id}(priority: {priority}) was deleted. reason: {reason}")


async def remove_obsolete_keys_and_sessions():
    global sessions, id_keys, waiting
    wait_time = config["session_timeout"]

    for x in sessions['id']:
        if x not in id_keys:
            del_session(x, "There are no keys for this ID")
            continue
        if x in id_keys:
            if id_keys[x][2]+wait_time < int(time.time()):
                del_session(x, "Session expired")
            elif id_keys[x][3]+86400 < int(time.time()):
                del_session(x, "A session that was created more than 24 hours ago must be recreated")


async def generate_id_keys(session_id: str):
    global id_keys
    await remove_obsolete_keys_and_sessions()
    if session_id not in id_keys:
        public_key_str, private_key_str = generate_keys()
        id_keys[session_id] = [public_key_str, private_key_str, int(time.time()), int(time.time())]


async def timer(delay: float):
    global timer_delay
    timer_delay = delay
    while True:
        await remove_obsolete_keys_and_sessions()
        await asyncio.sleep(timer_delay)


@app.route('/GetPublicKey', methods=['GET'])
async def get_public_key():
    session_id = request.headers.get('X-Session-ID')
    if session_id is None:
        abort(400, "")
    await generate_id_keys(session_id)
    return id_keys[session_id][0], 200


@app.route('/StartSession', methods=['POST'])
async def start_session():
    client_version = request.headers.get('Version')
    client_core_version = request.headers.get('Core-Version')
    if client_version is None or client_core_version is None or not str(client_version).isdigit():
        return jsonify({"success": False, "error": "client or core versions are not specified in headers"}), 400
    if int(client_version) < MIN_CLIENT_VERSION:
        return jsonify({"success": False, "error": "This version is not supported"}), 400
    if client_core_version != str(CORE_VERSION):
        return jsonify({"success": False, "error": "The core version is different"}), 400
    session_id = request.headers.get('X-Session-ID')
    token = request.headers.get('Authorization')
    if session_id is None or token is None:
        return jsonify({"success": False, "error": "invalid session id or token"}), 400
    data: main.reg_id_dict_type = await request.get_json()
    token = core.decrypt_message(token, id_keys[session_id][1])
    if token in config['priority']:
        sessions['id'].append(session_id)
        sessions['keys'][session_id] = data['public_key']
        sessions['priority'][session_id] = config["priority"][token]
        return jsonify({
            "success": True, "priority": config["priority"][token],
            "session_timeout": config["session_timeout"],
            "version": VERSION}), 200
    else:
        return jsonify({"success": False, "error": "Invalid Token"}), 403


@app.route('/ResumeSession', methods=['POST'])
async def resume_session():
    session_id = request.headers.get('X-Session-ID')
    token = request.headers.get('Authorization')
    if session_id in sessions['id']:
        if session_id is None or token is None:
            return jsonify({"success": False, "error": "invalid session id or token"}), 400
        token = core.decrypt_message(token, id_keys[session_id][1])
        if token in config['priority']:
            if session_id in id_keys:
                id_keys[session_id][2] = int(time.time())
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": "Invalid Token"}), 403
    else:
        abort(403, "Invalid session")


@app.route('/Available', methods=['GET', 'POST'])
async def available():
    global waiting, wait_to_stop
    session_id = request.headers.get('X-Session-ID')
    if session_id in sessions['id']:

        priority = sessions["priority"][session_id]

        temp_list = []
        temp_list.append(session_id)
        temp_list.append(int(time.time()))
        waiting[priority] = temp_list
        waiting = dict(sorted(waiting.items()))
        run = False
        available_to_run = []
        for x in waiting:
            timestamp = waiting[x][1]
            if int(time.time())-timestamp < 60:
                available_to_run.append(x)
        if int(time.time())-running_on[1] > 300:
            run = True
        elif running_on[0] > priority:
            wait_to_stop = running_on[0]
            run = False
        if run and int(time.time())-start_time < 60:
            run = False
        if run:
            for x in available_to_run:
                if int(x) < int(priority):
                    run = False
        return str(run)
    else:
        abort(403, "Invalid session")


@app.route('/AppIsRunning', methods=['POST'])
async def appisrunning():
    global running_on, waiting, wait_to_stop
    session_id = request.headers.get('X-Session-ID')
    if session_id in sessions['id']:
        priority = sessions["priority"][session_id]

        temp_list = []
        temp_list.append(session_id)
        temp_list.append(int(time.time()))
        waiting[priority] = temp_list
        waiting = dict(sorted(waiting.items()))

        if running_on[0] != 9999 and int(time.time())-running_on[1] < 300:
            if running_on[0] < priority:
                print(running_on, priority, 'a')
                return str(False)
            elif running_on[0] > priority:
                wait_to_stop = running_on[0]
                print(running_on, priority, 'b')
                return str(False)
        running_on[0] = priority
        running_on[1] = int(time.time())
        if priority == wait_to_stop:
            return str(False)
        return str(True)
    else:
        abort(403, "Invalid session")


@app.route('/AppStopped', methods=['POST'])
async def appstopped():
    global wait_to_stop, running_on
    session_id = request.headers.get('X-Session-ID')
    if session_id in sessions['id']:
        priority = sessions["priority"][session_id]
        if wait_to_stop == priority:
            wait_to_stop = 0
        if running_on[0] == priority:
            running_on[1] = 0
        return 'ok'
    else:
        abort(403, "Invalid session")


@app.route('/GetDBList', methods=['GET'])
async def get_db_list():
    session_id = request.headers.get('X-Session-ID')
    if session_id in sessions['id']:
        directory = '../light/db'
        return jsonify(get_sqlite_files(directory))
    else:
        abort(403, "Invalid session")


@app.route('/UploadDB/<filename>', methods=['POST'])
async def upload_db(filename):
    session_id = request.headers.get('X-Session-ID')
    token = request.headers.get('Authorization')
    if session_id in sessions['id']:
        token = core.decrypt_message(token, id_keys[session_id][1])
        if token not in config['priority']:
            return "Invalid token", 403
        if session_id in id_keys:
            id_keys[session_id][2] = int(time.time())
        file = (await request.files)['file']
        directory = '../light/db/'
        temp_directory = "../light/temp/decrypt"
        if filename in working_files:
            for x in range(100):
                if filename not in working_files:
                    break
                await asyncio.sleep(0.01)
            if filename in working_files:
                return "File locked", 500
        working_files[filename] = 1
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
            if not os.path.exists(temp_directory):
                os.makedirs(temp_directory)
            file_path = os.path.join(temp_directory, filename)
            await file.save(file_path)
            try:
                decrypt_file(file_path, id_keys[session_id][1])
                integrity = await core.check_db_integrity(file_path)
                if integrity == ('ok',):
                    shutil.move(file_path, os.path.join(directory, filename))
                    # await aiofiles.os.remove(file_path)
                else:
                    return "db file failed integrity check", 400
            except ValueError as e:
                return str(e.args[0]), 400
            except aiosqlite.DatabaseError as e:
                return str(e.args[0]), 400

            return 'File uploaded and decrypted successfully'
        finally:
            del working_files[filename]
    else:
        return "Invalid session", 403


@app.route('/GetDB/<filename>', methods=['GET'])
async def get_db(filename):
    session_id = request.headers.get('X-Session-ID')
    token = request.headers.get('Authorization')
    if session_id in sessions['id']:
        token = core.decrypt_message(token, id_keys[session_id][1])
        if token not in config['priority']:
            return "Invalid token", 403
        if session_id in id_keys:
            id_keys[session_id][2] = int(time.time())
        try:
            file_path = os.path.join('../light/db', filename)
            new_file_path = encrypt_file(file_path, sessions['keys'][session_id], "../light/temp/encrypt")
        except FileNotFoundError:
            return "NotFound", 404
        response = await send_file(new_file_path, as_attachment=True, mimetype='application/octet-stream')
        return response
    else:
        return "Invalid session", 403


@app.route('/Ping', methods=['GET'])
async def ping():
    return "Pong!", 200


async def main_task():
    import ipaddress
    import socket
    LOGGER.info("Initialized")

    ip = ipaddress.IPv4Address(config["ip"])
    host = "0.0.0.0"
    if ip.is_global:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((str(ip), int(config["port"])))
            s.close()
            host = str(ip)
        except OSError as e:
            LOGGER.error(f"OSError occurred: {e}")
            LOGGER.error(f"IP address {ip} is not available")
            LOGGER.error("Trying to bind to a different host")
            host = "0.0.0.0"
    else:
        if host != "0.0.0.0" and host != "127.0.0.1":
            LOGGER.error(f"IP address {ip} is not global")
            LOGGER.error("Trying to bind to a different host")
        host = "0.0.0.0"

    quart_task = asyncio.create_task(app.run_task(debug=False, port=int(config["port"]), host=host))
    asyncio.create_task(timer(5))
    await asyncio.gather(quart_task)


if __name__ == '__main__':
    core.prepair_temp()
    core.init_logging(logging.INFO, True, True, other_logs=True)
    LOGGER = logging.getLogger("light.server")
    core.warn_if_not_optimized(False)
    if CORE_VERSION != core.VERSION:
        LOGGER.critical("the core version is different")
        exit()
    asyncio.run(main_task())
