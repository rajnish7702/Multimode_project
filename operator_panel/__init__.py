from flask import Flask
from flask_sse import sse

app = Flask(__name__)

debug = True


def get_operator_panel():
    app = Flask(__name__)
    # app.config['SECRET_KEY'] = 'qporjflamfzpaqorigjqp'

    from .views import views
    # print(app.config,"------------op")
    app.config["SSE_REDIS_URL"] = "redis://localhost"

    app.register_blueprint(views, url_prefix="/")
    return app

# for stream url
def sse_func():
    app = Flask(__name__)
    app.config["SSE_REDIS_URL"] = "redis://localhost"
    # print(app.config)

    app.register_blueprint(sse, url_prefix='/')
    return app
