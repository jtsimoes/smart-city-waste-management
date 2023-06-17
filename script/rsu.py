import json
import paho.mqtt.client as mqtt
import threading
import time
import math
import os

# Fill percentage at which the garbage container is considered full and needs to be emptied
WARNING_PERCENTAGE = 70

# Get coordinates of all garbage containers
path = '../sensor/sensor_position.json'
if not os.path.isfile(path):
    raise FileNotFoundError("Garbage container coordinates file not found!")

with open(path, "r") as file:
    sensor_positions = json.load(file)

GARBAGE_COORDINATES = sensor_positions['positions']

# List containing the most recent position of each truck
truck_positions = [
    [None, None],
    [None, None],
    [None, None],
]

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam")


def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode('utf-8'))

    with open(f"../dashboard/static/out_cam_obu{message['stationID']}.json", "w") as file:
        json.dump(message, file)
    
    print('Topic: ' + msg.topic)
    print('Message: ' + str(message)) # json.dumps(message)

    print(f"Latitude: " + str(message["latitude"]))
    print(f"Longitude: " + str(message["longitude"]))
    print(f"Truck id: " + str(message["stationID"]))

    truck_positions[int(message["stationID"]) - 1] = [message["latitude"], message["longitude"]]


def generate(garbage_id, latitude, longitude):
    f = open('./vanetza/examples/in_denm.json')
    m = json.load(f)
    m["management"]["actionID"]["originatingStationID"] = garbage_id
    m["management"]["eventPosition"]["latitude"] = latitude
    m["management"]["eventPosition"]["longitude"] = longitude
    m["situation"]["eventType"]["causeCode"] = 50

    # Set initial minimum distance to infinity
    min_distance = float("inf")

    # Find the nearest truck to collect garbage
    for (truck_id, truck_position) in enumerate(truck_positions):
        lat, lon = truck_position[0], truck_position[1]
        distance = math.dist((latitude, longitude), (lat, lon))
        
        if distance < min_distance:
            min_distance = distance
            nearest_truck = truck_id + 1

    m["situation"]["eventType"]["subCauseCode"] = nearest_truck

    m = json.dumps(m)
    client.publish("vanetza/in/denm", m)
    #print("publishing")
    f.close()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.98.10", 1883, 60)

threading.Thread(target=client.loop_forever).start()

while(True):
    # read file and check if container is full
    with open("../sensor/sensor_data.txt", "r") as file:
        data = file.readlines()

    for (sensor_id, fill_percentage) in enumerate(data):

        if int(fill_percentage) > WARNING_PERCENTAGE:
            # Generate denm
            generate(sensor_id, GARBAGE_COORDINATES[sensor_id][0], GARBAGE_COORDINATES[sensor_id][1])

            data[sensor_id] = "0\n"
            data[-1] = data[-1].strip("\n")
            with open("../sensor/sensor_data.txt", "w") as file:
                file.writelines(data)

            time.sleep(0.3)
