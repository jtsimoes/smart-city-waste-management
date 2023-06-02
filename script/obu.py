import json
import paho.mqtt.client as mqtt
import threading
import time
import requests
import datetime
import math

# Mapbox Directions API access token
ACCESS_TOKEN = "pk.eyJ1IjoiYWdvcmFhdmVpcm8iLCJhIjoiY2trbmNoeXd5MXN2cTJudGRodzhjbjR6bSJ9.dvGHDz58mhv1i46hWJvEtQ"

# Default route for the truck #1
DEFAULT_ROUTE_TRUCK1 = [
    [40.644069, -8.641142],
    [40.644128, -8.641183],
    [40.644144, -8.641241],
    [40.644141, -8.64134],
    [40.644113, -8.64148],
    [40.64403,  -8.641896],
    [40.643783, -8.643119],
    [40.643753, -8.643253],
    [40.643706, -8.643444],
    [40.643679, -8.643518],
    [40.643577, -8.644],
    [40.643545, -8.644059],
    [40.643513, -8.64425,],
    [40.643411, -8.644824],
    [40.643392, -8.644933],
    [40.64336, -8.645092],
    [40.643286, -8.645453],
    [40.643199, -8.645899],
    [40.643126, -8.646026],
    [40.643038, -8.646486],
    [40.643023, -8.646522],
    [40.643005, -8.646542],
    [40.642998, -8.646545],
    [40.642921, -8.646581],
    [40.642921, -8.646581],
    [40.643269, -8.64489],
    [40.643309, -8.644656],
    [40.64337, -8.64435],
    [40.643396, -8.644209],
    [40.643433, -8.644063],
    [40.643481, -8.643823],
    [40.643537, -8.643489],
    [40.643553, -8.643349],
    [40.643571, -8.643184],
    [40.643593, -8.643075],
    [40.643813, -8.641978],
    [40.643833, -8.641882],
    [40.643925, -8.641426],
    [40.643955, -8.641274],
    [40.643985, -8.641187],
    [40.644018, -8.641158],
    [40.64406, -8.6411429]
]

# Default route for the truck #2
DEFAULT_ROUTE_TRUCK2 = [
    [40.643709, -8.652005],
    [40.643701, -8.652038],
    [40.643546, -8.652467],
    [40.64343, -8.652785],
    [40.64317, -8.652661],
    [40.643112, -8.652647],
    [40.643069, -8.652657],
    [40.642901, -8.652736],
    [40.6428, -8.652335],
    [40.642791, -8.652239],
    [40.642803, -8.65213,],
    [40.642932, -8.65186,],
    [40.642975, -8.651725],
    [40.643018, -8.651629],
    [40.643032, -8.651597],
    [40.643098, -8.651446],
    [40.64322, -8.651169],
    [40.643242, -8.651121],
    [40.643278, -8.651042],
    [40.643329, -8.65111,],
    [40.643421, -8.651163],
    [40.643892, -8.651455],
    [40.643847, -8.65158,],
    [40.643733, -8.651903],
    [40.64371, -8.652001]
]

# Default route for the truck #3
DEFAULT_ROUTE_TRUCK3 = [
    [40.644186, -8.649034],
    [40.644153, -8.649086],
    [40.644146, -8.649099],
    [40.644047, -8.649256],
    [40.644019, -8.649295],
    [40.644003, -8.649307],
    [40.643989, -8.649314],
    [40.643984, -8.649316],
    [40.643978, -8.649317],
    [40.643972, -8.649316],
    [40.643966, -8.649316],
    [40.643959, -8.649315],
    [40.643954, -8.649314],
    [40.643947, -8.649311],
    [40.643866, -8.649237],
    [40.643858, -8.649223],
    [40.643851, -8.649205],
    [40.643848, -8.649182],
    [40.643847, -8.649155],
    [40.643861, -8.649127],
    [40.643891, -8.649001],
    [40.643943, -8.648765],
    [40.643972, -8.648629],
    [40.643998, -8.648502],
    [40.644016, -8.648412],
    [40.644033, -8.648355],
    [40.644057, -8.648325],
    [40.644073, -8.648312],
    [40.644106, -8.648312],
    [40.644152, -8.648329],
    [40.644355, -8.648403],
    [40.644379, -8.648421],
    [40.644393, -8.648449],
    [40.644398, -8.648486],
    [40.644338, -8.648794],
    [40.644326, -8.648813],
    [40.644284, -8.648881],
    [40.644245, -8.648941],
    [40.644234, -8.648959],
    [40.644186, -8.649033]
]

# Array containing the queue of garbage containers to be emptied by each truck
queue_truck1 = []
queue_truck2 = []
queue_truck3 = []

# Array containing the current route that each truck is following
current_route_truck1 = []
current_route_truck2 = []
current_route_truck3 = []

# Flag to indicate if the truck needs to recalculate the route because of a alteration in the queue order
need_route_recalculation_truck1 = False
need_route_recalculation_truck2 = False
need_route_recalculation_truck3 = False

# Current position of each truck
truck_positions = [
    [None, None],
    [None, None],
    [None, None],
]


# Sort the garbage containers by distance to the truck
def sort_by_distance(queue, truck_position):
    return sorted(queue, key=lambda x: math.dist(x, truck_position))


# Draw the route between the truck and the next garbage container(s)
def draw_route(points, route_id):
    #
    # Mapbox Directions API
    # https://docs.mapbox.com/api/navigation/directions/
    #
    # Limitations:
    # - 25 total waypoints per request
    # - 300 requests per minute
    # - 100,000 requests per month
    #

    print(f"NUMBER OF POINTS: {len(points)}")
    print(f"POINTS: {points}")

    if len(points) < 2:     # TODO: check
        return points

    if len(points) > 25:
        print("\nERROR: You can only request directions for up to 25 points at a time.")
        exit()

    point_strings = [
        f"{point[1]},{point[0]}" for point in points if point is not None]
    points_url = ";".join(point_strings)

    print(f"POINTS URL: {points_url}")

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

    with open(f"../dashboard/static/route_obu{route_id}.json", "w") as file:
        json.dump({"geometry": route_geometry}, file)

    # return {"distance": route_distance, "duration": route_duration, "geometry": route_geometry}
    print(f"\n\n\nGENERATED ROUTE FOR TRUCK #{route_id}\n\n\n")
    return route_geometry


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/denm")


def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode('utf-8'))

    print('Topic: ' + msg.topic)
    print('Message' + str(message))

    assigned_truck = message["fields"]["denm"]["situation"]["eventType"]["subCauseCode"]
    truck_id = message["receiverID"]

    # check if DENM is for this truck or not
    if assigned_truck == truck_id:
        latitude = message["fields"]["denm"]["management"]["eventPosition"]["latitude"]
        longitude = message["fields"]["denm"]["management"]["eventPosition"]["longitude"]

        global queue_truck1, queue_truck2, queue_truck3
        global need_route_recalculation_truck1, need_route_recalculation_truck2, need_route_recalculation_truck3

        # append the garbage container to the queue
        if truck_id == 1:
            queue_truck1.append([latitude, longitude])
        elif truck_id == 2:
            queue_truck2.append([latitude, longitude])
        elif truck_id == 3:
            queue_truck3.append([latitude, longitude])

        # sort the queue by distance to the truck and recalculate the route if needed
        if truck_id == 1:
            if queue_truck1 != sort_by_distance(queue_truck1, truck_positions[0]):
                queue_truck1 = sort_by_distance(
                    queue_truck1, truck_positions[0])
                need_route_recalculation_truck1 = True

        elif truck_id == 2:
            if queue_truck2 != sort_by_distance(queue_truck2, truck_positions[1]):
                queue_truck2 = sort_by_distance(
                    queue_truck2, truck_positions[1])
                need_route_recalculation_truck2 = True

        elif truck_id == 3:
            if queue_truck3 != sort_by_distance(queue_truck3, truck_positions[2]):
                queue_truck3 = sort_by_distance(
                    queue_truck3, truck_positions[2])
                need_route_recalculation_truck3 = True


def generate(client, station_id, latitude, longitude):
    f = open("./vanetza/examples/in_cam.json")
    m = json.load(f)
    m["stationID"] = station_id
    m["latitude"] = latitude
    m["longitude"] = longitude
    m = json.dumps(m)
    client.publish("vanetza/in/cam", m)
    # Update the current position of the truck
    truck_positions[station_id - 1] = [latitude, longitude]
    #print("publishing")
    # print(m)
    f.close()
    time.sleep(0.3)


client1 = mqtt.Client()
client1.on_connect = on_connect
client1.on_message = on_message
client1.connect("192.168.98.20", 1883, 60)

client2 = mqtt.Client()
client2.on_connect = on_connect
client2.on_message = on_message
client2.connect("192.168.98.30", 1883, 60)

client3 = mqtt.Client()
client3.on_connect = on_connect
client3.on_message = on_message
client3.connect("192.168.98.40", 1883, 60)

threading.Thread(target=client1.loop_forever).start()
threading.Thread(target=client2.loop_forever).start()
threading.Thread(target=client3.loop_forever).start()

step_truck1 = 0
step_truck2 = 0
step_truck3 = 0

while (True):

    ##### TRUCK #1 #####
    if not queue_truck1:
        # Truck don't have any garbage container assigned to it, so it can follow the default route
        print("Truck is driving on the default route")
        if step_truck1 < len(DEFAULT_ROUTE_TRUCK1):
            waypoint = DEFAULT_ROUTE_TRUCK1[step_truck1]
            step_truck1 += 1
        else:
            step_truck1 = 0
    else:
        # Truck received a DENM message and needs to interrupt the default route to go empty a garbage container
        print("Truck #1 is on a mission to a garbage container!!!")
        if not current_route_truck1 or need_route_recalculation_truck1:
            current_route_truck1 = draw_route(queue_truck1, "1")

        waypoint = current_route_truck1.pop(0)

    generate(client1, 1, waypoint[0], waypoint[1])

    ##### TRUCK #2 #####
    if not queue_truck2:
        if step_truck2 < len(DEFAULT_ROUTE_TRUCK2):
            waypoint = DEFAULT_ROUTE_TRUCK2[step_truck2]
            step_truck2 += 1
        else:
            step_truck2 = 0
    else:
        print("Truck #2 is on a mission to a garbage container!!!")
        if not current_route_truck2 or need_route_recalculation_truck2:
            current_route_truck2 = draw_route(queue_truck2, "2")

        waypoint = current_route_truck2.pop(0)

    generate(client2, 2, waypoint[0], waypoint[1])

    ##### TRUCK #3 #####
    if not queue_truck3:
        if step_truck3 < len(DEFAULT_ROUTE_TRUCK3):
            waypoint = DEFAULT_ROUTE_TRUCK3[step_truck3]
            step_truck3 += 1
        else:
            step_truck3 = 0
    else:
        print("Truck #3 is on a mission to a garbage container!!!")
        if not current_route_truck3 or need_route_recalculation_truck3:
            current_route_truck3 = draw_route(queue_truck3, "3")

        waypoint = current_route_truck3.pop(0)

    generate(client3, 3, waypoint[0], waypoint[1])
