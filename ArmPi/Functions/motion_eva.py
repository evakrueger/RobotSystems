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
    def __init__(self, AK, servo1):
        print("mover INIT")
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

    def pick_up_object(self):
        print("mover PICK UP OBJECT")
        self.action_finish = False
        Board.setBusServoPulse(1, self.servo1 - 280, 500)
        servo2_angle = getAngle(self.world_X, self.world_Y, -90)
        Board.setBusServoPulse(2, servo2_angle, 500)
        time.sleep(0.8)
        self.lower_arm()
        Board.setBusServoPulse(1, self.servo1, 500)
        time.sleep(1)
        self.lift_arm()
        self.move_to_target()
        self.release_object()
        self.reset_position()

    def lower_arm(self):
        print("mover LOWER ARM")
        self.AK.setPitchRangeMoving((self.world_X, self.world_Y, 2), -90, -90, 0, 1000)
        time.sleep(2)

    def lift_arm(self):
        print("mover LIFT ARM")
        Board.setBusServoPulse(2, 500, 500)
        self.AK.setPitchRangeMoving((self.world_X, self.world_Y, 12), -90, -90, 0, 1000)
        time.sleep(1)

    def move_to_target(self):
        print("mover MOVE TO TARGET")
        result = self.AK.setPitchRangeMoving(self.coordinate[self.detect_color], -90, -90, 0)
        time.sleep(result[2] / 1000)
        servo2_angle = getAngle(self.coordinate[self.detect_color][0], self.coordinate[self.detect_color][1], -90)
        Board.setBusServoPulse(2, servo2_angle, 500)
        time.sleep(0.5)
        self.AK.setPitchRangeMoving((self.coordinate[self.detect_color][0], self.coordinate[self.detect_color][1], self.coordinate[self.detect_color][2] + 3), -90, -90, 0, 500)
        time.sleep(0.5)
        self.AK.setPitchRangeMoving(self.coordinate[self.detect_color], -90, -90, 0, 1000)
        time.sleep(0.8)

    def release_object(self):
        print("mover RELEASE OBJECT")
        Board.setBusServoPulse(1, self.servo1 - 200, 500)
        time.sleep(0.8)
        self.AK.setPitchRangeMoving((self.coordinate[self.detect_color][0], self.coordinate[self.detect_color][1], 12), -90, -90, 0, 800)
        time.sleep(0.8)

    def reset_position(self):
        print("mover RESET POSITION")
        initMove()
        time.sleep(1.5)
        self.detect_color = 'None'
        self.first_move = True
        self.action_finish = True
        self.start_pick_up = False

    def move(self):
        print("mover MOVE")
        while True:
            if self.first_move and self.start_pick_up:
                self.action_finish = False
                setBuzzer(0.1)
                result = self.AK.setPitchRangeMoving((self.world_X, self.world_Y - 2, 5), -90, -90, 0)
                self.unreachable = not result
                time.sleep(result[2] / 1000 if result else 0)
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
                    self.pick_up_object()
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
