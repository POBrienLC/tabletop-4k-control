"""
Safety Monitor Module

Monitors system parameters and enforces safety interlocks.
Triggers alarms and emergency shutdowns when necessary.
"""

from enum import Enum
from typing import Dict, List, Callable, Optional
import logging
from datetime import datetime


class SafetyLevel(Enum):
    """Safety alarm levels"""
    OK = "ok"
    INFO = "info"
    WARNING = "warning"
    ALARM = "alarm"
    CRITICAL = "critical"


class SafetyEvent:
    """Represents a safety-related event"""
    
    def __init__(
        self,
        level: SafetyLevel,
        message: str,
        source: str,
        timestamp: Optional[datetime] = None
    ):
        self.level = level
        self.message = message
        self.source = source
        self.timestamp = timestamp or datetime.now()
        self.acknowledged = False
    
    def __str__(self) -> str:
        return f"[{self.level.value.upper()}] {self.timestamp.isoformat()}: {self.message} (from {self.source})"


class SafetyMonitor:
    """
    Central safety monitoring system.
    
    Monitors all critical parameters and enforces safety interlocks.
    Can trigger emergency shutdown procedures.
    """
    
    def __init__(self):
        """Initialize safety monitor"""
        self._events: List[SafetyEvent] = []
        self._interlocks: Dict[str, bool] = {}
        self._callbacks: Dict[SafetyLevel, List[Callable]] = {
            level: [] for level in SafetyLevel
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Safety monitor initialized")
    
    def add_event(self, level: SafetyLevel, message: str, source: str) -> None:
        """
        Add a safety event.
        
        Args:
            level: Severity level of event
            message: Description of event
            source: Source component that generated event
        """
        event = SafetyEvent(level, message, source)
        self._events.append(event)
        
        # Log based on severity
        log_message = str(event)
        if level == SafetyLevel.CRITICAL:
            self.logger.critical(log_message)
        elif level == SafetyLevel.ALARM:
            self.logger.error(log_message)
        elif level == SafetyLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Trigger callbacks
        for callback in self._callbacks.get(level, []):
            try:
                callback(event)
            except Exception as e:
                self.logger.error(f"Error in safety callback: {e}")
        
        # Trigger emergency shutdown for critical events
        if level == SafetyLevel.CRITICAL:
            self._trigger_emergency_shutdown(message)
    
    def register_callback(self, level: SafetyLevel, callback: Callable) -> None:
        """
        Register a callback for safety events of specific level.
        
        Args:
            level: Safety level to monitor
            callback: Function to call when event occurs
        """
        self._callbacks[level].append(callback)
        self.logger.info(f"Registered callback for {level.value} events")
    
    def set_interlock(self, name: str, active: bool) -> None:
        """
        Set state of a safety interlock.
        
        Args:
            name: Interlock identifier
            active: True if interlock is active (blocking operations)
        """
        self._interlocks[name] = active
        if active:
            self.add_event(
                SafetyLevel.WARNING,
                f"Interlock activated: {name}",
                "SafetyMonitor"
            )
        else:
            self.add_event(
                SafetyLevel.INFO,
                f"Interlock cleared: {name}",
                "SafetyMonitor"
            )
    
    def check_interlock(self, name: str) -> bool:
        """
        Check if an interlock is active.
        
        Args:
            name: Interlock identifier
            
        Returns:
            True if interlock is active
        """
        return self._interlocks.get(name, False)
    
    def get_active_interlocks(self) -> List[str]:
        """
        Get list of all active interlocks.
        
        Returns:
            List of interlock names
        """
        return [name for name, active in self._interlocks.items() if active]
    
    def check_temperature_limits(
        self,
        sensor_name: str,
        temperature: float,
        min_temp: float,
        max_temp: float
    ) -> bool:
        """
        Check if temperature is within safe limits.
        
        Args:
            sensor_name: Name of temperature sensor
            temperature: Current temperature reading
            min_temp: Minimum safe temperature
            max_temp: Maximum safe temperature
            
        Returns:
            True if temperature is safe
        """
        if temperature < min_temp:
            self.add_event(
                SafetyLevel.ALARM,
                f"Temperature too low: {sensor_name} = {temperature}K (min: {min_temp}K)",
                sensor_name
            )
            return False
        
        if temperature > max_temp:
            self.add_event(
                SafetyLevel.ALARM,
                f"Temperature too high: {sensor_name} = {temperature}K (max: {max_temp}K)",
                sensor_name
            )
            return False
        
        return True
    
    def check_pressure_limits(
        self,
        sensor_name: str,
        pressure: float,
        max_pressure: float
    ) -> bool:
        """
        Check if pressure is within safe limits.
        
        Args:
            sensor_name: Name of pressure sensor
            pressure: Current pressure reading
            max_pressure: Maximum safe pressure
            
        Returns:
            True if pressure is safe
        """
        if pressure > max_pressure:
            self.add_event(
                SafetyLevel.CRITICAL,
                f"Pressure too high: {sensor_name} = {pressure} mbar (max: {max_pressure} mbar)",
                sensor_name
            )
            return False
        
        return True
    
    def _trigger_emergency_shutdown(self, reason: str) -> None:
        """
        Trigger emergency shutdown procedure.
        
        Args:
            reason: Reason for emergency shutdown
        """
        self.logger.critical(f"EMERGENCY SHUTDOWN TRIGGERED: {reason}")
        # TODO: Implement actual emergency shutdown logic
        # - Close critical valves
        # - Stop cooler
        # - Activate alarms
        # - Notify operators
    
    def get_recent_events(self, count: int = 100, min_level: SafetyLevel = SafetyLevel.INFO) -> List[SafetyEvent]:
        """
        Get recent safety events.
        
        Args:
            count: Maximum number of events to return
            min_level: Minimum severity level to include
            
        Returns:
            List of recent events
        """
        # Filter by level and get most recent
        level_values = [SafetyLevel.INFO, SafetyLevel.WARNING, SafetyLevel.ALARM, SafetyLevel.CRITICAL]
        min_level_index = level_values.index(min_level)
        
        filtered_events = [
            event for event in self._events
            if level_values.index(event.level) >= min_level_index
        ]
        
        return filtered_events[-count:]
    
    def acknowledge_event(self, event: SafetyEvent) -> None:
        """
        Acknowledge a safety event.
        
        Args:
            event: Event to acknowledge
        """
        event.acknowledged = True
        self.logger.info(f"Event acknowledged: {event}")
    
    def get_status(self) -> dict:
        """
        Get safety monitor status.
        
        Returns:
            Dictionary with safety status
        """
        recent_events = self.get_recent_events(10)
        active_interlocks = self.get_active_interlocks()
        
        return {
            "total_events": len(self._events),
            "recent_events": [str(e) for e in recent_events],
            "active_interlocks": active_interlocks,
            "interlock_count": len(active_interlocks),
            "has_critical_events": any(e.level == SafetyLevel.CRITICAL for e in recent_events),
            "has_alarms": any(e.level == SafetyLevel.ALARM for e in recent_events)
        }
