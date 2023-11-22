from common_utils import LocalMongoHelper, CacheHelper , logger, http_server_for_meta_data_util
from bson.objectid import ObjectId
import requests
import json
import pandas
import pickle
import random
import threading
from datetime import datetime


import time
from collections import defaultdict 

from Business_logic import *


LINK = http_server_for_meta_data_util()
logger.success(LINK)

def infer(data, part):
    """
    Description:
            Sorts line item to generate response and results
    """
    redis_obj = CacheHelper()
    mongo_obj = LocalMongoHelper()
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
        if result["camera_number"] != "NONE":
            model_data[model].append(result["camera_number"])
        try:
            ports[model] = result["Port Number"]
        except:
            ports[model] = ""
    # print(model_data,ports, part,)
    current_state = redis_obj.get_json("current_state")
    print(current_state)
    if current_state:
        for mod in model_data.copy().keys():
            if current_state["model"] == mod:
                break
            del model_data[mod]

    print(model_data)
    for key, value in model_data.items():
        print(key, value, ports[key], part)
        # time.sleep(6)
        port = ports[key]
        model = key
        part = redis_obj.get_json("part_name")
        end_process = redis_obj.get_json("end_process")
        print(redis_obj.get_json("bid"))
        if end_process:
            current_state = {
                "bid": redis_obj.get_json("bid"),
                "cid": redis_obj.get_json("cid"),
                "model": model,
            }
            print(current_state, "<- current state")
            state_collection = mongo_obj.getCollection("batch_state")

            redis_obj.set_json({"current_state": current_state})
            updated_state = {"$set": current_state}
            arg = {"bid": redis_obj.get_json("bid")}
            state_collection.update_one(arg, updated_state, upsert=True)
            break
        camera = value
        camera_list = list(cam.replace(" ", "") for cam in camera)
        print(camera_list, type(camera_list))

        # continue
        if model == "MOCR":
            continue
            # camera list will always have 1 camera
            url = "http://127.0.0.1:" + port + "/detectocr"
            payload = {
                "topic": str(camera_list[0]),
            }

            headers = {"Content-Type": "application/json"}
            response = requests.request(
                "POST", url, headers=headers, data=json.dumps(payload)
            )
            data = response.json()
            print(data["status"]["text"], type(data))
            temp = data["status"]["text"]
            response_data = {"status": [temp]}
            # print(response_data["status"], type(response_data['status']))
        elif model == "MBAR":
            continue
            # camera list will always have 1 camera
            url = "http://127.0.0.1:" + port + "/detectbar"
            payload = {
                "topic": str(camera_list[0]),
            }

            headers = {"Content-Type": "application/json"}
            response = requests.request(
                "POST", url, headers=headers, data=json.dumps(payload)
            )
            data = response.json()
            temp = data["status"]
            response_data = {"status": [temp]}
        else:
            from time import perf_counter

            t1_start = perf_counter()
            current_model = model.replace(" ", "")
            print(current_model)

            redis_obj.set_json({f"{current_model}_res": None})
            redis_obj.set_json({f"{current_model}": None})
            # format of redis keys used to communicate to container
            # M1 : [cam1, cam2]
            # M1_res : [res1,res2]
            redis_obj.set_json({current_model: camera_list})
            print(redis_obj.get_json(current_model), "<- set in redis")

            # can we change this?, because if container fails, this loop will break the flow.
            while True:
                response_list = redis_obj.get_json(f"{current_model}_res")
                # print(response_list)
                if response_list is None:
                    pass
                else:
                    response_data = response_list
                    redis_obj.set_json({f"{current_model}_res": None})
                    redis_obj.set_json({f"{current_model}": None})
                    break
            t1_stop = perf_counter()
            print("infer time taken", t1_stop - t1_start)

        print(len(response_data), len(camera))
        # print(response_data[0])
        # response = ["res1", "res2", "res3", "res4", "res5"]
        cid = redis_obj.get_json("cid")
        bid = redis_obj.get_json("bid")
        collection_name = f"batch_{bid}_logs"
        size_of_col = len(list(mongo_obj.getCollection(collection_name).find()))

        # data to send to bl
        data_bl = defaultdict(list) 
        # call BL
        for j, cam in enumerate(camera):

            query = {
                "_id": ObjectId(cid),
                f"{part}": {
                    "$elemMatch": {
                        "model_number": model,
                        "camera_number": cam,  # Replace with the desired Camera_number
                    }
                },
            }
            projection = {
                "_id": 0,
                f"{part}.features_count_logic": 1,
                f"{part}.defects_count_logic": 1,
                f"{part}.camera_number": 1,
                f"{part}.model_number": 1,
            }
            doc = (
                LocalMongoHelper()
                .getCollection(collection_name)
                .find_one(query, projection)
            )
            # doc = list(doc
            # print(doc)
            doc = doc[part]
            for re in doc:
                if re["camera_number"] == cam and re["model_number"] == model:
                    doc = re
                    break
            # print(doc, "<--")

            Count_logic_features = doc["features_count_logic"]
            Count_logic_defects = doc["defects_count_logic"]
            data_for_bl= [Count_logic_features,Count_logic_defects,response_data[j],""]
            data_bl[cam] = data_for_bl
        logger.error(data_bl)
        time.sleep(1)
        # call BL
        result_data = business_logic_all(data_bl,current_model,LINK)
        logger.info(result_data)

        # store data and keep track
        aggregate_model_result = "Accepted"
        for j, cam in enumerate(camera):
            res = result_data[cam]["result"]
            if res == "Rejected":
                aggregate_model_result = "Rejected"
            
            result_data[cam]["feature_actual"] = data_bl[cam][0]
            result_data[cam]["defects_actual"] = data_bl[cam][1]


            filter = {"_id": ObjectId(cid)}
            array_filters = [
                {
                    "element.model_number": model,
                    "element.camera_number": cam,
                }
            ]
            update = {
                "$set": {
                    f"{part}.$[element].Response": response_data[j],
                    f"{part}.$[element].Result": res,
                }
                # "arrayFilters":array_filters,
            }
            # update vaule in python
            LocalMongoHelper().getCollection(collection_name).update_one(
                filter, update, array_filters=array_filters, upsert=False
            )

        # setting model results to redis
        result_status = redis_obj.get_json("result_status")
        logger.error(result_status)
        result_status[model] = result_data
        result_status[model]["model_result"] = aggregate_model_result
        if aggregate_model_result == "Rejected":
            result_status["overall_result"] = "Rejected"
        elif result_status["overall_result"] == "Rejected": 
            result_status["overall_result"] = "Rejected"
        else:
            result_status["overall_result"] = aggregate_model_result
        redis_obj.set_json({"result_status":result_status})

        #update mongodb with results at every mode - > store result_status to mongodb "result" key
        filter= {"_id": ObjectId(cid)}
        update ={"$set": {
                    f"result": result_status,
                    "created_at": datetime.now()
                }}
        LocalMongoHelper().getCollection(collection_name).update_one(
                filter, update, upsert=True
            )
        rj_count = LocalMongoHelper().getCollection(collection_name).count_documents({"result.overall_result": "Rejected"})
        
        # call sse here
        if model == models[-1]:
            # add inspection result in mongodb with aggregation here
 
            stream_data = {
                "total_part": f"{redis_obj.get_json('last_part')}",
                "current_part": f"{part}",
                "status": result_status,
                # "overall_status": f"{result_temp}",
                "overall_status": "Rejected",
                "current_model": f"{model}",
                "total_model": f"{models[-1]}",
                "is_completed": True,
                "inspection_count": size_of_col,
                "is_batch_full": redis_obj.get_json("is_batch_full"),
                "ac_count": size_of_col - rj_count,
                "rj_count": rj_count,
            }

        else:
            stream_data = {
                "total_part": f"{redis_obj.get_json('last_part')}",
                "current_part": f"{part}",
                "status": result_status,
                # "overall_status": f"{result_temp}",
                "overall_status": "Rejected",
                "current_model": f"{model}",
                "total_model": f"{models[-1]}",
                "is_completed": redis_obj.get_json("inspection_completed"),
                "inspection_count": size_of_col,
                "is_batch_full": redis_obj.get_json("is_batch_full"),
                "ac_count": size_of_col-rj_count,
                "rj_count": rj_count,
            }
        # redis_obj.send_stream(stream_data)
        redis_obj.publish("current_stream", pickle.dumps(stream_data))
        redis_obj.set_json({"current_stats": dict(stream_data)})
        '''
        for j, cam in enumerate(camera):
            # df = pandas.DataFrame(response['status'][j])
            # data = pickle.dumps(df)
            # print(data)
            # call BL here
            # change this way
            # doc = (
            #     LocalMongoHelper()
            #     .getCollection(collection_name)
            #     .find_one({"_id": ObjectId(redis_obj.get_json("cid"))})
            # )
            # print(part)

            # Count_logic_features = [
            #     item["Count_logic_features"]
            #     for item in doc[part]
            #     if item["Usecase_number"] == model
            #     and item["Camera_number"] == cam
            # ]
            # Count_logic_defects = [
            #     item["Count_logic_defects"]
            #     for item in doc[part]
            #     if item["Usecase_number"] == model
            #     and item["Camera_number"] == cam
            # ][0]
            # print(Count_logic_defects,"->",Count_logic_features)

            # Count_logic_defects = doc["Count_logic_defects"]
            # Count_logic_features = doc["Count_logic_features"]
            # get features and defects from mongo here when proper recipie is made.
            print(cam, model, part)
            # pipeline = [
            # {
            # "$match": {
            # "_id": ObjectId(cid),
            # f"{part}": {
            # "$elemMatch": {
            # "Usecase_number": model,
            # "Camera_number": cam,  # Replace with the desired Camera_number
            # }
            # },
            # }
            # },
            # {"$unwind": f"${part}"},
            #
            # {
            # "$project": {
            # "_id": 0,
            # "Count_logic_features": f"${part}.Count_logic_features",
            # "Count_logic_defects": f"${part}.Count_logic_defects",
            # }
            # },
            # ]
            # doc = (
            #     LocalMongoHelper()
            #     .getCollection(collection_name).
            #     aggregate(pipeline)
            # )
            # query = {
            #     "_id": ObjectId(cid),
            #     f"{part}": {
            #         "$elemMatch": {
            #             "Usecase_number": model,
            #             "Camera_number": cam,  # Replace with the desired Camera_number
            #         }
            #     },
            # }
            # projection = {
            #     "_id": 0,
            #     f"{part}.Count_logic_features": 1,
            #     f"{part}.Count_logic_defects": 1,
            #     f"{part}.Camera_number": 1,
            #     f"{part}.Usecase_number": 1,
            # }

            # doc = (
            #     LocalMongoHelper()
            #     .getCollection(collection_name)
            #     .find_one(query, projection)
            # )
            # # doc = list(doc
            # print(doc)
            # doc = doc[part]
            # for re in doc:
            #     if re["Camera_number"] == cam and re["Usecase_number"] == model:
            #         doc = re
            #         break
            # print(doc, "<--")

            # Count_logic_features = doc["Count_logic_features"]
            # Count_logic_defects = doc["Count_logic_defects"]
            # response_data[j] = response_data[j].to_dict('records')
            from time import perf_counter

            t1_start = perf_counter()
            result = business_logic(
                response_data[j], Count_logic_features, Count_logic_defects
            )
            print(result)

            # result = "Accept"
            ac_count = redis_obj.get_json("ac_count")

            # call sse here
            # if model == models[-1]:
            #     stream_data = {
            #         "total_part": f"{redis_obj.get_json('last_part')}",
            #         "current_part": f"{part}",
            #         "model_status": {},
            #         # "overall_status": f"{result_temp}",
            #         "overall_status": "Rejected",

            #         "current_model": f"{model}",
            #         "total_model": f"{models[-1]}",
            #         "is_completed": True,
            #         "image": f"https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS8IHbPDhNDZR37HhcpzkRukmIgl0SwcRGOUg&usqp=CAU",
            #         "inspection_count": size_of_col,
            #         "is_batch_full": redis_obj.get_json("is_batch_full"),
            #         "ac_count": 0,
            #         "rj_count": size_of_col,
            #         "features": Count_logic_features,
            #         "defects": Count_logic_features,
            #     }

            # else:
            #     stream_data = {
            #         "total_part": f"{redis_obj.get_json('last_part')}",
            #         "current_part": f"{part}",
            #         "model_status": {},
            #         # "overall_status": f"{result_temp}",
            #         "overall_status": "Rejected",
            #         "current_model": f"{model}",
            #         "total_model": f"{models[-1]}",
            #         "is_completed": redis_obj.get_json('inspection_completed'),
            #         "image": f"https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS8IHbPDhNDZR37HhcpzkRukmIgl0SwcRGOUg&usqp=CAU",
            #         "inspection_count": size_of_col,
            #         "is_batch_full": redis_obj.get_json("is_batch_full"),
            #         "ac_count": 0,
            #         "rj_count": size_of_col,
            #         "features": Count_logic_features,
            #         "defects": Count_logic_defects,
            #     }
            # # redis_obj.send_stream(stream_data)
            # redis_obj.publish("current_stream", pickle.dumps(stream_data))
            # redis_obj.set_json({"current_stats": dict(stream_data)})

            filter = {"_id": ObjectId(cid)}
            array_filters = [
                {
                    "element.Usecase_number": model,
                    "element.Camera_number": cam,
                }
            ]
            update = {
                "$set": {
                    f"{part}.$[element].Response": response_data[j],
                    f"{part}.$[element].Result": result,
                }
                # "arrayFilters":array_filters,
            }
            # update vaule in python
            LocalMongoHelper().getCollection(collection_name).update_one(
                filter, update, array_filters=array_filters, upsert=False
            )
            t1_stop = perf_counter()
            print(t1_stop - t1_start)

            '''

    return "infer done"


def static_utils():
    """
    Description:
            Service for static. Controls the static.
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

        redis_obj = CacheHelper()
        mongo_obj = LocalMongoHelper()
        if service_status and is_running:
            part = redis_obj.get_json("part_name")
            current_inspection_id = redis_obj.get_json("cid")
            batch_id = redis_obj.get_json("bid")
            log_collection_name = f"batch_{batch_id}_logs"
            redis_obj.set_json({"inspection_completed": False})

            print(part)
            print(current_inspection_id)

            results = mongo_obj.getCollection(log_collection_name).find_one(
                {"_id": ObjectId(current_inspection_id)}
            )
            print(results)

            # set clear redis for results
            result_status = {
                "overall_result" : "Accepted",
            }
            redis_obj.set_json({"result_status":result_status})

            # call infer
            print(infer(results[part], part))

            # update mongo for results
            logger.success(redis_obj.get_json("result_status"))

            redis_obj.set_json({"inspection_completed": True})
            redis_obj.set_json({"current_state": None})

            redis_obj.set_json({"service_status": False})
        else:
            pass


# static_utils()

if __name__ == "__main__":
    static_utils()
