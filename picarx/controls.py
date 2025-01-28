from picarx_improved import Picarx
import logging
import math
import time
logging_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO, datefmt="%H:%M:%S")
logging.getLogger().setLevel(logging.DEBUG)


class Sensing():
    def __init__(self):
        self.px = Picarx()
    
    def get_grayscale(self):
        return self.px.get_grayscale_data()

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
        
class Controller():
    def __init__(self, scaling_factor=20):
        self.angle_scale = scaling_factor
        
    def follow_line(self, car, line_position):
        # logging.debug(f"\tdriving forward at angle: {line_position*self.angle_scale}")
        car.set_dir_servo_angle(line_position*self.angle_scale)
        car.forward(20)
        # car.move_forward_with_steering(speed=20, angle=line_position*self.angle_scale, duration = 0.05)

if __name__ == "__main__":
    px_sensing = Sensing()
    px_interpret = Interpretation(sensitivity=2.0, polarity=-1)
    px_controller = Controller()
    while True:
        grayscale_values = px_sensing.get_grayscale()
        # logging.debug(f"{grayscale_values}")
        line_position = px_interpret.line_position(grayscale_values)
        logging.debug(f"\tline_position: {line_position}")
        px_controller.follow_line(car=px_sensing.px, line_position=line_position)
        time.sleep(0.01)
