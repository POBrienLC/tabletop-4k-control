# Tabletop 4K Cryostat Control System - Architecture

## Overview

The Tabletop 4K Cryostat Control System is a Python-based control stack for operating a tabletop cryostat with a Gifford-McMahon (GM) cooler. The system interfaces with a Siemens PLC and provides both manual component control and automated process management with comprehensive safety interlocks.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│              (CLI, GUI, or Web Interface)                    │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Automation Package                          │
│            (tabletop_automation)                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Cooldown  │  │   Warmup   │  │  System    │           │
│  │  Process   │  │  Process   │  │  Monitor   │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│  ┌────────────┐  ┌──────────────────────────┐             │
│  │  Process   │  │   Automation Safety      │             │
│  │  State     │  │   Interlocks             │             │
│  │  Machine   │  └──────────────────────────┘             │
│  └────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Hardware Package                            │
│             (tabletop_hardware)                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │   Valves   │  │  Sensors   │  │  Cooler    │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│  ┌────────────┐  ┌──────────────────────────┐             │
│  │  Hardware  │  │   Safety Monitor         │             │
│  │  State     │  │   & Interlocks           │             │
│  │  Machine   │  └──────────────────────────┘             │
│  └────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  PLC Interface Layer                         │
│         (python-snap7 library)                               │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Siemens PLC                               │
│      (S7-1200/1500 or compatible)                           │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                Physical Hardware                             │
│  Valves, Sensors, GM Cooler, Vacuum System                  │
└─────────────────────────────────────────────────────────────┘
```

## Two-Package Design

### Package 1: Hardware Control (`tabletop_hardware`)

**Purpose**: Low-level control of individual hardware components

**Components**:
- **Components**: Individual device control
  - `valve.py`: Valve control with safety interlocks
  - `sensor.py`: Temperature and pressure sensors
  - `cooler.py`: GM cooler control
- **Interfaces**: Communication layers
  - `plc_interface.py`: Siemens PLC communication via SNAP7
- **Safety**: Hardware-level safety
  - `safety_monitor.py`: Real-time safety monitoring and alarms
- **State Machine**: Hardware states
  - `hardware_state.py`: Hardware state machine implementation

**Key Features**:
- Direct hardware control
- Safety interlocks on individual operations
- Real-time sensor reading
- PLC communication management
- Hardware state tracking

### Package 2: Automation Control (`tabletop_automation`)

**Purpose**: High-level automated processes and orchestration

**Components**:
- **Processes**: Automated sequences
  - `cooldown.py`: Automated cooldown to 4K
  - `warmup.py`: Automated warmup to room temperature
- **Monitoring**: System-wide monitoring
  - `system_monitor.py`: Aggregated system status
- **Safety**: Process-level safety
  - `automation_safety.py`: Process safety checks and interlocks
- **State Machine**: Process states
  - `process_state.py`: High-level process state machine

**Key Features**:
- Multi-stage automated processes
- Process safety validation
- System-wide monitoring
- Process state tracking
- Coordination of multiple hardware components

## State Machine Architecture

The system implements a dual state machine approach:

### 1. Hardware State Machine (Low-Level)

States:
- `UNINITIALIZED`: System not yet initialized
- `INITIALIZED`: Hardware initialized
- `IDLE`: Ready for commands
- `STARTING`: Hardware starting up
- `RUNNING`: Hardware in operation
- `STOPPING`: Hardware shutting down
- `ERROR`: Error condition
- `EMERGENCY`: Emergency stop active
- `MAINTENANCE`: Maintenance mode

### 2. Process State Machine (High-Level)

States:
- `OFFLINE`: System offline
- `INITIALIZING`: Initializing system
- `READY`: Ready for automated process
- `COOLDOWN`: Cooldown in progress
- `OPERATING`: At target temperature
- `WARMUP`: Warmup in progress
- `MAINTENANCE`: Maintenance mode
- `ERROR`: Error condition
- `EMERGENCY`: Emergency condition

## Safety System

### Multi-Layer Safety Approach

1. **Hardware Safety Layer**
   - Individual component interlocks
   - Real-time sensor monitoring
   - Immediate hardware shutdowns
   - PLC-level safety (fail-safe)

2. **Automation Safety Layer**
   - Process-level validation
   - Rate limiting (cooldown/warmup rates)
   - Sequence validation
   - Multi-sensor correlation

3. **Configuration-Based Limits**
   - Temperature limits
   - Pressure limits
   - Rate limits
   - Interlock conditions

### Safety Features

- **Emergency Shutdown**: Immediate hardware shutdown on critical conditions
- **Safety Interlocks**: Prevent unsafe operations
- **Rate Limiting**: Prevent too-fast temperature changes
- **Alarm System**: Multiple alarm levels (INFO, WARNING, ALARM, CRITICAL)
- **Watchdog Timer**: Ensures system responsiveness
- **Fail-Safe Design**: Safe state on power loss or communication failure

## Configuration System

All system parameters are configured via YAML files:

- `system_config.yaml`: Main system configuration
- `safety_limits.yaml`: Safety limits and interlock conditions
- `plc_config.yaml`: PLC communication and memory mapping

## Data Flow

1. **Sensor Data**:
   - PLC reads sensors → Hardware components → System monitor → Automation processes

2. **Control Commands**:
   - User/Automation → Hardware state machine → Safety checks → PLC interface → Hardware

3. **Safety Monitoring**:
   - Continuous polling → Safety monitors → Interlock evaluation → Actions (if needed)

## Communication Protocol

### PLC Interface (SNAP7)

- **Protocol**: Siemens S7 protocol
- **Connection**: Ethernet TCP/IP
- **Data Blocks**: Organized by function
  - DB1: Digital I/O (valves)
  - DB2: Analog inputs (sensors)
  - DB3: Cooler control
  - DB10: System status
- **Polling**: Multi-rate polling (fast/normal/slow)
- **Thread Safety**: Lock-based synchronization

## Extensibility

The system is designed for easy extension:

- **Add New Sensors**: Subclass `TemperatureSensor` or `PressureSensor`
- **Add New Processes**: Create new process classes similar to `CooldownProcess`
- **Custom State Transitions**: Extend state machines with new states/transitions
- **Additional Safety Checks**: Add to safety monitor classes

## Development Guidelines

- **Separation of Concerns**: Hardware vs. Automation packages
- **Safety First**: All operations must pass safety checks
- **State-Driven**: Use state machines to manage complexity
- **Configuration-Based**: Parameters in config files, not code
- **Logging**: Comprehensive logging at all levels
- **Testing**: Unit tests for components, integration tests for processes

## Next Steps

1. Implement user interface (CLI/GUI)
2. Add data logging and visualization
3. Implement PID controllers for temperature control
4. Add remote monitoring and alerts
5. Develop comprehensive test suite
