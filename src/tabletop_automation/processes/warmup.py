"""
Warmup Process Module

Automated warmup sequence for the cryostat from 4K to room temperature.
Implements controlled warming with safety monitoring.
"""

from enum import Enum
from typing import Optional, Dict, Callable
import logging
import time


class WarmupStage(Enum):
    """Stages of warmup process"""
    IDLE = "idle"
    PRE_WARMUP_CHECK = "pre_warmup_check"
    STOP_COOLER = "stop_cooler"
    INITIAL_WARMUP = "initial_warmup"  # 4K -> 20K
    INTERMEDIATE_WARMUP = "intermediate_warmup"  # 20K -> 77K
    FINAL_WARMUP = "final_warmup"  # 77K -> 300K
    VENTING = "venting"
    COMPLETE = "complete"
    ERROR = "error"
    ABORTED = "aborted"


class WarmupProcess:
    """
    Automated warmup process.
    
    Manages the complete warmup sequence from 4K to room temperature
    with safety monitoring and controlled rate.
    """
    
    def __init__(self):
        """Initialize warmup process"""
        self._stage = WarmupStage.IDLE
        self._start_time: Optional[float] = None
        self._stage_start_time: Optional[float] = None
        self._abort_requested = False
        self._pause_requested = False
        
        # Temperature targets for each stage
        self.stage_targets = {
            WarmupStage.INITIAL_WARMUP: 20.0,  # K
            WarmupStage.INTERMEDIATE_WARMUP: 77.0,  # K
            WarmupStage.FINAL_WARMUP: 300.0,  # K
        }
        
        # Maximum warmup rates (K/min) for safety
        self.max_warmup_rates = {
            WarmupStage.INITIAL_WARMUP: 2.0,
            WarmupStage.INTERMEDIATE_WARMUP: 5.0,
            WarmupStage.FINAL_WARMUP: 10.0,
        }
        
        # Callbacks for stage transitions
        self._stage_callbacks: Dict[WarmupStage, Callable] = {}
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Warmup process initialized")
    
    @property
    def stage(self) -> WarmupStage:
        """Get current warmup stage"""
        return self._stage
    
    @property
    def is_running(self) -> bool:
        """Check if warmup is in progress"""
        return self._stage not in [
            WarmupStage.IDLE,
            WarmupStage.COMPLETE,
            WarmupStage.ERROR,
            WarmupStage.ABORTED
        ]
    
    @property
    def elapsed_time(self) -> Optional[float]:
        """Get elapsed time since warmup started (seconds)"""
        if self._start_time is None:
            return None
        return time.time() - self._start_time
    
    def start(self) -> bool:
        """
        Start the warmup process.
        
        Returns:
            True if start successful
        """
        if self.is_running:
            self.logger.warning("Warmup already in progress")
            return False
        
        self.logger.info("Starting warmup process")
        self._stage = WarmupStage.PRE_WARMUP_CHECK
        self._start_time = time.time()
        self._stage_start_time = time.time()
        self._abort_requested = False
        self._pause_requested = False
        
        return True
    
    def abort(self) -> bool:
        """
        Abort the warmup process.
        
        Returns:
            True if abort successful
        """
        if not self.is_running:
            self.logger.warning("No warmup in progress to abort")
            return False
        
        self.logger.warning("Aborting warmup process")
        self._abort_requested = True
        self._stage = WarmupStage.ABORTED
        
        return True
    
    def pause(self) -> bool:
        """
        Pause the warmup process.
        
        Returns:
            True if pause successful
        """
        if not self.is_running:
            self.logger.warning("No warmup in progress to pause")
            return False
        
        self.logger.info("Pausing warmup process")
        self._pause_requested = True
        
        return True
    
    def resume(self) -> bool:
        """
        Resume paused warmup process.
        
        Returns:
            True if resume successful
        """
        if not self._pause_requested:
            self.logger.warning("Warmup is not paused")
            return False
        
        self.logger.info("Resuming warmup process")
        self._pause_requested = False
        
        return True
    
    def advance_stage(self, next_stage: WarmupStage) -> None:
        """
        Advance to next warmup stage.
        
        Args:
            next_stage: Next stage to transition to
        """
        self.logger.info(f"Warmup stage transition: {self._stage.value} -> {next_stage.value}")
        self._stage = next_stage
        self._stage_start_time = time.time()
        
        # Execute callback if registered
        if next_stage in self._stage_callbacks:
            try:
                self._stage_callbacks[next_stage]()
            except Exception as e:
                self.logger.error(f"Error in stage callback: {e}")
    
    def register_stage_callback(self, stage: WarmupStage, callback: Callable) -> None:
        """
        Register callback for stage transition.
        
        Args:
            stage: Stage to monitor
            callback: Function to call when stage is entered
        """
        self._stage_callbacks[stage] = callback
    
    def update(self, current_temp: float, warmup_rate: float) -> None:
        """
        Update warmup process based on current conditions.
        Should be called periodically to advance stages.
        
        Args:
            current_temp: Current temperature (K)
            warmup_rate: Current rate of temperature change (K/min)
        """
        if not self.is_running or self._pause_requested:
            return
        
        # Check for abort
        if self._abort_requested:
            self.advance_stage(WarmupStage.ABORTED)
            return
        
        # Check warmup rate safety
        current_stage = self._stage
        if current_stage in self.max_warmup_rates:
            if warmup_rate > self.max_warmup_rates[current_stage]:
                self.logger.warning(
                    f"Warmup rate too high: {warmup_rate:.2f} K/min "
                    f"(max: {self.max_warmup_rates[current_stage]} K/min)"
                )
                # TODO: Take corrective action
        
        # Stage-specific logic
        if self._stage == WarmupStage.PRE_WARMUP_CHECK:
            if self._check_preconditions():
                self.advance_stage(WarmupStage.STOP_COOLER)
            else:
                self.advance_stage(WarmupStage.ERROR)
        
        elif self._stage == WarmupStage.STOP_COOLER:
            # Move to initial warmup after cooler stopped
            self.advance_stage(WarmupStage.INITIAL_WARMUP)
        
        elif self._stage == WarmupStage.INITIAL_WARMUP:
            if current_temp >= self.stage_targets[WarmupStage.INITIAL_WARMUP]:
                self.advance_stage(WarmupStage.INTERMEDIATE_WARMUP)
        
        elif self._stage == WarmupStage.INTERMEDIATE_WARMUP:
            if current_temp >= self.stage_targets[WarmupStage.INTERMEDIATE_WARMUP]:
                self.advance_stage(WarmupStage.FINAL_WARMUP)
        
        elif self._stage == WarmupStage.FINAL_WARMUP:
            if current_temp >= self.stage_targets[WarmupStage.FINAL_WARMUP]:
                self.advance_stage(WarmupStage.VENTING)
        
        elif self._stage == WarmupStage.VENTING:
            # Wait for safe venting conditions
            stage_elapsed = time.time() - self._stage_start_time
            if stage_elapsed > 300:  # 5 minutes venting time
                self.advance_stage(WarmupStage.COMPLETE)
                self.logger.info(f"Warmup complete! Total time: {self.elapsed_time:.1f}s")
    
    def _check_preconditions(self) -> bool:
        """
        Check if preconditions for warmup are met.
        
        Returns:
            True if safe to proceed
        """
        # TODO: Implement actual precondition checks
        return True
    
    def get_progress(self) -> float:
        """
        Get warmup progress percentage.
        
        Returns:
            Progress from 0.0 to 1.0
        """
        stage_order = [
            WarmupStage.PRE_WARMUP_CHECK,
            WarmupStage.STOP_COOLER,
            WarmupStage.INITIAL_WARMUP,
            WarmupStage.INTERMEDIATE_WARMUP,
            WarmupStage.FINAL_WARMUP,
            WarmupStage.VENTING,
            WarmupStage.COMPLETE
        ]
        
        try:
            current_index = stage_order.index(self._stage)
            return current_index / (len(stage_order) - 1)
        except ValueError:
            return 0.0
    
    def get_status(self) -> dict:
        """
        Get warmup process status.
        
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
