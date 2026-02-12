"""
GM Cooler Control Module

Interface for controlling the Gifford-McMahon (GM) cooler.
"""

from enum import Enum
from typing import Optional
import logging


class CoolerState(Enum):
    """GM Cooler operational states"""
    OFF = "off"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class GMCooler:
    """
    GM Cooler control interface.
    
    Controls the compressor and monitors cooler performance.
    Implements safety interlocks and temperature monitoring.
    """
    
    def __init__(
        self,
        name: str,
        plc_address: str,
        max_runtime_hours: float = 10000.0
    ):
        """
        Initialize GM cooler interface.
        
        Args:
            name: Unique identifier for cooler
            plc_address: Base PLC address for cooler controls
            max_runtime_hours: Maximum runtime before maintenance
        """
        self.name = name
        self.plc_address = plc_address
        self.max_runtime_hours = max_runtime_hours
        
        self._state = CoolerState.OFF
        self._runtime_hours: float = 0.0
        self._compressor_on: bool = False
        
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.logger.info(f"Initialized GM cooler: {name}")
    
    @property
    def state(self) -> CoolerState:
        """Get current cooler state"""
        return self._state
    
    @property
    def runtime_hours(self) -> float:
        """Get total runtime in hours"""
        return self._runtime_hours
    
    def start(self) -> bool:
        """
        Start the GM cooler.
        
        Returns:
            True if start successful
        """
        if self._state == CoolerState.RUNNING:
            self.logger.warning("Cooler already running")
            return True
        
        if not self._check_start_interlocks():
            self.logger.error("Cannot start cooler: interlock check failed")
            return False
        
        self.logger.info("Starting GM cooler")
        self._state = CoolerState.STARTING
        # TODO: Send start command to PLC
        return True
    
    def stop(self) -> bool:
        """
        Stop the GM cooler.
        
        Returns:
            True if stop successful
        """
        if self._state == CoolerState.OFF:
            self.logger.warning("Cooler already stopped")
            return True
        
        self.logger.info("Stopping GM cooler")
        self._state = CoolerState.STOPPING
        # TODO: Send stop command to PLC
        return True
    
    def emergency_stop(self) -> bool:
        """
        Emergency stop of cooler.
        
        Returns:
            True if stop successful
        """
        self.logger.warning("EMERGENCY STOP: GM Cooler")
        self._state = CoolerState.OFF
        self._compressor_on = False
        # TODO: Send emergency stop to PLC
        return True
    
    def _check_start_interlocks(self) -> bool:
        """
        Check if it's safe to start the cooler.
        
        Returns:
            True if safe to start
        """
        # Check maintenance schedule
        if self._runtime_hours >= self.max_runtime_hours:
            self.logger.error("Cooler requires maintenance")
            return False
        
        # TODO: Check other interlocks (water flow, power, etc.)
        return True
    
    def update_runtime(self, hours: float) -> None:
        """Update cooler runtime from PLC"""
        self._runtime_hours = hours
        
        if self._runtime_hours >= self.max_runtime_hours * 0.9:
            self.logger.warning(
                f"Cooler approaching maintenance interval: "
                f"{self._runtime_hours:.1f}/{self.max_runtime_hours} hours"
            )
    
    def get_status(self) -> dict:
        """
        Get cooler status.
        
        Returns:
            Dictionary with cooler status information
        """
        return {
            "name": self.name,
            "state": self._state.value,
            "runtime_hours": self._runtime_hours,
            "max_runtime_hours": self.max_runtime_hours,
            "maintenance_due": self._runtime_hours >= self.max_runtime_hours * 0.9,
            "compressor_on": self._compressor_on,
            "plc_address": self.plc_address
        }
