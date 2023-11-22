from flask import Blueprint, request, jsonify, redirect, url_for, Response
import json
from bson.json_util import dumps
from flask import Flask, Response, Blueprint, request, jsonify, redirect, url_for
import json
from bson.json_util import dumps
from edgeplusv2_config.common_utils import LocalMongoHelper, getting_id
from bson import ObjectId, json_util
import subprocess
import threading
from .utils import *

import socket

views = Blueprint("views", __name__)


@views.route("/abc/")
def hello_world():
    return "Hello, World! --- inspection_station"


@views.route("/update_inspection_station_details/", methods=["POST"])
def update_inspection_station_details():
    """
    http://127.0.0.1:5000/inspection_station/update_inspection_station_details

    Input: None

    Payload : {
            "plc_ip_input": "192.168.1.50",
            "register_input": "2",
            "idle_value_input": "0",
            "active_value_input" : "1",
            "plc_ip_output": "192.168.1.50",
            "register_output": "23",
            "idle_value_output": "2",
            "active_value_output" : "1"
    }

    Response :{
            "_id": {
            "$oid": "64d24bed9ac2b4d676f6076f"
            },
            "workstation_name": "lincode_static",
            "workstation_plant_name": "",
            "workstation_location": "Bangalore",
            "workstation_status": "active",
            "workstation_type": "static",
            "workstation_type_detail": {
            "static_station_name": "Static0001"
            },
            "plc": [
                    {
                            "plc_name": "Plc_01",
                            "communication_protocol": "Modbus TCP/IP",
                            "interface_address": "2.3.4.5"
                    }
            ],
            "camera": [
                    {
                            "camera_name": "Camera_01",
                            "camera_type": "USB Cam",
                            "camera_address": "2"
                    }
            ],
            "use_case": 1,
            "quality_score": 0,
            "recent_user": "Rishabh",
            "last_activity": "",
            "created_by": "rishabh.singh@lincode.ai",
            "created_at": "2023-08-08 19:36:37",
            "isdeleted": false,
            "restart": false,
            "available_indexes": "",
            "active_value_input": "1",
            "active_value_output": "1",
            "idle_value_input": "0",
            "idle_value_output": "2",
            "plc_ip_input": "192.168.1.50",
            "plc_ip_output": "192.168.1.50",
            "register_input": "2",
            "register_output": "23"
            }

    """
    request_params = request.get_json()
    response = update_inspection_station_details_utils(request_params)
    return Response(response)


@views.route("/update_plc_register_values/", methods=["POST"])
def update_plc_register():
    """
    http://127.0.0.1:5000/inspection_station/update_plc_register_values/64d24bed9ac2b4d676f6076f

    Input: None

    Payload : {
            "plc_name": "Plc_01",
            "communication_protocol": "Modbus TCP/IP",
            "interface_address": "2.3.4.5"
    }

    Response :
    {
            "status": "updated",
            "data": {
            "_id": {
                    "$oid": "64d24bed9ac2b4d676f6076f"
            },
            "workstation_name": "lincode_static",
            "workstation_plant_name": "",
            "workstation_location": "Bangalore",
            "workstation_status": "active",
            "workstation_type": "static",
            "workstation_type_detail": {
            "static_station_name": "Static0001"
            },
            "plc": [
                    {
                            "plc_name": "Plc_01",
                            "communication_protocol": "Modbus TCP/IP",
                            "interface_address": "2.3.4.5"
                    }
            ],
            "camera": [
                    {
                            "camera_name": "Camera_01",
                            "camera_type": "USB Cam",
                            "camera_address": "2"
                    }
            ],
            "use_case": 1,
            "quality_score": 0,
            "recent_user": "Rishabh",
            "last_activity": "",
            "created_by": "rishabh.singh@lincode.ai",
            "created_at": "2023-08-08 19:36:37",
            "isdeleted": false,
            "restart": false,
            "available_indexes": "",
            "active_value_input": "1",
            "active_value_output": "1",
            "idle_value_input": "0",
            "idle_value_output": "2",
            "plc_ip_input": "192.168.1.50",
            "plc_ip_output": "192.168.1.50",
            "register_input": "2",
            "register_output": "23"
            }
            }
    """
    request_parameters = request.get_json()
    response = update_plc_register_utils(request_parameters)
    return Response(response)




@views.route("/get_inspection_station_details/", methods=["GET"])
def get_inspection_station_details():
    """
    http://127.0.0.1:5000/inspection_station/get_inspection_station_details

    Input: None

    Payload: {}

    Response: {
        "data": {
            "_id": {
                "$oid": "6433b83539f5254d591db5c0"
            },
            "workstation_name": "sample cobot station",
            "workstation_plant_name": "",
            "workstation_location": "Lincode",
            "workstation_status": "active",
            "workstation_type": "cobot",
            "workstation_type_detail": {
                "cobot_name": "Sample Cobot",
                "cobot_address": "Plant A"
            },
            "plc": [
                {
                    "plc_name": "PLC 1",
                    "communication_protocol": "Modbus TCP",
                    "interface_address": "0.0.0.1"
                }
            ],
            "camera": [
                {
                    "camera_name": "Camera 1",
                    "camera_type": "IP Cam",
                    "camera_address": "0.0.0.1"
                }
            ],
            "use_case": 4,
            "quality_score": 0,
            "recent_user": "",
            "last_activity": "",
            "created_by": "jitendranath.tudu@lincode.ai",
            "created_at": "2023-04-10 12:48:13",
            "isdeleted": True,
            "restart": False,
            "available_indexes": ""
        },
        "message": "48"
    }
    """

    headers = {"Content-Type": "application/json"}
    id_anchor_json = getting_id()
    payload = json.dumps(
        {
            "collection": "workstations",
            "document": [{"_id": id_anchor_json}, {"_id": 0}],
        }
    )

    api_gateway_mongoDB_url = "http://localhost:5000/api_gateway/get_one_documents"

    # Access the MongoDB through api_gateway to get the inspection station details
    workstation_list_json = requests.request(
        "POST", api_gateway_mongoDB_url, headers=headers, data=payload
    )

    user_collection = (
        LocalMongoHelper()
        .getCollection("workstations")
        .find_one({"_id": ObjectId(id_anchor_json)})
    )

    if user_collection is None:
        status = workstation_list_json.json().get("status")
        data = status
        insert_dict = {}
        for key in data:
            insert_dict[key] = data[key]
        insert_dict["_id"] = ObjectId(id_anchor_json)
        LocalMongoHelper().getCollection("workstations").insert_one(insert_dict)

    inspection_list = workstation_list_json.json()

    if "error" in inspection_list:
        # Handle the case where inspection details are not found
        error_message = inspection_list.get("error")
        return Response(json_util.dumps({"error": error_message}), 404)  # Return a 404 Not Found response

    response_data = {"data": inspection_list, "message": 120}
    return Response(json_util.dumps(response_data), 200)



@views.route("/connect_camera", methods=["POST"])
def connect_camera():
    """
    http://127.0.0.1:5000/inspection_station/connect_camera

    Input: None

    Payload : {
            "camera_address": 0,
            "camera_type": "USB Cam"
    }
    Response :
    """

    camera_type = ""
    camera_id = ""
    if request.json is not None and "camera_type" in request.json:
        camera_type = request.json["camera_type"]
    if request.json is not None and "camera_address" in request.json:
        camera_id = request.json["camera_address"]
    lock = threading.Lock()

    return Response(
        connect_camera_utils(camera_type, camera_id, lock),
        200,
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@views.route("/ping/", methods=["POST"])
def ping_camera():
    """

    Payload : {
            "_id":"64e339f5375bc10c59dd17c2"
    }

    Response : {
            {
                    "Camera 1": false
            },
            {
                    "PLC 1": false
            }
    }
    """
   

    headers = {"Content-Type": "application/json"}
    print(headers)
    id = ""
    if request.json is not None and "_id" in request.json:
        id = request.json["_id"]
    payload = json.dumps(
        {"collection": "workstations", "document": [{"_id": id}, {"_id": 0}]}
    )

   
    api_gateway__mongoDB_url = "http://localhost:5000/api_gateway/get_one_documents"
    

    # access the mongoDB through api_gateway to get the inspection station details
    workstation_list_json = requests.request(
        "POST", api_gateway__mongoDB_url, headers=headers, data=payload
    )
    print(workstation_list_json)
    inspection_list = workstation_list_json.json()
    print(inspection_list, "...................")
    cams = inspection_list["status"]["camera"]
    plcs = inspection_list["status"]["plc"]
    result = []
    camera_res = {}
    plc_res = {}

    for cam in cams:
        command = ["ping", "-c", "2", cam["camera_address"]]
        res_cam = subprocess.call(command) == 0
        camera_res[cam["camera_name"]] = res_cam
    result.append(camera_res)

    for plc in plcs:
        command = ["ping", "-c", "2", plc["interface_address"]]
        res_plc = subprocess.call(command) == 0
        plc_res[plc["plc_name"]] = res_plc
    result.append(plc_res)

    
    response_data = {"data": result, "message": 122}
    return Response(json.dumps(response_data), 200)
