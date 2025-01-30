import time
import concurrent.futures
from readerwriterlock import rwlock
from controls import Sensing, Interpretation, Controller

class MessageBus:
    def __init__(self):
        self.message = None
        # self.lock = rwlock.RWLockWriteD()
    
    def write(self, message_content):
        # with self.lock.gen_wlock():
        self.message = message_content
    
    def read(self):
        # with self.lock.gen_rlock():
        message = self.message
        return message

# Producer: sensor collecting data and writing to the producer bus
def producer(bus, delay_time):
    while True:
        camera_image = px_sensing.get_camera_image()
        print(f"[Producer] Collected camera image: {camera_image}")
        bus.write(camera_image)
        time.sleep(delay_time)


# Consumer-Producer: Reads sensor data, processes it, writes to the consumer bus
def consumer_producer(producer_bus, consumer_producer_bus, delay_time):
    while True:
        camera_data = producer_bus.read()
        if camera_data is not None:
            line_position = px_interpret.line_position_camera(px_sensing.path, px_sensing.name)
            print(f"[Consumer Producer] line_position: {line_position}")
            consumer_producer_bus.write(line_position)
        time.sleep(delay_time)


# Consumer: Reads data and acts on it
def consumer(consumer_producer_bus, delay_time):
    while True:
        line_position = consumer_producer_bus.read()
        if line_position is not None:
            print(f"[Consumer] Moving based on line location: {line_position}")
            px_controller.follow_line(car=px_sensing.px, line_position=line_position)
        time.sleep(delay_time)


if __name__ == "__main__":
    # from controls.py script:
    px_sensing = Sensing(camera=True)
    px_interpret = Interpretation(sensitivity=2.0, polarity=-1)
    px_controller = Controller()
    
    # Create message buses
    sensor_bus = MessageBus()
    interpretation_bus = MessageBus()

    # Define delays
    sensor_delay = 1  # 1 second
    interpreter_delay = 1  # 1 second
    controller_delay = 1  # 1 second

    # Run components concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Submit the tasks to the executor
        eSensor = executor.submit(producer, sensor_bus, sensor_delay)
        eInterpreter = executor.submit(consumer_producer, sensor_bus, interpretation_bus, interpreter_delay)
        eController = executor.submit(consumer, interpretation_bus, controller_delay)

    # Ensure exceptions are surfaced
    eSensor.result()
    eInterpreter.result()
    eController.result()

# #######
#     while True:
        
#         line_position = px_interpret.line_position_camera(px_sensing.path, px_sensing.name)
#         logging.debug(f"\tline_position: {line_position}")
#         px_controller.follow_line(car=px_sensing.px, line_position=line_position)
