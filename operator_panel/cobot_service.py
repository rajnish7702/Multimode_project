# to control inspect flow
from cobot_manager import *
import json
from pprint import pprint
from common_utils import *

LINK = http_server_for_meta_data_util()
logger.success(LINK)

# from plc_module import Button


CacheHelper().set_json({"service_status": False})


def get_coords(cycle_data, waypoints):
    """
    Description:
            Maps waypoint with coordinates for cycle.
    """
    coords = {}
    temp = [4,1,4,2,3,2,3,4]
    for i,cycle in enumerate(cycle_data):
        co = {}
        coords[cycle["waypoint"]] = temp[i]
    # print(coords)
    return coords


def waypoint_camera(waypoint_list, data, cycle_name):
    """
    Description:
            Maps waypoint with list of cameras used based on model(keeps track of primary and secondary models)
    """
    waypoint_camera = {}
    d = {}
    logger.error(data)
    logger.error(cycle_name)

    for i in waypoint_list:
        d[i] = True
    for i in range(len(data)):
        if data[i]["cycle_number"] != cycle_name:
            break
        elif d.get(data[i]["waypoint"] + data[i]["model_number"], True):
            waypoint_camera.setdefault(
                data[i]["waypoint"] + data[i]["model_number"], []
            )
            waypoint_camera[
                data[i]["waypoint"] + data[i]["model_number"]
            ].append(data[i]["camera_number"])
    # pprint(waypoint_camera)
    return waypoint_camera


def create_transit(data, cycle_name):
    """
    Description:
            Maps waypoints with transit points.
    """
    waypoint_transit = {}
    data = [i for i in data if i["cycle_number"] == cycle_name]
    # pprint(data)
    for i in data:
        if i["transit_point"] == True:
            waypoint_transit[i["waypoint"]] = True
        if i["transit_point"] == False:
            waypoint_transit[i["waypoint"]] = False

    # pprint(waypoint_transit)
    return waypoint_transit


def auxilliary(data):
    """
    Description:
            Maps waypoints with model(keeps track of primary and secondary models)
    """
    model_match = {}

    for i in data:
        model_match[str(i["waypoint"] + str(i["camera_number"]))] = i[
            "model_number"
        ]

    return model_match


def model_to_port(data):
    """
    Description:
            Maps model with ports.
    """
    model_port = {}
    for i in data:
        # print(i)
        try:
            model_port[str(i["model_number"])] = i["Port Number"]
        except:
            model_port[str(i["model_number"])] = ""            

    return model_port


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
            CacheHelper().set_json({"callInspectionTrigger": True})
            # for trigger to know which cycle/part to execute
            CacheHelper().set_json({"plcId": button.ip})
            # turn on the camera
            # CacheHelper().set_json({"inspect":True})

        if input == 0 and input_flag:
            input_flag = False


def start_cobot():
    """
    Description:
            Service for cobot. Controls the cobot.
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
            part_name = redis_obj.get_json("part_name")
            current_inspection_id = redis_obj.get_json("cid")
            batch_id = redis_obj.get_json("bid")
            collection_name = f"batch_{batch_id}_logs"
            redis_obj.set_json({"inspection_completed": False})

            print(part_name)
            print(current_inspection_id)
            # isolate data for part

            results = (
                mongo_obj
                .getCollection(collection_name)
                .find_one({"_id": ObjectId(current_inspection_id)})
            )

            cobot_recipe = results[part_name]
            # print(cobot_recipe)
            # mapping cycle-waypoints
            if part_name != None:
                current_cycle = cobot_recipe[0]["cycle_number"]
                current_waypoint_list = []
                cycle_dict = {}
                for data in cobot_recipe:
                    if data["cycle_number"] != current_cycle:
                        current_waypoint_list = list(set(current_waypoint_list))
                        current_waypoint_list.sort(key=lambda x: int(x[1:]))
                        cycle_dict[current_cycle] = current_waypoint_list
                        current_cycle = data["cycle_number"]
                        current_waypoint_list = []

                    current_waypoint_list.append(data["waypoint"])
                current_waypoint_list = list(set(current_waypoint_list))
                current_waypoint_list.sort(key=lambda x: int(x[1:]))
                cycle_dict[current_cycle] = current_waypoint_list

                # print(cycle_dict)
                redis_obj.set_json({"total_cycles" : f"{list(cycle_dict)[-1]}"})
                current_state = redis_obj.get_json("current_state")
                print(current_state)
                # current_state={"cycle":"Cycle 2"}
                # isolating required cycles
                if current_state:
                    for  cy in cycle_dict.copy().keys():
                        if current_state['cycle'] == cy:
                            break
                        del cycle_dict[cy]
                print(cycle_dict)
                # continue
                for cy, way in cycle_dict.items():
                    end_process = redis_obj.get_json("end_process")
                    if end_process:
                        break
                    
                    cycle_data = [x for x in cobot_recipe if x["cycle_number"] == cy]
                    # pprint(cycle_data)

                    # mapping required data with waypoints to create cobot object(each object is denoting individual cycle)
                    coords = get_coords(cycle_data, way)
                    # print(coords)
                    current_model = list(
                        filter(lambda x: x.get("cycle_number") == cy, cobot_recipe)
                    )
                    transit_points = create_transit(cobot_recipe, cy)
                    waypoints_camera = waypoint_camera(way, cycle_data, cy)
                    model_match = auxilliary(cycle_data)
                    model_port = model_to_port(cycle_data)
                    if redis_obj.get_json("result_status") is None or not redis_obj.get_json("result_status") :
                        result_status = {"Link":LINK}
                        result_status["overall_result"] = "Accepted" 
                    else:
                        result_status = redis_obj.get_json("result_status")
                    result_status[cy] ={}
                    result_status[cy]["cycle_result"] = "Accepted"
                        # for w in way:
                            # result_status[cy][w]["waypoint_result"]=""
                    logger.error(result_status)
                    redis_obj.set_json({"result_status":result_status})


                    cobot_obj = CobotExecutor(
                        "192.168.1.5",
                        waypoints=way,
                        transit=transit_points,
                        coords=coords,
                        waypoints_camera=waypoints_camera,
                        model=current_model[0]["model_number"],
                        model_match=model_match,
                        model_port=model_port,
                        cycle=cy,
                    )
                    cobot_obj.set_home_waypoint()
                    cobot_obj.start_inspection()
                    # break
                    
                redis_obj.set_json({"result_status":{}})

                redis_obj.set_json({"inspection_completed": True})
                # redis_obj.publish("inspection_completed", "True")
                redis_obj.set_json({"current_state":None})
                

                redis_obj.set_json({"service_status": False})

            else:
                pass
    # pass


if __name__ == "__main__":
    start_cobot()
