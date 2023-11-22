import os
import time
from json import dumps
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers='0.0.0.0:9094',
    value_serializer=lambda x: dumps(x).encode('utf-8')
)

idx = 0
while True:
    data = {'idx': idx}
    producer.send('test', value=data)
    print(data)
    time.sleep(0.03)
    idx += 1