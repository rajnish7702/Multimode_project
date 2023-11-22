from flask import Blueprint, request, jsonify, redirect, url_for,stream_with_context,Response
import json
from bson.json_util import dumps
from .part_capture_util import *

# from .utils import *
import socket
import time
# from loguru import logger
import requests
from docker import errors
from bson import json_util
from bson import ObjectId

views = Blueprint("views", __name__)

GOLDEN_IMAGE_PAYLOAD_PARAMETER=["part_id"]
GOLDEN_IMAGE_UPLOAD_PAYLOAD_PARAMETER=["part_id"]
GOLDEN_IMAGE_PAYLOAD_PARAMETER_FOR_UPDATE=["part_id","position_number","transit_point","waypoint"]
DATA_CAPTURE_PAYLOAD_PARAMETER=["workstation_id","part_number"]
DATA_CAPTURE_PAYLOAD_PARAMETER_FOR_USECASE=["workstation_id","usecase_id","part_number","usecase"]
DATA_CAPTURE_PAYLOAD_PARAMETER_FOR_PLC=["use_case_list","topic_list","part_id","part_name","workstation_type","plc_configuration"]
DATA_CAPTURE_UPLOAD_PAYLOAD_PARAMETER=["part_id"]

@views.route("/")
def hello_world():
    return "Hello, World! --- part_capture"

@views.route("/get_temp_parts_for_workstation/<workstation_id>",methods=["GET"])
def get_temp_parts_for_workstation(workstation_id):
    """
    Get all the parts in the workstation 

    Payload: None

    Response:
            {
                "message": 189,
                "data": {
                    "part_data": [
                        {
                            "_id": {
                                "$oid": "651d3f97ebca3cff29ab523f"
                            },
                            "part_name": "Grinding part45",
                            "part_number": "grd145",
                            "usecase_id": "651ae572d1d926dfcdf36c97",
                            "usecase_name": "welding defects"
                        },
                        {
                            "_id": {
                                "$oid": "651d39b5ebca3cff29ab5226"
                            },
                            "part_name": "Grinding part1",
                            "part_number": "grd123",
                            "usecase_id": "651c2526e8d8215df8b14eea",
                            "usecase_name": "milling defects"
                        },
                        {
                            "_id": {
                                "$oid": "651d3f41ebca3cff29ab523a"
                            },
                            "part_name": "Grinding part45",
                            "part_number": "grd145",
                            "usecase_id": "651c2526e8d8215df8b14eea",
                            "usecase_name": "milling defects"
                        },
                    ],
                    "workstation_type": "static",
                    "total": 3
                }
            }
    """ 

    if request.method=="GET":

        check_internet_connection= check_internet()
        if not check_internet_connection:
            result ={"message":109,
                    "data":{"part_data":[],"total":0}},
            response = Response(response=json.dumps(result),status=503,mimetype='application/json')
            return response
        else:
            authorization_token=fetch_the_authorization_token_util()
            # authorization_token="Bearer 74l5fa2R5j0o48wC8D9YeIwbTrPA05"
            if not authorization_token:
                result ={"message":5,
                    "data":{"part_data":[],"total":0}}
                response = Response(response=json.dumps(result),status=401,mimetype='application/json')
                return response    
            else:
                #get the list of part with the respective workstation_id
                url = f"https://v2.livis.ai/api/livis/v2/parts/get_temp_parts_for_workstation/{workstation_id}"

                headers = {"Content-Type": "application/json",
                           "Authorization":authorization_token}

                # sending request data and getting response all the parts belongs to the respective workstation
                api_geteway_response = requests.request("GET", url, headers=headers)
                print("api_geteway_response:",api_geteway_response)
                
                if api_geteway_response.status_code==200:
                    api_geteway_response = api_geteway_response.json()
                    print("api_geteway_response:",api_geteway_response)
                    # #If the data from the api gateway is not valid return the error response
                    if not api_geteway_response:
                        result ={"message":183,
                            "data":{"part_data":[],"total":0}}
                        response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                        return response      
                    elif not len(api_geteway_response["data"])>0:
                        result ={"message":194,
                            "data":{"part_data":[],"total":0}}
                        response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                        return response
                    else:
                        temp_part_data=get_part_details_list(api_geteway_response["data"])

                        result ={"message":189,
                                "data":{"part_data":temp_part_data,
                                        "workstation_type":api_geteway_response["data"][0]["workstation_type"],
                                        "total":2}}
                            
                        response = Response(response=json.dumps(result),status=200,mimetype='application/json')
                        return response
                else:
                    result ={"message":183,
                        "data":{"part_data":[],"total":0}}
                    response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                    return response    
    else:
        result ={"message":187,
              "data":{"request type":[],"total":0}}
        response = Response(response=json.dumps(result),status=405,mimetype='application/json')
        return response


@views.route("/golden_image_edge_connect/<temp_part_id>",methods=["GET"])
def golden_image_edge_connect(temp_part_id):
    """
    captured the golden image of part

    Payload: None

    Response:
            {"message":182,
                    "data":{"part_data":[{
                                            "_id": {
                                                "$oid": "64d4eb2fccd50444cbd570ec"
                                            },
                                            "part_name": "milling part1",
                                            "part_number": "1001",
                                            "part_description": "",
                                            "part_ocr": true,
                                            "part_barcode": true,
                                            "part_status": true,
                                            "usecase_id": "64d4eb0de682e33b52ea2eba",
                                            "workstation_id": "64d4eab6bc3026ca570f2f48",
                                            "workstation_type": "cobot",
                                            "cobot": [],
                                            "conveyor": [],
                                            "static": [],
                                            "plc": [],
                                            "features": [],
                                            "defects": [],
                                            "feature_count": 0,
                                            "defect_count": 0,
                                            "size": 0,
                                            "label_info": {
                                                "total_images": 0,
                                                "total_labelled_images": 0,
                                                "total_unlabelled_images": 0
                                            },
                                            "ready_to_train": false,
                                            "isdeleted": false,
                                            "created_by": "shyam@livis.ai",
                                            "created_at": "2023-08-10 19:20:39"
                                            }]
    """ 

    if request.method=="GET":

        check_internet_connection= check_internet()
        if not check_internet_connection:
            result ={"message":109,
                    "data":{"part_data":[],"total":0}},
            response = Response(response=json.dumps(result),status=503,mimetype='application/json')
            return response
        
        else:
            authorization_token=fetch_the_authorization_token_util()
            # authorization_token="Bearer 74l5fa2R5j0o48wC8D9YeIwbTrPA05"
            if not authorization_token:
                result ={"message":5,
                    "data":{"part_data":[],"total":0}}
                response = Response(response=json.dumps(result),status=401,mimetype='application/json')
                return response    
            else:
                part_data=LocalMongoHelper().getCollection("temp_part_data").find_one({"_id":ObjectId(temp_part_id)})
                print("part_data:",part_data)
                #If the data from the local mongo is not valid return the error response
                if not part_data:
                    print("data is not fpound")
                    result ={"message":183,
                        "data":{"part_data":[],"total":0}}
                    response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                    return response  
                    
                else:  
                    print("data is found")
                    workstation_id=part_data["workstation_id"]
                    #Establish the connection between livis and Edge plus
                    url = f"https://v2.livis.ai/api/livis/v2/data_management/establish_connection/"

                    headers = {"Content-Type": "application/json",
                            "Authorization":authorization_token}
                    payload={"workstation_id":workstation_id,
                            "temp_part_id":temp_part_id}
                    
                
                    api_geteway_response = requests.patch( url, headers=headers,json=payload)
           
                    print("api_geteway_response:",api_geteway_response)
                    if api_geteway_response.status_code==200:
                        api_geteway_response = api_geteway_response.json()
                          
                        camera_list=part_data["workstation_cameras"]
                        workstation_type= part_data["workstation_type"]

                        topic_list=[]
                        for camera_name in camera_list:
                            topic_list.append(camera_name["camera_name"].replace(" ",""))

                        if not topic_list:
                            result ={"message":183,
                                "data":{"part_data":[],"total":0}}
                            response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                            return response 
                        
                        #spawn the camera conatiner and assign the camera name as acontainer name
                        container_deployed= spawn_the_camera_conatiner_util(topic_list)

                        if not container_deployed:
                            res = {"message":190,
                                    "data":{"edge_connect":[],"total":0}}
                            return Response(response=json.dumps(res),status=503,mimetype='application/json')
                        else:
                            if workstation_type=="cobot":
                                local_collection=f"{workstation_type}_golden_image_{temp_part_id}"      
                                waypoint_document=LocalMongoHelper().getCollection(local_collection).find_one(sort=[("_id", -1)])

                                if waypoint_document is None:
                                    waypoint="P0"
                                else:
                                    last_waypoint=waypoint_document["waypoint"]
                                    waypoint_count=int(last_waypoint[1])+1
                                    waypoint=f"P{waypoint_count}"   

                                part_data["_id"]={"$oid":str(part_data["_id"])}
                                result ={"message":182,
                                    "data":{"part_data":[part_data],
                                            "last_waypoint":waypoint,"total":2}}
                                response = Response(response=json.dumps(result),status=200,mimetype='application/json')
                                return response
                            else:
                                part_data["_id"]={"$oid":str(part_data["_id"])}
                                result ={"message":182,
                                    "data":{"part_data":[part_data],"total":1}}
                                response = Response(response=json.dumps(result),status=200,mimetype='application/json')
                                return response
                            
                    else:
                        result ={"message":195,
                            "data":{"part_data":[],"total":0}}
                        response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                        return response  
    else:
        result ={"message":187,
              "data":{"request type":[],"total":0}}
        response = Response(response=json.dumps(result),status=405,mimetype='application/json')
        return response


@views.route("/capture_static_golden_image", methods=["POST"])
def capture_static_golden_image():
    """
    captured the golden image of part

    Payload: 
        {

            "topic_list":["Cam3","Cam1", "Cam2"],
            "part_id":"64d4eb2fccd50444cbd570ec",
            "part_name":"ABS",
            "workstation_type":"static"
            }

    Response: {"message":164,
                "data":{"golden_image":[],"total":0}}
    """
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):

        data = json.loads(request.data)
        part_id = data.get("part_id")

        data_validate_result=validate_required_data(GOLDEN_IMAGE_PAYLOAD_PARAMETER,data)

        if not data_validate_result:
                res =[{"message":184,"data":{"golden_image":[],"total":0}}]
                response = Response(response=json.dumps(res),status=422,mimetype='application/json')
                return response
        else:
            part_data=LocalMongoHelper().getCollection("temp_part_data").find_one({"_id":ObjectId(part_id)})

            #If the data from the local mongo is not valid return the error response
            if not part_data:
                result ={"message":183,
                    "data":{"part_data":[],"total":0}}
                response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                return response      
            else:
                # inspection_station="TATA45"
                camera_list=part_data["workstation_cameras"]
                workstation_type= part_data["workstation_type"]

                topic_list=[]
                for camera_name in camera_list:
                    topic_list.append(camera_name["camera_name"].replace(" ",""))

                part_name = part_data["part_name"]
                part_number= part_data["part_number"]
                usecase_id=part_data["usecase_id"]
                workstation_id=part_data["workstation_id"]                          
                waypoint="P0"

                static_golden_image_status=static_golden_images_util(
                    topic_list,part_id,part_name,workstation_type,usecase_id,workstation_id,part_number,waypoint,
                )

                image_file_render_url=image_file_render_url_util(workstation_type,part_id,topic_list)

                #check if there is any error occurs while capturing image 
                if CacheHelper().get_json("golden_image_error") or not image_file_render_url:
                    CacheHelper().set_json({"golden_image_error":None})
                    res = {"message":static_golden_image_status,
                            "data":{"golden_image":[],"total":0}}
                    return Response(response=json.dumps(res),status=503,mimetype='application/json')
                
                #check if there is any error occurs while creating HTTP server 
                elif not image_file_render_url:
                    res = {"message":191 ,
                            "data":{"golden_image":[],"total":0}}
                    return Response(response=json.dumps(res),status=501,mimetype='application/json')
                else:

                    res = {"message":static_golden_image_status,
                            "data":{"golden_image":image_file_render_url,"total":len(image_file_render_url)}}
                    return Response(response=json.dumps(res),status=200,mimetype='application/json')
    else:
        res={"message":186,
            "data":{"golden_image":[],"total":0}}
        response = Response(response=json.dumps(res),status=415,mimetype='application/json')
        return response


@views.route("/golden_image_upload", methods=["POST"])
def golden_image_upload():
    """
    All the catpured data are zipped

    Payload: {
            
            "use_case":"M1",
            "topic_list":["Cam3","Cam1", "Cam2"],
            "part_id":"64d4eb2fccd50444cbd570ec",
            "part_name":"ABS",
            "workstation_type":"static"}

    Response: {"message":150,
               "data":{"golden_image":[],"total":0}}
    """
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):

        check_internet_connection= check_internet()
        if not check_internet_connection:
            result ={"message":109,
                    "data":{"golden_image":[],"total":0}},
            response = Response(response=json.dumps(result),status=503,mimetype='application/json')
            return response
        else:
            data = json.loads(request.data)         
            part_id = data.get("part_id")

            data_validate_result=validate_required_data(GOLDEN_IMAGE_UPLOAD_PAYLOAD_PARAMETER,data)

            if not data_validate_result:
                    res =[{"message":184,"data":{"golden_image":[],"total":0}}]
                    response = Response(response=json.dumps(res),status=422,mimetype='application/json')
                    return response
            else:
                part_data=LocalMongoHelper().getCollection("temp_part_data").find_one({"_id":ObjectId(part_id)})

                #If the data from the local mongo is not valid return the error response
                if not part_data:
                    result ={"message":183,
                        "data":{"part_data":[],"total":0}}
                    response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                    return response      
                else:
                    # inspection_station="TATA45"
                    camera_list=part_data["workstation_cameras"]
                    workstation_type= part_data["workstation_type"]

                    topic_list=[]
                    for camera_name in camera_list:
                        topic_list.append(camera_name["camera_name"].replace(" ",""))

                    part_name = part_data["part_name"]
                    workstation_id=part_data["workstation_id"]
                    waypoint="P0"   

                    zip_file_name=golden_images_upload_util(
                        topic_list,part_id,part_name,workstation_type,waypoint
                    )

                    #check if there is any error occurs while zipping the captured data
                    if CacheHelper().get_json("golden_image_upload_error") or not zip_file_name:
                        CacheHelper().set_json({"golden_image_upload_error":None})
                        res = {"message":151,
                                "data":{"golden_image":[],"total":0}}
                        return Response(response=json.dumps(res),status=503,mimetype='application/json')
                    else:
                        authorization_token=fetch_the_authorization_token_util()
                        # authorization_token="Bearer 74l5fa2R5j0o48wC8D9YeIwbTrPA05"
                        if not authorization_token:
                            result ={"message":5,
                                    "data":{"part_data":[],"total":0}}
                            response = Response(response=json.dumps(result),status=401,mimetype='application/json')
                            return response  
                        else:
                            #uploading the zip file to the cloud
                            print("part_id:",part_id,"workstation_id",workstation_id,"zip_file",zip_file_name)
                            url = f"https://v2.livis.ai/api/livis/v2/data_management/upload_golden_images/"
                            form_data = {
                                                "temp_part_id":part_id,
                                                "workstation_id":workstation_id,                                                                                       
                                                }
                            file_path = f"{os.getcwd()}/{zip_file_name}"
                            headers = {"Authorization":authorization_token}
                            with open(file_path, 'rb') as file:
                                api_geteway_response = requests.post(url, headers=headers,files={'zip_file': (file.name, file, 'application/zip')}, data=form_data)
                            result = api_geteway_response.json()

                            print("api_geteway_response", result)
                            if api_geteway_response.status_code==200:
                                res = {"message":150,
                                        "data":{"golden_image":[],"total":0}}
                                return Response(response=json.dumps(res),status=200,mimetype='application/json')
                            else:
                                res = {"message":151,
                                        "data":{"golden_image":[],"total":0}}
                                return Response(response=json.dumps(res),status=417,mimetype='application/json')
    else:
        res={"message":186,
            "data":{"golden_image":[],"total":0}}
        response = Response(response=json.dumps(res),status=415,mimetype='application/json')
        return response


@views.route("/record_waypoint", methods=["POST"])
def record_waypoint():
    """
    Record the coordinates of cobots for respective waypoint

    Payload:{
            
            "use_case":"M1",
            "topic_list":["Cam3","Cam1", "Cam2"],
            "part_id":"64d4eb2fccd50444cbd570ec",
            "part_name":"ABS",
            "workstation_type":"cobot",
            "waypoint":"P0",
            "position_number":23,
            "cobot_name":"urx",
            "IP":"192.168.1.2"
            }

    Response: {"message":156,
               "data":{"golden_image":[IMAGE_AND_META_LIST_FOR_LAST_WAYPOINT],"total":5}}
    """

    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = json.loads(request.data)
        part_id = data.get("part_id")

        data_validate_result=validate_required_data(GOLDEN_IMAGE_PAYLOAD_PARAMETER,data)

        if not data_validate_result:
                res =[{"message":184,"data":{"golden_image":[],"total":0}}]
                response = Response(response=json.dumps(res),status=422,mimetype='application/json')
                return response
        else:
            part_data=LocalMongoHelper().getCollection("temp_part_data").find_one({"_id":ObjectId(part_id)})

            #If the data from the local mongo is not valid return the error response
            if not part_data:
                result ={"message":183,
                    "data":{"part_data":[],"total":0}}
                response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                return response      
            else:
                # inspection_station="SCHINNEDER_1"
                camera_list=part_data["workstation_cameras"]
                workstation_type= part_data["workstation_type"]

                topic_list=[]
                for camera_name in camera_list:
                    topic_list.append(camera_name["camera_name"].replace(" ",""))

                # camera_list_modified = [i.replace(" ", "") for i in camera_list]
                part_name = part_data["part_name"]
                part_number= part_data["part_number"]
                usecase_id=part_data["usecase_id"]
                workstation_id=part_data["workstation_id"]

                position_number=0
                local_collection=f"{workstation_type}_golden_image_{part_id}"
                waypoint_document=LocalMongoHelper().getCollection(local_collection).find_one(sort=[("_id", -1)])
                if waypoint_document is None:
                    waypoint="P0"
                else:
                    last_waypoint=waypoint_document["waypoint"]
                    waypoint_count=int(last_waypoint[1])+1
                    waypoint=f"P{waypoint_count}"

                cobot_name="doosan"

                cobot_golden_image_record_waypoint_status = cobot_golden_image_record_waypoint_util(
                        topic_list, part_id, part_name, workstation_type,usecase_id,workstation_id,part_number,waypoint,position_number,cobot_name
                    )
                
                image_file_render_url=image_file_render_url_util(workstation_type,part_id,topic_list)

                #check if there is any error occurs while capturing image
                if CacheHelper().get_json("golden_image_error"):
                    CacheHelper().set_json({"golden_image_error":None})
                    res = {"message":cobot_golden_image_record_waypoint_status,
                            "data":{"golden_image":[],"total":0}}
                    return Response(response=json.dumps(res),status=503,mimetype='application/json')
                
                #check if there is any error occurs while creating HTTP server 
                elif not image_file_render_url:
                    res = {"message":191 ,
                            "data":{"golden_image":[],"total":0}}
                    return Response(response=json.dumps(res),status=501,mimetype='application/json')         
                else:
                    coordinate_value=CacheHelper().get_json("coordinates_number")
                    if coordinate_value:               
                        CacheHelper().set_json({"coordinates_number":None})
                        waypoint_details={"coordinate":coordinate_value,"transit_point":False,"waypoint":waypoint}
                        res = {"message":cobot_golden_image_record_waypoint_status,
                                "data":{"golden_image":image_file_render_url,
                                        "waypoint_details":[waypoint_details],"total":2}}                   
                        return Response(response=json.dumps(res),status=200,mimetype='application/json')
                    else:
                        res = {"message":cobot_golden_image_record_waypoint_status,
                                "data":{"golden_image":image_file_render_url,"total":len(image_file_render_url)}}
                        return Response(response=json.dumps(res),status=200,mimetype='application/json')
    else:
        res={"message":186,
            "data":{"golden_image":[],"total":0}}
        response = Response(response=json.dumps(res),status=415,mimetype='application/json')
        return response

@views.route("/delete_waypoint", methods=["POST"])
def delete_waypoint():
    """
    Delete the last recorded waypoints all details

    Payload: {"part_id":"64d4eb2fccd50444cbd570ec",
              "waypoint":"P0"}

    Response: {"message":158,
                "data":{"golden_image":[],"total":0}}

        """
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = json.loads(request.data)

        part_id = data.get("part_id")
        workstation_type="cobot"
        local_collection=f"{workstation_type}_golden_image_{part_id}"

        waypoint_document=LocalMongoHelper().getCollection(local_collection).find_one(sort=[("_id", -1)])
        if waypoint_document is None:
            waypoint="P0"
        else:
            last_waypoint=waypoint_document["waypoint"]
            waypoint=last_waypoint

        delete_waypoint_parameter=["part_id"]
        print("waypoint",waypoint)
        data_validate_result=validate_required_data(delete_waypoint_parameter,data)

        if not data_validate_result:
                res =[{"message":184,"data":{"golden_image":[],"total":0}}]
                response = Response(response=json.dumps(res),status=422,mimetype='application/json')
                return response

        cobot_golden_image_delete_waypoint_status = cobot_golden_image_delete_waypoint_util(waypoint,part_id)

        if CacheHelper().get_json("there_is_no_waypoint_to_delete"):
            CacheHelper().set_json({"there_is_no_waypoint_to_delete":False})
            res = {"message":cobot_golden_image_delete_waypoint_status,
                    "data":{"golden_image":[],"total":0}}
            return Response(response=json.dumps(res),status=200,mimetype='application/json')
        
        #check if there is any error occurs while capturing image
        elif CacheHelper().get_json("golden_image_error"):
            CacheHelper().set_json({"golden_image_error":None})
            res = {"message":cobot_golden_image_delete_waypoint_status,
                    "data":{"golden_image":[],"total":0}}
            return Response(response=json.dumps(res),status=503,mimetype='application/json')
        else:
            local_collection=f"{workstation_type}_golden_image_{part_id}"
            waypoint_document=LocalMongoHelper().getCollection(local_collection).find_one(sort=[("_id", -1)])
            if waypoint_document is None:
                waypoint="P0"
            else:
                last_waypoint=waypoint_document["waypoint"]
                # waypoin_name_split=last_waypoint.split("")
                waypoint_count=int(last_waypoint[1])+1
                waypoint=f"P{waypoint_count}"
            res = {"message":cobot_golden_image_delete_waypoint_status,
                    "data":{"waypoint":[waypoint],"total":1}}
            return Response(response=json.dumps(res),status=200,mimetype='application/json')
    else:
        res={"message":186,
            "data":{"golden_image":[],"total":0}}
        response = Response(response=json.dumps(res),status=415,mimetype='application/json')
        return response
    

@views.route("/transit_point", methods=["POST"])
def transit_point():
    """
    Update the transit point details in meta data Json file

    Payload: {
            "waypoint":"P0",
            "part_id":"64d4eb2fccd50444cbd570ec"
            }

    Response: {"message":160,
                    "data":{"golden_image":[],"total":0}}
    """

    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = json.loads(request.data)

        part_id = data.get("part_id")
        waypoint=data.get("waypoint")
        position_number=data.get("position_number")
        transit_status=data.get("transit_point")
        
        data_validate_result=validate_required_data(GOLDEN_IMAGE_PAYLOAD_PARAMETER_FOR_UPDATE,data)

        if not data_validate_result:
                res =[{"message":184,"data":{"golden_image":[],"total":0}}]
                response = Response(response=json.dumps(res),status=422,mimetype='application/json')
                return response
        
        cobot_golden_image_transit_point_status = cobot_golden_image_transit_point_util(waypoint,part_id,position_number,transit_status)
        
        #check if there is any error occurs while capturing image
        if CacheHelper().get_json("golden_image_error"):
            CacheHelper().set_json({"golden_image_error":None})
            res = {"message":cobot_golden_image_transit_point_status,
                    "data":{"golden_image":[],"total":0}}
            return Response(response=json.dumps(res),status=503,mimetype='application/json')
        else:
            workstation_type="cobot"
            local_collection=f"{workstation_type}_golden_image_{part_id}"
            waypoint_document=LocalMongoHelper().getCollection(local_collection).find_one(sort=[("_id", -1)])
            if waypoint_document is None:
                waypoint="P0"
            else:
                last_waypoint=waypoint_document["waypoint"]
                # waypoin_name_split=last_waypoint.split("")
                # waypoint_count=int(last_waypoint[1])+1
                waypoint=last_waypoint
            update_details={"waypoint":waypoint,"coordinates":waypoint_document["coordinates"],"transit_point":waypoint_document["transit_point"]}
            res = {"message":cobot_golden_image_transit_point_status,
                    "data":{"update_details":[update_details],"total":1}}
            return Response(response=json.dumps(res),status=200,mimetype='application/json')
    else:
        res={"message":186,
            "data":{"golden_image":[],"total":0}}
        response = Response(response=json.dumps(res),status=415,mimetype='application/json')
        return response

@views.route("/get_all_parts_for_workstation/<workstation_id>",methods=["GET"])
def get_all_parts_for_workstation(workstation_id):
    """
    Get all the parts in the workstation 

    Payload: None

    Response:
            {
                "message": 189,
                "data": {
                    "part_data": [
                        {
                            "part_name": "sdaf",
                            "part_number": "3214r",
                            "present_in_usecases": 1
                        }
                    ],
                    "workstation_type": "static",
                    "total": 1
                }
            }
    """ 

    if request.method=="GET":

        check_internet_connection= check_internet()
        if not check_internet_connection:
            result ={"message":109,
                    "data":{"part_data":[],"total":0}},
            response = Response(response=json.dumps(result),status=503,mimetype='application/json')
            return response
        else:
            authorization_token=fetch_the_authorization_token_util()
            # authorization_token="Bearer 74l5fa2R5j0o48wC8D9YeIwbTrPA05"
            if not authorization_token:
                result ={"message":5,
                    "data":{"part_data":[],"total":0}}
                response = Response(response=json.dumps(result),status=401,mimetype='application/json')
                return response  
            else:
                #get the details of the respective part based on it's part_id
                url = f"https://v2.livis.ai/api/livis/v2/parts/get_all_parts_for_workstation/{workstation_id}"

                headers = {"Content-Type": "application/json",
                            "Authorization":authorization_token}

                # sending request data and getting response of one document
                api_geteway_response = requests.request("GET", url, headers=headers)
                print("api_geteway_response",api_geteway_response)
                result=api_geteway_response.json()
                print("api_geteway_response",result)
                if api_geteway_response.status_code==200:
                    part_list_for_workstation = api_geteway_response.json()

                    # #If the data from the cloudmongo is not valid return the error response
                    if not part_list_for_workstation:
                        result ={"message":183,
                            "data":{"part_data":[],"total":0}}
                        response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                        return response    
                    else:
                        workstation_details=get_the_workstation_details(workstation_id)

                        if not workstation_details:
                            result ={"message":5,
                                    "data":{"part_data":[],"total":0}}
                            response = Response(response=json.dumps(result),status=401,mimetype='application/json')
                            return response  
                        else:

                            if workstation_details.status_code!=200:
                                result ={"message":193,
                                    "data":{"part_data":[],"total":0}}
                                response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                                return response   
                            else:
                                workstation_data=workstation_details.json()
                                print("workstation_data:",workstation_data)
                                workstation_type=workstation_data["data"]["workstation_type"]
                                result ={"message":189,
                                        "data":{"part_data":part_list_for_workstation["data"],
                                                "workstation_type":workstation_type,"total":len(part_list_for_workstation["data"])}}
                                    
                                response = Response(response=json.dumps(result),status=200,mimetype='application/json')
                                return response
                else:
                    result ={"message":183,
                        "data":{"part_data":[],"total":0}}
                    response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                    return response   
    else:
        result ={"message":187,
              "data":{"request type":[],"total":0}}
        response = Response(response=json.dumps(result),status=405,mimetype='application/json')
        return response



@views.route("/get_usecases_for_given_part_number/",methods=["POST"])
def get_usecases_for_given_part_number():
    """
    captured the golden image of part

    Payload: None

    Response:
            {
                "message": 189,
                "data": {
                    "part_data": [
                        {
                            "_id": "64e5c9874a9266ce1c8ae96b",
                            "usecase_name": "ups cobot"
                        }
                    ],
                    "total": 1
                }
            }
    """ 
    if request.method=="POST":

        check_internet_connection= check_internet()
        if not check_internet_connection:
            result ={"message":109,
                    "data":{"part_data":[],"total":0}},
            response = Response(response=json.dumps(result),status=503,mimetype='application/json')
            return response
        else:
            data=json.loads(request.data)
            workstation_id=data.get("workstation_id")
            part_number=data.get("part_number")
            
            data_validate_result=validate_required_data(DATA_CAPTURE_PAYLOAD_PARAMETER,data)
            if not data_validate_result:
                    res =[{"message":184,"data":{"part_data":[],"total":0}}]
                    response = Response(response=json.dumps(res),status=422,mimetype='application/json')
                    return response
            else:
                authorization_token=fetch_the_authorization_token_util()
                # authorization_token="Bearer 74l5fa2R5j0o48wC8D9YeIwbTrPA05"
                if not authorization_token:
                    result ={"message":5,
                        "data":{"part_data":[],"total":0}}
                    response = Response(response=json.dumps(result),status=401,mimetype='application/json')
                    return response  
                else:
                    #get the details of the respective part based on it's part_number
                    url = f"https://v2.livis.ai/api/livis/v2/usecase/get_usecases_for_given_part_number/"
                    payload = json.dumps(
                        {
                            "workstation_id": workstation_id,
                            "part_number": part_number,
                        }
                    )

                    headers = {"Content-Type": "application/json",
                                "Authorization":authorization_token}

                    # sending request data and getting response of one document
                    api_geteway_response = requests.request("POST", url, headers=headers, data=payload)
                    print("api_geteway_response",api_geteway_response)
                    if api_geteway_response.status_code==200:
                        api_geteway_response = api_geteway_response.json()

                        # #If the data from the cloudmongo is not valid return the error response
                        if not api_geteway_response:
                            result ={"message":183,
                                "data":{"part_data":[],"total":0}}
                            response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                            return response    
                        else:

                            result ={"message":189,
                                    "data":{"part_data":api_geteway_response["data"],
                                            "total":len(api_geteway_response["data"])}}
                                
                            response = Response(response=json.dumps(result),status=200,mimetype='application/json')
                            return response
                    else:
                        result ={"message":183,
                            "data":{"part_data":[],"total":0}}
                        response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                        return response   
             
    else:
        result ={"message":187,
              "data":{"request type":[],"total":0}}
        response = Response(response=json.dumps(result),status=405,mimetype='application/json')
        return response


@views.route("/static_data_capture", methods=["POST"])
def static_data_capture():
    """
    Static data_capture is carried out

    Payload: {

            "use_case_list": ["feature1","feature2","feature3"],
            "topic_list": ["Cam1","Cam2" ],
            "part_id": "64d4eb2fccd50444cbd570ec",
            "part_name": "ABS",
            "workstation_type":"static"
             }

    Response:{"message":164,
                        "data":{"data_capture_image":[],"total":0}}"""

    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = json.loads(request.data)

        part_id = data.get("part_id")

        part_data=LocalMongoHelper().getCollection("part_data").find_one({"_id":ObjectId(part_id)},{"_id":0})
        print(part_data)

        #If the data from the local mongo is not valid return the error response
        if not part_data:
            result ={"message":183,
                "data":{"part_data":[],"total":0}}
            response = Response(response=json.dumps(result),status=417,mimetype='application/json')
            return response      
        else:
            use_case_list=[]
            topic_list=[]
            part_name=part_data["part_name"]
            part_number=part_data["part_number"]
            workstation_type=part_data["workstation_type"]
            workstation_id=part_data["workstation_id"]

            workstation_details=get_the_workstation_details(workstation_id)

            if not workstation_details:
                result ={"message":5,
                        "data":{"part_data":[],"total":0}}
                response = Response(response=json.dumps(result),status=401,mimetype='application/json')
                return response  
            else:

                if workstation_details.status_code!=200:
                    result ={"message":193,
                        "data":{"part_data":[],"total":0}}
                    response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                    return response   
                else:
                    workstation_details_data=workstation_details.json()
                    workstation_data=workstation_details_data["data"]
                    camera_details=workstation_data["camera"]
                    for camera_name in camera_details:
                        topic_list.append(camera_name["camera_name"].replace(" ",""))

                    # data_validate_result=validate_required_data(DATA_CAPTURE_PAYLOAD_PARAMETER,data)

                    # if not data_validate_result:
                    #         res =[{"message":184,"data":{"golden_image":[],"total":0}}]
                    #         response = Response(response=json.dumps(res),status=422,mimetype='application/json')
                    #         return response

                    #check use case selected or not
                    if CacheHelper().get_json("use_case"):

                        local_collection=f"{workstation_type}_data_capture_{part_id}"
                        cycle_data= LocalMongoHelper().getCollection(local_collection).find_one(sort=[("_id", -1)])
                        if cycle_data:
                            cycle_number=cycle_data["cycle"]+1
                        else:
                            cycle_number=1

                        static_data_capture_status = static_data_capture_util(
                            
                            use_case_list,
                            topic_list,
                            part_id,
                            part_name,
                            part_number,
                            workstation_type,
                            cycle_number
                        )

                        image_file_render_url=data_capture_image_file_render_url_util(workstation_type,part_id,topic_list)

                        #check if there is any error occurs while data capturing
                        if CacheHelper().get_json("data_capture_error"):
                            CacheHelper().set_json({"data_capture_error":None})
                            res = {"message":static_data_capture_status,
                                    "data":{"data_capture_image":[],"total":0}}
                            return Response(response=json.dumps(res),status=503,mimetype='application/json')
                        
                        #check if there is any error occurs while creating HTTP server 
                        elif not image_file_render_url:
                            res = {"message":191 ,
                                    "data":{"golden_image":[],"total":0}}
                            return Response(response=json.dumps(res),status=501,mimetype='application/json')  
                        #If data captured successfully return that status
                        else:
                            local_collection=f"{workstation_type}_data_capture_{part_id}"
                            cycle_data= LocalMongoHelper().getCollection(local_collection).find_one(sort=[("_id", -1)])
                            if cycle_data:
                                cycle_number=cycle_data["cycle"]+1
                            else:
                                cycle_number=1

                            # http_server_link=get_the_capture_image_server_url()
                            # local_collection=f"{workstation_type}_data_capture_{part_id}"
                            # image_file_list_object=LocalMongoHelper().getCollection(local_collection)
                            # all_image_file_list=list(image_file_list_object.find({},{"image_file":1,"_id":0}))
                            # # print("all_image_file_list",all_image_file_list)
                            # image_file_render_url=[]
                            # if all_image_file_list:
                            #     number_of_images=len(topic_list)
                            #     image_file_to_render_list=all_image_file_list[-number_of_images:]
                            #     for image_path in image_file_to_render_list:
                            #         image_file_path=image_path["image_file"]
                            #         file_url=f"{http_server_link}/{image_file_path}"
                            #         image_file_render_url.append(file_url)
                            
                            res = {"message":static_data_capture_status,
                                    "data":{"data_capture_image":image_file_render_url,
                                            "cycle":cycle_number,"total":2}}
                            return Response(response=json.dumps(res),status=200,mimetype='application/json')
                    else:
                        res={"message":166,
                            "data":{"data_capture_image":[],"total":0}}
                        response = Response(response=json.dumps(res),status=400,mimetype='application/json')
                        return response
    else:
        res={"message":186,
            "data":{"data_capture_image":[],"total":0}}
        response = Response(response=json.dumps(res),status=415,mimetype='application/json')
        return response


@views.route("/upload_data_capture", methods=["POST"])
def upload_static_data_capture():
    """
    All the catpured data are zipped

    Payload: {
            "part_id": "64d4eb2fccd50444cbd570ec",
             }

    Response: {"message":162,
                        "data":{"data_capture_image":[],"total":0}}
    """

    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = json.loads(request.data)

        check_internet_connection= check_internet()
        if not check_internet_connection:
            result ={"message":109,
                    "data":{"golden_image":[],"total":0}},
            response = Response(response=json.dumps(result),status=503,mimetype='application/json')
            return response
        else:
            data = json.loads(request.data)         
            part_id = data.get("part_id")

            data_validate_result=validate_required_data(DATA_CAPTURE_UPLOAD_PAYLOAD_PARAMETER,data)

            if not data_validate_result:
                    res =[{"message":184,"data":{"data_capture":[],"total":0}}]
                    response = Response(response=json.dumps(res),status=422,mimetype='application/json')
                    return response
            else:
                part_data=LocalMongoHelper().getCollection("part_data").find_one({"_id":ObjectId(part_id)})

                #If the data from the local mongo is not valid return the error response
                if not part_data:
                    result ={"message":183,
                        "data":{"part_data":[],"total":0}}
                    response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                    return response      
                else:
                    workstation_type= part_data["workstation_type"]
                    topic_list=[]
                    part_name = part_data["part_name"]
                    part_number = part_data["part_number"]
                    workstation_id=part_data["workstation_id"]
                    waypoint="P0" 
                    use_case_list=[]

                    #check use case selected or not
                    if CacheHelper().get_json("use_case"):

                        zip_file_name = data_capture_upload_util(
                            
                            use_case_list,
                            topic_list,
                            part_id,
                            part_name,
                            part_number,
                            workstation_type,
                        )
                     
                        CacheHelper().set_json({"use_case":False})

                        #check if there is any error occurs while data uploading
                        if CacheHelper().get_json("data_capture_upload_error") or not zip_file_name:
                            CacheHelper().set_json({"data_capture_upload_error":None})
                            res = {"message":163,
                                    "data":{"data_capture_image":[],"total":0}}
                            return Response(response=json.dumps(res),status=503,mimetype='application/json')
                        
                        #If data uploaded successfully return that status
                        else:

                            authorization_token=fetch_the_authorization_token_util()
                            # authorization_token="Bearer 74l5fa2R5j0o48wC8D9YeIwbTrPA05"
                            if not authorization_token:
                                result ={"message":5,
                                        "data":{"part_data":[],"total":0}}
                                response = Response(response=json.dumps(result),status=401,mimetype='application/json')
                                return response  
                            else:
                                #uploading the zip file to the cloud
                                print("part_id:",part_id,"workstation_id",workstation_id,"zip_file",zip_file_name)
                                url = f"https://upload.livis.ai/v1/uploads_edge"
                                form_data = {
                                                    "part_id":part_id,
                                                    "workstation_id":workstation_id,                                                                                       
                                                    }
                                file_path = f"{os.getcwd()}/{zip_file_name}"
                                headers = {"Authorization":authorization_token}
                                with open(file_path, 'rb') as file:
                                    api_geteway_response = requests.post(url, headers=headers,files={'livis_file': (file.name, file, 'application/zip')}, data=form_data)
                                result = api_geteway_response.json()

                                print("api_geteway_response", result)
                                if api_geteway_response.status_code==200:
                                    res = {"message":162,
                                            "data":{"data_capture_image":[],"total":0}}
                                    return Response(response=json.dumps(res),status=200,mimetype='application/json')
                                else:
                                    res = {"message":163,
                                            "data":{"data_capture_image":[],"total":0}}
                                    return Response(response=json.dumps(res),status=417,mimetype='application/json')
                    else:
                        res={"message":166,
                            "data":{"data_capture_image":[],"total":0}}
                        response = Response(response=json.dumps(res),status=400,mimetype='application/json')
                        return response
    else:
        res={"message":186,
            "data":{"data_capture_image":[],"total":0}}
        response = Response(response=json.dumps(res),status=415,mimetype='application/json')
        return response

@views.route("/sort_tag", methods=["POST"])
def sort_tag():
    """
    To catagerise the images as a OK or NOT OK .By default it will be a unsorted

    Payload: {"tag":"OK"}

    Response: {"message":167,
                    "data":{"sort_tag":[],"total":0}}
    """
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = json.loads(request.data)
        sort_tag_status_data = data.get("tag")

        data_validate_result=validate_required_data(["tag"],data)

        if not data_validate_result:
                res =[{"message":184,"data":{"data_capture_image":[],"total":0}}]
                response = Response(response=json.dumps(res),status=422,mimetype='application/json')
                return response
        
        elif sort_tag_status_data=="OK":
            CacheHelper().set_json({"sort_tag": sort_tag_status_data})
            res = {"message":167,
                    "data":{"sort_tag":[],"total":0}}
            return Response(response=json.dumps(res),status=200,mimetype='application/json')
        elif sort_tag_status_data=="NG":
            CacheHelper().set_json({"sort_tag": sort_tag_status_data})     
            res = {"message":168,
                    "data":{"sort_tag":[],"total":0}}
            return Response(response=json.dumps(res),status=200,mimetype='application/json')
        else:
            CacheHelper().set_json({"sort_tag": None})
            res = {"message":169,
                    "data":{"sort_tag":[],"total":0}}
            return Response(response=json.dumps(res),status=200,mimetype='application/json')
    else:
        res={"message":186,
            "data":{"sort_tag":[],"total":0}}
        response = Response(response=json.dumps(res),status=415,mimetype='application/json')
        return response

@views.route("/get_part_doc_for_data_capture", methods=["POST"])
def get_part_doc_for_data_capture():
    """
    Select the use_case to collect the data

    Payload: {"use_case":"feature1"}

    Response: {"message":170,
                "data":{"use_case":[],"total":0}}
    """
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):

        check_internet_connection= check_internet()
        if not check_internet_connection:
            result ={"message":109,
                    "data":{"part_data":[],"total":0}},
            response = Response(response=json.dumps(result),status=503,mimetype='application/json')
            return response
        else:
            data = json.loads(request.data)
            workstation_id = data.get("workstation_id")
            usecase_id = data.get("usecase_id")
            part_number = data.get("part_number")
            use_case = data.get("usecase")

            data_validate_result=validate_required_data(DATA_CAPTURE_PAYLOAD_PARAMETER_FOR_USECASE,data)

            if not data_validate_result:
                    res =[{"message":184,"data":{"data_capture_image":[],"total":0}}]
                    response = Response(response=json.dumps(res),status=422,mimetype='application/json')
                    return response
            else:
                CacheHelper().set_json({"use_case": use_case})
                authorization_token=fetch_the_authorization_token_util()
                # authorization_token="Bearer 74l5fa2R5j0o48wC8D9YeIwbTrPA05"
                if not authorization_token:
                    result ={"message":5,
                        "data":{"part_data":[],"total":0}}
                    response = Response(response=json.dumps(result),status=401,mimetype='application/json')
                    return response  
                else:
                    #get the details of the respective part based on it's part_id
                    url = f"https://v2.livis.ai/api/livis/v2/parts/get_part_doc_for_data_capture/"
                    payload = json.dumps(
                        {
                            "workstation_id": workstation_id,
                            "part_number": part_number,
                            "usecase_id":usecase_id
                        }
                    )

                    headers = {"Content-Type": "application/json",
                                "Authorization":authorization_token}

                    # sending request data and getting response of one document
                    api_geteway_response = requests.request("POST", url, headers=headers, data=payload)
                    print("api_geteway_response",api_geteway_response)
                    if api_geteway_response.status_code==200:
                        api_geteway_response = api_geteway_response.json()

                        # #If the data from the cloudmongo is not valid return the error response
                        if not api_geteway_response:
                            result ={"message":183,
                                "data":{"part_data":[],"total":0}}
                            response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                            return response    
                        else:
                            part_data=api_geteway_response["data"]
                            insert_part_data_to_local=dump_the_part_data_in_local_mongo(part_data)
                            part_data["_id"]=str(part_data["_id"])
                            workstation_id=part_data["workstation_id"]
                            workstation_details=get_the_workstation_details(workstation_id)

                            if not workstation_details:
                                result ={"message":5,
                                        "data":{"part_data":[],"total":0}}
                                response = Response(response=json.dumps(result),status=401,mimetype='application/json')
                                return response  
                            else:

                                if workstation_details.status_code!=200:
                                    result ={"message":193,
                                        "data":{"part_data":[],"total":0}}
                                    response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                                    return response   
                                else:
                                    workstation_data=workstation_details.json()
                                    camera_details=workstation_data["data"]["camera"]
                                    topic_list=[]
                                    for camera_name in camera_details:
                                        topic_list.append(camera_name["camera_name"].replace(" ",""))

                                    container_deployed= spawn_the_camera_conatiner_util(topic_list)

                                    if not container_deployed:
                                        res = {"message":190,
                                                "data":{"edge_connect":[],"total":0}}
                                        return Response(response=json.dumps(res),status=503,mimetype='application/json')
                                    else:
                                        print("part_data",part_data)
                                        result ={"message":192,
                                                "data":{"part_data":part_data,
                                                        "workstation_data":workstation_data,
                                                        "total":len(part_data)}}
                                            
                                        response = Response(response=json.dumps(result),status=200,mimetype='application/json')
                                        return response
                    else:
                        result ={"message":183,
                            "data":{"part_data":[],"total":0}}
                        response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                        return response   
    else:
        res={"message":186,
            "data":{"use_case":[],"total":0}}
        response = Response(response=json.dumps(res),status=415,mimetype='application/json')
        return response


@views.route("/start_cobot_cycle/<part_id>", methods=["GET"])
def start_cobot_cycle(part_id):
    """
    start the cobot cycle to capture image for all waypoints

    Payload: None

    Response: {"message":171,
                "data":{"data_capture_image":[],"total":0}}
    """

    if request.method=="GET":


        part_data=LocalMongoHelper().getCollection("part_data").find_one({"_id":ObjectId(part_id)},{"_id":0})
        print(part_data)

        #If the data from the local mongo is not valid return the error response
        if not part_data:
            result ={"message":183,
                "data":{"part_data":[],"total":0}}
            response = Response(response=json.dumps(result),status=417,mimetype='application/json')
            return response      
        else:
            use_case_list=[]
            topic_list=[]
            part_name=part_data["part_name"]
            part_number=part_data["part_number"]
            workstation_type=part_data["workstation_type"]
            workstation_id=part_data["workstation_id"]
            waypoint_dictionary=part_data["waypoint"]

            check_internet_connection= check_internet()
            if not check_internet_connection:
                print("internet error occurs")
                result ={"message":109,
                        "data":{"part_data":[],"total":0}},
                response = Response(response=json.dumps(result),status=503,mimetype='application/json')
                return response
            else:
                workstation_details=get_the_workstation_details(workstation_id)

                if not workstation_details:
                    result ={"message":5,
                            "data":{"part_data":[],"total":0}}
                    response = Response(response=json.dumps(result),status=401,mimetype='application/json')
                    return response  
                else:

                    if workstation_details.status_code!=200:
                        result ={"message":193,
                            "data":{"part_data":[],"total":0}}
                        response = Response(response=json.dumps(result),status=417,mimetype='application/json')
                        return response   
                    else:
                        workstation_details_data=workstation_details.json()
                        workstation_data=workstation_details_data["data"]
                        camera_details=workstation_data["camera"]
                        for camera_name in camera_details:
                            topic_list.append(camera_name["camera_name"].replace(" ",""))

                        # data_validate_result=validate_required_data(DATA_CAPTURE_PAYLOAD_PARAMETER,data)

                        # if not data_validate_result:
                        #         res =[{"message":184,"data":{"golden_image":[],"total":0}}]
                        #         response = Response(response=json.dumps(res),status=422,mimetype='application/json')
                        #         return response

                        #check use case selected or not
                        if CacheHelper().get_json("use_case"):

                            local_collection=f"{workstation_type}_data_capture_{part_id}"
                            cycle_data= LocalMongoHelper().getCollection(local_collection).find_one(sort=[("_id", -1)])
                            if cycle_data:
                                cycle_number=cycle_data["cycle"]+1
                            else:
                                cycle_number=1
                            # cobot_data is captured and meta data is created
                            cobot_data_capture_status = cobot_data_capture_util(
                                
                                use_case_list,
                                topic_list,
                                part_id,
                                part_name,
                                part_number,
                                workstation_type,
                                cycle_number,
                                workstation_data,
                                waypoint_dictionary
                            )
                            # time.sleep(0.1)
                            http_server_link=get_the_data_capture_image_server_url()
                            CacheHelper().set_json({"is_data_capture_cycle_completed":False})

                            camera_stream_url_list=[]
                            for topic in topic_list:
                                topic_url_string=f"http://127.0.0.1:5000/part_capture/video_stream/{topic}"
                                camera_stream_url_list.append(topic_url_string)

                            def stream_the_waypoint_data():
                                print("stream_function_called")
                                while True:
                                    print("stream_start")
                                    if CacheHelper().get_json("is_data_capture_cycle_completed"):
                                        time.sleep(2)
                                    if CacheHelper().get_json("data_capture_status"):
                                        time.sleep(1)
                                    else:
                                        time.sleep(0.5)

                                    print("inside meta stream")
                                    local_collection=f"{workstation_type}_data_capture_{part_id}"
                                    image_file_list_object=LocalMongoHelper().getCollection(local_collection)
                                    print("image_file_list_object:",image_file_list_object)
                                    all_image_file_list=list(image_file_list_object.find({"cycle":cycle_number},{"image_name":1,"_id":0,"waypoint":1}))
                                    print("all_image_file_list",all_image_file_list)
                                    image_file_render_url={}
                                    waypoint="P0"
                                    number_of_captured_images=0
                                    if all_image_file_list:
                                        waypoint_document=LocalMongoHelper().getCollection(local_collection).find_one(sort=[("_id", -1)])
                                        waypoint=waypoint_document["waypoint"]
                                        number_of_captured_images=len(all_image_file_list)
                                        # waypoint_stream_url={all_image_file_list["waypoint"]:[]}
                                        # image_file_to_render_list=all_image_file_list[-number_of_images:]
                                        for image_path in all_image_file_list:
                                            if image_path["waypoint"] in image_file_render_url.keys() :
                                                image_file_path=image_path["image_name"]
                                                file_url=f"{http_server_link}/{local_collection}/{image_file_path}"
                                                image_file_render_url[image_path["waypoint"]].append(file_url)
                                            else:
                                                image_file_render_url[image_path["waypoint"]]=[]
                                                image_file_path=image_path["image_name"]
                                                file_url=f"{http_server_link}/{local_collection}/{image_file_path}"
                                                image_file_render_url[image_path["waypoint"]].append(file_url)
                                    # print("image_file_render_url",image_file_render_url)
                                    if CacheHelper().get_json("is_data_capture_cycle_completed"):
                                        is_cycle_completed=True
                                    else:
                                        is_cycle_completed=False

                                    res = {"message":164,
                                            "data":{"sse":camera_stream_url_list,
                                                    "data_capture_image":image_file_render_url,
                                                    "cycle":cycle_number,"waypoint":waypoint,"number_of_captured_images":number_of_captured_images,
                                                    "is_cycle_completed":is_cycle_completed,"total":5}}
                                    CacheHelper().set_json({"data_capture_status":False})
                                            # return Response(response=json.dumps(res),status=200,mimetype='application/json')
                                    
                                    yield "data: {}\n\n".format(json.dumps(res), 200)
                                    

                            #check if there is any error occurs while data capturing
                            if CacheHelper().get_json("data_capture_error"):
                                CacheHelper().set_json({"data_capture_error":None})
                                res = {"message":cobot_data_capture_status,
                                        "data":{"data_capture_image":[],"total":0}}
                                if cobot_data_capture_status==183 or cobot_data_capture_status==165 :
                                    return Response(response=json.dumps(res),status=417,mimetype='application/json')
                                else:
                                    return Response(response=json.dumps(res),status=503,mimetype='application/json')
                            
                            #If data captured successfully return that status
                            else:

                                return Response(stream_with_context(stream_the_waypoint_data()), mimetype="text/event-stream")
                        else:
                            res={"message":166,
                                "data":{"data_capture_image":[],"total":0}}
                            response = Response(response=json.dumps(res),status=400,mimetype='text/event-stream')
                            return response
    else:
        res={"message":186,
            "data":{"data_capture_image":[],"total":0}}
        response = Response(response=json.dumps(res),status=415,mimetype='text/event-stream')
        return response



@views.route("/start_conveyor", methods=["POST"])
def start_conveyor():
    """
    start the conveyor to capture image 

    Payload: {

            "use_case_list": ["feature1","feature2","feature3"],
            "topic_list": ["Cam1","Cam2" ],
            "part_id": "64d4eb2fccd50444cbd570ec",
            "part_name": "ABS",
            "workstation_type":"conveyor",
            "plc_configuration":"plc"
             }

    Response: {"message":172,
                "data":{"data_capture_image":[],"total":0}}
    """
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = json.loads(request.data)

        # inspection_station = data.get("inspection_station")
        use_case_list = data.get("use_case_list")
        topic_list = data.get("topic_list")
        part_id = data.get("part_id")
        part_name = data.get("part_name",)
        workstation_type = data.get("workstation_type")
        plc_configuration=data.get("plc_configuration")
        part_number=data.get("part_number")

        data_validate_result=validate_required_data(DATA_CAPTURE_PAYLOAD_PARAMETER_FOR_PLC,data)

        if not data_validate_result:
                res =[{"message":184,"data":{"golden_image":[],"total":0}}]
                response = Response(response=json.dumps(res),status=422,mimetype='application/json')
                return response

        #check use case selected or not        
        if CacheHelper().get_json("use_case"):
            CacheHelper().set_json({"start_conveyor": True})
            CacheHelper().set_json({"is_stop_conveyor": False})

            # static_data is captured and meta data is created
            conveyor_data_capture_status = conveyor_data_capture_util(
                
                use_case_list,
                topic_list,
                part_id,
                part_name,
                part_number,
                workstation_type,
                plc_configuration
            )
            time.sleep(5)
            #check if there is any error occurs while data capturing
            # if CacheHelper().get_json("data_capture_error"):
            #     error_message_code=CacheHelper().get_json("data_capture_error")
            #     res = {"message":error_message_code,
            #             "data":{"data_capture_image":[],"total":0}}
            #     CacheHelper().set_json({"data_capture_error":None})
            #     return Response(response=json.dumps(res),status=503,mimetype='application/json')
            # else:
            def conveyor_data_capture_response():
                while CacheHelper().get_json("start_conveyor"):
                    data_capture_status_code=CacheHelper().get_json("capture_image_status")
                    conveyor_status= {"message":data_capture_status_code,
                                    "data":{"data_capture_image":[],"total":0}}
                    yield "data: {}\n\n".format(json.dumps(conveyor_status))
                    time.sleep(5)

                if CacheHelper().get_json("data_capture_error"):

                    error_message_code=CacheHelper().get_json("data_capture_error")
                    conveyor_status = {"message":error_message_code,
                            "data":{"data_capture_image":[],"total":0}}
                    CacheHelper().set_json({"data_capture_error":None})
                    yield "data: {}\n\n".format(json.dumps(conveyor_status))

                else:
                    conveyor_status= {"message":175,
                                        "data":{"data_capture_image":[],"total":0}}
                    yield "data: {}\n\n".format(json.dumps(conveyor_status))
            
            return Response(stream_with_context(conveyor_data_capture_response()), mimetype='text/event-stream',status=200)
        else:
            CacheHelper().set_json({"start_conveyor": False}) 
            res={"message":166,
                 "data":{"data_capture_image":[],"total":0}}
            response = Response(response=json.dumps(res),status=400,mimetype='application/json')
            return response
    else:
        res={"message":186,
            "data":{"data_capture_image":[],"total":0}}
        response = Response(response=json.dumps(res),status=415,mimetype='application/json')
        return response


@views.route("/stop_conveyor", methods=["GET"])
def stop_conveyor():
    """
    stop the conveyor to stop capturing image

    Payload: None

    Response: {"message":175,
            "data":{"data_capture_image":[],"total":0}}
    """
    if request.method=="GET":
        CacheHelper().set_json({"is_stop_conveyor": True})

        CacheHelper().set_json({"start_conveyor": False})

        res={"message":175,
            "data":{"data_capture_image":[],"total":0}}
        response = Response(response=json.dumps(res),status=200,mimetype='application/json')
        return response
    else:
        result ={"message":187,
              "data":{"request type":[],"total":0}}
        response = Response(response=json.dumps(result),status=405,mimetype='application/json')
        return response

@views.route("/preview_data_capture",methods=["POST"])
def preview_cobot_data_capture():
    """
    get the list of captured images to preview
    
    Payload: None
    
    Response: {"message":176,
                "data":{"data_preview_image":json_files,"total":length_of_json_files}}
    """
    if request.method=="POST":    
        try:
            data = json.loads(request.data)
            workstation_type=data.get("workstation_type")
            part_id=data.get("part_id")

            http_server_link=get_the_capture_image_server_url()
            local_collection=f"{workstation_type}_data_capture_{part_id}"
            image_file_list_object=LocalMongoHelper().getCollection(local_collection)
            all_image_file_list=list(image_file_list_object.find({},{"_id":0}))
            image_file_render_url={}
            if all_image_file_list:
                if workstation_type=="cobot":
                    for image_path in all_image_file_list:
                        print("##"*50)
                        print("image_path",image_path)
                        print("image_file_render_url.keys():",image_file_render_url.keys())
                        if image_path["waypoint"] in image_file_render_url.keys() :
                            image_file_path=image_path["image_name"]
                            file_url=f"{http_server_link}/{local_collection}/{image_file_path}"
                            image_data={"image_url":file_url,"image_name":image_path["image_name"],"waypoint":image_path["waypoint"],"tag_status":image_path["tag_status"],"cycle":image_path["cycle"],"image_file":image_path["image_file"]}
                            image_file_render_url[image_path["waypoint"]].append(image_data)
                        else:
            
                            image_file_render_url[image_path["waypoint"]]=[]
                            image_file_path=image_path["image_name"]
                            file_url=f"{http_server_link}/{local_collection}/{image_file_path}"
                            image_data={"image_url":file_url,"image_name":image_path["image_name"],"waypoint":image_path["waypoint"],"tag_status":image_path["tag_status"],"cycle":image_path["cycle"],"image_file":image_path["image_file"]}
                            image_file_render_url[image_path["waypoint"]].append(image_data)

                    result ={"message":176,
                            "data":{"data_preview_image":image_file_render_url,
                                    "workstation_type":workstation_type,"total":len(image_file_render_url)}}
                    response = Response(response=json.dumps(result),status=200,mimetype='application/json')
                    return response
                elif workstation_type=="static":
                    image_file_render_url_for_static=[]
                    for image_path in all_image_file_list:
                        print("##"*50)
                        # print("image_path",image_path)
                        # print("image_file_render_url.keys():",image_file_render_url.keys())
                        # if image_path["waypoint"] in image_file_render_url.keys() :
                        #     image_file_path=image_path["image_file"]
                        #     file_url=f"{http_server_link}/{image_file_path}"
                        #     image_data={"image_url":file_url,"image_name":image_path["image_name"],"waypoint":image_path["waypoint"],"tag_status":image_path["tag_status"],"cycle":image_path["cycle"],"image_file":image_path["image_file"]}
                        #     image_file_render_url[image_path["waypoint"]].append(image_data)
                        # else:
            
                            # image_file_render_url[image_path["waypoint"]]=[]
                        image_file_path=image_path["image_file"]
                        file_url=f"{http_server_link}/{image_file_path}"
                        image_data={"image_url":file_url,"image_name":image_path["image_name"],"tag_status":image_path["tag_status"],"cycle":image_path["cycle"],"image_file":image_path["image_file"]}
                        image_file_render_url_for_static.append(image_data)
                                               
                    result ={"message":176,
                            "data":{"data_preview_image":image_file_render_url_for_static,
                                    "workstation_type":workstation_type,"total":len(image_file_render_url)}}
                    response = Response(response=json.dumps(result),status=200,mimetype='application/json')
                    return response

        except Exception as e:
            print("error details: ",e)
            result ={"message":177,
                    "data":{"data_preview_image":[],"total":0}}
            response = Response(response=json.dumps(result),status=500,mimetype='application/json')
            return response
    else:
        result ={"message":187,
              "data":{"request type":[],"total":0}}
        response = Response(response=json.dumps(result),status=405,mimetype='application/json')
        return response
    
@views.route("/tag_update",methods=["POST"])
def tag_update():
    """
    get the list of captured images to preview
    
    Payload: None
    
    Response: {"message":176,
                "data":{"data_preview_image":json_files,"total":length_of_json_files}}
    """
    if request.method=="POST":    
        try:

            data = json.loads(request.data)
            workstation_type=data.get("workstation_type")
            part_id=data.get("part_id")
            tag_status=data.get("tag_status")
            image_file_list=data.get("image_file_list")

            for image_file in image_file_list:

                json_string=image_file.split(".")

                json_file_path=f"{json_string[0]}.json"
                print(json_file_path)
        

                # json_file_path
                json_file = open(json_file_path)
                print("tag_st",tag_status)
                json_meta_data = json.load(json_file)
                json_file.close()
                print("tag_statu",tag_status)
                json_meta_data["tag_status"] = tag_status
                if tag_status=="OK":
                    json_meta_data["good"]=True
                elif tag_status=="NG":
                    json_meta_data["bad"]=True
                else:
                    json_meta_data["unsorted"]=True
                print("tag_status",tag_status)
                with open(json_file_path, "w",encoding="utf-8") as json_file:
                    json.dump(json_meta_data, json_file)

                LocalMongoHelper().getCollection(f"{workstation_type}_data_capture_{part_id}").update_one({"image_file":image_file},{"$set":{"tag_status":tag_status}})

            result ={"message":191,
                    "data":{"data_tag_status":[],"total":0}}
            response = Response(response=json.dumps(result),status=200,mimetype='application/json')
            return response

        except Exception as e:
            print("error details: ",e)
            result ={"message":192,
                    "data":{"data_preview_image":[],"total":0}}
            response = Response(response=json.dumps(result),status=500,mimetype='application/json')
            return response
    else:
        result ={"message":187,
              "data":{"request type":[],"total":0}}
        response = Response(response=json.dumps(result),status=405,mimetype='application/json')
        return response
    
@views.route('/video_stream/<topic_name>',methods=['GET'])
def video_stream(topic_name):
 #video_thread_util()
    # print("current_thread_in_views",threading.current_thread().getName())
    return Response(video_stream_util(topic_name), mimetype='multipart/x-mixed-replace; boundary=frame')

# @views.route("/update_edge_connect",methods=["GET"])
# def update_edge_connect():
#     CacheHelper().set_json({"is_golden_image_edge_connect": False})
#     CacheHelper().set_json({"is_data_capture_edge_connect": False})
#     CacheHelper().set_json({"use_case": None})
#     print("start the cloud migration")
#     use_case_list=["feature1","feature2","feature3"]
#     # status=create_the_use_case_collection_in_localmongo(use_case_list)
#     return jsonify({"status":"closed edge connect"}),200
#     # return {"status":status}
