"""
Sensor Module

Provides interfaces for reading temperature and pressure sensors.
"""

from enum import Enum
from typing import Optional, List
import logging
from datetime import datetime


class SensorState(Enum):
    """Sensor operational states"""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    DISCONNECTED = "disconnected"
    CALIBRATING = "calibrating"


class TemperatureSensor:
    """
    Temperature sensor interface.
    
    Supports various sensor types (RTD, thermocouple, diode) for
    cryogenic temperature measurements.
    """
    
    def __init__(
        self,
        name: str,
        sensor_type: str,
        plc_address: str,
        min_temp: float = 0.0,
        max_temp: float = 300.0,
        warning_low: Optional[float] = None,
        warning_high: Optional[float] = None
    ):
        """
        Initialize temperature sensor.
        
        Args:
            name: Unique identifier for sensor
            sensor_type: Type of sensor (RTD, thermocouple, diode)
            plc_address: PLC memory address for reading
            min_temp: Minimum valid temperature (K)
            max_temp: Maximum valid temperature (K)
            warning_low: Low temperature warning threshold
            warning_high: High temperature warning threshold
        """
        self.name = name
        self.sensor_type = sensor_type
        self.plc_address = plc_address
        self.min_temp = min_temp
        self.max_temp = max_temp
        self.warning_low = warning_low or min_temp
        self.warning_high = warning_high or max_temp
        
        self._current_value: Optional[float] = None
        self._state = SensorState.DISCONNECTED
        self._history: List[tuple] = []  # (timestamp, value) pairs
        
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.logger.info(f"Initialized temperature sensor: {name} ({sensor_type})")
    
    @property
    def value(self) -> Optional[float]:
        """Get current temperature reading in Kelvin"""
        return self._current_value
    
    @property
    def state(self) -> SensorState:
        """Get current sensor state"""
        return self._state
    
    def read(self) -> Optional[float]:
        """
        Read current temperature from sensor.
        
        Returns:
            Temperature in Kelvin, or None if error
        """
        # TODO: Read from PLC via interface
        # For now, return cached value
        self._validate_reading()
        return self._current_value
    
    def update_value(self, value: float) -> None:
        """
        Update sensor value from PLC.
        
        Args:
            value: New temperature reading in Kelvin
        """
        self._current_value = value
        self._history.append((datetime.now(), value))
        
        # Limit history size
        if len(self._history) > 1000:
            self._history.pop(0)
        
        self._validate_reading()
    
    def _validate_reading(self) -> None:
        """Validate current reading and update sensor state"""
        if self._current_value is None:
            self._state = SensorState.DISCONNECTED
            return
        
        if self._current_value < self.min_temp or self._current_value > self.max_temp:
            self._state = SensorState.ERROR
            self.logger.error(
                f"Sensor {self.name} reading out of range: {self._current_value}K "
                f"(valid range: {self.min_temp}-{self.max_temp}K)"
            )
        elif self._current_value < self.warning_low or self._current_value > self.warning_high:
            self._state = SensorState.WARNING
            self.logger.warning(
                f"Sensor {self.name} reading in warning range: {self._current_value}K"
            )
        else:
            self._state = SensorState.OK
    
    def get_history(self, num_points: int = 100) -> List[tuple]:
        """
        Get recent temperature history.
        
        Args:
            num_points: Number of recent points to return
            
        Returns:
            List of (timestamp, temperature) tuples
        """
        return self._history[-num_points:]
    
    def get_status(self) -> dict:
        """
        Get sensor status.
        
        Returns:
            Dictionary with sensor status information
        """
        return {
            "name": self.name,
            "type": self.sensor_type,
            "state": self._state.value,
            "current_value": self._current_value,
            "unit": "K",
            "min_temp": self.min_temp,
            "max_temp": self.max_temp,
            "warning_low": self.warning_low,
            "warning_high": self.warning_high,
            "plc_address": self.plc_address
        }


class PressureSensor:
    """
    Pressure sensor interface.
    
    Supports various pressure gauges for vacuum and gas pressure monitoring.
    """
    
    def __init__(
        self,
        name: str,
        sensor_type: str,
        plc_address: str,
        min_pressure: float = 1e-8,
        max_pressure: float = 1e5,
        warning_high: Optional[float] = None
    ):
        """
        Initialize pressure sensor.
        
        Args:
            name: Unique identifier for sensor
            sensor_type: Type of sensor (Pirani, ion gauge, capacitance manometer)
            plc_address: PLC memory address for reading
            min_pressure: Minimum valid pressure (mbar)
            max_pressure: Maximum valid pressure (mbar)
            warning_high: High pressure warning threshold
        """
        self.name = name
        self.sensor_type = sensor_type
        self.plc_address = plc_address
        self.min_pressure = min_pressure
        self.max_pressure = max_pressure
        self.warning_high = warning_high or max_pressure * 0.9
        
        self._current_value: Optional[float] = None
        self._state = SensorState.DISCONNECTED
        self._history: List[tuple] = []
        
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.logger.info(f"Initialized pressure sensor: {name} ({sensor_type})")
    
    @property
    def value(self) -> Optional[float]:
        """Get current pressure reading in mbar"""
        return self._current_value
    
    @property
    def state(self) -> SensorState:
        """Get current sensor state"""
        return self._state
    
    def read(self) -> Optional[float]:
        """
        Read current pressure from sensor.
        
        Returns:
            Pressure in mbar, or None if error
        """
        # TODO: Read from PLC via interface
        self._validate_reading()
        return self._current_value
    
    def update_value(self, value: float) -> None:
        """
        Update sensor value from PLC.
        
        Args:
            value: New pressure reading in mbar
        """
        self._current_value = value
        self._history.append((datetime.now(), value))
        
        if len(self._history) > 1000:
            self._history.pop(0)
        
        self._validate_reading()
    
    def _validate_reading(self) -> None:
        """Validate current reading and update sensor state"""
        if self._current_value is None:
            self._state = SensorState.DISCONNECTED
            return
        
        if self._current_value < self.min_pressure or self._current_value > self.max_pressure:
            self._state = SensorState.ERROR
            self.logger.error(
                f"Sensor {self.name} reading out of range: {self._current_value} mbar"
            )
        elif self._current_value > self.warning_high:
            self._state = SensorState.WARNING
            self.logger.warning(
                f"Sensor {self.name} high pressure warning: {self._current_value} mbar"
            )
        else:
            self._state = SensorState.OK
    
    def get_status(self) -> dict:
        """
        Get sensor status.
        
        Returns:
            Dictionary with sensor status information
        """
        return {
            "name": self.name,
            "type": self.sensor_type,
            "state": self._state.value,
            "current_value": self._current_value,
            "unit": "mbar",
            "min_pressure": self.min_pressure,
            "max_pressure": self.max_pressure,
            "warning_high": self.warning_high,
            "plc_address": self.plc_address
        }
