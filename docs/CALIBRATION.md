# Calibration Guide

## Overview

Proper calibration is crucial for stable balancing. This guide covers:

1. IMU Calibration (gyro and accelerometer offsets)
2. ESC Calibration (PWM range)
3. PID Tuning (control gains)

## 1. IMU Calibration

### Gyroscope Offset Calibration

The robot should remain **completely stationary** on a level surface.

```bash
python3 src/main.py --calibrate
```

The calibration script will:
1. Read IMU data for 5 seconds
2. Calculate average pitch and roll values
3. Store offsets in `config/pixhawk_config.yaml`

### Verify Calibration

After calibration, pitch and roll should read ~0° when robot is on a level surface:

```bash
python3 src/main.py --test-imu
```

Example output:
```
Pitch: -0.12°, Roll: 0.05°   ✓ Good
Pitch: 5.32°, Roll: -2.14°   ✗ Needs recalibration
```

## 2. ESC Calibration

ESCs need to know the PWM range for proper motor control.

### Preparation

⚠️ **CRITICAL: REMOVE PROPELLERS BEFORE CALIBRATION**

### Calibration Steps

1. Disconnect battery
2. Run calibration:
   ```bash
   sudo python3 src/main.py --calibrate-esc
   ```
3. Follow on-screen instructions
4. The ESCs will beep as they learn the PWM range
5. Reconnect battery when prompted

### Expected Beeps

- 1 beep: Power on
- 2 beeps: Min throttle recognized
- 3 beeps: Max throttle recognized
- Steady beeping: Calibration complete

## 3. PID Tuning

PID tuning is critical for stable balancing. Use the Ziegler-Nichols method or manual tuning.

### Configuration

Edit `config/pid_params.yaml`:

```yaml
pitch_pid:
  Kp: 1.5    # Start conservative
  Ki: 0.1
  Kd: 0.3
```

### Manual Tuning Method

#### Step 1: Find Kp (Proportional)

1. Set Ki = 0, Kd = 0
2. Increase Kp gradually (0.5 → 1.0 → 1.5 → 2.0)
3. Tilt robot slowly by hand
4. Robot should resist tilting and return to upright
5. Stop when oscillation becomes noticeable

Example:
```yaml
Kp: 1.2  # Good - stable without oscillation
Ki: 0.0
Kd: 0.0
```

#### Step 2: Add Kd (Derivative)

1. Keep Kp at value from Step 1
2. Set Ki = 0, increase Kd gradually (0.1 → 0.2 → 0.3)
3. Push robot to tilt - it should resist quickly
4. Stop when overshoot becomes noticeable

Example:
```yaml
Kp: 1.2
Ki: 0.0
Kd: 0.2  # Reduces overshoot
```

#### Step 3: Add Ki (Integral)

1. Keep Kp and Kd from previous steps
2. Set small Ki value (0.05 - 0.15)
3. Tilt robot and hold at angle
4. Ki helps return to setpoint slowly
5. Too much Ki causes oscillation

Example:
```yaml
Kp: 1.2
Ki: 0.08  # Small integral
Kd: 0.2
```

### Ziegler-Nichols Method

1. Set Ki = 0, Kd = 0
2. Increase Kp until system oscillates (Ku)
3. Measure oscillation period (Pu)
4. Calculate gains:
   ```
   Kp = 0.6 * Ku
   Ki = 1.2 * Ku / Pu
   Kd = 0.075 * Ku * Pu
   ```

### Tuning Checklist

- [ ] Pitch control stable (forward/backward)
- [ ] Roll control stable (left/right)
- [ ] No excessive oscillation
- [ ] Responds quickly to disturbances
- [ ] Smooth motor output (no jerking)
- [ ] Battery voltage adequate (> 3V per cell)

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Oscillation | Kp too high | Decrease Kp |
| Slow response | Kp too low | Increase Kp |
| Overshoot | Kd too low | Increase Kd |
| Bouncing | Kd too high | Decrease Kd |
| Drift | Ki too low | Increase Ki |
| Oscillation | Ki too high | Decrease Ki |

## Testing PID Settings

### Real-World Test

1. Place robot in safe, enclosed space
2. Start with very low motor speeds (PWM 1100-1200)
3. Gradually increase when stable
4. Gently push robot to test response
5. Record results and adjust gains

### Data Logging

Check logs in `logs/` directory for:
- Motor PWM values
- Sensor readings
- PID errors and outputs
- Timestamps

## Final Verification

```bash
# Check calibration status
python3 src/main.py --status

# Output should show:
# Pixhawk connected: True
# ESC armed: False
# IMU readings close to 0 when stationary
```

## Safety Reminders

⚠️ **ALWAYS:**
- Start with low gains
- Remove propellers during ESC calibration
- Keep a failsafe procedure ready
- Stay away from rotating parts
- Have a kill switch accessible
- Test in a contained space
