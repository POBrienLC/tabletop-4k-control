"""
Tabletop Automation Package

This package provides high-level automation and orchestration for the
tabletop 4K cryostat system, including:
- Automatic cooldown sequences
- Automatic warmup sequences
- System monitoring
- Safety interlocks
- Process state machine

Builds on top of the tabletop_hardware package.
"""

__version__ = "0.1.0"

from .processes.cooldown import CooldownProcess
from .processes.warmup import WarmupProcess
from .monitoring.system_monitor import SystemMonitor
from .safety.automation_safety import AutomationSafety
from .state_machine.process_state import ProcessState, ProcessStateMachine

__all__ = [
    "CooldownProcess",
    "WarmupProcess",
    "SystemMonitor",
    "AutomationSafety",
    "ProcessState",
    "ProcessStateMachine",
]
