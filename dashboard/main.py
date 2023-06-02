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

GARBAGE_COORDINATES = [
    [40.6420268056196, -8.651936077164848],
    [40.64232528533871, -8.650319976735206],
    [40.64318475562894, -8.64835790759189],
    [40.64396869795805, -8.648609090356615],
    [40.643975890057774, -8.647026165011145],
    [40.643134410404926, -8.648936101882537],
    [40.643307022480656, -8.650936085405435],
    [40.6431164299547, -8.64649536369701],
    [40.643817663924374, -8.64685555030303],
    [40.64398667818958, -8.646931379062192],
    [40.64408017525881, -8.648301036024554],
    [40.64390396913453, -8.650073533269968],
    [40.6418757671792, -8.64964699649913],
    [40.642138286151095, -8.648253643049527],
    [40.64254105297752, -8.648059331854173],
    [40.6414586116266, -8.647793931198219],
    [40.64264534042641, -8.646580671051627],
    [40.64482455111141, -8.648154117804625],
    [40.64444337418198, -8.649381595843558],
    [40.64422042062351, -8.649030887832755],
    [40.641864978713606, -8.648154117806273],
    [40.6420339979234, -8.647087775880557],
    [40.64238641958003, -8.650277323062811],
    [40.64286829924738, -8.651068785735958],
    [40.644937323766214, -8.647352861401957],
    [40.64377753669243, -8.647725247479249],
    [40.64468434076897, -8.648903026700445],
    [40.64482233161361, -8.6481409342632],
    [40.64457263368578, -8.647205638999306],
    [40.642739296607445, -8.647339871189958],
]


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "garbage_coordinates": GARBAGE_COORDINATES})


@app.get("/truck")
async def truck():

    path = 'static/out_cam_obu1.json'
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(path) as out_cam:
        data = json.load(out_cam)

    #latitude = data['fields']['cam']['camParameters']['basicContainer']['referencePosition']['latitude']
    #longitude = data['fields']['cam']['camParameters']['basicContainer']['referencePosition']['longitude']
    latitude = data['latitude']
    longitude = data['longitude']

    return {"id": 1, "latitude": latitude, "longitude": longitude}


@app.get("/garbage")
async def garbage():

    with open('../sensor/sensor_data.txt') as sensor_data:
        data = sensor_data.readlines()

    for (garbage_id, fill_percentage) in enumerate(data):
        data[garbage_id] = {"garbage_id": garbage_id +
                            1, "fill_percentage": int(fill_percentage)}

    return data


if __name__ == "__main__":
    # TODO: using 'reload=True' for development environment only, remove for production
    uvicorn.run("main:app", host="127.0.0.1", port=81, reload=True)
