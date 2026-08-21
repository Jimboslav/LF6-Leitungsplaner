"""Berechnungslogik fuer die LF6-Leitungsplanungs-App."""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, sin, sqrt


SECTIONS = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]

# DIN-VDE-0298-4-Referenzwerte aus Tabelle 24 der bereitgestellten Formelsammlung.
AMPACITY = {
    "A1": {2: [15.5, 19.5, 26, 34, 46, 61, 80, 99, 119, 151, 182, 210, 240, 273, 321, 367],
           3: [13.5, 18, 24, 31, 42, 56, 73, 89, 108, 136, 164, 188, 216, 245, 286, 328]},
    "A2": {2: [15, 18.5, 25, 32, 43, 57, 75, 92, 110, 139, 167, 192, 219, 248, 291, 334],
           3: [13, 17.5, 23, 29, 39, 52, 68, 83, 99, 125, 150, 172, 196, 223, 261, 298]},
    "B1": {2: [17.5, 24, 32, 41, 57, 76, 101, 125, 151, 192, 232, 269, 300, 341, 400, 458],
           3: [15.5, 21, 28, 36, 50, 68, 89, 110, 134, 171, 207, 239, 262, 296, 346, 394]},
    "B2": {2: [16.5, 23, 30, 38, 52, 69, 90, 111, 133, 168, 201, 232, 258, 294, 344, 394],
           3: [15, 20, 27, 34, 46, 62, 80, 99, 118, 149, 179, 206, 225, 255, 297, 339]},
    "C": {2: [19.5, 27, 36, 46, 63, 85, 112, 138, 168, 213, 258, 299, 344, 392, 461, 530],
          3: [17.5, 24, 32, 41, 57, 76, 96, 119, 144, 184, 223, 259, 299, 341, 403, 464]},
}

STANDARD_FUSES = [6, 10, 13, 16, 20, 25, 32, 35, 40, 50, 63, 80, 100, 125, 160, 200, 224, 250, 315, 400]
CONDUCTIVITY = {"Kupfer": 54.0, "Aluminium": 34.0, "Gold": 45.0, "Silber": 62.0, "Stahl": 7.2, "Aldrey": 30.0}
ALPHA = {"Kupfer": 0.00393, "Aluminium": 0.00403, "Stahl": 0.00450, "Aldrey": 0.00360}
REACTANCE = {"Mehrleiterkabel": 0.08, "Einleiterkabel im Dreieck": 0.09, "Einleiterkabel nebeneinander": 0.14,
             "Freileitung": 0.33, "Sammelschiene": 0.12}


def operating_current(power_kw: float, voltage: float, power_factor: float, phases: int = 3,
                      efficiency: float = 1.0, simultaneity: float = 1.0) -> float:
    if min(power_kw, voltage, power_factor, efficiency, simultaneity) <= 0:
        raise ValueError("Alle Eingaben muessen groesser als null sein.")
    denominator = voltage * power_factor * efficiency * (sqrt(3) if phases == 3 else 1)
    return power_kw * 1000 * simultaneity / denominator


def conductor_resistance(length_m: float, section_mm2: float, material: str = "Kupfer", temperature_c: float = 20) -> float:
    if length_m < 0 or section_mm2 <= 0:
        raise ValueError("Laenge und Querschnitt sind ungueltig.")
    gamma = CONDUCTIVITY[material]
    r20 = length_m / (gamma * section_mm2)
    alpha = ALPHA.get(material, 0.004)
    return r20 * (1 + alpha * (temperature_c - 20))


def voltage_drop(current_a: float, length_m: float, section_mm2: float, voltage: float,
                 power_factor: float, phases: int = 3, material: str = "Kupfer",
                 temperature_c: float = 70, reactance_ohm_km: float = 0.0) -> tuple[float, float]:
    if not 0 < power_factor <= 1:
        raise ValueError("cos phi muss zwischen 0 und 1 liegen.")
    r_per_km = conductor_resistance(1000, section_mm2, material, temperature_c)
    sin_phi = sin(acos(power_factor))
    factor = sqrt(3) if phases == 3 else 2
    drop = factor * (length_m / 1000) * current_a * (r_per_km * power_factor + reactance_ohm_km * sin_phi)
    return drop, drop / voltage * 100


def next_standard_fuse(current_a: float) -> int | None:
    return next((value for value in STANDARD_FUSES if value >= current_a), None)


@dataclass(frozen=True)
class DimensioningResult:
    current_a: float
    required_reference_a: float
    section_mm2: float | None
    reference_ampacity_a: float | None
    corrected_ampacity_a: float | None
    fuse_a: int | None
    drop_v: float | None
    drop_percent: float | None
    overload_ok: bool
    trip_ok: bool
    voltage_ok: bool

    @property
    def successful(self) -> bool:
        return self.section_mm2 is not None and self.overload_ok and self.trip_ok and self.voltage_ok


@dataclass(frozen=True)
class ProtectionResult:
    trip_current_a: float
    max_permitted_trip_current_a: float
    rated_current_ok: bool
    trip_rule_ok: bool

    @property
    def successful(self) -> bool:
        return self.rated_current_ok and self.trip_rule_ok


def check_overload_protection(operating_current_a: float, rated_current_a: float,
                              ampacity_a: float, device: str) -> ProtectionResult:
    """Prueft Bemessungsstrom- und Ausloeseregel nach Abschnitt 6.9/7."""
    if min(operating_current_a, rated_current_a, ampacity_a) <= 0:
        raise ValueError("Stroeme und Belastbarkeit muessen groesser als null sein.")
    if device not in {"LS", "gG"}:
        raise ValueError("Unbekanntes Schutzorgan.")
    trip_factor = 1.45 if device == "LS" else 1.6
    trip_current = rated_current_a * trip_factor
    max_trip_current = 1.45 * ampacity_a
    return ProtectionResult(
        trip_current_a=trip_current,
        max_permitted_trip_current_a=max_trip_current,
        rated_current_ok=operating_current_a <= rated_current_a <= ampacity_a,
        trip_rule_ok=trip_current <= max_trip_current,
    )


def dimension_line(*, power_kw: float, voltage: float, power_factor: float, phases: int,
                   efficiency: float, simultaneity: float, installation: str, loaded_conductors: int,
                   correction_factor: float, length_m: float, material: str, temperature_c: float,
                   max_drop_percent: float, reactance_ohm_km: float = 0.0, trip_factor: float = 1.45) -> DimensioningResult:
    current = operating_current(power_kw, voltage, power_factor, phases, efficiency, simultaneity)
    if not 0 < correction_factor <= 2:
        raise ValueError("Der Gesamtkorrekturfaktor muss groesser als 0 sein.")
    required = current / correction_factor
    fuse = next_standard_fuse(current)
    values = AMPACITY[installation][loaded_conductors]
    for section, reference in zip(SECTIONS, values):
        corrected = reference * correction_factor
        overload_ok = fuse is not None and current <= fuse <= corrected
        # Fuer gG gilt typischerweise I2 = 1,6 In; fuer LS 1,45 In. Konservativ konfigurierbar.
        trip_ok = fuse is not None and trip_factor * fuse <= 1.45 * corrected
        drop_v, drop_pct = voltage_drop(current, length_m, section, voltage, power_factor, phases,
                                        material, temperature_c, reactance_ohm_km)
        voltage_ok = drop_pct <= max_drop_percent
        if reference >= required and overload_ok and trip_ok and voltage_ok:
            return DimensioningResult(current, required, section, reference, corrected, fuse,
                                      drop_v, drop_pct, overload_ok, trip_ok, voltage_ok)
    return DimensioningResult(current, required, None, None, None, fuse, None, None, False, False, False)


def mean_power_factor(loads: list[tuple[float, float]]) -> tuple[float, float, float]:
    if not loads or sum(p for p, _ in loads) <= 0:
        raise ValueError("Mindestens eine positive Last ist erforderlich.")
    from math import tan, atan, cos
    tan_mean = sum(p * tan(acos(pf)) for p, pf in loads) / sum(p for p, _ in loads)
    angle = atan(tan_mean)
    return cos(angle), sin(angle), tan_mean

