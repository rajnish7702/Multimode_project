from flask import Blueprint, request, jsonify, redirect, url_for, Response
import json
from bson.json_util import dumps

from operator_panel.inspection import *
from operator_panel.inspection_conveyor import *
import socket
from datetime import datetime
from operator_panel.common_utils import CacheHelper, Encoder
from flask_sse import sse
import threading

views = Blueprint("views", __name__)

# global t1
# t1 = threading.Thread(target=inspection(),daemon = True)
# t1.start()
# t1.join()
KEYS_TO_AVOID_RECIPIE = ['_id',  'created_at', 'info', 'input_controller', 'output_controller', 'recipe_id', 'recipie']


@views.route("/")
def hello():
    CacheHelper().publish("current_stream", "khali")

    return "Hello op"

@views.route("/get_running_status")
def get_running_status():
    mongo_obj = LocalMongoHelper()
    is_running = CacheHelper().get_json("is_running")
    if is_running is None:
        is_running=False
        current_batch = ""
    else:
        batches = mongo_obj.getCollection("batch_collection")
        current_batch = batches.find_one({"_id": ObjectId(CacheHelper().get_json('bid'))})
        del current_batch["_id"]
        bid = CacheHelper().get_json("bid")
        collection_name = f"batch_{bid}_logs"
        size_of_col = len(list(mongo_obj.getCollection(collection_name).find()))
        current_batch["Current batch size"] = size_of_col

    subscriber = CacheHelper().get_json("current_stats")
    
    
    result = {
        "message": 0,
        "data": {
            "is_running":is_running,
            "batch_details" : current_batch,
            "stream":subscriber
        }
    }

    response = Response(
        response=json.dumps(result, cls=Encoder), status=200, content_type="application/json"
    )
    return response

@views.route("/get_all_parts")
def get_all_parts():
    mongo_obj = LocalMongoHelper()
    recipie = mongo_obj.getCollection("deployed_recipie").find_one()
    parts = list(recipie.keys())
    for to_avoid in KEYS_TO_AVOID_RECIPIE:
        if to_avoid in parts:
            parts.remove(to_avoid)
    result = {
        "message": 0,
        "data": {
            "data": parts
            # "stream":value
        },
    }

    response = Response(
        response=json.dumps(result, cls=Encoder), status=200, mimetype="application/json"
    )
    return response
    


@views.route("/get_all_batches")
def get_all_batches():
    mongo_obj = LocalMongoHelper()
    batch_col = mongo_obj.getCollection("batch_collection")
    all_docs = list(batch_col.find())
    for doc in all_docs:
        del doc['_id']

    result = {
        "message": 0,
        "data": {
            "data":(all_docs),
            "count":len(all_docs),
        },
    }

    response = Response(
        response=json.dumps(result, cls=Encoder), status=200, mimetype="application/json"
    )
    return response    


@views.route("/stream", methods=["GET"])
def training_updates():
    """
    This function creates a streaming response to return either the metrics of a running experiment
    else returns a constant message
    """
    def running_experiments_stream():
        while True:
            subscriber = CacheHelper().subscribe("current_stream")
            yield ""

            for message in subscriber:
                
                print(message["data"])
                data = json.dumps(pickle.loads(message["data"]))
                yield 'data: %s\n\n' % data
        
    return Response(running_experiments_stream(), status=200, mimetype='text/event-stream')


@views.route("/get_operator_layout")
def get_operator_layout():
    cloud_mongo_obj = CloudMongoHelper()
    op_laypout = cloud_mongo_obj.getCollection("operator_layout_details").find_one()
    # print(op_laypout)
    del op_laypout['_id']
    
    result = {
        "message": 0,
        "data": {
            "data":op_laypout,
        },
    }

    response = Response(
        response=json.dumps(result, cls=Encoder), status=200, mimetype="application/json"
    )
    return response

@views.route("/get_operator_layout_details/<id>")
def get_operator_layout_details(id):
    mongo_obj = LocalMongoHelper()
    op_laypout = mongo_obj.getCollection("operator_layout_info").find_one({"data.layout_info._id": id})
    # print(op_laypout)
    
    result = {
        "message": 0,
        "data": {
            "data":op_laypout,
        },
    }

    response = Response(
        response=json.dumps(result, cls=Encoder), status=200, mimetype="application/json"
    )
    return response


@views.route("/sse")
def test_sse():
    # sse.publish("data", type='publish')
    # send_stream("one")
    # CacheHelper().send_stream("data")
    CacheHelper().publish("current_stream","gay")
    return "sent"


# @views.route("/start_process", methods=["POST"])
def start_batch(batch_name):
    """
    Payload :
    {
        "Batch name": "test_batch2"
    }

    Response:
        "batch {bid} started"
    """
    redis_obj = CacheHelper()
    mongo_obj = LocalMongoHelper()

    # params = request.get_json()
    # batch_name = params["Batch name"]

    redis_obj.set_json({"end_process": False})

    state_collection = mongo_obj.getCollection("batch_state")
    batches = mongo_obj.getCollection("batch_collection")
    current_batch = batches.find_one({"Batch name": batch_name})
    print(current_batch, "----------------------------")
    if current_batch:
        current_batch_id = current_batch["_id"]  # type: ignore
        print((current_batch_id), type(current_batch_id), "================")
        if current_batch_id:
            # checking for stored states
            print(current_batch_id)
            redis_obj.set_json({"bid": str(current_batch_id)})

            current_state_doc = state_collection.find_one(
                {"bid": str(current_batch_id)}
            )
            if current_state_doc:
                del current_state_doc["_id"]
                redis_obj.set_json({"current_state": current_state_doc})
                print(redis_obj.get_json("current_state"), "<-- stored state")
                # state_collection = mongo_obj.getCollection("batch_state")
                # print(state_collection)
                state_collection.delete_one({"bid": redis_obj.get_json("bid")})

            else:
                redis_obj.set_json({"current_state": None})
                # state_collection.insert_one({"bid":current_batch_id})

            redis_obj.set_json({"bid": str(current_batch_id)})
            redis_obj.set_json({"is_running": True})
            redis_obj.set_json({"inspection_completed": True})

            current_batch['_id']=str(current_batch['_id'])
            result = {
                "message": 131,
                "data": {
                    "status": (f"Process for Batch {str(current_batch_id)} started"),
                    "data": current_batch,
                },
            }

            response = Response(
                response=json.dumps(result, cls=Encoder ), status=200, mimetype="application/json"
            )
            return result
    else:
        result = {
            "message": 129,
            "data": {"status": (f"Batch with given name not found")},
        }
        response = Response(
            response=json.dumps(result, cls=Encoder), status=400, mimetype="application/json"
        )
        return result


@views.route("/end_process")
def end_process():
    """

    Response:
        "Batch {current_batch_id} stopped"
    """

    redis_obj = CacheHelper()
    mongo_obj = LocalMongoHelper()
    current_batch_id = redis_obj.get_json("bid")
    redis_obj.set_json({"end_process": True})
    if current_batch_id:
        # update mongo for stare
        is_completed = redis_obj.get_json("inspection_completed")
        state_collection = mongo_obj.getCollection("batch_state")
        print(is_completed)
        # time.sleep(2)
        if is_completed:
            #     # delete doc of state
            # state_collection.delete_one({"bid": current_batch_id})
            redis_obj.set_json({"inspection_completed": False})

        # flush redis keys
        # redis_obj.redis_cache.delete("bid")
        redis_obj.redis_cache.delete("is_running")

        result = {
            "message": 132,
            "data": {"status": (f"Batch {str(current_batch_id)} stopped")},
        }
        response = Response(
            response=json.dumps(result, cls=Encoder), status=200, mimetype="application/json"
        )
        return response

    else:
        result = {
            "message": 133,
            "data": {"status": (f"No batch running")},
        }
        response = Response(
            response=json.dumps(result, cls=Encoder), status=200, mimetype="application/json"
        )
        return response


@views.route("/create_batch", methods=["POST"])
def create_batch():
    # part = request.josn('Part')
    # batch_id = request.josn('Batch size')
    # batch_name = request.json('Batch name')
    """
    Payload :
    {
        "Part": "Part A",
        "Batch size": 10,
        "Batch name": "test_batch2"
    }

    Response:
        "batch created"
    """
    redis_obj = CacheHelper()
    mongo_obj = LocalMongoHelper()

    params = request.get_json()

    if not params["Batch size"] or not params["Batch name"] or not params["Part"]:
        result = {
            "message": 128,
            "data": {
                "status": (f"Missing values batch size or batch number or part"),
                "data": str(params),
                "workstation_type": redis_obj.get_json("workstation_type"),
            },
        }
        response = Response(
            response=json.dumps(result, cls=Encoder), status=400, mimetype="application/json"
        )
        return response

    if params["Batch size"] <= 0:
        result = {
            "message": 128,
            "data": {
                "status": (f"Batch size should not be zero"),
                "data": params,
                "workstation_type": redis_obj.get_json("workstation_type"),
            },
        }
        response = Response(
            response=json.dumps(result, cls=Encoder), status=400, mimetype="application/json"
        )
        return response
        

    print(redis_obj.get_json("is_running"))
    if redis_obj.get_json("is_running"):
        print("why")
        result = {
            "message": 130,
            "data": {"status": (f"Batch {redis_obj.get_json('bid')} already running")},
            "workstation_type": redis_obj.get_json("workstation_type"),
        }
        response = Response(
            response=json.dumps(result, cls=Encoder), status=200, mimetype="application/json"
        )
        return response

    current_batch_name = params["Batch name"]
    predefined_col = mongo_obj.getCollection("predefined_batch")
    existing_batches = predefined_col.find()

    if any(
        batch["Batch name"] == params["Batch name"] for batch in list(existing_batches)
    ):
        # batch already there - >start process for this batch
        # start_batch()
        
        process_response = start_batch(current_batch_name)

        bid = redis_obj.get_json("bid")
        collection_name = f"batch_{bid}_logs"
        size_of_col = len(list(mongo_obj.getCollection(collection_name).find()))

        result = {
            "message": 126,
            "data": {
                "status": (f"Batch with given name already exists"),
                "data": params,
                "process_response": process_response,
                "workstation_type": redis_obj.get_json("workstation_type"),
                "batches_inspected": f"{size_of_col}",
            },
        }
        response = Response(
            response=json.dumps(result, cls=Encoder), status=200, mimetype="application/json"
        )
        return response
    
    created_at = datetime.now()

    batch_col = mongo_obj.getCollection("batch_collection")
    params["_id"] = ObjectId()

    predefined_doc = {}
    predefined_doc["_id"] = ObjectId()
    predefined_doc["Batch name"] = params["Batch name"]
    predefined_doc["Batch size"] = params["Batch size"]
    predefined_doc["batch_id"]= str(params["_id"])
    predefined_doc["created_at"] = created_at
    predefined_col.insert_one(predefined_doc)

    params["created_at"] = created_at
    result = batch_col.insert_one(params)
    # print((result.inserted_id))
    # redis_obj.set_json({"bid": str(result.inserted_id)})

    datem = str(datetime.now().year) + "-" + str(datetime.now().month)
    # datem = datetime.strptime(datem, "%Y-%m")
    name = str("inspection_" + str(datem))
    inspection_col = mongo_obj.getCollection(name)
    temp = {
        "batch_id": str(params["_id"]),
    }
    temp["_id"] = ObjectId()
    temp["created_at"] = created_at
    # print(temp, "****************")
    result = inspection_col.insert_one(temp)
    process_response = start_batch(current_batch_name)

    bid = redis_obj.get_json("bid")
    collection_name = f"batch_{bid}_logs"
    size_of_col = len(list(mongo_obj.getCollection(collection_name).find()))
    params['_id'] =str(params['_id'])

    result = {
        "message": 125,
        "data": {
            "status": (f"Batch created"),
            "data": params,
            "process_reesponse": process_response,
            "workstation_type": redis_obj.get_json("workstation_type"),
            "batches_inspected": f"{size_of_col}",
        },
    }
    response = Response(
        response=json.dumps(result, cls=Encoder), status=201, mimetype="application/json"
    )
    return response


@views.route("/inspect", methods=["GET"])
def inspect():
    # if post req, take data from request
    redis_obj = CacheHelper()
    mongo_obj = LocalMongoHelper()
    recipie = mongo_obj.getCollection("deployed_recipie").find_one()

    # print(recipie)

    current_batch_id = redis_obj.get_json("bid")
    batches = mongo_obj.getCollection("batch_collection")
    current_batch = batches.find_one({"_id": ObjectId(current_batch_id)})
    status = redis_obj.get_json("is_running")
    inspection_completed = redis_obj.get_json("inspection_completed")
    # print(current_batch,"----")
    # if inspect false - >already running, else

    # return "None"
    if status:
        print(inspection_completed)
        if not inspection_completed:
            bid = redis_obj.get_json("bid")
            collection_name = f"batch_{bid}_logs"
            size_of_col = len(list(mongo_obj.getCollection(collection_name).find()))
            result = (
                {
                    "message": 134,
                    "data": {
                        "status": (f"Inspection already running"),
                        "data": f"{current_batch}",
                        "batches_inspected": f"{size_of_col}",
                    },
                },
            )

            response = Response(
                response=json.dumps(result, cls=Encoder), status=400, mimetype="application/json"
            )
            return response
            return {"status": "Already started inspection", "status_code": 200}, 200
        else:
            # redis_obj.set_json({"current_state":None})
            pass

        # recipie = json.loads(recipie)
        print(CacheHelper().get_json("bid"))
        if recipie["info"]["workstation_type"] == "conveyor":
            conveyor_inspection()
            start = "conveyor"
        elif recipie["info"]["workstation_type"] == "cobot":
            inspection()
            start = "cobot"
        else:
            inspection()
            start = "static"
            redis_obj.set_json({"start_inspection": True})

        bid = redis_obj.get_json("bid")
        collection_name = f"batch_{bid}_logs"
        size_of_col = len(list(mongo_obj.getCollection(collection_name).find()))
        # t1.join()
        result = (
            {
                "message": 135,
                "data": {
                    "status": (f"(inspection started for {start})"),
                    "data": f"{current_batch}",
                    "batches_inspected": f"{size_of_col}",
                },
            },
        )

        response = Response(
            response=json.dumps(result, cls=Encoder), status=200, mimetype="application/json"
        )
        return response

    else:
        result = (
            {
                "message": 133,
                "data": {
                    "status": (f"No Process started"),
                },
            },
        )

        response = Response(
            response=json.dumps(result, cls=Encoder), status=400, mimetype="application/json"
        )
        return response


@views.route("/update_batch", methods=["POST"])
def update_batch():
    updated_batch_size = request.json.get("Batch size", None)
    batch_name = request.json.get("Batch name", None)
    mongo_obj = LocalMongoHelper()
    inspection_col = mongo_obj.getCollection("batch_collection")
    inspection = inspection_col.find_one({"Batch name": batch_name})

    if inspection is None:
        result = (
            {
                "message": 129,
                "data": {
                    "status": (f"Batch with given name not found"),
                },
            },
        )

        response = Response(
            response=json.dumps(result, cls=Encoder), status=400, mimetype="application/json"
        )
        return response

    previous_batch_size = inspection.get("Batch size", None)

    if updated_batch_size:
        if previous_batch_size:
            if previous_batch_size >= updated_batch_size:
                result = (
                    {
                        "message": 138,
                        "data": {
                            "status": (f"New Batch size must be greater than previous"),
                            "previous_size": previous_batch_size,
                        },
                    },
                )

                response = Response(
                    response=json.dumps(result, cls=Encoder), status=400, mimetype="application/json"
                )
                return response

        inspection_col.update_one(
            {"Batch name": batch_name}, {"$set": {"Batch size": updated_batch_size}}
        )
        predefined = mongo_obj.getCollection("predefined_batch")
        predefined.update_one({}, {"$set": {"Batch size": updated_batch_size}})
        result = (
            {
                "message": 137,
                "data": {
                    "status": (f"Batch updated"),
                },
            },
        )

        response = Response(
            response=json.dumps(result, cls=Encoder), status=200, mimetype="application/json"
        )
        return response

    result = (
        {
            "message": 136,
            "data": {
                "status": (f"Invalid batch size"),
            },
        },
    )

    response = Response(
        response=json.dumps(result, cls=Encoder), status=400, mimetype="application/json"
    )
    return response
