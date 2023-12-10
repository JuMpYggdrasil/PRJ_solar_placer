""" cprofilev .\main_tkinter.py"""
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import simpledialog
from PIL import Image, ImageTk
import math
import datetime
import pytz
from pysolar.solar import get_altitude, get_azimuth
import matplotlib.pyplot as plt
import calendar
import json
import os
import copy

jsondata = None

# Define panel_info as a global variable
# Each entry contains (power, width, height) information for different solar panels
panel_info = {
    "Jinko 550W": (550, 2.278, 1.134),  # Default JKM530-550M-72HL4
    "Trina 300W": (300, 1.956, 0.992),
    "Jinko 350W": (350, 1.956, 0.992),
    "Jinko 500W": (500, 1.956, 1.310),
    "Jinko 600W": (600, 2.465, 1.134)
}

json_file_path = "parameter.json"

# Check if the JSON file exists
if os.path.exists(json_file_path):
    # Load panel_info from the JSON file
    with open(json_file_path, "r", encoding='utf-8') as json_file:
        jsondata = json.load(json_file)
        loaded_panel_info = jsondata["panel_info"]
        
    # Update panel_info with the loaded data
    panel_info.update(loaded_panel_info)

class SolarArray:
    def __init__(self, panel_points):
        # self.name = ""
        self.panel_points = panel_points
        self.total_panel_count = 0
        self.horizontal_panel_count = 0
        self.vertical_panel_count = 0
        self.intersect_keepout_count = 0
        self.kWp = 0
        self.azimuth_angle = 0

        # GUI panel setting
        self.panel_type = []
        self.tilt_angle = 0
        self.lavitation = 0
        self.panel_rotation_tick = 0
        self.walk_gap_rotation_tick = 0
        self.setback_length = 0

        self.gap_size = None
        self.small_rect_size = None

    def calculate_panel(self, canvas, keepout_set):
        if not self.panel_type:
            return
        
        if len(self.panel_points) < 4:
            return
        
        # Calculate approximate rectangle properties
        # Use the last four points to calculate rectangle properties
        # x_coords, y_coords = zip(*self.points[-4:])
        points = np.array(self.panel_points[-4:], dtype=np.int32)

        # Find the minimum area rectangle using OpenCV
        rect = cv2.minAreaRect(points)


        # Draw boundary
        center, size, angle = rect
        self.azimuth_angle = angle
        # Draw the rotated rectangle on the canvas
        self.draw_rotated_rectangle(canvas, center, size, angle, color="gold")
        

        # Draw boundary with setback
        center, size, angle = rect #  the angle value always lies between [-90,0) to X-axis
        
        size = tuple(s - 2 * self.setback_length for s in size)
        # Draw the rotated rectangle on the canvas
        self.draw_rotated_rectangle(canvas, center, size, angle)
        self.draw_rotated_angle(canvas, center, size, angle)
        self.draw_small_rectangles(canvas, center, size, keepout_set)

        return
        

    def draw_rotated_rectangle(self, canvas, center, size, angle, color="lightblue", stipple="gray50",scaled=1):
        # Calculate the coordinates of the four corners of the rotated rectangle
        w, h = size
        w = w*scaled
        h = h*scaled
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        x1 = center[0] - w / 2 * cos_a - h / 2 * sin_a
        y1 = center[1] - w / 2 * sin_a + h / 2 * cos_a

        x2 = center[0] + w / 2 * cos_a - h / 2 * sin_a
        y2 = center[1] + w / 2 * sin_a + h / 2 * cos_a

        x3 = center[0] + w / 2 * cos_a + h / 2 * sin_a
        y3 = center[1] + w / 2 * sin_a - h / 2 * cos_a

        x4 = center[0] - w / 2 * cos_a + h / 2 * sin_a
        y4 = center[1] - w / 2 * sin_a - h / 2 * cos_a

        # Draw the rotated rectangle on the canvas
        canvas.create_polygon(x1, y1, x2, y2, x3, y3, x4, y4, fill=color, stipple=stipple)

    def draw_rotated_angle(self, canvas, center, size, angle, color="lightblue", stipple="gray50",scaled=1):
        # Calculate the coordinates of the four corners of the rotated rectangle
        w, h = size
        w = w*scaled
        h = h*scaled
        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        x1 = center[0] - w / 2 * cos_a - h / 2 * sin_a
        y1 = center[1] - w / 2 * sin_a + h / 2 * cos_a

        x2 = center[0] + w / 2 * cos_a - h / 2 * sin_a
        y2 = center[1] + w / 2 * sin_a + h / 2 * cos_a

        x3 = center[0] + w / 2 * cos_a + h / 2 * sin_a
        y3 = center[1] + w / 2 * sin_a - h / 2 * cos_a

        x4 = center[0] - w / 2 * cos_a + h / 2 * sin_a
        y4 = center[1] - w / 2 * sin_a - h / 2 * cos_a

        ymax = max(y1,y2,y3,y4)

        canvas.create_line(x2, ymax, x3, ymax, fill="black")
        canvas.create_line(x2, ymax+1, x3, ymax+1, fill="white")
        canvas.create_line(x2, ymax, x1, ymax, fill="white")
        canvas.create_line(x2, ymax+1, x1, ymax+1, fill="black")
        canvas.create_text((x2+x3)/2, ymax+10, text=f"{(90-angle):.1f} deg", fill="black", font=('Helvetica 10 bold'))
        canvas.create_text((x2+x1)/2, ymax+10, text=f"{(angle):.1f} deg", fill="black", font=('Helvetica 10 bold'))

    def draw_small_rectangles(self, canvas, center, size, keepout_set):
        intersection_count = 0
        angle = self.azimuth_angle
        small_rect_size = self.small_rect_size
        small_rect_width,small_rect_height = small_rect_size
        big_gap_width,big_gap_height,small_gap_width,small_gap_height,gap_width,gap_height = self.gap_size

        # Calculate the number of rectangles that can fit within the rotated rectangle
        w, h = size

        num_rectangles_horizontal = int((w / (small_rect_width + gap_width)))  # Adjust the spacing as needed
        num_rectangles_vertical = int((h / (small_rect_height + gap_height)))  # Adjust the spacing as needed

        space_width = w - (num_rectangles_horizontal*(small_rect_width + gap_width) - gap_width)
        space_height = h - (num_rectangles_vertical*(small_rect_height + gap_height) - gap_height)

        for i in range(num_rectangles_horizontal):
            for j in range(num_rectangles_vertical):
                # Calculate the rotated offset
                if (i % 2)==0:
                    x_offset = i * (small_rect_width + gap_width)
                else:
                    x_offset = i * (small_rect_width + gap_width) + (small_gap_width - big_gap_width)/2
                
                if (j % 2)==0:
                    y_offset = j * (small_rect_height + gap_height)
                else:
                    y_offset = j * (small_rect_height + gap_height) + (small_gap_height - big_gap_height)/2

                rotated_x1, rotated_y1 = self.rotate_point(
                    center[0] - w/2 + small_rect_width/2 + gap_width/2 + space_width/2 + x_offset,
                    center[1] - h/2 + small_rect_height/2 + gap_height/2 + space_height/2 + y_offset,
                    center[0],
                    center[1],
                    angle
                )
                each_center = (rotated_x1,rotated_y1)
                small_rect = each_center, small_rect_size, angle
                agree_count = 0

                if keepout_set:
                    for prohibited_permanent_points in keepout_set:
                        prohibited_points = np.array(prohibited_permanent_points[-4:], dtype=np.int32)

                        # Find the minimum area rectangle using OpenCV
                        prohibited_rect = cv2.minAreaRect(prohibited_points)
                        intersection = cv2.rotatedRectangleIntersection(small_rect,prohibited_rect)

                        if intersection[1] is not None:
                            intersection_count = intersection_count + 1
                            break
                        else:
                            agree_count = agree_count + 1
                    if agree_count==len(keepout_set):
                        self.draw_rotated_rectangle(canvas, each_center, small_rect_size, angle,color="midnight blue",stipple=None,scaled=0.98)
                else:
                    self.draw_rotated_rectangle(canvas, each_center, small_rect_size, angle,color="midnight blue",stipple=None,scaled=0.98)

        x1, y1 = center[0] - 4, center[1] - 4
        x2, y2 = center[0] + 4, center[1] + 4
        canvas.create_oval(x1, y1, x2, y2, fill="green")

        # Update the label to display the total number of rectangles
        num_rectangles_total = num_rectangles_horizontal * num_rectangles_vertical - intersection_count
        # kWp_total = panel_power * num_rectangles_total /1000
        self.total_panel_count = num_rectangles_total
        self.horizontal_panel_count = num_rectangles_horizontal
        self.vertical_panel_count = num_rectangles_vertical
        self.intersect_keepout_count = intersection_count
        
        panel_power,panel_width,panel_height = self.panel_type
        self.kWp = panel_power * self.total_panel_count / 1000

        return
    
    def rotate_point(self, x, y, center_x, center_y, angle):
        # Rotate a point (x, y) around a center (center_x, center_y) by a given angle (in degrees)
        angle_rad = math.radians(angle)
        rotated_x = center_x + (x - center_x) * math.cos(angle_rad) - (y - center_y) * math.sin(angle_rad)
        rotated_y = center_y + (x - center_x) * math.sin(angle_rad) + (y - center_y) * math.cos(angle_rad)
        return rotated_x, rotated_y
    

    def copy(self):
        return copy.deepcopy(self)
    
    



class SolarPlanelPlacerApp:
    def __init__(self, master):
        self.shadow_datetimes = ["2023/03/23 09:00:00","2023/03/23 13:00:00","2023/03/23 16:00:00",
                                 "2023/06/23 09:00:00","2023/06/23 13:00:00","2023/06/23 16:00:00",
                                 "2023/09/23 09:00:00","2023/09/23 13:00:00","2023/09/23 16:00:00",
                                 "2023/12/23 09:00:00","2023/12/23 13:00:00","2023/12/23 16:00:00"]
        self.monthly_percent = [8.732360594,
                                8.321359862,
                                9.466129905,
                                9.541061671,
                                8.783314195,
                                7.957004153,
                                7.821377658,
                                7.810699881,
                                7.263136007,
                                7.707856034,
                                7.939395188,
                                8.656304852]
        self.tz = 'Asia/Bangkok'
        self.Latitude = 13.765733827940576
        self.Longitude = 100.50257304756634

        self.kWh_total = 0

        self.original_image = None
        
        ### Initialize list ###
        self.distance_labels = []

        # Store clicked points
        self.points = []

        # Store object
        self.pv1 = SolarArray([])
        self.reference_points = []
        self.prohibited_points = []
        self.tree_points = []

        self.panel_permanent_sets = []
        self.prohibited_permanent_sets = []
        self.tree_permanent_sets = []


        # Initial Variable & Flag
        self.already_draw_panel = 0
        self.already_draw_shadow = 0



        self.master = master
        width = self.master.winfo_screenwidth()
        height = self.master.winfo_screenheight()
        # Setting tkinter window size
        self.master.geometry("%dx%d" % (width, height))
        self.master.title("Solar Panel Estimation Tool")

        # Create Canvas
        self.canvas = tk.Canvas(self.master, width=0, height=0)
        self.canvas.pack()
        
        
        # Create a notebook (tabs container)
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill="both")
        
        # Create and add the first tab (Tab 1)
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text='panel layout')
        
        
        
        

        frame4 = tk.Frame(tab1)
        frame4.pack(side=tk.TOP)

        # Add a button to browse and load an image
        self.browse_button = tk.Button(frame4, text="Browse Image", command=self.browse_image_btn)
        self.browse_button.pack(side=tk.LEFT)

        # Entry widget for gap_width
        tk.Label(frame4, text="Gap Width (m):").pack(side=tk.LEFT)
        self.gap_width_entry = tk.Entry(frame4)
        self.gap_width_entry.insert(0, "0.2")  # Set default value
        self.gap_width_entry.pack(side=tk.LEFT)

        # Entry widget for small_gap_height
        tk.Label(frame4, text="Gap Height (m):").pack(side=tk.LEFT)
        self.gap_height_entry = tk.Entry(frame4)
        self.gap_height_entry.insert(0, "0.2")  # Set default value
        self.gap_height_entry.pack(side=tk.LEFT)
        
        # Entry widget for big_gap_height
        tk.Label(frame4, text="Walk Gap (m):").pack(side=tk.LEFT)
        self.walk_gap_entry = tk.Entry(frame4)
        self.walk_gap_entry.insert(0, "0.6")  # Set default value
        self.walk_gap_entry.pack(side=tk.LEFT)

        # Entry widget for big_gap_height
        tk.Label(frame4, text="Setback (m):").pack(side=tk.LEFT)
        self.setback_entry = tk.Entry(frame4)
        self.setback_entry.insert(0, "0")  # Set default value
        self.setback_entry.pack(side=tk.LEFT)

        
        # Bind the <FocusOut> event to the callback function
        self.gap_width_entry.bind("<FocusOut>", self.entry_changed1)
        self.gap_height_entry.bind("<FocusOut>", self.entry_changed1)
        self.walk_gap_entry.bind("<FocusOut>", self.entry_changed1)
        self.setback_entry.bind("<FocusOut>", self.entry_changed1)

        self.gap_width_entry.bind("<Return>", self.entry_changed1)
        self.gap_height_entry.bind("<Return>", self.entry_changed1)
        self.walk_gap_entry.bind("<Return>", self.entry_changed1)
        self.setback_entry.bind("<Return>", self.entry_changed1)

        # Checkbox for prohibiting points
        self.panel_rotate_var = tk.IntVar()
        self.panel_rotate_checkbox = tk.Checkbutton(frame4, text="panel rotation", variable=self.panel_rotate_var, command=self.toggle_panel_rotation)
        self.panel_rotate_checkbox.pack(side=tk.LEFT)

        # Checkbox for prohibiting points
        self.walk_gap_rotate_var = tk.IntVar()
        self.walk_gap_rotate_checkbox = tk.Checkbutton(frame4, text="walk gap rotation", variable=self.walk_gap_rotate_var, command=self.toggle_walk_gap_rotation)
        self.walk_gap_rotate_checkbox.pack(side=tk.LEFT)


        # Create a frame for the first line (area_label and distance_label)
        frame1 = tk.Frame(tab1)
        frame1.pack(side=tk.TOP)

        # Create a label to display the measured area
        self.area_label = tk.Label(frame1, text="Area: ")
        self.area_label.pack(side=tk.LEFT)

        self.distance_label = tk.Label(frame1, text="Distance: ")
        self.distance_label.pack(side=tk.LEFT)

        # Zoom factor
        self.zoom_factor = 1.0

        # Scale factor (to be set by the user)
        self.scale_factor = None

        # Bind mouse click and scroll events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

        # Bind right-click event for creating prohibited areas
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)

        # Bind mouse movement event for the canvas
        self.canvas.bind("<Motion>", self.on_canvas_motion)

        # Create a frame for the second line (buttons)
        frame2 = tk.Frame(tab1)
        frame2.pack(side=tk.TOP)

        

        # Create a Combobox for panel types
        panel_types = list(panel_info.keys())
        self.panel_type_var = tk.StringVar(value=panel_types[0])  # Set the default panel type
        self.panel_type_combobox = ttk.Combobox(frame2, textvariable=self.panel_type_var, values=panel_types)
        self.panel_type_combobox.pack(side=tk.LEFT)

        # Create a button to calculate rectangle properties based on the selected panel type
        self.calculate_button = tk.Button(frame2, text="PV Panel", command=self.calculate_panel_btn, state=tk.DISABLED)
        self.calculate_button.pack(side=tk.LEFT)

        self.new_panel_button = tk.Button(frame2, text="New Panel", command=self.new_panel_btn, state=tk.DISABLED)
        self.new_panel_button.pack(side=tk.LEFT)

        self.clear_button = tk.Button(frame2, text="Clear Panel", command=self.clear_canvas_btn)
        self.clear_button.pack(side=tk.LEFT)

        self.keepout_button = tk.Button(frame2, text="Keepout", command=self.add_keepout_btn, state=tk.DISABLED)
        self.keepout_button.pack(side=tk.LEFT)

        self.clear_all_button = tk.Button(frame2, text="Clear All", command=self.clear_all_canvas_btn)
        self.clear_all_button.pack(side=tk.LEFT)


        # Create a frame for the third line (total_rectangles_label)
        frame3 = tk.Frame(tab1)
        frame3.pack(side=tk.TOP)

        # Create a label to display the total number of rectangles
        self.total_rectangles_label = tk.Label(frame3, text="Total Rectangles: 0")
        self.total_rectangles_label.pack(side=tk.LEFT)
        
        
        
        
        # Create and add the second tab (Tab 2)
        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab2, text='Shadow')
        
        # Create a frame
        frame5 = tk.Frame(tab2)
        frame5.pack(side=tk.TOP)

        tk.Label(frame5, text="Latitude:").pack(side=tk.LEFT)
        self.lat_entry = tk.Entry(frame5, width=25)
        # self.lat_entry.insert(0, "13.765733827940576")  # Default value
        self.lat_entry.insert(0, self.Latitude)  # Default value
        self.lat_entry.pack(side=tk.LEFT)

        tk.Label(frame5, text="Longitude:").pack(side=tk.LEFT)
        self.lon_entry = tk.Entry(frame5, width=25)
        # self.lon_entry.insert(0, "100.50257304756634")  # Default value
        self.lon_entry.insert(0, self.Longitude)  # Default value
        self.lon_entry.pack(side=tk.LEFT)
        
        tk.Label(frame5, text="lavitage from ground (m):").pack(side=tk.LEFT)
        self.lavitage_entry = tk.Entry(frame5)
        self.lavitage_entry.insert(0, "0")  # Default value
        self.lavitage_entry.pack(side=tk.LEFT)

        tk.Label(frame5, text="Tilt Angle (deg):").pack(side=tk.LEFT)
        self.tilt_angle_entry = tk.Entry(frame5)
        self.tilt_angle_entry.insert(0, "10")  # Default value
        self.tilt_angle_entry.pack(side=tk.LEFT)

        # Bind the <FocusOut> event to the callback function
        self.lat_entry.bind("<FocusOut>", self.entry_changed2)
        self.lat_entry.bind("<Return>", self.entry_changed2)

        self.lon_entry.bind("<FocusOut>", self.entry_changed2)
        self.lavitage_entry.bind("<FocusOut>", self.entry_changed2)
        self.tilt_angle_entry.bind("<FocusOut>", self.entry_changed2)

        # Checkbox for prohibiting points
        self.tree_var = tk.IntVar()
        self.tree_checkbox = tk.Checkbutton(frame5, text="Tree", variable=self.tree_var, command=self.toggle_tree_cb, state=tk.DISABLED)
        self.tree_checkbox.pack(side=tk.LEFT)
        
        
        # Create a frame
        frame6 = tk.Frame(tab2)
        frame6.pack(side=tk.TOP)

        self.cal_shadow_button = tk.Button(frame6, text="Calculate Shadow", command=self.calculate_shadows_btn, state=tk.DISABLED)
        self.cal_shadow_button.pack(side=tk.LEFT)
        self.hide_shadow_button = tk.Button(frame6, text="Hide Shadow", command=self.hide_shadows_btn)
        self.hide_shadow_button.pack(side=tk.LEFT)
        self.clear_trees_button = tk.Button(frame6, text="Clear Trees", command=self.clear_trees_btn)
        self.clear_trees_button.pack(side=tk.LEFT)

        frame7 = tk.Frame(tab2)
        frame7.pack(side=tk.TOP)

        self.province_label = tk.Label(frame7, text="province: ")
        self.province_label.pack(side=tk.LEFT)

        # Create and add the second tab (Tab 3)
        tab3 = ttk.Frame(self.notebook)
        self.notebook.add(tab3, text='PVOUT/Year')

        # Create a frame
        frame8 = tk.Frame(tab3)
        frame8.pack(side=tk.TOP)


        # Entry widget for small_gap_height
        tk.Label(frame8, text="Specific photovoltaic power output per year (kWh/kWp):").pack(side=tk.LEFT)
        self.pvout_entry = tk.Entry(frame8)
        self.pvout_entry.insert(0, "1433.2")  # Set default value
        self.pvout_entry.pack(side=tk.LEFT)
        # float(self.pvout_entry.get())

        # Checkbox for prohibiting points
        self.pvout_en_var = tk.IntVar()
        self.pvout_en_var.set(1)
        self.pvout_en_checkbox = tk.Checkbutton(frame8, text="", variable=self.pvout_en_var, command=self.toggle_pvout_en)
        self.pvout_en_checkbox.pack(side=tk.LEFT)

        self.monthly_plot_button = tk.Button(frame8, text="Monthly Plot", command=self.monthly_plot_btn)
        self.monthly_plot_button.pack(side=tk.LEFT)

        # Create a frame
        frame9 = tk.Frame(tab3)
        frame9.pack(side=tk.TOP)
        tk.Label(frame9, text="https://globalsolaratlas.info/map parameter.json").pack(side=tk.LEFT)

        self.update_lat_lng()
        # Bind the tab selection event to the on_tab_selected function
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_selected)


    def on_tab_selected(self, event):
        # Get the selected tab index
        selected_tab_index = self.notebook.index(self.notebook.select())

        # Print or do something based on the selected tab index
        # print(f"Tab {selected_tab_index + 1} selected")

        self.update_canvas()
        self.update_lat_lng()

        
    def get_pvout(self, user_lat, user_lng):
        json_file_path = "parameter.json"
        # Load JSON data
        with open(json_file_path, 'r', encoding='utf-8') as file:
            jsondata = json.load(file)
            thai_pv_zipcode = jsondata["thai_pv_zipcode"]

        nearest_location = self.find_nearest_location(user_lat, user_lng, thai_pv_zipcode)

        # if nearest_location:
        #     print(f"Nearest Location: District - {nearest_location['district']}, Province - {nearest_location['province']}")
        # else:
        #     print("No locations found.")

        for location in thai_pv_zipcode:
            if nearest_location["province"] == location["province"]:
                # print(location["pvout"])
                return location["pvout"],location["province"]
            
        return None,None
        

    def monthly_plot_btn(self):
        annual_power = self.kWh_total

        # Calculate monthly power production
        monthly_power = [annual_power * (percent / 100) for percent in self.monthly_percent]

        # Get month names
        month_names = [calendar.month_abbr[i] for i in range(1, 13)]

        # Add labels to the top of each bar
        for month, power in zip(month_names, monthly_power):
            plt.text(month, power + 10, f'{power:,.0f}', ha='center', va='bottom')

        
        # Plot the bar chart
        plt.bar(month_names, monthly_power, color='blue')

        # Add labels and title
        plt.xlabel('Month')
        plt.ylabel('Power Production (kWh)')
        plt.title(f'Monthly Power Production (Total:{annual_power:,.0f} kWh)')

        # Show the plot
        plt.show()

    def browse_image_btn(self):
        # Open a file dialog to select an image file
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
        if not file_path:
            return
        
        # Load the selected image
        self.load_image(file_path)
        # Make the browse_button invisible
        self.browse_button.pack_forget()

    # only use in browse_image_btn()
    def load_image(self, image_path):
        # Load the original image
        self.original_image = Image.open(image_path)

        # Resize the image to half its original size
        new_size = (int(self.original_image.width *7/10), int(self.original_image.height *7/10))
        self.original_image = self.original_image.resize(new_size, Image.Resampling.LANCZOS)

        self.tk_image = ImageTk.PhotoImage(self.original_image)

        # Display the original image on the canvas
        self.canvas.config(width=self.original_image.width, height=self.original_image.height)

        # Display the original image on the canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def entry_changed1(self, event):
        # This function will be called when the entry loses focus
        # You can access the entry widget using 'event.widget'
        entry_widget = event.widget

        # Get the current value from the entry widget
        current_value = entry_widget.get()

        # Do something with the current value, e.g., print it
        # print(f"Value changed to: {current_value}")

        
        self.update_panel_setting(self.pv1)
        self.update_canvas()

    def entry_changed2(self, event):
        # This function will be called when the entry loses focus
        # You can access the entry widget using 'event.widget'
        entry_widget = event.widget

        # Get the current value from the entry widget
        current_value = entry_widget.get()

        # Do something with the current value, e.g., print it
        # print(f"Value changed to: {current_value}")
        self.update_lat_lng()
        self.update_panel_setting(self.pv1)



    def toggle_tree_cb(self):
        pass

    def toggle_pvout_en(self):
        if self.pvout_en_var.get() == 1:
            self.pvout_entry["state"] = tk.NORMAL
        else:
            self.pvout_entry["state"] = tk.DISABLED

    def toggle_panel_rotation(self):
        self.update_panel_setting(self.pv1)
        self.update_canvas()

    def toggle_walk_gap_rotation(self):
        self.update_panel_setting(self.pv1)
        self.update_canvas()


    def update_lat_lng(self):
        lat_str = self.lat_entry.get()
        if "," in lat_str:
            # Split the string by comma and strip spaces, then convert to float
            user_lat, user_lng = map(lambda s: float(s.strip()), lat_str.split(','))

            if self.pvout_en_var.get() == 1:
                self.lat_entry.delete(0,tk.END)
                self.lat_entry.insert(0,user_lat)

                self.lon_entry.delete(0,tk.END)
                self.lon_entry.insert(0,user_lng)
        else:
            try:
                user_lat = float(self.lat_entry.get())
            except ValueError:
                user_lat = 0
            try:
                user_lng = float(self.lon_entry.get())
            except ValueError:
                user_lng = 0
        
        self.Latitude = user_lat
        self.Longitude = user_lng

        self.pvout, self.province = self.get_pvout(self.Latitude,self.Longitude)
        if self.pvout:
            self.province_label.config(text=f"province: {self.province}")

            if self.pvout_en_var.get() == 1:
                self.pvout_entry.delete(0,tk.END)
                self.pvout_entry.insert(0,self.pvout)
        

    def calculate_shadows_btn(self, color="black", stipple="gray50"):
        self.already_draw_shadow = 1
        self.update_canvas()

    
    def hide_shadows_btn(self):
        self.already_draw_shadow = 0
        self.update_canvas()


    def clear_trees_btn(self):
        self.tree_points = []
        self.tree_permanent_sets = []
        self.update_canvas()


    def clear_canvas_btn(self):
        self.points = []
        self.pv1.panel_points = []
        self.already_draw_panel = 0
        self.already_draw_shadow = 0
        self.update_canvas()
        self.cal_shadow_button["state"] = tk.DISABLED
        self.tree_checkbox["state"] = tk.DISABLED


    def clear_all_canvas_btn(self):
        self.points = []
        self.pv1.panel_points = []
        self.panel_permanent_sets = []
        self.prohibited_points = []
        self.prohibited_permanent_sets = []
        self.tree_points = []
        self.tree_permanent_sets = []
        self.reference_points = []
        self.already_draw_panel = 0
        self.already_draw_shadow = 0
        self.update_canvas()
        self.calculate_button["state"] = tk.DISABLED
        self.new_panel_button["state"] = tk.DISABLED
        self.keepout_button["state"] = tk.DISABLED
        self.cal_shadow_button["state"] = tk.DISABLED
        self.tree_checkbox["state"] = tk.DISABLED
 

    def add_keepout_btn(self):
        self.prohibited_permanent_sets.append(self.prohibited_points.copy())
        self.keepout_button["state"] = tk.DISABLED
        self.update_canvas()


    def on_canvas_click(self, event):
        x, y = event.x, event.y

        self.points.append((x, y))

        if not self.reference_points:
            # If the first two points are clicked, prompt the user to enter the scale factor
            if len(self.points) >= 2:
                self.reference_points = self.points
                self.points = []
                
                pixel_distance = ((self.reference_points[-2][0] - self.reference_points[-1][0]) ** 2 + (
                            self.reference_points[-2][1] - self.reference_points[-1][1]) ** 2) ** 0.5
                pixel_distance = pixel_distance/3
                d_val = simpledialog.askfloat("Scale Factor", "Enter the scale factor (pixels to meters):")
                if d_val is not None:
                    self.scale_factor = d_val / pixel_distance
                    # print("scale_factor: ")
                    # print(self.scale_factor)
                    # Remove the binding for mouse wheel event
                    self.canvas.unbind("<MouseWheel>")
                    width = int(self.original_image.width * self.zoom_factor)
                    height = int(self.original_image.height * self.zoom_factor)
                    self.reference_points = [(int((x+2*width)/3), int((y+2*height)/3)) for x, y in self.reference_points]
                else:
                    # If the user cancels, clear the points and canvas and return
                    self.clear_all_canvas_btn()

            return

        if self.tree_var.get() == 1:
            self.tree_points.append((x,y))
            self.points = []
            if len(self.tree_points) == 2:
                h_val = simpledialog.askfloat("height of tree", "Enter the height of tree (meters):")
                if h_val is not None:
                    x,y,h = self.tree_points[0],self.tree_points[1],h_val
                    self.tree_permanent_sets.append((x,y,h))
                    self.tree_points = []
                else:
                    self.tree_points = []

        if len(self.points) > 4:
            self.points.pop(0)

        if len(self.points) > 2:
            area = self.calculate_area()
            self.area_label.config(text=f"Area: {area:.2f} square meters")
        else:
            area = 0
            self.area_label.config(text=f"Area: {area:.2f} square meters")
        if len(self.points) > 1:
            distance = self.calculate_distance()
            self.distance_label.config(text=f"Distance: {distance:.2f} meters")
        else:
            distance = 0
            self.distance_label.config(text=f"Distance: {distance:.2f} meters")

        if len(self.points) == 4:
            self.calculate_button["state"] = tk.NORMAL
            
            points = np.array(self.points[-4:], dtype=np.int32)
            # Find the minimum area rectangle using OpenCV
            rect = cv2.minAreaRect(points)
            box = cv2.boxPoints(rect)
            box = np.int_(box)
            self.pv1.panel_points = box.tolist()
            self.points = []

        self.update_canvas()
        

    def on_canvas_right_click(self, event):
        x, y = event.x, event.y

        if self.tree_var.get() == 1:
            if len(self.tree_points) == 0:
                self.tree_points = []
                self.tree_var.set(False)
            if len(self.tree_points) == 1:
                self.tree_points = []
            return
        
        self.prohibited_points.append((x, y))
        if len(self.prohibited_points) > 4:
            self.prohibited_points.pop(0)
        if len(self.prohibited_points)== 4:
            self.keepout_button["state"] = tk.NORMAL
        self.already_draw_panel = 0
        self.update_canvas()


    def on_canvas_motion(self, event):
        # Code to execute when the mouse moves over the canvas
        x, y = event.x, event.y

        self.update_canvas()
    
        if not self.reference_points:
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="", outline="purple", width=2)
            if 0 < len(self.points):
                self.canvas.create_line(self.points[0][0], self.points[0][1], x, y, fill="maroon1")
            return



        if self.tree_var.get() == 1:
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="lawn green", outline="", width=1)
            self.canvas.create_text(x, y, text=f"draw trees", fill="black", font=('Helvetica 10 bold'))
            self.canvas.pack()
            if len(self.tree_points) == 1:
                x_,y_ = self.tree_points[0]
                r = math.dist([x, y], [x_, y_])
                self.draw_circle(x_,y_,r,self.canvas)
                self.draw_circle(x_,y_,r+1,self.canvas,outline="white")

            return
        
        # self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="green2")
        self.draw_2half_circle(self.canvas,x, y,3,fill_left="green2",fill_right="deep pink")
        
        if 0 < len(self.points) and len(self.points) < 4:
            for i in range(len(self.points)-1):
                self.canvas.create_line(self.points[i][0], self.points[i][1], self.points[i + 1][0], self.points[i + 1][1], fill="orange")

            # Draw a line connecting the last point to the current mouse coordinates
            self.canvas.create_line(self.points[-1][0], self.points[-1][1], x, y, fill="orange")
            self.canvas.create_line(self.points[0][0], self.points[0][1], x, y, fill="orange")


    def on_mousewheel(self, event):
        # Update the zoom factor based on the mouse wheel movement
        if event.delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor /= 1.1

        self.update_canvas()


    # For draw all component on canvas
    def update_canvas(self):
        if self.original_image is None:
            return
        
        
    
        # Define the region of interest (ROI)
        roi_width = 200
        roi_height = 150

        # Resize the image based on the zoom factor
        width = int(self.original_image.width * self.zoom_factor)
        height = int(self.original_image.height * self.zoom_factor)
        resized_image = self.original_image.resize((width, height), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)

        if not self.reference_points:
            # Extract the region of interest from the resized image
            roi_image = resized_image.crop((width - roi_width, height - roi_height, width, height))
            triple_roi_image = roi_image.resize((roi_width * 3, roi_height * 3), Image.Resampling.LANCZOS)
            self.triple_roi_tk_image = ImageTk.PhotoImage(triple_roi_image)

        # Update the canvas with the resized image
        self.canvas.config(width=width, height=height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        if not self.reference_points:
            # Display the region of interest at the bottom right corner
            self.canvas.create_image(width, height, anchor=tk.SE, image=self.triple_roi_tk_image)

        
        # Draw prohibited areas
        for area in self.prohibited_points:
            x, y = area
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="pink")
        
        for prohibited_permanent_points in self.prohibited_permanent_sets:
            # Draw prohibited areas
            for area in prohibited_permanent_points:
                x, y = area
                self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="red")
                
            if len(prohibited_permanent_points)>=4:
                self.canvas.create_polygon(prohibited_permanent_points[0][0], prohibited_permanent_points[0][1], prohibited_permanent_points[1][0], prohibited_permanent_points[1][1], prohibited_permanent_points[2][0], prohibited_permanent_points[2][1], prohibited_permanent_points[3][0], prohibited_permanent_points[3][1], fill="red", stipple="gray50")

        # draw panel shadow
        if self.already_draw_panel == 1:
            for shadow_datetime in self.shadow_datetimes:
                self.calculate_panel_shadow(shadow_datetime,self.pv1.panel_points)

        for panel_permanent_array in self.panel_permanent_sets:
            for shadow_datetime in self.shadow_datetimes:
                self.calculate_panel_shadow(shadow_datetime,panel_permanent_array.panel_points)

        angle = 0
        panels_tempo_count = 0
        panels_permanent_count = 0
        
        # draw panel
        draw_cond = self.already_draw_panel == 1
        point_cond = len(self.pv1.panel_points) >= 4
        if draw_cond and point_cond:
            
            test_pv = self.pv1
            test_pv.calculate_panel(self.canvas, self.prohibited_permanent_sets)

            angle = min(self.pv1.azimuth_angle, 90 - self.pv1.azimuth_angle)

        for panel_permanent_array in self.panel_permanent_sets:
            panel_permanent_array.calculate_panel(self.canvas, self.prohibited_permanent_sets)

        total_panel_count = self.pv1.total_panel_count + panels_permanent_count
        selected_panel_type = self.panel_type_var.get()
        panel_power, _, _ = panel_info.get(selected_panel_type)

        kWp_total = panel_power * total_panel_count /1000
        kWp_tempo_total = panel_power * panels_tempo_count /1000
        kWp_permanent_total = panel_power * panels_permanent_count /1000
        tilt_ratio = self.tilt_calcutation(self.pv1.tilt_angle)
        PVSYST_ratio = 0.87
        try:
            kWp_to_kWh = float(self.pvout_entry.get()) # per year
        except:
            kWp_to_kWh = 0
        self.kWh_total = kWp_total * kWp_to_kWh * PVSYST_ratio * tilt_ratio
        try:
            self.total_rectangles_label.config(text=f"amount of panels {panels_permanent_count} + {panels_tempo_count} = {total_panel_count:,} , Azimuth angle(deg): {angle:,.2f} , kWp: {kWp_permanent_total} + {kWp_tempo_total} = {kWp_total:,.2f} kW, Anual Energy {self.kWh_total:,.2f} kWh")
        except:
            pass
        
        # draw trees shadow
        for shadow_datetime in self.shadow_datetimes:
            self.calculate_trees_shadow(shadow_datetime)

        # # draw trees
        for tree_permanent_points in self.tree_permanent_sets:
            x0,y0 = tree_permanent_points[0]
            x1,y1 = tree_permanent_points[1]
            r = math.dist([x0, y0], [x1, y1])
            self.draw_circle(x0,y0,r,self.canvas,fill="lawn green",outline="")
            self.canvas.create_text(x0, y0, text=f"{tree_permanent_points[2]:.1f} m", fill="black", font=('Helvetica 10 bold'))

        for area in self.points:
            x, y = area
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="yellow")

        if not self.reference_points:
            if len(self.points) == 1:
                x, y = self.points[0]
                self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="purple")

        for point in self.reference_points:
            x, y = point
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="purple")

        for n,point in enumerate(self.pv1.panel_points):
            x, y = point
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="blue")
            # self.canvas.create_text(x +10 , y, text=f"{n}", fill="black", font=('Helvetica 10 bold'))
            

        if len(self.pv1.panel_points) > 0:
            for i in range(len(self.pv1.panel_points)-1):
                x0,y0 = self.pv1.panel_points[i]
                x1,y1 = self.pv1.panel_points[i+1]
                self.canvas.create_line(x0, y0,x1, y1, fill="orange")
            self.canvas.create_line(self.pv1.panel_points[0][0], self.pv1.panel_points[0][1], self.pv1.panel_points[-1][0], self.pv1.panel_points[-1][1], fill="orange")

    def calculate_panel_shadow(self, date_input_str, selected_points, color="black", stipple="gray50"):
        if self.already_draw_shadow == 0:
            return
        
        if len(selected_points) < 4:
            return
        
        self.update_lat_lng()
        lavitage_height_str = self.lavitage_entry.get()
        
        local_datetime = datetime.datetime.strptime(date_input_str, "%Y/%m/%d %H:%M:%S")
        if local_datetime.month <7:
            color="gray2"
        else:
            color="gray4"
        pytz.timezone(self.tz)

        # Convert input to appropriate types
        # -Convert local to UTC
        date = local_datetime.astimezone(pytz.utc)
        try:
            lavitage_height = float(lavitage_height_str)
        except ValueError:
            lavitage_height = 0

        # Calculate solar position using pysolar
        solar_altitude = get_altitude(self.Latitude, self.Longitude, date)
        solar_azimuth = get_azimuth(self.Latitude, self.Longitude, date)
        # print(solar_azimuth)
        # print(solar_altitude)

        shadow_azimuth = solar_azimuth + 90

        # Calculate shadow length
        phi = math.radians(solar_altitude)
        phi = phi % (2 * math.pi)
        shadow_length = (lavitage_height / math.tan(phi)) / self.scale_factor
        
        # print(shadow_length)

        # Calculate shadow direction using azimuth
        shadow_direction_x = shadow_length * math.cos(math.radians(shadow_azimuth))
        shadow_direction_y = shadow_length * math.sin(math.radians(shadow_azimuth))

        

        
        # Draw shadow lines from each corner of the rectangle
        shadow_end_x1 = selected_points[-4][0] + shadow_direction_x
        shadow_end_y1 = selected_points[-4][1] + shadow_direction_y

        shadow_end_x2 = selected_points[-3][0] + shadow_direction_x
        shadow_end_y2 = selected_points[-3][1] + shadow_direction_y

        shadow_end_x3 = selected_points[-2][0] + shadow_direction_x
        shadow_end_y3 = selected_points[-2][1] + shadow_direction_y

        shadow_end_x4 = selected_points[-1][0] + shadow_direction_x
        shadow_end_y4 = selected_points[-1][1] + shadow_direction_y
        

        # Draw shadow lines from each corner to corresponding points on the ground
        # self.canvas.create_line(selected_points[-4][0], selected_points[-4][1], shadow_end_x1, shadow_end_y1, fill="black")
        # self.canvas.create_line(selected_points[-3][0], selected_points[-3][1], shadow_end_x2, shadow_end_y2, fill="black")
        # self.canvas.create_line(selected_points[-2][0], selected_points[-2][1], shadow_end_x3, shadow_end_y3, fill="black")
        # self.canvas.create_line(selected_points[-1][0], selected_points[-1][1], shadow_end_x4, shadow_end_y4, fill="black")
        
        # Draw the rotated rectangle on the canvas
        self.canvas.create_polygon(shadow_end_x1, shadow_end_y1, shadow_end_x2, shadow_end_y2, shadow_end_x3, shadow_end_y3, shadow_end_x4, shadow_end_y4, fill=color, stipple=stipple)

    
    def calculate_trees_shadow(self, date_input_str, color="black", stipple="gray50"):
        if self.already_draw_shadow == 0:
            return

        self.update_lat_lng()
        lavitage_height_str = self.lavitage_entry.get()
        
        local_datetime = datetime.datetime.strptime(date_input_str, "%Y/%m/%d %H:%M:%S")
        if local_datetime.month <7:
            color="gray2"
        else:
            color="gray4"
        pytz.timezone(self.tz)

        # Convert input to appropriate types
        # -Convert local to UTC
        date = local_datetime.astimezone(pytz.utc)
        
        try:
            lavitage_height = float(lavitage_height_str)
        except ValueError:
            lavitage_height = 0

        # Calculate solar position using pysolar
        solar_altitude = get_altitude(self.Latitude, self.Longitude, date)
        solar_azimuth = get_azimuth(self.Latitude, self.Longitude, date)
        # print(solar_azimuth)
        # print(solar_altitude)

        shadow_azimuth = solar_azimuth + 90

        # Calculate shadow length
        phi = math.radians(solar_altitude)
        phi = phi % (2 * math.pi)



        for tree_permanent_points in self.tree_permanent_sets:
            x0,y0 = tree_permanent_points[0]
            x1,y1 = tree_permanent_points[1]
            r = math.dist([x0, y0], [x1, y1])

            dh = self.bound(tree_permanent_points[2] - lavitage_height, 0,100)

            tree_shadow_length = (dh / math.tan(phi)) / self.scale_factor

            # Calculate shadow direction using azimuth
            tree_shadow_direction_x = tree_shadow_length * math.cos(math.radians(shadow_azimuth))
            tree_shadow_direction_y = tree_shadow_length * math.sin(math.radians(shadow_azimuth))

            shadow_x0 = x0 + tree_shadow_direction_x
            shadow_y0 = y0 + tree_shadow_direction_y

            self.draw_circle(shadow_x0,shadow_y0,r,self.canvas,fill="black")
            


    def calculate_area(self):
        # Shoelace formula to calculate the area of a polygon
        area_pixels = 0
        num_points = len(self.points)

        for i in range(num_points - 1):
            area_pixels += (self.points[i][0] * self.points[i + 1][1] - self.points[i + 1][0] * self.points[i][1])

        # Add the last edge (closing the loop)
        area_pixels += (self.points[-1][0] * self.points[0][1] - self.points[0][0] * self.points[-1][1])

        # Take the absolute value and divide by 2
        area_pixels = abs(area_pixels) / 2.0

        # Convert pixels squared to square meters using the scale factor
        area_square_meters = area_pixels * (self.scale_factor ** 2)

        return area_square_meters

    def calculate_distance(self):
        # Calculate the distance between the last two points in meters
        pixel_distance = ((self.points[-2][0] - self.points[-1][0]) ** 2 + (self.points[-2][1] - self.points[-1][1]) ** 2) ** 0.5
        distance_in_meters = pixel_distance * self.scale_factor
        return distance_in_meters


    def calculate_panel_btn(self):
        self.already_draw_panel = 1
        self.cal_shadow_button["state"] = tk.NORMAL
        self.tree_checkbox["state"] = tk.NORMAL
        self.new_panel_button["state"] = tk.NORMAL
        self.update_panel_setting(self.pv1)
        self.update_canvas()

    def update_panel_setting(self, solar_array):
        selected_panel_type = self.panel_type_var.get()
        panel_type = panel_info.get(selected_panel_type)
        solar_array.panel_type = panel_type

        try:
            setback_length = float(self.setback_entry.get()) / self.scale_factor
        except ValueError:
            setback_length = 0
        solar_array.setback_length = setback_length

        solar_array.panel_rotation_tick = self.panel_rotate_var.get()
        solar_array.walk_gap_rotation_tick = self.walk_gap_rotate_var.get()

        panel_power,panel_width,panel_height = panel_type

        # Fixed size for small rectangles
        if solar_array.panel_rotation_tick==1:
            small_rect_width = panel_width/self.scale_factor # unit: meter/self.scale_factor
            small_rect_height = panel_height/self.scale_factor
        else:
            small_rect_width = panel_height/self.scale_factor # unit: meter/self.scale_factor
            small_rect_height = panel_width/self.scale_factor
        small_rect_size = (small_rect_width,small_rect_height)
        solar_array.small_rect_size = small_rect_size

        if solar_array.walk_gap_rotation_tick == 1:
            big_gap_width = float(self.walk_gap_entry.get()) / self.scale_factor
            small_gap_width = float(self.gap_width_entry.get()) / self.scale_factor
            gap_width = big_gap_width*1/2+small_gap_width*1/2

            small_gap_height = float(self.gap_height_entry.get()) / self.scale_factor
            big_gap_height = small_gap_height
            gap_height = small_gap_height

        else:
            small_gap_width = float(self.gap_width_entry.get()) / self.scale_factor
            big_gap_width = small_gap_width
            gap_width = small_gap_width

            big_gap_height = float(self.walk_gap_entry.get()) / self.scale_factor
            small_gap_height = float(self.gap_height_entry.get()) / self.scale_factor
            gap_height = big_gap_height*1/2+small_gap_height*1/2
        gap_size = (big_gap_width,big_gap_height,small_gap_width,small_gap_height,gap_width,gap_height)
        solar_array.gap_size = gap_size

        solar_array.tilt_angle = float(self.tilt_angle_entry.get())
        solar_array.lavitation = float(self.lavitage_entry.get())

        

    def new_panel_btn(self):
        self.already_draw_panel = 0
        self.update_panel_setting(self.pv1)
        self.panel_permanent_sets.append(self.pv1.copy())
        self.pv1.panel_points = []
        self.update_canvas()
        self.new_panel_button["state"] = tk.DISABLED
        
    
    
    def tilt_calcutation(self,angle):
        self.update_lat_lng()

        date_input_str = "2021/09/21 12:10:00"
        
        local_datetime = datetime.datetime.strptime(date_input_str, "%Y/%m/%d %H:%M:%S")
        pytz.timezone(self.tz)

        # Convert input to appropriate types
        # -Convert local to UTC
        date = local_datetime.astimezone(pytz.utc)

        # Calculate solar position using pysolar
        solar_altitude = get_altitude(self.Latitude, self.Longitude, date)
        # solar_azimuth = get_azimuth(self.Latitude, self.Longitude, date)
        solar_zenith = 90 - solar_altitude
        
        TF = self.calculate_transposition_factor(angle, Z_ref=solar_zenith)
        
        return TF
    
    def calculate_transposition_factor(self, beta, Z_ref=14.47):
        # Convert angles from degrees to radians
        beta = math.radians(beta) # the tilt angle of the solar panel
        Z_ref = math.radians(Z_ref)

        # Calculate transposition factor
        TF = (math.cos(beta) * math.cos(Z_ref) + math.sin(beta) * math.sin(Z_ref)) / math.cos(Z_ref)
        
        return TF

    def check_hit_detection(self, rect1, rect2):
        # Check for precise intersection between two rotated rectangles

        def project(rect, axis):
            # Project the rectangle onto the axis and return the min and max values
            center, size, angle = rect
            points = cv2.boxPoints(((center[0], center[1]), (size[0], size[1]), angle))
            return np.dot(points, axis), np.dot(points, axis)


        def axis_test(v0, v1, u0, u1):
            # Perform the SAT axis test
            return not (v1 < u0 or u1 < v0)

        # Extract relevant information from the rectangles
        center1, size1, angle1 = rect1
        center2, size2, angle2 = rect2

        # Calculate the axes for each rectangle
        axes = [
            (np.cos(angle1), np.sin(angle1)),
            (np.cos(angle1 + np.pi / 2), np.sin(angle1 + np.pi / 2)),
            (np.cos(angle2), np.sin(angle2)),
            (np.cos(angle2 + np.pi / 2), np.sin(angle2 + np.pi / 2))
        ]

        # Project rectangles onto each axis and perform the SAT axis tests
        for axis in axes:
            v0, v1 = project(rect1, axis)
            u0, u1 = project(rect2, axis)

            if not axis_test(v0, v1, u0, u1):
                return False  # No intersection on this axis, rectangles do not intersect

        return True  # Rectangles intersect on all axes, there is an intersection


    

    def draw_circle(self, x, y, r, canvasName,fill="",outline="black"): #center coordinates, radius
        x0 = x - r
        y0 = y - r
        x1 = x + r
        y1 = y + r
            
        return canvasName.create_oval(x0, y0, x1, y1,fill=fill,outline=outline)
    
    def draw_circle_stipple(self, x, y, r, canvasName,outline="gray50"): #center coordinates, radius
        x0 = x - r
        y0 = y - r
        x1 = x + r
        y1 = y + r
        y_old = 0

        # Draw stipple lines inside the circle
        for angle in range(0, 360, 1):  # Adjust the step size as needed
            radian_angle = math.radians(angle)
            x_start = x - int(r * math.cos(radian_angle))
            x_end = x + int(r * math.cos(radian_angle))
            y_start = y + int(r * math.sin(radian_angle))
            y_end = y + int(r * math.sin(radian_angle))
            if abs(y_start - y_old) > 1:
                canvasName.create_line(x_start, y_start, x_end, y_end,fill="gray50")
                y_old = y_start
            
        return canvasName.create_oval(x0, y0, x1, y1,fill="",outline=outline)
    
    def draw_2half_circle(self,canvas, x, y, radius,fill_left="green2",fill_right="red"):
        # Draw left half with green2 color
        canvas.create_arc(x - radius, y - radius, x + radius, y + radius, start=90, extent=180, fill=fill_left, outline="")

        # Draw right half with red color
        canvas.create_arc(x - radius, y - radius, x + radius, y + radius, start=-90, extent=180, fill=fill_right, outline="")

    def bound(self,low, high, value):
        return max(low, min(high, value))

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Radius of the Earth in kilometers

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c  # Distance in kilometers

        return distance
    
    def find_nearest_location(self, user_lat, user_lng, locations):
        min_distance = float('inf')
        nearest_location = None

        for location in locations:
            lat = location['lat']
            lng = location['lng']
            distance = self.haversine(user_lat, user_lng, lat, lng)

            if distance < min_distance:
                min_distance = distance
                nearest_location = location

        return nearest_location


def main():
    root = tk.Tk()
    app = SolarPlanelPlacerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
