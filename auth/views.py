from flask import Blueprint, request, jsonify, redirect, url_for
import json
from datetime import datetime, date
from .utils import *
from bson.json_util import dumps
from edgeplusv2_config.common_utils import (
    LocalMongoHelper,
    CacheHelper,
    CloudMongoHelper,user_domain
)


views = Blueprint("views", __name__)



@views.route("/")
def hello_world():
    return "Hello, World!"


@views.route("/login", methods=["POST"])
def login():
    """
    payload
    {
        "user_name":"deepanshu.vishwakarma@lincode.ai",
        "password":"Deep@123"
    }
    response
            {
        "data": {
            "access_token": "ufENaBy7BxJRJtUq2MXGTRrc5TpjvT",
            "inspection_station_id": "64d4eab6bc3026ca570f2f48",
            "refresh_token": "q5IUmPJZMB04rdCH1oJJ5SND0tBVna",
            "role": "admin",
            "user_name": "deepanshu.vishwakarma@lincode.ai"
        },
        "message": 103
    }
    """
    # getting user_name and password fron user as request
    user_name=None
    password = None
    # password=None
    data = json.loads(request.data)
    user_name = data["user_name"]
    password = data["password"]
    

    response = login_user(user_name, password)
    status_code = response.get("message")
    if status_code==103:
        return jsonify(response),200
    elif status_code==101 or status_code==102:
        return jsonify(response),400
    elif status_code==106:
        return jsonify(response),404
    else:
        return jsonify(response),401

@views.route("/logout", methods=["GET"])
def logout():
    """
    payload:
        None
    response:
        {
            {"data":{},"message":103}
        }
    """
    # Checking user is already is login or not
    if isloggedin:
        # getting all mongo and camera container id from local mongo
        response = stop_camera_model_container()
        # if user is loging drop user_details fron local mongo
        LocalMongoHelper().getCollection("user_cred_log").drop()
        LocalMongoHelper().getCollection("workstations").drop()
        status_code = response.get("message")
        if status_code==103:
            return jsonify(response),200
    else:
        return jsonify({"data":{},"message":101})
