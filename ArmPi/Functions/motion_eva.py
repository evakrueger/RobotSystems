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
    def __init__(self, color_tracker):
        self.color_tracker = color_tracker
        self.track = False
        self._stop = False
        self.get_roi = False
        self.unreachable = False
        self.detect_color = 'None'
        self.action_finish = True
        self.rotation_angle = 0
        self.world_X = 0, self.world_Y = 0
        self.world_x = 0, self.world_y = 0
        self.center_list = [], self.count = 0
        self.start_pick_up = False, self.first_move = True

    # Robotic arm moving thread
    def move(self):
        # Quick placement coordinates (x, y, z) of different colors of wood
        coordinate = {
            'red':   (-15 + 0.5, 12 - 0.5, 1.5),
            'green': (-15 + 0.5, 6 - 0.5,  1.5),
            'blue':  (-15 + 0.5, 0 - 0.5,  1.5),
        }
        while True:
            if first_move and start_pick_up: # When an object is first detected               
                action_finish = False
                setBuzzer(0.1)               
                result = AK.setPitchRangeMoving((self.color_tracker.last_x, self.color_tracker.last_y - 2, 5), -90, -90, 0) # If the running time parameter is not filled in, the running time will be adaptive.
                if result == False:
                    unreachable = True
                else:
                    unreachable = False
                time.sleep(result[2]/1000) # The third item of the return parameter is time
                start_pick_up = False
                first_move = False
                action_finish = True
            elif not first_move and not unreachable: # This is not the first time an object is detected
                if track: # If it is the tracking stage # Stop and exit flag detectioe
                    AK.setPitchRangeMoving((self.color_tracker.last_x, self.color_tracker.last_y - 2, 5), -90, -90, 0, 20)
                    time.sleep(0.02)                    
                    track = False
                if start_pick_up: #If the object has not moved for a while, start gripping
                    action_finish = False # Stop and exit flag detectioe
                    Board.setBusServoPulse(1, servo1 - 280, 500)  # Claws spread
                    # Calculate the angle by which the gripper needs to be rotated
                    servo2_angle = getAngle(self.color_tracker.last_x, self.color_tracker.last_y, self.color_tracker.rotation_angle)
                    Board.setBusServoPulse(2, servo2_angle, 500)
                    time.sleep(0.8)
                    
                    AK.setPitchRangeMoving((self.color_tracker.last_x, self.color_tracker.last_y, 2), -90, -90, 0, 1000)  # lower height
                    time.sleep(2)
                    
                    Board.setBusServoPulse(1, servo1, 500)  # Gripper closed
                    time.sleep(1)
                    
                    Board.setBusServoPulse(2, 500, 500)
                    AK.setPitchRangeMoving((self.color_tracker.last_x, self.color_tracker.last_y, 12), -90, -90, 0, 1000)  # Robotic arm raised
                    time.sleep(1)
                    
                    # Classify and place blocks of different colors
                    result = AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0)   
                    time.sleep(result[2]/1000)
                    
                    servo2_angle = getAngle(coordinate[detect_color][0], coordinate[detect_color][1], -90)
                    Board.setBusServoPulse(2, servo2_angle, 500)
                    time.sleep(0.5)

                    AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], coordinate[detect_color][2] + 3), -90, -90, 0, 500)
                    time.sleep(0.5)
                    
                    AK.setPitchRangeMoving((coordinate[detect_color]), -90, -90, 0, 1000)
                    time.sleep(0.8)
                    
                    Board.setBusServoPulse(1, servo1 - 200, 500)  # Open your claws and drop the object
                    time.sleep(0.8)
                                        
                    AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0, 800)
                    time.sleep(0.8)

                    initMove()  # Return to initial position
                    time.sleep(1.5)

                    detect_color = 'None'
                    first_move = True
                    get_roi = False
                    action_finish = True
                    start_pick_up = False
                else:
                    time.sleep(0.01)
                    

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
