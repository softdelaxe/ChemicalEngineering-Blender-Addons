"""
E-102 SHELL-AND-TUBE HEAT EXCHANGER
geometry.py

Transparent, enclosed industrial visualization geometry.

Coordinate convention:
    X = exchanger longitudinal axis
    Y = horizontal transverse axis
    Z = vertical transverse axis

All dimensions are in metres.
"""

import bpy
import math
import inspect
import os
import bmesh
from mathutils import Vector

from . import utilities


# ============================================================
# GLOBAL SETTINGS
# ============================================================

COLLECTION_NAME = utilities.E102_COLLECTION_NAME

DEFAULT_SIDES = 64
DEFAULT_BAFFLE_CUT = 0.25
BOOLEAN_EPSILON = 0.003

SHELL_TRANSPARENCY = 0.22
CHANNEL_HEAD_LAP_LENGTH = 0.010

NOZZLE_DIAMETER = 0.065
NOZZLE_WALL = 0.004
NOZZLE_LENGTH = 0.12

FLANGE_EXTRA_RADIUS = 0.025
FLANGE_THICKNESS = 0.018
FLANGE_BOLT_COUNT = 8
FLANGE_BOLT_RADIUS = 0.004

REINFORCEMENT_PAD_THICKNESS = 0.008

TUBESHEET_EDGE_ALLOWANCE = 0.002

_LAST_TUBE_POSITIONS = []
_LAST_TUBE_DIAMETER = 0.0127
_LAST_TUBE_WALL = 0.0009
_LAST_TUBE_PITCH = 0.019


# ============================================================
# COLLECTION MANAGEMENT
# ============================================================

def get_equipment_collection():
    return utilities.get_e102_collection()


def link_object(obj, collection=None):

    if obj is None:
        return None

    if collection is None:
        collection = get_equipment_collection()

    if collection not in obj.users_collection:
        collection.objects.link(obj)

    return obj


def clear_equipment():

    global _LAST_TUBE_POSITIONS

    _LAST_TUBE_POSITIONS = []

    utilities.clear_e102_model()


# ============================================================
# MATERIAL MANAGEMENT
# ============================================================

def get_material(material_dict, *keys):

    if not material_dict:
        return None

    for key in keys:

        mat = material_dict.get(key)

        if mat is not None:
            return mat

    return None


def assign_material(obj, mat):

    if obj is None or mat is None:
        return obj

    if obj.type in {"MESH", "FONT", "CURVE"}:

        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    return obj


def assign_component_material(obj, material_dict, *keys):

    mat = get_material(material_dict, *keys)

    if mat:
        assign_material(obj, mat)

    return obj


def _set_material_alpha(mat, alpha):
    """Set material alpha for viewport and rendering."""

    if mat is None:
        return

    alpha = max(0.0, min(1.0, float(alpha)))

    color = mat.diffuse_color

    mat.diffuse_color = (
        color[0],
        color[1],
        color[2],
        alpha
    )

    if mat.use_nodes and mat.node_tree:

        for node in mat.node_tree.nodes:

            if node.type == "BSDF_PRINCIPLED":

                alpha_socket = node.inputs.get("Alpha")

                if alpha_socket:
                    alpha_socket.default_value = alpha

                break

    try:
        mat.surface_render_method = "DITHERED"
    except (AttributeError, TypeError, ValueError):
        pass

    try:
        mat.show_transparent_back = True
    except (AttributeError, TypeError, ValueError):
        pass


def make_transparent_material(mat, alpha=SHELL_TRANSPARENCY):
    """
    Create a transparent material copy without modifying
    the original shared material.

    Uses BLENDED transparency first, with DITHERED
    as a fallback for Blender version compatibility.
    """

    if mat is None:
        return None

    alpha = max(0.05, min(1.0, float(alpha)))

    # Create an independent copy of the original material.
    transparent = mat.copy()
    transparent.name = mat.name + "_E102_Transparent"
    transparent.use_nodes = True

    # Preserve the original material colour.
    color = mat.diffuse_color

    transparent.diffuse_color = (
        color[0],
        color[1],
        color[2],
        alpha
    )

    # Configure the Principled BSDF shader.
    if transparent.node_tree:

        bsdf = transparent.node_tree.nodes.get("Principled BSDF")

        if bsdf:

            base_color = bsdf.inputs.get("Base Color")
            alpha_socket = bsdf.inputs.get("Alpha")

            if base_color:
                base_color.default_value = (
                    color[0],
                    color[1],
                    color[2],
                    1.0
                )

            if alpha_socket:
                alpha_socket.default_value = alpha

    # Configure transparency.
    try:
        transparent.surface_render_method = "BLENDED"

    except (AttributeError, TypeError, ValueError):

        try:
            transparent.surface_render_method = "DITHERED"

        except (AttributeError, TypeError, ValueError):
            pass

    # Allow transparency to be visible from both sides.
    try:
        transparent.show_transparent_back = True

    except (AttributeError, TypeError, ValueError):
        pass

    return transparent


def apply_shell_transparency(
    shell,
    alpha=SHELL_TRANSPARENCY,
    material_dict=None
):
    """Apply the dedicated transparent-blue material to the shell."""

    if shell is None or shell.type != "MESH":
        return False

    alpha = max(0.05, min(1.0, float(alpha)))

    # Prefer the dedicated transparent material.
    transparent = None

    if material_dict:
        transparent = (
            material_dict.get("transparent_blue")
            or material_dict.get("transparent_shell")
        )

    # Fallback: create a dedicated transparent material.
    if transparent is None:

        transparent = bpy.data.materials.get(
            "E102_Shell_Transparent"
        )

        if transparent is None:
            transparent = bpy.data.materials.new(
                name="E102_Shell_Transparent"
            )

        transparent.diffuse_color = (
            0.18, 0.48, 0.72, alpha
        )

        transparent.use_nodes = True

        bsdf = transparent.node_tree.nodes.get(
            "Principled BSDF"
        )

        if bsdf:
            bsdf.inputs["Base Color"].default_value = (
                0.18, 0.48, 0.72, 1.0
            )
            bsdf.inputs["Alpha"].default_value = alpha

    else:

        # Use an independent copy so other components are unaffected.
        transparent = transparent.copy()
        transparent.name = "E102_Shell_Transparent"

        color = transparent.diffuse_color

        transparent.diffuse_color = (
            color[0], color[1], color[2], alpha
        )

        if transparent.use_nodes and transparent.node_tree:
            bsdf = transparent.node_tree.nodes.get(
                "Principled BSDF"
            )

            if bsdf:
                bsdf.inputs["Alpha"].default_value = alpha

    try:
        transparent.surface_render_method = "DITHERED"
    except (AttributeError, TypeError, ValueError):
        pass

    # Replace the shell's material.
    shell.data.materials.clear()
    shell.data.materials.append(transparent)

    shell.color = (0.18, 0.48, 0.72, alpha)
    shell.display_type = "TEXTURED"
    shell.show_in_front = False

    shell["transparent_shell"] = True
    shell["shell_alpha"] = alpha
    shell["inspection_mode"] = True

    return True


# ============================================================
# UNIVERSAL COMPONENT INSPECTOR INTEGRATION
# ============================================================

UCI_METADATA_VERSION = "1.0"


def set_component_metadata(obj, component, **properties):
    """Attach engineering properties and Python source information."""

    if obj is None:
        return

    obj["component"] = str(component)

    caller = inspect.currentframe().f_back

    try:
        if caller is not None:

            code = caller.f_code

            metadata = {
                "uci_metadata_version": UCI_METADATA_VERSION,
                "uci_component_type": str(component),
                "uci_source_function": code.co_name,
                "uci_source_module": caller.f_globals.get("__name__", ""),
                "uci_source_file": os.path.abspath(code.co_filename),
                "uci_source_line": code.co_firstlineno,
                "uci_metadata_call_line": caller.f_lineno,
                "uci_tracking_method": "automatic_geometry_metadata",
                "uci_source_available": True
            }

            for key, value in metadata.items():
                obj[key] = value

    finally:
        del caller

    for key, value in properties.items():

        try:
            obj[key] = value

        except Exception as exc:
            print(
                f"[E102 Geometry] Could not store "
                f"{key} on {obj.name}: {exc}"
            )


# ============================================================
# OBJECT HELPERS
# ============================================================

def create_hollow_cylinder(
    name,
    outer_radius,
    inner_radius,
    length,
    location,
    axis,
    collection=None
):

    if collection is None:
        collection = get_equipment_collection()

    if outer_radius <= 0:
        raise ValueError(f"{name}: outer radius must be positive.")

    if inner_radius < 0 or inner_radius >= outer_radius:
        raise ValueError(f"{name}: invalid inner radius.")

    if length <= 0:
        raise ValueError(f"{name}: length must be positive.")

    return utilities.create_hollow_cylinder(
        name=name,
        outer_radius=outer_radius,
        inner_radius=inner_radius,
        depth=length,
        location=location,
        vertices_count=DEFAULT_SIDES,
        axis=axis,
        collection=collection
    )


def create_solid_cylinder(
    name,
    radius,
    length,
    location,
    axis,
    collection=None
):

    if collection is None:
        collection = get_equipment_collection()

    if radius <= 0 or length <= 0:
        raise ValueError(f"{name}: invalid cylinder dimensions.")

    return utilities.create_cylinder(
        name=name,
        radius=radius,
        depth=length,
        location=location,
        vertices_count=DEFAULT_SIDES,
        axis=axis,
        collection=collection
    )


def create_box(
    name,
    location,
    dimensions,
    collection=None
):

    if collection is None:
        collection = get_equipment_collection()

    return utilities.create_box(
        name=name,
        location=location,
        dimensions=dimensions,
        collection=collection
    )


# ============================================================
# BOOLEAN OPERATIONS
# ============================================================

def boolean_difference(target, cutter, modifier_name):

    if target is None or cutter is None:
        return False

    if target.type != "MESH" or cutter.type != "MESH":
        return False

    modifier = None

    try:

        bpy.ops.object.select_all(action="DESELECT")

        target.select_set(True)
        bpy.context.view_layer.objects.active = target

        modifier = target.modifiers.new(
            name=modifier_name,
            type="BOOLEAN"
        )

        modifier.operation = "DIFFERENCE"
        modifier.solver = "EXACT"
        modifier.object = cutter

        bpy.ops.object.modifier_apply(
            modifier=modifier.name
        )

        bpy.data.objects.remove(
            cutter,
            do_unlink=True
        )

        return True

    except Exception as exc:

        print(
            "[E102 Geometry] Boolean failed:",
            modifier_name,
            exc
        )

        if modifier and modifier.name in target.modifiers:
            target.modifiers.remove(modifier)

        if cutter.name in bpy.data.objects:
            bpy.data.objects.remove(
                cutter,
                do_unlink=True
            )

        return False


def cut_circular_opening(
    target,
    radius,
    depth,
    location,
    axis,
    name
):

    cutter = create_solid_cylinder(
        name=name,
        radius=radius,
        length=depth,
        location=location,
        axis=axis
    )

    return boolean_difference(
        target,
        cutter,
        name + "_Boolean"
    )


# ============================================================
# TUBE POSITION CALCULATION
# ============================================================

def calculate_tube_positions(
    number_of_tubes,
    tube_pitch,
    shell_radius,
    tube_radius,
    clearance=0.008
):

    number_of_tubes = int(number_of_tubes)

    if number_of_tubes < 1:
        raise ValueError("Tube count must be at least one.")

    if tube_pitch <= 0:
        raise ValueError("Tube pitch must be positive.")

    available_radius = (
        shell_radius - tube_radius - clearance
    )

    if available_radius <= 0:
        raise ValueError("Insufficient shell space for tube bundle.")

    maximum_index = int(
        available_radius / tube_pitch
    ) + 1

    candidates = []

    for iy in range(-maximum_index, maximum_index + 1):

        for iz in range(-maximum_index, maximum_index + 1):

            y = iy * tube_pitch
            z = iz * tube_pitch

            radial_distance = math.sqrt(y * y + z * z)

            if radial_distance <= available_radius:

                candidates.append(
                    (radial_distance, y, z)
                )

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
            item[2]
        )
    )

    if len(candidates) < number_of_tubes:

        raise ValueError(
            "Requested tube count exceeds available shell space. "
            f"Requested: {number_of_tubes}; "
            f"Available: {len(candidates)}."
        )

    return [
        (item[1], item[2])
        for item in candidates[:number_of_tubes]
    ]


# ============================================================
# SHELL
# ============================================================

def create_shell(
    shell_diameter,
    shell_thickness,
    shell_length,
    collection=None,
    material_dict=None
):
    """Create a hollow cylindrical shell."""

    if collection is None:
        collection = get_equipment_collection()

    if shell_diameter <= 0 or shell_thickness <= 0:
        raise ValueError("Invalid shell dimensions.")

    if shell_length <= 0:
        raise ValueError("Shell length must be positive.")

    inner_radius = shell_diameter / 2.0
    outer_radius = inner_radius + shell_thickness

    shell = create_hollow_cylinder(
        name="E102_Shell",
        outer_radius=outer_radius,
        inner_radius=inner_radius,
        length=shell_length,
        location=(0.0, 0.0, 0.0),
        axis=(1.0, 0.0, 0.0),
        collection=collection
    )

    assign_component_material(
        shell,
        material_dict,
        "shell",
        "shell_material",
        "stainless_steel",
        "steel"
    )

    set_component_metadata(
        shell,
        "shell",
        shell_internal_diameter_m=shell_diameter,
        shell_external_diameter_m=outer_radius * 2.0,
        shell_thickness_m=shell_thickness,
        shell_length_m=shell_length,
        shell_open_ends=True
    )

    apply_shell_transparency(
    shell,
    alpha=SHELL_TRANSPARENCY,
    material_dict=material_dict
)

    utilities.set_smooth_shading(shell)

    return shell


# ============================================================
# TUBE BUNDLE
# ============================================================

def create_tube_bundle(
    number_of_tubes,
    tube_diameter,
    tube_length,
    tube_pitch,
    shell_diameter,
    collection=None,
    material_dict=None,
    tube_wall_thickness=None
):

    global _LAST_TUBE_POSITIONS
    global _LAST_TUBE_DIAMETER
    global _LAST_TUBE_WALL
    global _LAST_TUBE_PITCH

    if collection is None:
        collection = get_equipment_collection()

    if tube_wall_thickness is None:
        tube_wall_thickness = tube_diameter * 0.05

    tube_radius = tube_diameter / 2.0
    tube_inner_radius = tube_radius - tube_wall_thickness

    if tube_inner_radius <= 0:
        raise ValueError("Invalid tube wall thickness.")

    positions = calculate_tube_positions(
        number_of_tubes,
        tube_pitch,
        shell_diameter / 2.0,
        tube_radius
    )

    _LAST_TUBE_POSITIONS = positions
    _LAST_TUBE_DIAMETER = tube_diameter
    _LAST_TUBE_WALL = tube_wall_thickness
    _LAST_TUBE_PITCH = tube_pitch

    tubes = []

    for index, (y, z) in enumerate(positions):

        tube = create_hollow_cylinder(
            name=f"E102_Tube_{index + 1:03d}",
            outer_radius=tube_radius,
            inner_radius=tube_inner_radius,
            length=tube_length,
            location=(0.0, y, z),
            axis=(1.0, 0.0, 0.0),
            collection=collection
        )

        assign_component_material(
            tube,
            material_dict,
            "tube",
            "tubes",
            "tube_material",
            "stainless_steel"
        )

        set_component_metadata(
            tube,
            "tube",
            tube_number=index + 1,
            tube_y_m=y,
            tube_z_m=z,
            tube_diameter_m=tube_diameter,
            tube_wall_thickness_m=tube_wall_thickness,
            tube_length_m=tube_length
        )

        utilities.set_smooth_shading(tube)

        tubes.append(tube)

    return tubes


# ============================================================
# TUBESHEETS
# ============================================================

def create_tubesheet(
    name,
    shell_radius,
    thickness,
    x_position,
    collection=None,
    material_dict=None
):

    if collection is None:
        collection = get_equipment_collection()

    tubesheet = create_solid_cylinder(
        name=name,
        radius=shell_radius,
        length=thickness,
        location=(x_position, 0.0, 0.0),
        axis=(1.0, 0.0, 0.0),
        collection=collection
    )

    assign_component_material(
        tubesheet,
        material_dict,
        "tubesheet",
        "tube_sheet",
        "stainless_steel"
    )

    hole_radius = (
        _LAST_TUBE_DIAMETER / 2.0 + 0.0004
    )

    for index, (y, z) in enumerate(_LAST_TUBE_POSITIONS):

        cut_circular_opening(
            target=tubesheet,
            radius=hole_radius,
            depth=thickness + BOOLEAN_EPSILON,
            location=(x_position, y, z),
            axis=(1.0, 0.0, 0.0),
            name=f"{name}_TubeHole_{index + 1:03d}"
        )

    set_component_metadata(
        tubesheet,
        "tubesheet",
        thickness_m=thickness,
        tube_hole_count=len(_LAST_TUBE_POSITIONS),
        x_position_m=x_position,
        tubesheet_radius_m=shell_radius
    )

    return tubesheet


# ============================================================
# ELLIPSOIDAL CHANNEL HEADS (LAPPED & SYMMETRICAL)
# ============================================================


def create_channel_head(
    name,
    shell_radius,
    head_length,
    x_position,
    collection=None,
    material_dict=None,
    side="right",
    inner_radius=None,
    wall_thickness=None,
    lap_length=0.010
):
    """
    Create a hollow hemispherical channel head.

    Geometry:
        - Flat circular base overlaps the shell.
        - Dome projects outward from the shell.
        - Left head projects along -X.
        - Right head projects along +X.
        - Nozzle connection is located at the dome apex.

    Coordinate convention:
        X = longitudinal axis
        Y = horizontal transverse axis
        Z = vertical transverse axis

    x_position:
        Outer-face reference coordinate at the corresponding tubesheet.

    lap_length:
        Axial overlap between the channel-head base and tubesheet.
    """

    if collection is None:
        collection = get_equipment_collection()

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if shell_radius <= 0:
        raise ValueError("Invalid channel-head radius.")

    if head_length <= 0:
        raise ValueError("Head length must be positive.")

    if lap_length < 0:
        raise ValueError("Lap length cannot be negative.")

    if inner_radius is None:
        if wall_thickness is None:
            wall_thickness = 0.004

        inner_radius = shell_radius - wall_thickness

    if wall_thickness is None:
        wall_thickness = shell_radius - inner_radius

    if inner_radius <= 0 or inner_radius >= shell_radius:
        raise ValueError("Invalid inner radius.")

    if wall_thickness <= 0:
        raise ValueError("Wall thickness must be positive.")

    if not math.isclose(
        shell_radius - inner_radius,
        wall_thickness,
        rel_tol=1e-5,
        abs_tol=1e-7
    ):
        raise ValueError(
            "Inconsistent shell radius, inner radius and wall thickness."
        )

   # --------------------------------------------------------
# ORIENTATION
# --------------------------------------------------------

    side = str(side).lower()

    if side == "left":
        direction = -1.0

    elif side == "right":
        direction = 1.0

    else:
        raise ValueError(
            "Side must be 'left' or 'right'."
        )

    # Move the flat base inward into the tubesheet.
    base_x = x_position - direction * lap_length

    # Calculate the dome apex.
    apex_x = base_x + direction * head_length

    # --------------------------------------------------------
    # CREATE MESH
    # --------------------------------------------------------

    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)

    collection.objects.link(obj)

    bm = bmesh.new()

    segments = DEFAULT_SIDES
    rings = max(16, DEFAULT_SIDES // 2)

    outer_rings = []
    inner_rings = []

    # --------------------------------------------------------
    # GENERATE CONCENTRIC HEMISPHERICAL RINGS
    # --------------------------------------------------------

    for i in range(rings + 1):

        theta = (math.pi / 2.0) * (i / rings)

        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)

        r_out = shell_radius * cos_theta
        r_in = inner_radius * cos_theta

        # The channel head is an ellipsoidal dish: its radial
        # dimension follows the shell radius while its axial depth
        # follows the specified channel_head_length.
        inner_head_length = max(
            head_length - wall_thickness,
            head_length * 0.5
        )

        x_out = direction * head_length * sin_theta
        x_in = direction * inner_head_length * sin_theta

        out_ring = []
        in_ring = []

        for s in range(segments):

            angle = 2.0 * math.pi * s / segments

            cos_angle = math.cos(angle)
            sin_angle = math.sin(angle)

            out_ring.append(
                bm.verts.new((
                    x_out,
                    r_out * cos_angle,
                    r_out * sin_angle
                ))
            )

            in_ring.append(
                bm.verts.new((
                    x_in,
                    r_in * cos_angle,
                    r_in * sin_angle
                ))
            )

        outer_rings.append(out_ring)
        inner_rings.append(in_ring)

    # --------------------------------------------------------
    # OUTER DOME
    # --------------------------------------------------------

    for i in range(rings):

        for s in range(segments):

            sn = (s + 1) % segments

            bm.faces.new((
                outer_rings[i][s],
                outer_rings[i][sn],
                outer_rings[i + 1][sn],
                outer_rings[i + 1][s]
            ))

    # --------------------------------------------------------
    # INNER DOME
    # --------------------------------------------------------

    for i in range(rings):

        for s in range(segments):

            sn = (s + 1) % segments

            bm.faces.new((
                inner_rings[i][s],
                inner_rings[i + 1][s],
                inner_rings[i + 1][sn],
                inner_rings[i][sn]
            ))

    # --------------------------------------------------------
    # FLAT ANNULAR BASE
    # --------------------------------------------------------

    for s in range(segments):

        sn = (s + 1) % segments

        bm.faces.new((
            outer_rings[0][s],
            inner_rings[0][s],
            inner_rings[0][sn],
            outer_rings[0][sn]
        ))

    # --------------------------------------------------------
    # OUTER AND INNER APEX
    # --------------------------------------------------------

    inner_head_length = max(
        head_length - wall_thickness,
        head_length * 0.5
    )

    apex_outer = bm.verts.new((
        direction * head_length,
        0.0,
        0.0
    ))

    apex_inner = bm.verts.new((
        direction * inner_head_length,
        0.0,
        0.0
    ))

    for s in range(segments):

        sn = (s + 1) % segments

        bm.faces.new((
            outer_rings[-1][s],
            outer_rings[-1][sn],
            apex_outer
        ))

        bm.faces.new((
            inner_rings[-1][sn],
            inner_rings[-1][s],
            apex_inner
        ))

    # --------------------------------------------------------
    # FINALIZE MESH
    # --------------------------------------------------------

    bm.normal_update()

    bm.to_mesh(mesh)
    bm.free()

    mesh.update()

    # Consistent normals
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    obj.select_set(False)

    # --------------------------------------------------------
    # POSITION HEAD
    # --------------------------------------------------------

    obj.location = Vector((base_x, 0.0, 0.0))

    # --------------------------------------------------------
    # MATERIAL
    # --------------------------------------------------------

    assign_component_material(
        obj,
        material_dict,
        "channel_head",
        "head",
        "stainless_steel"
    )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    set_component_metadata(
        obj,
        "channel_head",

        side=side,
        head_length_m=head_length,
        external_radius_m=shell_radius,
        inner_radius_m=inner_radius,
        wall_thickness_m=wall_thickness,

        head_base_reference_x_m=x_position,
        base_x_m=base_x,
        apex_x_m=apex_x,

        lap_length_m=lap_length,

        head_geometry="ellipsoidal_hollow",

        direction_x=direction
    )

    utilities.set_smooth_shading(obj)

    return obj

# ============================================================
# CHANNEL HEAD PARTITIONS
# ============================================================

def create_channel_head_partition(
    name,
    shell_radius,
    head_length,
    x_position,
    collection=None,
    material_dict=None,
    partition_thickness=0.006
):
    """Create a preliminary longitudinal channel-head partition."""

    if collection is None:
        collection = get_equipment_collection()

    wall_thickness = max(shell_radius * 0.04, 0.004)
    inner_radius = shell_radius - wall_thickness

    partition = create_box(
        name=name,
        location=(x_position, 0.0, 0.0),
        dimensions=(
            head_length,
            inner_radius * 1.9,
            partition_thickness
        ),
        collection=collection
    )

    assign_component_material(
        partition,
        material_dict,
        "baffle_steel",
        "tube_sheet",
        "stainless_steel"
    )

    set_component_metadata(
        partition,
        "channel_head_partition",
        head_length_m=head_length,
        partition_thickness_m=partition_thickness,
        partition_count=1,
        flow_passes_represented=2,
        tube_routing_validated=False
    )

    return partition


# ============================================================
# BAFFLES
# ============================================================

def create_baffles(
    baffle_count,
    shell_radius,
    shell_length,
    collection=None,
    material_dict=None,
    baffle_cut_fraction=DEFAULT_BAFFLE_CUT
):

    if collection is None:
        collection = get_equipment_collection()

    baffle_count = int(baffle_count)

    if baffle_count <= 0:
        return []

    baffle_cut_fraction = max(
        0.05,
        min(0.45, float(baffle_cut_fraction))
    )

    baffle_thickness = max(
        shell_radius * 0.04,
        0.004
    )

    baffle_spacing = shell_length / (baffle_count + 1)

    window_height = (
        shell_radius * 2.0 * baffle_cut_fraction
    )

    baffles = []

    for index in range(baffle_count):

        x_position = (
            -shell_length / 2.0
            + baffle_spacing * (index + 1)
        )

        baffle = create_solid_cylinder(
            name=f"E102_Baffle_{index + 1:02d}",
            radius=shell_radius,
            length=baffle_thickness,
            location=(x_position, 0.0, 0.0),
            axis=(1.0, 0.0, 0.0),
            collection=collection
        )

        assign_component_material(
            baffle,
            material_dict,
            "baffle",
            "baffles",
            "baffle_steel",
            "stainless_steel"
        )

        window_z = (
            -shell_radius + window_height / 2.0
            if index % 2 == 0
            else shell_radius - window_height / 2.0
        )

        window = create_box(
            name=f"E102_Baffle_Window_{index + 1:02d}",
            location=(x_position, 0.0, window_z),
            dimensions=(
                baffle_thickness + BOOLEAN_EPSILON * 2.0,
                shell_radius * 2.2,
                window_height
            ),
            collection=collection
        )

        boolean_difference(
            baffle,
            window,
            f"E102_Baffle_Window_Cut_{index + 1:02d}"
        )

        for tube_index, (y, z) in enumerate(_LAST_TUBE_POSITIONS):

            cut_circular_opening(
                target=baffle,
                radius=_LAST_TUBE_DIAMETER / 2.0 + 0.0005,
                depth=baffle_thickness + BOOLEAN_EPSILON,
                location=(x_position, y, z),
                axis=(1.0, 0.0, 0.0),
                name=(
                    f"E102_Baffle_{index + 1:02d}"
                    f"_TubeHole_{tube_index + 1:03d}"
                )
            )

        set_component_metadata(
            baffle,
            "segmental_baffle",
            baffle_number=index + 1,
            x_position_m=x_position,
            baffle_cut_fraction=baffle_cut_fraction
        )

        baffles.append(baffle)

    return baffles


# ============================================================
# NOZZLE NECKS
# ============================================================

def create_nozzle(
    name,
    outside_diameter,
    wall_thickness,
    length,
    location,
    axis,
    collection=None,
    material_dict=None
):

    if collection is None:
        collection = get_equipment_collection()

    outer_radius = outside_diameter / 2.0
    inner_radius = outer_radius - wall_thickness

    if inner_radius <= 0:
        raise ValueError(f"Invalid wall thickness for {name}.")

    nozzle = create_hollow_cylinder(
        name=name,
        outer_radius=outer_radius,
        inner_radius=inner_radius,
        length=length,
        location=location,
        axis=axis,
        collection=collection
    )

    assign_component_material(
        nozzle,
        material_dict,
        "nozzle",
        "nozzles",
        "nozzle_steel",
        "stainless_steel"
    )

    set_component_metadata(
        nozzle,
        "nozzle",
        outside_diameter_m=outside_diameter,
        wall_thickness_m=wall_thickness,
        nozzle_length_m=length
    )

    return nozzle


# ============================================================
# NOZZLE FLANGES
# ============================================================

def create_nozzle_flange(
    name,
    outside_diameter,
    nozzle_axis,
    flange_center,
    collection=None,
    material_dict=None,
    bolt_count=FLANGE_BOLT_COUNT
):
    """Create an annular flange with bolt openings."""

    if collection is None:
        collection = get_equipment_collection()

    axis = Vector(nozzle_axis).normalized()

    nozzle_radius = outside_diameter / 2.0

    flange_outer_radius = (
        nozzle_radius + FLANGE_EXTRA_RADIUS
    )

    flange_inner_radius = nozzle_radius - 0.002

    flange = create_hollow_cylinder(
        name=name,
        outer_radius=flange_outer_radius,
        inner_radius=flange_inner_radius,
        length=FLANGE_THICKNESS,
        location=flange_center,
        axis=axis,
        collection=collection
    )

    assign_component_material(
        flange,
        material_dict,
        "flange",
        "flange_steel",
        "polished_steel",
        "stainless_steel"
    )

    reference = Vector((0.0, 0.0, 1.0))

    if abs(axis.dot(reference)) > 0.95:
        reference = Vector((0.0, 1.0, 0.0))

    u = axis.cross(reference).normalized()
    v = axis.cross(u).normalized()

    bolt_circle_radius = flange_outer_radius * 0.78

    for index in range(int(bolt_count)):

        angle = (
            2.0 * math.pi * index / max(1, int(bolt_count))
        )

        offset_y = bolt_circle_radius * math.cos(angle)
        offset_z = bolt_circle_radius * math.sin(angle)

        hole_center = (
            Vector(flange_center)
            + u * offset_y
            + v * offset_z
        )

        cut_circular_opening(
            target=flange,
            radius=FLANGE_BOLT_RADIUS,
            depth=FLANGE_THICKNESS + BOOLEAN_EPSILON,
            location=hole_center,
            axis=axis,
            name=f"{name}_BoltHole_{index + 1:02d}"
        )

    set_component_metadata(
        flange,
        "nozzle_flange",
        outside_radius_m=flange_outer_radius,
        flange_thickness_m=FLANGE_THICKNESS,
        bolt_hole_count=int(bolt_count),
        bolt_circle_radius_m=bolt_circle_radius
    )

    return flange


# ============================================================
# REINFORCEMENT PADS
# ============================================================

def create_reinforcement_pad(
    name,
    nozzle_diameter,
    shell_outer_radius,
    x_position,
    collection=None,
    material_dict=None
):
    """Create a simplified flat annular reinforcement pad."""

    if collection is None:
        collection = get_equipment_collection()

    inner_radius = nozzle_diameter / 2.0 + 0.002
    outer_radius = nozzle_diameter * 1.15

    pad_center_z = (
        shell_outer_radius
        + REINFORCEMENT_PAD_THICKNESS / 2.0
    )

    pad = create_hollow_cylinder(
        name=name,
        outer_radius=outer_radius,
        inner_radius=inner_radius,
        length=REINFORCEMENT_PAD_THICKNESS,
        location=(x_position, 0.0, pad_center_z),
        axis=(0.0, 0.0, 1.0),
        collection=collection
    )

    assign_component_material(
        pad,
        material_dict,
        "flange_steel",
        "nozzle_steel",
        "stainless_steel"
    )

    set_component_metadata(
        pad,
        "reinforcement_pad",
        nozzle_diameter_m=nozzle_diameter,
        pad_thickness_m=REINFORCEMENT_PAD_THICKNESS,
        calculated_reinforcement=False
    )

    return pad


# ============================================================
# SHELL-SIDE NOZZLES
# ============================================================

def create_shell_side_nozzles(
    shell_diameter,
    shell_length,
    collection=None,
    material_dict=None
):

    if collection is None:
        collection = get_equipment_collection()

    shell_inner_radius = shell_diameter / 2.0
    shell_outer_radius = shell_inner_radius + 0.004

    positions = [
        (-shell_length * 0.30, "Inlet"),
        (shell_length * 0.30, "Outlet")
    ]

    nozzles = []

    for x_position, label in positions:

        nozzle_center_z = (
            shell_outer_radius + NOZZLE_LENGTH / 2.0
        )

        nozzle = create_nozzle(
            name=f"E102_HotWater_{label}_Nozzle",
            outside_diameter=NOZZLE_DIAMETER,
            wall_thickness=NOZZLE_WALL,
            length=NOZZLE_LENGTH,
            location=(x_position, 0.0, nozzle_center_z),
            axis=(0.0, 0.0, 1.0),
            collection=collection,
            material_dict=material_dict
        )

        nozzle["fluid_service"] = "hot_water"
        nozzle["flow_direction"] = label.lower()

        flange_center = (
            x_position,
            0.0,
            shell_outer_radius + NOZZLE_LENGTH
            - FLANGE_THICKNESS / 2.0
        )

        flange = create_nozzle_flange(
            name=f"E102_HotWater_{label}_Flange",
            outside_diameter=NOZZLE_DIAMETER,
            nozzle_axis=(0.0, 0.0, 1.0),
            flange_center=flange_center,
            collection=collection,
            material_dict=material_dict
        )

        flange["fluid_service"] = "hot_water"

        pad = create_reinforcement_pad(
            name=f"E102_HotWater_{label}_Reinforcement",
            nozzle_diameter=NOZZLE_DIAMETER,
            shell_outer_radius=shell_outer_radius,
            x_position=x_position,
            collection=collection,
            material_dict=material_dict
        )

        nozzles.extend([nozzle, flange, pad])

    return nozzles


# ============================================================
# TUBE-SIDE NOZZLES (Attached to Dome Base / Cover)
# ============================================================

def create_tube_side_nozzles(
    shell_diameter,
    shell_length,
    head_length,
    collection=None,
    material_dict=None
):

    if collection is None:
        collection = get_equipment_collection()

    # The supplied head_length includes channel-head depth plus
    # tubesheet thickness. Place tube-side nozzles at the dome apex.
    # The head base laps over the tubesheet by CHANNEL_HEAD_LAP_LENGTH.
    apex_offset = (
        shell_length / 2.0
        + head_length
        - CHANNEL_HEAD_LAP_LENGTH
    )

    positions = [
        (-1.0, "Inlet"),
        (1.0, "Outlet")
    ]

    nozzles = []

    for direction, label in positions:

        # Nozzle begins at the ellipsoidal dome apex and projects outward.
        nozzle_center_x = direction * (
            apex_offset + NOZZLE_LENGTH / 2.0
        )

        nozzle = create_nozzle(
            name=f"E102_WCO_{label}_Nozzle",
            outside_diameter=NOZZLE_DIAMETER,
            wall_thickness=NOZZLE_WALL,
            length=NOZZLE_LENGTH,
            location=(nozzle_center_x, 0.0, 0.0),
            axis=(1.0, 0.0, 0.0),
            collection=collection,
            material_dict=material_dict
        )

        nozzle["fluid_service"] = "WCO"
        nozzle["flow_direction"] = label.lower()

        flange_center = (
            direction * (
                apex_offset
                + NOZZLE_LENGTH
                - FLANGE_THICKNESS / 2.0
            ),
            0.0,
            0.0
        )

        flange = create_nozzle_flange(
            name=f"E102_WCO_{label}_Flange",
            outside_diameter=NOZZLE_DIAMETER,
            nozzle_axis=(1.0, 0.0, 0.0),
            flange_center=flange_center,
            collection=collection,
            material_dict=material_dict
        )

        flange["fluid_service"] = "WCO"

        nozzles.extend([nozzle, flange])

    return nozzles


# ============================================================
# SHELL NOZZLE OPENINGS
# ============================================================

def cut_shell_nozzle_openings(
    shell,
    shell_diameter,
    shell_thickness,
    shell_length
):

    if shell is None:
        return False

    shell_inner_radius = shell_diameter / 2.0

    positions = (
        -shell_length * 0.30,
        shell_length * 0.30
    )

    success = True

    for index, x_position in enumerate(positions):

        result = cut_circular_opening(
            target=shell,
            radius=NOZZLE_DIAMETER / 2.0,
            depth=shell_thickness + BOOLEAN_EPSILON * 2.0,
            location=(
                x_position,
                0.0,
                shell_inner_radius + shell_thickness / 2.0
            ),
            axis=(0.0, 0.0, 1.0),
            name=f"E102_Shell_HotWater_Opening_{index + 1}"
        )

        success = success and result

    return success


# ============================================================
# SADDLE SUPPORTS
# ============================================================

def create_supports(
    shell_radius,
    shell_length,
    collection=None,
    material_dict=None
):
    """Create two curved saddle supports with base plates."""

    if collection is None:
        collection = get_equipment_collection()

    support_width = 0.16
    support_thickness = 0.012
    support_height = 0.18

    # The shell axis is X. The saddle must therefore have its cylinder
    # axis along X so its curved seating surface follows the shell's
    # transverse Y-Z cross-section. Match the saddle ID to the shell OD
    # so the shell rests on the cradle without being cut into it.
    saddle_inner_radius = shell_radius
    saddle_outer_radius = saddle_inner_radius + support_thickness

    positions = (
        -shell_length * 0.30,
        shell_length * 0.30
    )

    supports = []

    for index, x_position in enumerate(positions):

        saddle = create_hollow_cylinder(
            name=f"E102_Saddle_{index + 1}",
            outer_radius=saddle_outer_radius,
            inner_radius=saddle_inner_radius,
            length=support_width,
            location=(x_position, 0.0, 0.0),
            axis=(1.0, 0.0, 0.0),
            collection=collection
        )

        # Remove the upper half of the ring, leaving a lower cradle.
        # Since the saddle axis is X, the cutter's long dimension is Y.
        cutter = create_box(
            name=f"E102_Saddle_Upper_Cutter_{index + 1}",
            location=(
                x_position,
                0.0,
                saddle_outer_radius
            ),
            dimensions=(
                support_width * 2.0,
                saddle_outer_radius * 3.0,
                saddle_outer_radius * 2.0
            ),
            collection=collection
        )

        boolean_difference(
            saddle,
            cutter,
            f"E102_Saddle_Upper_Cut_{index + 1}"
        )

        assign_component_material(
            saddle,
            material_dict,
            "support",
            "saddle",
            "dark_steel",
            "stainless_steel"
        )

        set_component_metadata(
            saddle,
            "saddle_support",
            support_number=index + 1
        )

        for web_index, y_offset in enumerate(
            (-support_width * 0.32, support_width * 0.32)
        ):

            web = create_box(
                name=(
                    f"E102_Saddle_Web_{index + 1}_"
                    f"{web_index + 1}"
                ),
                location=(
                    x_position,
                    y_offset,
                    -shell_radius - support_height / 2.0
                ),
                dimensions=(
                    support_width,
                    support_thickness,
                    support_height
                ),
                collection=collection
            )

            assign_component_material(
                web,
                material_dict,
                "support",
                "dark_steel",
                "stainless_steel"
            )

            set_component_metadata(
                web,
                "support_web",
                support_number=index + 1
            )

            supports.append(web)

        base = create_box(
            name=f"E102_Support_Base_{index + 1}",
            location=(
                x_position,
                0.0,
                -shell_radius - support_height
            ),
            dimensions=(
                support_width * 1.8,
                support_width * 1.5,
                support_thickness
            ),
            collection=collection
        )

        assign_component_material(
            base,
            material_dict,
            "support",
            "dark_steel",
            "stainless_steel"
        )

        set_component_metadata(
            base,
            "support_base",
            support_number=index + 1
        )

        supports.extend([saddle, base])

    return supports


# ============================================================
# EQUIPMENT LABELS
# ============================================================

def create_equipment_labels(
    shell_radius,
    shell_length,
    collection=None,
    material_dict=None
):

    if collection is None:
        collection = get_equipment_collection()

    labels = []

    label_data = [
        (
            "E102_Label_Shell",
            "SHELL SIDE - HOT WATER",
            (0.0, -shell_radius - 0.10, shell_radius + 0.06)
        ),
        (
            "E102_Label_Tube",
            "TUBE SIDE - WCO",
            (0.0, -shell_radius - 0.10, -shell_radius - 0.12)
        ),
        (
            "E102_Label_Inlet",
            "WCO INLET",
            (-shell_length / 2.0 - 0.35, -shell_radius - 0.10, 0.0)
        ),
        (
            "E102_Label_Outlet",
            "WCO OUTLET",
            (shell_length / 2.0 + 0.35, -shell_radius - 0.10, 0.0)
        )
    ]

    for name, body, location in label_data:

        label = utilities.make_text(
            name=name,
            body=body,
            location=location,
            size=0.045,
            rotation=(
                math.radians(90.0),
                0.0,
                0.0
            ),
            collection=collection
        )

        assign_component_material(
            label,
            material_dict,
            "label",
            "text",
            "label_white"
        )

        set_component_metadata(
            label,
            "equipment_label"
        )

        labels.append(label)

    return labels


# ============================================================
# GEOMETRY BUILD
# ============================================================

def build_geometry(
    shell_diameter,
    shell_length,
    shell_wall_thickness,
    tube_outside_diameter,
    tube_wall_thickness,
    tube_length,
    number_of_tubes,
    tube_pitch,
    tube_passes,
    shell_passes,
    channel_head_length,
    tubesheet_thickness,
    baffle_count,
    baffle_cut_fraction=DEFAULT_BAFFLE_CUT,
    collection=None,
    material_dict=None
):
    """Build the enclosed E-102 exchanger.

    shell_diameter is the shell INTERNAL diameter.
    """

    global _LAST_TUBE_POSITIONS
    global _LAST_TUBE_DIAMETER
    global _LAST_TUBE_WALL
    global _LAST_TUBE_PITCH

    if collection is None:
        collection = get_equipment_collection()

    if shell_diameter <= 0:
        raise ValueError("Shell diameter must be positive.")

    if shell_length <= 0:
        raise ValueError("Shell length must be positive.")

    if shell_wall_thickness <= 0:
        raise ValueError("Shell wall thickness must be positive.")

    if tubesheet_thickness <= 0:
        raise ValueError("Tubesheet thickness must be positive.")

    if channel_head_length <= 0:
        raise ValueError("Channel head length must be positive.")

    if tube_outside_diameter <= 0:
        raise ValueError("Tube diameter must be positive.")

    if tube_wall_thickness <= 0:
        raise ValueError("Tube wall thickness must be positive.")

    if tube_wall_thickness >= tube_outside_diameter / 2.0:
        raise ValueError("Tube wall thickness is too large.")

    shell_inner_radius = shell_diameter / 2.0
    shell_outer_radius = shell_inner_radius + shell_wall_thickness

    # --------------------------------------------------------
    # Tube positions
    # --------------------------------------------------------

    positions = calculate_tube_positions(
        number_of_tubes,
        tube_pitch,
        shell_inner_radius,
        tube_outside_diameter / 2.0
    )

    _LAST_TUBE_POSITIONS = positions
    _LAST_TUBE_DIAMETER = tube_outside_diameter
    _LAST_TUBE_WALL = tube_wall_thickness
    _LAST_TUBE_PITCH = tube_pitch

    # --------------------------------------------------------
    # Shell
    # --------------------------------------------------------

    shell = create_shell(
        shell_diameter,
        shell_wall_thickness,
        shell_length,
        collection,
        material_dict
    )

    # --------------------------------------------------------
    # Tube bundle
    # --------------------------------------------------------

    tubes = create_tube_bundle(
        number_of_tubes,
        tube_outside_diameter,
        tube_length,
        tube_pitch,
        shell_diameter,
        collection,
        material_dict,
        tube_wall_thickness=tube_wall_thickness
    )

    # --------------------------------------------------------
    # Tubesheets
    # --------------------------------------------------------

    tubesheet_radius = (
        shell_outer_radius + TUBESHEET_EDGE_ALLOWANCE
    )

    left_sheet_x = (
        -shell_length / 2.0
        - tubesheet_thickness / 2.0
    )

    right_sheet_x = (
        shell_length / 2.0
        + tubesheet_thickness / 2.0
    )

    tubesheets = [
        create_tubesheet(
            "E102_Tubesheet_Left",
            tubesheet_radius,
            tubesheet_thickness,
            left_sheet_x,
            collection,
            material_dict
        ),
        create_tubesheet(
            "E102_Tubesheet_Right",
            tubesheet_radius,
            tubesheet_thickness,
            right_sheet_x,
            collection,
            material_dict
        )
    ]

    # --------------------------------------------------------
    # ELLIPSOIDAL CHANNEL HEADS (LAPPING THE TUBESHEETS)
    # --------------------------------------------------------

    head_length = channel_head_length

    # Set the base of the dome to overlap the tubesheet and shell end.
    left_base_x = (
        -shell_length / 2.0
        - tubesheet_thickness
    )

    right_base_x = (
        shell_length / 2.0
        + tubesheet_thickness
    )

    heads = [
        create_channel_head(
            name="E102_ChannelHead_Left",
            shell_radius=shell_outer_radius,
            head_length=head_length,
            x_position=left_base_x,
            collection=collection,
            material_dict=material_dict,
            side="left",
            inner_radius=shell_inner_radius,
            wall_thickness=shell_wall_thickness
        ),
        create_channel_head(
            name="E102_ChannelHead_Right",
            shell_radius=shell_outer_radius,
            head_length=head_length,
            x_position=right_base_x,
            collection=collection,
            material_dict=material_dict,
            side="right",
            inner_radius=shell_inner_radius,
            wall_thickness=shell_wall_thickness
        )
    ]

    # --------------------------------------------------------
    # CHANNEL-HEAD PARTITIONS
    # --------------------------------------------------------

    partitions = []

    if int(tube_passes) > 1:

        partitions = [
            create_channel_head_partition(
                "E102_ChannelHead_Left_Partition",
                shell_outer_radius,
                head_length,
                left_base_x,
                collection,
                material_dict
            ),
            create_channel_head_partition(
                "E102_ChannelHead_Right_Partition",
                shell_outer_radius,
                head_length,
                right_base_x,
                collection,
                material_dict
            )
        ]

    # --------------------------------------------------------
    # Baffles
    # --------------------------------------------------------

    baffles = create_baffles(
        baffle_count,
        shell_inner_radius,
        shell_length,
        collection,
        material_dict,
        baffle_cut_fraction=baffle_cut_fraction
    )

    # --------------------------------------------------------
    # Shell-side nozzles
    # --------------------------------------------------------

    shell_nozzles = create_shell_side_nozzles(
        shell_diameter,
        shell_length,
        collection,
        material_dict
    )

    cut_shell_nozzle_openings(
        shell,
        shell_diameter,
        shell_wall_thickness,
        shell_length
    )

    # --------------------------------------------------------
    # Tube-side nozzles (Attached at channel-head dome apex)
    # --------------------------------------------------------

    tube_nozzles = create_tube_side_nozzles(
        shell_diameter,
        shell_length,
        head_length + tubesheet_thickness,
        collection,
        material_dict
    )

    # --------------------------------------------------------
    # Supports
    # --------------------------------------------------------

    supports = create_supports(
        shell_outer_radius,
        shell_length,
        collection,
        material_dict
    )

    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    labels = create_equipment_labels(
        shell_outer_radius,
        shell_length,
        collection,
        material_dict
    )

    # --------------------------------------------------------
    # Shell metadata
    # --------------------------------------------------------

    shell["tube_count"] = int(number_of_tubes)
    shell["tube_passes"] = int(tube_passes)
    shell["shell_passes"] = int(shell_passes)

    shell["tube_pitch_m"] = float(tube_pitch)
    shell["tube_length_m"] = float(tube_length)
    shell["baffle_cut_fraction"] = float(baffle_cut_fraction)

    shell["shell_is_enclosed"] = True
    shell["shell_open_ends"] = False
    shell["shell_closed_by_ellipsoidal_heads"] = True
    shell["channel_head_type"] = "ellipsoidal_hollow"
    shell["tubesheets_close_shell_ends"] = True
    shell["transparent_visualization"] = True

    shell["channel_head_partitions_created"] = bool(partitions)
    shell["four_pass_routing_validated"] = False

    # --------------------------------------------------------
    # Return geometry objects
    # --------------------------------------------------------

    return {
        "shell": shell,
        "tubes": tubes,
        "tube_positions": positions,
        "tubesheets": tubesheets,
        "channel_heads": heads,
        "channel_head_covers": [],
        "channel_head_partitions": partitions,
        "baffles": baffles,
        "shell_nozzles": shell_nozzles,
        "tube_nozzles": tube_nozzles,
        "supports": supports,
        "labels": labels
    }


# ============================================================
# INSPECTION MODE
# ============================================================

def set_inspection_mode(enabled=True):
    """Switch between transparent and opaque shell display."""

    shell = bpy.data.objects.get("E102_Shell")

    if shell is None:
        return False

    if enabled:
        alpha = float(
            shell.get("shell_alpha", SHELL_TRANSPARENCY)
        )
    else:
        alpha = 1.0

    for mat in shell.data.materials:
        if mat is not None:
            _set_material_alpha(mat, alpha)

    shell.color = (0.45, 0.60, 0.72, alpha)
    shell["inspection_mode"] = bool(enabled)

    return True


# ============================================================
# GEOMETRY SUMMARY
# ============================================================

def get_geometry_summary():

    collection = bpy.data.collections.get(
        COLLECTION_NAME
    )

    if collection is None:
        return {
            "object_count": 0,
            "components": {}
        }

    components = {}

    def collect(current_collection):

        for obj in current_collection.objects:

            component = obj.get("component", "other")

            components[component] = (
                components.get(component, 0) + 1
            )

        for child in current_collection.children:
            collect(child)

    collect(collection)

    return {
        "object_count": len(utilities.get_e102_objects()),
        "components": components
    }


# ============================================================
# CLEANUP
# ============================================================

def remove_geometry():
    clear_equipment()


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

def create_heat_exchanger_geometry(*args, **kwargs):
    return build_geometry(*args, **kwargs)
