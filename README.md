# Self-Balancing Bot with Pixhawk and Brushless ESCs

A real-time self-balancing robot using Pixhawk flight controller, 2 brushless ESCs, and Raspberry Pi with ArduRover integration.

## Features

- ✅ **Pixhawk Integration** - Real-time IMU data (pitch, roll, yaw)
- ✅ **Dual Motor Control** - PWM control for 2 brushless ESCs
- ✅ **PID-Based Balancing** - Tunable PID parameters for stable balancing
- ✅ **ArduRover Compatible** - Runs alongside ArduRover on Raspberry Pi
- ✅ **Safe Operation** - Failsafe mechanisms and error handling
- ✅ **Configurable** - YAML-based configuration for easy tuning
- ✅ **Real-time Logging** - Monitor performance and debug issues

## Hardware Requirements

- **Pixhawk Flight Controller** (Pixhawk 2.4.8 or compatible)
- **Raspberry Pi 4** (2GB+ RAM recommended)
- **2x Brushless Motors** (with matching ESCs)
- **Power Distribution Board**
- **Battery** (suitable for motors and RPi)
- **USB Cable** (Pixhawk to RPi connection)
- **Servo/PWM Cable** (for ESC control)

## Software Requirements

- **Raspberry Pi OS** (Bullseye or later)
- **Python 3.8+**
- **ArduRover** (configured and running)
- See `requirements.txt` for Python dependencies

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/arhaan2010/self-balancing-bot.git
cd self-balancing-bot
```

### 2. Install Dependencies
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev python3-rpi.gpio
pip3 install -r requirements.txt
```

### 3. Configure Hardware
Edit configuration files:
- `config/pixhawk_config.yaml` - Pixhawk connection settings
- `config/esc_config.yaml` - ESC GPIO pins and PWM frequency
- `config/pid_params.yaml` - PID tuning parameters

See [HARDWARE_SETUP.md](docs/HARDWARE_SETUP.md) for detailed wiring instructions.

### 4. Calibrate System
```bash
python3 src/main.py --calibrate
```

See [CALIBRATION.md](docs/CALIBRATION.md) for step-by-step calibration guide.

### 5. Run Balancing Bot
```bash
python3 src/main.py
```

## Project Structure

```
self-balancing-bot/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── config/                            # Configuration files
│   ├── pixhawk_config.yaml           # Pixhawk settings
│   ├── esc_config.yaml               # ESC configuration
│   └── pid_params.yaml               # PID tuning parameters
├── src/                               # Source code
│   ├── __init__.py
│   ├── main.py                       # Entry point
│   ├── pixhawk_interface.py          # Pixhawk communication
│   ├── esc_control.py                # ESC PWM control
│   ├── imu_reader.py                 # IMU data reader
│   ├── pid_controller.py             # PID control loop
│   ├── balance_controller.py         # Main balancing logic
│   └── utils.py                      # Utility functions
├── launch/                            # Launch files
│   ├── ardurover.launch              # ArduRover launch
│   └── self_balance.launch           # Self-balance launch
├── tests/                             # Unit and integration tests
│   ├── test_pixhawk.py
│   ├── test_esc.py
│   └── test_balance.py
└── docs/                              # Documentation
    ├── SETUP.md                      # Installation guide
    ├── HARDWARE_SETUP.md             # Wiring diagram and setup
    ├── CALIBRATION.md                # Calibration procedures
    └── TROUBLESHOOTING.md            # Common issues and fixes
```

## Documentation

- **[SETUP.md](docs/SETUP.md)** - Detailed installation and setup instructions
- **[HARDWARE_SETUP.md](docs/HARDWARE_SETUP.md)** - Hardware wiring and connections
- **[CALIBRATION.md](docs/CALIBRATION.md)** - Sensor and ESC calibration
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common problems and solutions

## Usage Examples

### Run with Default Configuration
```bash
python3 src/main.py
```

### Run with Custom Config
```bash
python3 src/main.py --config custom_config.yaml
```

### Calibrate ESCs
```bash
python3 src/main.py --calibrate-esc
```

### Calibrate IMU
```bash
python3 src/main.py --calibrate-imu
```

### Run Tests
```bash
python3 -m pytest tests/
```

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Self-Balancing Bot Application              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │  │
│  │  │ IMU Reader   │  │ Balance      │  │ ESC       │  │  │
│  │  │              │  │ Controller   │  │ Control   │  │  │
│  │  └──────────────┘  └──────────────┘  └───────────┘  │  │
│  │         ↓                ↓                  ↓        │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │      PID Controller (Balancing Loop)         │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│           ↓ USB                    ↓ GPIO/PWM             │
├─────────────────────────────────────────────────────────────┤
│           ↓                        ↓                        │
└─────────────────────────────────────────────────────────────┘
        │                        │
        ↓                        ↓
    ┌────────┐            ┌──────────────┐
    │Pixhawk │            │ ESC (Motor)  │
    │IMU/GPS │            │ x2           │
    └────────┘            └──────────────┘
```

## PID Tuning Guide

Adjust these parameters in `config/pid_params.yaml`:

- **Kp (Proportional)** - Increases responsiveness (0.5 - 2.0)
- **Ki (Integral)** - Reduces steady-state error (0.0 - 0.5)
- **Kd (Derivative)** - Reduces overshoot (0.1 - 1.0)

Start conservative and gradually increase gains. See [CALIBRATION.md](docs/CALIBRATION.md) for detailed tuning steps.

## Performance Monitoring

The application logs real-time data including:
- IMU readings (pitch, roll, yaw)
- Motor PWM values
- PID error and output
- System status and warnings

Check logs in `logs/` directory.

## Safety Considerations

⚠️ **Important:**
- Always test in a safe, enclosed environment first
- Start with low motor speeds (PWM 1100-1200)
- Implement physical limits and failsafes
- Use a tether or protective frame during testing
- Check all connections before powering on

## Troubleshooting

Common issues and solutions are documented in [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## References

- [Pixhawk Documentation](https://ardupilot.org/copter/)
- [MAVProxy Documentation](https://ardupilot.github.io/MAVProxy/)
- [ArduRover](https://ardupilot.org/rover/)
- [Raspberry Pi GPIO](https://www.raspberrypi.org/documentation/usage/gpio/)

## Support

For issues and questions:
1. Check [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. Review documentation files
3. Open a GitHub issue with detailed information

---

**Happy Balancing!** 🤖⚖️
