# Arm Protection Node
# Gripper Pressure

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Joy
from rclpy.qos import qos_profile_sensor_data
from controls_msgs.msg import CanMessage
from robot_interfaces.msg import TargetedInt
from pyactuator import SpeedClosedLoopControlMsg, AbsolutePositionClosedLoopControlMsg, ReadMotorStatus1Msg

class ArmMonitor(Node):

    def __init__(self):
        super().__init__('arm_monitor')
        
        # Declare Parameters
        self.declare_parameter("timeout_period", 0.5) # "The period at which polling will occur (Do not set below 1.0)")
        self.declare_parameter("rail_id", 0)
        self.declare_parameter("shoulder_id", 0)
        self.declare_parameter("elbow_id", 0)
        self.declare_parameter("wrist_roll_id", 0)
        self.declare_parameter("wrist_pitch_id", 0)
        self.declare_parameter('can_network_id', 'can1')

        # Get Parameters
        self.timeout_period = self.get_parameter("timeout_period").get_parameter_value().double_value  # seconds
        self.rail_id        = self.get_parameter("rail_id").get_parameter_value().integer_value
        self.shoulder_id    = self.get_parameter("shoulder_id").get_parameter_value().integer_value
        self.elbow_id       = self.get_parameter("elbow_id").get_parameter_value().integer_value
        self.wrist_roll_id  = self.get_parameter("wrist_roll_id").get_parameter_value().integer_value
        self.wrist_pitch_id = self.get_parameter("wrist_pitch_id").get_parameter_value().integer_value
        self.can_network_id = self.get_parameter('can_network_id').get_parameter_value().string_value

        # CAN Message Pub
        self.can_msg_pub = self.create_publisher(CanMessage, f'/{self.can_network_id}_interface/send', 10)

        # CAN Message Listener
        self.drive_sub = self.create_subscription(CanMessage, f'/{self.can_network_id}_interface/rcvd', self.can_callback, qos_profile_sensor_data)

        # Motor Error Pub
        self.motor_error_pub = self.create_publisher(TargetedInt, '/health_monitor/motor_error', 10)

        # Timers
        self.timeout_timer = self.create_timer(self.timeout_period, self.timeout_callback)
        
        self.got_response = [False, False, False, False, False]

    # Callback for CAN Subscription
    def can_callback(self, can_msg):
        # Check to see which motor it was
        sender = can_msg.arbitration_id - 0x100
        type = can_msg.data[0]

        # If this wasn't a speed or position message ignore it
        if type == AbsolutePositionClosedLoopControlMsg._cmd_byte or type == SpeedClosedLoopControlMsg._cmd_byte:
            match sender:
                
                case self.rail_id:
                    self.got_response[0] = True

                case self.shoulder_id:
                    self.got_response[1] = True

                case self.elbow_id:
                    self.got_response[2] = True

                case self.wrist_roll_id:
                    self.got_response[3] = True

                case self.wrist_pitch_id:
                    self.got_response[4] = True
        
        # If this is a status1 message, check the error code
        if type == ReadMotorStatus1Msg._cmd_byte:
            error_code = can_msg.data[6] << 8 + can_msg.data[7]
            
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
            self.send_stop_message(self.rail_id)
            # self.get_logger().info(f'stopping rail')

        if not self.got_response[1]:
            self.send_stop_message(self.shoulder_id)
            # self.get_logger().info(f'stopping shoulder')

        if not self.got_response[2]:
            self.send_stop_message(self.elbow_id)
            # self.get_logger().info(f'stopping elbow')

        if not self.got_response[3]:
            self.send_stop_message(self.wrist_roll_id)
            # self.get_logger().info(f'stopping roll')

        if not self.got_response[4]:
            self.send_stop_message(self.wrist_pitch_id)
            # self.get_logger().info(f'stopping pitch')

        # Reset for next go around
        self.got_response = [False, False, False, False, False]

def main(args=None):
    rclpy.init(args=args)

    arm_monitor = ArmMonitor()

    rclpy.spin(arm_monitor)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    arm_monitor.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()