import json
import paho.mqtt.client as mqtt
import threading
import time
import requests
import datetime

# Mapbox Directions API access token
ACCESS_TOKEN = "pk.eyJ1IjoiYWdvcmFhdmVpcm8iLCJhIjoiY2trbmNoeXd5MXN2cTJudGRodzhjbjR6bSJ9.dvGHDz58mhv1i46hWJvEtQ"

# Flag to check if the truck is currently going to a garbage container or not
on_mission = False

def draw_route(*points):
    #
    # Mapbox Directions API
    # https://docs.mapbox.com/api/navigation/directions/
    #
    # Limitations:
    # - 25 total waypoints per request
    # - 300 requests per minute
    # - 100,000 requests per month
    #

    print("NUMBER OF POINTS: " + len(points))

    if len(points) > 25:
        print("\nERROR: You can only request directions for up to 25 points at a time.")
        exit()

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

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/denm")
    #client.subscribe("vanetza/in/cam")


# É chamada automaticamente sempre que recebe uma mensagem nos tópicos subscritos em cima
def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode('utf-8'))
    
    print('Topic: ' + msg.topic)
    print('Message' + str(message))

    # lat = message["latitude"]
    assigned_truck = message["fields"]["denm"]["situation"]["eventType"]["subCauseCode"]
    latitude = message["fields"]["denm"]["management"]["eventPosition"]["latitude"]
    longitude = message["fields"]["denm"]["management"]["eventPosition"]["longitude"]
    
    # check if DENM is for this truck or not
    if assigned_truck == client:
        global on_mission
        on_mission = True
        # ...
        # go to the garbage container
        # ...
        # when the truck arrives at the garbage container
        #on_mission = False
        # ...
        # send a new DENM to the RSU
        # ...
        # wait for the next DENM

        print(assigned_truck)
        print(latitude)
        print(longitude)


def generate(client, station_id, latitude, longitude):
    f = open("./vanetza/examples/in_cam.json")
    m = json.load(f)
    m["stationID"] = station_id
    m["latitude"] = latitude
    m["longitude"] = longitude
    m = json.dumps(m)
    client.publish("vanetza/in/cam",m)
    print("publishing")
    #print(m)
    f.close()
    time.sleep(1)

client1 = mqtt.Client()
client1.on_connect = on_connect
client1.on_message = on_message
client1.connect("192.168.98.20", 1883, 60)

#client2 = mqtt.Client()
#client2.on_connect = on_connect
#client2.on_message = on_message
#client2.connect("192.168.98.30", 1883, 60)

#client3 = mqtt.Client()
#client3.on_connect = on_connect
#client3.on_message = on_message
#client3.connect("192.168.98.40", 1883, 60)

threading.Thread(target=client1.loop_forever).start()
#threading.Thread(target=client2.loop_forever).start()
#threading.Thread(target=client3.loop_forever).start()


DEFAULT_ROUTE = [
    [-8.641142, 40.644069],
    [-8.641183, 40.644128],
    [-8.641241, 40.644144],
    [-8.64134, 40.644141],
    [-8.64148, 40.644113],
    [-8.641896, 40.64403],
    [-8.643119, 40.643783],
    [-8.643253, 40.643753],
    [-8.643444, 40.643706],
    [-8.643518, 40.643679],
    [-8.644, 40.643577],
    [-8.644059, 40.643545],
    [-8.64425, 40.643513],
    [-8.644824, 40.643411],
    [-8.644933, 40.643392],
    [-8.645092, 40.64336],
    [-8.645453, 40.643286],
    [-8.645899, 40.643199],
    [-8.646026, 40.643126],
    [-8.646486, 40.643038],
    [-8.646522, 40.643023],
    [-8.646542, 40.643005],
    [-8.646545, 40.642998],
    [-8.646581, 40.642921],
    [-8.646581, 40.642921],
    [-8.64489, 40.643269],
    [-8.644656, 40.643309],
    [-8.64435, 40.64337],
    [-8.644209, 40.643396],
    [-8.644063, 40.643433],
    [-8.643823, 40.643481],
    [-8.643489, 40.643537],
    [-8.643349, 40.643553],
    [-8.643184, 40.643571],
    [-8.643075, 40.643593],
    [-8.641978, 40.643813],
    [-8.641882, 40.643833],
    [-8.641426, 40.643925],
    [-8.641274, 40.643955],
    [-8.641187, 40.643985],
    [-8.641158, 40.644018],
    [-8.641142, 40.644069]
]

while(True):

    # Truck is not on a mission, so it is driving around on the default route
    if on_mission == False:
        for waypoint in DEFAULT_ROUTE:

            if on_mission == True:
                # Truck received a DENM message and needs to interrupt the default route to go to a garbage container
                break

            # Continue driving on the default route
            print("Truck is driving on the default route")
            generate(client1, "obu1", waypoint[1], waypoint[0])
            #generate(client2)
            #generate(client3)
    else:
        print("Truck is on a mission to a garbage container")
        exit()  
