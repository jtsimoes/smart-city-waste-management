# Smart City Waste Management
Final project for the subject of [Autonomous Networks and Systems](https://www.ua.pt/en/uc/15279) of the [University of Aveiro](https://www.ua.pt/).

## About

This project aims to implement an **autonomous waste management system**, where garbage containers are monitored by sensors and the routes of the different garbage trucks are optimized in real-time by an algorithm, instead of being the same every day.

This allows garbage trucks to be more efficient and reduce the time spent on the road, as well as the fuel consumption and the CO2 emissions.

## Dependencies

- [Docker](https://docs.docker.com/engine/install/ubuntu/)

- [NAP-Vanetza](https://code.nap.av.it.pt/mobility-networks/vanetza)

- Internet connection for [Mapbox Directions API](https://docs.mapbox.com/api/navigation/directions/) calls

- Python packages on `requirements.txt` (using the command `pip3 install -r requirements.txt`)


## Installation

### Vanetza containers

To start all docker containers of Vanetza, open a terminal window on the root of this project and run the following commands:

```
cd script
sudo docker-compose up --build
```

Do not close this terminal window.

### Dashboard

To start the dashboard, open a new terminal and run the following commands:

```
cd dashboard
python3 main.py
```

Do not close this terminal window. The dashboard server should be running on `http://localhost:8000/`.

### OBU script

To start the OBU script, open a new terminal and run the following commands:

```
cd script
python3 obu.py
```

Do not close this terminal window.

### RSU script

To start the RSU script, open a new terminal and run the following commands:

```
cd script
python3 rsu.py
```

Do not close this terminal window.

### Sensor simulator

To start the sensor simulator, open a new terminal and run the following commands:

```
cd sensor
python3 sensor_simulator.py
```

As soon as the garbage containers start filling up, the trucks will start moving to them and their routes will appear on the dashboard map.

## Configuration

Some parameters of this project can be modified, namely:

- Number of gargabe containers and its respective position

    - defined on the [`sensor/sensor_position.json` file](/sensor/sensor_position.json)
    - with 30 default values

- Home (initial and final) position of each one of the garbage trucks
    
    - defined on [this lines of `script/obu.py` script](/script/obu.py#L13-L20)
    - with the default values of:
        - `[40.642050351865485, -8.646329251761603]` for truck #1 (OBU1)
        - `[40.64302876711141, -8.653112236802189]` for truck #2 (OBU2)
        - `[40.64556274792325, -8.64612107999697]` for truck #3 (OBU3)

- Fill percentage at which the garbage container is considered full and will start to publish DENM messages to be emptied

    - defined on [this line of `sensor/sensor_simulator.py` script](/sensor/sensor_simulator.py#L14) and on [this line of `script/rsu.py` script](/script/rsu.py#L9)
    - with default value of `70`%

- Initial fill percentage of the garbage containers to speed up the simulation

    - defined on [this line of `sensor/sensor_simulator.py` script](/sensor/sensor_simulator.py#L11)
    - with default value of `0`%

- Maximum threshold percentage of the total number of garbage containers that a single truck can have assigned to it, to distribute the jobs more equally between the trucks

    - defined on [this line of `script/rsu.py` script](/script/rsu.py#L12)
    - with default value of `75`%

The sensor data (garbage containers fill percentage) can also be changed in real-time manually, by changing the respective line on the [`sensor/sensor_data.txt` file](/sensor/sensor_data.txt), instead of using the sensor simulator script.