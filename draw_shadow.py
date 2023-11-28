import tkinter as tk
from pysolar.solar import get_altitude, get_azimuth
import math
import datetime
import pytz

class ShadowCalculator:
    def __init__(self, master):
        self.master = master
        self.master.title("Shadow Projector")

        self.canvas = tk.Canvas(master, width=400, height=400)
        self.canvas.pack()

        # Entry widgets for user input with default values
        tk.Label(master, text="Date and Time (YYYY/MM/DD HH:mm:ss):").pack()
        self.date_entry = tk.Entry(master, width=25)
        self.date_entry.insert(0, "2023/06/23 16:00:00")  # Default value
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
        self.height_entry.insert(0, "10")  # Default value
        self.height_entry.pack()

        tk.Label(master, text="Width of Rectangle (m):").pack()
        self.width_entry = tk.Entry(master)
        self.width_entry.insert(0, "10")  # Default value
        self.width_entry.pack()

        tk.Label(master, text="lavitage from ground (m):").pack()
        self.lavitage_entry = tk.Entry(master)
        self.lavitage_entry.insert(0, "10")  # Default value
        self.lavitage_entry.pack()

        tk.Button(master, text="Calculate Shadow", command=self.calculate_shadow).pack()

    def calculate_shadow(self):
        # Get user input
        date_input_str = self.date_entry.get()
        lat_str = self.lat_entry.get()
        lon_str = self.lon_entry.get()
        height_str = self.height_entry.get()
        width_str = self.width_entry.get()
        lavitage_height_str = self.lavitage_entry.get()

        local_datetime = datetime.datetime.strptime(date_input_str, "%Y/%m/%d %H:%M:%S")
        pytz.timezone('Asia/Bangkok')


        # Convert input to appropriate types
        # -Convert local to UTC
        date = local_datetime.astimezone(pytz.utc)
        lat = float(lat_str)
        lon = float(lon_str)
        height = float(height_str)
        width = float(width_str)
        lavitage_height = float(lavitage_height_str)

        # Calculate solar position using pysolar
        solar_altitude = get_altitude(lat, lon, date)
        solar_azimuth = get_azimuth(lat, lon, date)
        print(solar_azimuth)
        print(solar_altitude)

        shadow_azimuth = solar_azimuth + 90

        # Calculate shadow length
        phi = math.radians(solar_altitude)
        phi = phi % (2 * math.pi)
        shadow_length = lavitage_height / math.tan(phi)
        print(shadow_length)

        # Calculate shadow direction using azimuth
        shadow_direction_x = shadow_length * math.cos(math.radians(shadow_azimuth))
        shadow_direction_y = shadow_length * math.sin(math.radians(shadow_azimuth))

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
