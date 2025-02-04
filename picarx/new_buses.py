import time
import logging
from RossROS import Bus, Producer, ConsumerProducer, Consumer, Timer, runConcurrently
from controls import Sensing, Interpretation, Controller, SensingUltrasonic, InterpretationUltrasonic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# my control classes
px_sensing = Sensing(camera=True)
px_sensing_ultrasonic = SensingUltrasonic(car=px_sensing.px)
px_interpret = Interpretation(sensitivity=2.0, polarity=-1)
px_controller = Controller()

# message buses
sensor_bus = Bus(name="Sensor Bus")
interpretation_bus = Bus(name="Interpretation Bus")
termination_bus = Bus(name="Termination Bus")

# Define delays
sensor_delay = 0.1
interpreter_delay = 0.1
controller_delay = 0.1
run_time = 5

# Get grayscale data
def get_grayscale_data():
    grayscale = px_sensing.px.get_grayscale_data()
    logging.info(f"GRAYSCALE: {grayscale}")
    return grayscale

def get_ultrasonic_data():
    ultrasonic_distance = px_sensing_ultrasonic.read_distance()
    logging.info(f"ULTRASONIC DISTANCE: {ultrasonic_distance}")
    return ultrasonic_distance

# Interpret grayscale data
def interpret_line_position(grayscale_data):
    try:
        line_position = px_interpret.line_position(grayscale_data)
        logging.info(f"LINE POSITION: {line_position}")
        return line_position
    except Exception as e:
        logging.info(f"ERROR with line position")
        return 0

# Move vehicle based on line position
def control_vehicle(line_position):
    logging.info(f"CONTROL VEHICLE Moving based on line position: {line_position}")
    px_controller.follow_line(car=px_sensing.px, line_position=line_position)

# runtime using Timer class
timer = Timer(
    output_buses=termination_bus,
    duration=run_time,
    delay=0.1,
    termination_buses=termination_bus,
    name="Run Timer"
)

# Use RossROS.py classes
# sensor_producer = Producer(
#     producer_function=get_grayscale_data,
#     output_buses=sensor_bus,
#     delay=sensor_delay,
#     termination_buses=termination_bus,
#     name="Sensor Producer"
# )

sensor_producer = Producer(
    producer_function=get_ultrasonic_data,
    output_buses=sensor_bus,
    delay=sensor_delay,
    termination_buses=termination_bus,
    name="Sensor Producer Ultrasonic"
)

line_interpreter = ConsumerProducer(
    consumer_producer_function=interpret_line_position,
    input_buses=sensor_bus,
    output_buses=interpretation_bus,
    delay=interpreter_delay,
    termination_buses=termination_bus,
    name="Line Interpreter"
)

vehicle_controller = Consumer(
    consumer_function=control_vehicle,
    input_buses=interpretation_bus,
    delay=controller_delay,
    termination_buses=termination_bus,
    name="Vehicle Controller"
)

# Run all components concurrently
try:
    runConcurrently([sensor_producer, line_interpreter, vehicle_controller, timer])
except KeyboardInterrupt:
    logging.info("[Main] Exiting gracefully")
    px_controller.stop(car=px_sensing.px)
    px_sensing.shutdown_camera()
finally:
    logging.info("[Main] Shutting down")
    px_controller.stop(car=px_sensing.px)
    px_sensing.shutdown_camera()
