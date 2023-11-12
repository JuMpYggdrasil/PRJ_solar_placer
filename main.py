import tkinter as tk
from PIL import Image, ImageTk
from tkinter import simpledialog


class AreaMeasurementApp:
    def __init__(self, master, image_path):
        self.master = master
        self.master.title("Area Measurement Tool")

        # Load the original image
        self.original_image = Image.open(image_path)
        self.tk_image = ImageTk.PhotoImage(self.original_image)

        # Create Canvas
        self.canvas = tk.Canvas(self.master, width=self.original_image.width, height=self.original_image.height)
        self.canvas.pack()

        # Display the original image on the canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        # Store clicked points
        self.points = []
        self.distance_labels = []

        # Create a label to display the measured area
        self.area_label = tk.Label(self.master, text="Area: ")
        self.area_label.pack()

        self.distance_label = tk.Label(self.master, text="Distance: ")
        self.distance_label.pack()

        # Zoom factor
        self.zoom_factor = 1.0

        # Scale factor (to be set by the user)
        self.scale_factor = None

        # Bind mouse click and scroll events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

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
            pixel_distance = ((self.points[-2][0] - self.points[-1][0])**2 + (self.points[-2][1] - self.points[-1][1])**2)**0.5
            self.scale_factor = d_val/pixel_distance
            # self.points.pop(0)
            if self.scale_factor is None:
                # If the user cancels, clear the points and return
                self.points = []
                return

        # If more than three points are clicked, draw a line to close the loop
        if len(self.points) > 3:
            self.canvas.create_line(self.points[-2], self.points[-1], fill="blue")
            area = self.calculate_area()
            self.area_label.config(text=f"Area: {area} square meters")
            distance = self.calculate_distance()
            self.distance_label.config(text=f"Distance: {distance:.2f} meters")

    def on_mousewheel(self, event):
        # Update the zoom factor based on the mouse wheel movement
        if event.delta > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor /= 1.1

        # Resize the image based on the zoom factor
        width = int(self.original_image.width * self.zoom_factor)
        height = int(self.original_image.height * self.zoom_factor)
        # resized_image = self.original_image.resize((width, height), "ANTIALIAS")
        resized_image = self.original_image.resize((width, height), 3)  # 3 corresponds to Image.ANTIALIAS
        self.tk_image = ImageTk.PhotoImage(resized_image)

        # Update the canvas with the resized image
        self.canvas.config(width=width, height=height)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def calculate_area(self):
        # Shoelace formula to calculate the area of a polygon
        area_pixels = 0
        num_points = len(self.points)

        for i in range(2,num_points - 1):
            area_pixels += (self.points[i][0] * self.points[i + 1][1] - self.points[i + 1][0] * self.points[i][1])

        # Add the last edge (closing the loop)
        area_pixels += (self.points[num_points - 1][0] * self.points[2][1] - self.points[2][0] * self.points[num_points - 1][1])

        # Take the absolute value and divide by 2
        area_pixels = abs(area_pixels) / 2.0

        # Convert pixels squared to square meters using the scale factor
        area_square_meters = area_pixels * (self.scale_factor ** 2)

        return area_square_meters
    
    def calculate_distance(self):
        # Calculate the distance between the last two points in meters
        pixel_distance = ((self.points[-2][0] - self.points[-1][0])**2 + (self.points[-2][1] - self.points[-1][1])**2)**0.5
        distance_in_meters = pixel_distance * self.scale_factor
        return distance_in_meters

def main():
    root = tk.Tk()
    app = AreaMeasurementApp(root, r"C:\Users\Egat\Desktop\Screenshot 2023-11-12 170355.png")

    root.mainloop()

if __name__ == "__main__":
    main()
