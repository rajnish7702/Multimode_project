from bson import ObjectId, json_util
from bson.json_util import dumps
from bson.objectid import ObjectId
import platform
from inspection_station.camera_service import Baumer, IP, RTSP, VideoStream, Camera
import queue
import threading
from edgeplusv2_config.common_utils import *


f = open("edgeplusv2_config/v2_config.json")
data = json.load(f)
f.close()


def get_user_email():
    """
    Fetching user email and extracting the domain livis and returning it to parent function.
    """
    user_credentials = LocalMongoHelper().getCollection("user_details").find_one({})
    mail = ""
    license_key = ""
    if user_credentials is not None and "username" in user_credentials:
        mail = user_credentials["username"]  # emial

    if user_credentials is not None and "_id" in user_credentials:
        license_key = user_credentials["_id"]  # lincense

    domain = user_domain(mail)
    return domain



def update_plc_register_utils(request_params):
    """
    Taking plc_name as input and searching for the plc in the document according to the
    passed object id then updating the PLC register values as passed in request_params.
    """

    plc_name = request_params["plc_name"]

    # Define the filter to find the document with the matching PLC name
    id_anchor_json = getting_id()
    filter = {"_id": str(ObjectId(id_anchor_json)), "plc.plc_name": plc_name}  # Convert ObjectId to string

    # Check if the PLC with the specified name exists
    local_mongo_collection = LocalMongoHelper().getCollection("workstations")
    workstation_data = local_mongo_collection.find_one(filter)

    if workstation_data:
        # Initialize a flag to check if PLC with specified name is found
        plc_found = False

        for plc in workstation_data.get("status", {}).get("plc", []):
            if plc["plc_name"] == plc_name:
                # PLC with the specified name found in the document
                plc_found = True
                status = "updated"

                # Define the update values using request_params
                update_values = {"$set": {}}
                for k, v in request_params.items():
                    update_values["$set"][f"plc.$.{k}"] = v

                # Update the local MongoDB
                update_result = local_mongo_collection.update_one(filter, update_values)

                if update_result.modified_count == 0:
                    # If no documents were modified, insert the updated document
                    updated_document = local_mongo_collection.find_one(filter)
                    if updated_document is not None:
                        updated_document.update(update_values["$set"])
                        local_mongo_collection.insert_one(updated_document)
                    else:
                        print("No document found for insertion")

        if not plc_found:
            status = "plc not found"
    else:
        # Collection does not exist, insert the new document
        local_mongo_collection.insert_one({"_id": str(ObjectId(id_anchor_json)), "plc": [request_params]})
        status = "collection not found, document inserted"

    response = {
        "data":workstation_data,
        "message": 119,
        "status": status
    }
    return json.dumps(response)







def update_inspection_station_details_utils(request_params):
    """
    Updating or adding new fields of the conveyor workstation details according to the
    object id.
    """
    

    headers = {"Content-Type": "application/json"}
    id_anchor_json = getting_id()
    filter = {"_id": id_anchor_json}
    new = {"$set": request_params}
    api_gateway__mongoDB_url = "http://localhost:5000/api_gateway/update_document"

    payload = json.dumps({"collection": "workstations", "document": [filter, new]})

    

   



    # access the mongoDB through api_gateway to get the inspection station details
    workstation_update_list_json = requests.request(
        "POST", api_gateway__mongoDB_url, headers=headers, data=payload,
    )

    local_mongo_collection = LocalMongoHelper().getCollection("workstations")
    update_result = local_mongo_collection.update_one({"_id": ObjectId(id_anchor_json)}, new)
    
    # Check if the local update was successful
    if update_result.modified_count > 0:
        status = "updated"
    else:
        status = "no update"

   
    
   
    
    
    status = "updated"
    return json.dumps({"status": status, "data":  workstation_update_list_json.json(),"message":121})


def connect_camera_utils(camera_type, camera_id, lock):
    lock.acquire()
    # user_doc = MongoHelper().getCollection("user_details").find_one({})
    # ws_id = user_doc["_id"]
    # send_stream_topic = str(ws_id)+"_"+str(camera_id)+"_i"
    send_stream_topic = str(camera_id) + "_i"

    send_stream_topic = send_stream_topic.replace(".", "")
    topic = send_stream_topic.replace(":", "")
    KAFKA_BROKER_URL = data["LOCAL_KAFKA_BROKER_URL"]

    if "USB" in camera_type:
        cam = VideoStream(
            KAFKA_BROKER_URL=KAFKA_BROKER_URL, topic=topic, camera_id=camera_id
        )
    elif "IP" in camera_type:
        cam = IP(KAFKA_BROKER_URL=KAFKA_BROKER_URL, topic=topic, camera_id=camera_id)
    elif "GIGE-BAUMER" in camera_type:
        # print(cam_idx)
        cam = Baumer(
            KAFKA_BROKER_URL=KAFKA_BROKER_URL, topic=topic, camera_id=camera_id
        )
        cam.connect()
    elif "RTSP" in camera_type:
        cam = RTSP(KAFKA_BROKER_URL=KAFKA_BROKER_URL, topic=topic, camera_id=camera_id)

    CacheHelper().set_json({"iskilled": False})
    data_queue = queue.Queue()

    def thread_function(data_queue):
        cam.start(data_queue)

    producer_thread = threading.Thread(
        target=thread_function, args=[data_queue], daemon=True
    )
    producer_thread.start()
    # print(shared_queue.get())
    # lock.release()
    iskilled = CacheHelper().get_json("iskilled")

    while not iskilled:
        try:
            frames = data_queue.get()
            print(frames)
            yield (
                b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frames + b"\r\n"
            )
            # if iskilled:
            #     break
        finally:
            continue
            # break
    print("reach")
    lock.release()

    # trying threads
    # def thread_function2(data_queue):
    #     # event.wait()
    #     print("inside con")
    #     while not iskilled:
    #         frames = data_queue.get()
    #         print(frames)
    #         print("yes")
    #         yield (b'--frame\r\n'
    #         b'Content-Type: image/jpeg\r\n\r\n' + frames + b'\r\n')

    # consumer_thread = threading.Thread(target = thread_function2,args=[data_queue],daemon=True)
    # consumer_thread.start()


def disconnect_camera_utils():
    print("Disconnecting camera...")
    CacheHelper().set_json({"iskilled": True})
    return "successfully disconnected"


