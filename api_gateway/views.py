import socket
import json
from bson.json_util import dumps
from flask import Blueprint, request, jsonify, redirect, url_for
from .utils import *


views = Blueprint("views", __name__)


@views.route("/")
def hello_world():
    return "Hello, World! --- api gateway"


@views.route("/get_one_documents", methods=["POST"])
def get_one_documents():
    # request
    """
    taking list of documents and return one documents
    {
        "collection": "user_details",
        "document": [
            {
                "username": "skumar@livis.ai"
            },
            {
            }
        ]
    }
    """

    # response

    """
        {
            "status": {
                "_id": {
                    "$oid": "64f51b2fb9dcbcf57878abd5"
                },
                "available_indexes": "",
                "camera": [
                    {
                        "camera_address": "192.168.0.1",
                        "camera_name": "TopViewCamera",
                        "camera_type": "GIG-E (Baumer)"
                    }
                ],
                "created_at": {
                    "$date": "2023-09-03T23:47:59.519Z"
                },
                "created_by": "shyam@livis.ai",
                "isdeleted": false,
                "last_activity": "",
                "plc": [
                    {
                        "communication_protocol": "Modbus TCP",
                        "direction_control": "Right to Left",
                        "encoder": "Increment",
                        "interface_address": "192.168.1.11",
                        "plc_name": "SeimensPLC-001"
                    }
                ],
                "quality_score": 0.0,
                "recent_user": "Shyam Gupta",
                "restart": false,
                "use_case": 2,
                "workstation_location": "Graz",
                "workstation_name": "magna-is0001",
                "workstation_plant_name": "Ilz",
                "workstation_status": "active",
                "workstation_type": "conveyor",
                "workstation_type_detail": {
                    "conveyor_name": "DornerConveyor"
                }
            }
        }
    """
    # print("inside")
    data = json.loads(request.data)
    collection = data["collection"]
    document = data["document"]
    res = one_document_utils(collection, document)
    return jsonify(res),200


@views.route("/get_all_documents", methods=["POST"])
def get_all_documents():
    # request
    """
    taking list of documents and find all collection and return all value match with documents
    {
        "collection": "user_details",
        "document":[{"user_name":"skumar@livis.ai"},{"_id":0}]
    }
    """
    # response
    """
    {
        "status": [
            {
                "expiry": "18-07-2023",
                "flage": true,
                "last_login": "10/07/2023",
                "license_key": "62161ab05d3e95fd7dff2801",
                "password": "Schinner@123",
                "token": "Token 5071ba6d4f8049b2afe7b286beb0a8823dc3d3e2",
                "user_name": "skumar@livis.ai",
                "username": "skumar@livis.ai"
            }
        ]
    }
    """
    data = json.loads(request.data)
    collection = data["collection"]
    document = data["document"]
    res = all_document_utils(collection, document)
    return jsonify(res),200


@views.route("/insert_document", methods=["POST"])
def insert_document():
    # request
    """
    taking list of collection and insert recored
    {
        "collection": "db",
        "document": [
            {
                "waypoint": "P0",
                "model": {
                    "model": "M5",
                    "url": "https://storage.googleapis.com/test_28001/yolov5m6.pt"
                },
                "camera": {
                    "camera_type": "MP4",
                    "path": "home/Documents/videos/cats.mp4",
                    "camera_name": "C1"
                },
                "features": {
                    "cat": 2
                },
                "defects": {}
            }
        ]
    }
    """
    # response
    """
            {
                "status": "64e49dded0587f2b5554c79b"
            }
    """
    data = json.loads(request.data)
    collection = data["collection"]
    document = data["document"]
    res = insert_document_utils(collection, document)
    return jsonify(res),201


@views.route("/delete_document", methods=["POST"])
def delete_document():
    # request
    """
    taking list of input and get id base on id remove  documents
    {
        "collection": "db",
        "document":[{"_id":"64e49266d9713774f44e6b4c"}]
    }
    """
    # response
    """
        {
            "status": "successfull deleted"
        }
    """
    data = json.loads(request.data)
    collection = data["collection"]
    document = data["document"]
    res = delete_document_util(collection, document)
    return jsonify(res),200


@views.route("/update_document", methods=["POST"])
def update_document():
    # request
    """
    taking list of document and update and return successfull updated
    {
        "collection": "user_details",
        "document":[{"_id":"64def71bf67521847b227561"},{ "$set": { "username": "skumar@livis.ai" } }]
    }
    """

    # response
    """
            {
                "status": "success"
            }
    """
    data = json.loads(request.data)
    collection = data["collection"]
    document = data["document"]
    res = update_documents_util(collection, document)
    return jsonify(res),200
