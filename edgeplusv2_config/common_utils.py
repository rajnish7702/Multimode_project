import json
import pickle
import redis
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
#import cv2
from datetime import datetime
#import numpy as np
from time import sleep
#from .camera_class import USBCamera
#from .image_class import Image_process
import threading
import docker
from docker.types import DeviceRequest
import requests
import platform

f = open("edgeplusv2_config/v2_config.json")
data = json.load(f)
f.close()

a = open("edgeplusv2_config/anchor.json")
anchor = json.load(a)
a.close()

id = anchor["_id"]


def get_inspection_id():
    return id


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

CLOUD_KAFKA_BROKER_URL = data["CLOUD_KAFKA_BROKER_URL"]
LOCAL_KAFKA_BROKER_URL = data["LOCAL_KAFKA_BROKER_URL"]

MONGO_COLLECTIONS = {MONGO_COLLECTION_PARTS: "parts"}

# MONGO_COLLECTIONS = {MONGO_COLLECTION_PARTS: "parts"}

#############
# def user_domain(email):
#     global domain
#     domain = "livis"
#     domain = email.split("@")[1].split(".")[0]

a = open("edgeplusv2_config/anchor.json")
data = json.load(a)
a.close()

id = data["_id"]

def user_domain(email):
    if email is not None:
        global domain
        domain="lincode"
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

def validate_required_data(param_list, data):

    for i in param_list:
        param = data.get(i, None)
        print("param",param)
        if  param is None:
            print("{} not provided".format(i),)
            return False
    return True

def getting_id():
    return data["_id"]

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj




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
    
    def getCollection(self, cname, create=False, codec_options=None, domain_override = None,domain=None):
        # try:
        #     user = get_current_user()
        #     email = user.email
        #     #print("YAHAN PER : : : ", email)
        #     domain = email.split('@')[1].split('.')[0]
        #     #print("YAHAN PER : : : ", domain)
        #     if email:
        #         domain = tldextract.extract(email).domain
        # except:
        domain="lincode"
        
        
        # domain_override = domain
        domain_override="lincode"
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
        print(self.db_cname)
        return self.db_cname


@singleton
class CacheHelper:
    def __init__(self):
        self.redis_cache = redis.StrictRedis(
            host=LOCAL_REDIS_HOST, port=LOCAL_REDIS_PORT, db=0, socket_timeout=1
        )
        print("REDIS CACHE UP!")

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
        domain="lincode"
        
        
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

    def get_data(self, collection_name):
        """
        Input : collection_name
        Returns : data=[list] -> all the data present in the collection.
        Descrition : uses find() method of docker in list comprehension way to fetch all the data.
        """
        collection_name = "livis" + collection_name
        print(collection_name)
        mycoll = self.db[collection_name]
        data = [x for x in mycoll.find()]
        return data

    def collection_checker_util(self, cname):
        _DB = LOCAL_MONGO_DB
        self.DB = self.client[_DB]
        # collectionExists = self.DB.listCollectionNames().into(new ArrayList()).contains(testCollectionName)
        collectionExists = self.DB.list_collection_names()
        # print(collectionExists)
        collection_name = "lincode" + cname
        print('collection_checkr_util_checking the recipie',collection_name,collectionExists)
        if collection_name in collectionExists:
            return True
        else:
            return False


def isloggedin():
    is_collection_exists = False
    if LocalMongoHelper().getCollection("user_details").find_one():
        is_collection_exists = True
    return is_collection_exists


def authenticate_user(email, password, license_key):
    response = 4
    if response == 4:
        add_user(email, password, license_key)
    return response


def add_user(email, password, license_key):
    user_details = {"email": email, "password": password, "license_key": license_key}
    LocalMongoHelper().getCollection("user_details").insert_one(user_details)


def logout_user():
    LocalMongoHelper().getCollection("user_details").drop()


def get_ws():
    workstation = "LINCODETEST-001"
    return workstation


def get_parts_list():
    parts_list = ["kat bolts", "mcb_green"]
    return parts_list


def insert_config_details(data):
    LocalMongoHelper().getCollection("deployment_config").insert_one(data)


def get_exp_list(workstation, part):
    experiemt_list = ["1", "2", "3"]
    return experiemt_list


def get_exp_details(workstation, part, experiment):
    return "workstation_type", "experiment_name", "accuracy", "training_date"


def get_cam_details():
    camera_type = "USB"
    camera_id = 0
    return camera_type, camera_id


def connect_camera(camera_type, camera_id):
    print("Connecting camera...")
    CacheHelper().set_json({"cameraActive": True})
    return "success"


def disconnect_camera():
    print("Disconnecting camera...")
    CacheHelper().set_json({"cameraActive": False})
    return "success"


def default_redis_keys():
    CacheHelper().set_json({"cameraActive": False})


def deploy_experiment():
    print("Deploying Experiment...")
    status = True
    return status


