"""
IMU Reader Module
Reads and processes IMU data from Pixhawk
"""

import logging
import time
from pixhawk_interface import PixhawkInterface
from utils import setup_logging, load_config, RollingAverage


class IMUReader:
    """Reads and filters IMU data from Pixhawk"""
    
    def __init__(self, pixhawk_interface, config_file='config/pixhawk_config.yaml'):
        """
        Initialize IMU reader
        
        Args:
            pixhawk_interface: PixhawkInterface instance
            config_file: Path to Pixhawk configuration file
        """
        self.logger = setup_logging(log_level=logging.INFO)
        self.config = load_config(config_file)
        self.pixhawk = pixhawk_interface
        
        # Smoothing filters
        self.pitch_filter = RollingAverage(window_size=5)
        self.roll_filter = RollingAverage(window_size=5)
        self.yaw_filter = RollingAverage(window_size=5)
        
        # Calibration offsets
        calib_config = self.config['imu']['calibration']
        self.pitch_offset = calib_config['pitch_offset']
        self.roll_offset = calib_config['roll_offset']
        
        # Last valid readings
        self.last_attitude = {
            'pitch': 0.0,
            'roll': 0.0,
            'yaw': 0.0,
        }
        
        self.last_angular_velocity = {
            'rollspeed': 0.0,
            'pitchspeed': 0.0,
            'yawspeed': 0.0,
        }
        
        self.last_acceleration = {
            'x': 0.0,
            'y': 0.0,
            'z': 0.0,
        }
    
    def read_attitude(self):
        """
        Read and filter attitude data
        
        Returns:
            dict: Filtered attitude with pitch, roll, yaw (degrees)
        """
        if not self.pixhawk.is_connected():
            self.logger.warning("Pixhawk not connected")
            return self.last_attitude.copy()
        
        try:
            data = self.pixhawk.read_imu_data()
            if data:
                attitude = data['attitude']
                
                # Apply calibration offsets
                pitch = attitude['pitch'] - self.pitch_offset
                roll = attitude['roll'] - self.roll_offset
                yaw = attitude['yaw']
                
                # Apply smoothing filter
                self.pitch_filter.add(pitch)
                self.roll_filter.add(roll)
                self.yaw_filter.add(yaw)
                
                self.last_attitude = {
                    'pitch': self.pitch_filter.get_average(),
                    'roll': self.roll_filter.get_average(),
                    'yaw': self.yaw_filter.get_average(),
                }
                
                return self.last_attitude.copy()
        
        except Exception as e:
            self.logger.error(f"Error reading attitude: {e}")
        
        return self.last_attitude.copy()
    
    def read_angular_velocity(self):
        """
        Read angular velocity data
        
        Returns:
            dict: Angular velocity with rollspeed, pitchspeed, yawspeed (rad/s)
        """
        if not self.pixhawk.is_connected():
            return self.last_angular_velocity.copy()
        
        try:
            data = self.pixhawk.read_imu_data()
            if data:
                self.last_angular_velocity = data['angular_velocity'].copy()
                return self.last_angular_velocity.copy()
        
        except Exception as e:
            self.logger.error(f"Error reading angular velocity: {e}")
        
        return self.last_angular_velocity.copy()
    
    def read_acceleration(self):
        """
        Read acceleration data
        
        Returns:
            dict: Acceleration with x, y, z (m/s²)
        """
        if not self.pixhawk.is_connected():
            return self.last_acceleration.copy()
        
        try:
            data = self.pixhawk.read_imu_data()
            if data:
                self.last_acceleration = data['acceleration'].copy()
                return self.last_acceleration.copy()
        
        except Exception as e:
            self.logger.error(f"Error reading acceleration: {e}")
        
        return self.last_acceleration.copy()
    
    def read_all(self):
        """
        Read all IMU data (attitude, angular velocity, acceleration)
        
        Returns:
            dict: Dictionary with all IMU data
        """
        return {
            'attitude': self.read_attitude(),
            'angular_velocity': self.read_angular_velocity(),
            'acceleration': self.read_acceleration(),
        }
    
    def get_pitch(self):
        """Get current pitch angle (degrees)"""
        return self.last_attitude['pitch']
    
    def get_roll(self):
        """Get current roll angle (degrees)"""
        return self.last_attitude['roll']
    
    def get_yaw(self):
        """Get current yaw angle (degrees)"""
        return self.last_attitude['yaw']
    
    def calibrate_imu(self, duration=5):
        """
        Calibrate IMU offsets (keep robot stationary)
        
        Args:
            duration: Calibration duration in seconds
        
        Returns:
            bool: True if calibration successful
        """
        self.logger.info(f"Starting IMU calibration ({duration}s)...")
        self.logger.info("Keep the robot stationary!")
        
        pitch_sum = 0.0
        roll_sum = 0.0
        samples = 0
        
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.pixhawk.is_connected():
                data = self.pixhawk.read_imu_data()
                if data:
                    pitch_sum += data['attitude']['pitch']
                    roll_sum += data['attitude']['roll']
                    samples += 1
            
            time.sleep(0.05)
        
        if samples > 0:
            self.pitch_offset = pitch_sum / samples
            self.roll_offset = roll_sum / samples
            
            self.logger.info(f"Calibration complete!")
            self.logger.info(f"Pitch offset: {self.pitch_offset:.2f}°")
            self.logger.info(f"Roll offset: {self.roll_offset:.2f}°")
            
            # Reset filters
            self.pitch_filter.reset()
            self.roll_filter.reset()
            self.yaw_filter.reset()
            
            return True
        else:
            self.logger.error("Calibration failed - no data received")
            return False
    
    def wait_for_stable_reading(self, timeout=5, max_variance=0.5):
        """
        Wait for stable IMU readings
        
        Args:
            timeout: Maximum wait time in seconds
            max_variance: Maximum acceptable variance in degrees
        
        Returns:
            bool: True if stable reading obtained
        """
        self.logger.info("Waiting for stable IMU reading...")
        
        readings = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            attitude = self.read_attitude()
            readings.append(attitude['pitch'])
            
            if len(readings) > 10:
                readings.pop(0)
                
                # Calculate variance
                avg = sum(readings) / len(readings)
                variance = sum((x - avg) ** 2 for x in readings) / len(readings)
                
                if variance < max_variance:
                    self.logger.info("Stable reading obtained")
                    return True
            
            time.sleep(0.1)
        
        self.logger.warning("Timeout waiting for stable reading")
        return False


if __name__ == "__main__":
    # Test IMU reader
    pixhawk = PixhawkInterface()
    
    if pixhawk.connect():
        imu = IMUReader(pixhawk)
        
        # Wait for stable reading
        if imu.wait_for_stable_reading():
            # Read data
            for i in range(10):
                attitude = imu.read_attitude()
                print(f"Pitch: {attitude['pitch']:.2f}°, Roll: {attitude['roll']:.2f}°")
                time.sleep(0.1)
        
        pixhawk.disconnect()
