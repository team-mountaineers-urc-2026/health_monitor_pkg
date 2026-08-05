# health_monitor_pkg
A package that enables health status pipelining

## Nodes
- [arm_monitor](#arm-monitor)
- [autonomy_monitor](#autonomy-monitor)
- [chassis_monitor](#chassis-monitor)
- [communications_monitor](#communication-monitor)
- [computer_monitor](#computer-monitor)

## Arm Monitor

⚠️⚠️⚠️ Work In Progress ⚠️⚠️⚠️

This node acts as a motor protection node for the arm motors.

### Parameters
| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `timeout_period` | Double | 1.0 | If a joy message is not recieved in this period, the motors will be sent zero velocity values |
| `rail_id` | Integer | 0 | The CAN Arbitration ID for the Rail Motor |
| `shoulder_id` | Integer | 0 | The CAN Arbitration ID for the Shoulder Motor |
| `elbow_id` | Integer | 0 | The CAN Arbitration ID for the Elbow Motor |
| `wrist_roll_id` | Integer | 0 | The CAN Arbitration ID for the Wrist Roll Motor |
| `wrist_pitch_id` | Integer | 0 | The CAN Arbitration ID for the Wrist Pitch Motor |

### Subscriptions
| Topic | Type | Description |
| --- | --- | --- |
| `/manipulator/joy` | Joy | The arm controller inputs |

### Publishers
| Topic | Type | Description |
| --- | --- | --- |
| `/can_interface/send` | CanMessage | The ROS2 interface for CAN messages to be sent |

## Autonomy Monitor

⚠️⚠️⚠️ Work In Progress ⚠️⚠️⚠️

### Parameters
- `None as of yet`

## Chassis Monitor

⚠️⚠️⚠️ Work In Progress ⚠️⚠️⚠️

#### TODO: Add in subscriber to the pico for the split body angle

This Node republishes the Chassis Pitch and Roll as degrees, the split body angle, as well as incorporating code from the Motor Protection Node.

### Parameters
| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `timeout_period` | Double | 1.0 | If a cmd_vel is not recieved in this period, the motors will be sent zero velocity values |
| `front_left_id` | Integer | 0 | The CAN Arbitration ID for the Front Left Motor |
| `front_right_id` | Integer | 0 | The CAN Arbitration ID for the Front Right Motor |
| `back_left_id` | Integer | 0 | The CAN Arbitration ID for the Back Left Motor |
| `back_right_id` | Integer | 0 | The CAN Arbitration ID for the Back Right Motor |

### Subscriptions
| Topic | Type | Description |
| --- | --- | --- |
| `/cmd_vel` | Twist | The velocity the rover is commanded to go at in Linear X and Angular Z |
| `/mavros/imu/data` | Imu | The IMU data reported back from the Pixhawk |

### Publishers
| Topic | Type | Description |
| --- | --- | --- |
| `chassis_orientation` | Vector3 | The orientation the rover is in space in radians. x is roll, y is pitch, and z is yaw |
| `/can_interface/send` | CanMessage | The ROS2 interface for CAN messages to be sent |
| `split_body_angle` | Float32 | The split body angle of the chassis in radians |

## Communication Monitor

⚠️⚠️⚠️ Work In Progress ⚠️⚠️⚠️

#### TODO: Add in Radio Strength monitoring

This Node has a polling process that runs at a given polling period. Each poll it will get the ping delay, signal strength, and % of bandwidth used.

### Parameters
| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `poll_period` | Double | 1.0 | Used to set the period at which the node will poll for information in seconds. Do not set to less than 1 second |
| `ping_address`| String | "192.168.1.69" | Used to set the IP address which will be pinged |

### Subscriptions
`None`

### Publishers
| Topic | Type | Description |
| --- | --- | --- |
| `/ping_rtt` | Float32 | Publishes the RTT of a ping to the provided address. Timeout of 1 second |
| `/signal_strength` | Vector3 | Publishes the signal strength of the rover and base. x component is Base, y component is Rover |

## Computer Monitor

#### TODO: Test

This node has a polling process that runs at a given polling period. Each poll it will get cpu usage, memory usage, disk space usage, and network usage

### Parameters
| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `poll_period` | Double | 1.0 | Used to set the period at which the node will poll for information in seconds. Do not set to less than 1 second |
| `cpu_count` | Integer | 16 | The number of cpu cores on the computer |
| `network_interface` | String | "wlp5s0" | The interface being monitored |
| `partition` | String | "/dev/sda2" | The partition being monitored |

### Subscriptions
`None`

### Publishers
| Topic | Type | Description |
| --- | --- | --- |
| `/cpu_usage` | Float32 | Publishes the CPU usage in terms of a percentage [0-100] |
| `/memory_usage` | Float32 | Publishes the memory usage in terms of a percentage [0-100] |
| `/network_usage` | Vector3 | Publishes the TX and RX bitrate of the given network. x component is RX usage in Mbps, y component is TX usage in Mbps
| `/disk_usage` | Float32 | Publishes the usage of the given partition in terms of a percentage [0-100] |


## Comms Notes
### `wstalist` Output Reference

The following command connects to a Ubiquiti airOS device and returns a JSON array of connected wireless stations/clients.

```bash
sshpass -p PASSWORD ssh \
  -o "StrictHostKeyChecking no" \
  -o HostKeyAlgorithms=+ssh-rsa \
  ubnt@DEVICE_IP \
  "/usr/bin/wstalist"
```


### Example Output

```json
 [
     {
       "mac": "1C:6A:1B:D0:B5:14",
       "name": "",
       "lastip": "0.0.0.0",
       "associd": 1,
       "aprepeater": 0,
       "tx": 72.222,
       "rx": 72.222,
       "signal": -31,
       "rssi": 65,
       "chainrssi": [66, 53],
       "rx_chainmask": 3,
       "ccq": 100,
       "idle": 0,
       "tx_latency": 8,
       "uptime": 368,
       "ack": 28,
       "distance": 1050,
       "txpower": 28,
       "noisefloor": -92,
       "tx_ratedata":[0,0,0,0,0,0,0,4],
       "airmax": {
          "priority": 0,
          "quality": 0,
          "beam": -1,
          "signal": 0,
          "capacity": 0
        },
       "stats": {
          "rx_data": 5554,
          "rx_bytes": 6293920,
          "rx_pps": 148,
          "tx_data": 4969,
          "tx_bytes": 1442236,
          "tx_pps": 0
       },
       "rates": ["MCS0","MCS1","MCS2","MCS3","MCS4","MCS5","MCS6","MCS7"],
       "signals": [0,0,0,0,0,0,0,-34],
       "remote_age": 0,
       "remote_age_max": 21,
       "remote": {
          "version": "2WA.ar934x.v8.7.11.46972.220614.0419",
          "uptime": 411,
          "hostname": "Bullet AC IP67",
          "platform": "BulletAC-IP67",
          "signal": -23,
          "tx_power": 21,
          "rssi": 73,
          "chainrssi": [73, 73],
          "tx_latency": 1,
          "rx_chainmask": 1,
          "noisefloor": -89,
          "distance": 600,
          "tx_ratedata":[2,0,5,4,12,371,422,2109],
          "time": "2022-06-14 04:25:45",
          "cpuload": 5.9405,
          "totalram": 63447040,
          "freeram": 28639232,
          "netrole": "bridge",
          "tx_bytes": 6561704,
          "rx_bytes": 1400960,
          "ccq": 0,
          "ethlist": [
             {
                "ifname": "eth0",
                "enabled":true,
                "plugged":true,
                "duplex":true,
                "speed": 100,
                "snr":[30,30,30,30],
                "cable_len": 0
              }   
           ]
        } 
     } 
 ]
```

### Common Fields

| Field | Type | Description |
|---|---|---|
| `mac` | `string` | MAC address of the connected station |
| `ip` | `string` | Current IP address of the station |
| `lastip` | `string` | Most recently observed IP address |
| `name` | `string` | Device hostname or configured name |
| `associd` | `integer` | Wireless association ID |
| `signal` | `integer` | RSSI signal strength in dBm |
| `noise` | `integer` | Noise floor in dBm |
| `ccq` | `float` | Client Connection Quality (%) |
| `tx` | `integer` | TX PHY rate in bps |
| `rx` | `integer` | RX PHY rate in bps |
| `txpower` | `integer` | Radio transmit power in dBm |
| `distance` | `integer` | Estimated link distance |
| `ack` | `integer` | ACK timeout/distance value |
| `idle` | `integer` | Idle time in seconds |
| `uptime` | `integer` | Connection uptime in seconds |
| `rates` | `string` | Modulation/coding scheme (example: `MCS15`) |
| `aprepeater` | `integer` | Indicates repeater mode status |
| `signal_chain0` | `integer` | RSSI for antenna chain 0 |
| `signal_chain1` | `integer` | RSSI for antenna chain 1 |
| `signal_chain2` | `integer` | RSSI for antenna chain 2 (if available) |
| `signal_chain3` | `integer` | RSSI for antenna chain 3 (if available) |


### Signal Strength Reference

| Signal (dBm) | Quality |
|---|---|
| `-50` to `-60` | Excellent |
| `-61` to `-70` | Good |
| `-71` to `-80` | Fair |
| `< -80` | Poor |


### Connection Quality (CCQ)

| CCQ (%) | Interpretation |
|---|---|
| `95 - 100` | Excellent |
| `80 - 94` | Good |
| `60 - 79` | Fair |
| `< 60` | Poor |


## Empty Output

If no wireless clients are connected:

```json
[]
```

Some firmware versions may instead return:

```json
null
```

---

### Notes

- Output format may vary slightly by airOS firmware version.
- Additional fields may appear on newer devices.
- PHY rates (`tx`/`rx`) are reported in bits per second.
- `signal_chainX` values are useful for diagnosing antenna imbalance or alignment issues.
- Devices operating in station mode may return different structures than AP mode.
