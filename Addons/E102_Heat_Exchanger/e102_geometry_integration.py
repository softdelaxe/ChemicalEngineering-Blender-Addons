"""
E-102 calculation-to-geometry integration.

Place this file beside calculation.py and geometry.py in the E-102 package.
It keeps the original geometry.build_geometry() API intact and adds:

    build_from_calculation(user_inputs=None, ...)

The calculation module supplies dimensions; geometry.py creates the Blender
objects. This is a visualization integration, not mechanical-code design.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

from . import calculations as calculation
from . import geometry


PLATFORM_THICKNESS_M = 0.050
PLATFORM_LENGTH_MARGIN_M = 0.600
PLATFORM_WIDTH_FACTOR = 1.60
PLATFORM_MIN_WIDTH_M = 0.800
PLATFORM_EDGE_MARGIN_M = 0.100
PLATFORM_SUPPORT_CLEARANCE_M = 0.002


def _medium_label(inputs: Dict[str, Any]) -> str:
    """Return a readable service label from the selected heating medium."""
    medium_type = str(inputs.get("heating_medium_type", "hot_water"))
    custom_name = inputs.get("heating_medium_name")
    if custom_name:
        return str(custom_name).replace("_", " ").upper()

    labels = {
        "hot_water": "HOT WATER",
        "steam": "STEAM",
        "thermal_oil": "THERMAL OIL",
        "glycol_water": "GLYCOL-WATER",
        "hot_air": "HOT AIR",
        "flue_gas": "FLUE GAS",
        "molten_salt": "MOLTEN SALT",
    }
    return labels.get(medium_type, medium_type.replace("_", " ").upper())


def create_foundation_platform(
    shell_diameter_m: float,
    shell_length_m: float,
    channel_head_length_m: float,
    collection=None,
    material_dict=None,
    thickness_m: float = PLATFORM_THICKNESS_M,
    shell_wall_thickness_m: float = 0.004,
):
    """
    Create a single flat rectangular steel foundation/platform under E-102.

    The existing saddle base plates sit on the top face. The platform is
    deliberately a visualization/supporting skid plate, not a civil or
    structural foundation design.
    """
    if thickness_m <= 0:
        raise ValueError("Platform thickness must be positive.")

    shell_outer_radius = (
        shell_diameter_m / 2.0
        + shell_wall_thickness_m
    )

    # geometry.create_supports() currently uses:
    # support_height = 0.18 m; support_thickness = 0.012 m.
    support_height = 0.18
    support_base_thickness = 0.012

    support_base_bottom_z = (
        -shell_outer_radius
        - support_height
        - support_base_thickness / 2.0
    )
    platform_top_z = (
        support_base_bottom_z + PLATFORM_SUPPORT_CLEARANCE_M
    )
    platform_center_z = platform_top_z - thickness_m / 2.0

    # Include both hemispherical heads plus a practical perimeter margin.
    # Hemispherical head axial projection is its outer radius.
    total_equipment_length = (
        shell_length_m
        + 2.0 * (shell_outer_radius + PLATFORM_EDGE_MARGIN_M)
    )
    platform_length = total_equipment_length + PLATFORM_LENGTH_MARGIN_M

    platform_width = max(
        PLATFORM_MIN_WIDTH_M,
        shell_diameter_m * PLATFORM_WIDTH_FACTOR
    )

    platform = geometry.create_box(
        name="E102_Foundation_Platform",
        location=(0.0, 0.0, platform_center_z),
        dimensions=(platform_length, platform_width, thickness_m),
        collection=collection,
    )

    geometry.assign_component_material(
        platform,
        material_dict,
        "platform",
        "base_plate",
        "support",
        "dark_steel",
        "stainless_steel",
    )

    geometry.set_component_metadata(
        platform,
        "foundation_platform",
        platform_length_m=platform_length,
        platform_width_m=platform_width,
        platform_thickness_m=thickness_m,
        platform_top_z_m=platform_top_z,
        platform_bottom_z_m=platform_center_z - thickness_m / 2.0,
        support_contact="saddle_base_plates",
        structural_design_validated=False,
        purpose="visualization_and_equipment_base",
    )

    return platform


def _apply_heating_medium_labels(
    built: Dict[str, Any],
    medium_label: str,
    medium_type: str,
):
    """Replace hard-coded hot-water names and labels with selected service."""
    token = "".join(
        character if character.isalnum() else "_"
        for character in medium_type.upper()
    ).strip("_")

    for obj in built.get("shell_nozzles", []):
        old_name = obj.name
        if "HotWater" in old_name:
            obj.name = old_name.replace("HotWater", token.title())
        if obj.get("fluid_service") == "hot_water":
            obj["fluid_service"] = medium_type
        obj["fluid_service_label"] = medium_label

    for obj in built.get("labels", []):
        if obj.type == "FONT" and "SHELL SIDE" in obj.data.body:
            obj.data.body = f"SHELL SIDE - {medium_label}"

    return built


def build_from_calculation(
    user_inputs: Optional[Dict[str, Any]] = None,
    *,
    collection=None,
    material_dict=None,
    clear_existing: bool = True,
    create_platform: bool = True,
    platform_thickness_m: float = PLATFORM_THICKNESS_M,
):
    """
    Calculate E-102, then build geometry from the calculated dimensions.

    Parameters
    ----------
    user_inputs:
        Overrides accepted by calculation.calculate_design().
    clear_existing:
        Clear the E-102 collection before rebuilding.
    create_platform:
        Add a flat rectangular base plate beneath the saddle base plates.

    Returns
    -------
    dict with:
        calculation: complete calculation result
        geometry: generated Blender objects
        platform: platform object (or None)
        geometry_inputs: dimensions passed to geometry.build_geometry()
    """
    result = calculation.calculate_design(user_inputs)
    dims = result["geometry"]
    inputs = result["inputs"]

    if clear_existing:
        geometry.clear_equipment()

    # The shell barrel length is the tube length. Do not use the overall
    # exchanger length here, because that already includes the heads/sheets.
    build_args = {
        "shell_diameter": dims["shell_internal_diameter_m"],
        "shell_length": dims["tube_length_m"],
        "shell_wall_thickness": dims["shell_wall_thickness_m"],
        "tube_outside_diameter": dims["tube_outside_diameter_m"],
        "tube_wall_thickness": inputs["tube_wall_thickness_m"],
        "tube_length": dims["tube_length_m"],
        "number_of_tubes": dims["tube_count"],
        "tube_pitch": dims["tube_pitch_m"],
        "tube_passes": dims["tube_passes"],
        "shell_passes": dims["shell_passes"],
        # geometry.py constructs hemispherical heads whose axial depth is
        # their radius. The supplied calculation head length is recorded,
        # but is not currently used to control the dome profile.
        "channel_head_length": dims["channel_head_length_m"],
        "tubesheet_thickness": dims["tubesheet_thickness_m"],
        "baffle_count": dims["baffle_count"],
        "baffle_cut_fraction": dims["baffle_cut_fraction"],
        "collection": collection,
        "material_dict": material_dict,
    }

    built = geometry.build_geometry(**build_args)

    medium_type = str(inputs.get("heating_medium_type", "hot_water"))
    medium_label = _medium_label(inputs)
    _apply_heating_medium_labels(built, medium_label, medium_type)

    platform = None
    if create_platform:
        platform = create_foundation_platform(
            shell_diameter_m=dims["shell_internal_diameter_m"],
            shell_length_m=dims["tube_length_m"],
            channel_head_length_m=dims["channel_head_length_m"],
            collection=collection,
            material_dict=material_dict,
            thickness_m=platform_thickness_m,
            shell_wall_thickness_m=dims["shell_wall_thickness_m"],
        )
        built["platform"] = platform
    else:
        built["platform"] = None

    # Record the calculation/design linkage on the shell and platform.
    shell = built.get("shell")
    if shell is not None:
        shell["calculation_geometry_linked"] = True
        shell["calculation_tube_count"] = int(dims["tube_count"])
        shell["calculation_installed_area_m2"] = float(
            dims["installed_tube_area_m2"]
        )
        shell["calculation_heating_medium"] = medium_type
        shell["calculation_status"] = result["feasibility"]["overall_status"]
        shell["calculation_shell_passes_assumed"] = int(dims["shell_passes"])

    if platform is not None:
        platform["equipment_tag"] = result["equipment_tag"]
        platform["calculation_status"] = result["feasibility"]["overall_status"]

    return {
        "calculation": result,
        "geometry": built,
        "platform": platform,
        "geometry_inputs": build_args,
    }


def build_default_e102(**kwargs):
    """Convenience entry point using the calculation module's default inputs."""
    return build_from_calculation(user_inputs=None, **kwargs)
