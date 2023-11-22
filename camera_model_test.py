import docker

client = docker.from_env()

client.containers.run(
                    "mod_image",
                    name="model_img_redis",
                    environment={"port":3456,"model_name":"mod_image"},
                    detach=True,
                    tty=True,
                    shm_size = "4G",
                    network="edge_v2_test_network2",
                    restart_policy = {"Name": "on-failure", "MaximumRetryCount": 5}
                    # command="python3 adapter.py"
                )

#  client.containers.run(
#                         image_name,name=container_name,
#                         detach=True,
#                         tty=True,
#                         shm_size = "4G",
#                         network="edge_v2_test_network2",
#                         restart_policy = {"Name": "on-failure", "MaximumRetryCount": 5},
#                         environment={"port":port,"model_name":container_name}
#                     )