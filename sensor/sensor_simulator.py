import random
import time
import os
import json


# Max capacity of the garbage container
MAX_CAPACITY = 100

# Initial fill percentage of the garbage container
INITIAL_PERCENTAGE = 0

# Fill percentage at which the garbage container is considered full and needs to be emptied
WARNING_PERCENTAGE = 70

# Get total number of sensors on garbage containers
path = 'sensor_position.json'
if not os.path.isfile(path):
    raise FileNotFoundError("Garbage container coordinates file not found!")

with open(path, "r") as file:
    sensor_positions = json.load(file)

NUMBER_SENSORS = len(sensor_positions['positions'])


# Create a list of initial fill percentages for all sensors
data = [str(INITIAL_PERCENTAGE) + "\n"] * NUMBER_SENSORS

# Remove the newline character from the last element to prevent an empty line at the end of the file
data[-1] = data[-1].strip("\n")

# Reset old sensor data
with open("sensor_data.txt", "w") as file:
    file.writelines(data)

while True:

    # Read current fill percentage of all sensors from sensor data file
    with open(f"sensor_data.txt", "r") as file:
        data = file.readlines()

    for (sensor_id, fill_percentage) in enumerate(data):

        fill_percentage = int(fill_percentage)

        if fill_percentage > WARNING_PERCENTAGE:
            # Maximum rate at which the container can be filled per iteration
            # Slower fill rate while the garbage container is full or almost full
            max_fill_rate = 2
            print(f"\033[93mGarbage container #{sensor_id + 1} needs to be emptied!\033[0m")
        else:
            # Faster fill rate while the garbage container is less full than the chosen warning percentage
            max_fill_rate = 30

        # Randomly generate a fill rate for the garbage container
        fill_rate = random.uniform(0, max_fill_rate)
        fill_percentage += fill_rate

        if fill_percentage > MAX_CAPACITY:
            # Prevent the garbage container from overflowing when completely full
            fill_percentage = MAX_CAPACITY
            print(f"\033[1m\033[91mGarbage container #{sensor_id + 1} is completely full!\033[0m")

        fill_percentage = round(fill_percentage)

        # print(f"Sensor #{sensor_id + 1} fill percentage: {fill_percentage}%")

        data[sensor_id] = str(fill_percentage) + "\n"

    # Remove the newline character from the last element to prevent an empty line at the end of the file
    data[-1] = data[-1].strip("\n")

    # Write new fill percentages to the sensor data file
    with open("sensor_data.txt", "w") as file:
        file.writelines(data)

    print("Sensor data updated.")

    # Simulate some delay between fill iterations
    time.sleep(15)
