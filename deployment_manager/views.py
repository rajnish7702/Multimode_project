from flask import Blueprint, request, jsonify, redirect, url_for
import json
from bson.json_util import dumps
import docker
from flask import Flask, request, json, jsonify
from docker import errors
from edgeplusv2_config.common_utils import (
    CacheHelper,
    LocalMongoHelper,
    CloudMongoHelper,
    getting_id,
)
from deployment_manager.deploy_recipe_util import (
    delete_recipe_util,
    check_ports_util,
    sanity_check_util,
    collection_creation_util,
    yolo_container_creation_util,
    fetch_the_authorization_token_util
)
from bson import ObjectId
import edgeplusv2_config
import socket
import datetime
import subprocess
import requests
import time
from loguru import logger
KEYS_TO_AVOID_RECIPIE = ['_id',  'created_at', 'info', 'input_controller', 'output_controller', 'recipe_id', 'recipie']

views = Blueprint("views", __name__)


@views.route("/")
def hello_world():
    return "Hello, World! --- deployment_manager"


# app = Flask(__name__)
client = docker.from_env()
@views.route("/get_all_recipies", methods=["GET"])
def get_all_recipies_from_cloud():

    # check_offline_collection = LocalMongoHelper().collection_checker_util("offline_recipies")
    # check_offline_show_collection = LocalMongoHelper().collection_checker_util("offline_recipies_to_show")
    # if check_offline_collection and check_offline_show_collection:
    #     LocalMongoHelper().getCollection("offline_recipies").drop()
    #     LocalMongoHelper().getCollection("offline_recipies_to_show").drop()
    offline_recipies_collection = LocalMongoHelper().getCollection("offline_recipies")
    offline_recipies_collection_to_show = LocalMongoHelper().getCollection("offline_recipies_to_show")
    deleted_recipie_local = LocalMongoHelper().getCollection("deleted_recipie_from_Local")

    collection_creation_util("offline_recipies_to_show")
    collection_creation_util("offline_recipies")

    workstation_id = getting_id()
    print(workstation_id)
    # tbd -> don't use cloudmongo directly, instead use apigateway for this.
    workstation_collection = CloudMongoHelper().getCollection("workstations")
    current_workstation_type = workstation_collection.find_one(
        {"_id": ObjectId(workstation_id)}
    ).get("workstation_type")
    CacheHelper().set_json({"workstation_type": current_workstation_type})
    print(current_workstation_type)
    # authorization_token= [ i for i in LocalMongoHelper().getCollection("lincodeuser_cred_log").find({})]
    
    # authorization_token = "Bearer NBli1k9pNMaq1nht7kNtJJ45G1Vftf"
    authorization_token=fetch_the_authorization_token_util()
    # print(authorization_token,'<<<<<------')
    url = "https://v2.livis.ai/api/livis/v2/recipe_builder/get_published_recipe_for_workstation/"+ str(workstation_id)
    # print(url)
    payload_show = json.dumps(
        {
            "collection": "lincoderecipe_collection",
            "document": [{}, {}],
        }
    )
    headers = {"Content-Type": "application/json","Authorization":authorization_token}
    response = requests.request("GET", url, headers=headers, data=payload_show)
    response_from_cloud = response.json()
    
    published_recipies = response_from_cloud["data"]['published_recipes']
    executable_recipies = response_from_cloud["data"]['executable_recipes']
    # print(published_recipies,'\n', executable_recipies)
    
    present_recipies = [
        i["_id"] for i in offline_recipies_collection.find({}, {"_id": 1})
    ]
    present_recipies_show = [
        i["_id"] for i in offline_recipies_collection_to_show.find({}, {"_id": 1})
    ]
    # print(present_recipies,present_recipies_show)
    recipies_to_be_inserted_in_show = []
    recipies_to_be_inserted = []
    recipies_present_in_show_collection = [i for i in offline_recipies_collection_to_show.find({})]

    for item in range(len(published_recipies)):
        # print(published_recipies[item]['_id'])
        id_from_cloud_published = published_recipies[item]['_id']
        if id_from_cloud_published not in present_recipies_show:
            recipies_to_be_inserted_in_show.append(published_recipies[item])
    
    for item in range(len(executable_recipies)):
        # print(executable_recipies[item]['_id'])
        id_from_cloud_executable = executable_recipies[item]['_id']
        if id_from_cloud_executable not in present_recipies:
            recipies_to_be_inserted.append(executable_recipies[item])
    
    # print(recipies_to_be_inserted,'\n','Up is executable<<<<-------->>>>below is show',recipies_to_be_inserted_in_show)
    ################## finding camera detials:

    headers = {"Content-Type": "application/json"}
    id_anchor_json = getting_id()
    payload = json.dumps(
        {
            "collection": "workstations",
            "document": [{"_id": id_anchor_json}, {"_id": 0}],
        }
    )

    api_gateway_mongoDB_url = "http://localhost:5000/api_gateway/get_one_documents"

    # Access the MongoDB through api_gateway to get the inspection station details
    workstation_list_json = requests.request(
        "POST", api_gateway_mongoDB_url, headers=headers, data=payload
    )

    user_collection = (
        LocalMongoHelper()
        .getCollection("workstations")
        .find_one({"_id": ObjectId(id_anchor_json)})
    )


    if user_collection is None:
        status = workstation_list_json.json().get("status")
        data = status
        insert_dict = {}
        for key in data:
            insert_dict[key] = data[key]
        insert_dict["_id"] = ObjectId(id_anchor_json)
        LocalMongoHelper().getCollection("workstations").insert_one(insert_dict)

    inspection_list = workstation_list_json.json()
    camera_details_list = inspection_list['status']['camera']
    # print(camera_details_list,'camera details')
    if len(recipies_to_be_inserted) >0 and len(recipies_to_be_inserted_in_show)>0:
        LocalMongoHelper().getCollection("offline_recipies").insert_many(recipies_to_be_inserted)
    
        LocalMongoHelper().getCollection("offline_recipies_to_show").insert_many(recipies_to_be_inserted_in_show)
        get_operator_layout_info()
        return {"message": 110, "data":{ "recipe":recipies_to_be_inserted_in_show,"camera_details":camera_details_list  } }
    else:
        return {"message": 110, "data":{"recipe":recipies_present_in_show_collection,"camera_details":camera_details_list }  }

@views.route("/get_operator_layout_info", methods=["GET"])
def get_operator_layout_info():
    operator_panel_info = [i for i in  LocalMongoHelper().getCollection("offline_recipies_to_show").find({})]
    print(operator_panel_info)
    operator_panel_id = operator_panel_info[0]["operator_layout_id"]
    print(operator_panel_id)
    url = "https://v2.livis.ai/api/livis/v2/operator_builder_panel/get_operator_layout_detail/" + str(operator_panel_id)

    payload_show = json.dumps(
        {
            "collection": "lincoderecipe_collection",
            "document": [{}, {}],
        }
    )
    authorization_token=fetch_the_authorization_token_util()
    headers = {"Content-Type": "application/json","Authorization":authorization_token}
    response = requests.request("GET", url, headers=headers, data=payload_show)
    response_from_cloud = response.json()
    operator_layout_info = response_from_cloud
    
    collection_creation_util("operator_layout_info")
    insertion = LocalMongoHelper().getCollection('operator_layout_info').insert_one(operator_layout_info)
    if insertion:
        return {"message": 110, "data": operator_panel_info}
    else:
        return {"message": 111, "data": "operator layout information not uploaded to mongodb"}


@views.route("/deploy_recipie", methods=["POST"])
def deploy_recipe():
    """
    API functionality - This api will create/check a collection deployed_recipie and update that with selected recipie and
    after finding the unique numbers of containers for Model/Camera it will create that much containers.

    PAyload : recipie1 # change payload in dictionary
    Response: "Containers created successfully".
    """
    # Collection creation starts here:-
    # if we are tryinh to deploy the recipie after stopping it, check the recipie id coming and in 
    # deployed recipie if equal instead of deploying just restart the recipie
    # collection_checking = LocalMongoHelper().collection_checker_util()
    collection_created = collection_creation_util("deployed_recipie")
    offline_recipies_collection = LocalMongoHelper().getCollection("offline_recipies")
    offline_recipies_collection_to_show = LocalMongoHelper().getCollection("offline_recipies_to_show")
    deployed_recipie_collection = LocalMongoHelper().getCollection("deployed_recipie")
    if collection_created:
        print("collection_created")
    check_collection = [
        i for i in deployed_recipie_collection.find()
    ]
    # print(check_collection,'<<<<----')
    recipie_number = json.loads(request.data)
    recipie_id_from_payload = recipie_number["id"]
    recipie_id = [i for i in offline_recipies_collection_to_show.find({"executable_recipe_id": recipie_id_from_payload})]
    print(recipie_id)
    recipie_id = recipie_id[0]["executable_recipe_id"]
    print("New recipie executable",recipie_id)
    # if len(check_collection) != 0:
        

    # Checking the deployed collection , if there is already one recipie inside collection or not:-
    if len(check_collection) == 0:
        # print("Inside the second if block")
        # fetching  the recipie from offline recipie collection.

        list_recipie_data = [
            i for i in offline_recipies_collection.find({"_id": recipie_id})
        ]

        # print(list_recipie_data)
        if len(list_recipie_data) == 0:
            return {"message": 111, "data": " Recipies Fetching failed"}
        else:
            json_data = list_recipie_data[0]

        containers_list = []
        parts_list = []
        camera_list = []

        # sanity check:
        # sanity_result = sanity_check_util(json_data)
        # print("sanity check result", sanity_result)

        for part_count in json_data.keys():
            if part_count in parts_list:
                print("recipe is not acceptable")
            else:
                parts_list.append(part_count)
        print("part list", parts_list)

        # fetching the different model.
        for parts in parts_list:
            print(parts)
            if parts in KEYS_TO_AVOID_RECIPIE:
                continue

            else:
                for items in json_data[parts]:
                    # print(items, ".............")
                    if items["model_number"] not in containers_list:
                        containers_list.append(items["model_number"])
                    if (
                        items["camera_number"] not in camera_list
                        and items["camera_number"] != "NONE"
                    ):
                        camera_list.append(items["camera_number"])
                    else:
                        continue

        model_list, ocr_br_list = [], []
        for model in containers_list:
            if model == "MOCR" or model == "MBAR":
                ocr_br_list.append(model)
            else:
                model_list.append(model)
        logger.error(model_list)
        if None in model_list:
            model_list.remove(None)

        logger.error(model_list)

        # creation of random ports and checking the availablity.
        port_list = check_ports_util(len(containers_list))
        port_modified_list = []
        for i in port_list:
            port_modified_list.append({"6789/tcp": i})

        f = open("edgeplusv2_config/v2_config.json")
        data_from_webapp = json.load(f)
        f.close()

        # camera containers creation.
        if None in camera_list:
            camera_list.remove(None)
        print(camera_list,'camera findings')
        camera_list_modified = [i.replace(" ", "") for i in camera_list]
        ################## finding camera detials:

        headers = {"Content-Type": "application/json"}
        id_anchor_json = getting_id()
        payload = json.dumps(
            {
                "collection": "workstations",
                "document": [{"_id": id_anchor_json}, {"_id": 0}],
            }
        )

        api_gateway_mongoDB_url = "http://localhost:5000/api_gateway/get_one_documents"

        # Access the MongoDB through api_gateway to get the inspection station details
        workstation_list_json = requests.request(
            "POST", api_gateway_mongoDB_url, headers=headers, data=payload
        )

        user_collection = (
            LocalMongoHelper()
            .getCollection("workstations")
            .find_one({"_id": ObjectId(id_anchor_json)})
        )


        if user_collection is None:
            status = workstation_list_json.json().get("status")
            data = status
            insert_dict = {}
            for key in data:
                insert_dict[key] = data[key]
            insert_dict["_id"] = ObjectId(id_anchor_json)
            LocalMongoHelper().getCollection("workstations").insert_one(insert_dict)

        inspection_list = workstation_list_json.json()
        camera_details_list = inspection_list['status']['camera']
        camera_type_list = [cam_type["camera_type"] for cam_type in camera_details_list]
        print(camera_type_list,'this is to be checked')
        for camera_type in camera_type_list:
            if camera_type == "usb":
                print("running USB script")
                command = ["python3", "deployment_manager/USB_script.py", "--arg1", "cam", "--arg2", "0"]
                # subprocess.Popen(["python3", "deployment_manager/USB_script.py"])
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
        camera_container_details = []
        for cam in camera_list_modified:
            camera_image = data_from_webapp["CAMERA_IMAGE"]
            camera_name = cam
            try:
                # Check the camera conatiner availability
                cam_container = client.containers.get(camera_name)

                # It will restart the camera_conatiner
                cam_container.restart()
                cam_container_id = client.containers.get(str(cam_container))
                camera_container_details.append(cam_container_id.id)
                container_deployed = True

            # If container not found then new container should create
            except errors.NotFound:
                client.containers.run(
                    camera_image,
                    name=str(camera_name),
                    environment={
                        "topic_name": str(cam),
                        "path": "videos/traffic.mp4",
                    },
                    detach=True,
                    tty=True,
                    shm_size="4G",
                    network="edge_v2_test_network2",
                    restart_policy={"Name": "on-failure", "MaximumRetryCount": 5},
                    command="python3 adapter.py",
                )
                cam_container_id = client.containers.get(str(camera_name))
                camera_container_details.append(cam_container_id.id)

        docker_image_yolo = data_from_webapp["DOCKER_IMAGE_YOLO"]
        model_port_list = yolo_container_creation_util(
            model_list, docker_image_yolo, port_list[: len(model_list)]
        )
        ocr_br_port_list = port_modified_list[len(model_list) :]
        container_details = []
        for i, container_to_create in enumerate(ocr_br_list):
            if container_to_create == "MOCR":
                docker_image_ocr = data_from_webapp["DOCKER_IMAGE_L_OCR"]
                ocr_container_name = "ep_ocr"
                container_deployed = False

                try:
                    # Check the ep_ocr conatiner availability
                    ocr_container = client.containers.get(ocr_container_name)
                    ocr_container_id = client.containers.get(str(ocr_container_name))

                    # It will restart the ocr_conatiner(ep_ocr)
                    ocr_container.restart()
                    container_deployed = True

                # If container not found then new container should create
                except errors.NotFound:
                    client.containers.run(
                        docker_image_ocr,
                        name=ocr_container_name,
                        detach=True,
                        tty=True,
                        device_requests=[
                            docker.types.DeviceRequest(
                                device_ids=["0"], capabilities=[["gpu"]]
                            )
                        ],
                        shm_size="4G",
                        network="edge_v2_test_network2",
                        restart_policy={"Name": "on-failure", "MaximumRetryCount": 5},
                        environment={"port": ocr_br_port_list[i]},
                    )
                    ocr_container_id = client.containers.get(str(ocr_container_name))
                    container_deployed = True

                finally:
                    if container_deployed:
                        port = [i for i in port_modified_list[i].keys()]
                        container_details.append(
                            (
                                "MOCR"
                                + "-"
                                + ocr_container_id.id
                                + "-"
                                + str(ocr_br_port_list[i][port[0]])
                            )
                        )
                        continue
                    else:
                        container_details.append("contianer with ocr not deployed")
                        continue

            elif container_to_create == "MBAR":
                docker_image_barcode = data_from_webapp["DOCKER_IMAGE_L_OCR"]
                barcode_container_name = "ep_barcode"
                container_deployed = False

                try:
                    # Check the ep_barcode conatiner availability
                    barcode_container = client.containers.get(barcode_container_name)

                    # It will restart the barcode_conatiner(ep_barcode)
                    barcode_container.start()
                    barcode_container_id = client.containers.get(
                        str(barcode_container_name)
                    )
                    container_deployed = True

                # If container not found then new container should create
                except errors.NotFound:
                    client.containers.run(
                        docker_image_barcode,
                        name=barcode_container_name,
                        detach=True,
                        tty=True,
                        device_requests=[
                            docker.types.DeviceRequest(
                                device_ids=["0"], capabilities=[["gpu"]]
                            )
                        ],
                        shm_size="4G",
                        network="edge_v2_test_network2",
                        restart_policy={"Name": "on-failure", "MaximumRetryCount": 5},
                        environment={"port": ocr_br_port_list[i]},
                    )

                    container_deployed = True
                    barcode_container_id = client.containers.get(
                        str(barcode_container_name)
                    )
                finally:
                    if container_deployed:
                        port = [i for i in port_modified_list[i].keys()]
                        container_details.append(
                            (
                                "MBAR"
                                + "-"
                                + barcode_container_id.id
                                + "-"
                                + str(ocr_br_port_list[i][port[0]])
                            )
                        )
                        continue
                    else:
                        # return False
                        container_details.append("contianer with barcode not deployed ")
                        continue

            else:
                # Code for Anomaly
                pass
        complete_container_details = {}
        count = 1

        for i in camera_container_details:
            complete_container_details.update({"camera_container" + str(count): i})
            count += 1

        # port updation changes here --->>>
        final_container_details_for_port_updation = container_details + model_port_list
        list_recipie_data = [
            i for i in offline_recipies_collection.find({"_id": recipie_id}, {})
        ]
        new_json_data = list_recipie_data[0]
        # new_json_data = json.loads(request.data)
        counter = 1

        # for starting service.py file
        print("--->>>>running the service.py files")
        if new_json_data["info"]["workstation_type"] == "cobot":
            file = subprocess.Popen(["python3", "operator_panel/cobot_service.py"])
            # subprocess.Popen(["python3", "BUsiness_logic.py"])
            # os.system('python3 operator_panel/cobot_service.py')
            # subprocess.call(["python3", "operator_panel/cobot_service.py"
        elif new_json_data["info"]["workstation_type"] == "static":
            file = subprocess.Popen(["python3", "operator_panel/static_service.py"])
            # subprocess.Popen(["python3", "BUsiness_logic.py"])
        elif new_json_data["info"]["workstation_type"] == "conveyor":
            file = subprocess.Popen(["python3", "operator_panel/conveyor_service.py"])
            # subprocess.Popen(["python3", "BUsiness_logic.py"])
        else:
            print("No header or wrong header description")
            return {"message": 117, "data": []}

        # container_deatils list above contains model container details.
        for i in final_container_details_for_port_updation:
            # print(i)
            model_with_id_port = i.split("-")
            # print(model_with_id_port)
            if len(model_with_id_port) >= 2:
                complete_container_details.update(
                    {"model_container" + str(counter): model_with_id_port[1]}
                )
            else:
                print("Invalid format for container:", i)
            counter += 1
            # print(parts_list)
            for parts in parts_list:
                if parts in KEYS_TO_AVOID_RECIPIE:
                    # val_dic = parts_list["info"]

                    continue
                for items in new_json_data[parts]:
                    if (
                        items["model_number"] == "MOCR"
                        and model_with_id_port[0] == "MOCR"
                    ):
                        port_dictionary = {"Port Number": model_with_id_port[-1]}
                        items.update(port_dictionary)

                    elif (
                        items["model_number"] == "MBAR"
                        and model_with_id_port[0] == "MBAR"
                    ):
                        port_dictionary = {"Port Number": model_with_id_port[-1]}
                        items.update(port_dictionary)

                    elif (
                        items["model_number"] in model_list
                        and model_with_id_port[0][0] + " " + model_with_id_port[0][1]
                        == items["model_number"]
                    ):
                        port_dictionary = {"Port Number": model_with_id_port[-1]}
                        items.update(port_dictionary)

        # print("complete- cont - details - dic", complete_container_details)
        # print("this is the new json format recipie updated with ports", new_json_data)
        collection_creation_util("container_id_collection")
        deployment = (
            LocalMongoHelper()
            .getCollection("deployed_recipie")
            .insert_one(new_json_data)
        )
        complete_container_details.update({"_id": deployment.inserted_id})
        recipie_deployed_previously = (
            LocalMongoHelper()
            .getCollection("container_id_collection")
            .find_one({"_id": deployment.inserted_id})
        )
        print(recipie_deployed_previously, "<<<<--------")
        if recipie_deployed_previously:
            print("recipie deployed previously hence restating the containers")

        LocalMongoHelper().getCollection("container_id_collection").insert_one(
            complete_container_details
        )
        # print(recipie_id,type(recipie_id),"recipie_id checking")
        deployment_show = (
                        offline_recipies_collection_to_show
                        .find_one({"executable_recipe_id": recipie_id})
                    ) 
        print(deployment_show)
        deployment_show["is_deployed"] = True
        deployment_show["last_deployed"] = datetime.datetime.now()
        # print(deployment_show)
        LocalMongoHelper().getCollection("offline_recipies_to_show").update_one(
            {"executable_recipe_id": recipie_id}, {"$set": deployment_show}, upsert=False
        )

        return {"message": 112, "data": " Choosen Recipie successfully deployed "}

    else:
        
        # Note --->>>if there is one previous recipe running than this part will execute.
        print("Inside the else  block")
        previously_deployed_id = [i for i in deployed_recipie_collection.find({},{"_id":1})]
        previously_deployed_id = previously_deployed_id[0]["_id"]
        print('check me',previously_deployed_id)
        print('you have to check this',recipie_id,previously_deployed_id,type(previously_deployed_id),type(recipie_id))
        all_running_containers = client.containers.list()
        previous_running_containers = client.containers.list(all=True)

        # if recipie_id == previously_deployed_id:
            # all_running_containers = client.containers.list()
            # previous_running_containers = client.containers.list(all=True)
        if recipie_id == previously_deployed_id:
            # all_running_containers = client.containers.list()
            # previous_running_containers = client.containers.list(all=True)
            try:
                # print(all_running_containers,previous_running_containers)
                for prev_running in previous_running_containers:
                    prev_running.restart()
                    # all_running_containers = client.containers.list()
                    deployment_show = (
                        offline_recipies_collection_to_show
                        .find_one({"executable_recipe_id": recipie_id})
                    ) 
                    
                    deployment_show["is_deployed"] = True
                    deployment_show["last_deployed"] = datetime.datetime.now()
                    # print(deployment_show)
                    LocalMongoHelper().getCollection("offline_recipies_to_show").update_one(
                        {"executable_recipe_id": recipie_id}, {"$set": deployment_show}, upsert=False
                    )


                return {"message": 113,
            "data": " Choosen Recipie successfully deployed after removing the previous one",}
            except:
                return {"message": 119, "data": " Recipie Incorrect "}
            
        if recipie_id != previously_deployed_id:
            deployment_show = (
                        offline_recipies_collection_to_show
                        .find_one({"executable_recipe_id": recipie_id})
                    ) 
            deployment_show["is_deployed"] = False
            deployment_show["last_deployed"] = datetime.datetime.now()
            # print(deployment_show)
            LocalMongoHelper().getCollection("offline_recipies_to_show").update_one(
                {"executable_recipe_id": recipie_id}, {"$set": deployment_show}, upsert=False
            )

            current_containers_list = [
                i
                for i in LocalMongoHelper()
                .getCollection("container_id_collection")
                .find({}, {"_id": 0})
            ]

            # below function stops the container.
            Running_containers = client.containers.list(all = True)
            print("In else if recipie is changed started to stop the containers",'\n',Running_containers,'\n',current_containers_list)
            
            for container in Running_containers:
                if container.id in current_containers_list[0].values():
                    print(container.id)
                    time.sleep(2)
                    container.stop()
                    container.remove()

            previous_recipie_id = (
                LocalMongoHelper()
                .getCollection("deployed_recipie")
                .find_one({}, {"_id": 1})
            )
            # print(previous_recipie_id,type(previous_recipie_id),'check meeee')
            previous_recipie_id = previous_recipie_id["_id"]
            
            deployment_show = (
                        offline_recipies_collection_to_show
                        .find_one({"executable_recipe_id": previous_recipie_id})
                    ) 
            deployment_show["is_deployed"] = False
            deployment_show["last_deployed"] = datetime.datetime.now()
            # print(deployment_show)
            LocalMongoHelper().getCollection("offline_recipies_to_show").update_one(
                {"executable_recipe_id": previous_recipie_id}, {"$set": deployment_show}, upsert=False
            )
            LocalMongoHelper().getCollection("deployed_recipie").drop()
            # LocalMongoHelper().getCollection("deployed_recipie").delete_one({"_id":ObjectId(previous_recipie_id)})
            LocalMongoHelper().getCollection("container_id_collection").drop()
            deploy_recipe()

            # print(current_recipie_list)
            return {
                "message": 113,
                "data": " Choosen Recipie successfully deployed after removing the previous one",
            }


@views.route("/stop_recipie", methods=["GET"])
def stop_recipe():
    offline_recipies_collection = LocalMongoHelper().getCollection("offline_recipies")
    offline_recipies_collection_to_show = LocalMongoHelper().getCollection("offline_recipies_to_show")
    deployed_recipie_collection = LocalMongoHelper().getCollection("deployed_recipie")
    """Api endpoint to stop all the runnning containers
    Response : {"Container Status": "Container successfully stopped"}
    """
    deployed_recipe_id = (
        LocalMongoHelper().getCollection("deployed_recipie").distinct("_id", {})
    )
    deployed_recipe_id = deployed_recipe_id[0]
    print(deployed_recipe_id)
    containers_id_coll = LocalMongoHelper().getCollection("container_id_collection")
    current_containers_list = [
        i for i in containers_id_coll.find({"_id": deployed_recipe_id})
    ]

    for container in client.containers.list():
        if container.id in current_containers_list[0].values():
            container.stop()
            # container.remove()
    deployment_show = (
                        offline_recipies_collection_to_show
                        .find_one({"executable_recipe_id": deployed_recipe_id})
                    ) 
    # print(deployment_show)
    deployment_show["is_deployed"] = False
    # deployment_show["last_deployed"] = datetime.datetime.now()
    # print(deployment_show)
    offline_recipies_collection_to_show.update_one(
        {"executable_recipe_id": deployed_recipe_id}, {"$set": deployment_show}, upsert=False
    )

    return {"message": 114, "data": " Choosen Recipie successfully stopped "}


@views.route("/restart_recipie", methods=["GET"])
def restart_recipe():
    offline_recipies_collection = LocalMongoHelper().getCollection("offline_recipies")
    offline_recipies_collection_to_show = LocalMongoHelper().getCollection("offline_recipies_to_show")
    deployed_recipie_collection = LocalMongoHelper().getCollection("deployed_recipie")
    """
    API functionality - If user has selected the same to recipe and hit restart again, in that case this api will run all the containers which are present.

    Rsponse:({"message":200,"data":" All the neccassary containers restarted "})

    """
    all_running_containers = client.containers.list()
    previous_running_containers = client.containers.list(all=True)
    try:
        # print(all_running_containers,previous_running_containers)
        for prev_running in previous_running_containers:
            prev_running.restart()
        previous_recipie_id = (
            LocalMongoHelper()
            .getCollection("deployed_recipie")
            .find_one({}, {"_id": 1})
        )
        previous_recipie_id = previous_recipie_id["_id"]
        print("in the restart",previous_recipie_id)
        all_running_containers = client.containers.list()
        deployment_show = (
                        offline_recipies_collection_to_show
                        .find_one({"executable_recipe_id": previous_recipie_id})
                    ) 
        deployment_show["is_deployed"] = True
        deployment_show["last_deployed"] = datetime.datetime.now()
        # print(deployment_show)
        LocalMongoHelper().getCollection("offline_recipies_to_show").update_one(
            {"executable_recipe_id": previous_recipie_id}, {"$set": deployment_show}, upsert=False
        )
        return {"message": 115, "data": " All the neccassary containers restarted "}
    except:
        return {"message": 400, "data": " Can't restart the container "}


@views.route("/delete_recipie", methods=["POST"])
def delete_recipe():
    offline_recipies_collection = LocalMongoHelper().getCollection("offline_recipies")
    offline_recipies_collection_to_show = LocalMongoHelper().getCollection("offline_recipies_to_show")
    deployed_recipie_collection = LocalMongoHelper().getCollection("deployed_recipie")
    """Api functionality - this is to delete the recipie selected by the user.
        Payload - {
            1
            }
    respone : ({"message":200,"data": " Deletion of the recipie succesfull "})
    """
    recipie_number = json.loads(request.data)

    recipie_id = recipie_number["id"]

    list_recipie_data = (
        offline_recipies_collection
        .find_one({"_id": recipie_id})
    )

    # if len(list_recipie_data) == 0:
    if list_recipie_data == None:
        return {"message": 111, "data": "Recipie not found in the local"}
    else:
        json_data = list_recipie_data
    print(json_data)

    selected_recipe_id = json_data["_id"]
    print(selected_recipe_id)
    if delete_recipe_util(selected_recipe_id):
        # print(delete_recipe_util(selected_recipe_id))
        return {"message": 116, "data": " Deletion of the recipie succesfull "}
    else:
        return {"message": 117, "data": " Deletion of the recipie unsuccesfull "}


@views.route("/get_recipie_info/<recipie_id>", methods=["GET"])
def get_recipie_info(recipie_id):
    offline_recipies_collection = LocalMongoHelper().getCollection("offline_recipies")
    offline_recipies_collection_to_show = LocalMongoHelper().getCollection("offline_recipies_to_show")
    deployed_recipie_collection = LocalMongoHelper().getCollection("deployed_recipie")
    """
    Description: This API will give info about the offline recipies.

    Args:
    - recipie_id: ObjectId of the recipe (passed in the URL)

    """
    # print(recipie_id,type(recipie_id))
    # recipie_id = ObjectId(recipie_id)
    # print(recipie_id,type(recipie_id))
    # Assuming LocalMongoHelper() is a valid class to fetch data from MongoDB
    # list_recipe_data = [i for i in LocalMongoHelper().getCollection("offline_recipies").find({"_id": str(ObjectId(recipie_id))}, {})]
    print(recipie_id,">")
    list_recipie_data = [
        i
        for i in offline_recipies_collection_to_show
        .find({"_id": (recipie_id)}, {})
    ]

    # print(list_recipie_data)

    if len(list_recipie_data) == 0:
        return {"message": 111, "data": []}
    else:
        json_data = list_recipie_data[0]

    return {"message": 118, "data": json_data}
