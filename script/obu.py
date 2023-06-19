import json
import paho.mqtt.client as mqtt
import threading
import time
import requests
import datetime
import math
import os

# Mapbox Directions API access token
ACCESS_TOKEN = "pk.eyJ1IjoiYWdvcmFhdmVpcm8iLCJhIjoiY2trbmNoeXd5MXN2cTJudGRodzhjbjR6bSJ9.dvGHDz58mhv1i46hWJvEtQ"

# Home position of the truck #1
HOME_TRUCK1 = [40.642050351865485, -8.646329251761603]  # Rotunda Monumento ao Paraquedista (https://goo.gl/maps/C5hhAGM1cUm3TDYq8)

# Home position of the truck #2
HOME_TRUCK2 = [40.64302876711141, -8.653112236802189]   # Igreja de Nossa Senhora da Apresentação (https://goo.gl/maps/L9veVFhzJ2Zi2LsG9)

# Home position of the truck #3
HOME_TRUCK3 = [40.64556274792325, -8.64612107999697]    # Guarda Nacional Republicana (https://goo.gl/maps/fL8zMy575usCnSwx8)

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

# Current position of each truck given by the CAM messages
truck_positions = [
    HOME_TRUCK1,
    HOME_TRUCK2,
    HOME_TRUCK3,
]


# Sort the garbage containers by distance to the truck
def sort_by_distance(queue, truck_position):
    return sorted(queue, key=lambda x: math.dist(x, truck_position))


# Draw the route between the truck and the next garbage container(s)
def draw_route(points, route_id, output_to_file=True):
    #
    # Mapbox Directions API
    # https://docs.mapbox.com/api/navigation/directions/
    #
    # Limitations:
    # - 25 total waypoints per request
    # - 300 requests per minute
    # - 100,000 requests per month
    #

    ### print(f"NUMBER OF POINTS: {len(points)}")
    ### print(f"POINTS: {points}")

    # add the truck position to the points array
    points.insert(0, truck_positions[int(route_id) - 1])

    point_strings = [
        f"{point[1]},{point[0]}" for point in points if point is not None]
    points_url = ";".join(point_strings)

    ### print(f"POINTS URL: {points_url}")

    request_url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{points_url}?geometries=geojson&overview=full&access_token={ACCESS_TOKEN}"
    response = requests.get(request_url)
    data = json.loads(response.text)

    if response.status_code != 200 or not data["routes"]:
        print("\n\n\nERROR:", data["message"])
        exit()

    route_geometry = data["routes"][0]["geometry"]["coordinates"]
    ### print(f"\nBEFORE: {route_geometry}\n")
    route_geometry = [[lon, lat] for lat, lon in route_geometry]
    ### print(f"\nAFTER: {route_geometry}\n")

    if output_to_file:

        route_distance = round(data["routes"][0]["distance"] / 1000, 2)

        route_duration = str(datetime.timedelta(seconds = round(data["routes"][0]["duration"])))

        # print("\n - Distance:", route_distance, "km")
        # print("\n - ETA:", route_duration)
        # print("\n - Route:", route_geometry)

        with open(f"../dashboard/static/route_obu{route_id}.json", "w") as file:
            json.dump({"geometry": route_geometry, "duration": route_duration, "distance": route_distance}, file)

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

    # print("publishing")
    f.close()


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

time.sleep(0.5)

while True:

    ##### TRUCK #1 #####
    if not queue_truck1 and not current_route_truck1:
        # Truck don't have any garbage container assigned to it, so it can go/stay at home
        if math.dist(HOME_TRUCK1, truck_positions[0]) < 0.0001:
            # Truck is already at home, can stay in the same position
            waypoint = HOME_TRUCK1
            print("Truck #1 is at home waiting for a mission")
        else:
            # Truck is not at home yet, needs to generate a route to go back home
            queue_truck1 = [HOME_TRUCK1]
            current_route_truck1 = draw_route([HOME_TRUCK1], "1", False)
            waypoint = current_route_truck1.pop(0)
            print("Truck #1 is going home")
    else:
        # Truck received a DENM message and needs to interrupt the default route to go empty a garbage container
        print("Truck #1 is on the road!!!")
        print(len(current_route_truck1))
        print(need_route_recalculation_truck1)
        if not current_route_truck1 or need_route_recalculation_truck1:
            need_route_recalculation_truck1 = False
            current_route_truck1 = draw_route(queue_truck1, "1")

        waypoint = current_route_truck1.pop(0)

        if not current_route_truck1:
            print("\nTruck #1 finished route\n")
            # Route is finished, clear all the garbage containers from the queue
            queue_truck1 = []
            # Delete truck route from the map
            if os.path.exists("../dashboard/static/route_obu1.json"):
                os.remove("../dashboard/static/route_obu1.json")

    # Publish the next move of the truck
    generate(client1, 1, waypoint[0], waypoint[1])
    time.sleep(0.3)

    ##### TRUCK #2 #####
    if not queue_truck2 and not current_route_truck2:
        # Truck don't have any garbage container assigned to it, so it can go/stay at home
        if math.dist(HOME_TRUCK2, truck_positions[1]) < 0.0001:
            # Truck is already at home, can stay in the same position
            waypoint = HOME_TRUCK2
            print("Truck #2 is at home waiting for a mission")
        else:
            # Truck is not at home yet, needs to generate a route to go back home
            queue_truck2 = [HOME_TRUCK2]
            current_route_truck2 = draw_route([HOME_TRUCK2], "2", False)
            waypoint = current_route_truck2.pop(0)
            print("Truck #2 is going home")
    else:
        print("Truck #2 is on the road!!!")
        print(len(current_route_truck2))
        print(need_route_recalculation_truck2)
        if not current_route_truck2 or need_route_recalculation_truck2:
            need_route_recalculation_truck2 = False
            current_route_truck2 = draw_route(queue_truck2, "2")

        waypoint = current_route_truck2.pop(0)

        if not current_route_truck2:
            print("\nTruck #2 finished route\n")
            # Route is finished, clear all the garbage containers from the queue
            queue_truck2 = []
            # Delete truck route from the map
            if os.path.exists("../dashboard/static/route_obu2.json"):
                os.remove("../dashboard/static/route_obu2.json")

    # Publish the next move of the truck
    generate(client2, 2, waypoint[0], waypoint[1])
    time.sleep(0.3)

    ##### TRUCK #3 #####
    if not queue_truck3 and not current_route_truck3:
        # Truck don't have any garbage container assigned to it, so it can go/stay at home
        if math.dist(HOME_TRUCK3, truck_positions[2]) < 0.0001:
            # Truck is already at home, can stay in the same position
            waypoint = HOME_TRUCK3
            print("Truck #3 is at home waiting for a mission")
        else:
            # Truck is not at home yet, needs to generate a route to go back home
            queue_truck3 = [HOME_TRUCK3]
            current_route_truck3 = draw_route([HOME_TRUCK3], "3", False)
            waypoint = current_route_truck3.pop(0)
            print("Truck #3 is going home")
    else:
        print("Truck #3 is on the road!!!")
        print(len(current_route_truck3))
        print(need_route_recalculation_truck3)
        if not current_route_truck3 or need_route_recalculation_truck3:
            need_route_recalculation_truck3 = False
            current_route_truck3 = draw_route(queue_truck3, "3")

        waypoint = current_route_truck3.pop(0)

        if not current_route_truck3:
            print("\nTruck #3 finished route\n")
            # Route is finished, clear all the garbage containers from the queue
            queue_truck3 = []
            # Delete truck route from the map
            if os.path.exists("../dashboard/static/route_obu3.json"):
                os.remove("../dashboard/static/route_obu3.json")

    # Publish the next move of the truck
    generate(client3, 3, waypoint[0], waypoint[1])
    time.sleep(0.3)
    print()
