from werkzeug.middleware.dispatcher import (
    DispatcherMiddleware,
)  # use to combine each Flask app into a larger one that is dispatched based on prefix
from auth import get_auth_app
from deployment_manager import get_deployment_manager_app
from inspection_station import get_inspection_station_config_app
from reports import get_reports_app
from part_capture import get_part_capture_app
from health_check import get_health_check_app
from updates import get_updates_app
from data_management import get_data_management_app
from api_gateway import get_api_gateway_app
from operator_panel import get_operator_panel, sse_func

auth = get_auth_app()
deployment_manager = get_deployment_manager_app()
inspection_station_config = get_inspection_station_config_app()
reports = get_reports_app()
part_capture = get_part_capture_app()
health_check = get_health_check_app()
updates = get_updates_app()
data_management = get_data_management_app()
api_gateway = get_api_gateway_app()
operator_panel=get_operator_panel()
sse = sse_func()

application = DispatcherMiddleware(
    auth,
    {
        "/deployment_manager": deployment_manager,
        "/inspection_station": inspection_station_config,
        "/reports": reports, 
        "/part_capture": part_capture,
        "/health_check": health_check,
        "/updates": updates, 
        "/data_management": data_management,
        "/api_gateway": api_gateway,
        "/operator_panel":operator_panel,
        "/stream":sse,
    },
)
