
"""
E-102 HEAT EXCHANGER
FLOW VISUALIZATION MODULE

Blender 5.2 compatible

Purpose:
    Create fluid-specific animated engineering schematics for:
        1. Waste cooking oil (WCO) in the tube side
        2. The selected heating medium in the shell side

Important:
    This is a fluid-specific schematic, not CFD. Particle colours,
    sizes and path styles identify the selected service; they are not
    calculated local velocities, temperatures, turbulence or phase
    distributions. The tube-side path remains a simplified pass-through
    because physical pass partitions and return bends are not implemented.

Coordinate convention:
    X = exchanger longitudinal axis
    Y = exchanger transverse axis
    Z = vertical axis

All dimensions are in metres.
"""

import bpy
import math

from mathutils import Vector


# ============================================================
# CONFIGURATION
# ============================================================

FLOW_COLLECTION_NAME = "E102_Flow"

FRAME_START = 1
FRAME_END = 160

PARTICLE_COUNT = 4
PARTICLE_RADIUS = 0.004

FLOW_LINE_THICKNESS = 0.0018

WCO_COLOR = (0.48, 0.16, 0.025, 1.0)
LABEL_COLOR = (1.0, 1.0, 1.0, 1.0)

# Visual identity for each shell-side service. These are display settings,
# not thermophysical property data.
HEATING_MEDIUM_VISUALS = {
    "hot_water": {
        "label": "HOT WATER",
        "color": (0.05, 0.42, 1.00, 1.0),
        "particle_scale": 1.00,
        "line_scale": 1.00,
        "description": "Liquid sensible heating",
    },
    "steam": {
        "label": "SATURATED STEAM",
        "color": (0.88, 0.92, 1.00, 1.0),
        "particle_scale": 1.35,
        "line_scale": 1.15,
        "description": "Condensing vapour service",
    },
    "thermal_oil": {
        "label": "THERMAL OIL",
        "color": (1.00, 0.32, 0.035, 1.0),
        "particle_scale": 1.10,
        "line_scale": 1.05,
        "description": "Liquid thermal-oil heating",
    },
    "glycol_water": {
        "label": "GLYCOL-WATER",
        "color": (0.05, 0.82, 0.62, 1.0),
        "particle_scale": 1.00,
        "line_scale": 1.00,
        "description": "Liquid glycol mixture",
    },
    "hot_air": {
        "label": "HOT AIR",
        "color": (1.00, 0.72, 0.08, 1.0),
        "particle_scale": 0.78,
        "line_scale": 0.90,
        "description": "Gas sensible heating",
    },
    "flue_gas": {
        "label": "FLUE GAS",
        "color": (0.64, 0.55, 0.42, 1.0),
        "particle_scale": 0.72,
        "line_scale": 0.90,
        "description": "Combustion-gas sensible heating",
    },
    "molten_salt": {
        "label": "MOLTEN SALT",
        "color": (0.95, 0.12, 0.20, 1.0),
        "particle_scale": 1.08,
        "line_scale": 1.05,
        "description": "High-temperature liquid salt service",
    },
}

DEFAULT_DIMENSIONS = {
    "shell_diameter": 0.200,
    "shell_length": 1.500,
    "tube_length": 1.500,
    "head_length": 0.180,
    "tubesheet_thickness": 0.025,
}


# ============================================================
# COLLECTION MANAGEMENT
# ============================================================

def get_flow_collection():

    collection = bpy.data.collections.get(
        FLOW_COLLECTION_NAME
    )

    if collection is None:

        collection = bpy.data.collections.new(
            FLOW_COLLECTION_NAME
        )

        bpy.context.scene.collection.children.link(
            collection
        )

    return collection


def _get_all_collection_objects(collection):

    objects = list(collection.objects)

    for child in collection.children:
        objects.extend(
            _get_all_collection_objects(child)
        )

    return objects


def clear_flow_visualization():

    collection = bpy.data.collections.get(
        FLOW_COLLECTION_NAME
    )

    if collection is None:
        return

    # Remove objects from the flow collection and
    # all nested flow collections.

    objects = _get_all_collection_objects(collection)

    for obj in set(objects):

        if obj.name in bpy.data.objects:

            bpy.data.objects.remove(
                obj,
                do_unlink=True
            )

    # Remove nested collections.

    def remove_children(parent):

        for child in list(parent.children):

            remove_children(child)

            bpy.data.collections.remove(
                child
            )

    remove_children(collection)


def link_to_flow_collection(obj):

    if obj is None:
        return None

    collection = get_flow_collection()

    for current_collection in list(obj.users_collection):

        current_collection.objects.unlink(obj)

    collection.objects.link(obj)

    return obj


# ============================================================
# MATERIALS
# ============================================================

def create_flow_material(
    name,
    color,
    metallic=0.0,
    roughness=0.35
):

    material = bpy.data.materials.get(name)

    if material is None:

        material = bpy.data.materials.new(name)

    material.diffuse_color = color
    material.use_nodes = True

    nodes = material.node_tree.nodes

    principled = nodes.get("Principled BSDF")

    if principled:

        principled.inputs["Base Color"].default_value = color
        principled.inputs["Metallic"].default_value = metallic
        principled.inputs["Roughness"].default_value = roughness

        # Blender 4.x and 5.x emission input compatibility.

        emission_color = principled.inputs.get("Emission Color")

        if emission_color:
            emission_color.default_value = color

        else:

            emission = principled.inputs.get("Emission")

            if emission:
                emission.default_value = color

        emission_strength = principled.inputs.get(
            "Emission Strength"
        )

        if emission_strength:
            emission_strength.default_value = 0.25

    return material


def initialize_flow_materials(heating_medium_type="hot_water"):
    """Create materials for WCO and the selected shell-side medium."""

    visual = HEATING_MEDIUM_VISUALS.get(
        heating_medium_type,
        HEATING_MEDIUM_VISUALS["hot_water"]
    )

    return {
        "wco": create_flow_material(
            "E102_WCO_Flow",
            WCO_COLOR
        ),
        "heating_medium": create_flow_material(
            "E102_{}_Flow".format(heating_medium_type),
            visual["color"]
        ),
        "label": create_flow_material(
            "E102_Flow_Label",
            LABEL_COLOR
        ),
        "heating_medium_visual": visual,
    }


# ============================================================
# CURVE CREATION
# ============================================================

def create_flow_curve(
    name,
    points,
    material,
    thickness=FLOW_LINE_THICKNESS
):

    if len(points) < 2:

        raise ValueError(
            "A flow curve requires at least two points."
        )

    curve_data = bpy.data.curves.new(
        name + "_Curve",
        type="CURVE"
    )

    curve_data.dimensions = "3D"
    curve_data.resolution_u = 24
    curve_data.bevel_depth = thickness
    curve_data.bevel_resolution = 4

    spline = curve_data.splines.new("POLY")

    spline.points.add(
        len(points) - 1
    )

    for index, point in enumerate(points):

        spline.points[index].co = (
            point[0],
            point[1],
            point[2],
            1.0
        )

    curve_object = bpy.data.objects.new(
        name,
        curve_data
    )

    get_flow_collection().objects.link(
        curve_object
    )

    curve_object.data.materials.append(
        material
    )

    curve_object["component"] = "flow_path"

    return curve_object


# ============================================================
# PARTICLE MESH
# ============================================================

def create_uv_sphere_mesh(
    name,
    radius,
    segments=12,
    rings=8
):

    vertices = []
    faces = []

    for ring in range(rings + 1):

        theta = math.pi * ring / rings

        for segment in range(segments):

            phi = (
                2.0 * math.pi * segment / segments
            )

            x = (
                radius *
                math.sin(theta) *
                math.cos(phi)
            )

            y = (
                radius *
                math.sin(theta) *
                math.sin(phi)
            )

            z = (
                radius *
                math.cos(theta)
            )

            vertices.append(
                (x, y, z)
            )

    for ring in range(rings):

        for segment in range(segments):

            current = (
                ring * segments + segment
            )

            next_segment = (
                ring * segments +
                (segment + 1) % segments
            )

            next_ring = (
                (ring + 1) * segments +
                segment
            )

            next_ring_segment = (
                (ring + 1) * segments +
                (segment + 1) % segments
            )

            faces.append((
                current,
                next_segment,
                next_ring_segment,
                next_ring
            ))

    mesh = bpy.data.meshes.new(name)

    mesh.from_pydata(
        vertices,
        [],
        faces
    )

    mesh.update()

    return mesh


def create_flow_particle(
    name,
    material,
    radius=PARTICLE_RADIUS
):

    mesh = create_uv_sphere_mesh(
        name + "_Mesh",
        radius
    )

    particle = bpy.data.objects.new(
        name,
        mesh
    )

    get_flow_collection().objects.link(
        particle
    )

    particle.data.materials.append(
        material
    )

    for polygon in particle.data.polygons:
        polygon.use_smooth = True

    particle["component"] = "flow_particle"

    return particle


# ============================================================
# PATH INTERPOLATION
# ============================================================

def calculate_path_lengths(points):

    if not points:
        return [], 0.0

    lengths = [0.0]
    total = 0.0

    for index in range(1, len(points)):

        distance = (
            Vector(points[index]) -
            Vector(points[index - 1])
        ).length

        total += distance
        lengths.append(total)

    return lengths, total


def position_on_path(points, fraction):

    if not points:

        return Vector((0.0, 0.0, 0.0))

    if len(points) == 1:

        return Vector(points[0])

    lengths, total_length = calculate_path_lengths(
        points
    )

    if total_length <= 0.0:

        return Vector(points[0])

    target_distance = (
        fraction % 1.0
    ) * total_length

    for index in range(1, len(points)):

        if lengths[index] >= target_distance:

            segment_start = Vector(
                points[index - 1]
            )

            segment_end = Vector(
                points[index]
            )

            segment_length = (
                lengths[index] -
                lengths[index - 1]
            )

            if segment_length <= 0.0:
                return segment_start

            local_fraction = (
                target_distance -
                lengths[index - 1]
            ) / segment_length

            return segment_start.lerp(
                segment_end,
                local_fraction
            )

    return Vector(points[-1])


# ============================================================
# ANIMATION
# ============================================================

def set_linear_interpolation(obj):

    """
    Set particle keyframes to linear interpolation.

    The legacy F-curve API is not available in every
    Blender 5.x Action configuration, so this is guarded.
    """

    if obj.animation_data is None:
        return

    action = obj.animation_data.action

    if action is None:
        return

    try:

        for fcurve in action.fcurves:

            for keyframe in fcurve.keyframe_points:

                keyframe.interpolation = "LINEAR"

    except (AttributeError, TypeError, RuntimeError):
        pass


def add_cycles_modifier(particle):

    """
    Add a cycles modifier where the current Blender
    Action API exposes legacy F-curves.

    The animation itself already returns each particle
    to its starting position at FRAME_END.
    """

    animation_data = particle.animation_data

    if animation_data is None:
        return

    action = animation_data.action

    if action is None:
        return

    try:

        for fcurve in action.fcurves:

            fcurve.modifiers.new("CYCLES")

    except (AttributeError, TypeError, RuntimeError):
        pass


def animate_particle(
    particle,
    points,
    particle_index,
    particle_count,
    frame_start=FRAME_START,
    frame_end=FRAME_END
):

    if particle_count <= 0:
        return

    if len(points) < 2:
        return

    if frame_end <= frame_start:

        raise ValueError(
            "Animation end frame must be greater than start frame."
        )

    offset = particle_index / particle_count

    sample_count = 40

    for sample in range(sample_count + 1):

        fraction = sample / sample_count

        position_fraction = (
            fraction + offset
        ) % 1.0

        position = position_on_path(
            points,
            position_fraction
        )

        frame = (
            frame_start +
            int(
                fraction *
                (frame_end - frame_start)
            )
        )

        particle.location = position

        particle.keyframe_insert(
            data_path="location",
            frame=frame
        )

    set_linear_interpolation(particle)
    add_cycles_modifier(particle)


def create_animated_flow(
    name,
    points,
    material,
    particle_count=PARTICLE_COUNT,
    particle_radius=PARTICLE_RADIUS
):

    particles = []

    for index in range(particle_count):

        particle = create_flow_particle(
            name + "_Particle_" + str(index + 1),
            material,
            radius=particle_radius
        )

        animate_particle(
            particle,
            points,
            index,
            particle_count
        )

        particles.append(particle)

    return particles


# ============================================================
# FLOW LABELS
# ============================================================

def create_flow_label(
    name,
    text,
    location,
    material,
    size=0.035
):

    text_data = bpy.data.curves.new(
        name + "_Text",
        type="FONT"
    )

    text_data.body = text
    text_data.size = size
    text_data.extrude = 0.0005

    text_object = bpy.data.objects.new(
        name,
        text_data
    )

    get_flow_collection().objects.link(
        text_object
    )

    text_object.location = location

    text_object.data.materials.append(
        material
    )

    text_object["component"] = "flow_label"

    return text_object


# ============================================================
# EXCHANGER DIMENSIONS
# ============================================================

def get_exchanger_dimensions(scene=None):

    """
    Read dimensions from the E-102 property group.

    Supports current property names and older alternatives.

    Fallback dimensions are used when a property is unavailable.
    """

    dimensions = dict(DEFAULT_DIMENSIONS)

    if scene is None:
        scene = bpy.context.scene

    if scene is None:
        return dimensions

    properties = getattr(
        scene,
        "e102_design",
        None
    )

    if properties is None:
        return dimensions

    def read_first(names, default):

        for name in names:

            if hasattr(properties, name):

                try:

                    value = float(
                        getattr(properties, name)
                    )

                    if value > 0.0:
                        return value

                except (TypeError, ValueError):
                    pass

        return default

    dimensions["shell_diameter"] = read_first(
        [
            "shell_internal_diameter_m",
            "shell_diameter_m",
            "shell_diameter"
        ],
        dimensions["shell_diameter"]
    )

    dimensions["shell_length"] = read_first(
        [
            "shell_length_m",
            "shell_length",
            "tube_length_m",
            "tube_length"
        ],
        dimensions["shell_length"]
    )

    dimensions["tube_length"] = read_first(
        [
            "tube_length_m",
            "tube_length"
        ],
        dimensions["tube_length"]
    )

    dimensions["head_length"] = read_first(
        [
            "channel_head_length_m",
            "channel_head_length"
        ],
        dimensions["head_length"]
    )

    dimensions["tubesheet_thickness"] = read_first(
        [
            "tubesheet_thickness_m",
            "tube_sheet_thickness_m",
            "tubesheet_thickness"
        ],
        dimensions["tubesheet_thickness"]
    )

    dimensions["baffle_count"] = int(read_first(
        ["baffle_count"],
        4
    ))

    return dimensions


# ============================================================
# FLOW PATH DEFINITIONS
# ============================================================

def create_wco_path(dimensions):

    """
    Schematic WCO path through the tube-side equipment.

    The path follows the exchanger longitudinal axis.

    It is not a physical four-pass route because the
    current equipment geometry has no pass partitions
    or return bends.
    """

    shell_length = dimensions["shell_length"]
    head_length = dimensions["head_length"]
    tubesheet_thickness = dimensions["tubesheet_thickness"]

    half_length = shell_length / 2.0

    nozzle_extension = 0.12

    # Keep the schematic path slightly below the centreline
    # so it remains visible in the transparent-shell view.

    y_offset = -0.025
    z_offset = -0.025

    left_nozzle = (
        -half_length
        - tubesheet_thickness
        - head_length
        - nozzle_extension
    )

    right_nozzle = (
        half_length
        + tubesheet_thickness
        + head_length
        + nozzle_extension
    )

    return [

        (left_nozzle, y_offset, z_offset),

        (
            -half_length
            - tubesheet_thickness
            - head_length * 0.5,
            y_offset,
            z_offset
        ),

        (-half_length * 0.5, y_offset, z_offset),

        (0.0, y_offset, z_offset),

        (half_length * 0.5, y_offset, z_offset),

        (
            half_length
            + tubesheet_thickness
            + head_length * 0.5,
            y_offset,
            z_offset
        ),

        (right_nozzle, y_offset, z_offset)

    ]


def create_shell_side_path(dimensions, heating_medium_type="hot_water"):
    """
    Create an illustrative shell-side zig-zag path.

    The path is visually adjusted to the baffle count and shell dimensions.
    It is not a CFD streamline and does not calculate leakage, bypass,
    crossflow distribution, local velocity or pressure drop.
    """

    shell_length = dimensions["shell_length"]
    radius = dimensions["shell_diameter"] / 2.0
    half_length = shell_length / 2.0

    # Use the baffle count as a visual guide for the number of path turns.
    # At least four stations are retained for a readable schematic.
    baffle_count = max(0, int(dimensions.get("baffle_count", 4)))
    station_count = max(5, min(2 * baffle_count + 3, 21))

    # Keep the path inside the nominal shell envelope.
    # The offset is intentionally reduced for small-diameter exchangers.
    z_offset = radius * 0.58
    y_offset = 0.0

    points = []
    for index in range(station_count):
        fraction = index / (station_count - 1)
        x = -half_length * 0.88 + fraction * shell_length * 0.88
        z = z_offset if index % 2 == 0 else -z_offset
        points.append((x, y_offset, z))

    return points


# Backwards-compatible function name for projects that imported it.
def create_hot_water_path(dimensions):
    return create_shell_side_path(dimensions, "hot_water")


# ============================================================
# MAIN FLOW BUILDER
# ============================================================

def build_flow_visualization(
    scene=None,
    clear_previous=True
):
    """
    Build fluid-specific animated flow schematics for E-102.

    The selected heating medium controls the shell-side material,
    particle scale and label. Path geometry is schematic only.
    Legacy return keys hot_water_path / hot_water_particles /
    hot_water_label are retained for operator compatibility.
    """

    if scene is None:
        scene = bpy.context.scene

    if scene is None:
        raise RuntimeError("No active Blender scene is available.")

    if clear_previous:
        clear_flow_visualization()

    properties = getattr(scene, "e102_design", None)
    medium_key = getattr(properties, "heating_medium_type", "hot_water")
    visual = HEATING_MEDIUM_VISUALS.get(
        medium_key,
        HEATING_MEDIUM_VISUALS["hot_water"]
    )

    collection = get_flow_collection()
    materials = initialize_flow_materials(medium_key)
    dimensions = get_exchanger_dimensions(scene)

    # --------------------------------------------------------
    # WCO TUBE-SIDE FLOW
    # --------------------------------------------------------
    wco_path = create_wco_path(dimensions)
    wco_curve = create_flow_curve(
        "E102_WCO_Flow_Path",
        wco_path,
        materials["wco"]
    )
    wco_particles = create_animated_flow(
        "E102_WCO",
        wco_path,
        materials["wco"],
        particle_radius=PARTICLE_RADIUS
    )
    process_fluid_key = getattr(properties, "process_fluid_type", "wco")
    process_fluid_label = (
        getattr(properties, "custom_process_fluid_name", "Custom process fluid")
        if process_fluid_key == "custom"
        else process_fluid_key.replace("_", " ").upper()
    )
    wco_label = create_flow_label(
        "E102_WCO_Flow_Label",
        f"{process_fluid_label} FLOW - TUBE SIDE",
        (
            -dimensions["shell_length"] / 2.0,
            -0.105,
            -0.095
        ),
        materials["label"]
    )

    # --------------------------------------------------------
    # SELECTED HEATING-MEDIUM SHELL-SIDE FLOW
    # --------------------------------------------------------
    shell_path = create_shell_side_path(dimensions, medium_key)
    shell_line_thickness = FLOW_LINE_THICKNESS * visual["line_scale"]
    shell_curve = create_flow_curve(
        "E102_{}_Flow_Path".format(medium_key),
        shell_path,
        materials["heating_medium"],
        thickness=shell_line_thickness
    )
    shell_particles = create_animated_flow(
        "E102_{}".format(medium_key),
        shell_path,
        materials["heating_medium"],
        particle_radius=PARTICLE_RADIUS * visual["particle_scale"]
    )
    shell_label = create_flow_label(
        "E102_{}_Flow_Label".format(medium_key),
        "{} - SHELL SIDE".format(visual["label"]),
        (
            -dimensions["shell_length"] / 2.0,
            0.105,
            dimensions["shell_diameter"] / 2.0
        ),
        materials["label"]
    )

    # Attach service metadata to every generated flow object.
    for obj in [shell_curve, shell_label] + shell_particles:
        obj["fluid_service"] = medium_key
        obj["fluid_service_label"] = visual["label"]
        obj["visualization_type"] = "fluid_specific_engineering_schematic"
        obj["is_cfd_result"] = False

    for obj in [wco_curve, wco_label] + wco_particles:
        obj["fluid_service"] = "wco"
        obj["fluid_service_label"] = process_fluid_label
        obj["visualization_type"] = "simplified_tube_side_schematic"
        obj["is_cfd_result"] = False

    # --------------------------------------------------------
    # SCENE ANIMATION SETTINGS
    # --------------------------------------------------------
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END
    scene.frame_set(FRAME_START)

    collection.hide_viewport = False
    collection.hide_render = False

    return {
        "collection": collection,
        "materials": materials,
        "wco_path": wco_curve,
        "wco_particles": wco_particles,
        "wco_label": wco_label,

        # New descriptive keys.
        "heating_medium_key": medium_key,
        "heating_medium_path": shell_curve,
        "heating_medium_particles": shell_particles,
        "heating_medium_label": shell_label,

        # Backwards-compatible aliases used by existing operators.
        "hot_water_path": shell_curve,
        "hot_water_particles": shell_particles,
        "hot_water_label": shell_label,

        "dimensions": dimensions,
    }


# ============================================================
# FLOW VISIBILITY CONTROLS
# ============================================================

def set_flow_visibility(visible=True):

    collection = bpy.data.collections.get(
        FLOW_COLLECTION_NAME
    )

    if collection is None:
        return False

    collection.hide_viewport = not visible
    collection.hide_render = not visible

    return True


def remove_flow_visualization():

    collection = bpy.data.collections.get(
        FLOW_COLLECTION_NAME
    )

    if collection is None:
        return

    clear_flow_visualization()

    bpy.data.collections.remove(
        collection
    )


# ============================================================
# REGISTRATION
# ============================================================

def register():
    pass


def unregister():

    remove_flow_visualization()


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    result = build_flow_visualization()

    print(
        "E-102 flow visualization created successfully."
    )

    print(
        "WCO particles:",
        len(result["wco_particles"])
    )

    print(
        "Hot water particles:",
        len(result["hot_water_particles"])
    )
