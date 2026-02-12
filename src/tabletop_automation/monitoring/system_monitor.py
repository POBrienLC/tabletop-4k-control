"""
System Monitor Module

High-level system monitoring for automated processes.
Aggregates data from hardware sensors and provides system-wide status.
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime
import threading
import time


class SystemStatus:
    """Container for system status information"""
    
    def __init__(self):
        self.timestamp = datetime.now()
        self.temperatures: Dict[str, float] = {}
        self.pressures: Dict[str, float] = {}
        self.valve_states: Dict[str, str] = {}
        self.cooler_state: Optional[str] = None
        self.vacuum_ok: bool = False
        self.cooling_power: Optional[float] = None
        self.safety_status: str = "unknown"
        
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "temperatures": self.temperatures,
            "pressures": self.pressures,
            "valve_states": self.valve_states,
            "cooler_state": self.cooler_state,
            "vacuum_ok": self.vacuum_ok,
            "cooling_power": self.cooling_power,
            "safety_status": self.safety_status
        }


class SystemMonitor:
    """
    System-wide monitoring.
    
    Aggregates data from all hardware components and provides
    a unified view of system status. Runs periodic updates.
    """
    
    def __init__(self, update_interval: float = 1.0):
        """
        Initialize system monitor.
        
        Args:
            update_interval: Interval between updates in seconds
        """
        self.update_interval = update_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        self._current_status = SystemStatus()
        self._status_history: List[SystemStatus] = []
        
        # Component references (to be set externally)
        self.temperature_sensors: Dict[str, any] = {}
        self.pressure_sensors: Dict[str, any] = {}
        self.valves: Dict[str, any] = {}
        self.cooler: Optional[any] = None
        self.safety_monitor: Optional[any] = None
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("System monitor initialized")
    
    def start(self) -> None:
        """Start periodic monitoring"""
        if self._running:
            self.logger.warning("Monitor already running")
            return
        
        self.logger.info("Starting system monitor")
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop monitoring"""
        if not self._running:
            return
        
        self.logger.info("Stopping system monitor")
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self._running:
            try:
                self.update()
                time.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
    
    def update(self) -> SystemStatus:
        """
        Update system status from all components.
        
        Returns:
            Current system status
        """
        status = SystemStatus()
        
        # Update temperatures
        for name, sensor in self.temperature_sensors.items():
            try:
                value = sensor.read()
                if value is not None:
                    status.temperatures[name] = value
            except Exception as e:
                self.logger.error(f"Error reading temperature sensor {name}: {e}")
        
        # Update pressures
        for name, sensor in self.pressure_sensors.items():
            try:
                value = sensor.read()
                if value is not None:
                    status.pressures[name] = value
            except Exception as e:
                self.logger.error(f"Error reading pressure sensor {name}: {e}")
        
        # Update valve states
        for name, valve in self.valves.items():
            try:
                status.valve_states[name] = valve.state.value
            except Exception as e:
                self.logger.error(f"Error reading valve {name}: {e}")
        
        # Update cooler state
        if self.cooler:
            try:
                status.cooler_state = self.cooler.state.value
            except Exception as e:
                self.logger.error(f"Error reading cooler state: {e}")
        
        # Check vacuum status
        if "vacuum" in status.pressures:
            status.vacuum_ok = status.pressures["vacuum"] < 1e-3
        
        # Update safety status
        if self.safety_monitor:
            try:
                safety_status = self.safety_monitor.get_status()
                if safety_status["has_critical_events"]:
                    status.safety_status = "critical"
                elif safety_status["has_alarms"]:
                    status.safety_status = "alarm"
                elif safety_status["interlock_count"] > 0:
                    status.safety_status = "warning"
                else:
                    status.safety_status = "ok"
            except Exception as e:
                self.logger.error(f"Error reading safety status: {e}")
        
        # Store status
        self._current_status = status
        self._status_history.append(status)
        
        # Limit history size
        if len(self._status_history) > 1000:
            self._status_history.pop(0)
        
        return status
    
    @property
    def current_status(self) -> SystemStatus:
        """Get current system status"""
        return self._current_status
    
    def get_status_history(self, count: int = 100) -> List[SystemStatus]:
        """
        Get recent status history.
        
        Args:
            count: Number of recent statuses to return
            
        Returns:
            List of recent system statuses
        """
        return self._status_history[-count:]
    
    def get_temperature(self, sensor_name: str) -> Optional[float]:
        """
        Get current temperature from a specific sensor.
        
        Args:
            sensor_name: Name of temperature sensor
            
        Returns:
            Temperature in K, or None if not available
        """
        return self._current_status.temperatures.get(sensor_name)
    
    def get_pressure(self, sensor_name: str) -> Optional[float]:
        """
        Get current pressure from a specific sensor.
        
        Args:
            sensor_name: Name of pressure sensor
            
        Returns:
            Pressure in mbar, or None if not available
        """
        return self._current_status.pressures.get(sensor_name)
    
    def is_system_healthy(self) -> bool:
        """
        Check if system is in healthy state.
        
        Returns:
            True if system is healthy
        """
        status = self._current_status
        
        # Check safety status
        if status.safety_status in ["critical", "alarm"]:
            return False
        
        # Check for required sensors
        if not status.temperatures or not status.pressures:
            return False
        
        return True
    
    def get_summary(self) -> dict:
        """
        Get system summary.
        
        Returns:
            Dictionary with system summary
        """
        status = self._current_status
        
        return {
            "timestamp": status.timestamp.isoformat(),
            "healthy": self.is_system_healthy(),
            "temperature_count": len(status.temperatures),
            "pressure_count": len(status.pressures),
            "valve_count": len(status.valve_states),
            "cooler_state": status.cooler_state,
            "vacuum_ok": status.vacuum_ok,
            "safety_status": status.safety_status,
            "monitoring_active": self._running
        }
