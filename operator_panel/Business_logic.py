from common_utils import CacheHelper, logger
from collections import defaultdict
import os 
import cv2
from PIL import Image  
import PIL  



redisobj = CacheHelper()
data = {
    "Cam1": [
        {"car": 4, "truck":2},
        ["airplane"],
        [
            {
                "xmin": 1144.7633056641,
                "ymin": 595.8936767578,
                "xmax": 1279.4097900391,
                "ymax": 719.1907958984,
                "confidence": 0.9060687423,
                "class": 2,
                "name": "truck",
            },
            {
                "xmin": 952.3121948242,
                "ymin": 373.3941345215,
                "xmax": 1034.9847412109,
                "ymax": 423.7705993652,
                "confidence": 0.8967467546,
                "class": 2,
                "name": "truck",
            },
            {
                "xmin": 33.6896286011,
                "ymin": 406.7064819336,
                "xmax": 199.5580444336,
                "ymax": 508.5615844727,
                "confidence": 0.5613247871,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 1207.9111328125,
                "ymin": 432.9835205078,
                "xmax": 1279.9526367188,
                "ymax": 509.4899902344,
                "confidence": 0.3046503067,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 1207.9111328125,
                "ymin": 432.9835205078,
                "xmax": 1279.9526367188,
                "ymax": 509.4899902344,
                "confidence": 0.8046503067,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 1207.9111328125,
                "ymin": 432.9835205078,
                "xmax": 1279.9526367188,
                "ymax": 509.4899902344,
                "confidence": 0.8046503067,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 755.8832397461,
                "ymin": 293.2763061523,
                "xmax": 794.061340332,
                "ymax": 320.8984985352,
                "confidence": 0.7089586258,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 116.0605239868,
                "ymin": 187.5576629639,
                "xmax": 158.2402954102,
                "ymax": 208.5818939209,
                "confidence": 0.6582431793,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 716.535949707,
                "ymin": 314.0187683105,
                "xmax": 762.3311157227,
                "ymax": 355.0004577637,
                "confidence": 0.5762862563,
                "class": 7,
                "name": "truck",
            },
            {
                "xmin": 467.29296875,
                "ymin": 253.7255859375,
                "xmax": 489.3034057617,
                "ymax": 271.6286621094,
                "confidence": 0.3830334246,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 545.7813720703,
                "ymin": 252.6777954102,
                "xmax": 566.2260742188,
                "ymax": 267.2114257812,
                "confidence": 0.3786118925,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 716.7490844727,
                "ymin": 312.4823303223,
                "xmax": 762.3085327148,
                "ymax": 356.3469543457,
                "confidence": 0.3716720343,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 796.477355957,
                "ymin": 263.6636352539,
                "xmax": 824.4439086914,
                "ymax": 286.2014160156,
                "confidence": 0.2904703021,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 405.9106445312,
                "ymin": 196.3486785889,
                "xmax": 848.0341796875,
                "ymax": 264.7123718262,
                "confidence": 0.6530582249,
                "class": 4,
                "name": "airplane",
            },
        ],
        "",
    ],
    "Cam2": [
        {"bus": 3, "car": 2, "chain": 1, "movie": 3, "person": 5, "remote": 4},
        ["cellphone", "clock", "stop sign"],
        [
            {
                "xmin": 1144.7633056641,
                "ymin": 595.8936767578,
                "xmax": 1279.4097900391,
                "ymax": 719.1907958984,
                "confidence": 0.9060687423,
                "class": 2,
                "name": "truck",
            },
            {
                "xmin": 952.3121948242,
                "ymin": 373.3941345215,
                "xmax": 1034.9847412109,
                "ymax": 423.7705993652,
                "confidence": 0.8967467546,
                "class": 2,
                "name": "truck",
            },
            {
                "xmin": 33.6896286011,
                "ymin": 406.7064819336,
                "xmax": 199.5580444336,
                "ymax": 508.5615844727,
                "confidence": 0.5613247871,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 1207.9111328125,
                "ymin": 432.9835205078,
                "xmax": 1279.9526367188,
                "ymax": 509.4899902344,
                "confidence": 0.3046503067,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 1207.9111328125,
                "ymin": 432.9835205078,
                "xmax": 1279.9526367188,
                "ymax": 509.4899902344,
                "confidence": 0.8046503067,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 1207.9111328125,
                "ymin": 432.9835205078,
                "xmax": 1279.9526367188,
                "ymax": 509.4899902344,
                "confidence": 0.8046503067,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 755.8832397461,
                "ymin": 293.2763061523,
                "xmax": 794.061340332,
                "ymax": 320.8984985352,
                "confidence": 0.7089586258,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 116.0605239868,
                "ymin": 187.5576629639,
                "xmax": 158.2402954102,
                "ymax": 208.5818939209,
                "confidence": 0.6582431793,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 716.535949707,
                "ymin": 314.0187683105,
                "xmax": 762.3311157227,
                "ymax": 355.0004577637,
                "confidence": 0.5762862563,
                "class": 7,
                "name": "truck",
            },
            {
                "xmin": 467.29296875,
                "ymin": 253.7255859375,
                "xmax": 489.3034057617,
                "ymax": 271.6286621094,
                "confidence": 0.3830334246,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 545.7813720703,
                "ymin": 252.6777954102,
                "xmax": 566.2260742188,
                "ymax": 267.2114257812,
                "confidence": 0.3786118925,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 716.7490844727,
                "ymin": 312.4823303223,
                "xmax": 762.3085327148,
                "ymax": 356.3469543457,
                "confidence": 0.3716720343,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 796.477355957,
                "ymin": 263.6636352539,
                "xmax": 824.4439086914,
                "ymax": 286.2014160156,
                "confidence": 0.2904703021,
                "class": 2,
                "name": "car",
            },
            {
                "xmin": 405.9106445312,
                "ymin": 196.3486785889,
                "xmax": 848.0341796875,
                "ymax": 264.7123718262,
                "confidence": 0.2530582249,
                "class": 4,
                "name": "airplane",
            },
        ],
        "",
    ],
}


def business_logic_all(data,model,LINK):
    results = {}
    for cam, response in data.items():
    # for i in range(1):
        # features = {"car": 4, "airplane":1,"truck": 2}
        # defects = ["car"]
        # logger.debug(cam)
        features = response[0]
        if features is None:
            features = {}
        defects = response[1]
        if defects is None:
            defects=[]
        resp = response[2]
        # img_link = response[3]
        
        result = ""
        results[cam] = {}
        results[cam]["feature_predicted"]={}
        results[cam]["defects_predicted"]={}

        result_img_link=draw_boxes(resp,cam,model)
        results[cam]["image"] = f"{LINK}{result_img_link}"
        
        items_found = defaultdict(lambda: 0)

        for res in resp:
            if res["confidence"] > 0.6:
                items_found[res["name"]] += 1

        # logger.debug(items_found)
        results[cam]["result"] = ""
        
        # parsing defects
        for defect in defects:
            if defect in items_found.keys():
                results[cam]["result"] = "Rejected"
                break
                # result = "Rejected"

        # parsing features
        if results[cam]["result"] != "Rejected":
            for name, count in features.items():
                # if
                # logger.info(name, count)
                if name in items_found.keys() and features[name] == items_found[name]:
                    results[cam]["result"] = "Accepted"
                else:
                    results[cam]["result"] =  "Rejected"
                    break
        for name, count in items_found.items():
            if name in features.keys():
                results[cam]["feature"][name]=count
            if name in defects:
                results[cam]["defects"][name]=count


        # logger.success(results)
        # break
    return results
    pass

def draw_boxes(response,cam,current_model_name):
    current_path = os.getcwd()
    
    logger.error(current_path)
    # parent_directory = os.path.dirname(current_path)
    # logger.error(parent_directory)
    print(f"{current_path}/data_lake_in_container/frame_{cam}_{current_model_name}.png")
    
    frame = cv2.imread(f"{current_path}/data_lake_in_container/frame_{cam}_{current_model_name}.png",1)
    # frame_copy = Image.fromarray(frame,mode="RGB")  
    cv2.imwrite(f"{current_path}/data_lake_in_container_infered/frame_{cam}_{current_model_name}_{CacheHelper().get_json('cid')}.png", frame)

    # frame_copy.save(f"{current_path}/data_lake_in_container_infered/frame_{cam}_{current_model_name}_{CacheHelper().get_json('cid')}.png")
    
    logger.error(frame)
    for res in response:
        print(res, "<-----")
        # logger.debug(res)

        p1=[]
        p2=[]
        p1.append(int(res["xmin"]))
        p1.append(int(res["xmax"]))

        p2.append(int(res["ymin"]))
        p2.append(int(res["ymax"]))
        print(p1, "<---p1")
        print(p2, "<---p2")

        label = res.get("name", "unknown")
        
        
        # print(f"{current_path}/data_lake_in_container/frame_{cam}_{current_model_name}.png")
        # print(frame)
        # cv2.imshow('image',frame)
        cv2.rectangle(frame, (p1[0], p2[0]), (p1[1], p2[1]), (0, 255, 0), 2)
        cv2.putText(frame, label, (p1[0], p2[0] - 10), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 0), 1)
    infered_frame_name = f"frame_{cam}_{current_model_name}_{CacheHelper().get_json('cid')}"
    # frame_pil = Image.fromarray(frame,mode="RGB")  
    # logger.error(f"{current_path}/data_lake_in_container/{infered_frame_name}.png")
    # frame_pil.save(f"{current_path}/data_lake_in_container_infered/{infered_frame_name}_infered.png")
    cv2.imwrite(f"{current_path}/data_lake_in_container_infered/{infered_frame_name}_infered.png", frame)
    return f"/data_lake_in_container_infered/{infered_frame_name}_infered.png"


def business_logic(response, cl_features, cl_defects):
    flag = None
    # print(response)
    # print(cl_features,cl_defects)
    if cl_defects is None:
        cl_defects = []
    if cl_features is None:
        cl_features = {}
    result_dic = cl_features.copy()
    # result_dic.update(cl_defects)
    result_dic_final = result_dic.copy()

    # print(result_dic,result_dic_final)
    for i in result_dic_final.keys():
        result_dic_final[i] = 0
    # print(result_dic_final)

    # for j in defects:
    #     result_dic_final[j] = 0

    feature_keys_list = list(cl_features.keys())
    # print(feature_keys_list)
    for res in response:
        # print(res)
        # print(feature_keys_list,res["name"])
        # if res['name'] in result_dic_final:
        #     result_dic_final[res['name']]+=1
        if res["confidence"] > 0.6 and res["name"] in feature_keys_list:
            result_dic_final[res["name"]] += 1

        if res["confidence"] > 0.6 and res["name"] in cl_defects:
            flag = "Rejected"
            # result_dic_final[res["name"]]+=1
            print("found defect")
            return flag

    print("final after additions", result_dic, result_dic_final)

    # print('updates-->>',result_dic_final)
    if len(result_dic) != len(result_dic_final):
        print("Not equal")
        flag = "Rejected"
        return flag

    # if len(result_dic)==len(result_dic_final):
    for i, j in result_dic.items():
        print(i, j)
        if j == result_dic_final[i]:
            flag = "Accepted"
        else:
            flag = "Rejected"
    return flag

    #     for i in result_dic:
    #         if result_dic.get(i)!=result_dic_final.get(i):
    #             flag=1
    #             break
    # return (flag)


# main call to program:

Response = [
    {
        "xmin": 1144.7633056641,
        "ymin": 595.8936767578,
        "xmax": 1279.4097900391,
        "ymax": 719.1907958984,
        "confidence": 0.9060687423,
        "class": 2,
        "name": "truck",
    },
    {
        "xmin": 952.3121948242,
        "ymin": 373.3941345215,
        "xmax": 1034.9847412109,
        "ymax": 423.7705993652,
        "confidence": 0.8967467546,
        "class": 2,
        "name": "truck",
    },
    {
        "xmin": 33.6896286011,
        "ymin": 406.7064819336,
        "xmax": 199.5580444336,
        "ymax": 508.5615844727,
        "confidence": 0.5613247871,
        "class": 2,
        "name": "car",
    },
    {
        "xmin": 1207.9111328125,
        "ymin": 432.9835205078,
        "xmax": 1279.9526367188,
        "ymax": 509.4899902344,
        "confidence": 0.3046503067,
        "class": 2,
        "name": "car",
    },
    {
        "xmin": 1207.9111328125,
        "ymin": 432.9835205078,
        "xmax": 1279.9526367188,
        "ymax": 509.4899902344,
        "confidence": 0.8046503067,
        "class": 2,
        "name": "car",
    },
    {
        "xmin": 1207.9111328125,
        "ymin": 432.9835205078,
        "xmax": 1279.9526367188,
        "ymax": 509.4899902344,
        "confidence": 0.8046503067,
        "class": 2,
        "name": "car",
    },
    {
        "xmin": 755.8832397461,
        "ymin": 293.2763061523,
        "xmax": 794.061340332,
        "ymax": 320.8984985352,
        "confidence": 0.7089586258,
        "class": 2,
        "name": "car",
    },
    {
        "xmin": 116.0605239868,
        "ymin": 187.5576629639,
        "xmax": 158.2402954102,
        "ymax": 208.5818939209,
        "confidence": 0.6582431793,
        "class": 2,
        "name": "car",
    },
    {
        "xmin": 716.535949707,
        "ymin": 314.0187683105,
        "xmax": 762.3311157227,
        "ymax": 355.0004577637,
        "confidence": 0.5762862563,
        "class": 7,
        "name": "truck",
    },
    {
        "xmin": 467.29296875,
        "ymin": 253.7255859375,
        "xmax": 489.3034057617,
        "ymax": 271.6286621094,
        "confidence": 0.3830334246,
        "class": 2,
        "name": "car",
    },
    {
        "xmin": 545.7813720703,
        "ymin": 252.6777954102,
        "xmax": 566.2260742188,
        "ymax": 267.2114257812,
        "confidence": 0.3786118925,
        "class": 2,
        "name": "car",
    },
    {
        "xmin": 716.7490844727,
        "ymin": 312.4823303223,
        "xmax": 762.3085327148,
        "ymax": 356.3469543457,
        "confidence": 0.3716720343,
        "class": 2,
        "name": "car",
    },
    {
        "xmin": 796.477355957,
        "ymin": 263.6636352539,
        "xmax": 824.4439086914,
        "ymax": 286.2014160156,
        "confidence": 0.2904703021,
        "class": 2,
        "name": "car",
    },
    {
        "xmin": 405.9106445312,
        "ymin": 196.3486785889,
        "xmax": 848.0341796875,
        "ymax": 264.7123718262,
        "confidence": 0.2530582249,
        "class": 4,
        "name": "airplane",
    },
]

"""
[
    {
        "xmin": 676.5651855469,
        "ymin": 39.3558197021,
        "xmax": 1065.7922363281,
        "ymax": 364.0089111328,
        "confidence": 0.6960488558,
        "class": 15,
        "name": "cat"
    },
    {
        "xmin": 258.700592041,
        "ymin": 368.9248046875,
        "xmax": 711.7763671875,
        "ymax": 712.2741699219,
        "confidence": 0.6559205472,
        "class": 15,
        "name": "cat"
    },
    {
        "xmin": 258.700592041,
        "ymin": 368.9248046875,
        "xmax": 711.7763671875,
        "ymax": 712.2741699219,
        "confidence": 0.5559205472,
        "class": 15,
        "name": "dog"
    },
    {
        "xmin": 139.7655792236,
        "ymin": 117.0407562256,
        "xmax": 438.1996459961,
        "ymax": 310.7407226562,
        "confidence": 0.6450715184,
        "class": 15,
        "name": "cat"
    },
    {
        "xmin": 198.5142211914,
        "ymin": 233.1630249023,
        "xmax": 651.8222045898,
        "ymax": 463.108581543,
        "confidence": 0.6107559323,
        "class": 15,
        "name": "cat"
    }
]
"""

# features = {"cat": 4}
# defects = ["dog"]

# features = {"car": 4}
# defects = ["airplane"]

# if __name__ == '__main__':

#   # response = redisobj.get_json("camera_response_data")
#   # count_logic = redisobj.get_json("camera_count_logic")
#   # if count_logic:
#     # features = count_logic["features"]
#     # defects = count_logic["defects"]

#     business_done = business_logic(Response,features,defects)
#     # camera_result = redisobj.set_json({"camera_result":business_done})
#     print(business_done)

# business_done = business_ka_logic_hu_mai(Response,features,defects)
# business_logic_all(data,"M2")
