
# Chassis Pitch
# Chassis Roll
# Split Body Angle
# Motor Protection Node

import rclpy
import math
from rclpy.node import Node

from std_msgs.msg import Float32, Int32MultiArray
from geometry_msgs.msg import Vector3, Twist
from rclpy.qos import qos_profile_sensor_data
from controls_msgs.msg import CanMessage
from sensor_msgs.msg import Imu
from robot_interfaces.msg import TargetedInt
from pyactuator import SpeedClosedLoopControlMsg, AbsolutePositionClosedLoopControlMsg, ReadMotorStatus1Msg

# For Signal Strength
import os
import subprocess
import json
import time

class ChassisMonitor(Node):

    def __init__(self):
        super().__init__('chassis_monitor')
        
        # Declare Parameters ==============================
        # Chassis Monitor
        self.declare_parameter("timeout_period", 0.5) # "The period at which timeout will occur
        self.declare_parameter("front_left_id", 0)
        self.declare_parameter("front_right_id", 0)
        self.declare_parameter("back_left_id", 0)
        self.declare_parameter("back_right_id", 0)
        self.declare_parameter('can_network_id', 'can0')


        # Get Parameters ========================
        # Chassis Monitor
        self.timeout_period = self.get_parameter("timeout_period").get_parameter_value().double_value  # seconds
        self.front_left_id  = self.get_parameter("front_left_id").get_parameter_value().integer_value
        self.front_right_id = self.get_parameter("front_right_id").get_parameter_value().integer_value
        self.back_left_id   = self.get_parameter("back_left_id").get_parameter_value().integer_value
        self.back_right_id  = self.get_parameter("back_right_id").get_parameter_value().integer_value
        self.can_network_id = self.get_parameter('can_network_id').get_parameter_value().string_value



        # ============================= #
        #      Chassis Monitor Setup    #
        # ============================= #

        # Subscribers: CAN Network, Chassis Orientation
        self.drive_sub = self.create_subscription(CanMessage, f'/{self.can_network_id}_interface/rcvd', self.can_callback, qos_profile_sensor_data)
        self.imu_sub = self.create_subscription(Imu, "/mavros/imu/data", self.imu_callback, qos_profile_sensor_data)
        
        # Publishers: Orientation , Split Body Angle, Motor Error, Can Messages
        self.orient_pub = self.create_publisher(Vector3, "chassis_orientation", qos_profile_sensor_data)
        self.split_angle_pub = self.create_publisher(Float32, "split_body_angle", qos_profile_sensor_data)
        self.motor_error_pub = self.create_publisher(TargetedInt, '/health_monitor/motor_error', 10)
        self.can_msg_pub = self.create_publisher(CanMessage, f'/{self.can_network_id}_interface/send', 10)

        # Timers
        self.timeout_timer = self.create_timer(self.timeout_period, self.timeout_callback)

        # Local Variables
        self.got_response = [False, False, False, False]








    # Callback for CAN Subscription
    def can_callback(self, can_msg):
        # Check to see which motor it was
        sender = can_msg.arbitration_id - 0x100
        type = can_msg.data[0]

        if type == AbsolutePositionClosedLoopControlMsg._cmd_byte or type == SpeedClosedLoopControlMsg._cmd_byte:
            match sender:
                
                case self.front_left_id:
                    self.got_response[0] = True

                case self.front_right_id:
                    self.got_response[1] = True

                case self.back_left_id:
                    self.got_response[2] = True

                case self.back_right_id:
                    self.got_response[3] = True
        
        # If this is a status1 message, check the error code
        if type == ReadMotorStatus1Msg._cmd_byte:
            error_code = can_msg.data[7] << 8 + can_msg.data[6]
            
            # If there is an error, yell about it
            if error_code != 0:
                self.motor_error_pub.publish(TargetedInt(target=sender, data=error_code))

    # Send a stop message to a given motor
    def send_stop_message(self, can_id):
        # Generate the CAN message
        stop_msg = CanMessage()
        can_msg = SpeedClosedLoopControlMsg.make_can_msg(can_id, int(0))
        stop_msg.arbitration_id = can_id
        stop_msg.data = can_msg.data
        self.can_msg_pub.publish(stop_msg)

    # Callback for timeout timer
    def timeout_callback(self):
        
        # If we have not recieved a joy message in timer period of seconds, stop it
        if not self.got_response[0]:
            self.send_stop_message(self.front_left_id)
            # self.get_logger().info(f'stopping front left')

        if not self.got_response[1]:
            self.send_stop_message(self.front_right_id)
            # self.get_logger().info(f'stopping front right')

        if not self.got_response[2]:
            self.send_stop_message(self.back_left_id)
            # self.get_logger().info(f'stopping back left')

        if not self.got_response[3]:
            self.send_stop_message(self.back_right_id)
            # self.get_logger().info(f'stopping back right')

        # Reset for next go around
        self.got_response = [False, False, False, False]

    # Callback for IMU
    def imu_callback(self, imu_msg : Imu):
        (roll_x, pitch_y, yaw_z) = euler_from_quaternion(imu_msg.orientation.x, imu_msg.orientation.y, imu_msg.orientation.z, imu_msg.orientation.w)

        orientation = Vector3()
        orientation.x = roll_x
        orientation.y = pitch_y
        orientation.z = yaw_z

        self.orient_pub.publish(orientation)


def euler_from_quaternion(x, y, z, w):
        """
        Convert a quaternion into euler angles (roll, pitch, yaw)
        roll is rotation around x in radians (counterclockwise)
        pitch is rotation around y in radians (counterclockwise)
        yaw is rotation around z in radians (counterclockwise)
        """
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        roll_x = math.atan2(t0, t1)
     
        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch_y = math.asin(t2)
     
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw_z = math.atan2(t3, t4)
     
        return roll_x, pitch_y, yaw_z # in radians

def main(args=None):
    rclpy.init(args=args)

    chassis_monitor = ChassisMonitor()

    rclpy.spin(chassis_monitor)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    chassis_monitor.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
