import json
import pickle
import redis
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_sse import sse
from flask import Flask


import os

# import cv2
from datetime import datetime

# import numpy as np
from time import sleep
from loguru import logger
import socket

import http.server
import socketserver
# from .camera_class import USBCamera
# from .image_class import Image_process
import threading
import docker
from docker.types import DeviceRequest
import requests
import platform
from pymodbus.client.sync import ModbusTcpClient as MC
from serial.tools import list_ports

f = open("edgeplusv2_config/v2_config.json")
data = json.load(f)
f.close()

LOCAL_MONGO_HOST = data["LOCAL_MONGO_HOST"]
LOCAL_MONGO_PORT = data["LOCAL_MONGO_PORT"]
LOCAL_MONGO_DB = data["LOCAL_MONGO_DB"]

CLOUD_MONGO_HOST = data["CLOUD_MONGO_HOST"]
CLOUD_MONGO_PORT = data["CLOUD_MONGO_PORT"]
CLOUD_MONGO_DB = data["CLOUD_MONGO_DB"]
MONGO_COLLECTION_PARTS = "parts"

LOCAL_REDIS_HOST = data["REDIS_HOST"]
LOCAL_REDIS_PORT = data["REDIS_PORT"]

API_URL = data["API_URL"]

KAFKA_BROKER_URL = data["CLOUD_KAFKA_BROKER_URL"]

MONGO_COLLECTIONS = {MONGO_COLLECTION_PARTS: "parts"}

# MONGO_COLLECTIONS = {MONGO_COLLECTION_PARTS: "parts"}

#############
# def user_domain(email):
#     global domain
#     domain = "livis"
#     domain = email.split("@")[1].split(".")[0]

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, int):
            return str(obj)
        if isinstance(obj, ObjectId):
           return str(obj)
        if isinstance(obj, datetime):
           return obj.isoformat()
        else:
           return obj

def get_free_port():
    sock = socket.socket()
    sock.bind(('', 0))
    # logger.success(sock.getsockname()[1])
    return sock.getsockname()[1]


def start_http_server(port, handler):
    """start the http_server to stream the data"""  
    httpd = socketserver.TCPServer(("", port), handler)
    print(f"Serving at port {port}")
    httpd.serve_forever()

def http_server_for_meta_data_util():
    """
    Run the HTTP server for to access the meta_data
    """

    # Directory name to create and serve
    folder_name = "."

    # Change the working directory to the folder you want to serve
    os.chdir(folder_name)
    port = get_free_port()

    # Start the HTTP server
    Handler = http.server.SimpleHTTPRequestHandler
    print("start")
    server_thread = threading.Thread(target=start_http_server, args=(port, Handler))
    print("end")
    # Start the HTTP server thread
    server_thread.start()

    # Return the server URL
    return f"http://localhost:{port}"



def user_domain(email):
    if email is not None:
        global domain
        domain = "livis"
        domain_parts = email.split("@")
        if len(domain_parts) >= 2:
            domain = domain_parts[1].split(".")[0]
        else:
            # Handle the case where email does not contain '@' character
            print("Error: Invalid email format.")
            domain = None

    else:
        # Handle the case where email is None
        print("Error: Email is None.")
        domain = None

    return domain


def singleton(cls):
    instances = {}

    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]

    return getinstance


@singleton
class CloudMongoHelper:
    client = None

    def __init__(self):
        if not self.client:
            self.client = MongoClient(host=CLOUD_MONGO_HOST, port=CLOUD_MONGO_PORT)
        self.db = self.client[CLOUD_MONGO_DB]
        self.DB = None
        self.db_cname = None

    def getDatabase(self):
        return self.db

    def create_index(self, collection_name, field_name):
        self.getCollection(collection_name).create_index(
            [(field_name, pymongo.TEXT)],
            name="search_index",
            default_language="english",
        )

    def getCollection(
        self, cname, create=False, codec_options=None, domain_override=None
    ):
        # try:
        #     user = get_current_user()
        #     email = user.email
        #     #print("YAHAN PER : : : ", email)
        #     domain = email.split('@')[1].split('.')[0]
        #     #print("YAHAN PER : : : ", domain)
        #     if email:
        #         domain = tldextract.extract(email).domain
        # except:
        #     domain = "lincode"
        domain = "livis"

        domain_override = domain
        _DB = CLOUD_MONGO_DB

        self.DB = self.client[_DB]

        # make it as cname in [LIST OF COMMON COLLECTIONS]
        if cname == "permissions" or cname == "domains":
            pass
        else:
            if domain_override:
                cname = domain_override + cname
            else:
                cname = domain + cname
        # print('collection_name for this request-------' ,cname )

        if cname in MONGO_COLLECTIONS:
            if codec_options:
                # return DB.get_collection(s.MONGO_COLLECTIONS[cname], codec_options=codec_options)
                self.db_cname = self.DB.get_collection(
                    MONGO_COLLECTIONS[cname], codec_options=codec_options
                )
            # return DB[s.MONGO_COLLECTIONS[cname]]
            self.db_cname = self.DB[MONGO_COLLECTIONS[cname]]
        else:
            # return DB[cname]
            self.db_cname = self.DB[cname]
        return self.db_cname


@singleton
class CacheHelper:
    def __init__(self):
        self.redis_cache = redis.StrictRedis(
            host=LOCAL_REDIS_HOST, port=LOCAL_REDIS_PORT, db=0
        )
        print("REDIS CACHE UP!")

    def subscribe(self, key):
        subscribe = self.redis_cache.pubsub(ignore_subscribe_messages = True)
        subscribe.subscribe(key)
        return subscribe.listen()
    
    def publish(self, key, message):
        self.redis_cache.publish(key, message)

    def send_stream(self,data):
        app = Flask(__name__)
        app.config["SSE_REDIS_URL"] = "redis://localhost"

        # print(app.config)
        with app.app_context():
            sse.publish(data, type='publish')


    def get_redis_pipeline(self):
        return self.redis_cache.pipeline()

    def set_json(self, dict_obj):
        try:
            k, v = list(dict_obj.items())[0]
            v = pickle.dumps(v)
            return self.redis_cache.set(k, v)
        except redis.ConnectionError:
            return None

    def get_json(self, key):
        try:
            temp = self.redis_cache.get(key)
            # print(temp)
            if temp:
                try:
                    temp = pickle.loads(temp)
                except:
                    temp = json.loads(temp.decode())
            return temp
        except redis.ConnectionError:
            return None
        return None

    def execute_pipe_commands(self, commands):
        return None


@singleton
class LocalMongoHelper:
    client = None

    def __init__(self):
        if not self.client:
            self.client = MongoClient(host=LOCAL_MONGO_HOST, port=LOCAL_MONGO_PORT)
        self.db = self.client[LOCAL_MONGO_DB]
        self.DB = None
        self.db_cname = None

    def getDatabase(self):
        return self.db

    def create_index(self, collection_name, field_name):
        self.getCollection(collection_name).create_index(
            [(field_name, pymongo.TEXT)],
            name="search_index",
            default_language="english",
        )

    def getCollection(
        self, cname, create=False, codec_options=None, domain_override=None
    ):
        _DB = LOCAL_MONGO_DB
        domain = "lincode"
        self.DB = self.client[_DB]
        if cname == "permissions" or cname == "domains" or cname == "user_details":
            pass
        else:
            domain_override = domain
            if domain_override:
                cname = domain_override + cname
            else:
                cname = domain + cname
        if cname in MONGO_COLLECTIONS:
            if codec_options:
                self.db_cname = self.DB.get_collection(
                    MONGO_COLLECTIONS[cname], codec_options=codec_options
                )
            self.db_cname = self.DB[MONGO_COLLECTIONS[cname]]
        else:
            self.db_cname = self.DB[cname]
        return self.db_cname


@singleton
class ModbusController:
    def __init__(self):
        # uid : unique identification (example: ip address for Modbus TCP and VID:HWID for Modbus ASCII/RTU)
        self.timeout = 1
        self.parity = "E"
        self.stopbits = 1
        self.bytesize = 7
        self.baudrate = 9600
        self.port = 502
        self.deviceId = 0x1

    def connect(self, uid, **kwargs):
        self.controller = self.establish_connection(uid, kwargs)
        if self.controller != None:
            print("Modbus Connection Established")
            return True
        else:
            print("Modbus Connection Failed")
            return False

    def fetch_port(self, uid):
        for port, pid, hwid in sorted(list_ports.comports()):
            try:
                if ((hwid.split())[1].split("="))[1] == uid:
                    print(port)
                    return port
            except e as Exception:
                print(e, ", Exception occured for :", hwid)

    def set(self, key, value):
        if key == "timeout":
            self.timeout = value
        elif key == "parity":
            self.parity = value
        elif key == "stopbits":
            self.stopbits = value
        elif key == "bytesize":
            self.bytesize = value
        elif key == "baudrate":
            self.baudrate = value
        elif key == "port":
            self.port = value
        elif key == "deviceId":
            self.deviceId = value

    def get(self, key):
        if key == "timeout":
            return self.timeout
        elif key == "parity":
            return self.parity
        elif key == "stopbits":
            return self.stopbits
        elif key == "bytesize":
            return self.bytesize
        elif key == "baudrate":
            return self.baudrate

    def establish_connection(self, uid, kwargs):
        if kwargs["mode"] == "TCP":
            client = MC(uid, port=self.port, timeout=self.timeout)
        elif kwargs["mode"] == "ASCII":
            client = MC(
                method="ascii",
                port=self.fetch_port(uid),
                timeout=self.timeout,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                baudrate=self.baudrate,
            )
        status = client.connect()
        if status == True:
            return client

    def write_holding_register(self, address, val):
        try:
            data = self.controller.write_register(address, val, unit=0x1)
            return not data.isError()
        except Exception as e:
            return e

    def read_holding_register(self, address):
        try:
            data = self.controller.read_holding_registers(address, 1, unit=0x1)
            # x = not data.isError()
            if data.isError() == False:
                return data.registers[0]
            else:
                print(data)
                return None
        except Exception as e:
            return e

    def write_multiple_holding_registers(self, start_address, val_list):
        try:
            data = self.controller.write_registers(start_address, val_list, unit=0x1)
            return not data.isError()
        except Exception as e:
            return e

    def read_multiple_holding_registers(self, address, count):
        try:
            data = self.controller.read_holding_registers(address, count, unit=0x1)
            # x = not data.isError()
            if data.isError() == False:
                return data.registers
            else:
                print(data)
                return None
        except Exception as e:
            return e

    def write_coil(self, address, val):
        try:
            data = self.controller.write_coil(address, val, unit=0x1)
            return not data.isError()
        except Exception as e:
            return e

    def read_coil(self, address):
        try:
            data = self.controller.read_coils(address, 1, unit=0x1)
            # x = not data.isError()
            if data.isError() == False:
                return data.bits[0]
            else:
                return None
        except Exception as e:
            return e

    def write_multiple_coils(self, address, val_list):
        try:
            data = self.controller.write_coil(address, val_list, unit=0x1)
            return not data.isError()
        except Exception as e:
            return e

    def read_multiple_coils(self, address, count):
        try:
            data = self.controller.read_coils(address, count, unit=0x1)
            # x = not data.isError()
            if data.isError() == False:
                return data.bits[0]
            else:
                return None
        except Exception as e:
            return e

    def read_discrete_input(self, address):
        try:
            data = self.controller.read_discrete_inputs(address, 1, unit=0x1)
            # x = not data.isError()
            if data.isError() == False:
                return data.bits[0]
            else:
                return None
        except Exception as e:
            return e

    def read_multiple_discrete_inputs(self, address, count):
        try:
            data = self.controller.read_discrete_inputs(address, count, unit=0x1)
            # x = not data.isError()
            if data.isError() == False:
                return data.bits[0]
            else:
                return None
        except Exception as e:
            return e

    def read_input_register(self, address):
        try:
            data = self.controller.read_input_registers(address, 1, unit=0x1)
            # x = not data.isError()
            if data.isError() == False:
                return data.bits[0]
            else:
                return None
        except Exception as e:
            return e

    def read_multiple_input_register(self, address):
        try:
            data = self.controller.read_input_registers(address, 1, unit=0x1)
            # x = not data.isError()
            if data.isError() == False:
                return data.bits[0]
            else:
                return None
        except Exception as e:
            return e

CacheHelper().set_json({"ac_count":0})
