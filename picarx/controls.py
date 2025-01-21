from picarx_improved import Picarx

class Sensing(object):
    def __init__(self):
        self.px = Picarx(self)
    
    def get_grayscale(self):
        self.px.get_grayscale_data()

if __name__ == "__main__":
    px = Picarx()
    px.get_grayscale_data()