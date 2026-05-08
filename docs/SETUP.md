# Setup Guide

## Prerequisites

- Raspberry Pi 4 (2GB+ RAM)
- Raspberry Pi OS (Bullseye or later)
- Python 3.8+
- pip3 package manager
- ArduRover already installed and running

## Installation Steps

### 1. Clone Repository

```bash
cd ~
git clone https://github.com/arhaan2010/self-balancing-bot.git
cd self-balancing-bot
```

### 2. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev
sudo apt-get install -y python3-rpi.gpio
sudo apt-get install -y i2c-tools
```

### 3. Install pigpio (for PWM control)

```bash
wget https://github.com/joan2937/pigpio/archive/master.zip
unzip master.zip
cd pigpio-master
make
sudo make install
sudo systemctl start pigpiod
sudo systemctl enable pigpiod
```

### 4. Install Python Dependencies

```bash
sudo pip3 install -r requirements.txt
```

### 5. Configure Hardware

Edit the configuration files:

- `config/pixhawk_config.yaml` - Pixhawk connection settings
- `config/esc_config.yaml` - ESC GPIO pin settings
- `config/pid_params.yaml` - PID tuning parameters

See [HARDWARE_SETUP.md](HARDWARE_SETUP.md) for detailed configuration.

### 6. Verify Installation

```bash
# Test Pixhawk connection
python3 src/main.py --test-imu

# Test ESC (without propellers!)
python3 src/main.py --test-esc
```

### 7. Run Calibration

```bash
python3 src/main.py --calibrate
```

See [CALIBRATION.md](CALIBRATION.md) for detailed steps.

## Running the Self-Balancing Bot

```bash
python3 src/main.py
```

## Options

```bash
# Show system status
python3 src/main.py --status

# Run for a specific duration (seconds)
python3 src/main.py --duration 30

# Test IMU only
python3 src/main.py --test-imu

# Test ESC only (without propellers!)
python3 src/main.py --test-esc

# Run calibration
python3 src/main.py --calibrate
```

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.
