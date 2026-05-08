"""
ESC Control Module
Handles PWM control for brushless ESCs
"""

import logging
import time
import pigpio
from utils import setup_logging, load_config, clamp, map_range


class ESCController:
    """Controller for brushless ESCs via GPIO PWM"""
    
    def __init__(self, config_file='config/esc_config.yaml'):
        """
        Initialize ESC controller
        
        Args:
            config_file: Path to ESC configuration file
        """
        self.logger = setup_logging(log_level=logging.INFO)
        self.config = load_config(config_file)
        
        # Initialize pigpio daemon
        self.pi = None
        self.connected = False
        
        # Motor states
        self.motors = {}
        self.throttle_values = {}
        self.is_armed = False
        
        # Initialize motors from config
        self._init_motors()
    
    def _init_motors(self):
        """Initialize motor configuration from config file"""
        for i in range(1, self.config['esc']['count'] + 1):
            motor_key = f'motor{i}'
            motor_config = self.config[motor_key]
            
            self.motors[motor_key] = {
                'gpio_pin': motor_config['gpio_pin'],
                'min_pulse': motor_config['min_pulse'],
                'max_pulse': motor_config['max_pulse'],
                'neutral_pulse': motor_config['neutral_pulse'],
                'direction': motor_config['direction'],
                'ramp_rate': motor_config['ramp_rate'],
                'max_throttle': motor_config['max_throttle'],
                'current_throttle': 0.0,
            }
            
            self.throttle_values[motor_key] = motor_config['neutral_pulse']
    
    def connect(self):
        """
        Connect to pigpio daemon
        
        Returns:
            bool: True if successful
        """
        try:
            self.pi = pigpio.pi()
            if not self.pi.connected:
                raise RuntimeError("Failed to connect to pigpio daemon")
            
            self.logger.info("Connected to pigpio daemon")
            self.connected = True
            
            # Initialize all motors
            for motor_key, motor_config in self.motors.items():
                gpio_pin = motor_config['gpio_pin']
                neutral_pulse = motor_config['neutral_pulse']
                
                # Set initial PWM value to neutral
                self.pi.hardware_PWM(gpio_pin, self.config['esc']['pwm_frequency'], 
                                   neutral_pulse)
                
                self.logger.info(f"{motor_key} initialized on GPIO {gpio_pin}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to pigpio: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from pigpio daemon"""
        if self.pi:
            # Set all motors to neutral before disconnect
            self.set_neutral()
            time.sleep(0.5)
            self.pi.stop()
            self.connected = False
            self.logger.info("Disconnected from pigpio daemon")
    
    def arm(self):
        """
        Arm the ESCs (enable motor control)
        
        Returns:
            bool: True if successful
        """
        if not self.connected:
            self.logger.error("Not connected to pigpio")
            return False
        
        try:
            # Send initialization pulse
            init_config = self.config['calibration']
            init_pulse = init_config['initialization_pulse']
            init_time = init_config['initialization_time']
            
            self.logger.info(f"Arming ESCs with {init_pulse}µs pulse for {init_time}s")
            
            for motor_key in self.motors.keys():
                self._set_pwm(motor_key, init_pulse)
            
            time.sleep(init_time)
            self.is_armed = True
            self.logger.info("ESCs armed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to arm ESCs: {e}")
            return False
    
    def disarm(self):
        """Disarm the ESCs (disable motor control)"""
        self.is_armed = False
        self.set_neutral()
        self.logger.info("ESCs disarmed")
    
    def _set_pwm(self, motor_key, pulse_us):
        """
        Set PWM pulse for a motor
        
        Args:
            motor_key: 'motor1' or 'motor2'
            pulse_us: Pulse width in microseconds
        """
        if not self.connected:
            return
        
        motor_config = self.motors[motor_key]
        gpio_pin = motor_config['gpio_pin']
        
        # Clamp to valid range
        pulse_clamped = clamp(pulse_us, motor_config['min_pulse'], 
                            motor_config['max_pulse'])
        
        # Send PWM signal
        self.pi.hardware_PWM(gpio_pin, self.config['esc']['pwm_frequency'], 
                           pulse_clamped)
        
        self.throttle_values[motor_key] = pulse_clamped
    
    def set_throttle(self, motor_key, throttle_percent):
        """
        Set throttle for a motor (0-100%)
        
        Args:
            motor_key: 'motor1' or 'motor2'
            throttle_percent: Throttle percentage (0-100)
        """
        if not self.connected or not self.is_armed:
            return
        
        motor_config = self.motors[motor_key]
        
        # Clamp throttle
        throttle = clamp(throttle_percent, 0, motor_config['max_throttle'])
        
        # Convert percentage to pulse
        min_pulse = motor_config['min_pulse']
        max_pulse = motor_config['max_pulse']
        pulse = map_range(throttle, 0, 100, min_pulse, max_pulse)
        
        self._set_pwm(motor_key, pulse)
        motor_config['current_throttle'] = throttle
    
    def set_both_throttle(self, throttle_left, throttle_right):
        """
        Set throttle for both motors
        
        Args:
            throttle_left: Left motor throttle (0-100%)
            throttle_right: Right motor throttle (0-100%)
        """
        self.set_throttle('motor1', throttle_left)
        self.set_throttle('motor2', throttle_right)
    
    def set_neutral(self):
        """Set both motors to neutral throttle"""
        for motor_key in self.motors.keys():
            motor_config = self.motors[motor_key]
            self._set_pwm(motor_key, motor_config['neutral_pulse'])
            motor_config['current_throttle'] = 0.0
    
    def get_throttle(self, motor_key):
        """
        Get current throttle value for a motor
        
        Args:
            motor_key: 'motor1' or 'motor2'
        
        Returns:
            float: Throttle percentage (0-100)
        """
        return self.motors[motor_key]['current_throttle']
    
    def get_pwm_value(self, motor_key):
        """
        Get current PWM value for a motor
        
        Args:
            motor_key: 'motor1' or 'motor2'
        
        Returns:
            int: PWM pulse width in microseconds
        """
        return self.throttle_values[motor_key]
    
    def is_armed_state(self):
        """
        Check if ESCs are armed
        
        Returns:
            bool: True if armed
        """
        return self.is_armed
    
    def calibrate_esc(self):
        """
        Calibrate ESCs (run before first use)
        
        This function goes through the ESC calibration sequence:
        1. Send max throttle
        2. Send min throttle
        3. Send neutral throttle
        """
        self.logger.info("Starting ESC calibration...")
        
        if not self.connected:
            self.logger.error("Not connected to pigpio")
            return False
        
        try:
            for motor_key in self.motors.keys():
                motor_config = self.motors[motor_key]
                
                self.logger.info(f"Calibrating {motor_key}...")
                
                # Step 1: Send max throttle
                self.logger.info(f"{motor_key}: Send max throttle (2000µs)")
                self._set_pwm(motor_key, motor_config['max_pulse'])
                time.sleep(2)
                
                # Step 2: Send min throttle
                self.logger.info(f"{motor_key}: Send min throttle (1000µs)")
                self._set_pwm(motor_key, motor_config['min_pulse'])
                time.sleep(2)
                
                # Step 3: Send neutral throttle
                self.logger.info(f"{motor_key}: Send neutral throttle ({motor_config['neutral_pulse']}µs)")
                self._set_pwm(motor_key, motor_config['neutral_pulse'])
                time.sleep(1)
            
            self.logger.info("ESC calibration complete!")
            return True
            
        except Exception as e:
            self.logger.error(f"ESC calibration failed: {e}")
            return False


if __name__ == "__main__":
    # Test ESC controller
    esc = ESCController()
    
    if esc.connect():
        print("Connected to ESC controller!")
        
        if esc.arm():
            print("ESCs armed")
            
            # Test throttle
            esc.set_throttle('motor1', 30)
            esc.set_throttle('motor2', 30)
            time.sleep(2)
            
            esc.set_neutral()
            esc.disarm()
        
        esc.disconnect()
    else:
        print("Failed to connect to ESC controller")
