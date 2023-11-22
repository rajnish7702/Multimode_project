from common_utils import LocalMongoHelper, CacheHelper
from bson.objectid import ObjectId
import requests 
import json
import pandas
import pickle
import random


# update response, bl and result
def infer(data, part):
    """
    Description:
            Sorts line item to generate response and results
    """
    redis_obj = CacheHelper()
    key = data[0]["model_number"]
    models = []
    # make unique list of models
    for result in data:
        models.append(result["model_number"])
    models = list(set(models))
    # making models-camera and model-ports
    ports = {}
    model_data = {}
    models.sort()
    for model in models:
        model_data.setdefault(model, [])
        ports.setdefault(model, "")
    for result in data:
        model = result["model_number"]
        model_data[model].append(result["camera_number"])
        ports[model] = result["Port Number"]
    # print(model_data,ports, part,)
    for key, value in model_data.items():
        print(key, value, ports[key], part)
        port = ports[key]
        model = key
        part = redis_obj.get_json("part_name")

        camera = value
        camera_list = list(cam.replace(" ","") for cam in camera)
        print(camera_list, type(camera_list))

        # continue
        if model == "MOCR":
            # camera list will always have 1 camera
            url="http://127.0.0.1:"+port+"/detectocr"
            payload = {
                "topic": str(camera_list[0]),
            }
        
            headers = {"Content-Type": "application/json"}
            response = requests.request("POST", url, headers=headers, data= json.dumps(payload))
            data=response.json()
            print(data["status"]['text'], type(data))
            temp = data['status']['text']
            response_data = {
                "status" : [temp]
            }
            # print(response_data["status"], type(response_data['status']))
        elif model == 'MBAR':
            # camera list will always have 1 camera
            url="http://127.0.0.1:"+port+"/detectbar"
            payload = {
                "topic": str(camera_list[0]),
            }
        
            headers = {"Content-Type": "application/json"}
            response = requests.request("POST", url, headers=headers, data= json.dumps(payload))
            data=response.json()
            temp = data['status']
            response_data = {
                "status" : [temp]
            }
        else:
            url="http://127.0.0.1:"+port+"/infer"
            # url = "http://127.0.0.1:2766/infer"
        
        
            payload = {
                    "model": {
                        "url": "https://storage.googleapis.com/test_28001/yolov5m6.pt"
                    },
                    "camera": {"camera_name":camera_list},
                }
        
            headers = {"Content-Type": "application/json"}
            response = requests.request("POST", url, headers=headers, data= json.dumps(payload))
            response_data=response.json()
            headers = {"Content-Type": "application/json"}
            response = requests.request("POST", url, headers=headers, data= json.dumps(payload))
            response_data=response.json()

        print(type(response_data['status'][0]), response_data['status'])


        # response = ["res1", "res2", "res3", "res4", "res5"]
        cid = redis_obj.get_json("cid")
        bid = redis_obj.get_json("bid")
        collection_name = f"batch_{bid}_logs"

        for j, cam in enumerate(camera):
            # df = pandas.DataFrame(response['status'][j])
            # data = pickle.dumps(df)
            # print(data)
            # call BL here
            # result = "Accept"
            result = random.choice(["Accepted", "Rejected"])
            # call sse here

            stream_data ={
                "part" : f"{part}/{redis_obj.get_json('last_part')}",
                "result" : f'{result}',
                "is_completed" : f"{redis_obj.get_json('inspection_completed')}"
            }
            redis_obj.send_stream(stream_data)

            filter = {"_id": ObjectId(cid)}
            array_filters = [
                {
                    "element.model_number": model,
                    "element.camera_number": cam,
                }
            ]
            update = {
                "$set": {f"{part}.$[element].Response": response_data['status'][j],
                         f"{part}.$[element].Result": result}
                # "arrayFilters":array_filters,
            }
            # update vaule in python
            LocalMongoHelper().getCollection(collection_name).update_one(
                filter, update, array_filters=array_filters, upsert=False
            )

    return "infer done"



def conveyor_utils():
    """
    Description:
            Service for Conveyor. Controls the Conveyor.
            Sends list of camera kafka topic to model container and updated logs with response, then send to BL and updates logs with results.
    Input:
        All inputs are via redis.

            service_status : True 
            cid : str 
            bid : str
            part_name : str
    
    Oputput:
        Updates logs for batch with result and response.

    """


    while True:
        service_status = CacheHelper().get_json("service_status")
        is_running = CacheHelper().get_json("is_running")

        # print(service_status)
        redis_obj = CacheHelper()
        mongo_obj = LocalMongoHelper()
        if service_status and is_running:
            part = redis_obj.get_json("part_name")
            current_inspection_id = redis_obj.get_json("cid")
            batch_id = redis_obj.get_json("bid")
            log_collection_name = f"batch_{batch_id}_logs"

            print(part)
            print(current_inspection_id)
            results = (
                 mongo_obj
                .getCollection(log_collection_name)
                .find_one({"_id": ObjectId(current_inspection_id)})
            )
            # print(results)
            plc_trigger = redis_obj.get_json("plc_trigger")
            # call infer if plc is triggered
            if plc_trigger:
                print(infer(results[part], part))
                redis_obj.set_json({"inspection_completed": True})
                redis_obj.set_json({"service_status": False})
                
            else:
                pass
                "No plc triggered"
            

if __name__ == "__main__":
    conveyor_utils()
