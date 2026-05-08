# Hardware Setup Guide

## Components

- **Pixhawk Flight Controller** (Pixhawk 2.4.8 or compatible)
- **Raspberry Pi 4** (2GB+ RAM)
- **2x Brushless Motors** (similar specifications)
- **2x Brushless ESCs** (30A+)
- **Power Distribution Board**
- **LiPo Battery** (3S or 4S recommended)
- **USB Cable** (USB micro-B to USB-A for Pixhawk connection)
- **Servo Cables** (for ESC PWM control)
- **Mounting hardware**

## Wiring Diagram

```
┌─────────────────────────────────────────────────────┐
│                  Raspberry Pi 4                     │
│  ┌─────────────────────────────────────────────┐   │
│  │GPIO Pins:                                   │   │
│  │GPIO 17 (Pin 11) → ESC Motor 1 PWM Signal    │   │
│  │GPIO 27 (Pin 13) → ESC Motor 2 PWM Signal    │   │
│  │GND (Pin 6)      → Common Ground             │   │
│  └─────────────────────────────────────────────┘   │
│                      ↓ USB                         │
└─────────────────────────────────────────────────────┘
                        ↓
              ┌──────────────────┐
              │     Pixhawk      │
              │  (Flight Ctrl)   │
              └──────────────────┘
                        ↓
         (Telem/GPS connections)

              Power Distribution
              ┌────────────────┐
              │      PDB       │
              └────────────────┘
                      ↓
          ┌─────────────────────┐
          │    LiPo Battery     │
          │   (3S or 4S)        │
          └─────────────────────┘
                ↓         ↓
          ┌─────────┐  ┌─────────┐
          │ ESC #1  │  │ ESC #2  │
          │         │  │         │
          │ PWM→17  │  │ PWM→27  │
          │ GND→6   │  │ GND→6   │
          └─────────┘  └─────────┘
              ↓            ↓
          ┌───────┐    ┌───────┐
          │Motor1 │    │Motor2 │
          └───────┘    └───────┘
```

## Pixhawk to Raspberry Pi Connection

### Serial Connection (USB)

1. Connect Pixhawk to RPi via USB cable (Micro-B to USB-A)
2. Check port:
   ```bash
   ls /dev/tty*
   # Look for /dev/ttyUSB0 or /dev/ttyACM0
   ```
3. Update `config/pixhawk_config.yaml`:
   ```yaml
   connection:
     type: serial
     serial:
       port: /dev/ttyUSB0
       baudrate: 921600
   ```

### MAVProxy Connection (UDP)

If running MAVProxy on RPi:
```bash
mav --master=/dev/ttyUSB0 --baudrate 921600 --out udpin:127.0.0.1:14550
```

Then update config:
```yaml
connection:
  type: udp
  udp:
    address: 127.0.0.1
    port: 14550
```

## ESC GPIO Wiring

### Motor 1 (GPIO 17 - Pin 11)

```
Raspberry Pi Pin 11 (GPIO 17) → ESC Signal Wire (White/Yellow)
Raspberry Pi Pin 6  (GND)      → ESC Ground Wire (Black)
ESC Battery Connector           → Power from PDB
ESC Motor Connector             → Motor 1
```

### Motor 2 (GPIO 27 - Pin 13)

```
Raspberry Pi Pin 13 (GPIO 27) → ESC Signal Wire (White/Yellow)
Raspberry Pi Pin 9  (GND)      → ESC Ground Wire (Black)
ESC Battery Connector           → Power from PDB
ESC Motor Connector             → Motor 2
```

## Power Distribution

### Battery to Power Distribution Board

```
LiPo Battery Positive  → PDB +V
LiPo Battery Negative  → PDB GND
```

### Power Distribution Board to Components

```
+V (high current)  → ESC #1 Power
+V (high current)  → ESC #2 Power
+V (5V regulated)  → Pixhawk Power Module
+V (5V regulated)  → Raspberry Pi (Optional - can use separate USB)
GND                → All GND connections (common ground!)
```

## Configuration Files

### Update GPIO Pin Numbers

If using different GPIO pins, update `config/esc_config.yaml`:

```yaml
motor1:
  gpio_pin: 17      # Change to your GPIO pin

motor2:
  gpio_pin: 27      # Change to your GPIO pin
```

### Update Pixhawk Port

If using different connection, update `config/pixhawk_config.yaml`:

```yaml
serial:
  port: /dev/ttyUSB0    # Check with: ls /dev/tty*
  baudrate: 921600
```

## Safety Checklist

- [ ] **Remove propellers** during testing
- [ ] **Check all connections** are secure
- [ ] **Verify common ground** between all components
- [ ] **Test PWM signals** without motors first
- [ ] **Start with low throttle** values (10-20%)
- [ ] **Keep hands away** from rotating parts
- [ ] **Use failsafe settings** in configuration
- [ ] **Test in enclosed area** away from people
- [ ] **Have emergency stop** procedure ready

## Voltage Check

```bash
# Check battery voltage
# 3S LiPo: 11.1V - 12.6V (nominal 11.1V)
# 4S LiPo: 14.8V - 16.8V (nominal 14.8V)

# Never discharge below:
# 3S: 9.0V (3.0V per cell)
# 4S: 12.0V (3.0V per cell)
```

## Testing Connections

```bash
# Test Pixhawk connection
python3 src/main.py --test-imu

# Test ESC (without propellers!)
python3 src/main.py --test-esc

# Check GPIO
gpio readall  # Requires WiringPi
```
