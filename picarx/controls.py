from picarx_improved import Picarx
import logging
import time
import cv2
import time
import io
import numpy as np
from vilib import Vilib
logging_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO, datefmt="%H:%M:%S")
logging.getLogger().setLevel(logging.DEBUG)


class Sensing():
    def __init__(self, camera=False):
        self.px = Picarx()
        if camera:
            self.px.set_cam_tilt_angle(-30)
            time.sleep(0.1)
            Vilib.camera_start(vflip=False,hflip=False)
            Vilib.display(local=True,web=True)
            self.name = 'img'
            self.path = f"picarx"
            time.sleep(0.5)
    
    def get_grayscale(self):
        return self.px.get_grayscale_data()

    def get_camera_image(self):
        # function that gets a camera image
        Vilib.take_photo(self.name, self.path)
    
    def shutdown_camera(self):
        Vilib.camera_close()

class Interpretation():
    def __init__(self, sensitivity=2.0, polarity=1): # sensitivity and polarity should have default values
        self.sensitivity = sensitivity
        self.polarity = polarity # polarity -1 = darker line, 1 = lighter line
    
    def line_position(self, grayscale_data):
        """take an input argument of the same format as the output of the
sensor method. It should then identify if there is a sharp change between two adjacent sensor
values (indicative of an edge), and then using the edge location and sign to determine both
whether the system is to the left or right of being centered, and whether it is very off-center
or only slightly off-center. Make this function robust to different lighting conditions, and with
an option to have the “target” darker or lighter than the surrounding floor."""
        if self.polarity == 1:
            # logging.debug("lighter")
            grayscale_data = [grayscale_datapoint - min(grayscale_data) for grayscale_datapoint in grayscale_data]
        elif self.polarity == -1:
            # logging.debug("darker")
            grayscale_data = [grayscale_datapoint - max(grayscale_data) for grayscale_datapoint in grayscale_data]
        left_grayscale, center_grayscale, right_grayscale = [abs(value) for value in grayscale_data]
        if left_grayscale > right_grayscale:
            # logging.debug(f"L > R: {(center_grayscale-left_grayscale)/max(left_grayscale, center_grayscale)}")
            if (center_grayscale-left_grayscale)/max(left_grayscale, center_grayscale) < 0:
                return self.polarity*(abs((center_grayscale-left_grayscale)/max(left_grayscale, center_grayscale)))
            return self.polarity*(1 - (center_grayscale-left_grayscale)/max(left_grayscale, center_grayscale))
        # logging.debug(f"R > L: {(center_grayscale-right_grayscale)/max(right_grayscale, center_grayscale)}")
        if (center_grayscale-right_grayscale)/max(right_grayscale, center_grayscale) < 0:
            return self.polarity*((center_grayscale-right_grayscale)/max(right_grayscale, center_grayscale))
        return self.polarity*(-1 + (center_grayscale-right_grayscale)/max(right_grayscale, center_grayscale))
        
    def line_position_camera(self, image_path, image_name):
        """Takes camera data and uses OpenCV to convert to grayscale image, thresholds to find line to follow, sets coordinate to -1 if line on far left of screen, sets to 1 if on far right of screen"""
        camera_data = cv2.imread(f'{image_path}/{image_name}.jpg')
        _, width, _ = camera_data.shape
        grayscale = cv2.cvtColor(camera_data, cv2.COLOR_BGR2GRAY)
        # Threshold
        if self.polarity == 1:
            _, binary = cv2.threshold(grayscale, 200, 255, cv2.THRESH_BINARY)  # Lighter line
        else:
            _, binary = cv2.threshold(grayscale, 50, 255, cv2.THRESH_BINARY_INV)  # Darker line

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 0.0

        largest_contour = max(contours, key=cv2.contourArea)
        centroid = cv2.moments(largest_contour)
        if centroid['m00'] !=0:
            centroid_x = int(centroid['m10'] / centroid['m00'])
            normalized_position = (centroid_x - width / 2) / (width / 2)
            return normalized_position
        return 0.0
    
# Create sensor and interpreter classes for the ultrasonic sensors, along with a controller that
# moves the car forward if the way forward is clear, and stops it if there is an obstacle imme-
# diately in front of it

class SensingUltrasonic():
    def __init__(self, car):
        self.px = car
        
    def read_distance(self):
        distance = round(self.px.ultrasonic.read(), 2)
        # print("ULTRASONIC DISTANCE: ",distance)
        return distance


class InterpretationUltrasonic():
    def __init__(self, distance_threshold=20): # sensitivity and polarity should have default values
        self.distance_threshold = distance_threshold
    
    def check_obstacle(self, ultrasonic_data):
        if ultrasonic_data <= self.distance_threshold and ultrasonic_data >= 0:
            # logging.debug("OBSTACLE OBSTACLE OBSTACLE")
            return True
        else:
            # logging.debug("NO OBSTACLES")
            return False

class Controller():
    def __init__(self, scaling_factor=25):
        self.angle_scale = scaling_factor
        
    def follow_line(self, car, line_position):
        # logging.debug(f"\tdriving forward at angle: {line_position*self.angle_scale}")
        if line_position < 0.2 and line_position > -0.2:
            car.set_dir_servo_angle(0)
            car.forward(20)
        else:
            car.set_dir_servo_angle(line_position*self.angle_scale)
            car.forward(20)
        # car.move_forward_with_steering(speed=20, angle=line_position*self.angle_scale, duration = 0.05)
    
    def stop_motors(self, car):
        car.stop()
    
    def stop(self, car):
        car.stop()
    

if __name__ == "__main__":
    px_sensing = Sensing(camera=True)
    px_interpret = Interpretation(sensitivity=2.0, polarity=-1)
    px_controller = Controller()
    while True:
        camera_image = px_sensing.get_camera_image()
        # logging.debug(f"{grayscale_values}")
        line_position = px_interpret.line_position_camera(px_sensing.path, px_sensing.name)
        logging.debug(f"\tline_position: {line_position}")
        px_controller.follow_line(car=px_sensing.px, line_position=line_position)
        #time.sleep(0.2)