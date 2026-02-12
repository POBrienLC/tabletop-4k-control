"""Unit tests for hardware package"""
import pytest
from tabletop_hardware.components.valve import Valve, ValveType, ValveState


class TestValve:
    """Test cases for Valve class"""
    
    def test_valve_initialization(self):
        """Test valve initialization"""
        valve = Valve(
            name="Test Valve",
            valve_type=ValveType.ISOLATION,
            plc_address="DB1.DBX0.0"
        )
        
        assert valve.name == "Test Valve"
        assert valve.valve_type == ValveType.ISOLATION
        assert valve.state == ValveState.UNKNOWN
    
    def test_valve_open(self):
        """Test opening a valve"""
        valve = Valve(
            name="Test Valve",
            valve_type=ValveType.ISOLATION,
            plc_address="DB1.DBX0.0"
        )
        
        result = valve.open()
        assert result is True
        assert valve.state == ValveState.OPENING
    
    def test_valve_close(self):
        """Test closing a valve"""
        valve = Valve(
            name="Test Valve",
            valve_type=ValveType.ISOLATION,
            plc_address="DB1.DBX0.0"
        )
        
        result = valve.close()
        assert result is True
        assert valve.state == ValveState.CLOSING
    
    def test_valve_emergency_close(self):
        """Test emergency close"""
        valve = Valve(
            name="Test Valve",
            valve_type=ValveType.ISOLATION,
            plc_address="DB1.DBX0.0"
        )
        
        result = valve.emergency_close()
        assert result is True
    
    def test_valve_get_status(self):
        """Test getting valve status"""
        valve = Valve(
            name="Test Valve",
            valve_type=ValveType.ISOLATION,
            plc_address="DB1.DBX0.0"
        )
        
        status = valve.get_status()
        assert status["name"] == "Test Valve"
        assert status["type"] == "isolation"
        assert "state" in status
