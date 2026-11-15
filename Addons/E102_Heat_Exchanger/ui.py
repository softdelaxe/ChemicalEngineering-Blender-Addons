
"""
============================================================
E-102 HEAT EXCHANGER DESIGNER
ui.py

Blender 5.2 compatible user interface.

Provides:
    - Process design inputs
    - Fluid properties
    - Thermal design parameters
    - Equipment geometry
    - Engineering calculation results
    - Design warnings
    - Equipment generation
    - Flow visualization controls
    - Exploded and assembled views

Engineering calculations are handled by calculations.py.
Scene input properties are handled by properties.py.
============================================================
"""

import bpy


# ============================================================
# PANEL SETTINGS
# ============================================================

PANEL_CATEGORY = "E-102"
PANEL_LABEL = "E-102 Engineering"
PANEL_ID = "VIEW3D_PT_E102_Engineering"


# ============================================================
# PROPERTY ACCESS
# ============================================================

def get_design_properties(context):
    """Return the E-102 property group from the active scene."""

    scene = getattr(context, "scene", None)

    if scene is None:
        return None

    return getattr(scene, "e102_design", None)


def draw_property(layout, properties, property_names, label=None):
    """
    Draw a property if it exists.

    property_names can be a single property name or a list
    of possible property names.
    """

    if properties is None:
        return False

    if isinstance(property_names, str):
        property_names = [property_names]

    for property_name in property_names:

        if hasattr(properties, property_name):

            layout.prop(
                properties,
                property_name,
                text=label if label else ""
            )

            return True

    return False


def draw_section_header(layout, title, icon="NONE"):
    """Draw a section heading."""

    row = layout.row()
    row.label(text=title, icon=icon)


def draw_operator_button(
    layout,
    operator_id,
    text,
    icon="NONE",
    enabled=True
):
    """Draw an operator button."""

    row = layout.row()
    row.enabled = enabled

    row.operator(
        operator_id,
        text=text,
        icon=icon
    )


def draw_result_row(layout, label, value, precision=3, unit=""):
    """Draw a formatted engineering result."""

    row = layout.row(align=True)

    row.label(text=label)

    row.alignment = "RIGHT"

    row.label(
        text=f"{value:.{precision}f} {unit}".strip()
    )


# ============================================================
# 1. PROCESS DESIGN
# ============================================================

def draw_process_design(layout, properties):

    box = layout.box()

    draw_section_header(
        box,
        "Process Design",
        "INFO"
    )

    # --------------------------------------------------------
    # COLD / PROCESS FLUID
    # --------------------------------------------------------

    col = box.column(align=True)

    col.label(
        text="Cold / Process Fluid",
        icon="MOD_FLUID"
    )

    col.prop(
        properties,
        "process_fluid_type",
        text="Process Fluid"
    )

    if properties.process_fluid_type == "custom":

        col.prop(
            properties,
            "custom_process_fluid_name",
            text="Fluid Name"
        )

    draw_property(
        col,
        properties,
        "wco_mass_flow_kg_h",
        "Mass Flow Rate (kg/h)"
    )

    draw_property(
        col,
        properties,
        "wco_inlet_temp_c",
        "Inlet Temperature (°C)"
    )

    draw_property(
        col,
        properties,
        "wco_outlet_temp_c",
        "Outlet Temperature (°C)"
    )

    box.separator()

    # --------------------------------------------------------
    # HEATING MEDIUM
    # --------------------------------------------------------

    col = box.column(align=True)

    col.label(
        text="Heating Medium",
        icon="MOD_FLUID"
    )

    col.prop(
        properties,
        "heating_medium_type",
        text="Heating Medium"
    )

    medium = properties.heating_medium_type

    draw_property(
        col,
        properties,
        "heating_medium_inlet_temp_c",
        "Inlet Temperature (°C)"
    )

    if medium != "steam":

        draw_property(
            col,
            properties,
            "heating_medium_outlet_temp_c",
            "Outlet Temperature (°C)"
        )

        draw_property(
            col,
            properties,
            "heating_medium_cp_kj_kg_k",
            "Specific Heat (kJ/kg·K)"
        )

        draw_property(
            col,
            properties,
            "heating_medium_density_kg_m3",
            "Density (kg/m³)"
        )

        draw_property(
            col,
            properties,
            "heating_medium_viscosity_pa_s",
            "Dynamic Viscosity (Pa·s)"
        )

    else:

        draw_property(
            col,
            properties,
            "heating_medium_latent_heat_kj_kg",
            "Latent Heat (kJ/kg)"
        )

    draw_property(
        col,
        properties,
        "heating_medium_pressure_bar",
        "Operating Pressure (bar)"
    )

    box.separator()

    # --------------------------------------------------------
    # DESIGN SETTINGS
    # --------------------------------------------------------

    col = box.column(align=True)

    col.label(
        text="Design Settings",
        icon="MODIFIER"
    )

    draw_property(
        col,
        properties,
        "design_factor",
        "Design Factor"
    )

    # --------------------------------------------------------
    # INFORMATION
    # --------------------------------------------------------

    box.separator()

    box.label(
        text="Temperature inputs are in degrees Celsius (°C).",
        icon="INFO"
    )

    box.label(
        text="Set an override to 0 to use the selected",
        icon="INFO"
    )

    box.label(
        text="heating medium's illustrative default."
    )


def draw_fluid_properties(layout, properties):
    """Display process-fluid properties and their reference information."""

    box = layout.box()

    draw_section_header(
        box,
        "Cold / Process Fluid Properties",
        "INFO"
    )

    # --------------------------------------------------------
    # NUMERICAL PROPERTIES
    # --------------------------------------------------------

    col = box.column(align=True)

    draw_property(
        col,
        properties,
        "wco_cp_kj_kg_k",
        "Specific Heat (kJ/kg·K)"
    )

    draw_property(
        col,
        properties,
        "wco_density_kg_m3",
        "Density (kg/m³)"
    )

    draw_property(
        col,
        properties,
        "wco_viscosity_pa_s",
        "Dynamic Viscosity (Pa·s)"
    )

    box.separator()

    # --------------------------------------------------------
    # PROPERTY REFERENCE INFORMATION
    # --------------------------------------------------------

    reference_box = box.box()

    reference_box.label(
        text="Fluid Property Reference",
        icon="BOOKMARKS"
    )

    # Reference temperature
    draw_property(
        reference_box,
        properties,
        "process_fluid_reference_temp_c",
        "Reference Temperature (°C)"
    )

    # Property data status
    status = getattr(
        properties,
        "process_fluid_status",
        "estimated"
    )

    status_labels = {
        "reference_backed": "Reference-backed data",
        "estimated": "Estimated data"
    }

    status_label = status_labels.get(
        status,
        str(status).replace("_", " ").title()
    )

    reference_box.label(
        text=f"Data Status: {status_label}",
        icon="INFO"
    )

    # Fluid composition
    composition = getattr(
        properties,
        "process_fluid_composition",
        ""
    )

    if composition:
        reference_box.label(
            text=f"Composition: {composition}"
        )

    # Source name
    source = getattr(
        properties,
        "process_fluid_source",
        ""
    )

    if source:
        reference_box.label(
            text=f"Source: {source}"
        )

    # Source URL
    source_url = getattr(
        properties,
        "process_fluid_source_url",
        ""
    )

    if source_url.startswith(("http://", "https://")):

        row = reference_box.row()

        operator = row.operator(
            "wm.url_open",
            text="Open Property Reference",
            icon="URL"
        )

        operator.url = source_url

    # Additional notes
    note = getattr(
        properties,
        "process_fluid_note",
        ""
    )

    if note:
        reference_box.separator()
        reference_box.label(
            text="Property Notes:",
            icon="INFO"
        )

        for line in note.splitlines():
            if line.strip():
                reference_box.label(text=line)

    # Engineering caution
    box.separator()

    box.label(
        text="Verify properties at actual operating conditions.",
        icon="ERROR"
    )

    box.label(
        text="Values are not automatically temperature-dependent."
    )


def draw_thermal_design(layout, properties):
    box = layout.box()
    draw_section_header(box, "Thermal Design", "MODIFIER")
    draw_property(box, properties, "overall_heat_transfer_coefficient_w_m2_k", "Overall U (W/m²·K)")
    draw_property(box, properties, "tube_fouling_resistance_m2_k_w", "Tube Fouling Resistance (m²·K/W)")
    draw_property(box, properties, "shell_fouling_resistance_m2_k_w", "Shell Fouling Resistance (m²·K/W)")
    draw_property(box, properties, "flow_arrangement", "Flow Arrangement")
    box.label(text="U is user-supplied; film coefficients are not independently rated.", icon="INFO")


# ============================================================
# 4. EQUIPMENT GEOMETRY
# ============================================================

def draw_equipment_geometry(layout, properties):

    box = layout.box()

    draw_section_header(
        box,
        "Equipment Geometry",
        "MESH_DATA"
    )

    # --------------------------------------------------------
    # SHELL
    # --------------------------------------------------------

    col = box.column(align=True)

    col.label(text="Shell")

    draw_property(
        col,
        properties,
        "shell_internal_diameter_m",
        "Internal Diameter (m)"
    )

    draw_property(
        col,
        properties,
        "shell_wall_thickness_m",
        "Wall Thickness (m)"
    )

    draw_property(
        col,
        properties,
        "shell_passes",
        "Shell Passes"
    )

    box.separator()

    # --------------------------------------------------------
    # TUBE BUNDLE
    # --------------------------------------------------------

    col = box.column(align=True)

    col.label(text="Tube Bundle")

    draw_property(
        col,
        properties,
        "tube_outside_diameter_m",
        "Outside Diameter (m)"
    )

    draw_property(
        col,
        properties,
        "tube_wall_thickness_m",
        "Wall Thickness (m)"
    )

    draw_property(
        col,
        properties,
        "tube_length_m",
        "Tube Length (m)"
    )

    draw_property(
        col,
        properties,
        "number_of_tubes",
        "Number of Tubes"
    )

    draw_property(
        col, properties, "auto_size_tubes", "Automatically Size Tube Count"
    )
    draw_property(
        col, properties, "tube_layout", "Tube Layout"
    )

    draw_property(
        col,
        properties,
        "tube_passes",
        "Tube Passes"
    )

    draw_property(
        col,
        properties,
        "tube_pitch_m",
        "Tube Pitch (m)"
    )

    box.separator()

    # --------------------------------------------------------
    # BAFFLES
    # --------------------------------------------------------

    col = box.column(align=True)

    col.label(text="Shell-Side Internals")

    draw_property(
        col,
        properties,
        "baffle_count",
        "Number of Baffles"
    )

    draw_property(
        col,
        properties,
        "baffle_cut_fraction",
        "Baffle Cut Fraction"
    )

    box.separator()

    # --------------------------------------------------------
    # CHANNEL HEADS AND TUBESHEETS
    # --------------------------------------------------------

    col = box.column(align=True)

    col.label(text="Heads and Tubesheets")

    draw_property(
        col,
        properties,
        "channel_head_length_m",
        "Channel Head Length (m)"
    )

    draw_property(
        col,
        properties,
        "tubesheet_thickness_m",
        "Tubesheet Thickness (m)"
    )


# ============================================================
# 5. CALCULATION RESULTS
# ============================================================

def draw_calculation_results(layout, context):

    box = layout.box()

    draw_section_header(
        box,
        "Engineering Results",
        "INFO"
    )

    scene = context.scene
    medium_name = scene.get("e102_last_heating_medium_name", "Selected heating medium")
    box.label(text=f"Heating medium: {medium_name}")

    completed = scene.get(
        "e102_calculations_completed",
        False
    )

    if not completed:

        box.label(
            text="No calculation results available.",
            icon="INFO"
        )

        box.label(
            text="Enter design inputs and run calculations."
        )

        return

    # --------------------------------------------------------
    # PROCESS AND DESIGN DUTY
    # --------------------------------------------------------

    col = box.column(align=True)

    col.label(
        text="Thermal Performance",
        icon="INFO"
    )

    draw_result_row(
        col,
        "Process Duty",
        scene.get("e102_last_process_duty_kw", 0.0),
        3,
        "kW"
    )

    draw_result_row(
        col,
        "Design Duty",
        scene.get("e102_last_design_duty_kw", 0.0),
        3,
        "kW"
    )

    box.separator()

    # --------------------------------------------------------
    # HEAT TRANSFER AREA
    # --------------------------------------------------------

    col = box.column(align=True)

    col.label(
        text="Heat Transfer Area",
        icon="SURFACE_DATA"
    )

    required_area = scene.get(
        "e102_last_required_area_m2",
        scene.get("e102_last_area_m2", 0.0)
    )

    installed_area = scene.get(
        "e102_last_installed_area_m2",
        0.0
    )

    draw_result_row(
        col,
        "Required Area",
        required_area,
        3,
        "m²"
    )

    draw_result_row(
        col,
        "Installed Area",
        installed_area,
        3,
        "m²"
    )

    area_difference = installed_area - required_area

    draw_result_row(
        col,
        "Area Difference",
        area_difference,
        3,
        "m²"
    )

    if area_difference >= 0:

        col.label(
            text="Installed area meets calculated area.",
            icon="CHECKMARK"
        )

    else:

        col.label(
            text="Installed area is below calculated area.",
            icon="ERROR"
        )

    box.separator()

    # --------------------------------------------------------
    # WATER REQUIREMENT
    # --------------------------------------------------------

    col = box.column(align=True)

    col.label(
        text="Heating-Medium Requirement",
        icon="MOD_FLUID"
    )

    draw_result_row(
        col,
        "Actual Medium Flow",
        scene.get("e102_last_water_flow_kg_h", 0.0),
        2,
        "kg/h"
    )

    draw_result_row(
        col,
        "Design Medium Flow",
        scene.get("e102_last_design_water_flow_kg_h", 0.0),
        2,
        "kg/h"
    )

    draw_result_row(
        col,
        "Medium Volume Flow",
        scene.get("e102_last_water_volume_flow_m3_h", 0.0),
        3,
        "m³/h"
    )

    box.separator()

    # --------------------------------------------------------
    # TEMPERATURE PERFORMANCE
    # --------------------------------------------------------

    col = box.column(align=True)

    col.label(
        text="Temperature Performance",
        icon="TEMP"
    )

    draw_result_row(
        col,
        "LMTD",
        scene.get("e102_last_lmtd_k", 0.0),
        3,
        "K"
    )

    draw_result_row(
        col,
        "Correction Factor",
        scene.get("e102_last_correction_factor", 0.0),
        4,
        ""
    )

    draw_result_row(
        col,
        "Corrected LMTD",
        scene.get("e102_last_corrected_lmtd_k", 0.0),
        3,
        "K"
    )

    box.separator()

    # --------------------------------------------------------
    # HYDRAULIC PERFORMANCE
    # --------------------------------------------------------

    col = box.column(align=True)

    col.label(
        text="WCO Tube-Side Hydraulics",
        icon="FORWARD"
    )

    draw_result_row(
        col,
        "WCO Velocity",
        scene.get("e102_last_wco_velocity_m_s", 0.0),
        4,
        "m/s"
    )

    draw_result_row(
        col,
        "Reynolds Number",
        scene.get("e102_last_reynolds_number", 0.0),
        1,
        ""
    )

    flow_regime = scene.get(
        "e102_last_flow_regime",
        "Not available"
    )

    col.label(
        text=f"Estimated Flow Regime: {flow_regime}"
    )

    box.separator()

    # --------------------------------------------------------
    # DESIGN WARNINGS
    # --------------------------------------------------------

    warning_count = scene.get(
        "e102_last_warning_count",
        0
    )

    warnings_text = scene.get(
        "e102_last_warnings",
        ""
    )

    warning_box = box.box()

    if warning_count:

        draw_section_header(
            warning_box,
            f"Design Warnings ({warning_count})",
            "ERROR"
        )

        for warning in warnings_text.splitlines():

            if warning.strip():

                warning_box.label(
                    text=warning,
                    icon="DOT"
                )

    else:

        warning_box.label(
            text="No warnings recorded.",
            icon="CHECKMARK"
        )

    status = scene.get("e102_last_feasibility", "Not calculated")
    box.label(text=f"Screening status: {status}", icon="INFO")
    box.label(
        text="Preliminary calculations only; not certified design.",
        icon="INFO"
    )


# ============================================================
# 6. CALCULATION CONTROLS
# ============================================================

def draw_calculation_controls(layout):

    box = layout.box()

    draw_section_header(
        box,
        "Engineering Calculations",
        "MODIFIER"
    )

    draw_operator_button(
        box,
        "e102.run_calculations",
        "Run Design Calculations",
        "PLAY"
    )


# ============================================================
# 7. EQUIPMENT GENERATION
# ============================================================

def draw_equipment_controls(layout):
    box = layout.box()
    draw_section_header(box, "Equipment Controls", "MESH_DATA")
    row = box.row(align=True)
    row.operator("e102.build_equipment", text="Build", icon="ADD")
    row.operator("e102.explode_equipment", text="Explode", icon="FULLSCREEN_ENTER")
    row.operator("e102.assemble_equipment", text="Assemble", icon="FULLSCREEN_EXIT")
    draw_operator_button(box, "e102.remove_equipment", "Remove E-102 Model", "TRASH")


# ============================================================
# 8. FLOW VISUALIZATION
# ============================================================

def draw_flow_controls(layout, context):

    box = layout.box()

    draw_section_header(
        box,
        "Flow Visualization",
        "PARTICLES"
    )

    box.label(
        text=f"{(get_design_properties(context).custom_process_fluid_name if get_design_properties(context).process_fluid_type == 'custom' else get_design_properties(context).process_fluid_type.replace('_', ' ').title())}: Tube Side",
        icon="FORWARD"
    )

    medium_labels = {
        "hot_water": "Hot Water",
        "steam": "Saturated Steam",
        "thermal_oil": "Thermal Oil",
        "glycol_water": "Glycol-Water",
        "hot_air": "Hot Air",
        "flue_gas": "Flue Gas",
        "molten_salt": "Molten Salt",
    }
    selected_medium = getattr(get_design_properties(context), "heating_medium_type", "hot_water")
    box.label(
        text=f"{medium_labels.get(selected_medium, 'Heating Medium')}: Shell Side",
        icon="FORWARD"
    )
    box.label(
        text="Fluid-specific colours and particle appearance",
        icon="MATERIAL"
    )
    box.label(
        text="Path is illustrative; not a CFD solution.",
        icon="INFO"
    )

    draw_operator_button(
        box,
        "e102.show_flow",
        "Build Flow Visualization",
        "ADD"
    )

    row = box.row(align=True)

    row.operator(
        "e102.show_flow_visibility",
        text="Show",
        icon="HIDE_OFF"
    )

    row.operator(
        "e102.hide_flow",
        text="Hide",
        icon="HIDE_ON"
    )

    box.separator()

    screen = context.screen

    is_playing = (
        screen is not None
        and screen.is_animation_playing
    )

    row = box.row(align=True)

    row.operator(
        "e102.toggle_flow_animation",
        text="Pause Animation" if is_playing else "Play Animation",
        icon="PAUSE" if is_playing else "PLAY"
    )

    row.operator(
        "e102.reset_flow_animation",
        text="Reset",
        icon="LOOP_BACK"
    )

    box.separator()

    box.label(
        text="Engineering flow schematic - not CFD.",
        icon="INFO"
    )


# ============================================================
# 9. EXPLODED VIEW AND ASSEMBLY
# ============================================================

def draw_assembly_controls(layout):
    box = layout.box()
    draw_section_header(box, "Assembly Utilities", "INFO")
    draw_operator_button(box, "e102.restore_equipment", "Restore Immediately", "LOOP_BACK")
    box.label(text="Explode and Assemble use the timeline animation.", icon="INFO")


# ============================================================
# 10. DESIGN INFORMATION
# ============================================================

def draw_design_information(layout, properties):

    box = layout.box()

    draw_section_header(
        box,
        "Design Information",
        "INFO"
    )

    box.label(text="Equipment: E-102")
    box.label(text="Type: Shell-and-Tube Heat Exchanger")

    # Get the selected process fluid
    fluid_type = getattr(
        properties,
        "process_fluid_type",
        "unknown"
    )

    if fluid_type == "custom":
        fluid_name = getattr(
            properties,
            "custom_process_fluid_name",
            ""
        ).strip()

        if not fluid_name:
            fluid_name = "Custom Process Fluid"

    else:
        fluid_name = str(fluid_type).replace(
            "_", " "
        ).title()

    box.label(
        text=f"Service: {fluid_name} Heating"
    )

    box.label(text="Status: Preliminary Design")

    box.separator()

    box.label(
        text="Hydraulic and mechanical validation required.",
        icon="ERROR"
    )
# ============================================================
# 11. MAIN PANEL
# ============================================================

class VIEW3D_PT_E102_Engineering(bpy.types.Panel):

    bl_label = PANEL_LABEL
    bl_idname = PANEL_ID

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    bl_category = PANEL_CATEGORY
    bl_context = "objectmode"

    @classmethod
    def poll(cls, context):

        return (
            context.scene is not None
            and context.area is not None
        )

    def draw(self, context):

        layout = self.layout

        props = get_design_properties(context)

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = layout.box()

        header.label(
            text="E-102 HEAT EXCHANGER",
            icon="INFO"
        )

        header.label(
            text="Chemical Engineering Design Tool"
        )

        if props is None:

            warning = layout.box()

            warning.label(
                text="E-102 properties not registered.",
                icon="ERROR"
            )

            warning.label(
                text="Check properties.py registration."
            )

            return

        # ----------------------------------------------------
        # INPUT SECTIONS
        # ----------------------------------------------------

        draw_process_design(
            layout,
            props
        )

        draw_fluid_properties(
            layout,
            props
        )

        draw_thermal_design(
            layout,
            props
        )

        draw_equipment_geometry(
            layout,
            props
        )

        # ----------------------------------------------------
        # CALCULATION CONTROLS AND RESULTS
        # ----------------------------------------------------

        draw_calculation_controls(layout)

        draw_calculation_results(
            layout,
            context
        )

        # ----------------------------------------------------
        # MODEL GENERATION
        # ----------------------------------------------------

        draw_equipment_controls(layout)

        # ----------------------------------------------------
        # FLOW
        # ----------------------------------------------------

        draw_flow_controls(
            layout,
            context
        )

        # ----------------------------------------------------
        # ASSEMBLY
        # ----------------------------------------------------

        draw_assembly_controls(layout)

        # ----------------------------------------------------
        # INFORMATION
        # ----------------------------------------------------

        draw_design_information(layout, props)


# ============================================================
# 12. REGISTRATION
# ============================================================

CLASSES = (
    VIEW3D_PT_E102_Engineering,
)


_REGISTERED_CLASSES = []


def register():
    """Register the E-102 engineering panel."""

    global _REGISTERED_CLASSES

    if _REGISTERED_CLASSES:
        return

    try:

        for cls in CLASSES:

            existing = getattr(
                bpy.types,
                cls.__name__,
                None
            )

            if existing is not None:

                try:
                    bpy.utils.unregister_class(existing)
                except RuntimeError:
                    pass

            bpy.utils.register_class(cls)

            _REGISTERED_CLASSES.append(cls)

            print(
                f"E-102: Registered UI panel {cls.__name__}"
            )

    except Exception:

        for cls in reversed(_REGISTERED_CLASSES):

            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                pass

        _REGISTERED_CLASSES.clear()

        raise


def unregister():
    """Unregister the E-102 engineering panel."""

    global _REGISTERED_CLASSES

    for cls in reversed(CLASSES):

        registered = getattr(
            bpy.types,
            cls.__name__,
            None
        )

        if registered is not None:

            try:
                bpy.utils.unregister_class(registered)

            except Exception as error:

                print(
                    f"E-102 UI unregister warning: {error}"
                )

    _REGISTERED_CLASSES.clear()
