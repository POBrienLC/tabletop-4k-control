#!/usr/bin/env python3
"""
Basic Hardware Control Example

Demonstrates basic control of hardware components:
- Connecting to PLC
- Reading sensors
- Operating valves
- Starting cooler
"""

import logging
import time
from tabletop_hardware import (
    PLCInterface,
    Valve, ValveType,
    TemperatureSensor, PressureSensor,
    GMCooler,
    SafetyMonitor,
    HardwareStateMachine, HardwareState
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main example function"""
    
    # Initialize PLC interface
    print("Connecting to PLC...")
    plc = PLCInterface(plc_ip="192.168.1.100", rack=0, slot=1)
    
    if not plc.connect():
        print("Failed to connect to PLC")
        return
    
    print("Connected to PLC")
    
    # Initialize safety monitor
    safety = SafetyMonitor()
    
    # Initialize state machine
    state_machine = HardwareStateMachine()
    
    # Initialize components
    print("\nInitializing hardware components...")
    
    # Valves
    isolation_valve = Valve(
        name="Isolation",
        valve_type=ValveType.ISOLATION,
        plc_address="DB1.DBX0.0"
    )
    
    needle_valve = Valve(
        name="Needle",
        valve_type=ValveType.NEEDLE,
        plc_address="DB1.DBX0.1"
    )
    
    # Sensors
    temp_sensor = TemperatureSensor(
        name="Stage 1",
        sensor_type="RTD",
        plc_address="DB2.DBD0",
        min_temp=0.0,
        max_temp=400.0
    )
    
    pressure_sensor = PressureSensor(
        name="Vacuum",
        sensor_type="Ion Gauge",
        plc_address="DB2.DBD12",
        min_pressure=1e-8,
        max_pressure=1.0
    )
    
    # Cooler
    cooler = GMCooler(
        name="GM Cooler",
        plc_address="DB3.DBX0.0"
    )
    
    # Transition to initialized state
    state_machine.transition_to(HardwareState.INITIALIZED)
    state_machine.transition_to(HardwareState.IDLE)
    
    print("Hardware initialized")
    
    # Read sensor values
    print("\n--- Reading Sensors ---")
    
    # In real operation, values would come from PLC
    # For demonstration, we'll update with dummy values
    temp_sensor.update_value(295.0)  # Room temperature
    pressure_sensor.update_value(1e-4)  # Good vacuum
    
    print(f"Temperature: {temp_sensor.value}K")
    print(f"Pressure: {pressure_sensor.value} mbar")
    print(f"Temp sensor state: {temp_sensor.state.value}")
    print(f"Pressure sensor state: {pressure_sensor.state.value}")
    
    # Check safety
    print("\n--- Safety Checks ---")
    is_safe = safety.check_temperature_limits(
        "Stage 1",
        temp_sensor.value,
        0.0,
        400.0
    )
    print(f"Temperature within safe limits: {is_safe}")
    
    is_safe = safety.check_pressure_limits(
        "Vacuum",
        pressure_sensor.value,
        1e-2
    )
    print(f"Pressure within safe limits: {is_safe}")
    
    # Operate valves
    print("\n--- Valve Operations ---")
    
    print("Opening isolation valve...")
    if isolation_valve.open():
        isolation_valve.update_state(ValveState.OPEN)
        print(f"Isolation valve state: {isolation_valve.state.value}")
    
    time.sleep(1)
    
    print("Opening needle valve...")
    if needle_valve.open():
        needle_valve.update_state(ValveState.OPEN)
        print(f"Needle valve state: {needle_valve.state.value}")
    
    # Get component status
    print("\n--- Component Status ---")
    print("Isolation Valve:", isolation_valve.get_status())
    print("Temperature Sensor:", temp_sensor.get_status())
    print("Cooler:", cooler.get_status())
    
    # State machine status
    print("\n--- State Machine Status ---")
    print(state_machine.get_status())
    
    # Safety status
    print("\n--- Safety Status ---")
    print(safety.get_status())
    
    # Close valves before exit
    print("\n--- Closing Valves ---")
    needle_valve.close()
    isolation_valve.close()
    
    # Disconnect PLC
    print("\nDisconnecting from PLC...")
    plc.disconnect()
    print("Disconnected")

if __name__ == "__main__":
    main()
