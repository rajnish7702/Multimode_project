from edgeplusv2_config.common_utils import CacheHelper, LocalMongoHelper, user_domain
from pymongo import MongoClient
from kafka.errors import KafkaTimeoutError
from kafka import KafkaProducer
import redis
import socket

import requests
from zipfile import ZipFile
from bson import ObjectId
import zipfile
import os
import glob
from edgeplusv2_config.common_utils import (
    CLOUD_MONGO_HOST,
    CLOUD_MONGO_PORT,
    LOCAL_KAFKA_BROKER_URL,
    CLOUD_KAFKA_BROKER_URL,
    LOCAL_REDIS_HOST,
    LOCAL_REDIS_PORT,
    LOCAL_MONGO_HOST,
    LOCAL_MONGO_PORT,
)
import cpuinfo
import GPUtil
import psutil
from bson.json_util import dumps
import docker
from kafka import KafkaAdminClient


def check_kafka_producer_server_utils():
    """
    Check the Kafka container health.

    Arguments: None

    Response:
        "Kafka is Running" if Kafka is reachable, else "Kafka is not Running"
    """

    kafka_broker_urls = [LOCAL_KAFKA_BROKER_URL, CLOUD_KAFKA_BROKER_URL]

    for broker_url in kafka_broker_urls:
        try:
            producer = KafkaProducer(bootstrap_servers=broker_url)

            # Try sending a test message to ensure the server is running
            # producer.send('test-topic', b'Test message')
            # producer.send('Jim_Topic', key=b'message-two', value=b'This is Kafka-Python')
            producer.flush()
            producer.close()
            return True
        except KafkaTimeoutError:
            pass  # Try the next broker URL

    return "Kafka is not Running"


def check_redis_server_utils():
    """
    check the redis container health

    Arguments: None

    Response:
            "Redis is Running"
    """

    try:
        # Connect to Redis server
        r = redis.Redis(host=LOCAL_REDIS_HOST, port=LOCAL_REDIS_PORT)

        # Send a test command to Redis server
        response = r.ping()

        if response:
            return True 
        else:
            return False
    except redis.ConnectionError:
        # print("Could not connect to Redis server")
        return "Could not connect to Redis server."


def check_mongodb_utils():
    """
    check the local_mongoDB health

    Arguments: None

    Response:
            "Mongo is Running"
    """
    try:
        client = MongoClient(
            LOCAL_MONGO_HOST, LOCAL_MONGO_PORT, serverSelectionTimeoutMS=2000
        )
        client.server_info()  # This will trigger a connection attempt
        return True
    except Exception:
        return False


def get_size_utils(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'

    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


def cpu_details_utils():
    """
    Get the CPU details

    Arguments: None

    Response:
                {"core_usage": {
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
                "total_cores": 8}
    """

    # processor details
    processor_detail = cpuinfo.get_cpu_info()["brand_raw"]

    # total no.of cores in system
    total_cores = psutil.cpu_count(logical=True)

    # core usage details per core
    core_usage = {
        f"Core {i}": f"{percentage}%"
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1))
    }

    return {
        "processor_detail": processor_detail,
        "total_cores": total_cores,
        "core_usage": core_usage,
    }


def ram_details_utils():
    """
    get the RAM details

    Arguments: None

    Response:
            {
                "available_memory": "2.38GB",
                "memory_percentage": "68.50B%",
                "total_memory": "7.57GB",
                "used_memory": "4.44GB"
            }
    """

    ram = psutil.virtual_memory()
    total_memory = get_size_utils(ram.total)
    available_memory = get_size_utils(ram.available)
    used_memory = get_size_utils(ram.used)
    memory_percentage = f"{get_size_utils(ram.percent)}%"

    return {
        "total_memory": total_memory,
        "available_memory": available_memory,
        "used_memory": used_memory,
        "memory_percentage": memory_percentage,
    }


def gpu_details_utils():
    """
    get the GPU details

    Arguments: None

    Response:
            "GPU": []

    """
    gpus = GPUtil.getGPUs()
    list_gpus = []
    for gpu in gpus:
        # get the GPU id
        gpu_id = gpu.id
        # name of GPU
        gpu_name = gpu.name
        # get % percentage of GPU usage of that GPU
        gpu_load = f"{gpu.load*100}%"
        # get free memory in MB format
        gpu_free_memory = f"{gpu.memoryFree}MB"
        # get used memory
        gpu_used_memory = f"{gpu.memoryUsed}MB"
        # get total memory
        gpu_total_memory = f"{gpu.memoryTotal}MB"
        # get GPU temperature in Celsius
        gpu_temperature = f"{gpu.temperature} °C"
        gpu_uuid = gpu.uuid
        list_gpus.append(
            {
                "gpu_id": gpu_id,
                "gpu_name": gpu_name,
                "gpu_load": gpu_load,
                "gpu_free_memory": gpu_free_memory,
                "gpu_used_memory": gpu_used_memory,
                "gpu_total_memory": gpu_total_memory,
                "gpu_temperature": gpu_temperature,
                "gpu_uuid": gpu_uuid,
            }
        )

    return list_gpus


def disk_details_utils():
    """
    get the disk details

    Arguments:None

    Response:
            {
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
    """

    # get all the partitions in disk
    partitions = psutil.disk_partitions()
    # print(partitions)
    partition_list = []
    partition_count = 1

    for partition in partitions:
        device = partition.device
        mountpoint = partition.mountpoint
        file_system_type = partition.fstype
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            # this can be catched due to the disk that
            # isn't ready
            continue

        total_size = get_size_utils(partition_usage.total)
        used = get_size_utils(partition_usage.used)
        free = get_size_utils(partition_usage.free)
        percentage = partition_usage.percent
        # partition_dict({f"partition_{i}":{}})
        partition_list.append(
            {
                f"partition_{partition_count}": {
                    "device": device,
                    "mountpoint": mountpoint,
                    "file_system_type": file_system_type,
                    "total_size": total_size,
                    "used": used,
                    "free": free,
                    "percentage": f"{percentage}%",
                }
            }
        )
        partition_count += 1

    # get IO statistics since boot
    disk_io = psutil.disk_io_counters()
    total_read = get_size_utils(disk_io.read_bytes)
    total_write = get_size_utils(disk_io.write_bytes)

    return {
        "partition": partition_list,
        "total_read": total_read,
        "total_write": total_write,
    }









def check_camera_utils():
    client = docker.from_env()
    
    # Getting all containers with details
    all_containers = client.containers.list()
    
    # Getting container data from mongo
    container_data = get_container_mongo_utils()
    
    # Initialize a list to store camera container details
    camera_containers = []

    if container_data is None:
        return []
    
    
    # Check if each camera container from MongoDB is running and get its details
    for container_name, container_id in container_data.items():
        if container_name.startswith("camera_"):
            for container in all_containers:
                if container.id == container_id:
                    container_info = {
                        "id": container_id,
                        # "name": container_name,
                        "command": container.attrs['Config']['Cmd'],
                        "created": container.attrs['Created'],
                        "status": container.status,
                        "ports": container.attrs['HostConfig']['PortBindings'],
                        "name": container.name
                    }
                    camera_containers.append(container_info)
    print(camera_containers, "...........")
    
    return camera_containers

def check_model_utils():
    client = docker.from_env()
    
    # Getting all containers with details
    all_containers = client.containers.list()
    
    # Getting container data from mongo
    container_data = get_container_mongo_utils()
    
    # Initialize a list to store model container details
    model_containers = []

    if container_data is None:
        return []
    
    
    # Check if each model container from MongoDB is running and get its details
    for container_name, container_id in container_data.items():
        if container_name.startswith("model_"):
            for container in all_containers:
                if container.id == container_id:
                    container_info = {
                        "id": container_id,
                        # "name": container_name,
                        "command": container.attrs['Config']['Cmd'],
                        "created": container.attrs['Created'],
                        "status": container.status,
                        "ports": container.attrs['HostConfig']['PortBindings'],
                        "name": container.name
                    }
                    model_containers.append(container_info)
    print(model_containers, ".........")
    
    return model_containers

# getting all model and camera container details from LocalMongo
def get_container_mongo_utils():
    # user_domain("sk@livis.ai")
    # getting all model and camera container details
    all_container = (
        LocalMongoHelper()
        .getCollection("container_id_collection")
        .find_one({}, {"_id": 0})
    )

    return all_container










 










 
