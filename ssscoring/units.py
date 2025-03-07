from enum import Enum
import pandas as pd
from .constants import FT_IN_M

class UnitSystem(Enum):
    SI = "SI"
    IMPERIAL = "Imperial"
    MIXED = "Mixed"

def meters_to_feet(meters: float) -> float:
    return meters * FT_IN_M

def feet_to_meters(feet: float) -> float:
    return feet / FT_IN_M

def kmh_to_mph(kmh: float) -> float:
    return kmh * 0.621371

def mph_to_kmh(mph: float) -> float:
    return mph / 0.621371

def convert_altitude(value: float, from_system: UnitSystem, to_system: UnitSystem) -> tuple[float, str]:
    """Convert altitude values between unit systems and return value with unit suffix"""
    if from_system == to_system:
        return (value, "m" if to_system == UnitSystem.SI else "ft")
    
    if to_system == UnitSystem.SI:
        return (feet_to_meters(value), "m")
    else:
        return (meters_to_feet(value), "ft")

def convert_speed(value: float, from_system: UnitSystem, to_system: UnitSystem) -> tuple[float, str]:
    """Convert speed values between unit systems and return value with unit suffix"""
    if from_system == to_system:
        return (value, "km/h" if to_system == UnitSystem.SI else "mph")
    
    if to_system == UnitSystem.SI:
        return (mph_to_kmh(value), "km/h")
    else:
        return (kmh_to_mph(value), "mph")

def format_value_with_unit(value: float, unit_system: UnitSystem, metric: str) -> str:
    """Format a value with its appropriate unit based on the metric type and unit system"""
    if metric == "altitude":
        val, unit = convert_altitude(value, UnitSystem.SI, unit_system)
    elif metric == "speed":
        val, unit = convert_speed(value, UnitSystem.SI, unit_system)
    else:
        return f"{value:.1f}"
    
    return f"{val:.1f} {unit}"
