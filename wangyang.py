# coding: utf-8
import argparse
from flask import Flask, request, Response
from threading import Lock
from jsonrpcserver import dispatch, method, Result, Success, Error
from jsonrpcclient import parse, Ok, request as request2
import requests
import hashlib

class Cache:
    def __init__(self):
        self.storage={}

    def get(self, key):
        return self.storage.get(key,None)

    def set(self, key, value):
        self.storage[key] = value

    def delete(self, key):
        if key in self.storage:
            del self.storage[key]
            return '1'
        return '0'

    def __str__(self):
        return str(self.storage)

app = Flask(__name__)
lock = Lock()
cache = Cache()
selfId = 0
servers = ['http://sdcs0:9527', 'http://sdcs1:9528', 'http://sdcs2:9529']

def getHash(key):
    return hashlib.sha1(key.encode('utf-8')).hexdigest()

def getServerId(key, serversNum):
    hash = getHash(key)
    return int(hash, 16) % serversNum


def execute_rpc_call(server_id, method, params):
    requests.DEFAULT_RETRIES = 5
    s = requests.Session()
    s.keep_alive = False
    response = requests.post(servers[server_id] + "/rpc", json=request2(method, params=params))
    parsed = parse(response.json())
    return parsed.result if isinstance(parsed, Ok) else None

def handle_rpc_call(key, method, value=None):
    target_server = getServerId(key, len(servers))

    if selfId == target_server:
        if method == 'get_rpc':
            return cache.get(key)
        elif method == 'set_rpc':
            with lock:
                cache.set(key, value)
        elif method == 'delete_rpc':
            with lock:
                return cache.delete(key)
    else:
        return execute_rpc_call(target_server, method, {"key": key, "value": value} if value else {"key": key})

@method
def get_rpc(key) -> Result:
    value = handle_rpc_call(key, 'get_rpc')
    return Success(value) if value is not None else Error(-32000, "Key not found at this server")

@method
def set_rpc(key, value) -> Result:
    handle_rpc_call(key, 'set_rpc', value)
    return Success("Set successfully")

@method
def delete_rpc(key) -> Result:
    result = handle_rpc_call(key, 'delete_rpc')
    return Success(result)

@app.route('/<key>')
def get(key):
    value = handle_rpc_call(key, 'get_rpc')
    return {key:value} if value is not None else Response(status=404)

@app.route('/', methods=['POST'])
def set():
    data = request.get_json()
    for key, value in data.items():
        handle_rpc_call(key, 'set_rpc', value)

    return Response(status=200)

@app.route('/<key>', methods=['DELETE'])
def delete(key):
    result = handle_rpc_call(key, 'delete_rpc')
    return result

@app.route('/rpc', methods=['POST'])
def jsonrpc():
    return Response(dispatch(request.get_data().decode()), content_type="application/json")

import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="start setting")
    parser.add_argument('--id', dest='id', type=int)
    parser.add_argument('--port', dest='port', type=int)
    args = parser.parse_args()
    selfId = args.id
    port = int(os.environ.get('port', 5000))
    selfId = int(os.environ.get('id', 5000))

    app.run(host='0.0.0.0', port=port, debug=True)