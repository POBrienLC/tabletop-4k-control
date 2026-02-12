# API Documentation

## Hardware Package (`tabletop_hardware`)

### Components

#### Valve

```python
from tabletop_hardware import Valve, ValveType, ValveState

valve = Valve(
    name="Isolation Valve",
    valve_type=ValveType.ISOLATION,
    plc_address="DB1.DBX0.0",
    normally_closed=True,
    interlock_enabled=True
)

# Open valve
valve.open()  # Returns True if successful

# Close valve
valve.close()  # Returns True if successful

# Emergency close (bypasses interlocks)
valve.emergency_close()

# Get status
status = valve.get_status()
# Returns: {name, type, state, target_state, normally_closed, interlock_enabled, plc_address}

# Check state
if valve.state == ValveState.OPEN:
    print("Valve is open")
```

**Valve Types**:
- `ISOLATION`: Isolation valve
- `NEEDLE`: Needle valve (fine control)
- `RELIEF`: Relief/safety valve
- `BYPASS`: Bypass valve

**Valve States**:
- `OPEN`: Valve is open
- `CLOSED`: Valve is closed
- `OPENING`: Valve is opening
- `CLOSING`: Valve is closing
- `ERROR`: Error state
- `UNKNOWN`: State unknown

#### Temperature Sensor

```python
from tabletop_hardware import TemperatureSensor

sensor = TemperatureSensor(
    name="Sample",
    sensor_type="RTD",
    plc_address="DB2.DBD0",
    min_temp=0.0,
    max_temp=400.0,
    warning_low=10.0,
    warning_high=350.0
)

# Read temperature
temperature = sensor.read()  # Returns temperature in Kelvin

# Update from PLC
sensor.update_value(295.0)

# Get current value
current_temp = sensor.value

# Check sensor state
if sensor.state == SensorState.OK:
    print("Sensor operating normally")

# Get history
history = sensor.get_history(100)  # Get last 100 readings

# Get status
status = sensor.get_status()
```

#### Pressure Sensor

```python
from tabletop_hardware import PressureSensor

sensor = PressureSensor(
    name="Vacuum",
    sensor_type="Ion Gauge",
    plc_address="DB2.DBD12",
    min_pressure=1e-8,
    max_pressure=1.0,
    warning_high=1e-3
)

# Read pressure
pressure = sensor.read()  # Returns pressure in mbar

# Similar API to TemperatureSensor
```

#### GM Cooler

```python
from tabletop_hardware.components.cooler import GMCooler

cooler = GMCooler(
    name="GM Cooler",
    plc_address="DB3.DBX0.0",
    max_runtime_hours=10000.0
)

# Start cooler
cooler.start()  # Returns True if successful

# Stop cooler
cooler.stop()

# Emergency stop
cooler.emergency_stop()

# Update runtime
cooler.update_runtime(5432.1)  # hours

# Get status
status = cooler.get_status()
```

### Interfaces

#### PLC Interface

```python
from tabletop_hardware import PLCInterface

plc = PLCInterface(
    plc_ip="192.168.1.100",
    rack=0,
    slot=1,
    auto_reconnect=True
)

# Connect
plc.connect()

# Check connection
if plc.is_connected:
    print("Connected to PLC")

# Read bit
value = plc.read_bit(db_number=1, start_address=0, bit_offset=0)

# Write bit
plc.write_bit(db_number=1, start_address=0, bit_offset=0, value=True)

# Read REAL (float)
value = plc.read_real(db_number=2, start_address=0)

# Write REAL
plc.write_real(db_number=2, start_address=0, value=295.5)

# Get status
status = plc.get_status()

# Disconnect
plc.disconnect()
```

### Safety

#### Safety Monitor

```python
from tabletop_hardware import SafetyMonitor, SafetyLevel

monitor = SafetyMonitor()

# Add event
monitor.add_event(
    level=SafetyLevel.WARNING,
    message="Temperature approaching limit",
    source="TempSensor1"
)

# Register callback
def on_critical(event):
    print(f"CRITICAL: {event.message}")

monitor.register_callback(SafetyLevel.CRITICAL, on_critical)

# Set interlock
monitor.set_interlock("vacuum_low", active=True)

# Check interlock
if monitor.check_interlock("vacuum_low"):
    print("Vacuum low interlock active")

# Check temperature limits
safe = monitor.check_temperature_limits(
    "Sample",
    temperature=295.0,
    min_temp=0.0,
    max_temp=400.0
)

# Check pressure limits
safe = monitor.check_pressure_limits(
    "Vacuum",
    pressure=1e-4,
    max_pressure=1e-2
)

# Get recent events
events = monitor.get_recent_events(count=10, min_level=SafetyLevel.WARNING)

# Get status
status = monitor.get_status()
```

### State Machine

#### Hardware State Machine

```python
from tabletop_hardware import HardwareStateMachine, HardwareState

state_machine = HardwareStateMachine()

# Get current state
current = state_machine.current_state

# Check if transition is valid
can_transition = state_machine.can_transition_to(HardwareState.RUNNING)

# Transition to new state
state_machine.transition_to(HardwareState.RUNNING)

# Emergency transition
state_machine.emergency_transition()

# Get valid transitions
valid_states = state_machine.get_valid_transitions()

# Get state history
history = state_machine.get_state_history(count=10)

# Reset
state_machine.reset()

# Get status
status = state_machine.get_status()
```

## Automation Package (`tabletop_automation`)

### Processes

#### Cooldown Process

```python
from tabletop_automation import CooldownProcess, CooldownStage

cooldown = CooldownProcess()

# Register stage callback
def on_complete():
    print("Cooldown complete!")

cooldown.register_stage_callback(CooldownStage.COMPLETE, on_complete)

# Start cooldown
cooldown.start()

# Update process (call periodically)
cooldown.update(current_temp=295.0, current_pressure=1e-4)

# Pause
cooldown.pause()

# Resume
cooldown.resume()

# Abort
cooldown.abort()

# Check if running
if cooldown.is_running:
    print("Cooldown in progress")

# Get progress
progress = cooldown.get_progress()  # 0.0 to 1.0

# Get status
status = cooldown.get_status()
# Returns: {stage, is_running, is_paused, elapsed_time, progress, abort_requested}
```

**Cooldown Stages**:
- `IDLE`: Not running
- `PRE_COOL_CHECK`: Checking preconditions
- `VACUUM_PUMP`: Pumping down vacuum
- `START_COOLER`: Starting cooler
- `INITIAL_COOLDOWN`: 300K → 77K
- `INTERMEDIATE_COOLDOWN`: 77K → 20K
- `FINAL_COOLDOWN`: 20K → 4K
- `STABILIZATION`: Stabilizing at target
- `COMPLETE`: Cooldown complete
- `ERROR`: Error occurred
- `ABORTED`: Aborted by user

#### Warmup Process

```python
from tabletop_automation import WarmupProcess, WarmupStage

warmup = WarmupProcess()

# Similar API to CooldownProcess
warmup.start()
warmup.update(current_temp=4.0, warmup_rate=5.0)
```

### Monitoring

#### System Monitor

```python
from tabletop_automation import SystemMonitor

monitor = SystemMonitor(update_interval=1.0)

# Set component references
monitor.temperature_sensors = {"sample": temp_sensor}
monitor.pressure_sensors = {"vacuum": pressure_sensor}
monitor.valves = {"isolation": valve}
monitor.cooler = cooler
monitor.safety_monitor = safety_monitor

# Start monitoring
monitor.start()

# Get current status
status = monitor.current_status

# Get temperature from specific sensor
temp = monitor.get_temperature("sample")

# Get pressure from specific sensor
pressure = monitor.get_pressure("vacuum")

# Check system health
if monitor.is_system_healthy():
    print("System OK")

# Get summary
summary = monitor.get_summary()

# Get status history
history = monitor.get_status_history(count=100)

# Stop monitoring
monitor.stop()
```

### Safety

#### Automation Safety

```python
from tabletop_automation import AutomationSafety

safety = AutomationSafety()

# Link to hardware safety
safety.hardware_safety = hardware_safety_monitor

# Check if cooldown is safe
is_safe, reason = safety.check_cooldown_safe(
    current_temp=295.0,
    current_pressure=1e-4,
    target_temp=4.0
)

if not is_safe:
    print(f"Cannot cooldown: {reason}")

# Check if warmup is safe
is_safe, reason = safety.check_warmup_safe(
    current_temp=4.0,
    target_temp=295.0
)

# Check temperature change rate
is_safe, reason = safety.check_rate_safe(
    rate=8.0,  # K/min
    rate_type="cooldown"
)

# Check valve sequence
valve_states = {"isolation": "open", "needle": "closed"}
required_states = {"isolation": "open", "needle": "closed"}
is_safe, reason = safety.check_valve_sequence_safe(valve_states, required_states)

# Enable/disable operations
safety.enable_cooldown()
safety.disable_cooldown()
safety.enable_warmup()
safety.disable_warmup()

# Emergency stop
safety.trigger_emergency_stop()
safety.reset_emergency_stop()

# Get status
status = safety.get_status()
```

### Process State Machine

```python
from tabletop_automation import ProcessStateMachine, ProcessState

state_machine = ProcessStateMachine()

# Similar API to HardwareStateMachine
state_machine.transition_to(ProcessState.READY)

# Check if operational
if state_machine.is_operational():
    print("System operational")

# Check if needs attention
if state_machine.requires_attention():
    print("Operator attention required")

# Get state duration
duration = state_machine.get_state_duration()  # seconds

# Get status
status = state_machine.get_status()
```

**Process States**:
- `OFFLINE`: System offline
- `INITIALIZING`: Initializing
- `READY`: Ready for operation
- `COOLDOWN`: Cooldown in progress
- `OPERATING`: At target temperature
- `WARMUP`: Warmup in progress
- `MAINTENANCE`: Maintenance mode
- `ERROR`: Error state
- `EMERGENCY`: Emergency state

## Configuration

### Loading Configuration

```python
import yaml

# Load system config
with open("config/system_config.yaml") as f:
    config = yaml.safe_load(f)

# Access configuration
plc_ip = config['plc']['ip_address']
sensors = config['temperature_sensors']
```

### Configuration Structure

See example configuration files:
- `config/system_config.yaml`
- `config/safety_limits.yaml`
- `config/plc_config.yaml`

## Error Handling

All methods return appropriate values or raise exceptions:

```python
try:
    valve.open()
except Exception as e:
    print(f"Error opening valve: {e}")
```

Check return values:

```python
if not plc.connect():
    print("Failed to connect to PLC")
```

## Logging

All modules use Python's logging module:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Log levels:
- `DEBUG`: Detailed information
- `INFO`: General information
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical issues

## Best Practices

1. **Always check safety before operations**
   ```python
   is_safe, reason = safety.check_cooldown_safe(...)
   if is_safe:
       cooldown.start()
   ```

2. **Use state machines to track system state**
   ```python
   if state_machine.can_transition_to(target_state):
       state_machine.transition_to(target_state)
   ```

3. **Monitor system continuously**
   ```python
   monitor = SystemMonitor()
   monitor.start()
   # ... system runs ...
   monitor.stop()
   ```

4. **Handle errors gracefully**
   ```python
   try:
       operation()
   except Exception as e:
       logging.error(f"Operation failed: {e}")
       # Trigger safe shutdown
   ```

5. **Use configuration files for parameters**
   - Don't hardcode values in code
   - Use YAML configuration files
   - Load at runtime
