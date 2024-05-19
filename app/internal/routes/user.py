from fastapi import APIRouter, UploadFile, File, Form, Request, Response
from fastapi.responses import JSONResponse
import asyncio
from pydantic import BaseModel
import app.internal.database.db as db
from typing import Dict
from time import sleep
import pandas as pd

router = APIRouter(
    prefix="/api/v1"
)


class Return(BaseModel):
    full_name: str


class ReturnID(BaseModel):
    id: int


class PersonData(BaseModel):
    id: int
    full_name: str
    birthdate: str
    phone_number: str
    mother_full_name: str
    city: str
    email: str


class DataReception(BaseModel):
    id: int
    full_name: str
    age: str
    parents_name: str
    address: str
    date_of_visit: str
    specialists_name: str
    meeting_format: str
    personal_factors: str
    neurosurgery: str
    sensitivity: str
    neurourology: str
    mobility: str
    self_service: str
    TCP: str
    neuroorthopedics: str
    coloproctology: str
    productive_activity: str
    leisure: str
    communication: str
    ophthalmology: str
    height_and_weight: str
    smart_functions: str
    pain: str
    tasks: str
    other: str


class TG_id(BaseModel):
    email: str
    id_tg: int


class TG_message(BaseModel):
    id_tg: int
    message: str


queue_message = []


@router.get("/return_all_users")
async def return_all_users():
    return {"data": await db.return_all_users()}


@router.post("/add_person")
async def add_person(data: PersonData):
    return {"status": await db.add_new_person(data)}


@router.post("/return_person")
async def return_person(data: Return):
    return {"data": await db.return_person(data.full_name)}


@router.post("/add_reception")
async def add_reception(data: DataReception):
    return {"status": await db.add_new_reception(data)}


@router.post("/return_reception")
async def return_reception(data: ReturnID):
    return {"data": await db.return_reception(data.id)}


@router.post("/add_tg_id")
async def add_tg_id(data: TG_id):
    return {"data": await db.add_tg_id(data.email, data.id_tg)}


@router.get("/get_message")
async def get_message():
    temp = queue_message.copy()
    queue_message.clear()
    return {"data": temp}


@router.post("/send_message")
async def send_message(data: TG_message):
    queue_message.append([data.id_tg, data.message])
    return {"status": "ok"}


@router.get("/get_table_people")
async def get_table_people(response: Response):
    temp = await db.get_table_people()
    pd.DataFrame(temp[1:], columns=temp[0]).to_csv(
        "C:/Users/sleim/PycharmProjects/SpinaBifida/table/people.csv")

    with open("C:/Users/sleim/PycharmProjects/SpinaBifida/table/people.csv", "r", encoding="utf-8") as csv_data:
        response.headers["Content-Disposition"] = "attachment; filename=people.csv"
        response.headers["Content-Type"] = "text/csv"
        return str(csv_data.read())
