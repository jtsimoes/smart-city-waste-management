import random
import time


# Total number of sensors
NUMBER_SENSORS = 30

# Max capacity of the garbage container
MAX_CAPACITY = 100

# Initial fill percentage of the garbage container
INITIAL_PERCENTAGE = 0

# Fill percentage at which the garbage container is considered full and needs to be emptied
WARNING_PERCENTAGE = 70


# Create a list of initial fill percentages for all sensors
data = [str(INITIAL_PERCENTAGE) + "\n"] * NUMBER_SENSORS

# Remove the newline character from the last element to prevent an empty line at the end of the file
data[-1] = data[-1].strip("\n")

# Reset old sensor data
with open(f"sensor_data.txt", "w") as file:
    # for i in range(1, NUMBER_SENSORS + 1):
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
            print(f"Garbage container #{sensor_id + 1} needs to be emptied!")
        else:
            # Faster fill rate while the garbage container is less full than the chosen warning percentage
            max_fill_rate = 5

        # Randomly generate a fill rate for the garbage container
        fill_rate = random.uniform(0, max_fill_rate)
        fill_percentage += fill_rate

        if fill_percentage > MAX_CAPACITY:
            # Prevent the garbage container from overflowing when completely full
            fill_percentage = MAX_CAPACITY
            print(f"(!) GARBAGE CONTAINER #{sensor_id + 1} COMPLETLY FULL (!)")

        fill_percentage = round(fill_percentage)

        # print(f"Sensor #{sensor_id + 1} fill percentage: {fill_percentage}%")

        data[sensor_id] = str(fill_percentage) + "\n"

    # Remove the newline character from the last element to prevent an empty line at the end of the file
    data[-1] = data[-1].strip("\n")

    # Write new fill percentages to the sensor data file
    with open(f"sensor_data.txt", "w") as file:
        file.writelines(data)

    print("Sensor data updated.")

    # Simulate some delay between fill iterations
    time.sleep(3)
