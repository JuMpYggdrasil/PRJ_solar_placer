import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import simpledialog
import math


class AreaMeasurementApp:
    def __init__(self, master, image_path):
        self.master = master
        self.master.title("Area Measurement Tool")

        # Load the original image
        self.original_image = Image.open(image_path)

        # Resize the image to half its original size
        new_size = (int(self.original_image.width *2/3), int(self.original_image.height *2/3))
        self.original_image = self.original_image.resize(new_size, Image.Resampling.LANCZOS)

        self.tk_image = ImageTk.PhotoImage(self.original_image)

        # Create Canvas
        self.canvas = tk.Canvas(self.master, width=self.original_image.width, height=self.original_image.height)
        self.canvas.pack()

        # Display the original image on the canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        # Create a frame for the first line (area_label and distance_label)
        frame1 = tk.Frame(self.master)
        frame1.pack(side=tk.TOP)

        # Store clicked points
        self.points = []
        self.distance_labels = []

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

        # Create a frame for the second line (buttons)
        frame2 = tk.Frame(self.master)
        frame2.pack(side=tk.TOP)

        # Create a button to calculate rectangle properties (initially disabled)
        self.calculate_button1 = tk.Button(frame2, text="Jinko 550W", command=self.calculate_rectangle1,
                                        state=tk.DISABLED)
        self.calculate_button1.pack(side=tk.LEFT)



        # Create a button to calculate rectangle properties (initially disabled)
        self.calculate_button2 = tk.Button(frame2, text="Jinko 600W", command=self.calculate_rectangle2,
                                        state=tk.DISABLED)
        self.calculate_button2.pack(side=tk.LEFT)


        # Create a frame for the third line (total_rectangles_label)
        frame3 = tk.Frame(self.master)
        frame3.pack(side=tk.TOP)

        # Create a label to display the total number of rectangles
        self.total_rectangles_label = tk.Label(frame3, text="Total Rectangles: 0")
        self.total_rectangles_label.pack(side=tk.LEFT)

    def on_canvas_click(self, event):
        x, y = event.x, event.y
        self.points.append((x, y))
        if len(self.points) <= 2:
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="purple")
        else:
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="red")

        # If the first two points are clicked, prompt the user to enter the scale factor
        if len(self.points) == 2:
            d_val = simpledialog.askfloat("Scale Factor", "Enter the scale factor (pixels to meters):")
            pixel_distance = ((self.points[-2][0] - self.points[-1][0]) ** 2 + (
                        self.points[-2][1] - self.points[-1][1]) ** 2) ** 0.5
            self.scale_factor = d_val / pixel_distance
            print("scale_factor: ")
            print(self.scale_factor)
            if self.scale_factor is None:
                # If the user cancels, clear the points and return
                self.points = []
                return

        # If more than three points are clicked, draw a line to close the loop
        if len(self.points) > 3:
            # self.canvas.create_line(self.points[-2], self.points[-1], fill="blue")
            area = self.calculate_area()
            self.area_label.config(text=f"Area: {area:.2f} square meters")
            distance = self.calculate_distance()
            self.distance_label.config(text=f"Distance: {distance:.2f} meters")

        # Enable the calculate button when six points are clicked
        if len(self.points) == 6:
            self.calculate_button1["state"] = tk.NORMAL
            self.calculate_button2["state"] = tk.NORMAL

    def on_mousewheel(self, event):
        # Update the zoom factor based on the mouse wheel movement
        if event.delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor /= 1.1

        # Resize the image based on the zoom factor
        width = int(self.original_image.width * self.zoom_factor)
        height = int(self.original_image.height * self.zoom_factor)
        resized_image = self.original_image.resize((width, height), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)

        # Update the canvas with the resized image
        self.canvas.config(width=width, height=height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def calculate_area(self):
        # Shoelace formula to calculate the area of a polygon
        area_pixels = 0
        num_points = len(self.points)

        for i in range(2, num_points - 1):
            area_pixels += (
                        self.points[i][0] * self.points[i + 1][1] - self.points[i + 1][0] * self.points[i][1])

        # Add the last edge (closing the loop)
        area_pixels += (
                    self.points[num_points - 1][0] * self.points[2][1] - self.points[2][0] * self.points[
                num_points - 1][1])

        # Take the absolute value and divide by 2
        area_pixels = abs(area_pixels) / 2.0

        # Convert pixels squared to square meters using the scale factor
        area_square_meters = area_pixels * (self.scale_factor ** 2)

        return area_square_meters

    def calculate_distance(self):
        # Calculate the distance between the last two points in meters
        pixel_distance = (
                (self.points[-2][0] - self.points[-1][0]) ** 2 + (self.points[-2][1] - self.points[-1][1]) ** 2) ** 0.5
        distance_in_meters = pixel_distance * self.scale_factor
        return distance_in_meters

    def draw_rotated_rectangle(self, center, size, angle, color="lightblue", stipple="gray50"):
        # Calculate the coordinates of the four corners of the rotated rectangle
        w, h = size
        w = w*0.95
        h = h*0.95
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
        self.canvas.create_polygon(x1, y1, x2, y2, x3, y3, x4, y4, fill=color, stipple=stipple)

    def draw_small_rectangles(self, center, size, angle,panel):
        panel_power,panel_width,panel_height = panel
        # Fixed size for small rectangles
        small_rect_width = panel_width/self.scale_factor # unit: meter/self.scale_factor
        small_rect_height = panel_height/self.scale_factor
        small_size = (small_rect_width,small_rect_height)

        gap_width = 0.2 / self.scale_factor  # unit: meter
        big_gap_height = 0.6/self.scale_factor
        small_gap_height = 0.2/self.scale_factor
        gap_height = big_gap_height*1/2+small_gap_height*1/2

        # Calculate the number of rectangles that can fit within the rotated rectangle
        w, h = size

        num_rectangles_horizontal = int((w / (small_rect_width + gap_width)))  # Adjust the spacing as needed
        num_rectangles_vertical = int((h / (small_rect_height + gap_height)))  # Adjust the spacing as needed

        for i in range(num_rectangles_horizontal):
            for j in range(num_rectangles_vertical):
                # Calculate the rotated offset
                x_offset = i * (small_rect_width + gap_width)
                if (j % 2)==0:
                    y_offset = j * (small_rect_height + gap_height) + big_gap_height/2
                else:
                    y_offset = j * (small_rect_height + gap_height) - small_gap_height/2

                rotated_x1, rotated_y1 = self.rotate_point(
                    center[0] - w / 2 + small_rect_width + x_offset,
                    center[1] - h / 2 + small_rect_height+ y_offset,
                    center[0],
                    center[1],
                    angle
                )
                each_center = (rotated_x1,rotated_y1)

                self.draw_rotated_rectangle(each_center, small_size, angle,color="darkblue",stipple=None)

        x1, y1 = center[0] - 4, center[1] - 4
        x2, y2 = center[0] + 4, center[1] + 4
        self.canvas.create_oval(x1, y1, x2, y2, fill="green")

        # Update the label to display the total number of rectangles
        num_rectangles_total = num_rectangles_horizontal * num_rectangles_vertical
        kW_total = panel_power * num_rectangles_total /1000
        self.total_rectangles_label.config(text=f"panel:{num_rectangles_horizontal}x{num_rectangles_vertical}= {num_rectangles_total} , kWp: {kW_total} , Helio:({kW_total*0.75})")


    def rotate_point(self, x, y, center_x, center_y, angle):
        # Rotate a point (x, y) around a center (center_x, center_y) by a given angle (in degrees)
        angle_rad = math.radians(angle)
        rotated_x = center_x + (x - center_x) * math.cos(angle_rad) - (y - center_y) * math.sin(angle_rad)
        rotated_y = center_y + (x - center_x) * math.sin(angle_rad) + (y - center_y) * math.cos(angle_rad)
        return rotated_x, rotated_y

    def calculate_rectangle1(self):
        # Calculate approximate rectangle properties
        # Use the last four points to calculate rectangle properties
        x_coords, y_coords = zip(*self.points[-4:])
        points = np.array(self.points[-4:], dtype=np.int32)

        # Find the minimum area rectangle using OpenCV
        rect = cv2.minAreaRect(points)

        # Unpack the rectangle properties
        center, size, angle = rect
        # Draw the rotated rectangle on the canvas
        self.draw_rotated_rectangle(center, size, angle)
        self.draw_small_rectangles(center, size, angle,(550,2.278,1.134))


    def calculate_rectangle2(self):
        # Calculate approximate rectangle properties
        # Use the last four points to calculate rectangle properties
        x_coords, y_coords = zip(*self.points[-4:])
        points = np.array(self.points[-4:], dtype=np.int32)

        # Find the minimum area rectangle using OpenCV
        rect = cv2.minAreaRect(points)

        # Unpack the rectangle properties
        center, size, angle = rect
        # Draw the rotated rectangle on the canvas
        self.draw_rotated_rectangle(center, size, angle)
        self.draw_small_rectangles(center, size, angle,(600,2.465,1.134))


def main():
    root = tk.Tk()
    app = AreaMeasurementApp(root, r"C:\Users\Egat\Desktop\Screenshot 2023-11-17 005107.png")
    root.mainloop()


if __name__ == "__main__":
    main()
