

import docker

# Create a Docker client
client = docker.from_env()

# List all running containers
containers = client.containers.list()

# Extract and print container names
container_names = [container.name for container in containers]
print(container_names)

networks = client.networks.list()

# Extract and print the names of the networks
network_names = [network.name for network in networks]
print(network_names)

#publish_all_ports (bool) – Publish all ports to the host.

# client.containers.run("ubuntu:latest", name=str("test33"), detach=True, tty = True, shm_size = "4G" , network = "edge_v2_test_network2" , restart_policy = {"Name": "on-failure", "MaximumRetryCount": 5}  )

client.containers.run('ubuntu',name=str("test303"), volumes = ["/home"]detach=True, tty = True, shm_size = "4G" ,device_requests=[docker.types.DeviceRequest(device_ids=["0"], capabilities=[['gpu']] )]   ) 

# from pymongo import MongoClient

# client = MongoClient('mongodb', port=27017)

# print(client.list_database_names())

# import time
# from json import dumps
# from kafka import KafkaProducer

# producer = KafkaProducer(
#     bootstrap_servers='edge_v2_kafka_1',
#     value_serializer=lambda x: dumps(x).encode('utf-8')
# )

# print(producer)
# idx = 0
# while True:
#     data = {'idx': idx}
#     print(data)
#     producer.send('test_1', value=data)
#     print(data)
#     time.sleep(0.03)
#     idx += 1

