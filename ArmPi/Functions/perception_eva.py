#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/ArmPi/')
import cv2
import numpy as np
import time
import Camera
import threading
from LABConfig import *
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board
from CameraCalibration.CalibrationConfig import *

class ColorDetector:
    def __init__(self, target_color):
        # Initialize the ColorDetector with a target color.
        # :param target_color: The color name (string) to be detected (e.g., 'red').
        self.target_color = target_color  # Store the target color for detection.

    def preprocess_image(self, img):
        # Resize and apply Gaussian blur to the input image to reduce noise and improve detection.
        # :param img: Input image (frame) from the camera.
        # :return: Preprocessed image.
        size = (640, 480)  # Define standard frame size for consistency.
        frame_resized = cv2.resize(img, size, interpolation=cv2.INTER_NEAREST)  # Resize frame.
        frame_blurred = cv2.GaussianBlur(frame_resized, (11, 11), 11)  # Apply Gaussian blur to smooth the image.
        return frame_blurred

    def detect_color_contours(self, img, color_range):
        # Convert the image to LAB color space, apply color thresholding, and extract contours.
        # :param img: Preprocessed image.
        # :param color_range: Dictionary containing LAB color ranges for different colors.
        # :return: List of detected contours.
        frame_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)  # Convert BGR image to LAB color space.
        detect_color = self.target_color  # Get the target color for detection.

        # Apply color threshold to isolate the target color.
        frame_mask = cv2.inRange(frame_lab, color_range[detect_color][0], color_range[detect_color][1])
        # Perform morphological operations to remove noise and improve shape detection.
        opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((6, 6), np.uint8))  # Remove small noise.
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((6, 6), np.uint8))  # Fill small holes.

        # Find contours of the detected regions.
        contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[-2]
        return contours

    def get_largest_contour(self, contours):
        # Identify the largest contour from the detected ones.
        # :param contours: List of contours detected in the image.
        # :return: The largest contour and its area.
        max_contour = None
        max_area = 0

        for contour in contours:
            area = math.fabs(cv2.contourArea(contour))  # Compute contour area.
            if area > max_area and area > 300:  # Ignore small noise by setting a minimum area threshold.
                max_area = area
                max_contour = contour  # Update the largest contour.

        return max_contour, max_area  # Return the largest contour found.

    def get_object_position(self, contour):
        # Compute the position (center coordinates) of the detected object.

        # :param contour: The largest contour detected.
        # :return: (x, y) coordinates of the object's center or (None, None) if no object is found.
        if contour is not None:
            rect = cv2.minAreaRect(contour)  # Get the minimum bounding rectangle around the contour.
            center_x, center_y = rect[0]  # Extract the center coordinates.
            return int(center_x), int(center_y)  # Return integer values for pixel coordinates.

        return None, None  # Return None if no contour is detected.

    def process_frame(self, img, color_range):
        # Process a single frame to detect the target object and determine its position.
        # :param img: Input image frame.
        # :param color_range: Dictionary of LAB color ranges.
        # :return: (x, y) coordinates of the detected object.
        img_preprocessed = self.preprocess_image(img)  # Preprocess the input image.
        contours = self.detect_color_contours(img_preprocessed, color_range)  # Detect color-based contours.
        largest_contour, _ = self.get_largest_contour(contours)  # Get the largest detected contour.
        return self.get_object_position(largest_contour)  # Compute object position based on contour.


if __name__ == "__main__":
    # Define LAB color range for the target color (e.g., 'red').
    color_range = {
        'red': ((0, 150, 150), (255, 255, 255)),  # Example LAB color range for red detection.
        'blue': ((0, 50, -100), (50, 80, -40)),
        'green': ((30, 50, 50), (200, 255, 255))
    }

    # Initialize the color detector for red objects
    detector = ColorDetector(target_color='blue')

    # Initialize and open the camera
    my_camera = Camera.Camera()
    my_camera.camera_open()

    while True:
        img = my_camera.frame  # Capture frame from camera
        if img is not None:
            frame = img.copy()  # Copy the frame to avoid modifying the original
            
            # Process the frame using the color detection pipeline
            x, y = detector.process_frame(frame, color_range)

            # If an object is detected, draw it on the frame
            if x is not None and y is not None:
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)  # Draw a marker
                cv2.putText(frame, f"Block at ({x}, {y})", (x + 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)  # Display position

            cv2.imshow('Frame', frame)  # Show the processed frame

        key = cv2.waitKey(1)
        if key == 27:  # Press 'Esc' key to exit
            break

    # Cleanup resources
    my_camera.camera_close()
    cv2.destroyAllWindows()
