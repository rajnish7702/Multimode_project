from abc import ABC, abstractmethod
import threading
import cv2
from inspection_station.neoapi import neoapi

# from arena_api.system import system
import queue
from kafka import KafkaConsumer
import numpy as np
from edgeplusv2_config.common_utils import *
import os
from datetime import datetime
import time
import ctypes

# from flask import Flask, Response
# from flask_cors import CORS
from threading import Event

no_frame_img = cv2.imread("no_camera.png")


class Camera(ABC):
    def __init__(
        self,
        event=Event(),
        no_frame_img=no_frame_img,
        camera_id=None,
        KAFKA_BROKER_URL=None,
        topic=None,
        width=640,
        height=480,
    ):
        self.KAFKA_BROKER_URL = KAFKA_BROKER_URL
        self.topic = topic
        self.camera_id = camera_id
        self.cap = None
        self.frame = None
        self.width = width
        self.height = height
        self.capture_time = None
        self.event = event
        self.no_frame_img = no_frame_img
        self.thread = None

    @abstractmethod
    def _start(self):
        pass

    def start(self, data_queue):
        shared_queue = queue.Queue()

        def thread_function():
            self._start(shared_queue)
            # print(self.thread)

        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=thread_function, daemon=True)
            self.thread.start()
        # print(data_queue.get())
        while True:
            try:
                frames = shared_queue.get()
                data_queue.put(frames)
                # print(frames)
                # print(data_queue)
            except:
                break

    def stop(self):
        try:
            if self.thread is not None and self.thread.is_alive():
                self.thread.join()
                self.thread = None
            self.event.set()
            print("stopping thread loop in camera class")
            self.t1.join()
            CacheHelper().set_json({"iskilled": True})

        except:
            pass

    def get_frame(self):
        if self.frame is not None:
            # print("get_frame size---------------->>>>>>>>>>", self.frame.shape)
            self.frame1 = cv2.resize(self.frame, (self.width, self.height))
            # CacheHelper().set_json({"stream_present":True})
            return self.frame1
        else:
            self.frame = self.no_frame_img
            self.frame2 = cv2.resize(self.frame, (self.width, self.height))
            # CacheHelper().set_json({"stream_present":False})
            return self.frame2


class KafkaStream(Camera):
    def _start(self):
        self.frame = None
        ws_id = data["inference"]["ws_id"]
        BOOTSTRAP_SERVERS = ["127.0.0.1:9092"]
        topic = ws_id + "_" + self.camera_id + "_i"
        topic.replace(":", "")
        topic.replace(".", "")
        consumer = KafkaConsumer(
            topic, bootstrap_servers=BOOTSTRAP_SERVERS, auto_offset_reset="latest"
        )
        for message in consumer:
            st = time.perf_counter()
            decoded = cv2.imdecode(np.frombuffer(message.value, np.uint8), 1)
            end = time.perf_counter()
            self.capture_time = end - st
            self.frame = decoded

        if self.frame is None:
            return None

    def _stop(self):
        pass


class IP(Camera):
    def _start(self, data_queue):
        self.ip = "rtsp://" + self.camera_id + "/h264_ulaw.sdp"
        self.cap = cv2.VideoCapture(self.ip)

        while True:
            iskilled = CacheHelper().get_json("iskilled")
            if not iskilled:
                try:
                    st = time.perf_counter()
                    ret, self.frame = self.cap.read()
                    end = time.perf_counter()
                    self.capture_time = end - st
                    payload_video_frame = cv2.imencode(
                        ".webp", self.frame, (cv2.IMWRITE_WEBP_QUALITY, 80)
                    )[1].tobytes()
                    data_queue.put(payload_video_frame)
                # return self.frame
                except:
                    pass
                if self.frame is None:
                    return None
            else:
                self.cap.release()
                break


class RTSP(Camera):
    def _start(self, data_queue):
        self.cap = cv2.VideoCapture(self.camera_id)
        while True:
            try:
                st = time.perf_counter()
                ret, self.frame = self.cap.read()
                end = time.perf_counter()
                self.capture_time = end - st
                payload_video_frame = cv2.imencode(
                    ".webp", self.frame, (cv2.IMWRITE_WEBP_QUALITY, 80)
                )[1].tobytes()
                data_queue.put(payload_video_frame)
            # return self.frame
            except:
                pass
            if self.frame is None:
                return None


class Baumer(Camera):
    def connect(self):
        try:
            self.camera = neoapi.Cam()
            self.camera.Connect(self.camera_id)
            self.camera.f.PixelFormat.SetString("BayerRG8")
        except Exception as e:
            print(e)

    def _start(self, data_queue):
        while True:
            iskilled = CacheHelper().get_json("iskilled")
            if not iskilled:
                try:
                    st = time.perf_counter()
                    input_frame = self.camera.GetImage()
                    end = time.perf_counter()
                    self.capture_time = end - st
                    if not input_frame.IsEmpty():
                        input_frame = input_frame.GetNPArray()
                        input_frame = cv2.cvtColor(input_frame, cv2.COLOR_BAYER_RG2RGB)
                        self.frame = input_frame
                    payload_video_frame = cv2.imencode(
                        ".webp", self.frame, (cv2.IMWRITE_WEBP_QUALITY, 80)
                    )[1].tobytes()
                    data_queue.put(payload_video_frame)
                except:
                    self.frame = None
            else:
                self.camera.Disconnect()
                break


# areana sdk issue
# class LUCID(Camera):
#     def connect(self):
#         tries = 0
#         tries_max = 3
#         sleep_time_secs = 5
#         while tries < tries_max:  # Wait for device for 60 seconds
#             devices = system.create_device()
#             if not devices:
#                 print(
#                     f'Try {tries+1} of {tries_max}: waiting for {sleep_time_secs} '
#                     f'secs for a device to be connected!')
#                 for sec_count in range(sleep_time_secs):
#                     time.sleep(1)
#                     print(f'{sec_count + 1 } seconds passed ',
#                         '.' * sec_count, end='\r')
#                 tries += 1
#             else:
#                 print(f'Created {len(devices)} device(s)')
#                 break

#         else:
#             raise Exception(f'No device found! Please connect a device and run '
#                             f'the example again.')

#         self.cap = devices[0]

#         # Get device stream nodemap
#         tl_stream_nodemap = self.cap.tl_stream_nodemap

#         tl_stream_nodemap["StreamBufferHandlingMode"].value = "NewestOnly"

#         # Enable stream auto negotiate packet size
#         tl_stream_nodemap['StreamAutoNegotiatePacketSize'].value = True

#         # Enable stream packet resend
#         tl_stream_nodemap['StreamPacketResendEnable'].value = True

#         # Get nodes ---------------------------------------------------------------
#         nodes = self.cap.nodemap.get_node(['Width', 'Height', 'PixelFormat'])

#         # Nodes
#         nodes['Width'].value = 1280

#         height = nodes['Height']
#         height.value = 720

#         # Set pixel format to PolarizedAolp_Mono8
#         # pixel_format_name = 'PolarizedAolp_Mono8'
#         # print(f'Setting Pixel Format to {pixel_format_name}')
#         # nodes['PixelFormat'].value = pixel_format_name

#         pixel_format_name = 'RGB8'
#         print(f'Setting Pixel Format to {pixel_format_name}')
#         nodes['PixelFormat'].value = pixel_format_name


#     def _start(self):
#         num_channels = 3
#         with self.cap.start_stream():
#             while True:
#                 time.sleep(0.1)
#                 st = time.perf_counter()

#                 buffer = self.cap.get_buffer()
#                 """
#                 Copy buffer and requeue to avoid running out of buffers
#                 """
#                 item = BufferFactory.copy(buffer)
#                 self.cap.requeue_buffer(buffer)

#                 buffer_bytes_per_pixel = int(len(item.data)/(item.width * item.height))
#                 """
#                 Buffer data as cpointers can be accessed using buffer.pbytes
#                 """
#                 array = (ctypes.c_ubyte * num_channels * item.width * item.height).from_address(ctypes.addressof(item.pbytes))
#                 """
#                 Create a reshaped NumPy array to display using OpenCV
#                 """
#                 npndarray = np.ndarray(buffer=array, dtype=np.uint8, shape=(item.height, item.width, buffer_bytes_per_pixel))

#                 self.frame = npndarray

#                 BufferFactory.destroy(item)

#                 self.capture_time = time.perf_counter()-st


class NoStream(Camera):
    def _start(self):
        while True:
            self.frame = None


class VideoStream(Camera):
    def __init__(
        self,
        event=Event(),
        no_frame_img=no_frame_img,
        camera_id=None,
        KAFKA_BROKER_URL=None,
        topic=None,
        width=640,
        height=480,
    ):
        super().__init__(
            event, no_frame_img, camera_id, KAFKA_BROKER_URL, topic, width, height
        )
        # t2 for kafka publish
        self.t2 = None

    def _start(self, data_queue):
        # print(self.camera_id)
        cap = cv2.VideoCapture(self.camera_id)
        # print(iskilled)
        while cap.isOpened():
            # print("here i am ")
            iskilled = CacheHelper().get_json("iskilled")
            # for publishing to kafkas
            # self.t2 =threading.Thread(target=self.publish_frame_to_kafka ,daemon = True)
            # self.t2.start()
            if not iskilled:
                try:
                    st = time.perf_counter()
                    ret, frame = cap.read()
                    end = time.perf_counter()
                    self.capture_time = end - st
                    # print("cap time for USB CAM === ", self.capture_time)
                    # if frame is read correctly ret is True
                    if not ret:
                        print("Can't receive frame (stream end?). Exiting ...")
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                        # break
                    if self.event.is_set():
                        print(
                            "event set to True , Stopping Thread in ",
                            __class__.__name__,
                        )
                        break

                    fps = 1 / self.capture_time
                    # print("Estimated frames per second : {0}".format(fps), __class__.__name__)
                    frame5 = cv2.putText(
                        img=frame,
                        text="Estimated FPS  :"
                        + str(format(fps))
                        + "___"
                        + str(__class__.__name__),
                        org=(50, 50),
                        fontFace=cv2.FONT_HERSHEY_DUPLEX,
                        fontScale=1.0,
                        color=(125, 146, 155),
                        thickness=2,
                    )
                    self.frame = frame5
                    # cv2.imshow('frame',self.frame)
                    if self.frame is None:
                        # print("None Frame Recieved!")
                        continue
                    payload_video_frame = cv2.imencode(
                        ".webp", self.frame, (cv2.IMWRITE_WEBP_QUALITY, 80)
                    )[1].tobytes()
                    data_queue.put(payload_video_frame)

                    # shared_queue.put(self.frame)
                    # print(shared_queue)
                except:
                    continue
            else:
                cap.release()
                # self.event.set()
                break


class Mp4_file(Camera):
    def _start(self):
        cap = cv2.VideoCapture(self.camera_id)
        while cap.isOpened():
            st = time.perf_counter()
            ret, frame = cap.read()
            # print("raw frame size---------------->>>>>>>>>>", frame.shape)

            end = time.perf_counter()
            self.capture_time = end - st
            # print("cap time for MP$ File === ", self.capture_time)
            if ret:
                self.frame3 = frame
                fps = 1 / self.capture_time
                print(
                    "Estimated frames per second : {0}".format(fps), __class__.__name__
                )

                self.frame = cv2.putText(
                    img=self.frame3,
                    text="Estimated FPS  :"
                    + str(format(fps))
                    + "___"
                    + str(__class__.__name__),
                    org=(50, 50),
                    fontFace=cv2.FONT_HERSHEY_DUPLEX,
                    fontScale=1.0,
                    color=(125, 146, 155),
                    thickness=2,
                )
            else:
                print("MP4 Video ended ")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.frame = None
                continue
            if self.event.is_set():
                print("event set to True , Stopping Thread in ", __class__.__name__)
                break


# cam_stream_obj = VideoStream(camera_id=0)

# cam_stream_obj.start()
# print("trying")
# time.sleep(5)
# cam_stream_obj.stop()

# mp4_stream_obj = Mp4_file(camera_id="traffic.mp4")

# mp4_stream_obj.start()

# # time.sleep(5)

# print("STOPING _____________________________USB ______________________")

# mp4_stream_obj.stop()
# print("STOPING _____________________________MP$ ______________________")
# while True:
#     print("llllllllllllllllllllllllllllllllllllllllllll")


# stream_dict = data["inference"]["stream"]
# camera_list = list(stream_dict.keys())

# if len(camera_list) == 0:
#     stream_obj = NoStream()
#     CacheHelper().set_json({"stream_present":False})

# else:
#     if OPERATING_SYSTEM == "Windows":
#         stream_obj = KafkaStream(camera_id=stream_dict["CAMERA_ID"])

#     elif OPERATING_SYSTEM == "Linux":

#         if "USB" in camera_list[0]:
#             print("USB")
#             # camera_id=stream_dict["USB"]
#             stream_obj = KafkaStream(camera_id=stream_dict["USB"])

#         elif "IP" in camera_list[0]:
#             camera_id=stream_dict["IP"]
#             stream_obj = IP(camera_id=stream_dict["IP"])

#         elif "RTSP" in camera_list[0]:
#             camera_id=stream_dict["RTSP"]
#             stream_obj = RTSP(camera_id=stream_dict["RTSP"])

#         elif "GIGE-BAUMER" in camera_list[0]:
#             camera_id=stream_dict["GIGE-BAUMER"]
#             stream_obj = Baumer(camera_id=stream_dict["GIGE-BAUMER"])
#             stream_obj.connect()

#         elif "LUCID" in camera_list[0]:
#             camera_id=stream_dict["LUCID"]
#             stream_obj = LUCID()
#             stream_obj.connect()

#     else:
#         camera_id = None
#         stream_obj = NoStream()

# stream_obj.start()


# def start_stream():
#     while True:

#         raw_frame = stream_obj.get_frame()

#         if raw_frame is not None:
#             inspect_trigger = CacheHelper().get_json("inspect")
#             stream_present = CacheHelper().get_json("stream_present")
#             if inspect_trigger and stream_present:
#                 image_name = datetime.now().strftime("%m%d%Y%H%M%S")
#                 save_raw_frame(raw_frame, image_name)
#                 CacheHelper().set_json({"inspect":False})
#                 # conn.send(raw_frame, image_name)
#                 inspection(raw_frame, image_name, stream_obj.capture_time)


# def save_raw_frame(raw_frame, image_name):
#     save_path = "saved_images"
#     raw_frame_name = "raw_frame_" + str(image_name) + "_.jpg"
#     cv2.imwrite(os.path.join(save_path, raw_frame_name), raw_frame)

# mp1 = threading.Thread(target=start_stream)
# mp1.start()


# def get_infered_stream():
#     while True:
#         raw_frame = stream_obj.get_frame()
#         if raw_frame is not None:
#             try:
#                 out_frame, original_frame,f ,d, infer_time = infered_frame(raw_frame)
#             except:
#                 out_frame = raw_frame

#         image_encoded = cv2.imencode('.jpeg', out_frame)[1].tobytes()
#         # print("Yielded")
#         yield (b'--frame\r\n'
#             b'Content-Type: image/jpeg\r\n\r\n' + image_encoded + b'\r\n\r\n')


# app = Flask(__name__)
# cors = CORS(app)


# @app.route('/')
# def index():
#     return Response(get_infered_stream(),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')

# def start_stream_server():
#     # global conn
#     # conn = parent_conn
#     app.run(host="0.0.0.0", port=8900)

# start_stream_server()
