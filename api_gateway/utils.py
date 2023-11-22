import json
import pymongo
from bson import json_util
from bson.objectid import ObjectId
from flask import jsonify, redirect, url_for
from edgeplusv2_config.common_utils import (
    CloudMongoHelper,
    CloudMongoHelper,
    user_domain,
)


# getting only one record
def one_document_utils(collection, document):
    document_1 = get_documents_id(document)
    res = {"status": "failure"}
    response = CloudMongoHelper().getCollection(collection)
    response = response.find_one(document_1, document[1])
   
    response=json.loads(json_util.dumps(response))
    res = {"status": response}
    return res


# Getting all recode base on filter
def all_document_utils(collection, document):
    document_1 = get_documents_id(document)
    res = {"status": "failure"}

    response = [
        docker_image
        for docker_image in CloudMongoHelper()
        .getCollection(collection)
        .find(document_1, document[1])
    ]
    response=json.loads(json_util.dumps(response))
    res = {"status": response}
    return res


# Insert one record
def insert_document_utils(collection, document):
    new = {"document": document}
    response = {"status": "fails"}
    result = CloudMongoHelper().getCollection(collection).insert_one(new).inserted_id
   
    response = {"status": str(result)}
    return response


# delete one record
def delete_document_util(collection, document):
    document_1 = get_documents_id(document)

    response = CloudMongoHelper().getCollection(collection)
    if response.delete_one(document_1).deleted_count > 0:
        response = {"status": "successfull deleted"}
    else:
        response = {"status": "Data deleted Failure"}

    return response


# update one record
def update_documents_util(collection, document):
    document_1 = get_documents_id(document)
    response = {"status": "failure"}
    response = (
        CloudMongoHelper().getCollection(collection).update_one(document_1, document[1])
    )
    response = {"status": "success"}
    return response


# if recive id adding ObjectId if not return and id not  same as is it
# def get_documents_id(document):
#     document_1 = {}
#     if "_id" in document[0].keys():
#         for i in document[0].keys():
#             if i == "_id":
#                 document_1[i] = ObjectId(document[0][i])
#             else:
#                 document_1[i] = document[0][i]
#     return document_1

def get_documents_id(document):
    document_1 = document[0]
    if "_id" in document[0].keys():
        # for i in document[0].keys():
        #     if i == "_id":
        document_1["_id"] = ObjectId(document[0]["_id"])
        return document_1
    else:
        # document_1 = document[0]
        return document_1
