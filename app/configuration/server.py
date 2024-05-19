from fastapi import FastAPI
#from fastapi_utils.tasks import repeat_every
from app.configuration.routes import __routes__

class Server:
    __app: FastAPI

    def __init__(self, app: FastAPI):
        self.__app = app
        self.__register_routes(app)

    def get_app(self) -> FastAPI:
        return self.__app

    @staticmethod
    def __register_event(app):
        # app.on_event('startup')(repeat_every(seconds=2)(test))
        ...

    @staticmethod
    def __register_routes(app):
        __routes__.register_routes(app)