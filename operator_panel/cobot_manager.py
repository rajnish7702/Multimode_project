import urx
import time
from common_utils import *
import pandas
import pprint
import random
from Business_logic import *


# uncomment set and get position cobot when actually connected to cobot
# class URX_Cobot:
#     def __init__(self, ip):
#         self.ip = ip
#         self.robot_controller = None
#         self.default_acc = 1
#         self.default_vel = 1

#         # self.connect()

#     def connect(self):
#         try:
#             self.robot_controller = urx.Robot(self.ip)
#         except Exception as e:
#             print("Error ->", str(e))
#             time.sleep(5)
#             self.connect()


    # def get_position(self):
    #     # data = self.robot_controller.getj(wait=True)
    #     # data1 = {'move_type':'j','a': self.default_acc,'v': self.default_vel}

    #     # for j in range(len(data)):
    #     #     data1['j'+str(j+1)] = data[j]
    #     # return data1
    #     pass

    # def set_position(self, pos, delay=1):
    #     # if pos['move_type'] == 'j':
    #     #     self.robot_controller.movej([pos['j1'], pos['j2'], pos['j3'], pos['j4'], pos['j5'], pos['j6']],self.default_acc,self.default_vel,wait=False)
    #     #     time.sleep(delay)
    #     #     while self.robot_controller.is_program_running():
    #     #         pass
    #     pass

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



class Doosan:
    def __init__(self,ip):
        self.robot = ModbusController()
        self.status = self.robot.connect(ip,mode='TCP')
        self.address = {}
        self.address['pos'] = 141
        self.address['exe'] = 142

    def get_pos(self):

        return self.robot.read_holding_register(self.address['pos']) or None

    
    def move_pos(self,pos):
        self.robot.write_holding_register(self.address['pos'],pos)
        self.robot.write_holding_register(self.address['exe'],1)
        while self.robot.read_holding_register(self.address['exe']) == 1:
            pass
        



# update cobot executor comments,and sse comments in infer
class CobotExecutor:
    redis_obj = CacheHelper()

    def __init__(
        self,
        ip,
        waypoints=[],
        transit={},
        coords={},
        waypoints_camera={},
        model=None,
        default_delay=2,
        model_match={},
        model_port={},
        cycle=None,
    ):
        """

        Description:
        Moves cobot to configured waypoints and gives trigger accordingly.

        Input:
        waypoints - List of dictionaries where each dictionary contains configuration of a waypoint

        """
        self.cycle = cycle
        self.model = model
        self.waypoints = waypoints
        self.coords = coords
        self.waypoints_camera = waypoints_camera
        self.isTransit_list = transit
        self.current_model = model_match
        self.model_port = model_port
        self.default_delay = default_delay
        self.cobot = Doosan(ip)
        self.home_waypoint = {}
        self.stack = []

    def check_cobot_trigger(self):
        """

        Description:
        Checks if cobot has been given the trigger to start inspection

        """
        while True:
            cobot_trigger = CobotExecutor.redis_obj.get_json("cobot_trigger")
            if cobot_trigger:
                print("Got cobot trigger")
                CobotExecutor.redis_obj.set_json({"cobot_trigger": False})
                inspection_id = CobotExecutor.redis_obj.get_json("inspection_id")
                if inspection_id is not None:
                    self.start_inspection()

    def set_home_waypoint(self):
        """

        Description:
        Extract and store the home waypoint for later use

        """
        if "P0" in self.coords.keys():
            self.home_waypoint = self.coords["P0"]
        else:
            self.home_waypoint = None

    def start_inspection(self):
        """

        Description:
        Moves cobot to configured positions and sends trigger for inspection

        """
        if self.home_waypoint == None:
            return "No Home found"

        redis_obj = CacheHelper()
        current_state = redis_obj.get_json("current_state")
        starting_point = ""
        if current_state and current_state["cycle"] == self.cycle:
            starting_point = self.waypoints.index(current_state["waypoint"])
        else:
            starting_point = 0

        cycle_start_time = time.perf_counter()
        for waypoint in self.waypoints[starting_point:]:
            if redis_obj.get_json("end_process"):
                current_state = {
                    "bid": redis_obj.get_json("bid"),
                    "cid": redis_obj.get_json("cid"),
                    "model": self.model,
                    "cycle": self.cycle,
                    "waypoint": waypoint,
                }
                print(current_state, "<- current state")
                redis_obj.set_json({"current_state": current_state})
                state_collection = LocalMongoHelper().getCollection("batch_state")
                print(redis_obj.get_json("bid"))
                updated_state = {"$set": current_state}
                arg = {"bid": str(redis_obj.get_json("bid"))}
                state_collection.update_one(arg, updated_state, upsert=True)
                print("here")
                break

            st = time.perf_counter()
            # print(waypoint)
            print("Next position ->", self.coords[waypoint])
            CobotExecutor.redis_obj.set_json(
                {"next_cobot_position": self.coords[waypoint]}
            )
            coord = self.coords[waypoint]
            # print(coord,waypoint,self.isTransit_list[waypoint])
            delay = self.default_delay
            self.cobot.move_pos(pos=coord)
            time.sleep(self.default_delay)
            self.stack.append(coord)
            print(self.isTransit_list, coord)
            if self.isTransit_list[waypoint] != True:
                CobotExecutor.redis_obj.set_json({"inspect": True})
                self.infer(waypoint)
            print("Waypoint iteration ->", str(time.perf_counter() - st))

        self.go_home()
        cycle_end_time = time.perf_counter()
        cycle_time = cycle_end_time - cycle_start_time
        CobotExecutor.redis_obj.set_json({"cobot_cycle_time": cycle_time})

    def infer(self, waypoint):
        """
        Description:
                Sorts line item to generate response and results and send sse stream
        """
        for model, port in self.model_port.items():
            name = str(waypoint) + str(model)
            redis_obj = CacheHelper()
            if name in self.waypoints_camera.keys():
                print(self.waypoints_camera[name], waypoint, model, port, self.cycle)
                # continue
                ports = port
                model = model
                part = str(redis_obj.get_json("part_name"))
                cycle = self.cycle
                waypoint = waypoint
                self.model = model

                camera = self.waypoints_camera[name]
                camera_list = list(cam.replace(" ", "") for cam in camera)
                # print(camera_list)
                # print(redis_obj.get_json("end_process"))
                if redis_obj.get_json("end_process"):
                    break

                # time.sleep(4)
                # continue
                if model == "MOCR":
                    continue
                    # camera list will always have 1 camera
                    url = "http://127.0.0.1:" + ports + "/detectocr"
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
                    url = "http://127.0.0.1:" + ports + "/detectbar"
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

                    # print(model)
                    current_model = model.replace(" ", "")
                    redis_obj.set_json({f"{current_model}_res": None})
                    redis_obj.set_json({f"{current_model}": None})
                    # ----------->>>> set features and defects in the redis here <<<<-------------------

                    # if business_done==0:
                    #     print("Accepted")
                    # else:
                    #     print("Rejected")
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

                # print(redis_obj.get_json(f"{model}_res"))
                # print(response_data)
                print(len(response_data), len(camera))
                # respomse_data = list(res)
                # print(response_data)

                # response = ["res1", "res2", "res3", "res4", "res5"]
                cid = redis_obj.get_json("cid")
                bid = redis_obj.get_json("bid")
                collection_name = f"batch_{bid}_logs"
                size_of_col = len(list(LocalMongoHelper().getCollection(collection_name).find()))


                data_bl = defaultdict(list) 
                for j, cam in enumerate(camera):
                    query = {
                        "_id": ObjectId(cid),
                        f"{part}": {
                            "$elemMatch": {
                                "model_number": model,
                                "camera_number": cam, 
                                "cycle_number": cycle,
                                "waypoint": waypoint,
                            }
                        },
                    }
                    projection = {
                        "_id": 0,
                        f"{part}.features_count_logic": 1,
                        f"{part}.defects_count_logic": 1,
                        f"{part}.camera_number": 1,
                        f"{part}.model_number": 1,
                        f"{part}.waypoint": 1,
                        f"{part}.cycle_number": 1,
                        f"{part}.transit_point":1,
                        f"{part}.weight_file_url":1,
                    }
                    doc = LocalMongoHelper().getCollection(collection_name).find_one(query,projection)
                    
                    # logger.debug(doc)
                    doc = doc[part]
                    
                    for re in doc:
                        if (
                            re["camera_number"] == cam
                            and re["model_number"] == model
                            and re["waypoint"] == waypoint
                            and re["cycle_number"] == cycle
                        ):
                            doc = re
                            break

                    Count_logic_features = doc["features_count_logic"]
                    Count_logic_defects = doc["defects_count_logic"]
                    data_for_bl= [Count_logic_features,Count_logic_defects,response_data[j],""]
                    data_bl[cam] = data_for_bl
                result_status = redis_obj.get_json("result_status")
                time.sleep(1)
                logger.info(result_status)

                result_data = business_logic_all(data_bl,current_model,result_status["Link"])
                logger.info(result_data)

                aggregate_waypoint_result = "Accepted"
                for j, cam in enumerate(camera):        
                    res = result_data[cam]["result"]
                    if res == "Rejected":
                        aggregate_waypoint_result = "Rejected"

                    result_data[cam]["feature_actual"] = data_bl[cam][0]
                    result_data[cam]["defects_actual"] = data_bl[cam][1]

                    filter = {"_id": ObjectId(cid)}
                    array_filters = [
                        {
                            "element.cycle_number": cycle,
                            "element.model_number": model,
                            "element.waypoint": waypoint,
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
                result_status = redis_obj.get_json("result_status")
                # logger.error(result_status)
                result_status[cycle][waypoint] = result_data
                result_status[cycle][waypoint]["waypoint_result"] = aggregate_waypoint_result
                if result_status[cycle]["cycle_result"] == "Accepted" and aggregate_waypoint_result == "Rejected":
                    result_status[cycle]["cycle_result"] = "Rejected"
                if result_status[cycle]["cycle_result"] == "Rejected":
                    result_status["overall_result"] = "Rejected"

                logger.success(result_status)
                redis_obj.set_json({"result_status":result_status})

                # result_status = json.dumps(result_status, cls=Encoder)
                
                filter= {"_id": ObjectId(cid)}
                update ={"$set": {
                    f"result": result_status,
                    "created_at": datetime.now()
                }}
                LocalMongoHelper().getCollection(collection_name).update_one(
                        filter, update, upsert=True
                    )
                rj_count = LocalMongoHelper().getCollection(collection_name).count_documents({"result.overall_result": "Rejected"})

                if (
                        self.cycle == redis_obj.get_json("total_cycle")
                        and waypoint == self.waypoints[-1]
                    ):
                    stream_data = {
                            "total_part": f"{redis_obj.get_json('last_part')}",
                            "current_part": f"{part}",
                            "status": result_status,
                            "current_waypoint" :f"{waypoint}",
                            "total_waypoint":f"{self.waypoints[-1]}",
                            "current_cycle": f"{self.cycle}",
                            "total_cycle": f"{redis_obj.get_json('total_cycle')}",
                            "is_completed": True,
                            "image": f"data:image/jpeg;base64,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",
                            "inspection_count": size_of_col,
                            "is_batch_full": False,
                            "ac_count": size_of_col,
                            "rj_count": rj_count,
                        }

                else:
                    stream_data = {
                            "total_part": f"{redis_obj.get_json('last_part')}",
                            "current_part": f"{part}",
                            "status": result_status,
                            "current_waypoint" :f"{waypoint}",
                            "total_waypoint":f"{self.waypoints[-1]}",
                            "current_cycle": f"{self.cycle}",
                            "total_cycle": f"{redis_obj.get_json('total_cycle')}",
                            "is_completed": f"{redis_obj.get_json('inspection_completed')}",
                            "image": f"data:image/jpeg;base64,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",
                            "inspection_count": size_of_col,
                            "is_batch_full": False,
                            "ac_count": size_of_col - rj_count,
                            "rj_count": rj_count,
                        }

                redis_obj.publish("current_stream", pickle.dumps(stream_data))
                redis_obj.set_json({"current_stats": dict(stream_data)})
                
                '''
                for j, cam in enumerate(camera):
                    # df = pandas.DataFrame(response['status'][j])
                    # data = pickle.dumps(df)
                    # print(data)

                    # call BL here
                    
                    # get features and defects from mongo here when proper recipie is made.

                    query = {
                        "_id": ObjectId(cid),
                        f"{part}": {
                            "$elemMatch": {
                                "model_number": model,
                                "camera_number": cam,  # Replace with the desired camera_number
                                "cycle_number": cycle,
                                "waypoint": waypoint,
                            }
                        },
                    }
                    projection = {
                        "_id": 0,
                        f"{part}.features_count_logic": 1,
                        f"{part}.defects_count_logic": 1,
                        f"{part}.camera_number": 1,
                        f"{part}.Usecase_number": 1,
                        f"{part}.waypoint": 1,
                        f"{part}.cycle_number": 1,
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
                        if (
                            re["camera_number"] == cam
                            and re["Usecase_number"] == model
                            and re["waypoint"] == waypoint
                            and re["cycle_number"] == cycle
                        ):
                            doc = re
                            break

                    Count_logic_features = doc["features_count_logic"]
                    Count_logic_defects = doc["defects_count_logic"]
                    # count_logic = {
                    #     "defects" : defects_count_logic,
                    #     "features" : features_count_logic,
                    # }
                    # redis_obj.set_json({"camera_count_logic": count_logic})
                    # redis_obj.set_json({"camera_response_data": response_data[j]})
                    # while True:
                    #     result_data = redis_obj.get_json("camera_result")
                    #     if result_data is None:
                    #         pass
                    #     else:
                    #         # result = result_data
                    #         if result_data == True:
                    #             result = "Accepted"
                    #         else:
                    #             result = "Rejected"
                    #         redis_obj.set_json({"camera_count_logic": None})
                    #         redis_obj.set_json({"camera_response_data": None})
                    #         redis_obj.set_json({"camera_result": None})
                    #         break
                    # print(response_data[j], type(response_data[j]))
                    # response_data[j] = response_data[j].to_dict('records')
                    result = business_logic(
                        response_data[j], features_count_logic, Count_logic_defects
                    )
                    print(result)
                    # result = "Accept"
                    result_temp = random.choice(["Accepted", "Rejected"])

                    # call sse here

                    # check for last value
                    # if (
                    #     self.cycle == redis_obj.get_json("total_cycle")
                    #     and waypoint == self.waypoints[-1]
                    # ):
                    #     stream_data = {
                    #         "cycle": f"{self.cycle}/{redis_obj.get_json('total_cycles')}",
                    #         "part": f"{part}/{redis_obj.get_json('last_part')}",
                    #         "waypoint": f"{waypoint}/{self.waypoints[-1]}",
                    #         "result": f"{result}",
                    #         "is_completed": True,
                    #     }

                    # else:
                    #     stream_data = {
                    #         "cycle": f"{self.cycle}/{redis_obj.get_json('total_cycles')}",
                    #         "part": f"{part}/{redis_obj.get_json('last_part')}",
                    #         "waypoint": f"{waypoint}/{self.waypoints[-1]}",
                    #         "result": f"{result}",
                    #         "is_completed": f"{redis_obj.get_json('inspection_completed')}",
                    #     }
                    # redis_obj.send_stream(stream_data)

                    # change the features and defects as features -> what we needed - what we got, meaning subtract the result data in bl and return and compare
                    if (
                        self.cycle == redis_obj.get_json("total_cycle")
                        and waypoint == self.waypoints[-1]
                    ):
                        stream_data = {
                            "total_part": {redis_obj.get_json("last_part")},
                            "current_part": f"{part}",
                            "waypoint_status": f"{result}",
                            "cycle_status": f"{result_temp}",
                            "overall_status": f"{result_temp}",
                            "current_waypoint" :f"{waypoint}",
                            "total_waypoint":f"{self.waypoints[-1]}",
                            "current_cycle": f"{self.cycle}",
                            "total_cycle": f"{redis_obj.get_json('total_cycle')}",
                            "is_completed": True,
                            "image": f"data:image/jpeg;base64,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",
                            "inspection_count": size_of_col,
                            "is_batch_full": False,
                            "ac_count": 0,
                            "rj_count": 0,
                            "features":Count_logic_features,
                            "defects":Count_logic_defects,
                        }

                    else:
                        stream_data = {
                            "total_part": {redis_obj.get_json("last_part")},
                            "current_part": f"{part}",
                            "waypoint_status": f"{result}",
                            "cycle_status": f"{result_temp}",
                            "overall_status": f"{result_temp}",
                            "current_waypoint" :f"{waypoint}",
                            "total_waypoint":f"{self.waypoints[-1]}",
                            "current_cycle": f"{self.cycle}",
                            "total_cycle": f"{redis_obj.get_json('total_cycle')}",
                            "is_completed": f"{redis_obj.get_json('inspection_completed')}",
                            "image": f"data:image/jpeg;base64,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",
                            "inspection_count": size_of_col,
                            "is_batch_full": False,
                            "ac_count": 0,
                            "rj_count": 0,
                        }

                    redis_obj.publish("current_stream", pickle.dumps(stream_data))
                    redis_obj.set_json({"current_stats": dict(stream_data)})



                    filter = {"_id": ObjectId(cid)}
                    array_filters = [
                        {
                            "element.cycle_number": cycle,
                            "element.Usecase_number": model,
                            "element.waypoint": waypoint,
                            "element.camera_number": cam,
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
                # return "success"
                '''
    def go_home(self):
        """

        Description:
        Sets cobot position to Home position

        """
        CobotExecutor.redis_obj.set_json({"next_cobot_position": "Home"})

        self.cobot.move_pos(self.home_waypoint)
        self.stack = []

    def emergency_reversal(self):
        """

        Description:
        Reverse traversal of all cobot positions if cobot stops midway

        """
        while len(self.stack) > 0:
            self.cobot.set_position(self.stack.pop())
