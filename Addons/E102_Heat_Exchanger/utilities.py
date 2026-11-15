
"""
E-102 Shell-and-Tube Heat Exchanger
utilities.py

Reusable Blender utility functions.

Functions include:
- Collection management
- Mesh creation
- Box and cylinder generation
- Text creation
- Object transformation
- Bevel modifiers
- Smooth shading
- E-102 model cleanup

This module contains no engineering calculations.
"""

import bpy
import math

from mathutils import Vector, Quaternion


# ============================================================
# GLOBAL SETTINGS
# ============================================================

E102_COLLECTION_NAME = "E102_Heat_Exchanger"

E102_OBJECT_PREFIX = "E102_"


# ============================================================
# COLLECTION MANAGEMENT
# ============================================================

def get_or_create_collection(
    name=E102_COLLECTION_NAME,
    parent=None,
):
    """
    Retrieve an existing collection or create a new one.

    Args:
        name: Collection name.
        parent: Parent collection. Defaults to scene collection.

    Returns:
        bpy.types.Collection
    """

    collection = bpy.data.collections.get(name)

    if collection is None:
        collection = bpy.data.collections.new(name)

    if parent is None:
        parent = bpy.context.scene.collection

    if collection.name not in parent.children:
        parent.children.link(collection)

    return collection


def get_e102_collection():
    """
    Retrieve the main E-102 collection.
    """

    return get_or_create_collection(
        E102_COLLECTION_NAME
    )


def create_subcollection(name):
    """
    Create a subcollection inside the main E-102 collection.
    """

    parent = get_e102_collection()

    full_name = f"E102_{name}"

    return get_or_create_collection(
        full_name,
        parent,
    )


def link_object(obj, collection=None):
    """
    Link an object to a specified collection.

    If no collection is specified, the main E-102
    collection is used.
    """

    if obj is None:
        return

    if collection is None:
        collection = get_e102_collection()

    if collection not in obj.users_collection:
        collection.objects.link(obj)


# ============================================================
# OBJECT MANAGEMENT
# ============================================================

def set_object_name(obj, name):
    """
    Assign a consistent E-102 object name.
    """

    if obj is None:
        return

    if not name.startswith(E102_OBJECT_PREFIX):
        name = E102_OBJECT_PREFIX + name

    obj.name = name

    return obj


def set_object_location(obj, location):
    """
    Set object location.
    """

    if obj is not None:
        obj.location = Vector(location)

    return obj


def set_object_rotation(obj, rotation):
    """
    Set object rotation in radians.

    Args:
        rotation: Euler rotation tuple.
    """

    if obj is not None:
        obj.rotation_euler = rotation

    return obj


def set_object_scale(obj, scale):
    """
    Set object scale.
    """

    if obj is not None:
        obj.scale = Vector(scale)

    return obj


# ============================================================
# GENERIC MESH CREATION
# ============================================================

def create_mesh_object(
    name,
    vertices,
    faces,
    collection=None,
):
    """
    Create a Blender mesh object directly from vertices and faces.

    This avoids relying on Blender primitive-add operators.

    Args:
        name: Object name.
        vertices: List of vertex coordinates.
        faces: List of face vertex indices.
        collection: Destination collection.

    Returns:
        bpy.types.Object
    """

    mesh = bpy.data.meshes.new(
        f"{name}_Mesh"
    )

    mesh.from_pydata(
        vertices,
        [],
        faces,
    )

    mesh.validate()
    mesh.update()

    obj = bpy.data.objects.new(
        name,
        mesh,
    )

    if collection is None:
        collection = get_e102_collection()

    collection.objects.link(obj)

    return obj


# ============================================================
# BOX CREATION
# ============================================================

def create_box(
    name,
    location=(0.0, 0.0, 0.0),
    dimensions=(1.0, 1.0, 1.0),
    collection=None,
):
    """
    Create a rectangular box using mesh geometry.

    Dimensions are actual dimensions in Blender units.
    """

    x, y, z = dimensions

    hx = x / 2.0
    hy = y / 2.0
    hz = z / 2.0

    vertices = [
        (-hx, -hy, -hz),
        ( hx, -hy, -hz),
        ( hx,  hy, -hz),
        (-hx,  hy, -hz),

        (-hx, -hy,  hz),
        ( hx, -hy,  hz),
        ( hx,  hy,  hz),
        (-hx,  hy,  hz),
    ]

    faces = [
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    ]

    obj = create_mesh_object(
        name,
        vertices,
        faces,
        collection,
    )

    obj.location = location

    return obj


# ============================================================
# CYLINDER CREATION
# ============================================================

def create_cylinder(
    name,
    radius=0.5,
    depth=1.0,
    location=(0.0, 0.0, 0.0),
    vertices_count=48,
    axis=(0.0, 0.0, 1.0),
    collection=None,
):
    """
    Create a cylinder along an arbitrary axis.

    The cylinder is generated along its local Z-axis
    and then rotated to the requested direction.

    Args:
        name: Object name.
        radius: Cylinder radius.
        depth: Cylinder length.
        location: Cylinder centre.
        vertices_count: Circumferential resolution.
        axis: Direction vector.
        collection: Destination collection.
    """

    if radius <= 0:
        raise ValueError("Cylinder radius must be positive.")

    if depth <= 0:
        raise ValueError("Cylinder depth must be positive.")

    if vertices_count < 3:
        raise ValueError("Cylinder requires at least 3 vertices.")

    axis_vector = Vector(axis)

    if axis_vector.length == 0:
        raise ValueError("Cylinder axis cannot be zero.")

    axis_vector.normalize()

    half_depth = depth / 2.0

    vertices = []

    for z in (-half_depth, half_depth):

        for i in range(vertices_count):

            angle = (
                2.0 * math.pi * i / vertices_count
            )

            x = radius * math.cos(angle)
            y = radius * math.sin(angle)

            vertices.append(
                (x, y, z)
            )

    faces = []

    # Bottom cap
    faces.append(
        tuple(reversed(range(vertices_count)))
    )

    # Top cap
    faces.append(
        tuple(
            range(
                vertices_count,
                2 * vertices_count,
            )
        )
    )

    # Side surfaces
    for i in range(vertices_count):

        next_i = (i + 1) % vertices_count

        faces.append(
            (
                i,
                next_i,
                next_i + vertices_count,
                i + vertices_count,
            )
        )

    obj = create_mesh_object(
        name,
        vertices,
        faces,
        collection,
    )

    rotation = Vector((0.0, 0.0, 1.0)).rotation_difference(
        axis_vector
    )

    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = rotation

    obj.location = location

    return obj


# ============================================================
# HOLLOW CYLINDER CREATION
# ============================================================

def create_hollow_cylinder(
    name,
    outer_radius,
    inner_radius,
    depth,
    location=(0.0, 0.0, 0.0),
    vertices_count=48,
    axis=(0.0, 0.0, 1.0),
    collection=None,
):
    """
    Create a hollow cylindrical component.

    Useful for:
    - Nozzles
    - Pipe sections
    - Short cylindrical connectors

    The cylinder has open ends and a visible wall thickness.
    """

    if outer_radius <= inner_radius:
        raise ValueError(
            "Outer radius must be greater than inner radius."
        )

    if inner_radius <= 0:
        raise ValueError(
            "Inner radius must be positive."
        )

    if depth <= 0:
        raise ValueError(
            "Depth must be positive."
        )

    axis_vector = Vector(axis)

    if axis_vector.length == 0:
        raise ValueError("Cylinder axis cannot be zero.")

    axis_vector.normalize()

    half_depth = depth / 2.0

    vertices = []

    # Four circular rings:
    # Outer bottom, outer top, inner bottom, inner top.

    rings = [
        (outer_radius, -half_depth),
        (outer_radius, half_depth),
        (inner_radius, -half_depth),
        (inner_radius, half_depth),
    ]

    for radius, z in rings:

        for i in range(vertices_count):

            angle = (
                2.0 * math.pi * i / vertices_count
            )

            vertices.append(
                (
                    radius * math.cos(angle),
                    radius * math.sin(angle),
                    z,
                )
            )

    faces = []

    outer_bottom = 0
    outer_top = vertices_count
    inner_bottom = 2 * vertices_count
    inner_top = 3 * vertices_count

    for i in range(vertices_count):

        j = (i + 1) % vertices_count

        # Outer cylindrical wall
        faces.append(
            (
                outer_bottom + i,
                outer_bottom + j,
                outer_top + j,
                outer_top + i,
            )
        )

        # Inner cylindrical wall
        faces.append(
            (
                inner_bottom + j,
                inner_bottom + i,
                inner_top + i,
                inner_top + j,
            )
        )

        # Bottom annular face
        faces.append(
            (
                outer_bottom + j,
                outer_bottom + i,
                inner_bottom + i,
                inner_bottom + j,
            )
        )

        # Top annular face
        faces.append(
            (
                outer_top + i,
                outer_top + j,
                inner_top + j,
                inner_top + i,
            )
        )

    obj = create_mesh_object(
        name,
        vertices,
        faces,
        collection,
    )

    obj.rotation_mode = 'QUATERNION'

    obj.rotation_quaternion = (
        Vector((0.0, 0.0, 1.0))
        .rotation_difference(axis_vector)
    )

    obj.location = location

    return obj


# ============================================================
# TEXT CREATION
# ============================================================

def make_text(
    name,
    body,
    location=(0.0, 0.0, 0.0),
    size=0.1,
    rotation=(0.0, 0.0, 0.0),
    collection=None,
    align_x='CENTER',
    align_y='CENTER',
):
    """
    Create a 3D text object.

    Useful for:
    - Equipment tags
    - Nozzle labels
    - Temperature indicators
    - Flow direction labels
    """

    curve = bpy.data.curves.new(
        name=f"{name}_TextData",
        type='FONT',
    )

    curve.body = str(body)
    curve.size = size
    curve.align_x = align_x
    curve.align_y = align_y

    curve.extrude = 0.001

    obj = bpy.data.objects.new(
        name,
        curve,
    )

    if collection is None:
        collection = get_e102_collection()

    collection.objects.link(obj)

    obj.location = location
    obj.rotation_euler = rotation

    return obj


# ============================================================
# BEVEL MODIFIER
# ============================================================

def add_bevel(
    obj,
    width=0.02,
    segments=3,
):
    """
    Add a bevel modifier to an object.
    """

    if obj is None:
        return None

    bevel = obj.modifiers.new(
        name="E102_Bevel",
        type='BEVEL',
    )

    bevel.width = width
    bevel.segments = segments

    bevel.limit_method = 'ANGLE'

    return bevel


# ============================================================
# SMOOTH SHADING
# ============================================================

def set_smooth_shading(obj):
    """
    Enable smooth shading for mesh polygons.
    """

    if obj is None or obj.type != 'MESH':
        return

    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def set_flat_shading(obj):
    """
    Enable flat shading for mesh polygons.
    """

    if obj is None or obj.type != 'MESH':
        return

    for polygon in obj.data.polygons:
        polygon.use_smooth = False


# ============================================================
# APPLY OBJECT TRANSFORMS
# ============================================================

def apply_object_transforms(
    obj,
    location=False,
    rotation=False,
    scale=True,
):
    """
    Apply selected transforms directly to mesh data.

    This avoids dependence on bpy.ops and active-object context.

    Note:
        Applying location and rotation modifies mesh coordinates
        while retaining the object's visible world position.
    """

    if obj is None or obj.type != 'MESH':
        return

    from mathutils import Matrix

    transform = Matrix.Identity(4)

    if location:
        transform = (
            Matrix.Translation(obj.location)
            @ transform
        )

    if rotation:
        transform = (
            obj.rotation_euler.to_matrix().to_4x4()
            @ transform
        )

    if scale:
        transform = (
            Matrix.Diagonal(
                (
                    obj.scale.x,
                    obj.scale.y,
                    obj.scale.z,
                    1.0,
                )
            )
            @ transform
        )

    obj.data.transform(transform)

    if location:
        obj.location = (0.0, 0.0, 0.0)

    if rotation:
        obj.rotation_euler = (0.0, 0.0, 0.0)

    if scale:
        obj.scale = (1.0, 1.0, 1.0)

    obj.data.update()


# ============================================================
# OBJECT VISIBILITY
# ============================================================

def set_object_visibility(
    obj,
    visible=True,
):
    """
    Set viewport and render visibility.
    """

    if obj is None:
        return

    obj.hide_viewport = not visible
    obj.hide_render = not visible


# ============================================================
# COLLECTION VISIBILITY
# ============================================================

def set_collection_visibility(
    collection,
    visible=True,
):
    """
    Set visibility for all objects in a collection.
    """

    if collection is None:
        return

    for obj in collection.objects:
        set_object_visibility(
            obj,
            visible,
        )


# ============================================================
# CLEAN GENERATED E102 OBJECTS
# ============================================================

def clear_collection(collection):
    """
    Remove all objects directly linked to a collection.

    Objects linked to other collections are unlinked from
    this collection but not deleted while other users remain.
    """

    if collection is None:
        return

    for obj in list(collection.objects):

        bpy.data.objects.remove(
            obj,
            do_unlink=True,
        )


def clear_e102_model():
    """
    Clear the generated E-102 model.

    This function removes objects from the main E-102
    collection and its child collections.

    It does not remove unrelated scene objects.
    """

    collection = bpy.data.collections.get(
        E102_COLLECTION_NAME
    )

    if collection is None:
        return

    def remove_objects_recursive(current_collection):

        for child in list(current_collection.children):
            remove_objects_recursive(child)

        clear_collection(current_collection)

    remove_objects_recursive(collection)


# ============================================================
# OBJECT LOOKUP
# ============================================================

def get_object(name):
    """
    Retrieve an object by name.
    """

    return bpy.data.objects.get(name)


def get_e102_objects():
    """
    Return all objects belonging to the E-102 collection
    and its nested collections.
    """

    root = bpy.data.collections.get(
        E102_COLLECTION_NAME
    )

    if root is None:
        return []

    objects = []

    def collect(current_collection):

        objects.extend(
            list(current_collection.objects)
        )

        for child in current_collection.children:
            collect(child)

    collect(root)

    # Remove duplicates while preserving order.
    return list(dict.fromkeys(objects))


# ============================================================
# OBJECT COUNT
# ============================================================

def count_e102_objects():
    """
    Count all objects in the E-102 model.
    """

    return len(get_e102_objects())


# ============================================================
# MODEL STATUS
# ============================================================

def print_model_status():
    """
    Print a simple E-102 model status report.
    """

    objects = get_e102_objects()

    print("\n" + "=" * 50)
    print("E-102 HEAT EXCHANGER MODEL STATUS")
    print("=" * 50)

    print("Total generated objects:", len(objects))

    for obj in objects:
        print(
            f"{obj.name:<35} {obj.type}"
        )

    print("=" * 50)


# ============================================================
# GENERAL INITIALIZATION
# ============================================================

def initialize_utilities():
    """
    Initialize the main E-102 collection.
    """

    return get_e102_collection()
