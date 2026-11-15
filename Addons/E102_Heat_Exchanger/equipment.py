
"""
E-102 SHELL-AND-TUBE HEAT EXCHANGER
equipment.py

Coordinates the engineering properties and geometry modules.

Responsibilities:
    - Read dimensions from the Blender scene.
    - Validate the exchanger dimensions.
    - Build the complete exchanger.
    - Manage equipment cleanup.
    - Return generated component references.

This module does not perform engineering calculations.
"""

import bpy
import traceback

from . import geometry
from . import utilities
from . import materials as material_library


# ============================================================
# MODULE SETTINGS
# ============================================================

EQUIPMENT_COLLECTION = "E102_Heat_Exchanger"

DEFAULTS = {
    "shell_internal_diameter_m": 0.200,
    "shell_wall_thickness_m": 0.004,

    "tube_outside_diameter_m": 0.0127,
    "tube_wall_thickness_m": 0.0009,
    "tube_length_m": 1.5,
    "number_of_tubes": 16,
    "tube_pitch_m": 0.019,

    "tube_passes": 4,
    "shell_passes": 1,

    "channel_head_length_m": 0.180,
    "tubesheet_thickness_m": 0.025,

    "baffle_count": 4,
    "baffle_cut_fraction": 0.25,
}


# ============================================================
# PROPERTY ACCESS
# ============================================================

def get_design_properties(scene=None):
    """
    Retrieve the E-102 property group from the scene.
    """

    if scene is None:
        scene = bpy.context.scene

    properties = getattr(scene, "e102_design", None)

    if properties is None:
        raise RuntimeError(
            "E-102 design properties were not found. "
            "Check that properties.py is registered."
        )

    return properties


def get_value(properties, property_name, default=None):
    """
    Safely retrieve a property from the Blender property group.
    """

    if hasattr(properties, property_name):
        value = getattr(properties, property_name)

        if value is not None:
            return value

    if default is not None:
        return default

    raise AttributeError(
        f"Missing E-102 property: {property_name}"
    )


# ============================================================
# DIMENSION RETRIEVAL
# ============================================================

def get_equipment_dimensions(scene=None):
    """
    Retrieve all equipment dimensions from scene.e102_design.

    Returns a dictionary in metres unless otherwise stated.
    """

    properties = get_design_properties(scene)

    dimensions = {
        "shell_diameter": get_value(
            properties,
            "shell_internal_diameter_m",
            DEFAULTS["shell_internal_diameter_m"]
        ),

        "shell_wall_thickness": get_value(
            properties,
            "shell_wall_thickness_m",
            DEFAULTS["shell_wall_thickness_m"]
        ),

        "tube_diameter": get_value(
            properties,
            "tube_outside_diameter_m",
            DEFAULTS["tube_outside_diameter_m"]
        ),

        "tube_wall_thickness": get_value(
            properties,
            "tube_wall_thickness_m",
            DEFAULTS["tube_wall_thickness_m"]
        ),

        "tube_length": get_value(
            properties,
            "tube_length_m",
            DEFAULTS["tube_length_m"]
        ),

        "number_of_tubes": get_value(
            properties,
            "number_of_tubes",
            DEFAULTS["number_of_tubes"]
        ),

        "tube_pitch": get_value(
            properties,
            "tube_pitch_m",
            DEFAULTS["tube_pitch_m"]
        ),

        "tube_passes": get_value(
            properties,
            "tube_passes",
            DEFAULTS["tube_passes"]
        ),

        "shell_passes": get_value(
            properties,
            "shell_passes",
            DEFAULTS["shell_passes"]
        ),

        "channel_head_length": get_value(
            properties,
            "channel_head_length_m",
            DEFAULTS["channel_head_length_m"]
        ),

        "tubesheet_thickness": get_value(
            properties,
            "tubesheet_thickness_m",
            DEFAULTS["tubesheet_thickness_m"]
        ),

        "baffle_count": get_value(
            properties,
            "baffle_count",
            DEFAULTS["baffle_count"]
        ),

        "baffle_cut_fraction": get_value(
            properties,
            "baffle_cut_fraction",
            DEFAULTS["baffle_cut_fraction"]
        ),
    }

    # Convert Blender integer properties to integers.
    dimensions["number_of_tubes"] = int(
        dimensions["number_of_tubes"]
    )

    dimensions["tube_passes"] = int(
        dimensions["tube_passes"]
    )

    dimensions["shell_passes"] = int(
        dimensions["shell_passes"]
    )

    dimensions["baffle_count"] = int(
        dimensions["baffle_count"]
    )

    return dimensions


# ============================================================
# DIMENSION VALIDATION
# ============================================================

def validate_equipment_dimensions(dimensions):
    """
    Validate basic geometric dimensions.

    These checks are not a substitute for engineering design
    or pressure-vessel code verification.
    """

    errors = []

    positive_dimensions = [
        "shell_diameter",
        "shell_wall_thickness",
        "tube_diameter",
        "tube_wall_thickness",
        "tube_length",
        "tube_pitch",
        "channel_head_length",
        "tubesheet_thickness",
    ]

    for key in positive_dimensions:
        if dimensions[key] <= 0:
            errors.append(
                f"{key} must be greater than zero."
            )

    if (
        dimensions["shell_wall_thickness"]
        >= dimensions["shell_diameter"] / 2.0
    ):
        errors.append(
            "Shell wall thickness must be smaller than "
            "the shell radius."
        )

    if (
        dimensions["tube_wall_thickness"]
        >= dimensions["tube_diameter"] / 2.0
    ):
        errors.append(
            "Tube wall thickness must be smaller than "
            "the tube radius."
        )

    if (
        dimensions["tube_diameter"]
        <= 2.0 * dimensions["tube_wall_thickness"]
    ):
        errors.append(
            "Tube internal diameter must be positive."
        )

    if (
        dimensions["tube_pitch"]
        <= dimensions["tube_diameter"]
    ):
        errors.append(
            "Tube pitch must be greater than tube outside diameter."
        )

    if dimensions["number_of_tubes"] < 1:
        errors.append(
            "At least one tube is required."
        )

    if dimensions["tube_passes"] < 1:
        errors.append(
            "At least one tube pass is required."
        )

    if dimensions["shell_passes"] < 1:
        errors.append(
            "At least one shell pass is required."
        )

    if dimensions["baffle_count"] < 0:
        errors.append(
            "Baffle count cannot be negative."
        )

    if not (
        0.05 <= dimensions["baffle_cut_fraction"] <= 0.50
    ):
        errors.append(
            "Baffle cut fraction must be between 0.05 and 0.50."
        )

    if errors:
        raise ValueError(
            "Invalid E-102 equipment dimensions:\n- "
            + "\n- ".join(errors)
        )

    return True


# ============================================================
# GEOMETRY BUILDING
# ============================================================

def create_shell(dimensions, collection, material_dict=None):
    return geometry.create_shell(
        shell_diameter=dimensions["shell_diameter"],
        shell_thickness=dimensions["shell_wall_thickness"],
        shell_length=dimensions["tube_length"],
        collection=collection,
        material_dict=material_dict
    )


def create_tube_bundle(
    dimensions,
    collection,
    material_dict=None
):
    return geometry.create_tube_bundle(
        number_of_tubes=dimensions["number_of_tubes"],
        tube_diameter=dimensions["tube_diameter"],
        tube_length=dimensions["tube_length"],
        tube_pitch=dimensions["tube_pitch"],
        shell_diameter=dimensions["shell_diameter"],
        collection=collection,
        material_dict=material_dict
    )


def create_tubesheets(
    dimensions,
    collection,
    material_dict=None
):
    """
    Create front and rear tubesheets.

    Tubesheets are located just outside the shell ends.
    """

    shell_length = dimensions["tube_length"]
    thickness = dimensions["tubesheet_thickness"]
    # Tubesheet must cover the shell outside diameter, with a small
    # radial edge allowance, rather than stopping at shell ID.
    shell_radius = (
        dimensions["shell_diameter"] / 2.0
        + dimensions["shell_wall_thickness"]
        + geometry.TUBESHEET_EDGE_ALLOWANCE
    )

    left_x = -shell_length / 2.0 - thickness / 2.0
    right_x = shell_length / 2.0 + thickness / 2.0

    left = geometry.create_tubesheet(
        name="E102_Tubesheet_Left",
        shell_radius=shell_radius,
        thickness=thickness,
        x_position=left_x,
        collection=collection,
        material_dict=material_dict
    )

    right = geometry.create_tubesheet(
        name="E102_Tubesheet_Right",
        shell_radius=shell_radius,
        thickness=thickness,
        x_position=right_x,
        collection=collection,
        material_dict=material_dict
    )

    return [left, right]


def create_channel_heads(
    dimensions,
    collection,
    material_dict=None
):
    """
    Create mirrored ellipsoidal channel heads.

    Each flat base laps over the outer face of its tubesheet.
    The left head projects toward -X and the right head toward +X.
    """

    shell_length = dimensions["tube_length"]
    head_length = dimensions["channel_head_length"]
    sheet_thickness = dimensions["tubesheet_thickness"]
    shell_radius = (
        dimensions["shell_diameter"] / 2.0
        + dimensions["shell_wall_thickness"]
    )

    # The channel-head base is referenced to the outer face of
    # each tubesheet. create_channel_head() applies the 10 mm lap.
    left_base_reference = -shell_length / 2.0 - sheet_thickness
    right_base_reference = shell_length / 2.0 + sheet_thickness

    left = geometry.create_channel_head(
        name="E102_ChannelHead_Left",
        shell_radius=shell_radius,
        head_length=head_length,
        x_position=left_base_reference,
        collection=collection,
        material_dict=material_dict,
        side="left",
        inner_radius=dimensions["shell_diameter"] / 2.0,
        wall_thickness=dimensions["shell_wall_thickness"]
    )

    right = geometry.create_channel_head(
        name="E102_ChannelHead_Right",
        shell_radius=shell_radius,
        head_length=head_length,
        x_position=right_base_reference,
        collection=collection,
        material_dict=material_dict,
        side="right",
        inner_radius=dimensions["shell_diameter"] / 2.0,
        wall_thickness=dimensions["shell_wall_thickness"]
    )

    return [left, right]


def create_baffles(
    dimensions,
    collection,
    material_dict=None
):
    """
    Create segmental baffles.

    The current geometry.create_baffles() implementation
    uses its DEFAULT_BAFFLE_CUT constant. We temporarily
    set it to the scene value for this build.
    """

    original_cut = geometry.DEFAULT_BAFFLE_CUT

    try:
        geometry.DEFAULT_BAFFLE_CUT = (
            dimensions["baffle_cut_fraction"]
        )

        return geometry.create_baffles(
            baffle_count=dimensions["baffle_count"],
            shell_radius=dimensions["shell_diameter"] / 2.0,
            shell_length=dimensions["tube_length"],
            collection=collection,
            material_dict=material_dict
        )

    finally:
        geometry.DEFAULT_BAFFLE_CUT = original_cut


def create_nozzles(
    dimensions,
    collection,
    material_dict=None
):
    shell_nozzles = geometry.create_shell_side_nozzles(
        shell_diameter=dimensions["shell_diameter"],
        shell_length=dimensions["tube_length"],
        collection=collection,
        material_dict=material_dict
    )

    tube_nozzles = geometry.create_tube_side_nozzles(
        shell_diameter=dimensions["shell_diameter"],
        shell_length=dimensions["tube_length"],
        head_length=(
            dimensions["channel_head_length"]
            + dimensions["tubesheet_thickness"]
        ),
        collection=collection,
        material_dict=material_dict
    )

    return {
        "shell_nozzles": shell_nozzles,
        "tube_nozzles": tube_nozzles
    }


def create_supports(
    dimensions,
    collection,
    material_dict=None
):
    return geometry.create_supports(
        shell_radius=dimensions["shell_diameter"] / 2.0,
        shell_length=dimensions["tube_length"],
        collection=collection,
        material_dict=material_dict
    )


def create_labels(
    dimensions,
    collection,
    material_dict=None
):
    return geometry.create_equipment_labels(
        shell_radius=dimensions["shell_diameter"] / 2.0,
        shell_length=dimensions["tube_length"],
        collection=collection,
        material_dict=material_dict
    )


# ============================================================
# BUILD COMPLETE EQUIPMENT
# ============================================================

def build_complete_equipment(
    scene=None,
    clear_previous=True,
    material_dict=None
):
    """
    Build the complete E-102 exchanger.

    This is the main function called by operators.py.

    Args:
        scene:
            Blender scene. Defaults to bpy.context.scene.

        clear_previous:
            Remove the previous E-102 model before building.

        material_dict:
            Optional material dictionary.

    Returns:
        Dictionary containing created Blender objects.
    """

    if scene is None:
        scene = bpy.context.scene

    print("\n" + "=" * 60)
    print("E-102 EQUIPMENT BUILD")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Retrieve dimensions
    # --------------------------------------------------------

    dimensions = get_equipment_dimensions(scene)

    # --------------------------------------------------------
    # 2. Validate dimensions
    # --------------------------------------------------------

    validate_equipment_dimensions(dimensions)

    print("[E102] Dimensions validated.")

    # --------------------------------------------------------
    # 2A. Initialize the shared E-102 material library
    # --------------------------------------------------------

    if material_dict is None:
        material_dict = material_library.create_materials()

    # Give the shell and channel heads transparent inspection
    # materials while retaining metallic materials for internals.
    material_dict.setdefault(
        "shell",
        material_dict.get("transparent_blue")
    )
    material_dict.setdefault(
        "channel_head",
        material_dict.get("transparent_blue")
    )

    # --------------------------------------------------------
    # 3. Clean previous geometry
    # --------------------------------------------------------

    if clear_previous:
        utilities.clear_e102_model()
        print("[E102] Previous equipment cleared.")

    # --------------------------------------------------------
    # 4. Get shared collection
    # --------------------------------------------------------

    collection = utilities.get_e102_collection()

    # --------------------------------------------------------
    # 5. Build components
    # --------------------------------------------------------

    created = {}

    try:
        print("[E102] Creating shell...")

        created["shell"] = create_shell(
            dimensions,
            collection,
            material_dict
        )

        print("[E102] Creating tube bundle...")

        created["tubes"] = create_tube_bundle(
            dimensions,
            collection,
            material_dict
        )

        print("[E102] Creating tubesheets...")

        created["tubesheets"] = create_tubesheets(
            dimensions,
            collection,
            material_dict
        )

        print("[E102] Creating channel heads...")

        created["channel_heads"] = create_channel_heads(
            dimensions,
            collection,
            material_dict
        )

        print("[E102] Creating baffles...")

        created["baffles"] = create_baffles(
            dimensions,
            collection,
            material_dict
        )

        print("[E102] Creating nozzles...")

        created.update(
            create_nozzles(
                dimensions,
                collection,
                material_dict
            )
        )

        print("[E102] Creating supports...")

        created["supports"] = create_supports(
            dimensions,
            collection,
            material_dict
        )

        print("[E102] Creating labels...")

        created["labels"] = create_labels(
            dimensions,
            collection,
            material_dict
        )

        # ----------------------------------------------------
        # 6. Store engineering metadata
        # ----------------------------------------------------

        shell = created["shell"]

        shell["tube_count"] = dimensions["number_of_tubes"]
        shell["tube_passes"] = dimensions["tube_passes"]
        shell["shell_passes"] = dimensions["shell_passes"]

        shell["tube_pitch_m"] = dimensions["tube_pitch"]
        shell["tube_diameter_m"] = dimensions["tube_diameter"]
        shell["tube_wall_thickness_m"] = (
            dimensions["tube_wall_thickness"]
        )

        shell["baffle_count"] = dimensions["baffle_count"]
        shell["baffle_cut_fraction"] = (
            dimensions["baffle_cut_fraction"]
        )

        shell["channel_head_length_m"] = (
            dimensions["channel_head_length"]
        )

        shell["tubesheet_thickness_m"] = (
            dimensions["tubesheet_thickness"]
        )

        shell["geometry_model"] = "E102_visualization"

        # ----------------------------------------------------
        # 7. Build result summary
        # ----------------------------------------------------

        summary = geometry.get_geometry_summary()

        created["dimensions"] = dimensions
        created["summary"] = summary

        print("\n[E102] EQUIPMENT BUILD COMPLETE")
        print("Objects:", summary["object_count"])
        print("Components:", summary["components"])

        print("=" * 60)

        return created

    except Exception as exc:
        print("\n[E102] EQUIPMENT BUILD FAILED")
        print(str(exc))
        traceback.print_exc()

        raise


# ============================================================
# REMOVE EQUIPMENT
# ============================================================

def remove_equipment():
    """
    Remove the generated E-102 equipment model.
    """

    utilities.clear_e102_model()

    print("[E102] Equipment geometry removed.")

    return True


# ============================================================
# VISIBILITY
# ============================================================

def set_equipment_visibility(visible=True):
    """
    Show or hide all equipment objects.
    """

    objects = utilities.get_e102_objects()

    for obj in objects:
        obj.hide_viewport = not visible
        obj.hide_render = not visible

    return len(objects)


# ============================================================
# INSPECTION MODE
# ============================================================

def set_inspection_mode(enabled=True):
    """
    Enable or disable shell inspection mode.
    """

    return geometry.set_inspection_mode(enabled)


# ============================================================
# EQUIPMENT STATUS
# ============================================================

def get_equipment_status():
    """
    Return the current equipment status.
    """

    summary = geometry.get_geometry_summary()

    shell = bpy.data.objects.get("E102_Shell")

    if shell is None:
        return {
            "built": False,
            "object_count": summary["object_count"],
            "components": summary["components"]
        }

    return {
        "built": True,
        "object_count": summary["object_count"],
        "components": summary["components"],
        "tube_count": shell.get("tube_count", 0),
        "tube_passes": shell.get("tube_passes", 1),
        "shell_passes": shell.get("shell_passes", 1)
    }
