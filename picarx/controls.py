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
    def __init__(self, sensitivity=50, polarity="darker"): # sensitivity and polarity should have default values
        self.sensitivity = sensitivity
        self.polarity = polarity
    
    def line_position(self, grayscale_data):
        """take an input argument of the same format as the output of the
sensor method. It should then identify if there is a sharp change between two adjacent sensor
values (indicative of an edge), and then using the edge location and sign to determine both
whether the system is to the left or right of being centered, and whether it is very off-center
or only slightly off-center. Make this function robust to different lighting conditions, and with
an option to have the “target” darker or lighter than the surrounding floor."""
        # calculate differences between the 3 sensors
        differences = [
            grayscale_data[i + 1] - grayscale_data[i]
            for i in range(len(grayscale_data) - 1)
        ]
        if self.polarity == "darker":
            differences = [-diff for diff in differences]

        # find maximum difference and its index
        max_change = max(differences, key=abs)
        max_index = differences.index(max_change)

        # Determine edge characteristics
        is_edge = abs(max_change) > self.sensitivity
        if is_edge:
            position = "left" if max_change > 0 else "right"
            offset = "sharp" if abs(max_change) > 2 * self.sensitivity else "slight"
            logging.debug(f"position: {position}, offset: {offset}")
            return {"position": position, "offset": offset}
        else:
            return {"position": "center", "offset": "slight"}
        

if __name__ == "__main__":
    px = Sensing()
    px_interpret = Interpretation()
    grayscale_values = px.get_grayscale()
    logging.debug(f"{grayscale_values}")
    line_position = px_interpret.line_position(grayscale_values)
    