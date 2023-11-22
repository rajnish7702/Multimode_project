from flask import Flask

app = Flask(__name__)

debug = True


def get_health_check_app():
    app = Flask(__name__)
    # app.config['SECRET_KEY'] = 'qporjflamfzpaqorigjqp'

    from .views import views

    app.register_blueprint(views, url_prefix="/")
    return app
