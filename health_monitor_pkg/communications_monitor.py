# RUN BASE STATION SIDE

# Signal Strength
# Bandwidth % used
# Ping Latency

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32
from geometry_msgs.msg import Vector3
from rclpy.qos import qos_profile_sensor_data
import subprocess
import re


class CommunicationsMonitor(Node):

    def __init__(self):
        super().__init__('communications_monitor')
        
        # Declare Parameters
        self.declare_parameter("ping_address", "192.168.1.69") # "The IP address the node will try and ping")
        self.declare_parameter("poll_period", 1.0) # "The period at which polling will occur (Do not set below 1.0)")

        # Get Parameters
        self.ping_address = self.get_parameter("ping_address").get_parameter_value().string_value
        self.poll_period = self.get_parameter("poll_period").get_parameter_value().double_value  # seconds
        
        # Publisher for signal strength
        self.signal_strength_pub = self.create_publisher(Vector3, 'signal_strength', qos_profile_sensor_data)

        # Publisher for bandwidth Percentage

        # Publisher for Ping RTT
        self.ping_rtt_pub = self.create_publisher(Float32, 'ping_rtt', qos_profile_sensor_data)
        self.timer = self.create_timer(self.poll_period, self.do_ping)
        
        self.ping_command = f"ping -c 1 -w 1 {self.ping_address}"
        self.command_arr = self.ping_command.split(" ")
        self.rolling_list = []

    def do_ping(self):
        
        # Run the command
        ping_res = subprocess.run(self.command_arr, capture_output=True, text=True)
        rtt_match = re.search(r'time=(\d+\.?\d*) ms', ping_res.stdout)
        
        # Capture the output
        msg = Float32()

        if rtt_match:
            rtt_value = float(rtt_match.group(1))

            # Parse the rolling list down to 10
            while len(self.rolling_list) >= 10:
                self.rolling_list = self.rolling_list[1:]
            
            # Add in the next value
            self.rolling_list.append(rtt_value)

            length = len(self.rolling_list)
            mean = sum(self.rolling_list)/length

            print(f"RTT: {rtt_value}\t\t10 Second Avg: {mean:.2f}\t\tElements: {length}/10")
            msg.data = rtt_value
        else:
            
            # Clear the rolling average because it is meaningless now
            self.rolling_list = []
            
            print("Timeout")
            msg.data = -1.0

        # Publish the outcome
        self.ping_rtt_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)

    communications_monitor = CommunicationsMonitor()

    rclpy.spin(communications_monitor)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    communications_monitor.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()