from flask import Blueprint, request, jsonify, redirect, url_for,Response
import json
from bson.json_util import dumps
from edgeplusv2_config.common_utils import *
from datetime import datetime

# from .utils import *
import socket

views = Blueprint("views", __name__)


@views.route("/")
def hello_world():
    return "Hello, World! --- reports"




@views.route("/get_mega_report",methods=["POST"])
def get_mega_report():
    """
    part_number : 
    status : 
    features :
    from_date: "2023-10-10 00:00:00"
    to_date : "2023-10-07 23:59:59"
    limit :
    skip :  
    """

    data = json.loads(request.data)
    from_date = data["from_date"]
    to_date = data["to_date"]
    part_number = data["part_number"]
    status = data["status"]
    

    from_date_obj = datetime.strptime(from_date,"%Y-%m-%d %H:%M:%S")
    to_date_obj = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S")

    from_year = from_date_obj.year
    from_month = from_date_obj.month
    from_day = from_date_obj.day

    to_year = to_date_obj.year
    to_month = to_date_obj.month
    to_day = to_date_obj.day


    start_date = datetime(from_year, from_month, from_day)
    end_date = datetime(to_year, to_month, to_day)

    months_years = []

    # Start from the beginning of the range and iterate through months until the end date
    current_date = start_date
    while current_date <= end_date:
        # Extract the year and month from the current date
        year = current_date.year
        month = current_date.month

        # Add the month-year combination to the list
        months_years.append(f"{year}-{month:02d}")

        # Move to the next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    print(months_years)

    filter_dict = {}

    if status is not "":
        filter_dict["final_results.overall_result"] = status
    if part_number is not "":
        filter_dict["part_number"] = part_number

    final_docs_list = []
    for index, value in enumerate(months_years):
        if index==0:
            start_date_str = value + "-"+ str(from_day)
            end_date_str = str(to_year) + "-" + str(to_month) + "-" + str(to_day+1) 

          
            sort_start_date = datetime.strptime(start_date_str,"%Y-%m-%d")
            sort_end_date = datetime.strptime(end_date_str,"%Y-%m-%d")
            print(type(sort_end_date))
            
            pipeline = [
                {
                    
                    "$match": {
                        "$and" : [
                            {"inspection_date_time": {"$gte": sort_start_date,
                                                      "$lte": sort_end_date}},
                            filter_dict
                        ],
                    }
                },
                {
                    "$sort": {
                        "inspection_date_time": 1 
                    }
                }
            ]
            result = LocalMongoHelper().getCollection(f'inspection_results_{value}').aggregate(pipeline)
            docs_list = []
            for docs in result:
                docs_list.append(docs)
            final_docs_list = final_docs_list + docs_list

        elif index == len(months_years) -1:
            input_date_str = value + "-"+ str(to_day+1)
            sort_input_date = datetime.strptime(input_date_str,"%Y-%m-%d")

            pipeline = [
                {
                    "$match": {
                        "$and" : [
                            {"inspection_date_time": {"$lte": sort_input_date},},
                            filter_dict
                        ],
                    }
                },
                {
                    "$sort": {
                        "inspection_date_time": 1  # 1 for ascending order, -1 for descending order
                    }
                }
            ]
            result = LocalMongoHelper().getCollection(f'inspection_results_{value}').aggregate(pipeline)
            docs_list = []
            for docs in result:
                docs_list.append(docs)
            final_docs_list = final_docs_list + docs_list
        else :
            print(value.split("-")[1])
    
            input_date = f"/^{value}/"
            print(input_date)
            pipeline = [
                {
                    "$match": {
                        "$and" : [
                            {"$expr": {
                                "$and": [
                                    { "$eq": [{ "$year": "$inspection_date_time" }, int(value.split("-")[0])] },
                                    { "$eq": [{ "$month": "$inspection_date_time" }, int(value.split("-")[1])] }
                                    ]
                                }
                            },
                            filter_dict
                        ]
                    }
                },
                {
                    "$sort": {
                        "inspection_date_time": 1  # 1 for ascending order, -1 for descending order
                    }
                }
            ]
            result = LocalMongoHelper().getCollection(f'inspection_results_{value}').aggregate(pipeline)
            docs_list = []
            for docs in result:
                docs_list.append(docs)
            final_docs_list = final_docs_list + docs_list

    print(len(final_docs_list))
    response = Response(response=json.dumps(final_docs_list,cls=Encoder), status=200, mimetype="applicationn/json")
    return response

