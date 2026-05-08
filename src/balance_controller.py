"""
Balance Controller Module
Main balancing logic integrating all components
"""

import logging
import time
import sys
from pixhawk_interface import PixhawkInterface
from esc_control import ESCController
from imu_reader import IMUReader
from pid_controller import BalancePIDController
from utils import setup_logging, load_config


class BalanceController:
    """Main balance controller - coordinates all components"""
    
    def __init__(self):
        """Initialize balance controller"""
        self.logger = setup_logging(log_level=logging.INFO)
        
        # Initialize components
        self.pixhawk = PixhawkInterface()
        self.esc = ESCController()
        self.imu = None
        self.pid = BalancePIDController()
        
        # Control loop parameters
        self.running = False
        self.frequency = 100  # Hz
        self.dt = 1.0 / self.frequency
        
        # Safety
        self.emergency_stop = False
        self.failsafe_engaged = False
    
    def initialize(self):
        """
        Initialize all subsystems
        
        Returns:
            bool: True if all systems initialized successfully
        """
        self.logger.info("Initializing balance controller...")
        
        # Connect to Pixhawk
        self.logger.info("Connecting to Pixhawk...")
        if not self.pixhawk.connect():
            self.logger.error("Failed to connect to Pixhawk")
            return False
        
        # Create IMU reader
        self.imu = IMUReader(self.pixhawk)
        
        # Wait for stable IMU data
        self.logger.info("Waiting for stable IMU data...")
        if not self.imu.wait_for_stable_reading(timeout=10):
            self.logger.error("Failed to get stable IMU reading")
            return False
        
        # Connect to ESC controller
        self.logger.info("Connecting to ESC controller...")
        if not self.esc.connect():
            self.logger.error("Failed to connect to ESC controller")
            return False
        
        self.logger.info("All systems initialized successfully!")
        return True
    
    def calibrate(self):
        """Run full calibration procedure"""
        self.logger.info("Starting calibration procedure...")
        
        # Calibrate IMU
        self.logger.info("\n=== IMU Calibration ===")
        if not self.imu.calibrate_imu(duration=5):
            self.logger.error("IMU calibration failed")
            return False
        
        # Calibrate ESCs
        self.logger.info("\n=== ESC Calibration ===")
        self.logger.info("Disconnect the battery before starting ESC calibration")
        input("Press Enter to continue...")
        
        if not self.esc.calibrate_esc():
            self.logger.error("ESC calibration failed")
            return False
        
        self.logger.info("\nCalibration complete!")
        return True
    
    def arm(self):
        """Arm the system (enable motors)"""
        self.logger.info("Arming system...")
        
        if not self.esc.arm():
            self.logger.error("Failed to arm ESCs")
            return False
        
        self.logger.info("System armed and ready!")
        return True
    
    def disarm(self):
        """Disarm the system (disable motors)"""
        self.logger.info("Disarming system...")
        self.esc.disarm()
        self.esc.set_neutral()
    
    def emergency_stop_system(self):
        """Perform emergency stop"""
        self.logger.error("EMERGENCY STOP ACTIVATED!")
        self.emergency_stop = True
        self.running = False
        self.esc.set_neutral()
        self.esc.disarm()
    
    def run_control_loop(self, duration=None):
        """
        Run main control loop
        
        Args:
            duration: Run duration in seconds (None for infinite)
        """
        self.logger.info("Starting control loop...")
        
        # Arm ESCs
        if not self.arm():
            self.logger.error("Failed to arm system")
            return False
        
        self.running = True
        self.emergency_stop = False
        
        start_time = time.time()
        loop_count = 0
        
        try:
            while self.running:
                loop_start = time.time()
                
                # Check duration
                if duration and time.time() - start_time > duration:
                    self.logger.info("Duration limit reached")
                    break
                
                # Read IMU data
                imu_data = self.imu.read_all()
                pitch = imu_data['attitude']['pitch']
                roll = imu_data['attitude']['roll']
                yaw = imu_data['attitude']['yaw']
                
                # Check if Pixhawk still connected
                if not self.pixhawk.is_connected():
                    self.logger.error("Lost connection to Pixhawk!")
                    self.failsafe_engaged = True
                    break
                
                # Update PID controllers
                control_output = self.pid.update(pitch, roll, yaw, self.dt)
                
                # Get motor commands
                motor_left = control_output['motor_left']
                motor_right = control_output['motor_right']
                
                # Set motor throttle
                self.esc.set_both_throttle(motor_left, motor_right)
                
                # Log data periodically
                if loop_count % 100 == 0:
                    self.logger.info(
                        f"Pitch: {pitch:6.2f}° | Roll: {roll:6.2f}° | "
                        f"Motor L: {motor_left:6.1f}% | Motor R: {motor_right:6.1f}%"
                    )
                
                loop_count += 1
                
                # Maintain loop frequency
                loop_time = time.time() - loop_start
                sleep_time = self.dt - loop_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            self.logger.info("Control loop interrupted by user")
        
        except Exception as e:
            self.logger.error(f"Error in control loop: {e}")
        
        finally:
            self.disarm()
            self.running = False
        
        return True
    
    def shutdown(self):
        """Shutdown and cleanup"""
        self.logger.info("Shutting down...")
        
        if self.running:
            self.disarm()
        
        if self.esc:
            self.esc.disconnect()
        
        if self.pixhawk:
            self.pixhawk.disconnect()
        
        self.logger.info("Shutdown complete")
    
    def print_status(self):
        """Print current system status"""
        print("\n" + "="*50)
        print("SYSTEM STATUS")
        print("="*50)
        
        print(f"Pixhawk connected: {self.pixhawk.is_connected()}")
        print(f"ESC armed: {self.esc.is_armed_state()}")
        print(f"Running: {self.running}")
        print(f"Emergency stop: {self.emergency_stop}")
        
        if self.imu:
            attitude = self.imu.read_attitude()
            print(f"\nIMU Data:")
            print(f"  Pitch: {attitude['pitch']:6.2f}°")
            print(f"  Roll:  {attitude['roll']:6.2f}°")
            print(f"  Yaw:   {attitude['yaw']:6.2f}°")
        
        if self.esc:
            print(f"\nMotor Status:")
            print(f"  Motor 1: {self.esc.get_throttle('motor1'):.1f}%")
            print(f"  Motor 2: {self.esc.get_throttle('motor2'):.1f}%")
        
        diagnostics = self.pid.get_diagnostics()
        print(f"\nPID Status:")
        print(f"  Pitch output: {diagnostics['pitch']['output']:.2f}")
        print(f"  Roll output:  {diagnostics['roll']['output']:.2f}")
        print(f"  Yaw output:   {diagnostics['yaw']['output']:.2f}")
        
        print("="*50 + "\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Self-Balancing Bot Controller')
    parser.add_argument('--calibrate', action='store_true', help='Run calibration')
    parser.add_argument('--duration', type=float, default=None, help='Run duration (seconds)')
    parser.add_argument('--test-imu', action='store_true', help='Test IMU only')
    parser.add_argument('--test-esc', action='store_true', help='Test ESC only')
    parser.add_argument('--status', action='store_true', help='Print status and exit')
    
    args = parser.parse_args()
    
    controller = BalanceController()
    
    try:
        # Initialize
        if not controller.initialize():
            return False
        
        # Handle different modes
        if args.calibrate:
            return controller.calibrate()
        
        elif args.test_imu:
            controller.logger.info("Testing IMU only...")
            for i in range(20):
                attitude = controller.imu.read_attitude()
                print(f"Pitch: {attitude['pitch']:.2f}°, Roll: {attitude['roll']:.2f}°")
                time.sleep(0.1)
            return True
        
        elif args.test_esc:
            controller.logger.info("Testing ESC...")
            if controller.arm():
                for throttle in [10, 20, 30, 20, 10, 0]:
                    controller.esc.set_both_throttle(throttle, throttle)
                    print(f"Throttle: {throttle}%")
                    time.sleep(1)
                controller.disarm()
            return True
        
        elif args.status:
            controller.print_status()
            return True
        
        else:
            # Run normal balancing
            return controller.run_control_loop(duration=args.duration)
    
    except KeyboardInterrupt:
        controller.logger.info("Interrupted by user")
    
    finally:
        controller.shutdown()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
