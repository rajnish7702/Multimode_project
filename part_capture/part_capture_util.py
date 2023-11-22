from time import sleep
from bson import ObjectId
from datetime import datetime
from edgeplusv2_config.common_utils import (
    CloudMongoHelper,
    LocalMongoHelper,
    CacheHelper,
    CLOUD_MONGO_HOST,
    CLOUD_MONGO_PORT,
    validate_required_data
)
import os

# from edgeplusv2_config.common_utils import LOCAL_MONGO_HOST,LOCAL_MONGO_PORT,REDIS_HOST,REDIS_PORT,CLOUD_KAFKA_BROKER_URL
import docker
import json
import cv2
from PIL import Image
import numpy as np
from kafka import KafkaProducer, KafkaConsumer
from datetime import datetime
import shutil
import zipfile
from zipfile import ZipFile
from edgeplusv2_config.common_utils import CloudMongoHelper,LocalMongoHelper,CacheHelper

# from edgeplusv2_config.common_utils import LOCAL_MONGO_HOST,LOCAL_MONGO_PORT,REDIS_HOST,REDIS_PORT,CLOUD_KAFKA_BROKER_URL
from collections import deque
from .part_capture_class import GoldenImage, StaticGoldenImage, CobotGoldenImage, DataCapture, StaticDataCapture, ConveyorDataCapture, CobotDataCapture
import http.server
import socketserver
import threading
import urx
import requests
import socket
import random
import uuid
import time
from docker import errors as dockererrors
from pymongo import errors
# import datetime
f = open("edgeplusv2_config/v2_config.json")
data = json.load(f)
f.close()
BOOTSTRAP_SERVERS = [data["LOCAL_KAFKA_BROKER_URL"]]

kAFKA_FRAME_TIMEOUT_MS=2000

def static_golden_images_util(

    topic_list,
    part_id,
    part_name,
    workstation_type,
    usecase_id,
    workstation_id,
    part_number,
    waypoint,
):
    """Save the images captured

    Arguments:
        use_case,topic_list,part_id,part_name,workstation_type,waypoint,

    Returns:
      ""successfully zipped""
    """
    print("inside the capture utils")

    capture_golden_image = StaticGoldenImage(
        topic_list,
        part_id,
        part_name,
        workstation_type,
        usecase_id,
        workstation_id,
        part_number,
        waypoint,
    )

    # golden_image_status = capture_golden_image.static_golden_image()
    golden_image_status = capture_golden_image.capture_golden_images()

    return golden_image_status


def golden_images_upload_util(
    topic_list,
    part_id,
    part_name,
    workstation_type,
    waypoint,
    
):
    """Save the images captured

    Arguments:
            topic_list,part_id,part_name,workstation_type,waypoint,

    Returns:
      ""successfully zipped""
    """
    print("inside the upload utils")

    capture_golden_image = GoldenImage(
        topic_list,
        part_id,
        part_name,
        workstation_type,
        waypoint,
    )

    # golden_image_status = capture_golden_image.static_golden_image()
    golden_image_status = capture_golden_image.golden_image_upload_util()

    return golden_image_status


def cobot_golden_image_record_waypoint_util(
     topic_list, part_id, part_name, workstation_type,usecase_id,workstation_id,part_number,waypoint,position_number,cobot_name
):
    """
    captured the golden image and create the meta_data file of that image for the respective part
    """

    cobot_image_object = CobotGoldenImage(
        
        topic_list,
        part_id,
        part_name,
        workstation_type,
        usecase_id,
        workstation_id,
        part_number,
        waypoint,
        position_number
    )

    cobot_golden_image_status = cobot_image_object.cobot_golden_image_record_waypoint(cobot_name)

    return cobot_golden_image_status


def cobot_golden_image_delete_waypoint_util(waypoint,part_id):
    """
    captured the golden image and create the meta_data file of that image for the respective part
    """

    cobot_image_object = CobotGoldenImage()

    cobot_golden_image_status = cobot_image_object.cobot_golden_image_delete_waypoint(waypoint,part_id)

    return cobot_golden_image_status


def cobot_golden_image_transit_point_util(waypoint,part_id,position_number,transit_status):
    """
    captured the golden image and create the meta_data file of that image for the respective part
    """

    cobot_image_object = CobotGoldenImage()

    cobot_golden_image_status = cobot_image_object.cobot_golden_image_transit_point(waypoint,part_id,position_number,transit_status)

    return cobot_golden_image_status


# def cobot_golden_image_upload_util(
#      use_case, topic_list, part_id, part_name, workstation_type,waypoint
# ):
#     """
#     captured the golden image and create the meta_data file of that image for the respective part
#     """

#     cobot_image_object = CobotGoldenImage(
#         
#         use_case,
#         topic_list,
#         part_id,
#         part_name,
#         workstation_type,
#         waypoint
#     )

#     cobot_golden_image_status = cobot_image_object.upload_golden_image()

#     return cobot_golden_image_status


def static_data_capture_util(
     use_case_list, topic_list, part_id, part_name, part_number,workstation_type,cycle_number
):
    """Data captured for the respective part .
        The workstation type is Static """

    static_data_capture = StaticDataCapture(
        
        use_case_list,
        topic_list,
        part_id,
        part_name,
        part_number,
        workstation_type,
    )
    static_data_collection = static_data_capture.static_data_capture(cycle_number)
    return static_data_collection


def data_capture_upload_util(
     use_case_list, topic_list, part_id, part_name, part_number,workstation_type
):
    """Data captured for the respective part .
        The workstation type is Static """

    static_data_capture = DataCapture(
        
        use_case_list,
        topic_list,
        part_id,
        part_number,
        part_name,
        workstation_type,
    )
    static_data_collection = static_data_capture.upload_data_capture()
    return static_data_collection


def conveyor_data_capture_util(
     use_case_list, topic_list, part_id, part_name, part_number,workstation_type,plc_configuration
):
    """Data captured for the respective part .
        The workstation type is conveyor"""
    
    conveyor_data_capture_thread = threading.Thread(target=conveyor_data_capture_thread_util,args=( use_case_list, 
                                                                                                   topic_list, part_id, part_name,part_number, 
                                                                                                   workstation_type,plc_configuration),daemon=True)
    conveyor_data_capture_thread.start()


def conveyor_data_capture_thread_util(
     use_case_list, topic_list, part_id, part_name, part_number,workstation_type,plc_configuration
):
    """Data captured for the respective part .
        The workstation type is conveyor"""
    
    static_data_capture = ConveyorDataCapture(
        
        use_case_list,
        topic_list,
        part_id,
        part_name,
        part_number,
        workstation_type,
    )
    static_data_collection = static_data_capture.conveyor_data_capture(plc_configuration)
    return static_data_collection

def cobot_data_capture_thread_util(
     use_case_list, topic_list, part_id, part_name,part_number, workstation_type,cycle_number,workstation_data,waypoint_dictionary
):
    """Data captured for the respective part .
        The workstation type is cobot"""
    
    cobot_data_capture = CobotDataCapture(
        
        use_case_list,
        topic_list,
        part_id,
        part_name,
        part_number,
        workstation_type,
    )
    cobot_data_collection = cobot_data_capture.cobot_data_capture(cycle_number,workstation_data,waypoint_dictionary)
    return cobot_data_collection

def cobot_data_capture_util(
     use_case_list, topic_list, part_id, part_name, part_number,workstation_type,cycle_number,workstation_data,waypoint_dictionary
):
    """Data captured for the respective part .
        The workstation type is conveyor"""
    
    cobot_data_capture_thread = threading.Thread(target=cobot_data_capture_thread_util,args=( use_case_list, 
                                                                                                   topic_list, part_id, part_name,part_number,
                                                                                                   workstation_type,cycle_number,workstation_data,
                                                                                                   waypoint_dictionary),daemon=True)
    cobot_data_capture_thread.start()

def utils_find_json_files(directory_path):
    """
    The function will be taking the path of the data lake directory and will be traversing through all
    the directories and will be searching for json meta file and willbe storing it inside a list which 
    the function will be returning.
    """

    json_files = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))
    return json_files


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

def find_the_usecase_name(usecase_id):
    """Find the usecase name for the part using usecase_id in temp_part collection in cloud """

    url = "http://127.0.0.1:5000/api_gateway/get_one_documents"
    payload = json.dumps(
        {
            "collection": "usecase",
            "document": [{"_id":usecase_id},{"_id":0,"usecase_name":1}],
        }
    )

    headers = {"Content-Type": "application/json"}
    # sending request data and getting response of one document
    api_geteway_response = requests.request("POST", url, headers=headers, data=payload)
    api_geteway_response = api_geteway_response.json()
    usecase_name=api_geteway_response.get("status")
    return usecase_name

def get_the_workstation_data(workstation_id):

    url = "http://127.0.0.1:5000/api_gateway/get_one_documents"
    payload = json.dumps(
        {
            "collection": "workstations",
            "document": [{"_id":workstation_id},{"workstation_name":1,"workstation_type":1,"workstation_type_detail":1,"plc":1,"camera":1}],
        }
    )

    headers = {"Content-Type": "application/json"}
    # sending request data and getting response of one document
    api_geteway_response = requests.request("POST", url, headers=headers, data=payload)
    api_geteway_response = api_geteway_response.json()
    workstation_data=api_geteway_response.get("status")
    return workstation_data


# def get_the_workstation_details(workstation_id):

#     url = "http://127.0.0.1:5000/api_gateway/get_one_documents"
#     payload = json.dumps(
#         {
#             "collection": "workstations",
#             "document": [{"_id":workstation_id},{}],
#         }
#     )

#     headers = {"Content-Type": "application/json"}
#     # sending request data and getting response of one document
#     api_geteway_response = requests.request("POST", url, headers=headers, data=payload)
#     api_geteway_response = api_geteway_response.json()
#     workstation_details=api_geteway_response.get("status")
#     return workstation_details

def get_the_usecase_details(usecase_id):

    url = "http://127.0.0.1:5000/api_gateway/get_one_documents"
    payload = json.dumps(
        {
            "collection": "usecase",
            "document": [{"_id":usecase_id},{}],
        }
    )

    headers = {"Content-Type": "application/json"}
    # sending request data and getting response of one document
    api_geteway_response = requests.request("POST", url, headers=headers, data=payload)
    print(api_geteway_response)
    # if api_geteway_response.status_code==200:
    api_geteway_response = api_geteway_response.json()
    usecase_details=api_geteway_response.get("status")
    return usecase_details
 

def get_the_temp_part_details(temp_part_id):

    url = "http://127.0.0.1:5000/api_gateway/get_one_documents"
    payload = json.dumps(
        {
            "collection": "temp_parts",
            "document": [{"_id":temp_part_id},{}],
        }
    )

    headers = {"Content-Type": "application/json"}
    # sending request data and getting response of one document
    api_geteway_response = requests.request("POST", url, headers=headers, data=payload)
    api_geteway_response = api_geteway_response.json()
    temp_part_details=api_geteway_response.get("status")
    return temp_part_details

def random_port_generator_util(n):
    # print("in rand0m+ports")
    port_list = []
    for _ in range(n):
     port_list.append(random.randint(1000, 4000))
    # print("random_port: ",port_list)
    return port_list

available_ports = []

def check_ports_util(n):
    # print('in check ports util')
    hostname = socket.gethostname()
    # print(hostname)
    ip = socket.gethostbyname(hostname)
    # ip="172.22.0.1"
    # print(ip)

    counter = 0

    port_list = random_port_generator_util(n)

    print(port_list)

    for port in port_list:
    # port=random.randint(a,b)

        try:
            # print("hello socket")
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # print("Hi bind")
            server.bind((ip, port))
            # print("Available port is {port}")
            available_ports.append(port)
            counter += 1
            # print(c)
        except:
            print(f"port number {port} is NOT available")
            # print(counter)
        server.close()
        if counter == n:
        # print("available_port",available_ports)
            return available_ports

    # elif index==len(port_list)-1:
    available_ports_list=check_ports_util(counter - n)

    print(available_ports)
    return available_ports_list


def http_server_for_meta_data_util(port):
    """
    Run the HTTP server for to access the meta_data
    """

    # Directory name to create and serve
    folder_name = "."

    # Change the working directory to the folder you want to serve
    os.chdir(folder_name)
    print("current_directory:",os.getcwd())

    # Start the HTTP server
    Handler = http.server.SimpleHTTPRequestHandler
    print("start")
    server_thread = threading.Thread(target=start_http_server, args=(port, Handler))
    print("end")
    # Start the HTTP server thread
    server_thread.start()
    # os.chdir("../")
    print("current_directory:",os.getcwd())
    # Return the server URL
    return f"http://localhost:{port}/data_lake"


def start_http_server(port, handler):
 """start the http_server to stream the data"""

 httpd = socketserver.TCPServer(("", port), handler)
 print(f"Serving at port {port}")
 httpd.serve_forever()

def get_the_capture_image_server_url():
    try:
        CacheHelper().set_json({"golden_image_error":None})
        port_list=check_ports_util(3)
        http_server_link=http_server_for_meta_data_util(port_list[0])
        return http_server_link
    except Exception as e:
        print("error:",str(e))
        CacheHelper().set_json({"golden_image_error":True})

def get_the_data_capture_image_server_url():
    try:
        CacheHelper().set_json({"data_capture_error":None})
        port_list=check_ports_util(3)
        http_server_link=http_server_for_meta_data_util(port_list[0])
        return http_server_link
    except Exception as e:
        print("error:",str(e))
        CacheHelper().set_json({"data_capture_error":True})


def video_stream_util(topic_name):
    # topic_name = json_data['camera']['camera_name']
    # print("topic_name: ",topic_name)
    #consumer = KafkaConsumer("topic_test", bootstrap_servers=BOOTSTRAP_SERVERS)
    timeout_ms=kAFKA_FRAME_TIMEOUT_MS

    consumer = KafkaConsumer(topic_name,
                bootstrap_servers=BOOTSTRAP_SERVERS,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id=str(uuid.uuid1()),
                consumer_timeout_ms=timeout_ms)
    # video=cv2.VideoCapture('/home/saravanan/Videos/videoplayback.mp4')


    for message in consumer:
        decoded = cv2.imdecode(np.frombuffer(message.value, np.uint8), 1)
        # print("Inside frame loop")
        #read frame 
        # frame_coming,frame=video.read()

        # if not frame_coming:
        # break

        frame=cv2.resize(decoded,(1536,864))
        
        #Encode frame as JPEG
        frame=cv2.imencode('.jpg', frame)[1].tobytes()

        # Yield the frame 
        yield (b'--frame\r\n'
        b'Content-Type: image/jpeg\r\n\r\n' + frame+ b'\r\n\r\n')

def fetch_the_authorization_token_util():
    """
    Fetach the authroization token from loacl mongo 
    
    Arguments: None
    
    Response: Bearer """

    authorization_token_data= LocalMongoHelper().getCollection("user_cred_log").find_one({},{"access_token":1,"_id":0})
    print("authorization_token_data",authorization_token_data)
    if authorization_token_data:
        authorization_token=authorization_token_data["access_token"]
        print("authorization_token",authorization_token)
        return f"Bearer {authorization_token}"
    else:
        return False
    
def get_part_details_list(temp_part_data):
    """It filter the part data from the temp_part data
    """
    part_details_list=[]
    for part_data in temp_part_data:
        part_detail={}
        part_detail["_id"]={}
        part_detail["_id"]["$oid"]=part_data["_id"]
        part_detail["part_name"]=part_data["part_name"]
        part_detail["part_number"]=part_data["part_number"]
        part_detail["usecase_id"]=part_data["usecase_id"]
        part_detail["usecase_name"]=part_data["usecase_name"]
        part_details_list.append(part_detail)

    inserted_id=dump_the_temp_part_data_in_local_mongo(temp_part_data)
    if inserted_id:
        return part_details_list
    else:
        return False

def dump_the_temp_part_data_in_local_mongo(temp_part_data):
    """It dumps the temp part data in the local mongo """

    for index in range(len(temp_part_data)):
        try:
            temp_part_data[index]["_id"]=ObjectId(temp_part_data[index]["_id"])
        # temp_part_dictionary

            inserted_id= LocalMongoHelper().getCollection("temp_part_data").insert_one(temp_part_data[index])
        except errors.DuplicateKeyError:
            print("error duplikatekey error")
    return True


def dump_the_part_data_in_local_mongo(part_data):
    """It dumps the temp part data in the local mongo """
    try:
        part_data["_id"]=ObjectId(part_data["_id"])

        inserted_id= LocalMongoHelper().getCollection("part_data").insert_one(part_data)

        return inserted_id
    except errors.DuplicateKeyError:
        return True
    

def spawn_the_camera_conatiner_util(topic_list):
    """ spwan the camera conatiner with camera name as a container name"""

    client = docker.from_env()
    f = open("edgeplusv2_config/v2_config.json")
    data_from_webapp = json.load(f)
    f.close()

    camera_image = data_from_webapp["CAMERA_IMAGE"]

    container_deployed=[False]*len(topic_list)
    for index,cam in enumerate(topic_list):
        # count = 1
        
        camera_name = cam
        print("camera_name:",camera_name)
        try:
            container_deployed[index]=False

            # Check the camera conatiner availability
            cam_container = client.containers.get(camera_name)

            if cam_container.status=="Exited" or cam_container.status=="exited" :
               
                # It will restart the camera_conatiner
                cam_container.restart()
                time.sleep(3)
                container_deployed[index] = True

            else:
                container_deployed[index] = True

        # If container not found then new container should create
        except dockererrors.NotFound:
            try:
                container_deployed[index] = False
                client.containers.run(
                    camera_image,
                    name=str(camera_name),
                    environment={
                        "topic_name": str(cam),
                        "path": "videos/traffic.mp4",
                    },
                    detach=True,
                    tty=True,
                    shm_size="4G",
                    network="edge_v2_test_network2",
                    restart_policy={"Name": "on-failure", "MaximumRetryCount": 5},
                    command="python3 adapter.py",
                )
                
                container_deployed[index] = True
            except Exception as e:
                print("error: ",str(e) )
                container_deployed[index]= False
                return False
    
    if False not in container_deployed:
        return True
    else:
        return False

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

def image_file_render_url_util(workstation_type,part_id,topic_list):
    """It gives the image render url list"""
    try:
        #create the http server for root directory
        http_server_link=get_the_capture_image_server_url()

        local_collection=f"{workstation_type}_golden_image_{part_id}"

        http_server_link_for_respective_folder= f"{http_server_link}/{local_collection}"

        #get the list of image to render
        image_file_list_object=LocalMongoHelper().getCollection(local_collection)
        all_image_file_list=list(image_file_list_object.find({},{"image_name":1,"_id":0}))
        image_file_render_url=[]
        if all_image_file_list:
            number_of_images=len(topic_list)
            image_file_to_render_list=all_image_file_list[-number_of_images:]
            for image_path in image_file_to_render_list:
                image_file_path=image_path["image_name"]
                file_url=f"{http_server_link_for_respective_folder}/{image_file_path}"
                image_file_render_url.append(file_url)
        return image_file_render_url
    
    except Exception as e:
        print(str(e))
        return False
    
def data_capture_image_file_render_url_util(workstation_type,part_id,topic_list):
    """It gives the image render url list"""
    try:
        #create the http server for root directory
        http_server_link=get_the_data_capture_image_server_url()

        local_collection=f"{workstation_type}_data_capture_{part_id}"

        http_server_link_for_respective_folder= f"{http_server_link}/{local_collection}"

        #get the list of image to render
        image_file_list_object=LocalMongoHelper().getCollection(local_collection)
        all_image_file_list=list(image_file_list_object.find({},{"image_name":1,"_id":0}))
        image_file_render_url=[]
        if all_image_file_list:
            number_of_images=len(topic_list)
            image_file_to_render_list=all_image_file_list[-number_of_images:]
            for image_path in image_file_to_render_list:
                image_file_path=image_path["image_name"]
                file_url=f"{http_server_link_for_respective_folder}/{image_file_path}"
                image_file_render_url.append(file_url)
        return image_file_render_url
    
    except Exception as e:
        print(str(e))
        return False

def get_the_workstation_details(workstation_id):
    """It fetch the workstation details based on the workstation_id"""

    authorization_token=fetch_the_authorization_token_util()
    # authorization_token="Bearer 74l5fa2R5j0o48wC8D9YeIwbTrPA05"
    if not authorization_token:
        return False  
    else:
        url = f"https://v2.livis.ai/api/livis/v2/workstations/workstation/{workstation_id}"

        headers = {"Content-Type": "application/json",
                    "Authorization":authorization_token}

        # sending request data and getting response of one document
        api_geteway_response = requests.request("GET", url, headers=headers)
        return api_geteway_response
    
# def preview_data_capture_image_util():
#     """ It return the list of captured images in a single cycle"""
#     print("start")
#     dictionary_of_captured_images=LocalMongoHelper().getCollection("preview_image_list").find_one({},{"_id":0,"image_name":1})
#     # list_of_captured_images=dictionary_of_captured_images["image_name"]
#     print("preview_image",dictionary_of_captured_images)
#     list_of_captured_images=dictionary_of_captured_images["image_name"]
#     print(list_of_captured_images)

#     return list_of_captured_images


# def static__golden_image_update_util(part_id):
#     """
#     Zip the entire file of the part

#     Arguments: None

#     Response: "successfully zipped"
#     """

#     folder_to_be_delete = "data_lake/"
#     zip_file_name = f"golden_image_{part_id}.zip"

#     with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED) as zipf:
#         for root, dirs, files in os.walk(folder_to_be_delete):
#             for file in files:
#                 file_path = os.path.join(root, file)
#                 arcname = os.path.relpath(file_path, folder_to_be_delete)
#                 zipf.write(file_path, arcname)

#     port = 6788
#     print("start")
#     url_to_access_captured_data = http_server_for_meta_data_util(port)
#     print("end")
#     return url_to_access_captured_data


# #   return "successfully zipped"


# def http_server_for_meta_data_util(port):
#     """
#     Run the HTTP server for to access the meta_data
#     """

#     # Directory name to create and serve
#     folder_name = "./data_lake"

#     # Change the working directory to the folder you want to serve
#     os.chdir(folder_name)

#     # Start the HTTP server
#     Handler = http.server.SimpleHTTPRequestHandler
#     print("start")
#     server_thread = threading.Thread(target=start_http_server, args=(port, Handler))
#     print("end")
#     # Start the HTTP server thread
#     server_thread.start()

#     # Return the server URL
#     return f"http://localhost:{port}"


# def start_http_server(port, handler):
#     """start the http_server to stream the data"""

#     httpd = socketserver.TCPServer(("", port), handler)
#     print(f"Serving at port {port}")
#     httpd.serve_forever()

# def create_the_use_case_collection_in_localmongo(use_case_list):
#     """It fetch the coordinate values of use case from cloud mongo to local mongo"""
#     try:
#         for use_case in use_case_list:
            
#             #Collect the data for respective use_case
#             use_case_coordinates_list=[coordinates for coordinates in CloudMongoHelper().getCollection(use_case).find({},{"_id":0})]
            
#             #Create the use_case collection on local
#             LocalMongoHelper().getCollection(use_case).insert_many(use_case_coordinates_list)
#             # print("successfully insert")

#         return {"message":178,
#                 "data":{"data_capture_use_case":[],"total":0}}
    
#     except Exception as e:
#         return {"message":179,
#                 "data":{"data_capture_use_case":[str(e)],"total":1}}