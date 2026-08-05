# Latte Panda CPU Usage
# Latte Panda Memory Usage
# Latte Panda Disk Usage
# Latte Panda Network Usage

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32
from geometry_msgs.msg import Vector3
from rclpy.qos import qos_profile_sensor_data
import subprocess
import re
import os
import json
import time


class ComputerMonitor(Node):

    def __init__(self):
        super().__init__('computer_monitor')
        
        # Declare Parameters
        self.declare_parameter("poll_period", 1.0) # "The period at which ping will occur (Do not set below 1.0)")
        self.declare_parameter("cpu_count", 16)
        self.declare_parameter("network_interface", "wlp5s0")
        self.declare_parameter("partition", "/dev/sda2")

        # Get Parameters
        self.poll_period = self.get_parameter("poll_period").get_parameter_value().double_value  # seconds
        self.cpu_count = self.get_parameter("cpu_count").get_parameter_value().integer_value
        self.network = self.get_parameter("network_interface").get_parameter_value().string_value
        self.partition = self.get_parameter("partition").get_parameter_value().string_value

        # Publisher for CPU usage
        self.cpu_usage_pub = self.create_publisher(Float32, 'cpu_usage', qos_profile_sensor_data)
        self.last_cpu_idle = -1

        # Publisher for Memory usage
        self.mem_usage_pub = self.create_publisher(Float32, 'memory_usage', qos_profile_sensor_data)

        # Publisher for Disk usage
        self.disk_usage_pub = self.create_publisher(Float32, 'disk_usage', qos_profile_sensor_data)

        # Publisher for Network Usage
        self.net_usage_pub = self.create_publisher(Vector3, 'network_usage', qos_profile_sensor_data)
        self.last_recieve_bytes = -1
        self.last_transmit_bytes = -1

        # Information Timer
        self.timer = self.create_timer(self.poll_period, self.poll_info)
        
        # Initialization
        self.poll_cpu()
        self.poll_network()

        # self.ping_command = f"ping -c 1 -w 1 {self.ping_address}"
        # self.command_arr = self.ping_command.split(" ")
        # self.rolling_list = []

    def poll_info(self):
        
        cpu_usage = self.poll_cpu()
        memory_usage = self.poll_mem()
        disk_usage = self.poll_disk()
        network_usage = self.poll_network()

        cpu_data = Float32(data=cpu_usage)
        mem_data = Float32(data=memory_usage)
        dis_data = Float32(data=disk_usage)
        net_data = Vector3(x=float(network_usage[0]), y=float(network_usage[1]))

#        self.get_logger().info(f"CPU: {cpu_usage:.2f}%\tMEMORY: {memory_usage:.2f}%\tDISK: {disk_usage:.2f}%\tTX: {network_usage[0]:.3f} Mbps\tRX: {network_usage[1]:.3f} Mbps ")

        self.cpu_usage_pub.publish(cpu_data)
        self.mem_usage_pub.publish(mem_data)
        self.disk_usage_pub.publish(dis_data)
        self.net_usage_pub.publish(net_data)

    def poll_cpu(self):
        cpu_command = "cat /proc/stat"
        command_arr = cpu_command.split(" ")

        cpu_res = subprocess.run(command_arr, capture_output=True, text=True)
        cpu_res_arr = cpu_res.stdout.split("/n")

        # Split into lines and grab the first one, then grab the idle time
        column_match = re.search(r'cpu  \d+ \d+ \d+ (\d+) \d+ \d+ \d+ \d+ \d+ \d+', cpu_res_arr[0])
        if column_match:
            
            curr_cpu_idle = float(column_match.group(1))

            if self.last_cpu_idle == -1:
                self.last_cpu_idle = curr_cpu_idle
                return 0
            else:
                delta = curr_cpu_idle - self.last_cpu_idle
                # Convert to a percentage of time
                delta = 100 - delta / (self.poll_period * self.cpu_count)
                self.last_cpu_idle = curr_cpu_idle
                return float(delta)
        else:
            return float(-1.0)

    def poll_mem(self):
        mem_command = "cat /proc/meminfo"
        command_arr = mem_command.split(" ")

        mem_res = subprocess.run(command_arr, capture_output=True, text=True)
        mem_res_arr = mem_res.stdout.split("\n")
        
        # Split into lines and grab the total and free memories
        try:
            total_match = re.search(r'(\d+) kB', mem_res_arr[0])
            avail_match = re.search(r'(\d+) kB', mem_res_arr[2])

            total_mem = float(total_match.group(1))
            avail_mem = float(avail_match.group(1))

            return float(100 * (1 - avail_mem/total_mem))

        except Exception as e:
            self.get_logger().error(e)
            return float(-1.0)

    def poll_disk(self):
        disk_command = "df"
        command_arr = disk_command.split(" ")

        disk_res = subprocess.run(command_arr, capture_output=True, text=True)
        disk_res_arr = disk_res.stdout.split("\n")

        # Go through each line in the output and find the one with the correct partition
        for line in disk_res_arr:
            partition_match = re.search(r'{} +\d+ +(\d+) +(\d+) +\d+%'.format(self.partition), line)
            
            if partition_match:
                used_disk = float(partition_match.group(1))
                avail_disk = float(partition_match.group(2))

                delta = 100 * used_disk / (used_disk + avail_disk)

                return float(delta)
            
        return float(-1)

    def poll_network(self):
        network_command = f"netstat -e -n -i"
        command_arr = network_command.split(" ")
        
        network_res = subprocess.run(command_arr, capture_output=True, text=True)
        network_res_arr = network_res.stdout.split("\n")

        begin_search = False

        rx_bytes = 0
        tx_bytes = 0

        # Look through the output lines to find the ones with RX packets and TX packets
        for line in network_res_arr:
            network_match = re.search(f'{self.network}:', line)
            rx_match = re.search(r'RX packets \d+  bytes (\d+)', line)
            tx_match = re.search(r'TX packets \d+  bytes (\d+)', line)

            # Are we looking at the right network yet?
            if network_match:
                begin_search = True

            # If it is the rx line
            if rx_match and begin_search:
                
                total_rx_bytes = float(rx_match.group(1))

                # if this is the first run through
                if self.last_recieve_bytes != -1:
                    delta = total_rx_bytes - self.last_recieve_bytes

                    # Convert to Mbps
                    delta = delta/(self.poll_period * (2**17)) # 17 because 2^3 is 8
                    rx_bytes = float(delta)

                self.last_recieve_bytes = total_rx_bytes

            elif tx_match and begin_search:

                total_tx_bytes = float(tx_match.group(1))

                # if this is the first run through
                if self.last_transmit_bytes != -1:
                    delta = total_tx_bytes - self.last_transmit_bytes

                    # Convert to Mbps
                    delta = delta/(self.poll_period * (2**17)) # 17 because 2^3 is 8
                    tx_bytes = float(delta)

                self.last_transmit_bytes = total_tx_bytes

                # If we have found the tx portion, we are done so we can break the loop early
                break

        return (rx_bytes, tx_bytes)

def main(args=None):
    rclpy.init(args=args)

    computer_monitor = ComputerMonitor()

    rclpy.spin(computer_monitor)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    computer_monitor.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
