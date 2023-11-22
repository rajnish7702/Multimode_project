import json
# session[‘keyword’] = “foo” can be used to store anything into sessions.
# Stored values can be retrieved using bar = session.get(‘keyword’)
from flask import Blueprint, request, jsonify, redirect, url_for , Response, session



def get_anchor_details():
    anchor_file_path = "edgeplusv2_config/anchor.json"
    with open(anchor_file_path, "r") as f:
        anchor_data = json.load(f)
    
    anchor_inspection_station_name = anchor_data["INFO"][0]["inspection_station_name"]
    anchor_inspection_station_type = anchor_data["INFO"][0]["inspection_station_type"]

    return anchor_inspection_station_name, anchor_inspection_station_type

def get_inspection_station_details():
    recipe_file_path = "edgeplusv2_config/static_recipe.json"
    with open(recipe_file_path, "r") as f:
        recipe_data = json.load(f)
    
    recipe_inspection_station_name = recipe_data["INFO"][0]["inspection_station_name"]
    recipe_inspection_station_type = recipe_data["INFO"][0]["inspection_station_type"]
    return recipe_inspection_station_name , recipe_inspection_station_type


# send unique part list

def get_unique_part_list():
    recipe_file_path = "edgeplusv2_config/static_recipe.json"
    with open(recipe_file_path, "r") as f:
        recipe_data = json.load(f)
    
    unique_parts = set()

    for key in recipe_data.keys():
        if key.strip():
            unique_parts.add(key)
    
    unique_parts.remove("INFO")
    unique_parts.remove("Part Name")

    return list(unique_parts), recipe_data

# static flow
# group all the similar part (get uniq part list) 
# and get the ask user to select the part (select part api)


def set_global_part(data): 
    if data["selected_part"] in get_unique_part_list()[0]:   
        # global SELECTED_PART 
        # SELECTED_PART = data["selected_part"]
        session['SELECTED_PART'] = data["selected_part"]
        return data["selected_part"]
    else:
        return data["selected_part"] + "  Mentioned part not in recipe.. !!!!!!!"


# recipe verification for the selected part

def recipe_verification_for_static_inspection_station(selected_part):

    if selected_part in get_unique_part_list()[0]:
        # check if all cycle number are == 0  and 
        # check if all waypoint number == p 0 in the recipe
        cycle_set = set()
        wpnum_set = set()
        recipe_data = get_unique_part_list()[1]
        for i in range(len(recipe_data[selected_part])):
            cycle_set.add(recipe_data[selected_part][i]["Cycle Number"])
            wpnum_set.add(recipe_data[selected_part][i]["Waypoint Number"])

        if len(cycle_set) and len(wpnum_set) == 1:
            return True  
        else:
            return False
    else:
        return "Error in Part selection"


# get uniq models and camera listings for selcted part

def get_recipe_models_and_cams():
    _, recipe_data = get_unique_part_list()
    selected_part = session.get('SELECTED_PART')
    model_set=set()
    cam_set = set()

    for i in range(len(recipe_data[selected_part])):
        model_set.add((recipe_data[selected_part][i]["Model/Use case Number"]))
        cam_set.add((recipe_data[selected_part][i]["Camera Number"]))
    
    return list(model_set) , list(cam_set)
   
# get all the cameras for each model 

def get_cam_details_per_model():
    _, recipe_data = get_unique_part_list()
    selected_part = session.get('SELECTED_PART')

    print(recipe_data[selected_part])

# get_cam_details_per_model()