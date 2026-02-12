# Tabletop 4K Cryostat Control System

PLC and Python control stack for the Tabletop 4K cryostat, including automation, safety interlocks, and comprehensive documentation.

## Overview

This project provides a complete control system for a tabletop 4K cryostat with GM (Gifford-McMahon) cooler. The system is built with a state machine architecture and includes two main Python packages:

1. **`tabletop_hardware`**: Low-level hardware control for individual components (valves, sensors, cooler)
2. **`tabletop_automation`**: High-level automation for automated processes (cooldown, warmup, monitoring)

Both packages include built-in safety interlocks and comprehensive monitoring.

## Key Features

- **State Machine Architecture**: Both hardware and process-level state machines
- **Safety First**: Multi-layer safety with hardware and process-level interlocks
- **PLC Integration**: Siemens S7 PLC communication via SNAP7
- **Automated Processes**: Cooldown and warmup with staged progression
- **Real-time Monitoring**: System-wide monitoring with alarm management
- **Configuration-Based**: All parameters in YAML config files
- **Comprehensive Documentation**: Architecture, API, and safety procedures

## Project Structure

```
tabletop-4k-control/
├── src/
│   ├── tabletop_hardware/          # Hardware control package
│   │   ├── components/             # Individual hardware components
│   │   │   ├── valve.py           # Valve control
│   │   │   ├── sensor.py          # Temperature & pressure sensors
│   │   │   └── cooler.py          # GM cooler control
│   │   ├── interfaces/            # Communication interfaces
│   │   │   └── plc_interface.py   # Siemens PLC interface
│   │   ├── safety/                # Hardware safety
│   │   │   └── safety_monitor.py  # Safety monitoring & alarms
│   │   └── state_machine/         # Hardware state machine
│   │       └── hardware_state.py  # State machine implementation
│   │
│   └── tabletop_automation/        # Automation package
│       ├── processes/              # Automated processes
│       │   ├── cooldown.py        # Automated cooldown
│       │   └── warmup.py          # Automated warmup
│       ├── monitoring/            # System monitoring
│       │   └── system_monitor.py  # System-wide monitoring
│       ├── safety/                # Process safety
│       │   └── automation_safety.py # Process safety checks
│       └── state_machine/         # Process state machine
│           └── process_state.py   # Process state machine
│
├── config/                         # Configuration files
│   ├── system_config.yaml         # Main system config
│   ├── safety_limits.yaml         # Safety limits & interlocks
│   └── plc_config.yaml            # PLC communication config
│
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md            # System architecture
│   └── SAFETY_PROCEDURES.md       # Safety procedures
│
├── examples/                      # Example scripts
│   ├── basic_hardware_control.py  # Hardware control example
│   └── automated_cooldown.py      # Automated process example
│
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   └── integration/               # Integration tests
│
├── pyproject.toml                 # Project configuration
├── requirements.txt               # Dependencies
└── requirements-dev.txt           # Development dependencies
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Siemens PLC (S7-1200/1500 or compatible)
- python-snap7 library for PLC communication

### Install from source

```bash
git clone https://github.com/POBrienLC/tabletop-4k-control.git
cd tabletop-4k-control
pip install -e .
```

### Install development dependencies

```bash
pip install -r requirements-dev.txt
```

## Quick Start

### Basic Hardware Control

```python
from tabletop_hardware import PLCInterface, Valve, ValveType, TemperatureSensor

# Connect to PLC
plc = PLCInterface(plc_ip="192.168.1.100")
plc.connect()

# Create valve instance
valve = Valve(
    name="Isolation Valve",
    valve_type=ValveType.ISOLATION,
    plc_address="DB1.DBX0.0"
)

# Open valve (with safety checks)
valve.open()

# Read temperature
temp_sensor = TemperatureSensor(
    name="Sample",
    sensor_type="RTD",
    plc_address="DB2.DBD0"
)
temperature = temp_sensor.read()
print(f"Temperature: {temperature}K")
```

### Automated Cooldown

```python
from tabletop_automation import CooldownProcess, SystemMonitor, AutomationSafety

# Initialize components
cooldown = CooldownProcess()
monitor = SystemMonitor()
safety = AutomationSafety()

# Start system monitoring
monitor.start()

# Check safety before starting
is_safe, reason = safety.check_cooldown_safe(current_temp, current_pressure, target_temp)

if is_safe:
    # Start automated cooldown
    cooldown.start()
    
    # Monitor progress
    while cooldown.is_running:
        status = cooldown.get_status()
        print(f"Stage: {status['stage']}, Progress: {status['progress']*100}%")
```

## Configuration

Edit configuration files in the `config/` directory:

- **`system_config.yaml`**: System parameters, sensor definitions, valve configuration
- **`safety_limits.yaml`**: Temperature/pressure limits, interlock conditions
- **`plc_config.yaml`**: PLC connection settings and memory mapping

## Safety

The system implements multi-layer safety:

1. **Hardware Safety**: Individual component interlocks
2. **Process Safety**: Automated process validation
3. **Configuration Limits**: Temperature, pressure, and rate limits
4. **Emergency Shutdown**: Automatic emergency stop on critical conditions

See [Safety Procedures](docs/SAFETY_PROCEDURES.md) for detailed information.

## Documentation

- [Architecture](docs/ARCHITECTURE.md): System architecture and design
- [Safety Procedures](docs/SAFETY_PROCEDURES.md): Safety protocols and procedures

## Examples

Example scripts are provided in the `examples/` directory:

- `basic_hardware_control.py`: Basic hardware component control
- `automated_cooldown.py`: Automated cooldown sequence

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_valve.py
```

## Development

### Code Style

The project uses:
- **black** for code formatting
- **flake8** for linting
- **mypy** for type checking

```bash
black src/
flake8 src/
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License

## Authors

- Tabletop 4K Team

## Contact

For questions or support, please open an issue on GitHub.
