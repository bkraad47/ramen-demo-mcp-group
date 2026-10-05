"""Factor-based unit conversion; temperature is the one affine family."""

LENGTH_M = {"mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0, "inch": 0.0254, "foot": 0.3048, "yard": 0.9144, "mile": 1609.344}
MASS_KG = {"mg": 1e-6, "g": 0.001, "kg": 1.0, "tonne": 1000.0, "ounce": 0.028349523125, "pound": 0.45359237}
TEMPERATURE = ("celsius", "fahrenheit", "kelvin")


def _to_celsius(value: float, unit: str) -> float:
    return {"celsius": value, "fahrenheit": (value - 32) * 5 / 9, "kelvin": value - 273.15}[unit]


def _from_celsius(value: float, unit: str) -> float:
    return {"celsius": value, "fahrenheit": value * 9 / 5 + 32, "kelvin": value + 273.15}[unit]


def convert(value: float, from_unit: str, to_unit: str) -> float:
    a, b = from_unit.strip().lower(), to_unit.strip().lower()
    for table in (LENGTH_M, MASS_KG):
        if a in table and b in table:
            return value * table[a] / table[b]
    if a in TEMPERATURE and b in TEMPERATURE:
        return _from_celsius(_to_celsius(value, a), b)
    accepted = sorted(LENGTH_M) + sorted(MASS_KG) + list(TEMPERATURE)
    raise ValueError(f"cannot convert {from_unit!r} to {to_unit!r}; both must be in one family of {accepted}")
