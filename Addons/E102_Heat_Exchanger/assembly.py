
"""
E-102 SHELL-AND-TUBE HEAT EXCHANGER
assembly.py

Animated exploded and assembled equipment views.

Blender 5.2 compatible.

Uses component metadata created by geometry.py.

Coordinates:
    X = longitudinal axis
    Y = transverse axis
    Z = vertical axis

Purpose:
    1. Explode equipment components for visual inspection.
    2. Animate components back to their original positions.
    3. Restore the original equipment transforms.
    4. Report assembly status.

Important:
    This is a visualization feature, not a manufacturing
    disassembly procedure.
"""

import bpy

from mathutils import Vector

from . import utilities


# ============================================================
# CONFIGURATION
# ============================================================

EXPLODE_FRAME = 1

ASSEMBLY_DURATION = 40

EXPLODE_DISTANCE = 0.30

MIN_EXPLODE_DISTANCE = 0.025

ROTATION_OFFSET = 0.12


# ============================================================
# OBJECT DISCOVERY
# ============================================================

def get_equipment_objects():
    """
    Return E-102 equipment objects.

    Only objects inside the E-102 equipment collection
    hierarchy are considered.

    Flow visualization objects are excluded.
    """

    objects = []

    try:
        candidates = utilities.get_e102_objects()

    except (AttributeError, RuntimeError) as error:

        print(
            "[E102 Assembly] Could not retrieve equipment objects:",
            error
        )

        return objects

    for obj in candidates:

        if obj is None:
            continue

        if obj.type not in {
            "MESH",
            "CURVE",
            "FONT",
            "SURFACE",
            "META"
        }:
            continue

        if not obj.name.startswith("E102_"):
            continue

        # Exclude flow objects.

        if obj.get("E102_flow_object", False):
            continue

        component = str(
            obj.get("component", "")
        ).lower()

        if component.startswith("flow"):
            continue

        # Exclude objects linked only to the flow collection.

        flow_only = True

        for collection in obj.users_collection:

            if collection.name != "E102_Flow":
                flow_only = False
                break

        if flow_only:
            continue

        objects.append(obj)

    return objects


# ============================================================
# HOME POSITION STORAGE
# ============================================================

def store_home_position(obj, force=False):
    """
    Store the original transform of an object.

    The home transform is stored only once unless force=True.

    This prevents repeated explode operations from replacing
    the original position with an already-exploded position.
    """

    if obj is None:
        return

    if "E102_home_location" not in obj or force:

        obj["E102_home_location"] = [
            float(obj.location.x),
            float(obj.location.y),
            float(obj.location.z)
        ]

    if "E102_home_rotation" not in obj or force:

        obj["E102_home_rotation"] = [
            float(obj.rotation_euler.x),
            float(obj.rotation_euler.y),
            float(obj.rotation_euler.z)
        ]

    if "E102_home_scale" not in obj or force:

        obj["E102_home_scale"] = [
            float(obj.scale.x),
            float(obj.scale.y),
            float(obj.scale.z)
        ]


def get_home_location(obj):

    value = obj.get("E102_home_location")

    if value is None:

        store_home_position(obj)

        value = obj.get("E102_home_location")

    return Vector(value)


def get_home_rotation(obj):

    value = obj.get("E102_home_rotation")

    if value is None:

        store_home_position(obj)

        value = obj.get("E102_home_rotation")

    return Vector(value)


def get_home_scale(obj):

    value = obj.get("E102_home_scale")

    if value is None:

        store_home_position(obj)

        value = obj.get("E102_home_scale")

    return Vector(value)


# ============================================================
# COMPONENT INFORMATION
# ============================================================

def get_component_type(obj):

    return str(
        obj.get("component", "other")
    ).lower()


def get_component_number(obj, property_name, default=1):

    try:

        return int(
            obj.get(property_name, default)
        )

    except (TypeError, ValueError):

        return default


# ============================================================
# EXPLODE DIRECTION
# ============================================================

def get_explode_direction(obj):
    """
    Determine a useful explode direction from component type.

    These are visual assembly directions, not manufacturing
    disassembly instructions.
    """

    component = get_component_type(obj)
   
    name = obj.name.lower()

    # --------------------------------------------------------
    # TUBESHEETS
    # --------------------------------------------------------

    if component == "tubesheet":

        if "left" in name:
            return Vector((-1.0, 0.0, 0.0))

        if "right" in name:
            return Vector((1.0, 0.0, 0.0))

        number = get_component_number(
            obj,
            "tubesheet_number",
            1
        )

        direction = -1.0 if number % 2 else 1.0

        return Vector((direction, 0.0, 0.0))

    # --------------------------------------------------------
    # CHANNEL HEADS AND COVERS
    # --------------------------------------------------------

    if component in (
        "channel_head",
        "channel_head_cover",
        "channel_cover"
    ):

        if "left" in name:
            return Vector((-1.0, 0.0, 0.0))

        if "right" in name:
            return Vector((1.0, 0.0, 0.0))

        return Vector((0.0, 0.0, 1.0))

    # --------------------------------------------------------
    # SHELL
    # --------------------------------------------------------

    if component == "shell":

        return Vector((0.0, 1.0, 0.0))

    # --------------------------------------------------------
    # TUBES
    # --------------------------------------------------------

    if component in (
        "tube",
        "heat_transfer_tube"
    ):

        number = get_component_number(
            obj,
            "tube_number",
            1
        )

        direction = 1.0 if number % 2 else -1.0

        return Vector((0.0, 0.0, direction))

    # --------------------------------------------------------
    # BAFFLES
    # --------------------------------------------------------

    if component in (
        "segmental_baffle",
        "baffle"
    ):

        number = get_component_number(
            obj,
            "baffle_number",
            1
        )

        direction = 1.0 if number % 2 else -1.0

        return Vector((0.0, direction, 0.0))

    # --------------------------------------------------------
    # NOZZLES
    # --------------------------------------------------------

    if component == "nozzle":

        if "hotwater" in name or "hot_water" in name:

            return Vector((0.0, 0.0, 1.0))

        if "left" in name:
            return Vector((-1.0, 0.0, 0.0))

        if "right" in name:
            return Vector((1.0, 0.0, 0.0))

        return Vector((0.0, 1.0, 0.0))

    # --------------------------------------------------------
    # SUPPORTS
    # --------------------------------------------------------
# --------------------------------------------------------
# FOUNDATION PLATFORM
# --------------------------------------------------------

    if component == "foundation_platform":
        return Vector((0.0, 0.0, -1.0))
    
    if component in (
        "support",
        "support_base",
        "saddle_support",
        "support_web"
    ):

        return Vector((0.0, 0.0, -1.0))

    # --------------------------------------------------------
    # LABELS
    # --------------------------------------------------------

    if component in (
        "equipment_label",
        "label"
    ):

        return Vector((0.0, -1.0, 0.0))

    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    return Vector((0.0, 0.0, 1.0))


# ============================================================
# EXPLODE DISTANCE
# ============================================================

def get_component_explode_distance(obj):

    component = get_component_type(obj)
    if component == "foundation_platform":
        return EXPLODE_DISTANCE * 1.5

    if component == "shell":
        return EXPLODE_DISTANCE * 1.8

    if component in (
        "tube",
        "heat_transfer_tube"
    ):
        return EXPLODE_DISTANCE * 0.45

    if component in (
        "segmental_baffle",
        "baffle"
    ):
        return EXPLODE_DISTANCE * 0.8

    if component == "tubesheet":
        return EXPLODE_DISTANCE * 1.2

    if component in (
        "channel_head",
        "channel_head_cover",
        "channel_cover"
    ):
        return EXPLODE_DISTANCE * 1.3

    if component == "nozzle":
        return EXPLODE_DISTANCE * 0.9

    if component in (
        "equipment_label",
        "label"
    ):
        return EXPLODE_DISTANCE * 0.5

    if component in (
        "support",
        "support_base",
        "saddle_support",
        "support_web"
    ):
        return EXPLODE_DISTANCE * 0.8

    return EXPLODE_DISTANCE


# ============================================================
# KEYFRAME HELPERS
# ============================================================

def insert_transform_keyframes(obj, frame):
    """
    Insert location, rotation and scale keyframes.
    """

    obj.keyframe_insert(
        data_path="location",
        frame=frame,
        group="E102 Assembly"
    )

    obj.keyframe_insert(
        data_path="rotation_euler",
        frame=frame,
        group="E102 Assembly"
    )

    obj.keyframe_insert(
        data_path="scale",
        frame=frame,
        group="E102 Assembly"
    )


def _get_action_fcurves(obj):
    """
    Retrieve animation F-curves.

    Supports legacy Actions and Blender's newer layered
    Action structure where available.

    Returns an empty list if the Action API does not expose
    editable F-curves.
    """

    if obj.animation_data is None:
        return []

    action = obj.animation_data.action

    if action is None:
        return []

    # Legacy Action API.

    try:

        return list(action.fcurves)

    except (AttributeError, TypeError, RuntimeError):
        pass

    # Blender layered Action API.

    curves = []

    try:

        slot = obj.animation_data.action_slot

        if slot is None:
            return curves

        for layer in action.layers:

            for strip in layer.strips:

                channelbag = strip.channelbag(slot)

                if channelbag is None:
                    continue

                curves.extend(
                    list(channelbag.fcurves)
                )

    except (AttributeError, TypeError, RuntimeError):

        return curves

    return curves


def set_linear_interpolation(obj):
    """
    Set interpolation to linear.

    Linear interpolation gives a constant-speed movement
    between assembly and exploded positions.
    """

    if obj.animation_data is None:
        return

    for fcurve in _get_action_fcurves(obj):

        try:

            for point in fcurve.keyframe_points:

                point.interpolation = "LINEAR"

        except (AttributeError, TypeError, RuntimeError):
            continue


def set_bezier_interpolation(obj):
    """
    Optional smooth interpolation for presentation animations.
    """

    if obj.animation_data is None:
        return

    for fcurve in _get_action_fcurves(obj):

        try:

            for point in fcurve.keyframe_points:

                point.interpolation = "BEZIER"

                point.handle_left_type = "AUTO"

                point.handle_right_type = "AUTO"

        except (AttributeError, TypeError, RuntimeError):
            continue


# ============================================================
# ANIMATION VALIDATION
# ============================================================

def validate_animation_arguments(scene, duration):

    if scene is None:

        raise RuntimeError(
            "No active Blender scene is available."
        )

    try:

        duration = int(duration)

    except (TypeError, ValueError):

        raise ValueError(
            "Animation duration must be an integer."
        )

    if duration < 1:

        raise ValueError(
            "Animation duration must be at least one frame."
        )

    return duration


# ============================================================
# EXPLODE
# ============================================================

def explode_equipment(
    scene=None,
    duration=ASSEMBLY_DURATION,
    distance_scale=1.0
):
    """
    Animate equipment components away from their home positions.

    Calling this function repeatedly uses the stored home
    transforms rather than accumulating movement.
    """

    if scene is None:
        scene = bpy.context.scene

    duration = validate_animation_arguments(
        scene,
        duration
    )

    try:
        distance_scale = float(distance_scale)

    except (TypeError, ValueError):

        raise ValueError(
            "Distance scale must be a valid number."
        )

    if distance_scale <= 0.0:

        raise ValueError(
            "Distance scale must be greater than zero."
        )

    objects = get_equipment_objects()

    if not objects:

        print(
            "[E102 Assembly] No equipment objects found."
        )

        return False

    start_frame = scene.frame_current

    end_frame = start_frame + duration

    # --------------------------------------------------------
    # STORE ORIGINAL TRANSFORMS FIRST
    # --------------------------------------------------------

    for obj in objects:

        store_home_position(obj)

    # --------------------------------------------------------
    # ANIMATE COMPONENTS
    # --------------------------------------------------------

    for obj in objects:

        home = get_home_location(obj)

        home_rotation = get_home_rotation(obj)

        direction = get_explode_direction(obj)

        if direction.length == 0.0:

            direction = Vector(
                (0.0, 0.0, 1.0)
            )

        direction.normalize()

        distance = (
            get_component_explode_distance(obj)
            * distance_scale
        )

        distance = max(
            distance,
            MIN_EXPLODE_DISTANCE
        )

        exploded_location = (
            home + direction * distance
        )

        # Start from the original transform.

        obj.location = home

        obj.rotation_euler = home_rotation

        obj.scale = get_home_scale(obj)

        insert_transform_keyframes(
            obj,
            start_frame
        )

        # Apply exploded position.

        obj.location = exploded_location

        component = get_component_type(obj)

        if component in (
            "tubesheet",
            "channel_head",
            "channel_head_cover",
            "channel_cover",
            "segmental_baffle",
            "baffle"
        ):

            obj.rotation_euler.z = (
                home_rotation.z + ROTATION_OFFSET
            )

        insert_transform_keyframes(
            obj,
            end_frame
        )

        set_linear_interpolation(obj)

        obj["E102_exploded"] = True

    scene.frame_set(start_frame)

    print(
        "[E102 Assembly] Exploded animation created:",
        len(objects),
        "components"
    )

    return True


# ============================================================
# ASSEMBLE
# ============================================================

def assemble_equipment(
    scene=None,
    duration=ASSEMBLY_DURATION
):
    """
    Animate every component back to its stored home transform.
    """

    if scene is None:
        scene = bpy.context.scene

    duration = validate_animation_arguments(
        scene,
        duration
    )

    objects = get_equipment_objects()

    if not objects:

        print(
            "[E102 Assembly] No equipment objects found."
        )

        return False

    # Ensure all original transforms exist.

    for obj in objects:

        store_home_position(obj)

    start_frame = scene.frame_current

    end_frame = start_frame + duration

    for obj in objects:

        home = get_home_location(obj)

        home_rotation = get_home_rotation(obj)

        home_scale = get_home_scale(obj)

        # Capture the current exploded transform.

        insert_transform_keyframes(
            obj,
            start_frame
        )

        # Restore original transform.

        obj.location = home

        obj.rotation_euler = home_rotation

        obj.scale = home_scale

        insert_transform_keyframes(
            obj,
            end_frame
        )

        set_linear_interpolation(obj)

        obj["E102_exploded"] = False

    scene.frame_set(start_frame)

    print(
        "[E102 Assembly] Assembly animation created:",
        len(objects),
        "components"
    )

    return True


# ============================================================
# INSTANT RESTORE
# ============================================================

def restore_equipment_immediately():
    """
    Restore original transforms without an animated transition.

    A keyframe is inserted at the current frame so the
    restored position is not immediately overridden by
    an existing keyframe at that frame.
    """

    objects = get_equipment_objects()

    if not objects:
        return False

    current_frame = bpy.context.scene.frame_current

    for obj in objects:

        store_home_position(obj)

        obj.location = get_home_location(obj)

        obj.rotation_euler = get_home_rotation(obj)

        obj.scale = get_home_scale(obj)

        insert_transform_keyframes(
            obj,
            current_frame
        )

        obj["E102_exploded"] = False

    bpy.context.scene.frame_set(
        current_frame
    )

    return True


# ============================================================
# RESET HOME POSITIONS
# ============================================================

def reset_home_positions():
    """
    Force the current transforms to become the new home positions.

    Use this only after intentionally changing the assembled
    equipment layout.
    """

    objects = get_equipment_objects()

    for obj in objects:

        store_home_position(
            obj,
            force=True
        )

        obj["E102_exploded"] = False

    return len(objects)


# ============================================================
# STATUS
# ============================================================

def get_assembly_status():

    objects = get_equipment_objects()

    exploded = sum(
        1
        for obj in objects
        if bool(obj.get("E102_exploded", False))
    )

    component_types = {}

    for obj in objects:

        component = get_component_type(obj)

        component_types[component] = (
            component_types.get(component, 0) + 1
        )

    return {

        "component_count": len(objects),

        "exploded_component_count": exploded,

        "assembled": exploded == 0,

        "component_types": component_types

    }


# ============================================================
# REGISTRATION
# ============================================================

def register():
    pass


def unregister():
    pass


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    result = explode_equipment()

    print(
        "E-102 explode operation:",
        result
    )

    print(
        "Assembly status:",
        get_assembly_status()
    )
