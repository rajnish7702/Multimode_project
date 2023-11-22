from flask import Flask
from werkzeug.serving import run_simple  # werkzeug development server
from app import application
import subprocess
import time
def services_up():
    """Starts the docker containers housing the required services.

    Args:
      None

    Returns:
      None
    """
    print("starting services")
    subprocess.run(["docker-compose", "up", "-d"])

def service_down():
    """Stops and removes all running docker containers for this project.
    
    Args:
      None
      
    Returns:
      None
    """
    print('stopping services')
    subprocess.run(['docker-compose', 'down'])

    

if __name__ == "__main__":
    # service_down()
    # time.sleep(5)
    services_up()
    run_simple(
        "0.0.0.0",
        5000,
        application,
        use_reloader=True,
        use_debugger=True,
        use_evalex=True,
        threaded=True
    )
