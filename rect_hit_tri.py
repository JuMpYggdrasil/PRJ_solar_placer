import matplotlib.pyplot as plt
import numpy as np
import cv2

def check_hit_detection(rect, triangle):
    def project(rect_or_triangle, axis):
        points = rect_or_triangle if len(rect_or_triangle) == 3 else cv2.boxPoints(((rect_or_triangle[0], rect_or_triangle[1]), (rect_or_triangle[2], rect_or_triangle[3]), rect_or_triangle[4]))
        return np.dot(points, axis)

    def axis_test(v0, v1, u0, u1):
        return not (v1 < u0 or u1 < v0)

    # Calculate the axes for the rectangle and the triangle
    axes = [
        (np.cos(rect[4]), np.sin(rect[4])),
        (np.cos(rect[4] + np.pi / 2), np.sin(rect[4] + np.pi / 2)),
        (np.cos(triangle[2]), np.sin(triangle[2])),
        (np.cos(triangle[2] + np.pi / 2), np.sin(triangle[2] + np.pi / 2)),
    ]

    # Project rectangles and triangles onto each axis and perform the SAT axis tests
    for axis in axes:
        v = project(rect, axis)
        u = project(triangle, axis)

        v0, v1 = np.min(v), np.max(v)
        u0, u1 = np.min(u), np.max(u)

        if not axis_test(v0, v1, u0, u1):
            return False  # No intersection on this axis, shapes do not intersect

    return True  # Shapes intersect on all axes, there is an intersection


def draw_rect(rect):
    rect_points = cv2.boxPoints(((rect[0], rect[1]), (rect[2], rect[3]), rect[4]))
    rect_points = np.int_(rect_points)
    plt.fill(rect_points[:, 0], rect_points[:, 1], edgecolor='r', facecolor='r', alpha=0.4)

def draw_triangle(triangle):
    plt.fill(triangle[:, 0], triangle[:, 1], edgecolor='b', facecolor='b', alpha=0.4)

def draw_hit_detection(rect, triangle, intersection):
    plt.figure()

    draw_rect(rect)
    draw_triangle(triangle)

    plt.title(f'Intersection: {intersection}')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.grid(True)
    plt.show()

# Example usage:
rect = (70, 70, 20, 20, 45)  # Rectangle: (center_x, center_y, width, height, angle)
triangle = np.array([(80, 70), (70, 90), (90, 90)])  # Triangle: Three corner points

intersection = check_hit_detection(rect, triangle)

draw_hit_detection(rect, triangle, intersection)