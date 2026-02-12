#!/usr/bin/env python3
"""
Automated Cooldown Example

Demonstrates automated cooldown process:
- System initialization
- Pre-cooldown checks
- Automated cooldown sequence
- Monitoring and safety
"""

import logging
import time
from tabletop_hardware import (
    PLCInterface,
    SafetyMonitor,
    HardwareStateMachine,
    TemperatureSensor,
    PressureSensor,
    GMCooler
)
from tabletop_automation import (
    CooldownProcess,
    SystemMonitor,
    AutomationSafety,
    ProcessStateMachine,
    ProcessState
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main example function"""
    
    print("=== Automated Cooldown Example ===\n")
    
    # Initialize hardware layer
    print("Initializing hardware...")
    plc = PLCInterface(plc_ip="192.168.1.100")
    plc.connect()
    
    hardware_safety = SafetyMonitor()
    hardware_state = HardwareStateMachine()
    
    # Initialize sensors
    temp_sensor = TemperatureSensor(
        name="Sample",
        sensor_type="Diode",
        plc_address="DB2.DBD8"
    )
    
    vacuum_sensor = PressureSensor(
        name="Vacuum",
        sensor_type="Ion Gauge",
        plc_address="DB2.DBD12"
    )
    
    cooler = GMCooler(
        name="GM Cooler",
        plc_address="DB3.DBX0.0"
    )
    
    # Initialize automation layer
    print("Initializing automation...")
    system_monitor = SystemMonitor(update_interval=1.0)
    automation_safety = AutomationSafety()
    automation_safety.hardware_safety = hardware_safety
    process_state = ProcessStateMachine()
    
    # Setup system monitor with components
    system_monitor.temperature_sensors = {"sample": temp_sensor}
    system_monitor.pressure_sensors = {"vacuum": vacuum_sensor}
    system_monitor.cooler = cooler
    system_monitor.safety_monitor = hardware_safety
    
    # Start monitoring
    system_monitor.start()
    
    # Initialize cooldown process
    cooldown = CooldownProcess()
    
    # Register callbacks for stage transitions
    def on_vacuum_pump():
        print("Stage: Vacuum pumping started")
    
    def on_cooler_start():
        print("Stage: Starting GM cooler")
        cooler.start()
    
    def on_complete():
        print("Stage: Cooldown complete!")
    
    cooldown.register_stage_callback(CooldownStage.VACUUM_PUMP, on_vacuum_pump)
    cooldown.register_stage_callback(CooldownStage.START_COOLER, on_cooler_start)
    cooldown.register_stage_callback(CooldownStage.COMPLETE, on_complete)
    
    # Transition to ready state
    process_state.transition_to(ProcessState.INITIALIZING)
    process_state.transition_to(ProcessState.READY)
    
    # Pre-cooldown checks
    print("\n--- Pre-Cooldown Checks ---")
    
    # Simulate current conditions
    current_temp = 295.0  # Room temperature
    current_pressure = 5e-4  # Good vacuum
    
    temp_sensor.update_value(current_temp)
    vacuum_sensor.update_value(current_pressure)
    
    print(f"Current temperature: {current_temp}K")
    print(f"Current pressure: {current_pressure} mbar")
    
    # Check if cooldown is safe
    is_safe, reason = automation_safety.check_cooldown_safe(
        current_temp,
        current_pressure,
        4.0  # Target temperature
    )
    
    if not is_safe:
        print(f"ERROR: Cannot start cooldown - {reason}")
        return
    
    print("Pre-cooldown checks passed")
    
    # Start cooldown
    print("\n--- Starting Cooldown ---")
    process_state.transition_to(ProcessState.COOLDOWN)
    
    if not cooldown.start():
        print("Failed to start cooldown")
        return
    
    print("Cooldown started")
    
    # Simulate cooldown process
    print("\n--- Cooldown Progress ---")
    
    # In real operation, this would run continuously
    # For demonstration, we'll simulate a few iterations
    simulation_temps = [295.0, 250.0, 200.0, 150.0, 100.0, 77.0, 50.0, 20.0, 10.0, 4.0]
    
    for temp in simulation_temps:
        # Update temperature
        temp_sensor.update_value(temp)
        current_temp = temp
        
        # Update cooldown process
        cooldown.update(current_temp, current_pressure)
        
        # Display progress
        status = cooldown.get_status()
        progress = status['progress'] * 100
        
        print(f"Temperature: {current_temp:6.1f}K | "
              f"Stage: {status['stage']:20s} | "
              f"Progress: {progress:5.1f}%")
        
        # Safety check
        if status['stage'] == 'error':
            print("ERROR: Cooldown encountered error")
            break
        
        if status['stage'] == 'complete':
            print("\nCooldown completed successfully!")
            break
        
        time.sleep(0.5)  # Simulate time passing
    
    # Final status
    print("\n--- Final Status ---")
    print(f"Process State: {process_state.current_state.value}")
    print(f"Cooldown Stage: {cooldown.stage.value}")
    print(f"System Status: {system_monitor.get_summary()}")
    
    # Cleanup
    print("\n--- Cleanup ---")
    process_state.transition_to(ProcessState.OPERATING)
    system_monitor.stop()
    plc.disconnect()
    print("Complete")

if __name__ == "__main__":
    # Need to import these after defining main
    from tabletop_hardware.components.valve import ValveState
    from tabletop_automation.processes.cooldown import CooldownStage
    main()
