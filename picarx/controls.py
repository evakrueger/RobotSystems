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
    def __init__(self, sensitivity, polarity):
        self.sensitivity = sensitivity
        self.polarity = polarity

if __name__ == "__main__":
    px = Sensing()
    logging.debug(f"{px.get_grayscale()}")