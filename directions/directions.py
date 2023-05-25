import requests
import json
import folium
import datetime

access_token = "pk.eyJ1IjoiYWdvcmFhdmVpcm8iLCJhIjoiY2trbmNoeXd5MXN2cTJudGRodzhjbjR6bSJ9.dvGHDz58mhv1i46hWJvEtQ"

# Coordinates of all points
p1  = p25 = [40.637950450148810, -8.643881276054529]    # Start point is the same as the end point
p2  = [40.630597634559855, -8.653586106799972]
p3  = [40.644325583333085, -8.643174600153820]
p4  = None
p5  = None
p6  = None
p7  = None
p8  = None
p9  = None
p10 = None
p11 = None
p12 = None
p13 = None
p14 = None
p15 = None
p16 = None
p17 = None
p18 = None
p19 = None
p20 = None
p21 = None
p22 = None
p23 = None
p24 = None

#
# Mapbox Directions API
# https://docs.mapbox.com/api/navigation/directions/
#
# Limitations:
# - 25 total waypoints per request
# - 300 requests per minute
# - 100,000 requests per month
#

points = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16, p17, p18, p19, p20, p21, p22, p23, p24, p25]
point_strings = [f"{point[1]},{point[0]}" for point in points if point is not None]
points_url = ";".join(point_strings)

request_url = f"https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{points_url}?geometries=geojson&overview=full&access_token={access_token}"

response = requests.get(request_url)

data = json.loads(response.text)

if response.status_code != 200 or not data["routes"]:
    print("\nERROR:", data["message"])
    exit()

route_geometry = data["routes"][0]["geometry"]["coordinates"]
route_geometry = [[lon, lat] for lat, lon in route_geometry]

route_distance = round(data["routes"][0]["distance"] / 1000, 2)

route_duration = str(datetime.timedelta(seconds=round(data["routes"][0]["duration"])))

print("\n - Distance:", route_distance, "km")
print("\n - ETA:", route_duration)
print("\n - Route:", route_geometry)

route_map = folium.Map(tiles="cartodb positron")
route_map.fit_bounds(points)

folium.Marker(p1, popup=folium.Popup(html="<center>Start/end point</center>", show=True, sticky=True)).add_to(route_map)

for index, point in enumerate(points):
    if point == p1 or point == p25:
        continue
    if point is not None:
        folium.Marker(point, popup=folium.Popup(html=f"<center>Container #{index}</center>", show=True, sticky=True)).add_to(route_map)

folium.PolyLine(route_geometry, popup=folium.Popup(html=f"<b>Distance:</b> {route_distance} km<br><b>ETA:</b> {route_duration}", show=True, sticky=True), weight=2, color="#FF0000").add_to(route_map)
route_map.save("route_map.html")

print("\nSUCCESS: Map saved to route_map.html")