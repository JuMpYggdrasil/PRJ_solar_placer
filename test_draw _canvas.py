import tkinter as tk
from tkinter import colorchooser
import random

class CircleDrawer:
    def __init__(self, root):
        self.root = root
        self.root.title("Circle Drawer")

        self.canvas = tk.Canvas(root, width=600, height=400, bg="white")
        self.canvas.pack()

        self.drawn_objects = []
        self.canvas.bind("<Button-1>", self.draw_circle)

        self.undo_button = tk.Button(root, text="Undo", command=self.undo)
        self.undo_button.pack()

    def draw_circle(self, event):
        x, y = event.x, event.y

        # Record the current state of the canvas
        image = self.get_image()
        self.drawn_objects.append(image)

        # Draw the circle at the clicked point with a random color
        color = self.get_random_color()
        radius = 20
        circle = self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, tags=("circle",))

        self.drawn_objects.append(circle)

    def undo(self):
        if self.drawn_objects:
            # Remove the last drawn circle and its recorded state
            self.canvas.delete(self.drawn_objects.pop())
            self.canvas.delete(self.drawn_objects.pop())

    def get_image(self):
        # Get the current state of the canvas as a PhotoImage
        image = tk.PhotoImage(width=self.canvas.winfo_reqwidth(), height=self.canvas.winfo_reqheight())
        self.canvas.postscript(file=image, colormode="color")
        return image

    def get_random_color(self):
        # Generate a random RGB color
        color = "#{:02x}{:02x}{:02x}".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        return color

if __name__ == "__main__":
    root = tk.Tk()
    app = CircleDrawer(root)
    root.mainloop()
