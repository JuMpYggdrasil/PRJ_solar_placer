import folium

# Define the GPS coordinates
latitude = 13.810626620188648
longitude = 100.50678668006759

# Create a map centered at the given coordinates
mymap = folium.Map(location=[latitude, longitude], zoom_start=15)

# Add a marker at the given coordinates
folium.Marker([latitude, longitude], popup="My Location").add_to(mymap)

# Save the map to an HTML file
mymap.save("map.html")

# Display the map
mymap
