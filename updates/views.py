from flask import Blueprint, request, jsonify, redirect, url_for
import json
from bson.json_util import dumps
import requests
from .utils import *
import socket

views = Blueprint("views", __name__)


@views.route("/")
def hello_world():
    return "Hello, World! --- updates"


@views.route("/update_base_docker_images", methods=["GET"])
def update_base_docker_images():
    """
    Update the docker image in v2_config.json file by using the updated docker image detail get from the  cloudmongo

    Input: None

    Request parameter: None

    Response:
            "successfully updated the docker image"
    """

    headers = {"Content-Type": "application/json"}

    payload = json.dumps({"collection": "docker_images", "document": [{}, {"_id": 0}]})
    api_gateway__mongoDB_url = "http://localhost:5000/api_gateway/get_one_documents"

    # access the mongoDB through api_gateway to get the latest docker_image details
    docker_images_dict_in_json = requests.request(
        "POST", api_gateway__mongoDB_url, headers=headers, data=payload
    )

    # get the data from the api_gateway_mongoDB_url
    docker_images__status_dict = docker_images_dict_in_json.json()

    docker_images_dict = docker_images__status_dict["status"]

    # DIRECT ACCESS: docker_images_list=[docker_image for docker_image in CloudMongoHelper().getCollection("docker_images").find({},{"_id":0})]

    # compare the docker image and update it in the v2_config.json file
    docker_image_name_update = update_docker_image_name_in_config_json(
        docker_images_dict
    )

    return jsonify(docker_image_name_update)
