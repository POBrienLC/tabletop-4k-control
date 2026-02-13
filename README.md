# tabletop-4k-control
PLC and Python control stack for the Tabletop 4K cryostat, including automation, safety interlocks, and documentation.

# State Machin Modes
- OFF/ SAFE
- PUMP DOWN
- COOLING
- REGULATING
- WARMUP
- VENTING

Each mode has:

Entry actions (things you must do when entering)
Permitted commands (what operators/automation are allowed to request)
Continuous invariants (conditions that must remain true)
Exit conditions (what must be true to leave normally)
Fault triggers (what forces an emergency transition)

Commands are implemented via ROE
Request (requested mode or operation)
Observation (sensor-confirmed conditions)
Effect (outputs to reach the intent safely)

Transitions should be driven by verified conditions, not by assumptions like “I opened valve so pressure will drop.”

# State Machine Sub-Modes
Each state contains a number of sub-modes for different process phases. 

# State: PUMP_DOWN
