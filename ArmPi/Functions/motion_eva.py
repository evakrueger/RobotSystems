#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/ArmPi/')
import cv2
import time
import Camera
import threading
from LABConfig import *
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board
from CameraCalibration.CalibrationConfig import *
import time
from perception_eva import ColorDetector

AK = ArmIK()
servo1 = 500

# initial position
def initMove():
    Board.setBusServoPulse(1, servo1 - 50, 300)
    Board.setBusServoPulse(2, 500, 500)
    AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)

def setBuzzer(timer):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(timer)
    Board.setBuzzer(0)
    
class MoveHandler:
    def __init__(self, perception):
        print("mover INIT")
        self.perception = perception
        self.AK = AK
        self.servo1 = servo1
        self.__isRunning = False
        self._stop = False
        self.first_move = True
        self.start_pick_up = False
        self.action_finish = False
        self.unreachable = False
        self.track = False
        self.detect_color = "None"
        self.world_X, self.world_Y = 0, 0
        self.coordinate = {
            'red': (-15 + 0.5, 12 - 0.5, 1.5),
            'green': (-15 + 0.5, 6 - 0.5, 1.5),
            'blue': (-15 + 0.5, 0 - 0.5, 1.5),
        }

    def move(self):
        while True:
            if self.perception.current_color != "None":
                current_color = self.perception.current_color

                desired_x, desired_y, desired_angle = self.perception.last_x, self.perception.last_y, self.perception.rotation_angle
                result = self.arm_kinematics.setPitchRangeMoving((desired_x, desired_y, self.desired_approach_height_grasp), -90, -90, 0)  

                if result:
                    time.sleep(result[2]/self.sleep_divider)

                    block_rotation = getAngle(desired_x, desired_y, desired_angle)
                    Board.setBusServoPulse(self.servo_1_id, self.gripper_closed - self.gripper_open, self.gripper_closed)
                    Board.setBusServoPulse(self.servo_2_id, block_rotation, self.gripper_closed)
                    time.sleep(self.sleep_time)

                    self.arm_kinematics.setPitchRangeMoving((desired_x, desired_y, self.desired_final_height_grasp), -90, -90, 0, 1000)
                    time.sleep(self.sleep_time)

                    Board.setBusServoPulse(self.servo_1_id, self.gripper_closed, self.gripper_closed)
                    time.sleep(self.sleep_time)

                    Board.setBusServoPulse(self.servo_2_id, self.gripper_closed, self.gripper_closed)
                    self.arm_kinematics.setPitchRangeMoving((desired_x, desired_y, self.desired_approach_height_grasp), -90, -90, 0, 1000)
                    time.sleep(2*self.sleep_time)

                    result = self.arm_kinematics.setPitchRangeMoving((self.colour_coordinates[current_color][0], self.colour_coordinates[current_color][1], 12), -90, -90, 0)   
                    time.sleep(result[2]/self.sleep_divider)
                                    
                    block_rotation = getAngle(self.colour_coordinates[current_color][0], self.colour_coordinates[current_color][1], -90)
                    Board.setBusServoPulse(self.servo_2_id, block_rotation, self.gripper_closed)
                    time.sleep(self.sleep_time)

                    self.arm_kinematics.setPitchRangeMoving((self.colour_coordinates[current_color][0], self.colour_coordinates[current_color][1], self.colour_coordinates[current_color][2] + 3), -90, -90, 0, 500)
                    time.sleep(self.sleep_time)
                                        
                    self.arm_kinematics.setPitchRangeMoving((self.colour_coordinates[current_color]), -90, -90, 0, 1000)
                    time.sleep(self.sleep_time)

                    Board.setBusServoPulse(1, self.gripper_closed - self.gripper_open, self.gripper_closed)
                    time.sleep(self.sleep_time)

                    self.arm_kinematics.setPitchRangeMoving((self.colour_coordinates[current_color][0], self.colour_coordinates[current_color][1], 12), -90, -90, 0, 800)
                    time.sleep(self.sleep_time)

                    self.move_home()

                    current_color = 'None'
                    time.sleep(3*self.sleep_time)

if __name__ == "__main__":
    detector = ColorDetector()
    my_camera = Camera.Camera()
    my_camera.camera_open()
    move_handler = MoveHandler(detector)

    
    move_thread = threading.Thread(target=move_handler.move)
    move_thread.daemon = True
    move_thread.start()
    
    while True:
        img = my_camera.frame
        if img is not None:
            frame = img.copy()
            img_processed = detector.preprocess_image(frame)
            box, detected_color_temp = detector.find_box_space(img_processed)
            annotated_img = detector.annotate_box(box, detected_color_temp)
            
            cv2.imshow('annotated image', annotated_img)
            
            if detected_color_temp:
                # print("object detected")
                move_handler.detect_color = detected_color_temp
                move_handler.world_X, move_handler.world_Y = detector.world_x, detector.world_y
                move_handler.track = detector.track
                
                if move_handler.first_move:
                    move_handler.start_pick_up = True
            
            key = cv2.waitKey(1)
            if key == 27:
                break
    
    my_camera.camera_close()
    cv2.destroyAllWindows()
