"""
Automation Safety Module

High-level safety checks and interlocks for automated processes.
Builds on hardware safety monitor with process-specific checks.
"""

from typing import Optional, Dict, Callable
import logging


class AutomationSafety:
    """
    Safety system for automated processes.
    
    Implements additional safety checks specific to automated
    cooldown/warmup sequences beyond basic hardware interlocks.
    """
    
    def __init__(self):
        """Initialize automation safety"""
        self.logger = logging.getLogger(__name__)
        
        # Safety limits
        self.max_cooldown_rate = 10.0  # K/min
        self.max_warmup_rate = 15.0  # K/min
        self.max_pressure_rate = 1.0  # mbar/min
        
        # Process state
        self._cooldown_allowed = True
        self._warmup_allowed = True
        self._emergency_stop_active = False
        
        # Reference to hardware safety monitor
        self.hardware_safety: Optional[any] = None
        
        self.logger.info("Automation safety initialized")
    
    def check_cooldown_safe(
        self,
        current_temp: float,
        current_pressure: float,
        target_temp: float
    ) -> tuple[bool, str]:
        """
        Check if cooldown operation is safe.
        
        Args:
            current_temp: Current temperature (K)
            current_pressure: Current pressure (mbar)
            target_temp: Target temperature (K)
            
        Returns:
            Tuple of (is_safe, reason)
        """
        if self._emergency_stop_active:
            return False, "Emergency stop active"
        
        if not self._cooldown_allowed:
            return False, "Cooldown not allowed"
        
        # Check pressure is low enough
        if current_pressure > 1e-2:
            return False, f"Vacuum pressure too high: {current_pressure} mbar"
        
        # Check temperature is reasonable
        if current_temp < target_temp:
            return False, "Current temperature already below target"
        
        if current_temp < 2.0:
            return False, "Temperature already at minimum"
        
        # Check hardware safety
        if self.hardware_safety:
            interlocks = self.hardware_safety.get_active_interlocks()
            if interlocks:
                return False, f"Hardware interlocks active: {', '.join(interlocks)}"
        
        return True, "OK"
    
    def check_warmup_safe(
        self,
        current_temp: float,
        target_temp: float
    ) -> tuple[bool, str]:
        """
        Check if warmup operation is safe.
        
        Args:
            current_temp: Current temperature (K)
            target_temp: Target temperature (K)
            
        Returns:
            Tuple of (is_safe, reason)
        """
        if self._emergency_stop_active:
            return False, "Emergency stop active"
        
        if not self._warmup_allowed:
            return False, "Warmup not allowed"
        
        # Check temperature is reasonable
        if current_temp > target_temp:
            return False, "Current temperature already above target"
        
        if current_temp > 350.0:
            return False, "Temperature already at maximum safe limit"
        
        # Check hardware safety
        if self.hardware_safety:
            interlocks = self.hardware_safety.get_active_interlocks()
            if interlocks:
                return False, f"Hardware interlocks active: {', '.join(interlocks)}"
        
        return True, "OK"
    
    def check_rate_safe(
        self,
        rate: float,
        rate_type: str = "cooldown"
    ) -> tuple[bool, str]:
        """
        Check if temperature change rate is safe.
        
        Args:
            rate: Rate of change (K/min)
            rate_type: Type of rate ("cooldown" or "warmup")
            
        Returns:
            Tuple of (is_safe, reason)
        """
        if rate_type == "cooldown":
            max_rate = self.max_cooldown_rate
            if abs(rate) > max_rate:
                return False, f"Cooldown rate too high: {abs(rate):.2f} K/min (max: {max_rate})"
        
        elif rate_type == "warmup":
            max_rate = self.max_warmup_rate
            if abs(rate) > max_rate:
                return False, f"Warmup rate too high: {abs(rate):.2f} K/min (max: {max_rate})"
        
        return True, "OK"
    
    def check_valve_sequence_safe(
        self,
        valve_states: Dict[str, str],
        required_states: Dict[str, str]
    ) -> tuple[bool, str]:
        """
        Check if valve configuration is safe for operation.
        
        Args:
            valve_states: Current valve states
            required_states: Required valve states
            
        Returns:
            Tuple of (is_safe, reason)
        """
        for valve_name, required_state in required_states.items():
            if valve_name not in valve_states:
                return False, f"Valve {valve_name} state unknown"
            
            if valve_states[valve_name] != required_state:
                return False, f"Valve {valve_name} not in required state (current: {valve_states[valve_name]}, required: {required_state})"
        
        return True, "OK"
    
    def enable_cooldown(self) -> None:
        """Enable cooldown operations"""
        self._cooldown_allowed = True
        self.logger.info("Cooldown operations enabled")
    
    def disable_cooldown(self) -> None:
        """Disable cooldown operations"""
        self._cooldown_allowed = False
        self.logger.warning("Cooldown operations disabled")
    
    def enable_warmup(self) -> None:
        """Enable warmup operations"""
        self._warmup_allowed = True
        self.logger.info("Warmup operations enabled")
    
    def disable_warmup(self) -> None:
        """Disable warmup operations"""
        self._warmup_allowed = False
        self.logger.warning("Warmup operations disabled")
    
    def trigger_emergency_stop(self) -> None:
        """Trigger emergency stop for all automated processes"""
        self.logger.critical("AUTOMATION EMERGENCY STOP TRIGGERED")
        self._emergency_stop_active = True
        self._cooldown_allowed = False
        self._warmup_allowed = False
    
    def reset_emergency_stop(self) -> None:
        """Reset emergency stop after manual verification"""
        self.logger.warning("Resetting automation emergency stop")
        self._emergency_stop_active = False
    
    def get_status(self) -> dict:
        """
        Get automation safety status.
        
        Returns:
            Dictionary with safety status
        """
        return {
            "cooldown_allowed": self._cooldown_allowed,
            "warmup_allowed": self._warmup_allowed,
            "emergency_stop_active": self._emergency_stop_active,
            "max_cooldown_rate": self.max_cooldown_rate,
            "max_warmup_rate": self.max_warmup_rate,
            "max_pressure_rate": self.max_pressure_rate
        }
