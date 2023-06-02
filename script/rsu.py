import json
import paho.mqtt.client as mqtt
import threading
import time
import math

# Fill percentage at which the garbage container is considered full and needs to be emptied
WARNING_PERCENTAGE = 70

# Total number of sensors
NUMBER_SENSORS = 7

# Coordinates of all possible garbage containers
garbage_coordinates = [
    [40.639089, -8.650802],
    [40.641669, -8.648054],
    [40.638034, -8.644034],
    [40.627141, -8.645695],
    [40.626920, -8.651401],
    [40.633373, -8.655760],
    [40.630078, -8.659179],
    [40.638556, -8.657554],
    [40.641701, -8.655609],
    [40.642703, -8.655421],
    [40.646985, -8.651289],
    [40.643648, -8.639638],
    [40.638621, -8.639318],
    [40.637050, -8.632803],
    [40.632896, -8.631251],
    [40.626729, -8.637357],
    [40.618851, -8.654700],
    [40.623699, -8.649597],
    [40.632037, -8.650261],
    [40.630318, -8.653844],
    [40.633382, -8.661360],
    [40.636627, -8.649961],
    [40.635358, -8.645863],
    [40.631908, -8.646494],
    [40.634004, -8.648422],
    [40.640516, -8.651795],
    [40.636870, -8.653476],
    [40.628768, -8.659954],
    [40.623382, -8.657870],
    [40.643800, -8.651797],
]

# List containing the most recent position of each truck
truck_positions = [
    [40.6317090, -8.6875641],
    [40.6258137, -8.6448027],
    [40.6397940, -8.6435776],
]

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam")
    #client.subscribe("vanetza/in/denm")


def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode('utf-8'))
    
    print('Topic: ' + msg.topic)
    print('Message: ' + str(message)) # json.dumps(message)
    print('Client: ' + client)

    print("Latitude: " + message["latitude"])
    print("Longitude: " + message["longitude"])
    print("Truck id: " + message["stationID"])

    truck_positions[int(message["stationID"]) - 1] = [message["latitude"], message["longitude"]]


def generate(garbage_id, latitude, longitude):
    f = open('./vanetza/examples/in_denm.json')
    m = json.load(f)
    m["management"]["actionID"]["originatingStationID"] = garbage_id
    m["management"]["eventPosition"]["latitude"] = latitude
    m["management"]["eventPosition"]["longitude"] = longitude
    #m["situation"]["eventType"]["causeCode"] = 50

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
    print("publishing")
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
            generate(sensor_id, garbage_coordinates[sensor_id][0], garbage_coordinates[sensor_id][1])

            data[sensor_id] = "0\n"
            with open("../sensor/sensor_data.txt", "w") as file:
                file.writelines(data)

            time.sleep(1)
