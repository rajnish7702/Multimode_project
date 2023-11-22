import os
import cv2
import pymongo
from edgeplusv2_config.common_utils import (
    CloudMongoHelper,
    LocalMongoHelper,
    CacheHelper,
)
from kafka import KafkaConsumer
import json
import numpy as np
from PIL import Image
import shutil
import time
from abc import ABC, abstractmethod
# import urx
import zipfile
from flask import Response, stream_with_context
from datetime import datetime
from .conveyor_class import conveyor_main
import multiprocessing
import threading
from .robot_controller import robot_controller
import requests
import uuid
import http.server
import socketserver
from bson import json_util

f = open("edgeplusv2_config/v2_config.json")
data = json.load(f)
f.close()

BOOTSTRAP_SERVERS = [data["LOCAL_KAFKA_BROKER_URL"]]
print(BOOTSTRAP_SERVERS)

kAFKA_FRAME_TIMEOUT_MS=2000
COBOT_ADDRESS=data["COBOT_ADDRESS"]

class GoldenImage:
    """Base class for Golden images"""

    def __init__(
        self,


        topic_list=[],
        part_id=None,
        part_name=None,
        workstation_type=None,
        usecase_id=None,
        workstation_id=None,
        part_number=None,
        waypoint=None,
        position_number=None,
        coordintaes=[],
        waypoint_info={},
    ):

        self.topic_list = topic_list
        self.part_id = part_id
        self.part_name = part_name
        self.workstation_type = workstation_type
        self.usecase_id=usecase_id
        self.workstation_id=workstation_id
        self.part_number=part_number
        self.waypoint = waypoint
        self.position_number=position_number
        self.coordinates = coordintaes
        self.waypoint_info = waypoint_info
        self.meta_data_dictionry = {}
        self.image_count=0


    def get_frame(self, topic):
        """
        Get the frame for respective topic subscribed

        Arguments:
            topic

        Response:
            decoded_image
        """

        timeout_ms=kAFKA_FRAME_TIMEOUT_MS
        try:
            # consumer = KafkaConsumer(topic_name, bootstrap_servers=BOOTSTRAP_SERVERS,consumer_timeout_ms=timeout_ms)         
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=BOOTSTRAP_SERVERS,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id=str(uuid.uuid1()),
                consumer_timeout_ms=timeout_ms
            )

            # do a dummy poll to retrieve some message
            consumer.poll()

            # go to end of the stream
            consumer.seek_to_end()
            print(consumer)
            
            #geth the frames from the camera using kafka consumer and decoded the frames
            for message in consumer:
                print("Hello World Consumer")
                decoded_frame = cv2.imdecode(np.frombuffer(message.value, np.uint8), 1)
                return decoded_frame
                # break
            print("Frame not found after timeout set")
            return None
        except Exception as e:
            print(e)
            if 'NoBrokersAvailable' in str(e):
                CacheHelper().set_json({"golden_image_error":True}) 
                return 185
            else:
                return 180
            
    def meta_data_utils(self, topic, part_id_path,image_name):
        """
        This method calls other methods to calculate the image resolution and
        creating meta data for image in the same directory.

        Arguments: [topic,part_id_path,image_name]

        Response: meta_data_status
        """

        image_path = self.meta_data_dictionry["image_file"]

        resolution = self.get_image_resolution(
            image_path
        )  # Resolution of the image will be get using this function
        # print(resolution)

        if resolution:
            # final_resolution = (
            #     str(resolution[0]) + " x " + str(resolution[1]) + " pixels"
            # )
            # self.meta_data_dictionry["image_resolution"] = final_resolution
            self.meta_data_dictionry["image_public_url"]=""
            self.meta_data_dictionry["metadata"]={}
            self.meta_data_dictionry["metadata"]["image_width"] = resolution[0]
            self.meta_data_dictionry["metadata"]["image_height"] = resolution[1]
            self.meta_data_dictionry["metadata"]["format"]="jpg"
            self.meta_data_dictionry["metadata"]["size"]=resolution[2]
            meta_data_status = self.save_resolution_and_image_path_to_text_file(
                part_id_path,image_name
            )

            return meta_data_status
        else:
            # print("Failed to read image or invalid image format.")
            return "Failed to read image or invalid image format."

    def get_image_resolution(self, image_path):
        """
        This function is calculating the image resolution of an image from the directory.

        Arguments: image_path

        Response: (1280,720)
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size  # get the frame size
                file_size= os.stat(image_path)
                file_size_in_bytes=file_size.st_size
                return width, height ,file_size_in_bytes
        except Exception as e:
            print("error exception:", e)
            return 0,0

    def save_resolution_and_image_path_to_text_file(self, part_id_path,image_name):
        """
        It create the meta data json file

        Arguments : [part_id_path,image_name]

        Response: text_file_path
        """

        text_file_path = f"{part_id_path}/{image_name}.json"
        self.meta_data_dictionry["meta_data_file_name"]=text_file_path

        if self.workstation_type == "cobot":
            self.meta_data_dictionry["waypoint"] = self.waypoint
            self.meta_data_dictionry["coordinates"] = self.coordinates
            self.meta_data_dictionry["transit_point"] = self.waypoint_info["transit_point"]
             
        collection_name=str(self.workstation_type) + "_golden_image_" + str(self.part_id)
        insertion_id=LocalMongoHelper().getCollection(collection_name).insert_one(self.meta_data_dictionry).inserted_id 

        part_configuration_write=self.part_configuration_details(part_id_path)

        del self.meta_data_dictionry["image_file"]
        del self.meta_data_dictionry["meta_data_file_name"]
        del self.meta_data_dictionry["_id"]

        with open(text_file_path, "w") as json_file_1:
            json.dump(self.meta_data_dictionry, json_file_1)
        return text_file_path
    
    def part_configuration_details(self,part_id_path):
        """It gives the configuration details of the part """

        part_configuration_file_name=f"{part_id_path}/part_configuration.json"

        part_configuration_dictionary={
                                        "workstation_type": self.workstation_type,
                                        "part_name": self.part_name,
                                        "part_number": self.part_number,
                                        "part_id": self.part_id,
                                        "usecase_id": self.usecase_id,
                                        "workstation_id": self.workstation_id,
                                        "platform": "Edge+",
                                        "operation_type": "golden_image_capture",
                                        "waypoint":{}
                                        }

        if self.workstation_type=="static":
            print("static selected to implement")
            part_configuration_dictionary["waypoint"]="P0"

            with open(part_configuration_file_name,"w") as json_file:
                json.dump(part_configuration_dictionary, json_file)
            return True
                
        elif self.workstation_type=="cobot":

            waypoint_coordinates_dictionary={"transit_point":self.waypoint_info["transit_point"],
                                             "coordinates":self.coordinates}
            print("waypoint_coordinates_dictionary",waypoint_coordinates_dictionary)
            if self.waypoint=="P0":

                part_configuration_dictionary["waypoint"][self.waypoint]=waypoint_coordinates_dictionary
                with open(part_configuration_file_name,"w") as json_file:
                    json.dump(part_configuration_dictionary, json_file)
            else:
                part_configuration_file=open(part_configuration_file_name)
                part_configuration_file_as_dictionary=json.load(part_configuration_file)
                part_configuration_file_as_dictionary["waypoint"][self.waypoint]=waypoint_coordinates_dictionary                   

                print("part_configuration_dictionary",part_configuration_file_as_dictionary)
                with open(part_configuration_file_name,"w") as json_file:
                    json.dump(part_configuration_file_as_dictionary, json_file)
            return True
        
        else:
            return False                


    
    def meta_mongo_backup(self):
        """Update the meta data in Local Mongo"""

        collection_name=str(self.workstation_type) + "_golden_image_" + str(self.part_id)

        # with open(text_file_path) as file:
        #     file_data = json.load(file)

        insertion_id=LocalMongoHelper().getCollection(collection_name).insert_one(self.meta_data_dictionry).inserted_id 

        return insertion_id


    def golden_image_upload_util(self):
        """
        Zip the entire file of the part

        Arguments: None

        Response: "cobot_golden_image_64e5d0c3fb04d754d9a5c619.zip"
        """
        try:
            CacheHelper().set_json({"golden_image_upload_error":None})
            folder_to_be_delete = "data_lake/"
            zip_file_name = f"{self.workstation_type}_golden_image_{self.part_id}.zip"
            
            part_id_path=f"data_lake/{self.workstation_type}_golden_image_{self.part_id}"

            with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_to_be_delete):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, folder_to_be_delete)
                        zipf.write(file_path, arcname)

            after_zip_local_folder_delete_status=self.remove_the_directory()
            if after_zip_local_folder_delete_status:
                return zip_file_name  
            else:
                return False         
        
        except Exception as e:
            print(str(e))
            CacheHelper().set_json({"golden_image_upload_error":True})  
            return 151
        

    def remove_the_directory(self):
        """It remove the directory inlocal and mongo collection for respective part once file is zipped"""

        directory_to_delete = f"data_lake/{self.workstation_type}_golden_image_{self.part_id}"

        try:
            shutil.rmtree(directory_to_delete)
            print(f"Directory '{directory_to_delete}' and its contents have been deleted successfully.")
            LocalMongoHelper().getCollection(f"{self.workstation_type}_golden_image_{self.part_id}").delete_many({})
            return True
        except OSError as e:
            print(f"Error: {e.strerror}") 
            return False         


class StaticGoldenImage(GoldenImage):

    def capture_golden_images(self):
        """
        captured the golden image and saves the meta data of that image as a json file

        Arguments: None

        Response: 153("Golden image captured successfully")
        """
        try:
            CacheHelper().set_json({"golden_image_error":None})
            data_dir = "data_lake/"
            part_id_path = os.path.join(
                data_dir, str(self.workstation_type) + "_golden_image_" + str(self.part_id)
            )
            if not os.path.exists(data_dir):
                os.mkdir(data_dir)
            if not os.path.exists(part_id_path):
                os.mkdir(part_id_path)
                
            filename = ""
            image_list = []
            for camera_index,topic in enumerate(self.topic_list):
                current_datetime = datetime.now()

                # Format it as a string without milliseconds
                formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H:%M:%S:%f")

                # filename = part_id_path + "/" + str(self.part_id) + topic + ".jpg"
                image_name = (
                    str(self.part_id)
                    + "_"
                    + str(formatted_datetime)
                    + "_"
                    + str(self.waypoint)
                    + "_"
                    + str(self.image_count)
                )

                filename = part_id_path + "/" + image_name + ".jpg"
                captured_frame = self.get_frame(
                    topic
                )  # get the frames for respective topic

                if captured_frame is None:
                    print("image_none_got")
                    CacheHelper().set_json({"golden_image_error":185}) 
                    return 185
                elif captured_frame.all()==185:
                    CacheHelper().set_json({"golden_image_error":185}) 
                    return 185
                else:
                    print("filename", filename)
                    cv2.imwrite(
                        filename, captured_frame
                    )  # images are saved in the part_id_path

                    image_list.append(filename)

                    # all the meta data is added to a dictionary to create the meta data json file
                    image_name_with_format = image_name + ".jpg"

                    self.meta_data_dictionry["workstation_type"] = self.workstation_type
                    # self.meta_data_dictionry["inspection_station"] = self.inspection_station
                    # self.meta_data_dictionry["use_case"] = self.use_case
                    self.meta_data_dictionry["part_name"] = self.part_name
                    self.meta_data_dictionry["part_number"] = self.part_number
                    self.meta_data_dictionry["part_id"] = self.part_id
                    self.meta_data_dictionry["usecase_id"]=self.usecase_id
                    self.meta_data_dictionry["workstation_id"]=self.workstation_id
                    # self.meta_data_dictionry["camera"] = topic
                    self.meta_data_dictionry["camera_index"] = camera_index
                    self.meta_data_dictionry["image_name"] = image_name_with_format
                    self.meta_data_dictionry["image_file"] = filename
                    self.meta_data_dictionry["created_at"] = f"{current_datetime}"
                    self.meta_data_dictionry["platform"]="Edge+"
                    self.meta_data_dictionry["operation_type"]="golden_image_capture"
                    self.meta_data_dictionry["isdeleted"]=False
                    self.meta_data_dictionry["labelled"]=False

                    # meta data file will be create using self.meta_data_dictionary data
                    meta_data = self.meta_data_utils(topic, part_id_path,image_name)
    
                    # url_to_access_meta_data=self.http_server_for_meta_data_util(1278,part_id_path)
                    self.meta_data_dictionry = {}
                        
                     # It set the dictionary to have the new images meta data
                    self.image_count += 1
            return 153
        
        except Exception as e:
            print("error printing",str(e))
            CacheHelper().set_json({"golden_image_error":True})  
            return 180
        


class CobotGoldenImage(GoldenImage):
    """It inherit the GoldenImage base class for capture image and create meta data file"""

    def cobot_golden_image_record_waypoint(self,cobot_name):
        """
        Capture the golden image for cobot

        Arguments: None

        Response: "successfully zipped"
        """
        update_meta_data = []
        waypoint_count = 0


        try:
            CacheHelper().set_json({"golden_image_error":None})

            # wait for record_waypoint API hit to capture the waypoint golden image and meta data
            waypoint_info = {}

            waypoint_info["waypoint"] = self.waypoint
            # self.waypoint = waypoint

            # coordinates = [
            # ("move_type", "j"),
            # ("a", 1),
            # ("v", 1),
            # ("j1", -1.2453764120685022),
            # ("j2", -2.07605487505068),
            # ("j3", -1.460860554371969),
            # ("j4", -0.6070650259601038),
            # ("j5", 0.0015448415651917458),
            # ("j6", -0.0012224356280725601)
            # ]
            # coordinates={
            #     "move_type": "j",
            #     "a": 1,
            #     "v": 1,
            #     "j1": -1.2453764120685022,
            #     "j2": -2.07605487505068,
            #     "j3": -1.460860554371969,
            #     "j4": -0.6070650259601038,
            #     "j5": 0.0015448415651917458,
            #     "j6": -0.0012224356280725601,
            #     }

            # collect the coordinates of cobot                       ]
            cobot_coordinates=self.get_coordinates_util(self.waypoint,cobot_name)

            if cobot_coordinates==188:
                return 188
            
            # self.coordinates=cobot_coordinates
            # self.coordinates = coordinates

            # set the transit_point by default False
            waypoint_info["transit_point"] = False
            self.waypoint_info = waypoint_info

            # capture the golden image and create the meta data file for that image
            golden_image_status = self.capture_golden_images(cobot_name)

            if golden_image_status!=153:
                return golden_image_status

            return 156

        except Exception as e:
            print(str(e))
            CacheHelper().set_json({"golden_image_error":True})  
            return 157


    def cobot_golden_image_delete_waypoint(self,waypoint,part_id):
        """It deletes the last recorder waypoint details in both local image,meta data file and Localmongo document """

        try:
            CacheHelper().set_json({"golden_image_error":None})
            waypoint_data=[image_meta_data for image_meta_data in LocalMongoHelper().getCollection(f"cobot_golden_image_{part_id}").find({"waypoint":waypoint},{"image_file":1,"meta_data_file_name":1,"_id":0})]

            if len(waypoint_data) < 0:
                print("No waypoint is there to delete")
                CacheHelper().set_json({"there_is_no_waypoint_to_delete":True})
                return 158

            else:
                CacheHelper().set_json({"there_is_no_waypoint_to_delete":False})

                # get the data of last created waypoint to delete
                for image_file in waypoint_data:
                    image_file=image_file["image_file"]
                    if os.path.exists(image_file):
                        os.remove(image_file)  # Delete the file
                        print(f"File '{image_file}' deleted successfully.")
                    else:
                        print(f"File '{image_file}' does not exist.")

                for json_file in waypoint_data:
                    json_file=json_file["meta_data_file_name"]
                    if os.path.exists(json_file):
                        os.remove(json_file)  # Delete the file
                        print(f"File '{json_file}' deleted successfully.")
                    else:
                        print(f"File '{json_file}' does not exist.")
                
                LocalMongoHelper().getCollection(f"cobot_golden_image_{part_id}").delete_many({"waypoint":waypoint})
                return 158
            
        except Exception as e:
            print(str(e))
            CacheHelper().set_json({"golden_image_error":True})  
            return 159


    def cobot_golden_image_transit_point(self,waypoint,part_id,position_number,transit_status):
        """It updates the transit point and coordinate values data"""

        try:
            CacheHelper().set_json({"golden_image_error":None})

            #get the list of meta data json file to update transit status
            list_of_json_data_to_update_transit_status=[image["meta_data_file_name"] for image in LocalMongoHelper().getCollection(f"cobot_golden_image_{part_id}").find({"waypoint":waypoint},{"meta_data_file_name":1,"_id":0})]
            transit_status = self.update_transit_status(list_of_json_data_to_update_transit_status,part_id,waypoint,position_number,transit_status)
            return 160
        
        except Exception as e:
            print(str(e))
            CacheHelper().set_json({"golden_image_error":True})     
            return 161      


    def capture_golden_images(self,cobot_name):
        """
        captured the golden image and saves the meta data of that image as a json file

        Arguments: None

        Response: 153
        """
        try:
            data_dir = "data_lake/"
            part_id_path = os.path.join(
                data_dir, str(self.workstation_type) + "_golden_image_" + str(self.part_id)
            )
            if not os.path.exists(data_dir):
                print("not exist")
                os.mkdir(data_dir)
            if not os.path.exists(part_id_path):
                os.mkdir(part_id_path)

            print("part_id_path", part_id_path)

            filename = ""
            meta_data = ""
            image_and_meta_data_list = {"image_file_name":[],"json_file_name":[]}

            for camera_index,topic in enumerate(self.topic_list):
                details = []
                print("images captured start")

                current_datetime = datetime.now()

                # Format it as a string without milliseconds
                formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H:%M:%S:%f")

                # filename = part_id_path + "/" + str(self.part_id) + topic + ".jpg"
                image_name = (
                    str(self.part_id)
                    + "_"
                    + str(formatted_datetime)
                    + "_"
                    + str(self.waypoint)
                    + "_"
                    + str(self.image_count)
                )

                filename = part_id_path + "/" + image_name + ".jpg"
                captured_frame = self.get_frame(
                    topic
                )  # get the frames for respective topic

                if captured_frame is None or type(captured_frame)==int:
                    print("image_none_got")
                    CacheHelper().set_json({"golden_image_error":185}) 
                    return 185
                elif captured_frame.all()==185:
                    CacheHelper().set_json({"golden_image_error":185}) 
                    return 185
                else:
                    print("filename", filename)
                    cv2.imwrite(
                        filename, captured_frame
                    )  # images are saved in the part_id_path

                    image_and_meta_data_list["image_file_name"].append(filename)

                    # all the meta data is added to a dictionary to create the meta data json file
                    image_name_with_format = image_name + ".jpg"

                    self.meta_data_dictionry["workstation_type"] = self.workstation_type
                    # self.meta_data_dictionry["inspection_station"] = self.inspection_station
                    self.meta_data_dictionry["part_name"] = self.part_name
                    self.meta_data_dictionry["part_number"] = self.part_number
                    self.meta_data_dictionry["part_id"] = self.part_id
                    self.meta_data_dictionry["usecase_id"]=self.usecase_id
                    self.meta_data_dictionry["workstation_id"]=self.workstation_id
                    # self.meta_data_dictionry["camera"] = topic
                    self.meta_data_dictionry["camera_index"] = camera_index
                    self.meta_data_dictionry["image_name"] = image_name_with_format
                    self.meta_data_dictionry["image_file"] = filename
                    self.meta_data_dictionry["created_at"] = f"{current_datetime}"
                    self.meta_data_dictionry["platform"]="Edge+"
                    self.meta_data_dictionry["operation_type"]="golden_image_capture"
                    self.meta_data_dictionry["isdeleted"]=False
                    self.meta_data_dictionry["labelled"]=False

                    # meta data file will be create using self.meta_data_dictionary data
                    meta_data = self.meta_data_utils(topic, part_id_path,image_name)
                    print(meta_data)
                    image_and_meta_data_list["json_file_name"].append(meta_data)

                    self.meta_data_dictionry = {} # It set the dictionary to have the new images meta data    
                    self.image_count += 1
                
            return 153
        except Exception as e:
            print("error printing",str(e))
            CacheHelper().set_json({"golden_image_error":True})  
            return 180

    def get_coordinates_util(self, way_point,cobot_name):
        """
        get the current coordinates of cobot

        Arguments: waypoint

        Response:{
                "move_type": "j",
                "a": 1,
                "v": 1,
                "j1": -1.2453764120685022,
                "j2": -2.07605487505068,
                "j3": -1.460860554371969,
                "j4": -0.6070650259601038,
                "j5": 0.0015448415651917458,
                "j6": -0.0012224356280725601,
                }
        """
        try:
            if cobot_name=="urx":
                ip = "192.168.1.2"
                cobot_ip=COBOT_ADDRESS
                print(cobot_ip)
                robot_controller_urx = urx.Robot(ip)
                default_acc = 1
                default_vel = 1

                # get the coordination from the cobot
                data = robot_controller_urx.getj(wait=True)
                waypoint_dictionary = {"move_type": "j", "a": default_acc, "v": default_vel}

                for j in range(len(data)):
                    waypoint_dictionary["j" + str(j + 1)] = data[j]

                waypoint_dictionary["waypoint"] = way_point
                return waypoint_dictionary
            elif cobot_name=="doosan":
                # cobot_ip= use_case_data_of_part["IP"]
                # cobot_ip="192.168.1.15"
                # print(cobot_ip)
                # cobot_ip=cobot_details["workstation_type_detail"]["cobot_address"]
                # print(cobot_ip)
                # cobot_ip=COBOT_ADDRESS
                # print(cobot_ip)
                # robot_object=robot_controller(cobot_ip)
                # if not robot_object.status:
                #     CacheHelper().set_json({"golden_image_error":True})
                #     return 188
                # # print("robot_object_status",robot_object.status)      
                # else:
                #     print("position collection started")
                #     waypoint_position=robot_object.get_pos()
                #     self.coordinates=int(waypoint_position)
                #     print("self.coordinates:",self.coordinates)
                #     waypoint_dictionary ={ "coordinates":way_point}
                waypoint_position=4
                self.coordinates=int(waypoint_position)
                CacheHelper().set_json({"coordinates_number":waypoint_position})
                return self.coordinates
        except Exception as e:
            print(str(e))
            CacheHelper().set_json({"golden_image_error":True})  
            return 188


    def update_transit_status(self,list_of_json_data_to_update_transit_status,part_id,waypoint,position_number,transit_status):
        """
        Update the transit status in the meta data Json file

        Arguments: None

        Response: "successfully update transit status"
        """
        for json_file_path in list_of_json_data_to_update_transit_status:

            json_file = open(json_file_path)
            json_meta_data = json.load(json_file)
            json_file.close()
            if transit_status:
                json_meta_data["transit_point"] = transit_status
                print("transit_data: ",json_meta_data["transit_point"])
            if type(json_meta_data["coordinates"])==int:
                json_meta_data["coordinates"]=position_number
            # rewrite the meta data Json file
            with open(json_file_path, "w", encoding="utf-8") as json_file:
                json.dump(json_meta_data, json_file)

        part_configuration_file_path=f"data_lake/cobot_golden_image_{part_id}/part_configuration.json"
        
        part_configuration_json_file=open(part_configuration_file_path)
        part_configuration_data=json.load(part_configuration_json_file)
        part_configuration_json_file.close()

        part_configuration_data["waypoint"][waypoint]["transit_point"]=transit_status
        part_configuration_data["waypoint"][waypoint]["coordinates"]=position_number

        with open(part_configuration_file_path,"w",encoding="utf-8") as part_config_json_file:
            json.dump(part_configuration_data,part_config_json_file)

        LocalMongoHelper().getCollection(f"cobot_golden_image_{part_id}").update_many({"waypoint":waypoint},{"$set":{"transit_point":transit_status,"coordinates":position_number}})
        return "successfully update transit status"



class DataCapture:
    """Base class for DataCapture"""

    def __init__(
        self,
        use_case_list=[],
        topic_list=[],
        part_id=None,
        part_name=None,
        part_number=None,
        workstation_type=None,
        waypoint=None,
        coordintaes=[],
        waypoint_info={},
    ):
        self.use_case_list = use_case_list
        self.use_case = None
        self.topic_list = topic_list
        self.part_id = part_id
        self.part_name = part_name
        self.part_number= part_number
        self.workstation_type = workstation_type
        self.waypoint = waypoint
        self.coordinates = coordintaes
        self.waypoint_info = waypoint_info
        self.image_count = 0
        self.tag_status = None
        self.meta_data_dictionry = {}
        self.image_name_list=[]


    def start_capture_image(self,cycle_number):
        """
        captured the golden image and saves the meta data of that image as a json file

        Arguments: None

        Response: list of captured image name
        """
        try:
            CacheHelper().set_json({"data_capture_error":None})  
            data_dir = "data_lake/"
            part_id_path = os.path.join(
                data_dir, str(self.workstation_type) + "_data_capture_" + str(self.part_id)
            )
            if not os.path.exists(data_dir):
                os.mkdir(data_dir)
            if not os.path.exists(part_id_path):
                os.mkdir(part_id_path)

            # if self.tag_status == "OK":
            #     part_id_path = os.path.join(part_id_path + "/", str(self.tag_status))
            #     if not os.path.exists(part_id_path):
            #         os.mkdir(part_id_path)
            # elif self.tag_status == "NG":
            #     part_id_path = os.path.join(part_id_path + "/", str(self.tag_status))
            #     if not os.path.exists(part_id_path):
            #         os.mkdir(part_id_path)
            # else:
            #     part_id_path = os.path.join(part_id_path + "/unsorted")
            #     if not os.path.exists(part_id_path):
            #         os.mkdir(part_id_path)
            if self.tag_status=="OK" or self.tag_status=="NG":
                tag_status=self.tag_status
            else:
                tag_status="UNSORTED"
            print("part_id_path", part_id_path)

            filename = ""
            meta_data = ""
            image_list = []

            for index,topic in enumerate(self.topic_list):
                print("topic:",topic)
                details = []
                print("images captured start")

                current_datetime = datetime.now()
                # Format it as a string without milliseconds
                formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H:%M:%S")
                image_name = (
                    str(self.part_id)
                    + "_"
                    + str(formatted_datetime)
                    + "_"
                    + str(self.waypoint)
                    + "_"
                    + str(self.image_count)
                )

                filename = part_id_path + "/" + image_name + ".jpg"

                captured_frame = self.get_frame(
                    topic
                )  # get the frames for respective topic
                if captured_frame is None:
                    CacheHelper().set_json({"data_capture_error":185}) 
                    return 185
                elif captured_frame.all()==185 :
                    CacheHelper().set_json({"data_capture_error":185}) 
                    return 185
                else:
                    print("filename", filename)
                    cv2.imwrite(
                        filename, captured_frame
                    )  # images are saved in the part_id_path

                    image_list.append(filename)

                    # all the meta data is added to a dictionary to create the meta data json file
                    image_name_with_format = image_name + ".jpg"

                    self.meta_data_dictionry["workstation_type"] = self.workstation_type
                    # self.meta_data_dictionry["inspection_station"] = self.inspection_station
                    self.meta_data_dictionry["use_case"] = self.use_case
                    self.meta_data_dictionry["part_name"] = self.part_name
                    self.meta_data_dictionry["part_id"] = self.part_id
                    # self.meta_data_dictionry["camera"] = topic
                    self.meta_data_dictionry["camera_index"] = index
                    self.meta_data_dictionry["image_name"] = image_name_with_format
                    self.meta_data_dictionry["image_file"] = filename
                    self.meta_data_dictionry["date_time"] = datetime.now().isoformat()
                    self.meta_data_dictionry["labelled"] = False
                    self.meta_data_dictionry["annotation_detection"] = []
                    self.meta_data_dictionry["operation_type"] = "capture"
                    self.meta_data_dictionry["platform"] = "Edge+"
                    self.meta_data_dictionry["isdeleted"] = False
                    self.meta_data_dictionry["cycle"] = cycle_number
                    self.meta_data_dictionry["tag_status"]=tag_status
                    self.meta_data_dictionry["good"]=False
                    self.meta_data_dictionry["bad"]=False
                    self.meta_data_dictionry["unsorted"]=False
                    if tag_status=="OK":
                        self.meta_data_dictionry["good"]=True
                    elif tag_status=="NG":
                        self.meta_data_dictionry["bad"]=True
                    else:
                        self.meta_data_dictionry["unsorted"]=True

                    print("datails list:", details)

                    # meta data file will be create using self.meta_data_dictionary data
                    meta_data = self.meta_data_utils(topic, part_id_path, image_name)
                    print(meta_data)

                    self.meta_data_dictionry = (
                        {}
                    )  # It set the dictionary to have the new images meta data
                    self.image_count += 1
            self.image_name_list.extend(image_list)
            print("image captured -message code is 164")
            return 164
        
        except Exception as e:
            print("error printing",str(e))
            CacheHelper().set_json({"data_capture_error":180})  
            return 180
        
    def get_frame(self, topic):
        """
        Get the frame for respective topic subscribed

        Arguments:
            topic

        Response:
            decoded_image
        """

        timeout_ms=kAFKA_FRAME_TIMEOUT_MS
        try:
            # consumer = KafkaConsumer(topic_name, bootstrap_servers=BOOTSTRAP_SERVERS,consumer_timeout_ms=timeout_ms)         
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=BOOTSTRAP_SERVERS,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id=str(uuid.uuid1()),
                consumer_timeout_ms=timeout_ms
            )

            # do a dummy poll to retrieve some message
            consumer.poll()

            # go to end of the stream
            consumer.seek_to_end()
            print(consumer)
            
            #geth the frames from the camera using kafka consumer and decoded the frames
            for message in consumer:
                print("Hello World Consumer")
                decoded_frame = cv2.imdecode(np.frombuffer(message.value, np.uint8), 1)
                return decoded_frame
                # break
            print("Frame not found after timeout set")
            return None
        
        except Exception as e:
            print("Frame error: ",e)
            if 'NoBrokersAvailable' in str(e):
                CacheHelper().set_json({"data_capture_error":True}) 
                return 185
            else:
                return 180

    def meta_data_utils(self, topic, part_id_path, image_name):
        """
        This method calls other methods to calculate the image resolution and
        creating meta data for image in the same directory.

        Arguments: [topic,part_id_path]

        Response: "image meta data stored successfully"
        """

        image_path = self.meta_data_dictionry["image_file"]

        resolution = self.get_image_resolution(
            image_path
        )  # Resolution of the image will be get using this function
        print(resolution)

        if resolution:
            # final_resolution = (
            #     str(resolution[0]) + " x " + str(resolution[1]) + " pixels"
            # )
            # self.meta_data_dictionry["image_resolution"] = final_resolution

            self.meta_data_dictionry["image_public_url"]=""
            self.meta_data_dictionry["metadata"]={}
            self.meta_data_dictionry["metadata"]["image_width"] = resolution[0]
            self.meta_data_dictionry["metadata"]["image_height"] = resolution[1]
            self.meta_data_dictionry["metadata"]["format"]="jpg"
            self.meta_data_dictionry["metadata"]["size"]=resolution[2]

            meta_data_status = self.save_resolution_and_image_path_to_text_file(
                part_id_path, image_name
            )
            print(meta_data_status)

            return meta_data_status
        else:
            print("Failed to read image or invalid image format.")
            return "Failed to read image or invalid image format."

    def get_image_resolution(self, image_path):
        """
        This function is calculating the image resolution of an image from the directory.

        Arguments: image_path

        Response: (1280,720)
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size  # get the frame size
                file_size= os.stat(image_path)
                file_size_in_bytes=file_size.st_size
                return width, height ,file_size_in_bytes
                # return width, height
        except Exception as e:
            print("error exception:", e)
            return 0,0

    def save_resolution_and_image_path_to_text_file(
        self, part_id_path, image_name
    ):
        """
        It create the meta data json file

        Arguments : [part_id_path, image_name]

        Response: "image meta data stored successfully"
        """

        # filename = image_name
        text_file_path = f"{part_id_path}/{image_name}.json"
        print("text_file_path", text_file_path)
        self.meta_data_dictionry["meta_data_file_name"]=text_file_path

        if self.workstation_type == "cobot":
            self.meta_data_dictionry["waypoint"] = self.waypoint
            self.meta_data_dictionry["coordinates"] = self.coordinates
            # self.meta_data_dictionry["transit_point"]=self.waypoint_info["transit_point"]

        collection_name=str(self.workstation_type) + "_data_capture_" + str(self.part_id)
        insertion_id=LocalMongoHelper().getCollection(collection_name).insert_one(self.meta_data_dictionry).inserted_id 

        del self.meta_data_dictionry["image_file"]
        del self.meta_data_dictionry["meta_data_file_name"]
        del self.meta_data_dictionry["_id"]

        with open(text_file_path, "w") as json_file_1:
            json.dump(self.meta_data_dictionry, json_file_1)
        return text_file_path

        # print("details list check:", self.meta_data_dictionry)

        # with open(text_file_path, "w") as json_file:
        #     json.dump(self.meta_data_dictionry, json_file)

        # meta_mongo_backup_status=self.meta_mongo_backup(text_file_path)

        # return "image meta data stored successfully"


    def meta_mongo_backup(self, text_file_path):
        """Update the meta data in Local Mongo"""

        collection_name=str(self.workstation_type) + "_data_capture_" + str(self.part_id)

        with open(text_file_path) as file:
            file_data = json.load(file)

        insertion_id=LocalMongoHelper().getCollection(collection_name).insert_one(file_data) 

        return insertion_id


    def upload_data_capture(self):
        """
        Zip the entire file of the part

        Arguments: None

        Response: "successfully zipped"
        """
        try:
            print("upload startiing")
            CacheHelper().set_json({"data_capture_upload_error":None})
            folder_to_be_delete = "data_lake/"
            zip_file_name = f"{self.workstation_type}_data_capture_{self.part_id}.zip"

            with zipfile.ZipFile(zip_file_name, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_to_be_delete):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, folder_to_be_delete)
                        zipf.write(file_path, arcname)
            print("zip complete now")
            after_zip_local_folder_delete_status=self.remove_the_directory()
            if after_zip_local_folder_delete_status:
                return zip_file_name  
            else:
                return False   

        except Exception as e:
            print(str(e))
            CacheHelper().set_json({"data_capture_upload_error":True})  
            return 163
        
    def remove_the_directory(self):
        """It remove the directory once file is uploaded"""

        directory_to_delete = f"data_lake/{self.workstation_type}_data_capture_{self.part_id}"

        
    def remove_the_directory(self):
        """It remove the directory once file is uploaded"""

        directory_to_delete = f"data_lake/{self.workstation_type}_data_capture_{self.part_id}"

        try:
            shutil.rmtree(directory_to_delete)
            print(f"Directory '{directory_to_delete}' and its contents have been deleted successfully.")
            LocalMongoHelper().getCollection(f"{self.workstation_type}_data_capture_{self.part_id}").delete_many({})
            return True
        except OSError as e:
            print(f"Error: {e.strerror}") 
            return False    

class StaticDataCapture(DataCapture):
    """Data capture for static workstation"""

    def static_data_capture(self,cycle_number):

        try:                   
            CacheHelper().set_json({"data_capture_error":None})
            self.use_case = CacheHelper().get_json("use_case")
            self.tag_status = CacheHelper().get_json("sort_tag")
            print("tag_status: ", self.tag_status)

            # It capture the image and create the meta data 
            capture_image = self.start_capture_image(cycle_number)
            CacheHelper().set_json({"sort_tag": None})
            return capture_image

        except Exception as e:
            print(str(e))
            CacheHelper().set_json({"data_capture_error":True})
            return 180


class ConveyorDataCapture(DataCapture):
    """Data capture for static workstation"""        

    def conveyor_data_capture(self,plc_configuration):
        conveyor_started=False
        try:
            CacheHelper().set_json({"data_capture_error":None})
            print("conveyor started")
            #It will start the conveyor and capture the image if it gets the trigger
            # self.start_conveyor_process(plc_configuration,self.workstation_type)
            self.start_conveyor_process_without_plc()
            conveyor_started=True
            print("multiprocess successfully")
            self.use_case = CacheHelper().get_json("use_case")
            self.tag_status = CacheHelper().get_json("sort_tag")
            print("tag_status: ", self.tag_status)

            self.start_capture_image_after_plc_trigger()
            return 172
        
        except Exception as e:
            print(str(e))
            # CacheHelper().set_json({"data_capture_error":True})  
            if conveyor_started:
                CacheHelper().set_json({"data_capture_error":173})  
                return 173
            else:
                CacheHelper().set_json({"data_capture_error":174})  
                return 174


    def start_capture_image_after_plc_trigger(self):

        """It capture the data if PLC get the trigger to capture"""

        while CacheHelper().get_json("start_conveyor"):
            CacheHelper().set_json({"capture_image_status":173})
            print("In loop conveyor become true")
            #If PLC trigger get hit then start capturing images
            if CacheHelper().get_json("trigger_capture"):
                print("tigger capture become true")
                capture_image = self.start_capture_image()

                CacheHelper().set_json({"capture_image_status":capture_image})

                CacheHelper().set_json({"sort_tag": None})

                CacheHelper().set_json({"trigger_capture":False})

                time.sleep(5)
                CacheHelper().set_json({"isAccepted":True})    
            time.sleep(4)    

    def start_conveyor_process(self,plc_configuration,workstation_type):

        """Conveyor process started as a multiprocess and gives the trigger to capture images if  PLC gets the input trigger """

        global conveyor_trigger_process
        conveyor_trigger_process = multiprocessing.Process(target=conveyor_main,args=(plc_configuration,workstation_type),daemon=True)
        conveyor_trigger_process.start()

    def start_conveyor_process_without_plc(self):
        print("conveyor multithreading started")
        conveyor_trigger_process = threading.Thread(target=self.conveyor_without_plc,args=(),daemon=True)
        # conveyor_trigger_process = threading.Thread(target=conveyor_without_plc,args=(),daemon=True)
        print("multiprocess going tostart")
        conveyor_trigger_process.start()
        print("multiprocess start done")

    def conveyor_without_plc(self):
        print("inside the thread func")
        try:
            while not CacheHelper().get_json("is_stop_conveyor"): 
                print("multithhreading working fine")
                CacheHelper().set_json({"trigger_capture":True})
                print("tigger_capture_status",CacheHelper().get_json("trigger_capture"))
                time.sleep(4)
        except:
            CacheHelper().set_json({"start_conveyor": False})
            CacheHelper().set_json({"is_stop_conveyor": True})
        


class CobotDataCapture(DataCapture):
    """Data capture for cobot workstation"""

    def cobot_data_capture(self,cycle_number,workstation_data,waypoint_dictionary):

        try:
            CacheHelper().set_json({"data_capture_error":None})
            print("inside the cycle")
            self.use_case = CacheHelper().get_json("use_case")

            cobot_name=workstation_data["workstation_type_detail"]["cobot_name"]
            waypoint_list=[]
            for waypoint in waypoint_dictionary.keys():
                print("waypoint_inter:",waypoint)
                waypoint_details={"coordinates":waypoint_dictionary[waypoint]["coordinates"],"waypoint":waypoint}
                waypoint_list.append(waypoint_details)

            CacheHelper().set_json({"is_data_capture_cycle_completed":False})
            if cobot_name == "urx":
                CacheHelper().set_json({"data_capture_status":False})
                # ip = "192.168.1.2"
                # ip=cobot_details["workstation_type_detail"]["cobot_address"]
                # cobot_ip=COBOT_ADDRESS
                # print(cobot_ip)
                # robot_controller_urx = urx.Robot(ip)  
                capture_image_status=False
                for pos in waypoint_list:
                    CacheHelper().set_json({"data_capture_status":False})
                    capture_image_status=False
                    self.waypoint = pos
                    # if pos["move_type"] == "j":
                    if pos[0]["move_type"] == "j":

                        # robot_controller_urx.movej(
                        #     [pos["j1"], pos["j2"], pos["j3"], pos["j4"], pos["j5"], pos["j6"]],
                        #     pos["a"],
                        #     pos["v"],
                        #     wait=False,
                        # )
                        # time.sleep(0.1)
                        # while 1:
                        #     if robot_controller_urx.is_program_running():
                        #         print("Robot Started Moving")
                        #         break
                        # while 1:
                        #     if robot_controller_urx.is_program_running():
                        
                        #        # print(r.getj(wait=True))
                        #         # time.sleep(0.1)
                        #         pass
                        #     else:
                        #         print("Robot Stopped")
                        #         # print(r.getj(wait=True))
                        #         # time.sleep(1)
                        #         break

                        self.tag_status = CacheHelper().get_json("sort_tag")
                        print("tag_status: ", self.tag_status)
                        capture_image_status = self.start_capture_image(cycle_number)
                        if capture_image_status:
                            CacheHelper().set_json({"data_capture_status":True})
                if capture_image_status:
                    CacheHelper().set_json({"is_data_capture_cycle_completed":True})
                    return capture_image_status
            # elif use_case_data_of_part["cobot_name"]== "doosan":
            elif cobot_name== "doosan":

                # waypoint_list= cobot_configuration["waypoint_list"]

                # cobot_ip= use_case_data_of_part["IP"]
                # print(cobot_ip)
                # cobot_ip=cobot_details["workstation_type_detail"]["cobot_address"]
                # print(cobot_ip)
                # cobot_ip=COBOT_ADDRESS
                # print(cobot_ip)
                # robot_object=robot_controller(cobot_ip)
                # if not robot_object.status:
                #     CacheHelper().set_json({"data_capture_error":True})
                #     return 188
                # # print("robot_object_status",robot_object.status)
                # else:
                
                    print("inside doosan robot")
                    CacheHelper().set_json({"data_capture_status":False})
                    capture_image_status=False
                    print("h123")
                    for waypoint in waypoint_list:
                        print("ADFD123")
                        CacheHelper().set_json({"data_capture_status":False})
                        capture_image_status=False
                        print("waypoint",waypoint)
                        print("waypoint_coordinates",waypoint["coordinates"])
                        cobot_coordinate=int(waypoint["coordinates"])
                        # robot_object.move_pos(cobot_coordinate)   
                        self.coordinates=waypoint["coordinates"]
                        self.waypoint=waypoint["waypoint"]

                        self.tag_status = CacheHelper().get_json("sort_tag")
                        print("tag_status: ", self.tag_status)
                        capture_image_status = self.start_capture_image(cycle_number)
                        if capture_image_status:
                            CacheHelper().set_json({"data_capture_status":True})
                        time.sleep(1)
                    if capture_image_status:
                        CacheHelper().set_json({"sort_tag": None})
                        CacheHelper().set_json({"is_data_capture_cycle_completed":True})
                        return capture_image_status
            else:
                CacheHelper().set_json({"data_capture_error":True})
                return 165

            # print(waypoint_list)
            print("Cycle is completed")

            CacheHelper().set_json({"sort_tag": None})
            return capture_image_status
        
        except Exception as e:
            CacheHelper().set_json({"data_capture_error":True})
            print("error occurs",str(e))
            if 'timed out' in str(e):
                return 188
            else:          
                return 180
            
def find_the_usecase_name_from_usecase_collection(usecase_id):
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