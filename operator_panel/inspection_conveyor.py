from operator_panel.common_utils import *
from bson.objectid import ObjectId
import json
import time
import json
from operator_panel.plc_module import Button

# from common_utils import LOCAL_REDIS_HOST,LOCAL_REDIS_PORT,CLOUD_MONGO_HOST,CLOUD_MONGO_PORT,CLOUD_MONGO_DB
from pprint import pprint
import threading



def create_plc(params=["192.168.1.50", "21", "0", "1"]):
    """
    Description:
                    Creates a PLC button based on the params.
    """
    button = Button(params[0], int(params[1]), int(params[2]), int(params[3]))
    # output_button = Button
    plc_trigger(button)


def plc_trigger(button):
    """
    Description:
                    Controls PLC triggers based on the input.
    """
    input_flag = False
    while True:
        input = button.get_status()
        if input == 1 and not input_flag:
            print("Trigger")
            time.sleep(2)
            input_flag = True
            # for setting inspect
            CacheHelper().set_json({"plc_trigger": True})
            # for trigger to know which cycle/part to execute
            CacheHelper().set_json({"plcId": button.ip})
            # turn on the camera
            # CacheHelper().set_json({"inspect":True})

        if input == 0 and input_flag:
            input_flag = False

        # isAccepted = CacheHelper().get_json("isAccepted")
        # if isAccepted is not None:
        #     CacheHelper().set_json({"isAccepted":None})
        #     if isAccepted:
        #         output_button.write_value(1)
        #     else:
        #         output_button.write_value(2)


# plc_exists = False


# def plc_trigger1():
#     print("Listening for trigger")
#     sensor_config = data["data_capture"]["plc"]["sensor"]
#     output_config = data["data_capture"]["plc"]["output"]

#     # Check if IP of PLCs is same
#     if sensor_config[0] == output_config[0]:
#         plc = PLC(sensor_config[0]).plc
#         sensor_trigger = Button("192.168.1.50", 2, 0, 1)
#         print(sensor_trigger)
#         # sensor_trigger = Button(plc, sensor_config[1], sensor_config[2], sensor_config[3])
#         output_button = Button(plc, output_config[1], output_config[2], output_config[3])
#     else:
#         plc1 = PLC(sensor_config[0]).plc
#         plc2 = PLC(output_config[0]).plc
#         sensor_trigger = Button(plc1, sensor_config[1], sensor_config[2], sensor_config[3])
#         output_button = Button(plc2, output_config[1], output_config[2], output_config[3])

#     sensor_flag = False
#     CacheHelper().set_json({"trigger":False})

#     while True:
#         sensor_value = sensor_trigger.get_value()
#         if sensor_value == 1 and not sensor_flag:
#             sensor_flag = True
#             CacheHelper().set_json({"trigger":True})
#         elif sensor_value == 0 and sensor_flag:
#             sensor_flag = False


def conveyor_inspection():
    """
    Description:
                    Starts inspection for the selected branch. For conveyor(exclusively by plc).
                    This initiates inspection and controls the flow of individual inspection
    Input:
        Batch_id(redis)

    Db names: 
        - lincode_batch_collection
        - lincode_temp_static
        - lincode_batch_{bid}_logs  (created automatically)
    """

    try:
        redis_obj = CacheHelper()
        mongo_obj = LocalMongoHelper()
    except:
        print("Couldn't connect to redis or mongodb")
        redis_obj = None
        mongo_obj = None

    redis_obj.set_json({"inspection_completed": False})
    redis_obj.set_json({"service_status": False})
    redis_obj.set_json({"cid": None})
    bid = redis_obj.get_json("bid")
    is_running = redis_obj.get_json("is_running")

    # copy data to logs from temp
    if bid and is_running:
        batch = mongo_obj.getCollection("batch_collection")
        batch = batch.find_one({"_id": ObjectId(bid)})
        # get data from batch doc
        part_name = batch["Part"]
        bsize = int(batch["Batch size"])
        collection_name = f"batch_{bid}_logs"
        size_of_col = len(list(mongo_obj.getCollection(collection_name).find()))
        redis_obj.set_json({"part_name": part_name})

        if size_of_col < bsize:
            size_of_col = len(list(mongo_obj.getCollection(collection_name).find()))
            print(size_of_col)
            
            recipie = LocalMongoHelper().getCollection("deployed_recipie").find_one()
            # results = results[part_name]
            # pprint((results))
            last_part = list(recipie.keys())[-1]
            redis_obj.set_json({'last_part': last_part})


            # make plc object
            plc_data = recipie[part_name][0]
            plc_input = plc_data["PLC_INPUT"].strip("{}")
            plc_input = plc_input.split(",")
            plc_input = [plc.strip("'") for plc in plc_input]
            print(plc_input)

            # createing plc thread (plc_input)
            t = threading.Thread(target=create_plc, args=(plc_input,))
            t.start()

            collection = mongo_obj.getCollection(collection_name)
            recipie["_id"] = ObjectId()
            result = collection.insert_one(recipie)
            # print((result.inserted_id))
            redis_obj.set_json({"cid": str(result.inserted_id)})
            print(redis_obj.get_json("cid"))
            time.sleep(2)

            redis_obj.set_json({"service_status": True})
            print(redis_obj.get_json("service_status"))

            # # if true, start next inspection
            # subscriber = redis_obj.subscribe('inspection_completed')
            # for message in subscriber:
            #     print(message)
            #     if message["data"] == b"True":
            #         redis_obj.set_json({"service_status": False})
            #         # code sometimes breaking if cid set to none
            #         # redis_obj.set_json({"cid":None})
            #         redis_obj.set_json({"inspection_completed": False})
            #         # print("init")
            #         break
            #     else:
            #         print("something went wrong with inspection cycle of ", id)
            #     # break
            print("end")
        else:
            redis_obj.set_json({"is_running" : False})

            pass
        # tells that all inspections
        return "inspection started"


        
    else:
        print("Batch not selected")

     
# inspection()

if __name__ == "__main__":
    conveyor_inspection()