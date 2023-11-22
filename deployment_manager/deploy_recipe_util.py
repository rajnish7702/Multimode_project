import socket
import random
import docker
from time import perf_counter
from edgeplusv2_config.common_utils import LocalMongoHelper, user_domain
from bson import ObjectId
import os

# KEYS_TO_AVOID_RECIPIE = ["INFO", "_id", "recipie"]

# KEYS_TO_AVOID_RECIPIE = ["info" , "_id" , "recipie"]
KEYS_TO_AVOID_RECIPIE = ['_id',  'created_at', 'info', 'input_controller', 'output_controller', 'recipe_id', 'recipie']

def random_port_generator_util(n):
    # print("in rand0m+ports")
    port_list = []
    for _ in range(n):
        port_list.append(random.randint(1000, 4000))
    # print("random_port: ",port_list)
    return port_list


available_ports = []


def check_ports_util(n):
    # print('in check ports util')
    hostname = socket.gethostname()
    # print(hostname)
    ip = socket.gethostbyname(hostname)
    # ip="172.22.0.1"
    # print(ip)

    counter = 0

    port_list = random_port_generator_util(n)

    print(port_list)

    for port in port_list:
        # port=random.randint(a,b)

        try:
            # print("hello socket")
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # print("Hi bind")
            server.bind((ip, port))
            # print("Available port is {port}")
            available_ports.append(port)
            counter += 1
        # print(c)
        except:
            print(f"port number {port} is NOT available")
            # print(counter)
        server.close()
        if counter == n:
            # print("available_port",available_ports)
            return available_ports

        # elif index==len(port_list)-1:
    check_ports_util(counter - n)

    print(available_ports)
    return available_ports


# below Function is to check the type of the recipe - (static/cobot/conveyor).
def sanity_check_util(data):
    data_keys = data.keys()
    # print(data_keys)
    result = True
    # print("inside the sanity check.................")

    if data['info']["workstation_type"] == "static":
        # print("inside static loop")
        for part in data_keys:
            
            if part in KEYS_TO_AVOID_RECIPIE:
                continue
            else:
                # print(part,data[part])
                for part_document in range(len(data[part])):
                    # print( part_document, "...............",part_document)
                    if (
                        data[part][part_document]["cycle_number"] != "Cycle1"
                        or data[part][part_document]["waypoint"] != "P0"
                    ):
                        result = False

    elif data['info']["workstation_type"] == "conveyor":
        final_result = []
        for part in data_keys:
            plc_input_1 = False
            plc_output_1 = False

            if part in KEYS_TO_AVOID_RECIPIE:
                continue
            else:
                for part_document in range(len(data[part])):
                    # print(
                    #     len(data[part]),
                    #     part_document,
                    #     "ccccccccccccccccccccccccccccccccccc",
                    # )
                    if (
                        data[part][part_document]["PLC_INPUT"] != "None"
                        and data[part][part_document]["PLC_INPUT"] != ""
                    ):
                        plc_input_1 = True
                    if (
                        data[part][part_document]["PLC_OUTPUT"] != "None"
                        and data[part][part_document]["PLC_OUTPUT"] != ""
                    ):
                        plc_output_1 = True
                    if (
                        data[part][part_document]["Cycle_number"] != "Cycle 0"
                        or data[part][part_document]["Waypoint_number"] != "P0"
                    ):
                        final_result.append(False)
                        break

                if plc_output_1 == True and plc_input_1 == True:
                    final_result.append(True)
                else:
                    final_result.append(False)

        if False in final_result:
            result = False
        else:
            result = True

    elif data['info']["workstation_type"] == "cobot":
        result = False
        for part in data_keys:
            # print(part,1)
            if part in KEYS_TO_AVOID_RECIPIE:
                continue
            else:
                for part_document in range(len(data[part])):
                    # print(
                    #     data[part][part_document]["Cycle_number"],
                    #     data[part][part_document]["Waypoint_number"],
                    # )
                    if (
                        data[part][part_document]["Cycle_number"] == "Cycle1"
                        and data[part][part_document]["Waypoint_number"] == "2"
                    ):
                        result = True
                        return result

    return result


def delete_recipe_util(selected_recipe):
    is_Deleted = False
    print(selected_recipe)
    #mycoll = LocalMongoHelper().getCollection("offline_recipies")
    recipie_deleted_offline_recipie = LocalMongoHelper().getCollection("offline_recipies").delete_one({"_id": selected_recipe})
    recipie_deleted_offline_recipie_to_show = LocalMongoHelper().getCollection("offline_recipies_to_show").delete_one({"executable_recipe_id": selected_recipe})
    if not recipie_deleted_offline_recipie or not recipie_deleted_offline_recipie_to_show:
        return ("not deleted")
    else:
        print("deleted the recipes")
    return_value = collection_creation_util("deleted_recipie_from_Local")
    print(return_value)
    inserted_id = LocalMongoHelper().getCollection("deleted_recipie_from_Local").insert_one({"deleted_id":selected_recipe})
    if inserted_id:
        print("deleted recipie insertion done")
    #mycoll.deleteOne({"_id": ObjectId(selected_recipe)})
    flag = LocalMongoHelper().getCollection("offline_recipies").find_one({"_id": selected_recipe})
    print(flag)
    if not flag:
        is_Deleted = True
        return is_Deleted
    else:
        return is_Deleted


# collection creation utils
def collection_creation_util(name):
    data = {"test": "testing"}
    collection_name = name
    collection_checker_flag = LocalMongoHelper().collection_checker_util(
        collection_name
    )
    print("fromutils", collection_checker_flag)
    if not collection_checker_flag:
        # print("check this flag",collection_checker_flag)
        LocalMongoHelper().getCollection(collection_name).insert_one(data)
        LocalMongoHelper().getCollection(collection_name).delete_one(data)
        return True
    if collection_checker_flag:
        print("check this flag", collection_checker_flag)
        print("collection already exist")
        return False


def yolo_container_creation_util(model_list, docker_image_yolo, port_modified_list):
    from concurrent.futures import ThreadPoolExecutor
    import docker

    model_port_list = []
    model_list = [i.replace(" ", "") for i in model_list]
    current_path = os.getcwd()
    print(current_path)

    def run_docker_container(image_name, container_name, port):
        client = docker.from_env()
        container = client.containers.run(
            image_name,
            name=container_name,
            detach=True,
            tty=True,
            volumes={f"{current_path}/data_lake_in_container/":{"bind":"/app/data_lake/"}},
            shm_size="4G",
            network="edge_v2_test_network2",
            device_requests=[
                docker.types.DeviceRequest(device_ids=["0"], capabilities=[["gpu"]])
            ],
            restart_policy={"Name": "on-failure", "MaximumRetryCount": 5},
            environment={"port": port, "model_name": container_name},
        )
        # model_port_list.append(container_name +'-'+ str(container.id) +'-'+str(port['6789/tcp']))
        model_port_list.append(
            container_name + "-" + str(container.id) + "-" + str(port)
        )
        return container

    # print(model_port_list)
    docker_configurations = []
    for i in range(len(model_list)):
        docker_configurations.append(
            {
                "image_name": docker_image_yolo,
                "container_name": model_list[i],
                "port": port_modified_list[i],
            }
        )

    print(
        docker_configurations, "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    )
    max_threads = 4

    with ThreadPoolExecutor(max_threads) as executor:
        containers = executor.map(
            lambda config: run_docker_container(**config), docker_configurations
        )
    # print("1234",model_port_list)
    return model_port_list


def fetch_the_authorization_token_util():
    """
    Fetach the authroization token from loacl mongo 
    
    Arguments: None
    
    Response: Bearer """

    authorization_token_data= LocalMongoHelper().getCollection("user_cred_log").find_one({},{"access_token":1,"_id":0})
    print("authorization_token_data",authorization_token_data)
    if authorization_token_data:
        authorization_token=authorization_token_data["access_token"]
        print("authorization_token",authorization_token)
        return f"Bearer {authorization_token}"
    else:
        return False
