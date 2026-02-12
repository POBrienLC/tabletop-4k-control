"""
Hardware State Machine Module

Implements state machine for hardware control system.
Manages transitions between operational states with safety validation.
"""

from enum import Enum
from typing import Optional, Dict, List, Callable
import logging
from datetime import datetime


class HardwareState(Enum):
    """Hardware system states"""
    UNINITIALIZED = "uninitialized"
    INITIALIZED = "initialized"
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"


class StateTransition:
    """Represents a state transition"""
    
    def __init__(
        self,
        from_state: HardwareState,
        to_state: HardwareState,
        condition: Optional[Callable] = None,
        action: Optional[Callable] = None
    ):
        """
        Define a state transition.
        
        Args:
            from_state: Source state
            to_state: Destination state
            condition: Optional function that must return True for transition
            action: Optional function to execute during transition
        """
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition
        self.action = action


class HardwareStateMachine:
    """
    State machine for hardware control system.
    
    Manages system state transitions with validation and safety checks.
    """
    
    def __init__(self):
        """Initialize state machine"""
        self._current_state = HardwareState.UNINITIALIZED
        self._previous_state: Optional[HardwareState] = None
        self._transitions: Dict[HardwareState, List[StateTransition]] = {
            state: [] for state in HardwareState
        }
        self._state_history: List[tuple] = []  # (timestamp, state) pairs
        
        self.logger = logging.getLogger(__name__)
        self._setup_transitions()
        self.logger.info("Hardware state machine initialized")
    
    def _setup_transitions(self) -> None:
        """Define valid state transitions"""
        # From UNINITIALIZED
        self.add_transition(HardwareState.UNINITIALIZED, HardwareState.INITIALIZED)
        
        # From INITIALIZED
        self.add_transition(HardwareState.INITIALIZED, HardwareState.IDLE)
        self.add_transition(HardwareState.INITIALIZED, HardwareState.ERROR)
        
        # From IDLE
        self.add_transition(HardwareState.IDLE, HardwareState.STARTING)
        self.add_transition(HardwareState.IDLE, HardwareState.MAINTENANCE)
        self.add_transition(HardwareState.IDLE, HardwareState.ERROR)
        self.add_transition(HardwareState.IDLE, HardwareState.EMERGENCY)
        
        # From STARTING
        self.add_transition(HardwareState.STARTING, HardwareState.RUNNING)
        self.add_transition(HardwareState.STARTING, HardwareState.ERROR)
        self.add_transition(HardwareState.STARTING, HardwareState.EMERGENCY)
        
        # From RUNNING
        self.add_transition(HardwareState.RUNNING, HardwareState.STOPPING)
        self.add_transition(HardwareState.RUNNING, HardwareState.ERROR)
        self.add_transition(HardwareState.RUNNING, HardwareState.EMERGENCY)
        
        # From STOPPING
        self.add_transition(HardwareState.STOPPING, HardwareState.IDLE)
        self.add_transition(HardwareState.STOPPING, HardwareState.ERROR)
        self.add_transition(HardwareState.STOPPING, HardwareState.EMERGENCY)
        
        # From ERROR
        self.add_transition(HardwareState.ERROR, HardwareState.IDLE)
        self.add_transition(HardwareState.ERROR, HardwareState.MAINTENANCE)
        self.add_transition(HardwareState.ERROR, HardwareState.EMERGENCY)
        
        # From EMERGENCY (limited transitions)
        self.add_transition(HardwareState.EMERGENCY, HardwareState.MAINTENANCE)
        
        # From MAINTENANCE
        self.add_transition(HardwareState.MAINTENANCE, HardwareState.IDLE)
    
    def add_transition(
        self,
        from_state: HardwareState,
        to_state: HardwareState,
        condition: Optional[Callable] = None,
        action: Optional[Callable] = None
    ) -> None:
        """
        Add a valid state transition.
        
        Args:
            from_state: Source state
            to_state: Destination state
            condition: Optional condition function
            action: Optional action function
        """
        transition = StateTransition(from_state, to_state, condition, action)
        self._transitions[from_state].append(transition)
    
    @property
    def current_state(self) -> HardwareState:
        """Get current state"""
        return self._current_state
    
    @property
    def previous_state(self) -> Optional[HardwareState]:
        """Get previous state"""
        return self._previous_state
    
    def can_transition_to(self, target_state: HardwareState) -> bool:
        """
        Check if transition to target state is valid.
        
        Args:
            target_state: Desired state
            
        Returns:
            True if transition is valid
        """
        valid_transitions = self._transitions.get(self._current_state, [])
        
        for transition in valid_transitions:
            if transition.to_state == target_state:
                # Check condition if specified
                if transition.condition is None or transition.condition():
                    return True
        
        return False
    
    def transition_to(self, target_state: HardwareState, force: bool = False) -> bool:
        """
        Transition to a new state.
        
        Args:
            target_state: Desired state
            force: Force transition (bypass validation)
            
        Returns:
            True if transition successful
        """
        if not force and not self.can_transition_to(target_state):
            self.logger.error(
                f"Invalid state transition: {self._current_state.value} -> {target_state.value}"
            )
            return False
        
        # Find and execute transition action
        if not force:
            valid_transitions = self._transitions.get(self._current_state, [])
            for transition in valid_transitions:
                if transition.to_state == target_state:
                    if transition.action:
                        try:
                            transition.action()
                        except Exception as e:
                            self.logger.error(f"Error executing transition action: {e}")
                            return False
                    break
        
        # Perform transition
        self._previous_state = self._current_state
        self._current_state = target_state
        self._state_history.append((datetime.now(), target_state))
        
        self.logger.info(
            f"State transition: {self._previous_state.value} -> {self._current_state.value}"
        )
        
        return True
    
    def emergency_transition(self) -> bool:
        """
        Force transition to EMERGENCY state.
        This bypasses normal transition validation.
        
        Returns:
            True always
        """
        self.logger.critical("EMERGENCY STATE TRANSITION")
        return self.transition_to(HardwareState.EMERGENCY, force=True)
    
    def get_valid_transitions(self) -> List[HardwareState]:
        """
        Get list of valid target states from current state.
        
        Returns:
            List of valid target states
        """
        valid_transitions = self._transitions.get(self._current_state, [])
        valid_states = []
        
        for transition in valid_transitions:
            if transition.condition is None or transition.condition():
                valid_states.append(transition.to_state)
        
        return valid_states
    
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
        """Reset state machine to UNINITIALIZED"""
        self.logger.warning("Resetting state machine")
        self._previous_state = self._current_state
        self._current_state = HardwareState.UNINITIALIZED
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
            "state_changes": len(self._state_history)
        }
