"""
Valve Control Module

Provides control interface for various types of valves in the cryostat system.
Supports safety interlocks and state validation.
"""

from enum import Enum
from typing import Optional
import logging


class ValveState(Enum):
    """Valve states"""
    OPEN = "open"
    CLOSED = "closed"
    OPENING = "opening"
    CLOSING = "closing"
    ERROR = "error"
    UNKNOWN = "unknown"


class ValveType(Enum):
    """Types of valves in the system"""
    ISOLATION = "isolation"
    NEEDLE = "needle"
    RELIEF = "relief"
    BYPASS = "bypass"


class Valve:
    """
    Generic valve control class with safety features.
    
    Attributes:
        name: Unique identifier for the valve
        valve_type: Type of valve (isolation, needle, etc.)
        plc_address: Address in PLC memory for this valve
        state: Current valve state
        interlock_enabled: Whether safety interlocks are active
    """
    
    def __init__(
        self,
        name: str,
        valve_type: ValveType,
        plc_address: str,
        normally_closed: bool = True,
        interlock_enabled: bool = True
    ):
        """
        Initialize a valve.
        
        Args:
            name: Unique identifier for the valve
            valve_type: Type of valve
            plc_address: PLC memory address (e.g., "DB1.DBX0.0")
            normally_closed: True if valve is normally closed
            interlock_enabled: Enable safety interlocks
        """
        self.name = name
        self.valve_type = valve_type
        self.plc_address = plc_address
        self.normally_closed = normally_closed
        self.interlock_enabled = interlock_enabled
        self._state = ValveState.UNKNOWN
        self._target_state: Optional[ValveState] = None
        
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.logger.info(f"Initialized valve: {name} ({valve_type.value})")
    
    @property
    def state(self) -> ValveState:
        """Get current valve state"""
        return self._state
    
    def open(self, force: bool = False) -> bool:
        """
        Open the valve.
        
        Args:
            force: Bypass safety interlocks (use with extreme caution)
            
        Returns:
            True if command successful, False otherwise
        """
        if self.interlock_enabled and not force:
            if not self._check_open_interlocks():
                self.logger.warning(f"Valve {self.name}: Open command blocked by interlocks")
                return False
        
        self.logger.info(f"Opening valve {self.name}")
        self._target_state = ValveState.OPEN
        self._state = ValveState.OPENING
        # TODO: Send command to PLC via interface
        return True
    
    def close(self, force: bool = False) -> bool:
        """
        Close the valve.
        
        Args:
            force: Bypass safety interlocks (use with extreme caution)
            
        Returns:
            True if command successful, False otherwise
        """
        if self.interlock_enabled and not force:
            if not self._check_close_interlocks():
                self.logger.warning(f"Valve {self.name}: Close command blocked by interlocks")
                return False
        
        self.logger.info(f"Closing valve {self.name}")
        self._target_state = ValveState.CLOSED
        self._state = ValveState.CLOSING
        # TODO: Send command to PLC via interface
        return True
    
    def emergency_close(self) -> bool:
        """
        Emergency close - bypasses normal interlocks.
        Used in emergency shutdown scenarios.
        
        Returns:
            True if command successful
        """
        self.logger.warning(f"EMERGENCY CLOSE: {self.name}")
        return self.close(force=True)
    
    def _check_open_interlocks(self) -> bool:
        """
        Check if it's safe to open the valve.
        Override in subclasses for specific valve logic.
        
        Returns:
            True if safe to open
        """
        # TODO: Implement specific interlock logic
        return True
    
    def _check_close_interlocks(self) -> bool:
        """
        Check if it's safe to close the valve.
        Override in subclasses for specific valve logic.
        
        Returns:
            True if safe to close
        """
        # TODO: Implement specific interlock logic
        return True
    
    def update_state(self, new_state: ValveState) -> None:
        """
        Update valve state from PLC feedback.
        
        Args:
            new_state: New state from PLC
        """
        if new_state != self._state:
            self.logger.info(f"Valve {self.name} state changed: {self._state.value} -> {new_state.value}")
            self._state = new_state
    
    def get_status(self) -> dict:
        """
        Get current valve status.
        
        Returns:
            Dictionary with valve status information
        """
        return {
            "name": self.name,
            "type": self.valve_type.value,
            "state": self._state.value,
            "target_state": self._target_state.value if self._target_state else None,
            "normally_closed": self.normally_closed,
            "interlock_enabled": self.interlock_enabled,
            "plc_address": self.plc_address
        }
