import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException

import json
import requests
import datetime
import os
import time

app = FastAPI(title="Smart City Waste Management", version="1.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Get coordinates of all garbage containers
path = '../sensor/sensor_position.json'
if not os.path.isfile(path):
    raise FileNotFoundError("Garbage container coordinates file not found!")

with open(path, "r") as file:
    sensor_positions = json.load(file)

GARBAGE_COORDINATES = sensor_positions['positions']

# Delete previous OBU positions, if any
if os.path.exists("static/out_cam_obu1.json"):
    os.remove("static/out_cam_obu1.json")
if os.path.exists("static/out_cam_obu2.json"):
    os.remove("static/out_cam_obu2.json")
if os.path.exists("static/out_cam_obu3.json"):
    os.remove("static/out_cam_obu3.json")

# Delete previous OBU routes, if any
if os.path.exists("static/route_obu1.json"):
    os.remove("static/route_obu1.json")
if os.path.exists("static/route_obu2.json"):
    os.remove("static/route_obu2.json")
if os.path.exists("static/route_obu3.json"):
    os.remove("static/route_obu3.json")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "garbage_coordinates": GARBAGE_COORDINATES})


@app.get("/truck/{truck_id}")
async def truck(truck_id: int):

    path = f'static/out_cam_obu{truck_id}.json'
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(path) as out_cam:
        data = json.load(out_cam)

    latitude = data['latitude']
    longitude = data['longitude']

    return {"id": truck_id, "latitude": latitude, "longitude": longitude}


@app.get("/garbage")
async def garbage():

    path = '../sensor/sensor_data.txt'
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(path) as sensor_data:
        data = sensor_data.readlines()

    for (garbage_id, fill_percentage) in enumerate(data):
        data[garbage_id] = {"garbage_id": garbage_id +
                            1, "fill_percentage": int(fill_percentage)}

    return data


@app.get("/route/{route_id}")
async def route(route_id: int):

    path = f'static/route_obu{route_id}.json'
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(path) as route:
        data = json.load(route)

    return {"geometry": data['geometry'], "distance": data['distance'], "duration": data['duration']}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=81)
