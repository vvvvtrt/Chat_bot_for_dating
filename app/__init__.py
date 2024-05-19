from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.configuration.server import Server


def create_app(_=None) -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return Server(app).get_app()
