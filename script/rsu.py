import json
import paho.mqtt.client as mqtt
import threading
import time
import math

# Fill percentage at which the garbage container is considered full and needs to be emptied
WARNING_PERCENTAGE = 70

# Coordinates of all garbage containers
GARBAGE_COORDINATES = [
    [40.6420268056196, -8.651936077164848],
    [40.64318475562894, -8.64835790759189],
    [40.64396869795805, -8.648609090356615],
    [40.643134410404926, -8.648936101882537],
    [40.643307022480656, -8.650936085405435],
    [40.6431164299547, -8.64649536369701],
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
    [40.64457263368578, -8.647205638999306],
    [40.642739296607445, -8.647339871189958],
]

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
            with open("../sensor/sensor_data.txt", "w") as file:
                file.writelines(data)

            time.sleep(0.3)
