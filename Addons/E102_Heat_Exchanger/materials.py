
"""Materials for the E-102 shell-and-tube heat exchanger.

Blender 5.2 compatible.
Provides reusable industrial materials for equipment geometry,
process-fluid visualization and transparent inspection views.
"""

import bpy


# ============================================================
# MATERIAL COLOURS
# ============================================================

MATERIAL_COLORS = {
    # Main equipment
    "E102_Stainless_Steel": (0.48, 0.53, 0.58, 1.0),
    "E102_Polished_Steel": (0.72, 0.77, 0.82, 1.0),
    "E102_Dark_Steel": (0.12, 0.15, 0.18, 1.0),

    # Equipment components
    "E102_Tube_Sheet": (0.58, 0.63, 0.67, 1.0),
    "E102_Baffle_Steel": (0.38, 0.44, 0.49, 1.0),
    "E102_Flange_Steel": (0.52, 0.57, 0.62, 1.0),
    "E102_Nozzle_Steel": (0.46, 0.52, 0.57, 1.0),
    "E102_Bolt_Steel": (0.30, 0.34, 0.38, 1.0),

    # Transparent shell
    "E102_Transparent_Blue": (0.18, 0.48, 0.72, 0.12),
    # Process fluids
    "E102_WCO": (0.35, 0.19, 0.055, 1.0),
    "E102_Hot_Water": (0.90, 0.18, 0.045, 1.0),
    "E102_Cold_Water": (0.04, 0.32, 0.88, 1.0),

    # Other materials
    "E102_Gasket": (0.055, 0.065, 0.075, 1.0),
    "E102_Insulation": (0.58, 0.49, 0.32, 1.0),
    "E102_Concrete": (0.28, 0.29, 0.30, 1.0),

    # Labels and highlights
    "E102_Label_White": (0.92, 0.94, 0.96, 1.0),
    "E102_Label_Gold": (0.83, 0.57, 0.12, 1.0),
    "E102_Highlight_Green": (0.12, 0.85, 0.32, 1.0),
}


# ============================================================
# MATERIAL PRESETS
# ============================================================

MATERIAL_PRESETS = {
    "stainless_steel": {
        "color": MATERIAL_COLORS["E102_Stainless_Steel"],
        "metallic": 0.85,
        "roughness": 0.28,
    },
    "polished_steel": {
        "color": MATERIAL_COLORS["E102_Polished_Steel"],
        "metallic": 0.95,
        "roughness": 0.16,
    },
    "dark_steel": {
        "color": MATERIAL_COLORS["E102_Dark_Steel"],
        "metallic": 0.75,
        "roughness": 0.38,
    },
    "tube_sheet": {
        "color": MATERIAL_COLORS["E102_Tube_Sheet"],
        "metallic": 0.85,
        "roughness": 0.30,
    },
    "baffle_steel": {
        "color": MATERIAL_COLORS["E102_Baffle_Steel"],
        "metallic": 0.80,
        "roughness": 0.34,
    },
    "flange_steel": {
        "color": MATERIAL_COLORS["E102_Flange_Steel"],
        "metallic": 0.85,
        "roughness": 0.27,
    },
    "nozzle_steel": {
        "color": MATERIAL_COLORS["E102_Nozzle_Steel"],
        "metallic": 0.85,
        "roughness": 0.29,
    },
    "bolt_steel": {
        "color": MATERIAL_COLORS["E102_Bolt_Steel"],
        "metallic": 0.90,
        "roughness": 0.24,
    },
    "transparent_blue": {
        "color": MATERIAL_COLORS["E102_Transparent_Blue"],
        "metallic": 0.15,
        "roughness": 0.20,
    },
    "wco": {
        "color": MATERIAL_COLORS["E102_WCO"],
        "metallic": 0.0,
        "roughness": 0.30,
    },
    "hot_water": {
        "color": MATERIAL_COLORS["E102_Hot_Water"],
        "metallic": 0.0,
        "roughness": 0.25,
    },
    "cold_water": {
        "color": MATERIAL_COLORS["E102_Cold_Water"],
        "metallic": 0.0,
        "roughness": 0.25,
    },
    "gasket": {
        "color": MATERIAL_COLORS["E102_Gasket"],
        "metallic": 0.05,
        "roughness": 0.72,
    },
    "insulation": {
        "color": MATERIAL_COLORS["E102_Insulation"],
        "metallic": 0.0,
        "roughness": 0.85,
    },
    "concrete": {
        "color": MATERIAL_COLORS["E102_Concrete"],
        "metallic": 0.0,
        "roughness": 0.90,
    },
    "label_white": {
        "color": MATERIAL_COLORS["E102_Label_White"],
        "metallic": 0.0,
        "roughness": 0.50,
    },
    "label_gold": {
        "color": MATERIAL_COLORS["E102_Label_Gold"],
        "metallic": 0.65,
        "roughness": 0.30,
    },
    "highlight_green": {
        "color": MATERIAL_COLORS["E102_Highlight_Green"],
        "metallic": 0.0,
        "roughness": 0.35,
    },
}


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _set_principled_input(bsdf, possible_names, value):
    """Set a Principled BSDF input using compatible socket names."""

    if bsdf is None:
        return

    for name in possible_names:
        socket = bsdf.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return



def _configure_transparency(mat, alpha):
    """Configure Eevee transparency for Blender 5.x."""

    if alpha >= 0.999:
        return

    mat.diffuse_color = (
        mat.diffuse_color[0],
        mat.diffuse_color[1],
        mat.diffuse_color[2],
        alpha,
    )

    # Blender 5.x Eevee uses DITHERED surface transparency.
    try:
        mat.surface_render_method = 'DITHERED'
    except (AttributeError, TypeError, ValueError):
        # Compatibility fallback for Blender builds exposing BLENDED.
        try:
            mat.surface_render_method = 'BLENDED'
        except (AttributeError, TypeError, ValueError):
            pass

    try:
        mat.use_transparency_overlap = False
    except (AttributeError, TypeError, ValueError):
        pass

    try:
        mat.show_transparent_back = True
    except (AttributeError, TypeError, ValueError):
        pass


# ============================================================
# MATERIAL CREATION
# ============================================================

def material(
    name,
    color,
    alpha=1.0,
    metallic=0.0,
    roughness=0.5,
):
    """Create or update a material."""

    mat = bpy.data.materials.get(name)

    if mat is None:
        mat = bpy.data.materials.new(name=name)

    mat.diffuse_color = (
        color[0],
        color[1],
        color[2],
        alpha,
    )

    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")

    if bsdf is None:
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")

    _set_principled_input(
        bsdf,
        ["Base Color"],
        (color[0], color[1], color[2], 1.0),
    )

    _set_principled_input(
        bsdf,
        ["Alpha"],
        alpha,
    )

    _set_principled_input(
        bsdf,
        ["Metallic"],
        metallic,
    )

    _set_principled_input(
        bsdf,
        ["Roughness"],
        roughness,
    )

    if alpha < 0.999:
        _configure_transparency(mat, alpha)

    return mat


# ============================================================
# CREATE ALL E-102 MATERIALS
# ============================================================

def create_materials():
    """Create the complete E-102 material library.

    Existing dictionary keys are preserved for compatibility
    with geometry.py and other add-on modules.
    """

    materials = {}

    for key, preset in MATERIAL_PRESETS.items():

        mat = material(
            name="E102_" + key.replace("_", " ").title().replace(" ", "_"),
            color=preset["color"],
            alpha=preset["color"][3],
            metallic=preset["metallic"],
            roughness=preset["roughness"],
        )

        materials[key] = mat

    # Preserve the original material names and keys.
    # These aliases allow existing geometry code to continue
    # requesting the original materials.

    original_materials = {
        "stainless_steel": "E102_Stainless_Steel",
        "polished_steel": "E102_Polished_Steel",
        "dark_steel": "E102_Dark_Steel",
        "transparent_blue": "E102_Transparent_Blue",
        "wco": "E102_WCO",
        "hot_water": "E102_Hot_Water",
        "cold_water": "E102_Cold_Water",
        "gasket": "E102_Gasket",
        "insulation": "E102_Insulation",
        "concrete": "E102_Concrete",
        "label_white": "E102_Label_White",
        "label_gold": "E102_Label_Gold",
        "highlight_green": "E102_Highlight_Green",
    }

    for key, name in original_materials.items():

        preset = MATERIAL_PRESETS[key]

        materials[key] = material(
            name=name,
            color=preset["color"],
            alpha=preset["color"][3],
            metallic=preset["metallic"],
            roughness=preset["roughness"],
        )

    # Additional industrial component materials.
    materials["tube_sheet"] = material(
        "E102_Tube_Sheet",
        MATERIAL_COLORS["E102_Tube_Sheet"],
        metallic=0.85,
        roughness=0.30,
    )

    materials["baffle_steel"] = material(
        "E102_Baffle_Steel",
        MATERIAL_COLORS["E102_Baffle_Steel"],
        metallic=0.80,
        roughness=0.34,
    )

    materials["flange_steel"] = material(
        "E102_Flange_Steel",
        MATERIAL_COLORS["E102_Flange_Steel"],
        metallic=0.85,
        roughness=0.27,
    )

    materials["nozzle_steel"] = material(
        "E102_Nozzle_Steel",
        MATERIAL_COLORS["E102_Nozzle_Steel"],
        metallic=0.85,
        roughness=0.29,
    )

    materials["bolt_steel"] = material(
        "E102_Bolt_Steel",
        MATERIAL_COLORS["E102_Bolt_Steel"],
        metallic=0.90,
        roughness=0.24,
    )

    return materials


# ============================================================
# MATERIAL ACCESS
# ============================================================

def get_material(name):
    """Return an existing material by name."""

    return bpy.data.materials.get(name)


def assign_material(obj, mat):
    """Assign a material to an object."""

    if obj is None or mat is None:
        return False

    if not hasattr(obj.data, "materials"):
        return False

    obj.data.materials.clear()
    obj.data.materials.append(mat)

    return True


def assign_material_by_key(obj, materials, key):
    """Assign a material using a key from create_materials()."""

    if materials is None:
        return False

    mat = materials.get(key)

    if mat is None:
        return False

    return assign_material(obj, mat)


# ============================================================
# MATERIAL CLEANUP
# ============================================================

def remove_unused_e102_materials():
    """Remove unused E-102 materials."""

    removed = 0

    for mat in list(bpy.data.materials):

        if not mat.name.startswith("E102_"):
            continue

        if mat.users == 0:
            bpy.data.materials.remove(mat)
            removed += 1

    return removed


# ============================================================
# INITIALIZATION
# ============================================================

def initialize_materials():
    """Initialize and return all E-102 materials."""

    return create_materials()
