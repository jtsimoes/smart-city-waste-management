import json
import paho.mqtt.client as mqtt
import threading
import time
import math
import os

# Fill percentage at which the garbage container is considered full and needs to be emptied
WARNING_PERCENTAGE = 70

# Limit percentage of the total number of garbage containers that can be assigned to a single truck
THRESHOLD_PERCENTAGE = 75

threshold = THRESHOLD_PERCENTAGE / 100

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

# Count the number of garbage containers assigned to each truck
truck_assigned_garbage_counts = [
    0,
    0,
    0,
]

# Count the total number of garbage containers assigned to all trucks
total_assigned_garbage_count = 0

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    print()
    client.subscribe("vanetza/out/cam")


def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode('utf-8'))

    with open(f"../dashboard/static/out_cam_obu{message['stationID']}.json", "w") as file:
        json.dump(message, file)
    
    print(f"Message received in the topic: {msg.topic}")
    #print(f"Message: {message}")

    print(f"Truck id: #{message['stationID']}")
    print(f"Truck coordinates: {(message['latitude'], message['longitude'])}")
    print()

    # Update truck current position
    truck_positions[int(message["stationID"]) - 1] = [message["latitude"], message["longitude"]]


def generate(garbage_id, latitude, longitude):
    f = open('in_denm.json')
    m = json.load(f)
    m["management"]["actionID"]["originatingStationID"] = garbage_id + 1
    m["management"]["eventPosition"]["latitude"] = latitude
    m["management"]["eventPosition"]["longitude"] = longitude
    m["situation"]["eventType"]["causeCode"] = 50

    # Set initial minimum distance to infinity
    min_distance = float("inf")

    # Find the nearest truck to collect garbage
    for (truck_id, truck_position) in enumerate(truck_positions):
        global truck_assigned_garbage_counts, total_assigned_garbage_count

        lat, lon = truck_position[0], truck_position[1]

        # Don't generate a DENM message if the truck position is unknown
        if lat == None or lon == None:
            return False

        # If the truck is already assigned to too many garbage containers, assign it to the next nearest one
        if(truck_assigned_garbage_counts[truck_id] > total_assigned_garbage_count * threshold):
            continue

        distance = math.dist((latitude, longitude), (lat, lon))
        
        if distance < min_distance:
            min_distance = distance
            nearest_truck = truck_id + 1

    m["situation"]["eventType"]["subCauseCode"] = nearest_truck

    # Add one more garbage container to the count of the truck that was assigned to collect it
    truck_assigned_garbage_counts[nearest_truck - 1] += 1

    # Add one more garbage container to the total count
    total_assigned_garbage_count += 1

    m = json.dumps(m)
    client.publish("vanetza/in/denm", m)
    #print("publishing")
    f.close()
    return True

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.98.10", 1883, 60)

threading.Thread(target=client.loop_forever).start()

while True:
    # Read all sensor data and check if any garbage container is (almost) full
    with open("../sensor/sensor_data.txt", "r") as file:
        data = file.readlines()

    for (sensor_id, fill_percentage) in enumerate(data):

        if int(fill_percentage) > WARNING_PERCENTAGE:
            # If container is (almost) full, generate a DENM message
            if generate(sensor_id, GARBAGE_COORDINATES[sensor_id][0], GARBAGE_COORDINATES[sensor_id][1]):
                # If a DENM message was generated, reset the fill percentage of that garbage container
                data[sensor_id] = "0\n"
                data[-1] = data[-1].strip("\n")
                with open("../sensor/sensor_data.txt", "w") as file:
                    file.writelines(data)
            else:
                # If no DENM message was generated, wait for trucks to join the network
                print("Currently there are no trucks to collect the garbage.")

            time.sleep(0.3)
