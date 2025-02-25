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
    def __init__(self, arm_ik, detector):
        self.AK = arm_ik
        self.detector = detector
        self.servo1 = 500
        self.__isRunning = True
        self._stop = False
        self.first_move = True
        self.start_pick_up = False
        self.unreachable = False
        self.action_finish = False
        self.detect_color = None
        self.world_X = 0
        self.world_Y = 0
        self.track = False
        
        self.coordinate = {
            'red': (-14.5, 11.5, 1.5),
            'green': (-14.5, 5.5, 1.5),
            'blue': (-14.5, -0.5, 1.5),
        }

    def move(self):
        while True:
            if self.__isRunning:
                if self.first_move and self.start_pick_up:
                    self.action_finish = False
                    setBuzzer(0.1)
                    result = self.AK.setPitchRangeMoving((self.world_X, self.world_Y - 2, 5), -90, -90, 0)
                    if not result:
                        self.unreachable = True
                    else:
                        self.unreachable = False
                    time.sleep(result[2] / 1000)
                    self.start_pick_up = False
                    self.first_move = False
                    self.action_finish = True
                elif not self.first_move and not self.unreachable:
                    if self.track:
                        if not self.__isRunning:
                            continue
                        self.AK.setPitchRangeMoving((self.world_X, self.world_Y - 2, 5), -90, -90, 0, 20)
                        time.sleep(0.02)
                        self.track = False
                    if self.start_pick_up:
                        self.action_finish = False
                        if not self.__isRunning:
                            continue
                        Board.setBusServoPulse(1, self.servo1 - 280, 500)
                        servo2_angle = getAngle(self.world_X, self.world_Y, -90)
                        Board.setBusServoPulse(2, servo2_angle, 500)
                        time.sleep(0.8)
                        
                        if not self.__isRunning:
                            continue
                        self.AK.setPitchRangeMoving((self.world_X, self.world_Y, 2), -90, -90, 0, 1000)
                        time.sleep(2)
                        
                        if not self.__isRunning:
                            continue
                        Board.setBusServoPulse(1, self.servo1, 500)
                        time.sleep(1)
                        
                        if not self.__isRunning:
                            continue
                        Board.setBusServoPulse(2, 500, 500)
                        self.AK.setPitchRangeMoving((self.world_X, self.world_Y, 12), -90, -90, 0, 1000)
                        time.sleep(1)
                        
                        if not self.__isRunning:
                            continue
                        result = self.AK.setPitchRangeMoving(self.coordinate[self.detect_color], -90, -90, 0)
                        time.sleep(result[2] / 1000)
                        
                        if not self.__isRunning:
                            continue
                        servo2_angle = getAngle(self.coordinate[self.detect_color][0], self.coordinate[self.detect_color][1], -90)
                        Board.setBusServoPulse(2, servo2_angle, 500)
                        time.sleep(0.5)
                        
                        if not self.__isRunning:
                            continue
                        self.AK.setPitchRangeMoving((self.coordinate[self.detect_color][0], self.coordinate[self.detect_color][1], self.coordinate[self.detect_color][2] + 3), -90, -90, 0, 500)
                        time.sleep(0.5)
                        
                        if not self.__isRunning:
                            continue
                        self.AK.setPitchRangeMoving(self.coordinate[self.detect_color], -90, -90, 0, 1000)
                        time.sleep(0.8)
                        
                        if not self.__isRunning:
                            continue
                        Board.setBusServoPulse(1, self.servo1 - 200, 500)
                        time.sleep(0.8)
                        
                        if not self.__isRunning:
                            continue
                        self.AK.setPitchRangeMoving((self.coordinate[self.detect_color][0], self.coordinate[self.detect_color][1], 12), -90, -90, 0, 800)
                        time.sleep(0.8)
                        
                        initMove()
                        time.sleep(1.5)
                        
                        self.detect_color = 'None'
                        self.first_move = True
                        self.action_finish = True
                        self.start_pick_up = False
                    else:
                        time.sleep(0.01)
            else:
                if self._stop:
                    self._stop = False
                    initMove()
                    time.sleep(1.5)
                time.sleep(0.01)

if __name__ == "__main__":
    detector = ColorDetector()
    my_camera = Camera.Camera()
    my_camera.camera_open()
    move_handler = MoveHandler(AK, detector)
    
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
                print("object detected")
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
