"""
Cooldown Process Module

Automated cooldown sequence for the cryostat to reach 4K operation.
Implements staged cooling with safety monitoring.
"""

from enum import Enum
from typing import Optional, Dict, Callable
import logging
import time


class CooldownStage(Enum):
    """Stages of cooldown process"""
    IDLE = "idle"
    PRE_COOL_CHECK = "pre_cool_check"
    VACUUM_PUMP = "vacuum_pump"
    START_COOLER = "start_cooler"
    INITIAL_COOLDOWN = "initial_cooldown"  # 300K -> 77K
    INTERMEDIATE_COOLDOWN = "intermediate_cooldown"  # 77K -> 20K
    FINAL_COOLDOWN = "final_cooldown"  # 20K -> 4K
    STABILIZATION = "stabilization"
    COMPLETE = "complete"
    ERROR = "error"
    ABORTED = "aborted"


class CooldownProcess:
    """
    Automated cooldown process.
    
    Manages the complete cooldown sequence from room temperature to 4K
    with safety monitoring and staged progression.
    """
    
    def __init__(self):
        """Initialize cooldown process"""
        self._stage = CooldownStage.IDLE
        self._start_time: Optional[float] = None
        self._stage_start_time: Optional[float] = None
        self._abort_requested = False
        self._pause_requested = False
        
        # Temperature targets for each stage
        self.stage_targets = {
            CooldownStage.INITIAL_COOLDOWN: 77.0,  # K
            CooldownStage.INTERMEDIATE_COOLDOWN: 20.0,  # K
            CooldownStage.FINAL_COOLDOWN: 4.0,  # K
        }
        
        # Callbacks for stage transitions
        self._stage_callbacks: Dict[CooldownStage, Callable] = {}
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Cooldown process initialized")
    
    @property
    def stage(self) -> CooldownStage:
        """Get current cooldown stage"""
        return self._stage
    
    @property
    def is_running(self) -> bool:
        """Check if cooldown is in progress"""
        return self._stage not in [
            CooldownStage.IDLE,
            CooldownStage.COMPLETE,
            CooldownStage.ERROR,
            CooldownStage.ABORTED
        ]
    
    @property
    def elapsed_time(self) -> Optional[float]:
        """Get elapsed time since cooldown started (seconds)"""
        if self._start_time is None:
            return None
        return time.time() - self._start_time
    
    def start(self) -> bool:
        """
        Start the cooldown process.
        
        Returns:
            True if start successful
        """
        if self.is_running:
            self.logger.warning("Cooldown already in progress")
            return False
        
        self.logger.info("Starting cooldown process")
        self._stage = CooldownStage.PRE_COOL_CHECK
        self._start_time = time.time()
        self._stage_start_time = time.time()
        self._abort_requested = False
        self._pause_requested = False
        
        return True
    
    def abort(self) -> bool:
        """
        Abort the cooldown process.
        
        Returns:
            True if abort successful
        """
        if not self.is_running:
            self.logger.warning("No cooldown in progress to abort")
            return False
        
        self.logger.warning("Aborting cooldown process")
        self._abort_requested = True
        self._stage = CooldownStage.ABORTED
        
        return True
    
    def pause(self) -> bool:
        """
        Pause the cooldown process.
        
        Returns:
            True if pause successful
        """
        if not self.is_running:
            self.logger.warning("No cooldown in progress to pause")
            return False
        
        self.logger.info("Pausing cooldown process")
        self._pause_requested = True
        
        return True
    
    def resume(self) -> bool:
        """
        Resume paused cooldown process.
        
        Returns:
            True if resume successful
        """
        if not self._pause_requested:
            self.logger.warning("Cooldown is not paused")
            return False
        
        self.logger.info("Resuming cooldown process")
        self._pause_requested = False
        
        return True
    
    def advance_stage(self, next_stage: CooldownStage) -> None:
        """
        Advance to next cooldown stage.
        
        Args:
            next_stage: Next stage to transition to
        """
        self.logger.info(f"Cooldown stage transition: {self._stage.value} -> {next_stage.value}")
        self._stage = next_stage
        self._stage_start_time = time.time()
        
        # Execute callback if registered
        if next_stage in self._stage_callbacks:
            try:
                self._stage_callbacks[next_stage]()
            except Exception as e:
                self.logger.error(f"Error in stage callback: {e}")
    
    def register_stage_callback(self, stage: CooldownStage, callback: Callable) -> None:
        """
        Register callback for stage transition.
        
        Args:
            stage: Stage to monitor
            callback: Function to call when stage is entered
        """
        self._stage_callbacks[stage] = callback
    
    def update(self, current_temp: float, current_pressure: float) -> None:
        """
        Update cooldown process based on current conditions.
        Should be called periodically to advance stages.
        
        Args:
            current_temp: Current temperature (K)
            current_pressure: Current vacuum pressure (mbar)
        """
        if not self.is_running or self._pause_requested:
            return
        
        # Check for abort
        if self._abort_requested:
            self.advance_stage(CooldownStage.ABORTED)
            return
        
        # Stage-specific logic
        if self._stage == CooldownStage.PRE_COOL_CHECK:
            # Check pre-conditions
            if self._check_preconditions():
                self.advance_stage(CooldownStage.VACUUM_PUMP)
            else:
                self.advance_stage(CooldownStage.ERROR)
        
        elif self._stage == CooldownStage.VACUUM_PUMP:
            # Wait for vacuum to reach target
            if current_pressure < 1e-3:  # Target vacuum level
                self.advance_stage(CooldownStage.START_COOLER)
        
        elif self._stage == CooldownStage.START_COOLER:
            # Start cooler and move to initial cooldown
            self.advance_stage(CooldownStage.INITIAL_COOLDOWN)
        
        elif self._stage == CooldownStage.INITIAL_COOLDOWN:
            if current_temp <= self.stage_targets[CooldownStage.INITIAL_COOLDOWN]:
                self.advance_stage(CooldownStage.INTERMEDIATE_COOLDOWN)
        
        elif self._stage == CooldownStage.INTERMEDIATE_COOLDOWN:
            if current_temp <= self.stage_targets[CooldownStage.INTERMEDIATE_COOLDOWN]:
                self.advance_stage(CooldownStage.FINAL_COOLDOWN)
        
        elif self._stage == CooldownStage.FINAL_COOLDOWN:
            if current_temp <= self.stage_targets[CooldownStage.FINAL_COOLDOWN]:
                self.advance_stage(CooldownStage.STABILIZATION)
        
        elif self._stage == CooldownStage.STABILIZATION:
            # Wait for temperature to stabilize
            stage_elapsed = time.time() - self._stage_start_time
            if stage_elapsed > 600:  # 10 minutes stabilization
                self.advance_stage(CooldownStage.COMPLETE)
                self.logger.info(f"Cooldown complete! Total time: {self.elapsed_time:.1f}s")
    
    def _check_preconditions(self) -> bool:
        """
        Check if preconditions for cooldown are met.
        
        Returns:
            True if safe to proceed
        """
        # TODO: Implement actual precondition checks
        # - All valves in correct position
        # - Sensors operational
        # - Safety interlocks clear
        return True
    
    def get_progress(self) -> float:
        """
        Get cooldown progress percentage.
        
        Returns:
            Progress from 0.0 to 1.0
        """
        stage_order = [
            CooldownStage.PRE_COOL_CHECK,
            CooldownStage.VACUUM_PUMP,
            CooldownStage.START_COOLER,
            CooldownStage.INITIAL_COOLDOWN,
            CooldownStage.INTERMEDIATE_COOLDOWN,
            CooldownStage.FINAL_COOLDOWN,
            CooldownStage.STABILIZATION,
            CooldownStage.COMPLETE
        ]
        
        try:
            current_index = stage_order.index(self._stage)
            return current_index / (len(stage_order) - 1)
        except ValueError:
            return 0.0
    
    def get_status(self) -> dict:
        """
        Get cooldown process status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "stage": self._stage.value,
            "is_running": self.is_running,
            "is_paused": self._pause_requested,
            "elapsed_time": self.elapsed_time,
            "progress": self.get_progress(),
            "abort_requested": self._abort_requested
        }
