from picarx_improved import Picarx
import logging
logging_format = "%(asctime)s: %(message)s"
logging.basicConfig(format=logging_format, level=logging.INFO, datefmt="%H:%M:%S")
logging.getLogger().setLevel(logging.DEBUG)


class Sensing(object):
    def __init__(self):
        self.px = Picarx(self)
    
    def get_grayscale(self):
        return self.px.get_grayscale_data()

if __name__ == "__main__":
    px = Picarx()
    logging.debug(f"{px.get_grayscale_data()}")