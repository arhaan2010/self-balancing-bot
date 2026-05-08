"""
Pixhawk Interface Module
Handles communication with Pixhawk flight controller via MAVLink
"""

import logging
import time
from pymavlink import mavutil
from utils import setup_logging, load_config, clamp


class PixhawkInterface:
    """Interface for communicating with Pixhawk flight controller"""
    
    def __init__(self, config_file='config/pixhawk_config.yaml'):
        """
        Initialize Pixhawk interface
        
        Args:
            config_file: Path to Pixhawk configuration file
        """
        self.logger = setup_logging(log_level=logging.INFO)
        self.config = load_config(config_file)
        self.connection = None
        self.connected = False
        
        # IMU data storage
        self.attitude = {
            'roll': 0.0,      # degrees
            'pitch': 0.0,     # degrees
            'yaw': 0.0,       # degrees
        }
        
        self.angular_velocity = {
            'rollspeed': 0.0,  # rad/s
            'pitchspeed': 0.0, # rad/s
            'yawspeed': 0.0,   # rad/s
        }
        
        self.acceleration = {
            'x': 0.0,  # m/s²
            'y': 0.0,  # m/s²
            'z': 0.0,  # m/s²
        }
        
        self.last_heartbeat = time.time()
    
    def connect(self):
        """
        Connect to Pixhawk
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            connection_config = self.config['connection']
            connection_type = connection_config['type']
            
            if connection_type == 'serial':
                serial_config = connection_config['serial']
                port = serial_config['port']
                baudrate = serial_config['baudrate']
                connection_string = f"{port}:{baudrate}"
                
            elif connection_type == 'udp':
                udp_config = connection_config['udp']
                address = udp_config['address']
                port = udp_config['port']
                connection_string = f"udpin:{address}:{port}"
                
            elif connection_type == 'tcp':
                tcp_config = connection_config['tcp']
                address = tcp_config['address']
                port = tcp_config['port']
                connection_string = f"tcp:{address}:{port}"
            else:
                raise ValueError(f"Unknown connection type: {connection_type}")
            
            self.logger.info(f"Connecting to Pixhawk: {connection_string}")
            self.connection = mavutil.mavlink_connection(connection_string)
            
            # Wait for heartbeat
            timeout = self.config['timeout']['heartbeat']
            self.connection.wait_heartbeat(timeout=timeout)
            
            self.connected = True
            self.logger.info("Successfully connected to Pixhawk")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Pixhawk: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Pixhawk"""
        if self.connection:
            self.connection.close()
            self.connected = False
            self.logger.info("Disconnected from Pixhawk")
    
    def read_imu_data(self):
        """
        Read IMU data from Pixhawk
        
        Returns:
            dict: Dictionary with attitude, angular velocity, and acceleration
        """
        if not self.connected:
            return None
        
        try:
            timeout = self.config['timeout']['data_read']
            
            # Read attitude message
            msg = self.connection.recv_match(type='ATTITUDE', timeout=timeout)
            if msg:
                # Convert radians to degrees
                self.attitude['roll'] = msg.roll * 180.0 / 3.14159
                self.attitude['pitch'] = msg.pitch * 180.0 / 3.14159
                self.attitude['yaw'] = msg.yaw * 180.0 / 3.14159
                
                self.angular_velocity['rollspeed'] = msg.rollspeed
                self.angular_velocity['pitchspeed'] = msg.pitchspeed
                self.angular_velocity['yawspeed'] = msg.yawspeed
                
                self.last_heartbeat = time.time()
            
            # Read acceleration data
            msg = self.connection.recv_match(type='SCALED_IMU', timeout=timeout)
            if msg:
                # Convert to m/s² (accel_x is in milli-g)
                self.acceleration['x'] = msg.xacc / 1000.0 * 9.81
                self.acceleration['y'] = msg.yacc / 1000.0 * 9.81
                self.acceleration['z'] = msg.zacc / 1000.0 * 9.81
            
            return {
                'attitude': self.attitude.copy(),
                'angular_velocity': self.angular_velocity.copy(),
                'acceleration': self.acceleration.copy()
            }
            
        except Exception as e:
            self.logger.warning(f"Error reading IMU data: {e}")
            return None
    
    def get_attitude(self):
        """
        Get current attitude (roll, pitch, yaw)
        
        Returns:
            dict: Dictionary with roll, pitch, yaw in degrees
        """
        return self.attitude.copy()
    
    def get_angular_velocity(self):
        """
        Get current angular velocity
        
        Returns:
            dict: Dictionary with rollspeed, pitchspeed, yawspeed in rad/s
        """
        return self.angular_velocity.copy()
    
    def get_acceleration(self):
        """
        Get current acceleration
        
        Returns:
            dict: Dictionary with x, y, z acceleration in m/s²
        """
        return self.acceleration.copy()
    
    def is_connected(self):
        """
        Check if still connected to Pixhawk
        
        Returns:
            bool: True if connected and receiving data
        """
        if not self.connected:
            return False
        
        # Check for timeout
        timeout = self.config['safety']['failsafe_timeout']
        if time.time() - self.last_heartbeat > timeout:
            self.logger.warning("Pixhawk connection timeout!")
            return False
        
        return True
    
    def wait_for_data(self, timeout=5.0):
        """
        Wait for initial data from Pixhawk
        
        Args:
            timeout: Maximum time to wait in seconds
        
        Returns:
            bool: True if data received, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.read_imu_data():
                return True
            time.sleep(0.1)
        
        self.logger.error("Timeout waiting for Pixhawk data")
        return False
    
    def set_mode(self, mode_name):
        """
        Set flight mode on Pixhawk
        
        Args:
            mode_name: Name of mode (e.g., 'MANUAL', 'STABILIZE')
        
        Returns:
            bool: True if successful
        """
        try:
            if not self.connection:
                return False
            
            # Get mode ID from mode name
            mode_id = self.connection.mode_mapping()[mode_name]
            self.connection.set_mode(mode_id)
            self.logger.info(f"Set mode to {mode_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set mode: {e}")
            return False
    
    def arm(self):
        """
        Arm the Pixhawk (enable motors)
        
        Returns:
            bool: True if successful
        """
        try:
            if not self.connection:
                return False
            
            self.connection.mav.command_long_send(
                self.connection.target_system,
                self.connection.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,      # confirmation
                1, 0, 0, 0, 0, 0, 0  # arm
            )
            
            self.logger.info("Sent arm command")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to arm: {e}")
            return False
    
    def disarm(self):
        """
        Disarm the Pixhawk (disable motors)
        
        Returns:
            bool: True if successful
        """
        try:
            if not self.connection:
                return False
            
            self.connection.mav.command_long_send(
                self.connection.target_system,
                self.connection.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0,      # confirmation
                0, 0, 0, 0, 0, 0, 0  # disarm
            )
            
            self.logger.info("Sent disarm command")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to disarm: {e}")
            return False


if __name__ == "__main__":
    # Test Pixhawk interface
    pixhawk = PixhawkInterface()
    
    if pixhawk.connect():
        print("Connected to Pixhawk!")
        
        # Read some IMU data
        for i in range(10):
            data = pixhawk.read_imu_data()
            if data:
                print(f"Pitch: {data['attitude']['pitch']:.2f}°, Roll: {data['attitude']['roll']:.2f}°")
            time.sleep(0.1)
        
        pixhawk.disconnect()
    else:
        print("Failed to connect to Pixhawk")
