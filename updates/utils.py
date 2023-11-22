from edgeplusv2_config.common_utils import (
    LocalMongoHelper,
    CloudMongoHelper,
    user_domain,
    data,
)
import json


def update_docker_image_name_in_config_json(docker_images_dict):
    """
    update the docker image in v2_config.json

    Arguments:
            {"DOCKER_IMAGE_BE": "ritikaniyengar/ep_backend_live:v15", "DOCKER_IMAGE_BE_HYBRID": "ritikaniyengar/cobot-conveyor:v13",
            "DOCKER_IMAGE_FE": "ritikaniyengar/edge_fe_live:v4", "DOCKER_FE_NAME": "frontend_v0",
            "DOCKER_IMAGE_FE_HYBRID": "ritikaniyengar/cobot_conveyor_fe:v2", "DOCKER_FE_HYBRID_NAME": "frontend_v1",
            "DOCKER_IMAGE_OCR": "ritikaniyengar/ocr_container:v3","DOCKER_IMAGE_BARCODE": "ritikaniyengar/barcode_container:v1"}

    Response:
            "successfully updated the docker image"

    """

    for i in docker_images_dict.keys():
        
        if i in data and docker_images_dict[i] != data[i]:
            file_path = "edgeplusv2_config/v2_config.json"

            # update the docker_image names
            data[i] = docker_images_dict[i]
          

            # rewrite the docker_image names
            with open(file_path, "w", encoding="utf-8") as json_file:
                json.dump(data, json_file)

    return "successfully updated the docker image"
