import pymongo
import requests
import json
import docker
import os
import uuid
from datetime import datetime, date
from datetime import datetime
from pymongo import MongoClient
from datetime import datetime, date
from bson.objectid import ObjectId
from edgeplusv2_config.common_utils import (
    CLOUD_MONGO_HOST,
    CLOUD_MONGO_PORT,
    user_domain,
    getting_id,
    LocalMongoHelper,
    CacheHelper,
    CloudMongoHelper,
)


def check_internet():
    """Checks if the internet is available

    request:
      None

    response:
      True: If the internet is available.
      False: If the internet is not available.

    """
    import socket

    timeout = 2
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # presumably
    sock.settimeout(timeout)
    try:
        sock.connect((CLOUD_MONGO_HOST, CLOUD_MONGO_PORT))
    except Exception as e:
        return False
    else:
        sock.close()
        return True


def login_user(user_name, password):
    """
    login user based on user credentials

    request:
        user_name,
        password
    reponse:
        loging success

    """

    # Cheching internate connection
    connect = check_internet()
    if not connect:
        return {"data":{},"message":109}
    else:
        # url for v2 login
        url = "https://v2.livis.ai/api/livis/v2/authorization/login/"

        payload = json.dumps({"user_name": user_name, "password": password})

        headers = {"Content-Type": "application/json"}
        # sending request to v2 login url and getting response

        response = requests.request("POST", url, headers=headers, data=payload)
        print(response.status_code,"....")
        # if getting response code 200 then process
        response = response.json()
        data_login_url = response.get("data")
        if response.get("message")==3:
            id_anchor_json = getting_id()
            # data_login_url = response.get("data")
            # insert_user_utils(data_login_url)
           
            url = "http://127.0.0.1:5000/api_gateway/get_one_documents"
            payload = json.dumps(
                {
                    "collection": "workstations",
                    "document": [{"_id": id_anchor_json}, {}],
                }
            )

            headers = {"Content-Type": "application/json"}

            # sending request data and getting response of one document
            api_geteway_response = requests.request("POST", url, headers=headers, data=payload)
            api_geteway_response = api_geteway_response.json()
            status_api_geteway=api_geteway_response.get("status")
            # storing value into Loacal Mongo
            result = loging_mongo_insert(status_api_geteway,user_name,data_login_url)
            # print(result)
            return result
        elif response.get('message')==1:
            # email is not provided
            # print(response.get('message'))
            return {"data":{},"message":101}
        elif response.get('message')==2:
            # password is not provided
            return {"data":{},"message":102}
        elif response.get("message")==4:
            # user account is lock
            return {"data":{},"message":104}
        elif response.get('message')==5:
            # loging is Failed
            return {"data":{},"message":105}

def loging_mongo_insert(status_api_geteway,user_name,data_login_url):
    # checking staus valuse is commint null or not
    id_anchor_json=read_json_file()
    if status_api_geteway ==None:
        return {"data":{},"message":106}
    # response = CloudMongoHelper().getCollection("workstations").find_one({"_id":ObjectId(id_anchor_json)})
    else:
        inspection_station_id = status_api_geteway.get("_id")
        inspection_station_id = inspection_station_id.get("$oid")
        data={}
        
        data["user_name"]=user_name
        data["inspection_station_id"]=id_anchor_json
        data["role"]="admin"
        data["access_token"]=data_login_url["access_token"]
        data["refresh_token"]=data_login_url["refresh_token"]
        # deleting if frome reponse
      
        del status_api_geteway["_id"]["$oid"]
        # print(inspection_station_id['_id'])
       
     
        is_deleted = status_api_geteway.get("isdeleted")
        print("#############")
        print(is_deleted)
            # comparing anchor json id and inspection_station id if both id is equal then do otherwise return False
            # checking if delete value is Trune or False
        if is_deleted:
            return {"data":{},"message":107}
        else:
            
            insert_local_mongo = status_api_geteway
    
            # checking based on Anchor id if record is present on local mongo return user already present

            insert_local_mongo["_id"]=ObjectId(id_anchor_json)
            user_collection = (
                LocalMongoHelper()
                .getCollection("workstations")
                .find_one({"_id": ObjectId(inspection_station_id)})
            )
            
            # checking if user_collection is none then user can login
            if user_collection is None:
                insert_user_utils(data_login_url)
                LocalMongoHelper().getCollection("workstations").insert_one(
                    insert_local_mongo
                )
                return {"data":data,"message":103}
            else:
                return {"data":{},"message":108}

            


def isloggedin():
    """
    checking user is already loging or not

    request:
        None
    reponse:
        True

    """
    # cheching user is login or not if loging restun true otherwise return False
    is_collection_exists = False
    # checking if any record is present in local mongo
    if LocalMongoHelper().getCollection("user_cred_log").find_one():
        is_collection_exists = True
    return is_collection_exists


def insert_user_utils(result):
    """
    insert new record on LocalMongo

    request:
        user_name,
        password,
        token

    response:
        True
    """
    # inserting data
    # user_details = {"user_name": user_name, "password": password, "token": token}
    if LocalMongoHelper().getCollection("user_cred_log").insert_one(result):
        return True
    else:
        return False


def stop_camera_model_container():
    """
    Stoping Model and Camera Container Running system


    request:
        None

    response:
        container stop
    """

    client = docker.from_env()

    list_container = client.containers.list()

    # getting all container
    all_container_id = []
    # geetting container full id
    for container_id in list_container:
        all_container_id.append(container_id.id)

    # getting model and camera container form Local mongo
    model_camera = (
        LocalMongoHelper()
        .getCollection("container_id_collection")
        .find_one({}, {"_id": 0})
    )

    # getting all model and camera and store into list
    model_and_camera = []

    # if model_camera == None:
    #     return {"data":{},"message":105}
    if model_camera is None:
       pass
    elif model_camera is not None:
        for m_c_container in model_camera:
            model_and_camera.append(model_camera.get(m_c_container))

    # checking container is available or not in local
    # model_camera_container_id = []
    list_container = []
    for status_api_geteway in all_container_id:
        if status_api_geteway in model_and_camera:
            list_container.append(status_api_geteway)
    # stop camera and model container
    for id in list_container:
        container = client.containers.get(id)
        container.stop()
    return {"data":{},"message":103}


def read_json_file():
    with open('edgeplusv2_config/anchor.json', 'r') as openfile:
    
        data = json.load(openfile)
    return data["_id"]