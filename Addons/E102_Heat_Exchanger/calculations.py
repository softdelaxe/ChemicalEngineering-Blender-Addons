"""
E-102 SHELL-AND-TUBE HEAT EXCHANGER
PRELIMINARY ENGINEERING CALCULATION MODULE

File: calculation.py

Purpose
-------
Preliminary thermal calculations, heating-medium selection, automatic
tube-count estimation, tube-side hydraulic screening, preliminary bundle
fit screening, and design-feasibility reporting.

Initial service
---------------
Waste cooking oil (WCO) heated in the tube side.

Heating medium
--------------
Selectable heating medium on the shell side:
- Hot water
- Saturated steam (condensing)
- Thermal oil
- Glycol-water mixture
- Hot air
- Flue gas
- Molten salt

IMPORTANT ENGINEERING LIMITATIONS
---------------------------------
This is a preliminary engineering/educational tool. It is NOT a complete
TEMA exchanger rating program, ASME pressure-vessel design, or fabrication
design.

The heating-medium database contains illustrative starting values only.
Actual properties must be obtained from validated sources at the actual
operating temperature, pressure, and composition.

The module:
- Uses a user-supplied overall heat-transfer coefficient, U.
- Uses a preliminary counter-current LMTD approach.
- Uses Ft = 1 for ideal isothermal condensing steam only as a preliminary
  thermal approximation.
- Estimates tube count from required area and rounds it to a multiple of
  tube passes.
- Uses a simplified tube-bundle envelope estimate, not a TEMA bundle
  diameter calculation.
- Does not calculate shell-side heat-transfer coefficients or pressure
  drop, tube-side pressure drop, vibration, nozzle losses, or mechanical
  integrity.
- Does not automatically determine the number of shells.

A FEASIBLE status means only that the implemented screening checks pass.
It does not mean the exchanger is certified or ready for fabrication.
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Dict, Optional


# =============================================================================
# 1. HEATING-MEDIUM DATABASE
# =============================================================================
# These are illustrative values, not guaranteed properties.
# Replace them with validated values for the actual fluid composition,
# temperature and pressure before using the results for design decisions.

HEATING_MEDIUMS: Dict[str, Dict[str, Any]] = {
    "hot_water": {
        "name": "Hot water",
        "mode": "sensible",
        "inlet_temp_c": 90.0,
        "outlet_temp_c": 70.0,
        "cp_kj_kg_k": 4.18,
        "density_kg_m3": 977.0,
        "viscosity_pa_s": 0.00040,
        "latent_heat_kj_kg": None,
        "pressure_bar": 2.0,
        "property_note": "Approximate liquid-water properties; verify at operating conditions.",
    },
    "steam": {
        "name": "Saturated steam (condensing)",
        "mode": "condensing",
        "inlet_temp_c": 120.0,
        "outlet_temp_c": 120.0,
        "cp_kj_kg_k": None,
        "density_kg_m3": None,
        "viscosity_pa_s": None,
        "latent_heat_kj_kg": 2201.0,
        "pressure_bar": 2.0,
        "property_note": "Illustrative saturation temperature and latent heat; obtain from steam tables at actual pressure.",
    },
    "thermal_oil": {
        "name": "Thermal oil",
        "mode": "sensible",
        "inlet_temp_c": 180.0,
        "outlet_temp_c": 150.0,
        "cp_kj_kg_k": 2.30,
        "density_kg_m3": 850.0,
        "viscosity_pa_s": 0.0030,
        "latent_heat_kj_kg": None,
        "pressure_bar": 3.0,
        "property_note": "Generic illustrative values; actual thermal-oil properties vary significantly by product and temperature.",
    },
    "glycol_water": {
        "name": "Glycol-water mixture",
        "mode": "sensible",
        "inlet_temp_c": 90.0,
        "outlet_temp_c": 70.0,
        "cp_kj_kg_k": 3.60,
        "density_kg_m3": 1030.0,
        "viscosity_pa_s": 0.0020,
        "latent_heat_kj_kg": None,
        "pressure_bar": 2.0,
        "property_note": "Illustrative mixture values; glycol type and concentration must be specified.",
    },
    "hot_air": {
        "name": "Hot air",
        "mode": "sensible",
        "inlet_temp_c": 180.0,
        "outlet_temp_c": 120.0,
        "cp_kj_kg_k": 1.005,
        "density_kg_m3": 0.85,
        "viscosity_pa_s": 0.000022,
        "latent_heat_kj_kg": None,
        "pressure_bar": 1.0,
        "property_note": "Illustrative gas properties; density and heat capacity depend on temperature and pressure.",
    },
    "flue_gas": {
        "name": "Flue gas",
        "mode": "sensible",
        "inlet_temp_c": 250.0,
        "outlet_temp_c": 150.0,
        "cp_kj_kg_k": 1.10,
        "density_kg_m3": 0.75,
        "viscosity_pa_s": 0.000025,
        "latent_heat_kj_kg": None,
        "pressure_bar": 1.0,
        "property_note": "Illustrative gas properties; actual composition and temperature-dependent properties are required.",
    },
    "molten_salt": {
        "name": "Molten salt",
        "mode": "sensible",
        "inlet_temp_c": 300.0,
        "outlet_temp_c": 250.0,
        "cp_kj_kg_k": 1.50,
        "density_kg_m3": 1800.0,
        "viscosity_pa_s": 0.0030,
        "latent_heat_kj_kg": None,
        "pressure_bar": 1.0,
        "property_note": "Illustrative only. Salt chemistry, freezing point, corrosion and material compatibility are critical.",
    },
}


# =============================================================================
# 2. DEFAULT INPUTS
# =============================================================================

DEFAULT_INPUTS: Dict[str, Any] = {
    # Process fluid: WCO, tube side
    "process_fluid_name": "Waste cooking oil",

    # Process-fluid metadata supplied by the Blender property group.
    # These fields document the selected fluid-property preset and its
    # provenance; they do not independently alter the thermal calculations.
    "process_fluid_type": "wco",
    "process_fluid_reference_temp_c": 25.0,
    "process_fluid_status": "estimated",
    "process_fluid_composition": "Variable used cooking oil",
    "process_fluid_source": "Existing E-102 preliminary design assumption",
    "process_fluid_source_url": "",
    "process_fluid_note": "Validate properties for actual fluid and conditions.",

    "wco_mass_flow_kg_h": 100.0,
    "wco_inlet_temp_c": 25.0,
    "wco_outlet_temp_c": 60.0,
    "wco_cp_kj_kg_k": 3.40,
    "wco_density_kg_m3": 900.0,
    "wco_viscosity_pa_s": 0.030,

    # Heating medium: default hot water, shell side
    "heating_medium_type": "hot_water",

    # Heating-medium operating conditions.
    # These values override the database values when supplied.
    "heating_medium_inlet_temp_c": None,
    "heating_medium_outlet_temp_c": None,
    "heating_medium_cp_kj_kg_k": None,
    "heating_medium_density_kg_m3": None,
    "heating_medium_viscosity_pa_s": None,
    "heating_medium_latent_heat_kj_kg": None,
    "heating_medium_pressure_bar": None,

    # Thermal design
    "design_factor": 1.20,
    "overall_heat_transfer_coefficient_w_m2_k": 150.0,

    # Preliminary fouling allowance.
    # This module reports the entered fouling resistances but does not
    # derive U from individual film coefficients.
    "tube_fouling_resistance_m2_k_w": 0.0002,
    "shell_fouling_resistance_m2_k_w": 0.0002,

    # Flow arrangement and exchanger geometry
    "flow_arrangement": "counter_current",
    "tube_outside_diameter_m": 0.0127,
    "tube_wall_thickness_m": 0.0009,
    "tube_length_m": 1.500,
    "tube_count": 16,
    "auto_size_tubes": True,
    "tube_passes": 4,
    "shell_passes": 1,
    "tube_pitch_m": 0.019,
    "tube_layout": "triangular",  # triangular or square

    # Shell dimensions
    "shell_internal_diameter_m": 0.200,
    "shell_wall_thickness_m": 0.004,

    # Other preliminary geometry
    "channel_head_length_m": 0.180,
    "tubesheet_thickness_m": 0.025,
    "baffle_count": 4,
    "baffle_cut_fraction": 0.25,

    # Screening limits. These are configurable screening values,
    # not universal design-code limits.
    "minimum_tube_velocity_m_s": 0.30,
    "maximum_tube_velocity_m_s": 2.00,
    "maximum_tube_reynolds_number_warning": None,

    # Mechanical screening inputs (not a mechanical design)
    "design_pressure_bar": 5.0,
    "design_temperature_c": 120.0,
    "corrosion_allowance_m": 0.0015,
    "construction_material": "Carbon steel (unverified)",
}


# =============================================================================
# 3. INPUT PREPARATION
# =============================================================================

def prepare_inputs(user_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Merge user inputs with defaults and the selected heating-medium database.

    Heating-medium database values are loaded first. Explicit user values
    override them. None values mean "use database value".
    """
    supplied = user_inputs or {}
    data = deepcopy(DEFAULT_INPUTS)

    unknown = set(supplied) - set(data)
    if unknown:
        raise KeyError("Unknown input(s): " + ", ".join(sorted(unknown)))

    data.update(supplied)

    medium_key = data["heating_medium_type"]
    if medium_key not in HEATING_MEDIUMS:
        raise ValueError(
            f"Unsupported heating medium '{medium_key}'. "
            f"Choose from: {', '.join(HEATING_MEDIUMS)}"
        )

    medium = deepcopy(HEATING_MEDIUMS[medium_key])

    field_map = {
        "heating_medium_inlet_temp_c": "inlet_temp_c",
        "heating_medium_outlet_temp_c": "outlet_temp_c",
        "heating_medium_cp_kj_kg_k": "cp_kj_kg_k",
        "heating_medium_density_kg_m3": "density_kg_m3",
        "heating_medium_viscosity_pa_s": "viscosity_pa_s",
        "heating_medium_latent_heat_kj_kg": "latent_heat_kj_kg",
        "heating_medium_pressure_bar": "pressure_bar",
    }

    for input_key, medium_key_name in field_map.items():
        if supplied.get(input_key) is None:
            data[input_key] = medium[medium_key_name]

    data["heating_medium_name"] = medium["name"]
    data["heating_medium_mode"] = medium["mode"]
    data["heating_medium_property_note"] = medium["property_note"]

    return data


# =============================================================================
# 4. VALIDATION
# =============================================================================

def validate_inputs(data: Dict[str, Any]) -> None:
    """Validate E-102 numerical inputs and supported design conditions."""

    # --------------------------------------------------------
    # 1. POSITIVE NUMERICAL INPUTS
    # --------------------------------------------------------

    positive_keys = [
        "wco_mass_flow_kg_h",
        "wco_cp_kj_kg_k",
        "wco_density_kg_m3",
        "wco_viscosity_pa_s",
        "design_factor",
        "overall_heat_transfer_coefficient_w_m2_k",
        "tube_outside_diameter_m",
        "tube_wall_thickness_m",
        "tube_length_m",
        "tube_count",
        "tube_passes",
        "shell_passes",
        "tube_pitch_m",
        "shell_internal_diameter_m",
        "shell_wall_thickness_m",
        "channel_head_length_m",
        "tubesheet_thickness_m",
        "design_pressure_bar",
        "corrosion_allowance_m",
        "minimum_tube_velocity_m_s",
        "maximum_tube_velocity_m_s",
    ]

    for key in positive_keys:
        value = data[key]

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} must be numeric.")

        if not math.isfinite(float(value)) or value <= 0:
            raise ValueError(
                f"{key} must be finite and greater than zero."
            )

    # --------------------------------------------------------
    # 2. TEMPERATURE INPUTS
    # Temperatures are entered in degrees Celsius.
    # Zero and negative Celsius values are valid.
    # --------------------------------------------------------

    temperature_keys = [
        "wco_inlet_temp_c",
        "wco_outlet_temp_c",
        "heating_medium_inlet_temp_c",
        "design_temperature_c",
    ]

    if data["heating_medium_mode"] == "sensible":
        temperature_keys.append(
            "heating_medium_outlet_temp_c"
        )

    for key in temperature_keys:
        value = data[key]

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f"{key} must be a numerical temperature in °C."
            )

        if not math.isfinite(float(value)):
            raise ValueError(
                f"{key} must be a finite temperature."
            )

    if data["wco_outlet_temp_c"] <= data["wco_inlet_temp_c"]:
        raise ValueError(
            "WCO outlet temperature must exceed inlet temperature."
        )

    # --------------------------------------------------------
    # 3. INTEGER INPUTS
    # --------------------------------------------------------

    integer_keys = [
        "tube_count",
        "tube_passes",
        "shell_passes",
        "baffle_count",
    ]

    for key in integer_keys:
        value = data[key]

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} must be a whole number.")

        if not math.isfinite(float(value)) or int(value) != value:
            raise ValueError(f"{key} must be a finite whole number.")

    if data["baffle_count"] < 0:
        raise ValueError("baffle_count cannot be negative.")

    # --------------------------------------------------------
    # 4. SUPPORTED SHELL-PASS CONFIGURATION
    # --------------------------------------------------------

    if data["shell_passes"] != 1:
        raise ValueError(
            "This calculation version supports one shell pass only. "
            "Multi-shell-pass correction-factor calculations "
            "have not yet been implemented."
        )

    if data["tube_passes"] > data["tube_count"]:
        if not data["auto_size_tubes"]:
            raise ValueError(
                "Tube passes cannot exceed tube count."
            )

    # --------------------------------------------------------
    # 5. TUBE AND SHELL GEOMETRY
    # --------------------------------------------------------

    if data["tube_outside_diameter_m"] <= (
        2 * data["tube_wall_thickness_m"]
    ):
        raise ValueError(
            "Tube wall thickness leaves no positive tube inside diameter."
        )

    if data["tube_pitch_m"] <= data["tube_outside_diameter_m"]:
        raise ValueError(
            "Tube pitch must exceed tube outside diameter."
        )

    if data["shell_internal_diameter_m"] <= (
        2 * data["shell_wall_thickness_m"]
    ):
        raise ValueError(
            "Shell wall thickness is too large for shell diameter."
        )

    if data["tube_layout"] not in ("triangular", "square"):
        raise ValueError(
            "tube_layout must be 'triangular' or 'square'."
        )

    # --------------------------------------------------------
    # 6. BAFFLE VALIDATION
    # --------------------------------------------------------

    baffle_cut = data["baffle_cut_fraction"]

    if (
        isinstance(baffle_cut, bool)
        or not isinstance(baffle_cut, (int, float))
        or not math.isfinite(float(baffle_cut))
    ):
        raise ValueError(
            "Baffle cut fraction must be a finite number."
        )

    if not 0.05 <= baffle_cut <= 0.45:
        raise ValueError(
            "Baffle cut fraction should be between 0.05 and 0.45."
        )

    # --------------------------------------------------------
    # 7. FLOW ARRANGEMENT
    # --------------------------------------------------------

    if data["flow_arrangement"] != "counter_current":
        raise ValueError(
            "This version currently supports counter-current "
            "temperature calculations only."
        )

    # --------------------------------------------------------
    # 8. HEATING-MEDIUM VALIDATION
    # --------------------------------------------------------

    mode = data["heating_medium_mode"]

    if mode == "sensible":

        positive_medium_keys = [
            "heating_medium_cp_kj_kg_k",
            "heating_medium_density_kg_m3",
            "heating_medium_viscosity_pa_s",
        ]

        for key in positive_medium_keys:
            value = data[key]

            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or value <= 0
            ):
                raise ValueError(
                    f"{key} must be finite and greater than zero."
                )

        if (
            data["heating_medium_inlet_temp_c"]
            <= data["heating_medium_outlet_temp_c"]
        ):
            raise ValueError(
                "Heating-medium inlet temperature must exceed "
                "its outlet temperature."
            )

    elif mode == "condensing":

        latent = data["heating_medium_latent_heat_kj_kg"]

        if (
            isinstance(latent, bool)
            or not isinstance(latent, (int, float))
            or not math.isfinite(float(latent))
            or latent <= 0
        ):
            raise ValueError(
                "Steam latent heat must be finite and greater than zero."
            )

    else:
        raise ValueError(
            f"Unsupported heating-medium calculation mode: {mode}"
        )

    # --------------------------------------------------------
    # 9. OPTIONAL HEATING-MEDIUM PRESSURE
    # --------------------------------------------------------

    pressure = data["heating_medium_pressure_bar"]

    if pressure is not None:
        if (
            isinstance(pressure, bool)
            or not isinstance(pressure, (int, float))
            or not math.isfinite(float(pressure))
            or pressure <= 0
        ):
            raise ValueError(
                "Heating-medium pressure must be positive and finite."
            )

    # --------------------------------------------------------
    # 10. FOULING RESISTANCE
    # --------------------------------------------------------

    fouling_keys = [
        "tube_fouling_resistance_m2_k_w",
        "shell_fouling_resistance_m2_k_w",
    ]

    for key in fouling_keys:
        value = data[key]

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or value < 0
        ):
            raise ValueError(
                f"{key} must be finite and cannot be negative."
            )

# =============================================================================
# 5. PROCESS DUTY AND DESIGN DUTY
# =============================================================================

def calculate_process_duty(data: Dict[str, Any]) -> Dict[str, float]:
    mass_flow_kg_s = data["wco_mass_flow_kg_h"] / 3600.0
    delta_t = data["wco_outlet_temp_c"] - data["wco_inlet_temp_c"]
    duty_w = mass_flow_kg_s * data["wco_cp_kj_kg_k"] * 1000.0 * delta_t

    return {
        "mass_flow_kg_s": mass_flow_kg_s,
        "temperature_change_k": delta_t,
        "process_duty_w": duty_w,
        "process_duty_kw": duty_w / 1000.0,
    }


def calculate_design_duty(data: Dict[str, Any], process: Dict[str, float]) -> Dict[str, float]:
    duty_w = process["process_duty_w"] * data["design_factor"]
    return {
        "design_duty_w": duty_w,
        "design_duty_kw": duty_w / 1000.0,
        "design_factor": data["design_factor"],
    }


# =============================================================================
# 6. HEATING-MEDIUM FLOW
# =============================================================================

def calculate_heating_medium_flow(
    data: Dict[str, Any],
    process: Dict[str, float],
    design: Dict[str, float],
) -> Dict[str, Any]:
    """Calculate mass flow for sensible media or condensing steam."""

    mode = data["heating_medium_mode"]
    actual_duty = process["process_duty_w"]
    design_duty = design["design_duty_w"]

    if mode == "sensible":
        delta_t = (
            data["heating_medium_inlet_temp_c"]
            - data["heating_medium_outlet_temp_c"]
        )
        cp_j_kg_k = data["heating_medium_cp_kj_kg_k"] * 1000.0

        actual_mass_flow = actual_duty / (cp_j_kg_k * delta_t)
        design_mass_flow = design_duty / (cp_j_kg_k * delta_t)
        method = "Sensible heat: Q = m_dot * Cp * delta_T"

    else:
        latent_j_kg = data["heating_medium_latent_heat_kj_kg"] * 1000.0
        actual_mass_flow = actual_duty / latent_j_kg
        design_mass_flow = design_duty / latent_j_kg
        delta_t = 0.0
        method = "Condensing steam: Q = m_dot * latent_heat"

    density = data["heating_medium_density_kg_m3"]
    actual_volume_flow = (
        actual_mass_flow / density if density not in (None, 0) else None
    )
    design_volume_flow = (
        design_mass_flow / density if density not in (None, 0) else None
    )

    return {
        "medium_name": data["heating_medium_name"],
        "calculation_mode": mode,
        "calculation_method": method,
        "temperature_change_k": delta_t,
        "actual_mass_flow_kg_s": actual_mass_flow,
        "actual_mass_flow_kg_h": actual_mass_flow * 3600.0,
        "design_mass_flow_kg_s": design_mass_flow,
        "design_mass_flow_kg_h": design_mass_flow * 3600.0,
        "actual_volume_flow_m3_h": (
            actual_volume_flow * 3600.0 if actual_volume_flow is not None else None
        ),
        "design_volume_flow_m3_h": (
            design_volume_flow * 3600.0 if design_volume_flow is not None else None
        ),
    }


# =============================================================================
# 7. TEMPERATURE DRIVING FORCE
# =============================================================================

def calculate_lmtd(data: Dict[str, Any]) -> Dict[str, float]:
    """
    Counter-current LMTD.

    Sensible medium:
      DT1 = Th,in - Tc,out
      DT2 = Th,out - Tc,in

    Condensing steam:
      The condensing temperature is treated as approximately constant.
      DT1 = Tsat - Tc,out
      DT2 = Tsat - Tc,in
    """
    tc_in = data["wco_inlet_temp_c"]
    tc_out = data["wco_outlet_temp_c"]

    if data["heating_medium_mode"] == "condensing":
        th_in = data["heating_medium_inlet_temp_c"]
        th_out = th_in
    else:
        th_in = data["heating_medium_inlet_temp_c"]
        th_out = data["heating_medium_outlet_temp_c"]

    dt1 = th_in - tc_out
    dt2 = th_out - tc_in

    if dt1 <= 0 or dt2 <= 0:
        raise ValueError(
            "No positive counter-current temperature driving force. "
            "The selected heating-medium temperatures cannot achieve "
            "the specified process outlet under this assumed arrangement."
        )

    if math.isclose(dt1, dt2, rel_tol=1e-10, abs_tol=1e-10):
        lmtd = dt1
    else:
        lmtd = (dt1 - dt2) / math.log(dt1 / dt2)

    return {
        "delta_t1_k": dt1,
        "delta_t2_k": dt2,
        "lmtd_k": lmtd,
    }


def calculate_correction_factor(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preliminary correction-factor treatment.

    For ideal isothermal condensation, Ft is provisionally set to 1.0.
    For sensible heating, the current analytical one-shell-pass relation
    is evaluated. This is a screening approximation and must be verified
    using an accepted exchanger design method before final design.
    """
    if data["heating_medium_mode"] == "condensing":
        return {
            "R": None,
            "P": None,
            "correction_factor": 1.0,
            "method": "Ideal isothermal condensation approximation",
        }

    hot_change = (
        data["heating_medium_inlet_temp_c"]
        - data["heating_medium_outlet_temp_c"]
    )
    cold_change = (
        data["wco_outlet_temp_c"] - data["wco_inlet_temp_c"]
    )
    denominator = (
        data["heating_medium_inlet_temp_c"] - data["wco_inlet_temp_c"]
    )

    if denominator <= 0 or cold_change <= 0:
        raise ValueError("Invalid temperatures for correction-factor calculation.")

    r_value = hot_change / cold_change
    p_value = cold_change / denominator

    if not 0 < p_value < 1:
        raise ValueError("Correction-factor parameter P is outside its valid range.")

    if math.isclose(r_value, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError("Correction-factor relation is singular at R = 1.")

    root = math.sqrt(r_value * r_value + 1.0)
    term_a = (1.0 - p_value) / (1.0 - p_value * r_value)
    term_b = 2.0 - p_value * (r_value + 1.0 - root)
    term_c = 2.0 - p_value * (r_value + 1.0 + root)

    if term_a <= 0 or term_b <= 0 or term_c <= 0:
        raise ValueError("Invalid logarithm argument in correction-factor calculation.")

    denominator_log = math.log(term_b / term_c)
    if abs(denominator_log) < 1e-12:
        raise ValueError("Correction-factor denominator is too small.")

    numerator_log = math.log(term_a)
    ft = (root / (r_value - 1.0)) * (numerator_log / denominator_log)

    if not 0 < ft <= 1:
        raise ValueError(
            "Calculated correction factor is outside 0 to 1. "
            "Review the temperature program and exchanger arrangement."
        )

    return {
        "R": r_value,
        "P": p_value,
        "correction_factor": ft,
        "method": "Preliminary one-shell-pass analytical relation",
    }


# =============================================================================
# 8. REQUIRED AREA AND AUTOMATIC TUBE COUNT
# =============================================================================

def calculate_required_area(
    data: Dict[str, Any],
    design: Dict[str, float],
    lmtd: Dict[str, float],
    correction: Dict[str, Any],
) -> Dict[str, float]:
    corrected_lmtd = lmtd["lmtd_k"] * correction["correction_factor"]
    required_area = design["design_duty_w"] / (
        data["overall_heat_transfer_coefficient_w_m2_k"] * corrected_lmtd
    )

    return {
        "corrected_lmtd_k": corrected_lmtd,
        "required_area_m2": required_area,
    }


def calculate_automatic_tube_count(data: Dict[str, Any], area: Dict[str, float]) -> Dict[str, Any]:
    """
    Estimate minimum tube count from required outside surface area.

    N_min = A_required / (pi * Do * L)

    Tube count is rounded upward to a multiple of tube passes so that
    an equal number of tubes can be allocated to each pass.

    This is a thermal area estimate only. Hydraulic and bundle-fit
    checks are performed separately.
    """
    do = data["tube_outside_diameter_m"]
    length = data["tube_length_m"]
    passes = int(data["tube_passes"])

    area_per_tube = math.pi * do * length
    raw_required = area["required_area_m2"] / area_per_tube
    minimum_integer = math.ceil(raw_required)

    selected_count = (
        math.ceil(minimum_integer / passes) * passes
        if data["auto_size_tubes"]
        else int(data["tube_count"])
    )

    installed_area = selected_count * area_per_tube

    return {
        "area_per_tube_m2": area_per_tube,
        "raw_required_tube_count": raw_required,
        "minimum_whole_tube_count": minimum_integer,
        "selected_tube_count": selected_count,
        "tubes_per_pass": selected_count / passes,
        "installed_area_m2": installed_area,
        "area_margin_m2": installed_area - area["required_area_m2"],
        "automatically_sized": bool(data["auto_size_tubes"]),
    }


# =============================================================================
# 9. TUBE-SIDE HYDRAULICS
# =============================================================================

def calculate_tube_side_hydraulics(
    data: Dict[str, Any],
    process: Dict[str, float],
    tube_sizing: Dict[str, Any],
) -> Dict[str, Any]:
    tube_id = (
        data["tube_outside_diameter_m"]
        - 2.0 * data["tube_wall_thickness_m"]
    )

    tubes_per_pass = tube_sizing["tubes_per_pass"]
    single_tube_area = math.pi * tube_id ** 2 / 4.0
    total_flow_area = tubes_per_pass * single_tube_area

    volume_flow = process["mass_flow_kg_s"] / data["wco_density_kg_m3"]
    velocity = volume_flow / total_flow_area

    reynolds = (
        data["wco_density_kg_m3"] * velocity * tube_id
        / data["wco_viscosity_pa_s"]
    )

    if reynolds < 2300:
        regime = "Laminar"
    elif reynolds < 4000:
        regime = "Transitional"
    else:
        regime = "Turbulent"

    return {
        "tube_inside_diameter_m": tube_id,
        "tubes_per_pass": tubes_per_pass,
        "single_tube_flow_area_m2": single_tube_area,
        "total_flow_area_per_pass_m2": total_flow_area,
        "wco_volume_flow_m3_s": volume_flow,
        "wco_tube_velocity_m_s": velocity,
        "wco_reynolds_number": reynolds,
        "flow_regime": regime,
        "pressure_drop_calculated": False,
    }


# =============================================================================
# 10. PRELIMINARY BUNDLE AND SHELL FIT
# =============================================================================

def calculate_bundle_geometry(data: Dict[str, Any], tube_sizing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estimate a circular envelope for the tube array.

    This is a rough packing estimate, not a detailed tube-layout or
    TEMA bundle-diameter calculation. It omits pass lanes, peripheral
    clearances, sealing strips, tie rods, baffle-hole clearances and
    fabrication tolerances.
    """
    n_tubes = int(tube_sizing["selected_tube_count"])
    pitch = data["tube_pitch_m"]
    do = data["tube_outside_diameter_m"]

    if data["tube_layout"] == "triangular":
        cell_area = (math.sqrt(3.0) / 2.0) * pitch ** 2
    else:
        cell_area = pitch ** 2

    occupied_area_estimate = n_tubes * cell_area
    equivalent_diameter = math.sqrt(4.0 * occupied_area_estimate / math.pi)

    # Add one tube diameter as a simple edge allowance.
    estimated_bundle_diameter = equivalent_diameter + do

    shell_id = data["shell_internal_diameter_m"]
    radial_clearance = (shell_id - estimated_bundle_diameter) / 2.0

    return {
        "tube_layout": data["tube_layout"],
        "tube_pitch_m": pitch,
        "estimated_bundle_diameter_m": estimated_bundle_diameter,
        "shell_internal_diameter_m": shell_id,
        "estimated_radial_clearance_m": radial_clearance,
        "estimated_bundle_fits": estimated_bundle_diameter < shell_id,
        "method": "Simplified packing-envelope estimate; not TEMA sizing",
    }


def calculate_geometry(
    data: Dict[str, Any],
    tube_sizing: Dict[str, Any],
    bundle: Dict[str, Any],
) -> Dict[str, Any]:
    shell_id = data["shell_internal_diameter_m"]
    shell_wall = data["shell_wall_thickness_m"]
    shell_od = shell_id + 2.0 * shell_wall
    tube_od = data["tube_outside_diameter_m"]
    tube_id = tube_od - 2.0 * data["tube_wall_thickness_m"]
    tube_length = data["tube_length_m"]

    baffle_spacing = (
        tube_length / (data["baffle_count"] + 1)
        if data["baffle_count"] > 0 else tube_length
    )

    total_length = (
        tube_length
        + 2.0 * data["channel_head_length_m"]
        + 2.0 * data["tubesheet_thickness_m"]
    )

    return {
        "shell_internal_diameter_m": shell_id,
        "shell_external_diameter_m": shell_od,
        "shell_wall_thickness_m": shell_wall,
        "tube_outside_diameter_m": tube_od,
        "tube_inside_diameter_m": tube_id,
        "tube_length_m": tube_length,
        "tube_count": tube_sizing["selected_tube_count"],
        "tube_passes": int(data["tube_passes"]),
        "shell_passes": int(data["shell_passes"]),
        "tube_pitch_m": data["tube_pitch_m"],
        "tube_layout": data["tube_layout"],
        "estimated_bundle_diameter_m": bundle["estimated_bundle_diameter_m"],
        "baffle_count": int(data["baffle_count"]),
        "baffle_spacing_m": baffle_spacing,
        "baffle_cut_fraction": data["baffle_cut_fraction"],
        "channel_head_length_m": data["channel_head_length_m"],
        "tubesheet_thickness_m": data["tubesheet_thickness_m"],
        "exchanger_total_length_m": total_length,
        "installed_tube_area_m2": tube_sizing["installed_area_m2"],
    }


# =============================================================================
# 11. FEASIBILITY ASSESSMENT
# =============================================================================

def assess_feasibility(
    data: Dict[str, Any],
    lmtd: Dict[str, Any],
    area: Dict[str, Any],
    tube_sizing: Dict[str, Any],
    hydraulics: Dict[str, Any],
    bundle: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Classify implemented checks as PASS, WARNING, FAIL or NOT_ASSESSED.

    Overall:
      INFEASIBLE: at least one hard failure.
      CONDITIONAL: no hard failure, but warnings or unassessed critical items.
      FEASIBLE_SCREENING: all implemented screening checks pass.
    """
    checks = []

    def add(name: str, status: str, finding: str, recommendation: str = "") -> None:
        checks.append({
            "check": name,
            "status": status,
            "finding": finding,
            "recommendation": recommendation,
        })

    # Temperature approach
    min_approach = min(lmtd["delta_t1_k"], lmtd["delta_t2_k"])
    if min_approach <= 0:
        add("Temperature feasibility", "FAIL", "A temperature difference is zero or negative.")
    elif min_approach < 5.0:
        add(
            "Temperature approach",
            "WARNING",
            f"Minimum terminal approach is only {min_approach:.2f} K.",
            "Review heating-medium temperature, exchanger area and process target.",
        )
    else:
        add(
            "Temperature feasibility",
            "PASS",
            f"Both terminal temperature differences are positive; minimum is {min_approach:.2f} K.",
        )

    # Thermal area
    if tube_sizing["installed_area_m2"] + 1e-12 < area["required_area_m2"]:
        add(
            "Heat-transfer area",
            "FAIL",
            "Installed area is below calculated required area.",
            "Increase tube count, tube length or tube diameter, or review U and process conditions.",
        )
    else:
        add(
            "Heat-transfer area",
            "PASS",
            f"Installed area {tube_sizing['installed_area_m2']:.3f} m2 "
            f">= required area {area['required_area_m2']:.3f} m2.",
        )

    # Tube pass distribution
    if int(tube_sizing["selected_tube_count"]) % int(data["tube_passes"]) != 0:
        add(
            "Tube-pass distribution",
            "FAIL",
            "Tube count cannot be divided equally among the selected passes.",
            "Change tube count or number of passes.",
        )
    else:
        add(
            "Tube-pass distribution",
            "PASS",
            f"{tube_sizing['tubes_per_pass']:.0f} tubes per pass.",
        )

    # Tube velocity
    velocity = hydraulics["wco_tube_velocity_m_s"]
    if velocity < data["minimum_tube_velocity_m_s"]:
        add(
            "Tube-side velocity",
            "WARNING",
            f"Velocity {velocity:.3f} m/s is below the configured screening minimum "
            f"{data['minimum_tube_velocity_m_s']:.3f} m/s.",
            "Review tube passes, tube count, fouling tendency and an appropriate velocity range for WCO.",
        )
    elif velocity > data["maximum_tube_velocity_m_s"]:
        add(
            "Tube-side velocity",
            "WARNING",
            f"Velocity {velocity:.3f} m/s exceeds the configured screening maximum "
            f"{data['maximum_tube_velocity_m_s']:.3f} m/s.",
            "Review tube passes and calculate pressure drop before accepting the design.",
        )
    else:
        add(
            "Tube-side velocity",
            "PASS",
            f"Velocity {velocity:.3f} m/s is within the configured screening range.",
        )

    # Flow regime
    if hydraulics["flow_regime"] == "Laminar":
        add(
            "Tube-side flow regime",
            "WARNING",
            f"Estimated flow is laminar (Re = {hydraulics['wco_reynolds_number']:.0f}).",
            "Use an appropriate laminar heat-transfer correlation and reassess U.",
        )
    elif hydraulics["flow_regime"] == "Transitional":
        add(
            "Tube-side flow regime",
            "WARNING",
            f"Estimated flow is transitional (Re = {hydraulics['wco_reynolds_number']:.0f}).",
            "Use a correlation suitable for the transitional regime.",
        )
    else:
        add(
            "Tube-side flow regime",
            "PASS",
            f"Estimated flow is turbulent (Re = {hydraulics['wco_reynolds_number']:.0f}).",
        )

    # Bundle fit
    if not bundle["estimated_bundle_fits"]:
        add(
            "Bundle/shell fit",
            "FAIL",
            "The simplified estimated bundle envelope exceeds the selected shell internal diameter.",
            "Increase shell diameter or revise tube count, pitch or layout. Confirm with a detailed bundle design.",
        )
    else:
        add(
            "Bundle/shell fit",
            "WARNING",
            "The simplified bundle envelope fits, but detailed TEMA clearances and pass lanes are not checked.",
            "Perform a detailed tube-layout and bundle-diameter calculation.",
        )

    # Heating medium property validation
    add(
        "Heating-medium properties",
        "WARNING",
        data["heating_medium_property_note"],
        "Replace illustrative properties with validated data at operating temperature, pressure and composition.",
    )

    # Pressure drop
    add(
        "Pressure drop",
        "NOT_ASSESSED",
        "Tube-side and shell-side pressure drops are not calculated in this version.",
        "Add friction, fittings, baffle-window, crossflow and nozzle-loss calculations.",
    )

    # Shell-side heat transfer
    add(
        "Shell-side heat transfer",
        "NOT_ASSESSED",
        "Shell-side film coefficient and detailed overall U are not calculated.",
        "Add a suitable shell-side rating method and verify the selected U.",
    )

    # Mechanical design
    add(
        "Mechanical integrity",
        "NOT_ASSESSED",
        "Shell, heads, tubesheet, flanges, nozzles and supports have not been mechanically designed.",
        "Perform applicable pressure-vessel and exchanger mechanical design checks.",
    )

    # Material compatibility
    add(
        "Material compatibility",
        "NOT_ASSESSED",
        f"Construction material entered: {data['construction_material']}. Compatibility has not been verified.",
        "Check corrosion, erosion, temperature limits and compatibility with WCO and selected heating medium.",
    )

    # Shell count
    add(
        "Number of shells",
        "NOT_ASSESSED",
        "The module assumes one shell and does not automatically size parallel or series shells.",
        "Evaluate multiple shells only after thermal rating, pressure drop and flow arrangement are implemented.",
    )

    statuses = {item["status"] for item in checks}
    if "FAIL" in statuses:
        overall = "INFEASIBLE"
    elif "WARNING" in statuses or "NOT_ASSESSED" in statuses:
        overall = "CONDITIONAL"
    else:
        overall = "FEASIBLE_SCREENING"

    return {
        "overall_status": overall,
        "checks": checks,
        "hard_failures": sum(1 for c in checks if c["status"] == "FAIL"),
        "warnings": sum(1 for c in checks if c["status"] == "WARNING"),
        "not_assessed": sum(1 for c in checks if c["status"] == "NOT_ASSESSED"),
        "interpretation": (
            "INFEASIBLE: one or more implemented constraints failed."
            if overall == "INFEASIBLE"
            else "CONDITIONAL: no hard failure was found, but warnings or important unassessed items remain."
            if overall == "CONDITIONAL"
            else "FEASIBLE_SCREENING: implemented screening checks passed; this is not design-code approval."
        ),
    }


# =============================================================================
# 12. MAIN DESIGN FUNCTION
# =============================================================================

def calculate_design(user_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main E-102 entry point.

    Examples
    --------
    result = calculate_design()

    result = calculate_design({
        "wco_mass_flow_kg_h": 150.0,
        "wco_outlet_temp_c": 65.0,
        "heating_medium_type": "thermal_oil",
    })

    result = calculate_design({
        "heating_medium_type": "steam",
        "heating_medium_inlet_temp_c": 120.0,
        "heating_medium_latent_heat_kj_kg": 2201.0,
        "heating_medium_pressure_bar": 2.0,
    })

    For sensible media, optional overrides include:
      heating_medium_inlet_temp_c
      heating_medium_outlet_temp_c
      heating_medium_cp_kj_kg_k
      heating_medium_density_kg_m3
      heating_medium_viscosity_pa_s
    """
    data = prepare_inputs(user_inputs)
    validate_inputs(data)

    process = calculate_process_duty(data)
    design = calculate_design_duty(data, process)

    heating_medium = calculate_heating_medium_flow(data, process, design)
    lmtd = calculate_lmtd(data)
    correction = calculate_correction_factor(data)
    area = calculate_required_area(data, design, lmtd, correction)

    tube_sizing = calculate_automatic_tube_count(data, area)
    hydraulics = calculate_tube_side_hydraulics(data, process, tube_sizing)
    bundle = calculate_bundle_geometry(data, tube_sizing)
    geometry = calculate_geometry(data, tube_sizing, bundle)

    feasibility = assess_feasibility(
        data, lmtd, area, tube_sizing, hydraulics, bundle
    )

    return {
        "equipment_tag": "E-102",
        "service": f"{data['process_fluid_name']} heating",
        "inputs": data,
        "process": process,
        "design": design,
        "heating_medium": heating_medium,
        "lmtd": lmtd,
        "correction": correction,
        "area": area,
        "tube_sizing": tube_sizing,
        "hydraulics": hydraulics,
        "bundle": bundle,
        "geometry": geometry,
        "feasibility": feasibility,
    }


# =============================================================================
# 13. ENGINEERING REPORT
# =============================================================================

def print_design_report(result: Dict[str, Any]) -> None:
    data = result["inputs"]
    print("\n" + "=" * 76)
    print("E-102 SHELL-AND-TUBE HEAT EXCHANGER")
    print("PRELIMINARY ENGINEERING CALCULATION REPORT")
    print("=" * 76)

    print("\nPROCESS DUTY")
    print("-" * 76)
    print(f"Process fluid                 : {data['process_fluid_name']}")
    print(f"Process mass flow             : {data['wco_mass_flow_kg_h']:.3f} kg/h")
    print(f"Process inlet temperature     : {data['wco_inlet_temp_c']:.2f} deg C")
    print(f"Process outlet temperature    : {data['wco_outlet_temp_c']:.2f} deg C")
    print(f"Process heat duty             : {result['process']['process_duty_kw']:.3f} kW")
    print(f"Design heat duty              : {result['design']['design_duty_kw']:.3f} kW")
    print(f"Design factor                 : {data['design_factor']:.3f}")

    print("\nHEATING MEDIUM")
    print("-" * 76)
    print(f"Selected medium               : {data['heating_medium_name']}")
    print(f"Calculation mode              : {data['heating_medium_mode']}")
    print(f"Heating-medium inlet          : {data['heating_medium_inlet_temp_c']:.2f} deg C")
    if data["heating_medium_mode"] == "sensible":
        print(f"Heating-medium outlet         : {data['heating_medium_outlet_temp_c']:.2f} deg C")
    else:
        print("Heating-medium outlet         : Condensate condition not modelled")
        print(f"Latent heat                   : {data['heating_medium_latent_heat_kj_kg']:.2f} kJ/kg")
    print(f"Actual medium flow            : {result['heating_medium']['actual_mass_flow_kg_h']:.3f} kg/h")
    print(f"Design medium flow            : {result['heating_medium']['design_mass_flow_kg_h']:.3f} kg/h")
    if result["heating_medium"]["actual_volume_flow_m3_h"] is not None:
        print(f"Actual volume flow            : {result['heating_medium']['actual_volume_flow_m3_h']:.5f} m3/h")
    print(f"Property note                 : {data['heating_medium_property_note']}")

    print("\nTHERMAL DESIGN")
    print("-" * 76)
    print(f"Terminal temperature diff. 1 : {result['lmtd']['delta_t1_k']:.3f} K")
    print(f"Terminal temperature diff. 2 : {result['lmtd']['delta_t2_k']:.3f} K")
    print(f"LMTD                          : {result['lmtd']['lmtd_k']:.3f} K")
    print(f"Correction factor             : {result['correction']['correction_factor']:.4f}")
    print(f"Correction method             : {result['correction']['method']}")
    print(f"Corrected LMTD                : {result['area']['corrected_lmtd_k']:.3f} K")
    print(f"Assumed overall U             : {data['overall_heat_transfer_coefficient_w_m2_k']:.2f} W/m2.K")
    print(f"Required heat-transfer area   : {result['area']['required_area_m2']:.4f} m2")

    print("\nTUBE SIZING")
    print("-" * 76)
    print(f"Automatic tube sizing         : {result['tube_sizing']['automatically_sized']}")
    print(f"Raw calculated tube count     : {result['tube_sizing']['raw_required_tube_count']:.3f}")
    print(f"Minimum whole tube count      : {result['tube_sizing']['minimum_whole_tube_count']}")
    print(f"Selected tube count           : {result['tube_sizing']['selected_tube_count']}")
    print(f"Tube passes                   : {data['tube_passes']}")
    print(f"Tubes per pass                : {result['tube_sizing']['tubes_per_pass']:.0f}")
    print(f"Area per tube                 : {result['tube_sizing']['area_per_tube_m2']:.5f} m2")
    print(f"Installed tube area           : {result['tube_sizing']['installed_area_m2']:.4f} m2")
    print(f"Area margin                   : {result['tube_sizing']['area_margin_m2']:.4f} m2")

    print("\nTUBE-SIDE HYDRAULIC SCREENING")
    print("-" * 76)
    print(f"Tube inside diameter          : {result['hydraulics']['tube_inside_diameter_m'] * 1000:.3f} mm")
    print(f"WCO velocity                  : {result['hydraulics']['wco_tube_velocity_m_s']:.4f} m/s")
    print(f"Reynolds number               : {result['hydraulics']['wco_reynolds_number']:.1f}")
    print(f"Flow regime                   : {result['hydraulics']['flow_regime']}")
    print("Pressure drop                 : NOT CALCULATED")

    print("\nPRELIMINARY GEOMETRY")
    print("-" * 76)
    print(f"Shell internal diameter       : {result['geometry']['shell_internal_diameter_m'] * 1000:.2f} mm")
    print(f"Shell external diameter       : {result['geometry']['shell_external_diameter_m'] * 1000:.2f} mm")
    print(f"Tube outside diameter         : {result['geometry']['tube_outside_diameter_m'] * 1000:.2f} mm")
    print(f"Tube length                   : {result['geometry']['tube_length_m']:.3f} m")
    print(f"Tube layout                   : {result['geometry']['tube_layout']}")
    print(f"Tube pitch                    : {result['geometry']['tube_pitch_m'] * 1000:.2f} mm")
    print(f"Estimated bundle diameter     : {result['bundle']['estimated_bundle_diameter_m'] * 1000:.2f} mm")
    print(f"Estimated bundle fits shell   : {result['bundle']['estimated_bundle_fits']}")
    print(f"Baffle count                  : {result['geometry']['baffle_count']}")
    print(f"Baffle spacing                : {result['geometry']['baffle_spacing_m']:.3f} m")
    print(f"Baffle cut                    : {result['geometry']['baffle_cut_fraction']:.3f}")
    print(f"Approx. exchanger length      : {result['geometry']['exchanger_total_length_m']:.3f} m")

    print("\nFEASIBILITY ASSESSMENT")
    print("-" * 76)
    print(f"OVERALL STATUS                : {result['feasibility']['overall_status']}")
    print(result["feasibility"]["interpretation"])
    print(
        f"Failures: {result['feasibility']['hard_failures']} | "
        f"Warnings: {result['feasibility']['warnings']} | "
        f"Not assessed: {result['feasibility']['not_assessed']}"
    )

    for item in result["feasibility"]["checks"]:
        print(f"\n[{item['status']}] {item['check']}")
        print(f"  {item['finding']}")
        if item["recommendation"]:
            print(f"  Action: {item['recommendation']}")

    print("\n" + "=" * 76)
    print("ENGINEERING LIMITATION")
    print(
        "This is a preliminary screening calculation, not a certified "
        "thermal rating, TEMA design or ASME mechanical design."
    )
    print("=" * 76)


# =============================================================================
# 14. EXAMPLE TESTS
# =============================================================================

def run_example_tests() -> None:
    """Run one example for each heating-medium option."""
    for medium_key in HEATING_MEDIUMS:
        print("\n\n" + "#" * 76)
        print(f"TESTING HEATING MEDIUM: {medium_key}")
        print("#" * 76)
        try:
            result = calculate_design({"heating_medium_type": medium_key})
            print_design_report(result)
        except (ValueError, KeyError, TypeError) as exc:
            print(f"Calculation could not be completed: {exc}")


if __name__ == "__main__":
    result = calculate_design()
    print_design_report(result)

    # To test every heating medium, comment out the two lines above
    # and uncomment the following line:
    # run_example_tests()
