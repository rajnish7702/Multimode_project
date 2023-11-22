from flask import (
    Blueprint,
    request,
    jsonify,
    redirect,
    url_for,
    Response,
    stream_with_context,
)
import json
import time
from .utils import *
import socket
import requests
from bson import ObjectId


views = Blueprint("views", __name__)


@views.route("/")
def hello_world():
    return "Hello, World! --- health_check"


@views.route("/get_system_stats", methods=["GET"])
def get_system_stats():
    """
    Get the system details (CPU,RAM,GPU,MEMORY)

    Input: None

    Request_Parameter: None

    Response:
                    {
                    "CPU": {
                            "core_usage": {
                                    "Core 0": "8.2%",
                                    "Core 1": "9.3%",
                                    "Core 2": "16.5%",
                                    "Core 3": "22.9%",
                                    "Core 4": "5.1%",
                                    "Core 5": "20.0%",
                                    "Core 6": "37.5%",
                                    "Core 7": "25.5%"
                            },
                            "processor_detail": "Intel(R) Core(TM) i5-8365U CPU @ 1.60GHz",
                            "total_cores": 8
                    },
                    "GPU": [],
                    "HDD": {
                            "partition": [
                                    {
                                            "partition_1": {
                                                    "device": "/dev/nvme0n1p2",
                                                    "file_system_type": "ext4",
                                                    "free": "91.35GB",
                                                    "mountpoint": "/",
                                                    "percentage": "58.7%",
                                                    "total_size": "233.18GB",
                                                    "used": "129.91GB"
                                            }
                                    },
                                    {
                                            "partition_2": {
                                                    "device": "/dev/loop1",
                                                    "file_system_type": "squashfs",
                                                    "free": "0.00B",
                                                    "mountpoint": "/snap/brave/257",
                                                    "percentage": "100.0%",
                                                    "total_size": "155.00MB",
                                                    "used": "155.00MB"
                                            }
                                    },

                            ],
                            "total_read": "9.66GB",
                            "total_write": "7.09GB"
                    },
                    "RAM": {
                            "available_memory": "2.38GB",
                            "memory_percentage": "68.50B%",
                            "total_memory": "7.57GB",
                            "used_memory": "4.44GB"
                    }
            },
            {"message":101}

    """

    cpu = cpu_details_utils()
    ram_usage = ram_details_utils()
    gpus = gpu_details_utils()
    disk = disk_details_utils()

    result={"CPU": cpu, "RAM": ram_usage, "HDD": disk, "GPU": gpus}
    response_data={"data":result,"message":123}

    return jsonify(response_data),200


@views.route("/get_container_status", methods=["GET"])
def get_container_stats():
    """
    request

       None

    response:
    {
        "kafka": "Kafka is Running",
        "redis": "Redis is Running ",
        "mongo": "Return Mongo is Running",
        "camera": "camera containers running",
        "model": "model conatiners running"
    }

    """

    # data = json.dumps(request.data)
    def monitor_generator():
        while True:
                kafka_running = check_kafka_producer_server_utils()
                redis_running = check_redis_server_utils()
                mongo_running = check_mongodb_utils()
                model_status =  check_model_utils()
                camera_status=  check_camera_utils()
               
                

                mon_dict = {
                "kafka": kafka_running,
                "redis": redis_running,
                "mongo": mongo_running,
                "model": model_status,
                "camera":camera_status
                }

                response_data = {"data": mon_dict, "message": 124}
                yield "data: {}\n\n".format(json.dumps(response_data), 200)
                time.sleep(10)

    return Response(
     stream_with_context(monitor_generator()), mimetype="text/event-stream"
)