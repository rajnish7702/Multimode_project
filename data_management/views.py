from flask import Blueprint, request, jsonify, redirect, url_for
import json
from bson.json_util import dumps

# from .utils import *
import socket

views = Blueprint("views", __name__)


@views.route("/")
def hello_world():
    return "Hello, World! --- data management"

