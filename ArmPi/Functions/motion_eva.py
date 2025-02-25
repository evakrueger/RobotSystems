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

class RoboticArm:
    def __init__(self):
        self._is_running = False
        self._stop = False
        self.unreachable = False
        self.detect_color = None
        self.action_finish = True
        self.rotation_angle = 0
        self.world_X, self.world_Y = 0, 0
        self.world_x, self.world_y = 0, 0
        self.start_pick_up = False
        self.first_move = True
        self.get_roi = False
        self.track = False
        self.coordinate = {
            'red': (-14.5, 11.5, 1.5),
            'green': (-14.5, 5.5, 1.5),
            'blue': (-14.5, -0.5, 1.5)
        }
        self.servo1 = 500 # The angle at which the gripper closes when clamping
    
    # initial position
    def initMove(self):
        Board.setBusServoPulse(1, servo1 - 50, 300)
        Board.setBusServoPulse(2, 500, 500)
        AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)
    
    def setBuzzer(self, timer):
        Board.setBuzzer(0)
        Board.setBuzzer(1)
        time.sleep(timer)
        Board.setBuzzer(0)
    
    def move_to_initial_position(self):
        """ Moves the arm to the initial position. """
        Board.setBusServoPulse(1, self.servo1 - 70, 300)
        time.sleep(0.5)
        Board.setBusServoPulse(2, 500, 500)
        AK.setPitchRangeMoving((0, 10, 10), -30, -30, -90, 1500)
        time.sleep(1.5)
    
    def move_to_detected_object(self):
        """ Moves to the detected object when first seen. """
        self.action_finish = False
        self.setBuzzer(0.1)
        result = AK.setPitchRangeMoving((self.world_X, self.world_Y - 2, 5), -90, -90, 0)
        self.unreachable = not result
        if result:
            time.sleep(result[2] / 1000)
        self.start_pick_up = False
        self.first_move = False
        self.action_finish = True
    
    def track_object(self):
        """ Adjusts the arm position while tracking an object. """
        if not self._is_running:
            return
        AK.setPitchRangeMoving((self.world_x, self.world_y - 2, 5), -90, -90, 0, 20)
        time.sleep(0.02)
        self.track = False
    
    def pick_up_object(self):
        """ Performs the gripping and lifting sequence. """
        self.action_finish = False
        Board.setBusServoPulse(1, self.servo1 - 280, 500)
        servo2_angle = getAngle(self.world_X, self.world_Y, self.rotation_angle)
        Board.setBusServoPulse(2, servo2_angle, 500)
        time.sleep(0.8)

        if not self._is_running:
            return
        AK.setPitchRangeMoving((self.world_X, self.world_Y, 2), -90, -90, 0, 1000)
        time.sleep(2)
        
        Board.setBusServoPulse(1, self.servo1, 500)
        time.sleep(1)
        
        Board.setBusServoPulse(2, 500, 500)
        AK.setPitchRangeMoving((self.world_X, self.world_Y, 12), -90, -90, 0, 1000)
        time.sleep(1)
    
    def place_object(self):
        """ Moves the object to its designated placement area. """
        target = self.coordinate.get(self.detect_color, (0, 0, 0))
        result = AK.setPitchRangeMoving((target[0], target[1], 12), -90, -90, 0)
        time.sleep(result[2] / 1000)

        servo2_angle = getAngle(target[0], target[1], -90)
        Board.setBusServoPulse(2, servo2_angle, 500)
        time.sleep(0.5)

        AK.setPitchRangeMoving((target[0], target[1], target[2] + 3), -90, -90, 0, 500)
        time.sleep(0.5)
        
        AK.setPitchRangeMoving(target, -90, -90, 0, 1000)
        time.sleep(0.8)

        Board.setBusServoPulse(1, self.servo1 - 200, 500)
        time.sleep(0.8)

        AK.setPitchRangeMoving((target[0], target[1], 12), -90, -90, 0, 800)
        time.sleep(0.8)
    
        self.reset_after_placement()
    
    def reset_after_placement(self):
        """ Resets variables and returns arm to the initial position. """
        self.initMove()
        time.sleep(1.5)
        self.detect_color = 'None'
        self.first_move = True
        self.get_roi = False
        self.action_finish = True
        self.start_pick_up = False
    
    def move(self):
        """ Main loop for controlling the robotic arm. """
        while True:
            if self._is_running:
                if self.first_move and self.start_pick_up:
                    self.move_to_detected_object()
                elif not self.first_move and not self.unreachable:
                    if self.track:
                        self.track_object()
                    if self.start_pick_up:
                        self.pick_up_object()
                        self.place_object()
                else:
                    time.sleep(0.01)
            else:
                if self._stop:
                    self._stop = False
                    self.move_to_initial_position()
                time.sleep(0.01)
