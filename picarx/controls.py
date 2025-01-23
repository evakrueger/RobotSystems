from picarx_improved import Picarx
import logging
import math
logging_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO, datefmt="%H:%M:%S")
logging.getLogger().setLevel(logging.DEBUG)


class Sensing():
    def __init__(self):
        self.px = Picarx()
    
    def get_grayscale(self):
        return self.px.get_grayscale_data()

class Interpretation():
    def __init__(self, sensitivity=2.0, polarity="darker"): # sensitivity and polarity should have default values
        self.sensitivity = sensitivity
        self.polarity = polarity
    
    def line_position(self, grayscale_data):
        """take an input argument of the same format as the output of the
sensor method. It should then identify if there is a sharp change between two adjacent sensor
values (indicative of an edge), and then using the edge location and sign to determine both
whether the system is to the left or right of being centered, and whether it is very off-center
or only slightly off-center. Make this function robust to different lighting conditions, and with
an option to have the “target” darker or lighter than the surrounding floor."""
        if self.polarity == "lighter":
            grayscale_data = [grayscale_datapoint - min(grayscale_data) for grayscale_datapoint in grayscale_data]
        elif self.polarity == "darker":
            grayscale_data = [grayscale_datapoint - max(grayscale_data) for grayscale_datapoint in grayscale_data]
        left_grayscale, center_grayscale, right_grayscale = [abs(value) for value in grayscale_data]
        # logging.debug(f"updated: {left_grayscale}, {center_grayscale}, {right_grayscale}")
        # very left = 1
        # slightly left = 0.5
        # center = 0
        # slightly right = -0.5
        # very right = -1
        if left_grayscale > right_grayscale:
            # logging.debug(f"L > R: {(center_grayscale-left_grayscale)/max(left_grayscale, center_grayscale)}")
            if (center_grayscale-left_grayscale)/max(left_grayscale, center_grayscale) < 0:
                return abs((center_grayscale-left_grayscale)/max(left_grayscale, center_grayscale))
            return 1 - (center_grayscale-left_grayscale)/max(left_grayscale, center_grayscale)
        # logging.debug(f"R > L: {(center_grayscale-right_grayscale)/max(right_grayscale, center_grayscale)}")
        if (center_grayscale-right_grayscale)/max(right_grayscale, center_grayscale) < 0:
            return ((center_grayscale-right_grayscale)/max(right_grayscale, center_grayscale))
        return -1 + (center_grayscale-right_grayscale)/max(right_grayscale, center_grayscale)
        

if __name__ == "__main__":
    px_sensing = Sensing()
    px_interpret = Interpretation(sensitivity=2.0, polarity="darker")
    while True:
        grayscale_values = px_sensing.get_grayscale()
        # logging.debug(f"{grayscale_values}")
        line_position = px_interpret.line_position(grayscale_values)
        logging.debug(f"{line_position}")
    