from picarx_improved import Picarx
import logging
logging_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO, datefmt="%H:%M:%S")
logging.getLogger().setLevel(logging.DEBUG)


class Sensing():
    def __init__(self):
        self.px = Picarx()
    
    def get_grayscale(self):
        return self.px.get_grayscale_data()

class Interpretation():
    def __init__(self, sensitivity=100, polarity="darker"): # sensitivity and polarity should have default values
        self.sensitivity = sensitivity
        self.polarity = polarity
    
    def line_position(self, grayscale_data):
        """take an input argument of the same format as the output of the
sensor method. It should then identify if there is a sharp change between two adjacent sensor
values (indicative of an edge), and then using the edge location and sign to determine both
whether the system is to the left or right of being centered, and whether it is very off-center
or only slightly off-center. Make this function robust to different lighting conditions, and with
an option to have the “target” darker or lighter than the surrounding floor."""
        left_grayscale = grayscale_data[0]
        center_grayscale = grayscale_data[1]
        right_grayscale = grayscale_data[2]
        logging.debug(f"left, center, and right divided by center: {left_grayscale/center_grayscale}, {center_grayscale/center_grayscale}, {right_grayscale/center_grayscale}")
        

        return {"position": "center", "offset": "slight"}
        

if __name__ == "__main__":
    px = Sensing()
    px_interpret = Interpretation()
    grayscale_values = px.get_grayscale()
    logging.debug(f"{grayscale_values}")
    line_position = px_interpret.line_position(grayscale_values)
    