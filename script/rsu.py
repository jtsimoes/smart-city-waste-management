import json
import paho.mqtt.client as mqtt
import threading
import time
import math

# Fill percentage at which the garbage container is considered full and needs to be emptied
WARNING_PERCENTAGE = 70

# Total number of sensors
NUMBER_SENSORS = 7

garbage_coordinates = [
    (40.631709, -8.6875641),
    (40.6258137, -8.6448027),
    (40.639794, -8.6435776),
    (40.621431, -8.6291841),
    (40.6669451, -8.6258256),
    (40.6451389, -8.6435942),
    (40.6327564, -8.6374649),
]

truck_positions = [
    [40.6317090, -8.6875641],
    [40.6258137, -8.6448027],
    [40.6397940, -8.6435776],
]

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam")
    #client.subscribe("vanetza/in/denm")


# É chamada automaticamente sempre que recebe uma mensagem nos tópicos subscritos em cima
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
            with open("sensor_data.txt", "w") as file:
                file.writelines(data)

            time.sleep(1)
