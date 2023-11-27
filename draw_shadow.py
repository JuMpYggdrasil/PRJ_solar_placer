import tkinter as tk
import ephem
import math

class ShadowCalculator:
    def __init__(self, master):
        self.master = master
        self.master.title("Shadow Projector")

        self.canvas = tk.Canvas(master, width=400, height=400)
        self.canvas.pack()

        # Entry widgets for user input with default values
        tk.Label(master, text="Date and Time (YYYY/MM/DD HH:mm:ss):").pack()
        self.date_entry = tk.Entry(master, width=25)
        self.date_entry.insert(0, "2023/06/23 17:00:00")  # Default value
        self.date_entry.pack()

        tk.Label(master, text="Latitude:").pack()
        self.lat_entry = tk.Entry(master, width=25)
        self.lat_entry.insert(0, "13.811352331546372")  # Default value
        self.lat_entry.pack()

        tk.Label(master, text="Longitude:").pack()
        self.lon_entry = tk.Entry(master, width=25)
        self.lon_entry.insert(0, "100.50430749660208")  # Default value
        self.lon_entry.pack()

        tk.Label(master, text="Height of Rectangle (m):").pack()
        self.height_entry = tk.Entry(master)
        self.height_entry.pack()

        tk.Label(master, text="Width of Rectangle (m):").pack()
        self.width_entry = tk.Entry(master)
        self.width_entry.pack()

        tk.Button(master, text="Calculate Shadow", command=self.calculate_shadow).pack()

    def calculate_shadow(self):
        # Get user input
        date_str = self.date_entry.get()
        lat_str = self.lat_entry.get()
        lon_str = self.lon_entry.get()
        height_str = self.height_entry.get()
        width_str = self.width_entry.get()

        # Convert input to appropriate types
        date = ephem.Date(date_str)
        lat = float(lat_str)
        lon = float(lon_str)
        height = float(height_str)
        width = float(width_str)

        # Calculate solar position
        observer = ephem.Observer()
        observer.lat, observer.lon = lat, lon
        observer.date = date

        sun = ephem.Sun(observer)
        sun_altitude = sun.alt
        sun_azimuth = sun.az # 90 - az ???????
        print(sun_altitude)
        print(sun_azimuth)


        # Calculate shadow length
        shadow_length = height / math.tan(math.radians(sun_altitude))

        # Calculate shadow direction using azimuth
        shadow_direction_x = shadow_length * math.cos(math.radians(sun_azimuth))
        shadow_direction_y = shadow_length * math.sin(math.radians(sun_azimuth))

        # Draw rectangle and shadow on canvas
        self.canvas.delete("all")

        # Draw rectangle
        rect_x = 175
        rect_y = 200
        rect_width = width
        rect_height = height
        self.canvas.create_rectangle(rect_x, rect_y, rect_x + rect_width, rect_y + rect_height, fill="blue")

        # Draw shadow lines from each corner of the rectangle
        shadow_end_x1 = rect_x + shadow_direction_x
        shadow_end_y1 = rect_y + shadow_direction_y

        shadow_end_x2 = rect_x + rect_width + shadow_direction_x
        shadow_end_y2 = rect_y + shadow_direction_y

        shadow_end_x3 = rect_x + rect_width + shadow_direction_x
        shadow_end_y3 = rect_y + rect_height + shadow_direction_y

        shadow_end_x4 = rect_x + shadow_direction_x
        shadow_end_y4 = rect_y + rect_height + shadow_direction_y

        # Draw shadow lines from each corner to corresponding points on the ground
        self.canvas.create_line(rect_x, rect_y, shadow_end_x1, shadow_end_y1, fill="red")
        self.canvas.create_line(rect_x + rect_width, rect_y, shadow_end_x2, shadow_end_y2, fill="red")
        self.canvas.create_line(rect_x + rect_width, rect_y + rect_height, shadow_end_x3, shadow_end_y3, fill="red")
        self.canvas.create_line(rect_x, rect_y + rect_height, shadow_end_x4, shadow_end_y4, fill="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = ShadowCalculator(root)
    root.mainloop()
