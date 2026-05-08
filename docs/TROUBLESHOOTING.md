# Troubleshooting Guide

## Connection Issues

### Cannot Connect to Pixhawk

**Problem:** `Failed to connect to Pixhawk`

**Solutions:**

1. Check USB cable connection
   ```bash
   ls /dev/tty*
   ```
   Should show `/dev/ttyUSB0` or `/dev/ttyACM0`

2. Check permissions
   ```bash
   sudo usermod -a -G dialout pi
   ```
   Then log out and back in.

3. Try different baud rates in `config/pixhawk_config.yaml`:
   ```yaml
   baudrate: 921600  # or 115200, 57600
   ```

4. Test with MAVProxy:
   ```bash
   mavproxy.py --master=/dev/ttyUSB0 --baudrate 921600
   ```

### Cannot Connect to ESCs

**Problem:** `Failed to connect to pigpio`

**Solutions:**

1. Start pigpio daemon
   ```bash
   sudo systemctl start pigpiod
   sudo systemctl status pigpiod
   ```

2. Reinstall pigpio
   ```bash
   wget https://github.com/joan2937/pigpio/archive/master.zip
   unzip master.zip
   cd pigpio-master
   make
   sudo make install
   sudo systemctl restart pigpiod
   ```

3. Check GPIO pins in config
   ```bash
   gpio readall
   ```

## IMU Issues

### No IMU Data

**Problem:** `Timeout waiting for Pixhawk data`

**Solutions:**

1. Check Pixhawk is powered
2. Verify USB connection is solid
3. Check baud rate matches Pixhawk settings
4. Increase timeout in config:
   ```yaml
   timeout:
     data_read: 1.0  # Increase from 0.5
   ```

### Unstable IMU Readings

**Problem:** Pitch/roll values jumping around

**Solutions:**

1. Recalibrate IMU
   ```bash
   python3 src/main.py --calibrate
   ```

2. Increase filter window size in config:
   ```yaml
   imu:
     filter:
       window_size: 10  # Increase smoothing
   ```

3. Check for vibrations - add damping

4. Check battery voltage (should be stable)

## Motor/ESC Issues

### Motors Don't Spin

**Problem:** ESC armed but no motor movement

**Solutions:**

1. Check battery voltage
   ```bash
   # Should be:
   # 3S LiPo: 11.1V - 12.6V
   # 4S LiPo: 14.8V - 16.8V
   ```

2. Recalibrate ESCs
   ```bash
   python3 src/main.py --calibrate-esc
   ```

3. Check PWM signal with oscilloscope:
   ```bash
   # GPIO 17 and 27 should show 1000-2000µs pulses
   ```

4. Try different max_throttle in config:
   ```yaml
   motor1:
     max_throttle: 100  # or reduce to 80
   ```

### Motors Spin But Unstable

**Problem:** Robot tilts too much or oscillates wildly

**Solutions:**

1. Reduce PID gains
   ```yaml
   Kp: 0.8  # Reduce from 1.5
   Kd: 0.2  # Reduce from 0.3
   ```

2. Check motor direction - both should push in same direction for balancing
   ```bash
   python3 src/main.py --test-esc
   ```

3. Check motor alignment - should be perfectly parallel

4. Verify battery voltage is stable (not sagging)

### One Motor Spins Faster Than Other

**Problem:** Robot drifts left or right

**Solutions:**

1. Check motor and ESC specs - should be matched

2. Recalibrate ESCs individually

3. Adjust motor neutral pulse if needed

4. Add trim value to motor2 if motors are different:
   ```yaml
   motor2:
     trim: 0.95  # Reduce speed of motor2 to 95%
   ```

## Power Issues

### Battery Voltage Drops Quickly

**Problem:** Voltage drops during operation

**Solutions:**

1. Check battery condition
   - Measure internal resistance
   - Check cells individually

2. Check for shorts in wiring

3. Reduce motor throttle/load

4. Use higher capacity battery

5. Check battery connectors - clean with pencil eraser

### Pixhawk Powers Off

**Problem:** System randomly reboots

**Solutions:**

1. Check battery voltage - ensure > 3V per cell

2. Use separate power for Pixhawk

3. Check power connector is secure

4. Add capacitor to power line (1000µF minimum)

## Software Issues

### ImportError: No module named 'pymavlink'

**Solution:**
```bash
sudo pip3 install pymavlink
```

### ImportError: No module named 'pigpio'

**Solution:**
```bash
sudo pip3 install pigpio
```

### Script Hangs or Freezes

**Problem:** Program doesn't respond

**Solutions:**

1. Increase timeout in config

2. Kill process and restart
   ```bash
   sudo pkill -f "python3 src/main.py"
   ```

3. Check system resources
   ```bash
   free -h
   top
   ```

### Wrong IMU/Motor Direction

**Problem:** Robot falls in opposite direction

**Solutions:**

1. Reverse motor direction in ESC calibration

2. Or adjust in config:
   ```yaml
   motor1:
     direction: reverse  # Was: forward
   ```

## Performance Tuning

### Robot Oscillates

1. Reduce Kp
2. Increase Kd
3. Reduce filter window size for faster response

### Robot Response Too Slow

1. Increase Kp
2. Reduce filter window size
3. Increase control loop frequency in config

### High CPU Usage

1. Reduce control loop frequency
2. Disable logging if not needed
3. Use simpler filter (reduce window size)

## Getting Help

If you're stuck:

1. Check [README.md](../README.md) and docs
2. Review configuration files - all have comments
3. Enable verbose logging:
   ```python
   # In code, change:
   setup_logging(log_level=logging.DEBUG)
   ```
4. Check system logs:
   ```bash
   dmesg
   journalctl -u pigpiod
   ```
5. Post issue on GitHub with:
   - System information
   - Error messages
   - Configuration files (redact sensitive info)
   - Steps to reproduce
