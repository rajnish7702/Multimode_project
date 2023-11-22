from operator_panel.common_utils import *
import time




def inspection():
    """
    Description:
            Starts inspection for the selected branch. For static and cobot.
            This initiates inspection and controls the flow of individual inspection
    Input:
        Batch_id(redis)

    Db names: 
        - lincode_batch_collection
        - deployed_recipie
        - lincode_batch_{bid}_logs  (created automatically)
    """

    try:
        redis_obj = CacheHelper()
        mongo_obj = LocalMongoHelper()
    except:
        print("Couldn't connect to redis or mongodb")
        redis_obj = None
        mongo_obj = None
    
    
    redis_obj.set_json({"service_status": False})
    redis_obj.set_json({"cid": None})
    bid = redis_obj.get_json("bid")
    is_running = redis_obj.get_json("is_running")
    current_state = redis_obj.get_json("current_state")
    print(current_state)
    if current_state:
        redis_obj.set_json({"inspection_completed": False})
    # bid = "64f6fcfc10968abd80cad884"
    # redis_obj.set_json({"bid": bid})
    # copy data to logs from temps
    if bid and is_running:
        batch = mongo_obj.getCollection("batch_collection")
        batch = batch.find_one({"_id": ObjectId(bid)})
        # get data from batch doc
        
        part_name = batch["Part"]
        bsize = batch["Batch size"]
        collection_name = f"batch_{bid}_logs"
        size_of_col = len(list(mongo_obj.getCollection(collection_name).find()))
        redis_obj.set_json({"part_name": part_name})
        if size_of_col -1 ==bsize:
            redis_obj.set_json({"is_batch_full":True})
        if size_of_col < bsize:
            size_of_col = len(list(mongo_obj.getCollection(collection_name).find()))
            print(size_of_col)
            
            # temp = str("temp_" + station_type)
            recipie = LocalMongoHelper().getCollection("deployed_recipie").find_one()

            last_part = list(recipie.keys())[-2]
            # print(last_part)
            redis_obj.set_json({'last_part': last_part})
            if not current_state:
                collection = mongo_obj.getCollection(collection_name)
                recipie["_id"] = ObjectId()
                result = collection.insert_one(recipie)
                # print((result.inserted_id))
                redis_obj.set_json({"cid": str(result.inserted_id)})
            else:
                redis_obj.set_json({"cid": current_state['cid']})

            print(redis_obj.get_json("cid"))
            time.sleep(2)
            
            

            redis_obj.set_json({"service_status": True})
            print(redis_obj.get_json("result_status"))

            # if true, move to next inspection
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
            # upadte batch size
            
            # redis_obj.set_json({"is_running" : False})
            pass
        state_collection = mongo_obj.getCollection("batch_state")
        print(state_collection)
        state_collection.delete_one({"bid":redis_obj.get_json("bid")})
        # tells that all inspections done
        return "inspection started"

