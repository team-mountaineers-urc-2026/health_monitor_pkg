# Chassis Pitch
# Chassis Roll
# Split Body Angle
# Motor Protection Node

import rclpy
import math
from rclpy.node import Node

from std_msgs.msg import Float32, Int64MultiArray
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

class CommsMonitor(Node):

    def __init__(self):
        super().__init__('comms_monitor')
        
        # Declare Parameters ==============================
        self.declare_parameter("comms_period", 1.0) 

        self.comms_period = self.get_parameter("comms_period").get_parameter_value().double_value  # 1 per second    


        self.comms_timer = self.create_timer(self.comms_period, self.comms_callback) # Adjust period.
        self.comms_info_pub = self.create_publisher(Int64MultiArray, '/health_monitor/communicatons_data', 10)


    def comms_callback(self):
        output_24 = None
        output_58 = None

        # Check 5.8 GHz Connection
        try:
            output_58 = subprocess.check_output(
                    'sshpass -p URC2026 ssh -o "StrictHostKeyChecking no" -o HostKeyAlgorithms=+ssh-rsa ubnt@192.168.1.34 "/usr/bin/wstalist"', stderr=subprocess.DEVNULL, shell=True)
            #self.get_logger().info((repr(output)))
        except Exception as E:
            print()
            # self.get_logger().error("5.8 GHz Not Detected")
            # self.get_logger().error(str(E))
        
        # Check 2.4 GHz Connection
        try:
            output_24 = subprocess.check_output(
                    'sshpass -p wvuurc ssh -o "StrictHostKeyChecking no" -o HostKeyAlgorithms=+ssh-rsa wvuurc@192.168.1.30 "/usr/bin/wstalist"',stderr=subprocess.DEVNULL, shell=True)

        except Exception as E:
            print()
            #self.get_logger().error("2.4 GHz Not Detected")
            
            
        
        # No Data Available
        if not output_24 and not output_58:
            return
            
        # Data in 5.8 GHz device
        elif not output_24:
            # Decode JSON 
            decode_output_58 = output_58.decode('ASCII')
            data_58 = json.loads(decode_output_58)

            try:
                # Create 5.8 GHz Comms Info Message               
                comms_data = Int64MultiArray()

                # comms_data [ Frequency, Base Station Signal, CCQ, Rover Signal, Base RX, Base TX, Rover RX, Rover TX]
                comms_data.data = [58, data_58[0]['signal'], data_58[0]['ccq'], data_58[0]['remote']['signal'], data_58[0]['rx_bytes'], data_58[0]['tx_bytes'], data_58[0]['uptime'], data_58[0]['distance']]
                comms_data.data[4] = int(comms_data.data[4] / comms_data.data[6])
                comms_data.data[5] = int(comms_data.data[5] / comms_data.data[6])
                self.comms_info_pub.publish(comms_data)


                #self.get_logger().info(f"5.8GHz -- > BaseRX: {data_58[0]['signal']}, RoverRX: {data_58[0]['remote']['signal']}")

            except:
                self.get_logger().info("")

		# self.get_logger().error("Failed to Print Signal Strengths")
        
        # Data in 2.4 GHz Device
        elif not output_58:
            # Decode JSON
            decode_output_24 = output_24.decode('ASCII')
            data_24 = json.loads(decode_output_24)

            try:
                # Create 2.4 GHz Comms Info Message               
                comms_data = Int64MultiArray()

                # comms_data [ Frequency, Base Station Signal, CCQ, Rover Signal, Base RX, Base TX, Rover RX, Rover TX]
                comms_data.data = [24, data_24[0]['signal'], data_24[0]['ccq'], data_24[0]['remote']['signal'], data_24[0]['rx_bytes'], data_24[0]['tx_bytes'], data_24[0]['uptime'], data_24[0]['distance']]
                comms_data.data[4] = int(comms_data.data[4] / comms_data.data[6])
                comms_data.data[5] = int(comms_data.data[5] / comms_data.data[6])
                self.comms_info_pub.publish(comms_data)

                # self.get_logger().info(f"2.4GHz -- > BaseRX: {data_24[0]['signal']}, RoverRX: {data_24[0]['remote']['signal']}")
            except:
                self.get_logger().info("")

        # Data in 2.4 GHz & 5.8 GHz Device
        else:
            # Decode both JSON
            decode_output_24 = output_24.decode('ASCII')
            decode_output_58 = output_58.decode('ASCII')

            data_24 = json.loads(decode_output_24)
            data_58 = json.loads(decode_output_58)

            try:
                # Create 2.4 GHz Comms Info Message               
                comms_data_24 = Int64MultiArray()
                comms_data_24.data = [24, data_24[0]['signal'], data_24[0]['ccq'], data_24[0]['remote']['signal'], data_24[0]['stats']['rx_bytes'], data_24[0]['stats']['tx_bytes'], data_24[0]['uptime'], data_24[0]['distance']]
                comms_data_24.data[4] = int(comms_data_24.data[4] / comms_data_24.data[6])
                comms_data_24.data[5] = int(comms_data_24.data[5] / comms_data_24.data[6])
                
                # Create 5.8 GHz Comms Info Message               
                comms_data_58 = Int64MultiArray()
                comms_data_58.data = [58, data_58[0]['signal'], data_58[0]['ccq'], data_58[0]['remote']['signal'], data_58[0]['stats']['rx_bytes'], data_58[0]['stats']['tx_bytes'], data_58[0]['uptime'],data_58[0]['distance']]
                comms_data_58.data[4] = int(comms_data_58.data[4] / comms_data_58.data[6])
                comms_data_58.data[5] = int(comms_data_58.data[5] / comms_data_58.data[6])
                # Publish Comms data
                self.comms_info_pub.publish(comms_data_24)
                self.comms_info_pub.publish(comms_data_58)



                # self.get_logger().info(f"2.4GHz -- > BaseRX: {data_24[0]['signal']}, RoverRX: {data_24[0]['remote']['signal']}")
                # self.get_logger().info(f"5.8GHz -- > BaseRX: {data_58[0]['signal']}, RoverRX: {data_58[0]['remote']['signal']}")
            except Exception as e:
                self.get_logger().error("")
                self.get_logger().error(str(E))
 
        return

        

def main(args=None):
    rclpy.init(args=args)

    comms_monitor = CommsMonitor()

    rclpy.spin(comms_monitor)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    comms_monitor.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

