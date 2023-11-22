from kafka import KafkaProducer
import json
import cv2
import threading
import os
import argparse
# f = open("edgeplusv2_config/v2_config.json")
print(os.getcwd())
f=open("edgeplusv2_config/v2_config.json")
data = json.load(f)
f.close()
producer = KafkaProducer(bootstrap_servers='127.0.0.1:9094')
KAFKA_BROKER_URL = data["LOCAL_KAFKA_BROKER_URL"]


parser = argparse.ArgumentParser()
parser.add_argument("--arg1", type=str, help="Argument 1")
parser.add_argument("--arg2", type=str, help="Argument 2")
args = parser.parse_args()
if args.arg1:
    print("Argument 1:", args.arg1)
if args.arg2:
    print("Argument 2:", args.arg2)


def start_cam(topic_name,path):
    
    camera_id = path
    topic = topic_name
    cap = cv2.VideoCapture(camera_id)
    while(True):
        
        ret, frame = cap.read()
        # window_name = 'image'
        # cv2.imshow(window_name, frame) 
        if ret:
            frame2= frame.tobytes()
            producer.send(topic, value=frame2)
            # print("frame sent", topic)
        else:
            cap.release()
            break
if __name__ == '__main__':
    
    
    topic_name = "cam"
    path =  0
    
    start_cam(topic_name,path)