"""
PID Controller Module
Implements PID control loop for balancing
"""

import logging
import time
from utils import setup_logging, load_config, clamp


class PIDController:
    """Generic PID controller implementation"""
    
    def __init__(self, name, kp, ki, kd, output_min=-100, output_max=100):
        """
        Initialize PID controller
        
        Args:
            name: Controller name (for logging)
            kp: Proportional gain
            ki: Integral gain
            kd: Derivative gain
            output_min: Minimum output value
            output_max: Maximum output value
        """
        self.name = name
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_min = output_min
        self.output_max = output_max
        
        # PID terms
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = time.time()
        
        # Anti-windup limits
        self.integral_min = output_min / 2 if ki > 0 else 0
        self.integral_max = output_max / 2 if ki > 0 else 0
        
        self.logger = setup_logging()
    
    def update(self, error, dt=None):
        """
        Update PID controller and calculate output
        
        Args:
            error: Current error value
            dt: Time delta (seconds). If None, calculated from last update
        
        Returns:
            float: PID output value
        """
        # Calculate time delta
        if dt is None:
            current_time = time.time()
            dt = current_time - self.last_time
            self.last_time = current_time
        
        if dt <= 0:
            return 0.0
        
        # Proportional term
        p_term = self.kp * error
        
        # Integral term (with anti-windup)
        self.integral += error * dt
        self.integral = clamp(self.integral, self.integral_min, self.integral_max)
        i_term = self.ki * self.integral
        
        # Derivative term
        derivative = (error - self.last_error) / dt if dt > 0 else 0
        d_term = self.kd * derivative
        
        self.last_error = error
        
        # Calculate output
        output = p_term + i_term + d_term
        output = clamp(output, self.output_min, self.output_max)
        
        return output
    
    def reset(self):
        """Reset PID controller state"""
        self.integral = 0.0
        self.last_error = 0.0
        self.last_time = time.time()
    
    def set_gains(self, kp, ki, kd):
        """
        Update PID gains
        
        Args:
            kp: Proportional gain
            ki: Integral gain
            kd: Derivative gain
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
    
    def set_integral_limits(self, min_val, max_val):
        """
        Set integral anti-windup limits
        
        Args:
            min_val: Minimum integral value
            max_val: Maximum integral value
        """
        self.integral_min = min_val
        self.integral_max = max_val


class BalancePIDController:
    """
    Complete PID controller system for self-balancing bot
    Manages pitch, roll, and yaw control
    """
    
    def __init__(self, config_file='config/pid_params.yaml'):
        """
        Initialize balance PID controller
        
        Args:
            config_file: Path to PID configuration file
        """
        self.logger = setup_logging(log_level=logging.INFO)
        self.config = load_config(config_file)
        
        # Create PID controllers for each axis
        pitch_config = self.config['pitch_pid']
        roll_config = self.config['roll_pid']
        yaw_config = self.config['yaw_pid']
        
        self.pitch_pid = PIDController(
            'Pitch',
            pitch_config['Kp'],
            pitch_config['Ki'],
            pitch_config['Kd'],
            pitch_config['output_min'],
            pitch_config['output_max']
        )
        
        self.roll_pid = PIDController(
            'Roll',
            roll_config['Kp'],
            roll_config['Ki'],
            roll_config['Kd'],
            roll_config['output_min'],
            roll_config['output_max']
        )
        
        self.yaw_pid = PIDController(
            'Yaw',
            yaw_config['Kp'],
            yaw_config['Ki'],
            yaw_config['Kd'],
            yaw_config['output_min'],
            yaw_config['output_max']
        )
        
        # Set integral limits
        self.pitch_pid.set_integral_limits(
            pitch_config['integral_min'],
            pitch_config['integral_max']
        )
        self.roll_pid.set_integral_limits(
            roll_config['integral_min'],
            roll_config['integral_max']
        )
        self.yaw_pid.set_integral_limits(
            yaw_config['integral_min'],
            yaw_config['integral_max']
        )
        
        # Control loop settings
        control_config = self.config['control_loop']
        self.setpoint_pitch = control_config['setpoint']['pitch']
        self.setpoint_roll = control_config['setpoint']['roll']
        self.setpoint_yaw = control_config['setpoint']['yaw']
        self.frequency = control_config['frequency']
        
        # Dead zones
        dead_zone = control_config['dead_zone']
        self.pitch_dead_zone = dead_zone['pitch']
        self.roll_dead_zone = dead_zone['roll']
        self.yaw_dead_zone = dead_zone['yaw']
        
        # Safety settings
        safety = self.config['safety']
        self.max_error = safety['max_error']
        self.max_error_rate = safety['max_error_rate']
        
        # Motor mapping
        self.motor_mapping = control_config['motor_mapping']['method']
        
        # Last outputs
        self.last_pitch_output = 0.0
        self.last_roll_output = 0.0
        self.last_yaw_output = 0.0
    
    def update(self, pitch, roll, yaw, dt=None):
        """
        Update all PID controllers
        
        Args:
            pitch: Current pitch angle (degrees)
            roll: Current roll angle (degrees)
            yaw: Current yaw angle (degrees)
            dt: Time delta (seconds)
        
        Returns:
            dict: Output values for pitch, roll, yaw control
        """
        # Apply dead zones
        pitch_error = pitch - self.setpoint_pitch
        if abs(pitch_error) < self.pitch_dead_zone:
            pitch_error = 0.0
        
        roll_error = roll - self.setpoint_roll
        if abs(roll_error) < self.roll_dead_zone:
            roll_error = 0.0
        
        yaw_error = yaw - self.setpoint_yaw
        if abs(yaw_error) < self.yaw_dead_zone:
            yaw_error = 0.0
        
        # Check safety limits
        if abs(pitch_error) > self.max_error or abs(roll_error) > self.max_error:
            self.logger.warning(f"Error exceeds safety limit! Pitch: {pitch_error:.2f}°, Roll: {roll_error:.2f}°")
            self.reset()
            return {
                'pitch': 0.0,
                'roll': 0.0,
                'yaw': 0.0,
                'motor_left': 0.0,
                'motor_right': 0.0,
            }
        
        # Update PID controllers
        pitch_output = self.pitch_pid.update(pitch_error, dt)
        roll_output = self.roll_pid.update(roll_error, dt)
        yaw_output = self.yaw_pid.update(yaw_error, dt)
        
        self.last_pitch_output = pitch_output
        self.last_roll_output = roll_output
        self.last_yaw_output = yaw_output
        
        # Calculate motor commands
        motor_outputs = self._map_to_motors(pitch_output, roll_output, yaw_output)
        
        return {
            'pitch': pitch_output,
            'roll': roll_output,
            'yaw': yaw_output,
            'motor_left': motor_outputs['left'],
            'motor_right': motor_outputs['right'],
        }
    
    def _map_to_motors(self, pitch_output, roll_output, yaw_output):
        """
        Map PID outputs to motor commands
        
        Args:
            pitch_output: Pitch PID output
            roll_output: Roll PID output
            yaw_output: Yaw PID output
        
        Returns:
            dict: Motor commands for left and right motors
        """
        if self.motor_mapping == 'differential':
            # Differential drive
            # Forward = pitch
            # Turn = roll + yaw
            forward = pitch_output
            turn = roll_output + yaw_output
            
            left = forward + turn
            right = forward - turn
            
            return {
                'left': clamp(left, -100, 100),
                'right': clamp(right, -100, 100),
            }
        
        elif self.motor_mapping == 'independent':
            # Independent motor control
            # Left motor = pitch + roll
            # Right motor = pitch - roll
            left = pitch_output + roll_output
            right = pitch_output - roll_output
            
            return {
                'left': clamp(left, -100, 100),
                'right': clamp(right, -100, 100),
            }
        
        else:
            # Tank drive (default)
            return {
                'left': clamp(pitch_output + roll_output, -100, 100),
                'right': clamp(pitch_output - roll_output, -100, 100),
            }
    
    def reset(self):
        """Reset all PID controllers"""
        self.pitch_pid.reset()
        self.roll_pid.reset()
        self.yaw_pid.reset()
        self.logger.info("PID controllers reset")
    
    def update_gains(self, pitch_gains=None, roll_gains=None, yaw_gains=None):
        """
        Update PID gains at runtime
        
        Args:
            pitch_gains: Tuple of (Kp, Ki, Kd) for pitch
            roll_gains: Tuple of (Kp, Ki, Kd) for roll
            yaw_gains: Tuple of (Kp, Ki, Kd) for yaw
        """
        if pitch_gains:
            self.pitch_pid.set_gains(*pitch_gains)
        if roll_gains:
            self.roll_pid.set_gains(*roll_gains)
        if yaw_gains:
            self.yaw_pid.set_gains(*yaw_gains)
    
    def get_diagnostics(self):
        """
        Get diagnostic information about PID controllers
        
        Returns:
            dict: Diagnostic data
        """
        return {
            'pitch': {
                'output': self.last_pitch_output,
                'integral': self.pitch_pid.integral,
                'gains': (self.pitch_pid.kp, self.pitch_pid.ki, self.pitch_pid.kd),
            },
            'roll': {
                'output': self.last_roll_output,
                'integral': self.roll_pid.integral,
                'gains': (self.roll_pid.kp, self.roll_pid.ki, self.roll_pid.kd),
            },
            'yaw': {
                'output': self.last_yaw_output,
                'integral': self.yaw_pid.integral,
                'gains': (self.yaw_pid.kp, self.yaw_pid.ki, self.yaw_pid.kd),
            },
        }


if __name__ == "__main__":
    # Test PID controller
    controller = BalancePIDController()
    
    # Simulate some angle changes
    pitch = 0.0
    roll = 0.0
    yaw = 0.0
    
    for i in range(20):
        # Simulate pitch increasing (robot tilting forward)
        pitch += 0.5
        
        # Get control outputs
        output = controller.update(pitch, roll, yaw)
        
        print(f"Pitch: {pitch:.2f}°, Output: {output['pitch']:.2f}, Motors: L={output['motor_left']:.2f} R={output['motor_right']:.2f}")
        
        time.sleep(0.1)
