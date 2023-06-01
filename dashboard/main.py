import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import json
import requests
import datetime

app = FastAPI(title="Smart City Waste Management", version="1.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/truck/{truck_id}")
async def get_truck_data(truck_id: int):

    # TODO: access out_cam.json from Docker container
    #
    # import urllib
    # out_cam = urllib.urlopen('http://ip:port/path/json')
    # data = json.load(out_cam)
    # out_cam.close()

    with open('static/out_cam.json') as out_cam:
        data = json.load(out_cam)

    latitude = data['fields']['cam']['camParameters']['basicContainer']['referencePosition']['latitude']
    longitude = data['fields']['cam']['camParameters']['basicContainer']['referencePosition']['longitude']
    state = "moving"

    print(truck_id)

    return {"id": truck_id, "latitude": latitude, "longitude": longitude, "state": state}


@app.post("/truck/{truck_id}")
async def set_truck_data(truck_id: int, latitude: float, longitude: float):

    # TODO: update out_cam.json from Docker container

    data = {
        'fields': {
            'cam': {
                'camParameters': {
                    'basicContainer': {
                        'referencePosition': {
                            'latitude': latitude,
                            'longitude': longitude
                        }
                    }
                }
            }
        }
    }

    with open('static/out_cam.json', 'w') as out_cam:
        json.dump(data, out_cam, indent=4)

    print(truck_id)

    return {"message": "Truck position updated successfully."}


@app.get("/garbage")
async def get_garbage_data():

    with open('static/out_denm.json') as out_denm:
        data = json.load(out_denm)

    latitude = data['fields']['denm']['management']['eventPosition']['latitude']
    longitude = data['fields']['denm']['management']['eventPosition']['longitude']
    percentage = data['fields']['denm']['situation']['eventType']['causeCode']

    garbage_id = None
    print(garbage_id)

    return {"id": garbage_id, "latitude": latitude, "longitude": longitude, "percentage": percentage}


@app.post("/garbage")
async def set_garbage_data():

    # with open('static/out_denm.json') as out_denm:
    #    data = json.load(out_denm)

    # latitude = data['fields']['denm']['management']['eventPosition']['latitude']
    # longitude = data['fields']['denm']['management']['eventPosition']['longitude']
    # percentage = data['fields']['denm']['situation']['eventType']['causeCode']

    # print(garbage_id)

    percentage = None

    return {"percentage": percentage}


@app.get("/route")
# async def set_route_data(p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16, p17, p18, p19, p20, p21, p22, p23, p24, p25):
async def set_route_data():

    ACCESS_TOKEN = "pk.eyJ1IjoiYWdvcmFhdmVpcm8iLCJhIjoiY2trbmNoeXd5MXN2cTJudGRodzhjbjR6bSJ9.dvGHDz58mhv1i46hWJvEtQ"

    # Coordinates of all points
    # Start point is the same as the end point
    p1 = p25 = [40.637950450148810, -8.643881276054529]
    p2 = [40.630597634559855, -8.653586106799972]
    p3 = [40.644325583333085, -8.643174600153820]
    p4 = None
    p5 = None
    p6 = None
    p7 = None
    p8 = None
    p9 = None
    p10 = None
    p11 = None
    p12 = None
    p13 = None
    p14 = None
    p15 = None
    p16 = None
    p17 = None
    p18 = None
    p19 = None
    p20 = None
    p21 = None
    p22 = None
    p23 = None
    p24 = None

    #
    # Mapbox Directions API
    # https://docs.mapbox.com/api/navigation/directions/
    #
    # Limitations:
    # - 25 total waypoints per request
    # - 300 requests per minute
    # - 100,000 requests per month
    #

    points = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13,
              p14, p15, p16, p17, p18, p19, p20, p21, p22, p23, p24, p25]
    point_strings = [
        f"{point[1]},{point[0]}" for point in points if point is not None]
    points_url = ";".join(point_strings)

    request_url = f"https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{points_url}?geometries=geojson&overview=full&access_token={ACCESS_TOKEN}"
    response = requests.get(request_url)
    data = json.loads(response.text)

    if response.status_code != 200 or not data["routes"]:
        print("\nERROR:", data["message"])
        exit()

    route_geometry = data["routes"][0]["geometry"]["coordinates"]
    route_geometry = [[lon, lat] for lat, lon in route_geometry]

    route_distance = round(data["routes"][0]["distance"] / 1000, 2)

    route_duration = str(datetime.timedelta(
        seconds=round(data["routes"][0]["duration"])))

    # print("\n - Distance:", route_distance, "km")
    # print("\n - ETA:", route_duration)
    # print("\n - Route:", route_geometry)

    # marker = folium.Marker(p1, popup=folium.Popup(html="<center>Start/end point</center>", show=True, sticky=True)).add_to(route_map)

    # for index, point in enumerate(points):
    #    if point == p1 or point == p25:
    #        continue
    #    if point is not None:
    #        folium.Marker(point, popup=folium.Popup(html=f"<center>Container #{index}</center>", show=True, sticky=True)).add_to(route_map)

    return {"distance": route_distance, "duration": route_duration, "geometry": route_geometry}


if __name__ == "__main__":
    # TODO: using 'reload=True' for development environment only, remove for production
    uvicorn.run("main:app", host="127.0.0.1", port=80, reload=True)
