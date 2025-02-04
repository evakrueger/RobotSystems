import time
import logging
from RossROS import Bus, Producer, ConsumerProducer, Consumer, Timer, runConcurrently
from controls import Sensing, Interpretation, Controller

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# my control classes
px_sensing = Sensing(camera=True)
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
def produce_sensor_data():
    grayscale = px_sensing.px.get_grayscale_data()
    logging.info(f"[Producer] Collected grayscale data: {grayscale}")
    return grayscale

# Interpret grayscale data
def interpret_line_position(grayscale_data):
    line_position = px_interpret.line_position(grayscale_data)
    logging.info(f"[Consumer-Producer] Line position: {line_position}")
    return line_position

# Move vehicle based on line position
def control_vehicle(line_position):
    logging.info(f"[Consumer] Moving based on line position: {line_position}")
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
sensor_producer = Producer(
    producer_function=produce_sensor_data,
    output_buses=sensor_bus,
    delay=sensor_delay,
    termination_buses=termination_bus,
    name="Sensor Producer"
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
    px_controller.stop()
finally:
    logging.info("[Main] Shutting down")
    px_controller.stop()