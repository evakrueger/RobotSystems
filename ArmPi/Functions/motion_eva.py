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

    # Robotic arm moving thread
    def move(self):
        global rect
        global track
        global _stop
        global get_roi
        global unreachable
        global __isRunning
        global detect_color
        global action_finish
        global rotation_angle
        global world_X, world_Y
        global world_x, world_y
        global center_list, count
        global start_pick_up, first_move

        # Quick placement coordinates (x, y, z) of different colors of wood
        coordinate = {
            'red':   (-15 + 0.5, 12 - 0.5, 1.5),
            'green': (-15 + 0.5, 6 - 0.5,  1.5),
            'blue':  (-15 + 0.5, 0 - 0.5,  1.5),
        }
        while True:
            if __isRunning:
                if first_move and start_pick_up: # When an object is first detected               
                    action_finish = False
                    #set_rgb(detect_color)
                    setBuzzer(0.1)               
                    result = AK.setPitchRangeMoving((world_X, world_Y - 2, 5), -90, -90, 0) # If the running time parameter is not filled in, the running time will be adaptive.
                    if result == False:
                        unreachable = True
                    else:
                        unreachable = False
                    time.sleep(result[2]/1000) # The third item of the return parameter is time
                    start_pick_up = False
                    first_move = False
                    action_finish = True
                elif not first_move and not unreachable: # This is not the first time an object is detected
                    #set_rgb(detect_color)
                    if track: # If it is the tracking stage
                        if not __isRunning: # Stop and exit flag detection
                            continue
                        AK.setPitchRangeMoving((world_x, world_y - 2, 5), -90, -90, 0, 20)
                        time.sleep(0.02)                    
                        track = False
                    if start_pick_up: #If the object has not moved for a while, start gripping
                        action_finish = False
                        if not __isRunning: # Stop and exit flag detection
                            continue
                        Board.setBusServoPulse(1, servo1 - 280, 500)  # Claws spread
                        # Calculate the angle by which the gripper needs to be rotated
                        servo2_angle = getAngle(world_X, world_Y, rotation_angle)
                        Board.setBusServoPulse(2, servo2_angle, 500)
                        time.sleep(0.8)
                        
                        if not __isRunning:
                            continue
                        AK.setPitchRangeMoving((world_X, world_Y, 2), -90, -90, 0, 1000)  # lower height
                        time.sleep(2)
                        
                        if not __isRunning:
                            continue
                        Board.setBusServoPulse(1, servo1, 500)  # Gripper closed
                        time.sleep(1)
                        
                        if not __isRunning:
                            continue
                        Board.setBusServoPulse(2, 500, 500)
                        AK.setPitchRangeMoving((world_X, world_Y, 12), -90, -90, 0, 1000)  # Robotic arm raised
                        time.sleep(1)
                        
                        if not __isRunning:
                            continue
                        # Classify and place blocks of different colors
                        result = AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0)   
                        time.sleep(result[2]/1000)
                        
                        if not __isRunning:
                            continue
                        servo2_angle = getAngle(coordinate[detect_color][0], coordinate[detect_color][1], -90)
                        Board.setBusServoPulse(2, servo2_angle, 500)
                        time.sleep(0.5)

                        if not __isRunning:
                            continue
                        AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], coordinate[detect_color][2] + 3), -90, -90, 0, 500)
                        time.sleep(0.5)
                        
                        if not __isRunning:
                            continue
                        AK.setPitchRangeMoving((coordinate[detect_color]), -90, -90, 0, 1000)
                        time.sleep(0.8)
                        
                        if not __isRunning:
                            continue
                        Board.setBusServoPulse(1, servo1 - 200, 500)  # Open your claws and drop the object
                        time.sleep(0.8)
                        
                        if not __isRunning:
                            continue                    
                        AK.setPitchRangeMoving((coordinate[detect_color][0], coordinate[detect_color][1], 12), -90, -90, 0, 800)
                        time.sleep(0.8)

                        initMove()  # Return to initial position
                        time.sleep(1.5)

                        detect_color = 'None'
                        first_move = True
                        get_roi = False
                        action_finish = True
                        start_pick_up = False
                        #set_rgb(detect_color)
                    else:
                        time.sleep(0.01)
            else:
                if _stop:
                    _stop = False
                    Board.setBusServoPulse(1, servo1 - 70, 300)
                    time.sleep(0.5)
                    Board.setBusServoPulse(2, 500, 500)
                    AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)
                    time.sleep(1.5)
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
