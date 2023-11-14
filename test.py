import tkinter as tk
import math

def rotate_point(point, angle, center):
    """Rotate a point around a center by a specified angle."""
    x, y = point
    cx, cy = center
    new_x = (x - cx) * math.cos(angle) - (y - cy) * math.sin(angle) + cx
    new_y = (x - cx) * math.sin(angle) + (y - cy) * math.cos(angle) + cy
    return new_x, new_y

def calculate_rows_columns(points, rectangle_size, gap, angle):
    # Rotate all points
    center = (0, 0)  # You may need to adjust the center based on your data
    rotated_points = [rotate_point(point, math.radians(angle), center) for point in points]

    # Find the bounding box
    min_x = min(rotated_points, key=lambda p: p[0])[0]
    max_x = max(rotated_points, key=lambda p: p[0])[0]
    min_y = min(rotated_points, key=lambda p: p[1])[1]
    max_y = max(rotated_points, key=lambda p: p[1])[1]

    # Calculate rows and columns
    width_of_bounding_box = max_x - min_x
    height_of_bounding_box = max_y - min_y

    columns = math.floor(width_of_bounding_box / (rectangle_size[0] + gap[0]))
    rows = math.floor(height_of_bounding_box / (rectangle_size[1] + gap[1]))

    return rows, columns, rotated_points

def draw_rectangles_and_boundary(canvas, rows, columns, rectangle_size, gap, angle, rotated_points):
    # Draw boundary lines
    for i in range(len(rotated_points)):
        x1, y1 = rotated_points[i]
        x2, y2 = rotated_points[(i + 1) % len(rotated_points)]
        canvas.create_line(x1, y1, x2, y2, fill="blue")

    # Draw rectangles
    for row in range(rows):
        for col in range(columns):
            x = col * (rectangle_size[0] + gap[0])
            y = row * (rectangle_size[1] + gap[1])
            canvas.create_rectangle(x, y, x + rectangle_size[0], y + rectangle_size[1])

# Example usage:
points = [(10,10), (10, 60), (90, 90), (80, 30)]  # Replace with your actual points
rectangle_size = (5, 8)
gap = (1, 1)
angle = 45  # Replace with your desired angle

rows, columns, rotated_points = calculate_rows_columns(points, rectangle_size, gap, angle)

# Create the GUI
root = tk.Tk()
root.title("Rectangles Drawing")

# Create a canvas to draw on
canvas = tk.Canvas(root, width=200, height=200)  # Adjust the size as needed
canvas.pack()

# Draw rectangles and boundary
draw_rectangles_and_boundary(canvas, rows, columns, rectangle_size, gap, angle, rotated_points)

# Start the GUI main loop
root.mainloop()
