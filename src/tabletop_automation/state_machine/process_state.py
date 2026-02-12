"""
Process State Machine Module

High-level state machine for automated processes.
Manages overall system operation modes.
"""

from enum import Enum
from typing import Optional, List, Dict
import logging
from datetime import datetime


class ProcessState(Enum):
    """High-level process states"""
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    READY = "ready"
    COOLDOWN = "cooldown"
    OPERATING = "operating"  # At target temperature
    WARMUP = "warmup"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    EMERGENCY = "emergency"


class ProcessStateMachine:
    """
    State machine for automated process control.
    
    Manages high-level operational states and coordinates
    hardware and automation subsystems.
    """
    
    def __init__(self):
        """Initialize process state machine"""
        self._current_state = ProcessState.OFFLINE
        self._previous_state: Optional[ProcessState] = None
        self._state_history: List[tuple] = []  # (timestamp, state) pairs
        
        # Valid state transitions
        self._valid_transitions: Dict[ProcessState, List[ProcessState]] = {
            ProcessState.OFFLINE: [
                ProcessState.INITIALIZING
            ],
            ProcessState.INITIALIZING: [
                ProcessState.READY,
                ProcessState.ERROR
            ],
            ProcessState.READY: [
                ProcessState.COOLDOWN,
                ProcessState.WARMUP,
                ProcessState.MAINTENANCE,
                ProcessState.OFFLINE,
                ProcessState.ERROR,
                ProcessState.EMERGENCY
            ],
            ProcessState.COOLDOWN: [
                ProcessState.OPERATING,
                ProcessState.READY,
                ProcessState.ERROR,
                ProcessState.EMERGENCY
            ],
            ProcessState.OPERATING: [
                ProcessState.WARMUP,
                ProcessState.ERROR,
                ProcessState.EMERGENCY
            ],
            ProcessState.WARMUP: [
                ProcessState.READY,
                ProcessState.ERROR,
                ProcessState.EMERGENCY
            ],
            ProcessState.MAINTENANCE: [
                ProcessState.READY,
                ProcessState.OFFLINE
            ],
            ProcessState.ERROR: [
                ProcessState.READY,
                ProcessState.MAINTENANCE,
                ProcessState.EMERGENCY
            ],
            ProcessState.EMERGENCY: [
                ProcessState.MAINTENANCE
            ]
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Process state machine initialized")
    
    @property
    def current_state(self) -> ProcessState:
        """Get current process state"""
        return self._current_state
    
    @property
    def previous_state(self) -> Optional[ProcessState]:
        """Get previous process state"""
        return self._previous_state
    
    def can_transition_to(self, target_state: ProcessState) -> bool:
        """
        Check if transition to target state is valid.
        
        Args:
            target_state: Desired state
            
        Returns:
            True if transition is valid
        """
        valid_targets = self._valid_transitions.get(self._current_state, [])
        return target_state in valid_targets
    
    def transition_to(self, target_state: ProcessState, force: bool = False) -> bool:
        """
        Transition to a new process state.
        
        Args:
            target_state: Desired state
            force: Force transition (bypass validation)
            
        Returns:
            True if transition successful
        """
        if not force and not self.can_transition_to(target_state):
            self.logger.error(
                f"Invalid process state transition: {self._current_state.value} -> {target_state.value}"
            )
            return False
        
        # Perform transition
        self._previous_state = self._current_state
        self._current_state = target_state
        self._state_history.append((datetime.now(), target_state))
        
        log_msg = f"Process state transition: {self._previous_state.value} -> {self._current_state.value}"
        if force:
            log_msg += " (FORCED)"
        
        self.logger.info(log_msg)
        
        return True
    
    def emergency_transition(self) -> bool:
        """
        Force transition to EMERGENCY state.
        
        Returns:
            True always
        """
        self.logger.critical("EMERGENCY PROCESS STATE TRANSITION")
        return self.transition_to(ProcessState.EMERGENCY, force=True)
    
    def get_valid_transitions(self) -> List[ProcessState]:
        """
        Get list of valid target states from current state.
        
        Returns:
            List of valid target states
        """
        return self._valid_transitions.get(self._current_state, [])
    
    def is_operational(self) -> bool:
        """
        Check if system is in an operational state.
        
        Returns:
            True if system can perform useful work
        """
        return self._current_state in [
            ProcessState.READY,
            ProcessState.COOLDOWN,
            ProcessState.OPERATING,
            ProcessState.WARMUP
        ]
    
    def requires_attention(self) -> bool:
        """
        Check if state requires operator attention.
        
        Returns:
            True if operator intervention needed
        """
        return self._current_state in [
            ProcessState.ERROR,
            ProcessState.EMERGENCY,
            ProcessState.MAINTENANCE
        ]
    
    def get_state_duration(self) -> Optional[float]:
        """
        Get time spent in current state.
        
        Returns:
            Duration in seconds, or None if unknown
        """
        if not self._state_history:
            return None
        
        last_transition = self._state_history[-1][0]
        return (datetime.now() - last_transition).total_seconds()
    
    def get_state_history(self, count: int = 100) -> List[tuple]:
        """
        Get recent state history.
        
        Args:
            count: Number of recent states to return
            
        Returns:
            List of (timestamp, state) tuples
        """
        return self._state_history[-count:]
    
    def reset(self) -> None:
        """Reset state machine to OFFLINE"""
        self.logger.warning("Resetting process state machine")
        self._previous_state = self._current_state
        self._current_state = ProcessState.OFFLINE
        self._state_history.append((datetime.now(), self._current_state))
    
    def get_status(self) -> dict:
        """
        Get state machine status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "current_state": self._current_state.value,
            "previous_state": self._previous_state.value if self._previous_state else None,
            "valid_transitions": [s.value for s in self.get_valid_transitions()],
            "is_operational": self.is_operational(),
            "requires_attention": self.requires_attention(),
            "state_duration": self.get_state_duration(),
            "state_changes": len(self._state_history)
        }
