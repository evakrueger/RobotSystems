import time
import concurrent.futures
from readerwriterlock import rwlock
from controls import Sensing, Interpretation, Controller

class MessageBus:
    def __init__(self):
        self.message = None
        self.lock = rwlock.RWLockWriteD()
    
    def write(self, message_content):
        with self.lock.gen_wlock():
            self.message = message_content
    
    def read(self):
        with self.lock.gen_rlock():
            message = self.message
        return message

# Producer: sensor collecting data and writing to the producer bus
def producer(bus, delay_time):
    try:
        while True:
            grayscale = px_sensing.px.get_grayscale_data()
            print(f"[Producer] Collected grayscale data: {grayscale}")
            bus.write(grayscale)
            time.sleep(delay_time)
    except KeyboardInterrupt:
        print("[Producer] Exiting gracefully")


# Consumer-Producer: Reads sensor data, processes it, writes to the consumer bus
def consumer_producer(producer_bus, consumer_producer_bus, delay_time):
    try:
        while True:
            grayscale_data = producer_bus.read()
            if grayscale_data is not None:
                line_position = px_interpret.line_position(grayscale_data)
                print(f"[Consumer Producer] grayscale data line_position: {line_position}")
                consumer_producer_bus.write(line_position)
            time.sleep(delay_time)
    except KeyboardInterrupt:
        print("[Consumer Producer] Exiting gracefully")


# Consumer: Reads data and acts on it
def consumer(consumer_producer_bus, delay_time):
    try:
        while True:
            line_position = consumer_producer_bus.read()
            if line_position is not None:
                print(f"[Consumer] Moving based on line location: {line_position}")
                px_controller.follow_line(car=px_sensing.px, line_position=line_position)
            time.sleep(delay_time)
    except KeyboardInterrupt:
        print("[Consumer] Exiting gracefully")
        px_controller.stop_motors()


if __name__ == "__main__":
    # from controls.py script:
    px_sensing = Sensing(camera=True)
    px_interpret = Interpretation(sensitivity=2.0, polarity=-1)
    px_controller = Controller()
    
    # Create message buses
    sensor_bus = MessageBus()
    interpretation_bus = MessageBus()

    # Define delays
    sensor_delay = 0.1  # 1 second
    interpreter_delay = 0.1  # 1 second
    controller_delay = 0.1  # 1 second

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
