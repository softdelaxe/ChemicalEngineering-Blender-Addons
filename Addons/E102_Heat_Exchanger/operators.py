
"""
============================================================
E-102 HEAT EXCHANGER DESIGNER
operators.py

Blender operators for:
    - Equipment generation and removal
    - Engineering calculations
    - Flow visualization and animation
    - Exploded and assembled equipment views

Compatible with Blender 5.2+

Engineering calculations:
    calculations.py

Blender input properties:
    properties.py
============================================================
"""

import bpy
import traceback


# ============================================================
# LAZY MODULE IMPORTS
# ============================================================

def _properties():
    from . import properties
    return properties


def _calculations():
    from . import calculations
    return calculations


def _equipment():
    from . import equipment
    return equipment


def _utilities():
    from . import utilities
    return utilities


def _flow():
    from . import flow
    return flow


def _assembly():
    from . import assembly
    return assembly


# ============================================================
# GENERAL HELPERS
# ============================================================

def _report_exception(operator, message, error):
    """Print the full traceback and report a concise Blender error."""

    traceback.print_exc()

    operator.report(
        {"ERROR"},
        f"{message}: {error}"
    )


def _store_scene_value(scene, key, value):
    """Safely store a scalar value as a Blender scene custom property."""

    try:
        scene[key] = value
    except (TypeError, ValueError, RuntimeError) as error:
        print(
            f"E-102: Could not store scene property "
            f"'{key}': {error}"
        )


def _get_flow_removal_function(flow_module):
    """
    Support either flow-removal function name.

    The preferred function is clear_flow_visualization().
    Older versions may expose remove_flow_visualization().
    """

    function = getattr(
        flow_module,
        "clear_flow_visualization",
        None
    )

    if callable(function):
        return function

    function = getattr(
        flow_module,
        "remove_flow_visualization",
        None
    )

    if callable(function):
        return function

    raise AttributeError(
        "flow.py must provide clear_flow_visualization() "
        "or remove_flow_visualization()."
    )


# ============================================================
# ENGINEERING CALCULATIONS
# ============================================================

def get_scene_inputs(scene):
    """Get calculation inputs from the active Blender scene."""

    return _properties().get_calculation_inputs(scene)


def run_e102_calculations(scene):
    """Run the current preliminary calculation engine and cache panel results."""
    inputs = get_scene_inputs(scene)
    result = _calculations().calculate_design(inputs)
    process = result["process"]
    design = result["design"]
    area = result["area"]
    sizing = result["tube_sizing"]
    medium = result["heating_medium"]
    hydraulics = result["hydraulics"]
    feasibility = result["feasibility"]

    values = {
        "e102_last_process_duty_kw": process["process_duty_kw"],
        "e102_last_design_duty_kw": design["design_duty_kw"],
        "e102_last_lmtd_k": result["lmtd"]["lmtd_k"],
        "e102_last_correction_factor": result["correction"]["correction_factor"],
        "e102_last_corrected_lmtd_k": area["corrected_lmtd_k"],
        "e102_last_required_area_m2": area["required_area_m2"],
        "e102_last_area_m2": area["required_area_m2"],
        "e102_last_installed_area_m2": sizing["installed_area_m2"],
        "e102_last_water_flow_kg_h": medium["actual_mass_flow_kg_h"],
        "e102_last_design_water_flow_kg_h": medium["design_mass_flow_kg_h"],
        "e102_last_water_volume_flow_m3_h": medium["actual_volume_flow_m3_h"] or 0.0,
        "e102_last_wco_velocity_m_s": hydraulics["wco_tube_velocity_m_s"],
        "e102_last_reynolds_number": hydraulics["wco_reynolds_number"],
        "e102_last_flow_regime": hydraulics["flow_regime"],
        "e102_last_warning_count": feasibility["warnings"] + feasibility["not_assessed"] + feasibility["hard_failures"],
        "e102_last_warnings": "\n".join(
            f"{item['status']}: {item['check']} — {item['finding']}"
            for item in feasibility["checks"]
            if item["status"] != "PASS"
        ),
        "e102_last_heating_medium_name": medium["medium_name"],
        "e102_last_tube_count": sizing["selected_tube_count"],
        "e102_last_feasibility": feasibility["overall_status"],
    }
    for key, value in values.items():
        if value is not None:
            _store_scene_value(scene, key, value)
    _store_scene_value(scene, "e102_calculations_completed", True)
    return result


def format_calculation_summary(result):
    process_duty = result["process"]["process_duty_kw"]
    design_duty = result["design"]["design_duty_kw"]
    required_area = result["area"]["required_area_m2"]
    installed_area = result["tube_sizing"]["installed_area_m2"]
    tube_count = result["tube_sizing"]["selected_tube_count"]
    status = result["feasibility"]["overall_status"]
    return (f"{process_duty:.2f} kW process | {design_duty:.2f} kW design | "
            f"Area {required_area:.3f}/{installed_area:.3f} m² | "
            f"{tube_count} tubes | {status}")


def print_calculation_report(result):
    _calculations().print_design_report(result)


# ============================================================
# OPERATOR 1: BUILD EQUIPMENT
# ============================================================

class E102_OT_BuildEquipment(bpy.types.Operator):

    bl_idname = "e102.build_equipment"
    bl_label = "Build E-102 Equipment"
    bl_description = "Generate the shell-and-tube heat exchanger"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            from . import e102_geometry_integration
            inputs = _properties().get_calculation_inputs(context.scene)
            run_e102_calculations(context.scene)
            result = e102_geometry_integration.build_from_calculation(
                inputs,
                clear_existing=True,
                create_platform=True,
            )
            calc = result["calculation"]
            summary = format_calculation_summary(calc)
            self.report({"INFO"}, f"E-102 generated: {summary}")
            return {"FINISHED"}
        except Exception as error:
            _report_exception(self, "Equipment generation failed", error)
            return {"CANCELLED"}



# ============================================================
# OPERATOR 2: RUN DESIGN CALCULATIONS
# ============================================================

class E102_OT_RunCalculations(bpy.types.Operator):

    bl_idname = "e102.run_calculations"
    bl_label = "Run Design Calculations"
    bl_description = "Calculate the preliminary thermal design of E-102"
    bl_options = {"REGISTER"}

    def execute(self, context):

        try:

            # Validate inputs before running the calculation.
            is_valid, error_message = (
                _properties().validate_calculation_inputs(
                    context.scene
                )
            )

            if not is_valid:
                self.report(
                    {"ERROR"},
                    f"Invalid design inputs: {error_message}"
                )

                return {"CANCELLED"}

            result = run_e102_calculations(
                context.scene
            )

            print_calculation_report(result)

            summary = format_calculation_summary(result)

            warning_count = (result["feasibility"]["warnings"] + result["feasibility"]["not_assessed"] + result["feasibility"]["hard_failures"])

            if warning_count:
                self.report(
                    {"WARNING"},
                    f"{summary} | {warning_count} design warnings"
                )
            else:
                self.report(
                    {"INFO"},
                    f"Calculation complete: {summary}"
                )

            return {"FINISHED"}

        except Exception as error:

            _report_exception(
                self,
                "Calculation failed",
                error
            )

            return {"CANCELLED"}


# ============================================================
# OPERATOR 3: REMOVE EQUIPMENT
# ============================================================

class E102_OT_RemoveEquipment(bpy.types.Operator):

    bl_idname = "e102.remove_equipment"
    bl_label = "Remove E-102 Model"
    bl_description = "Remove generated E-102 equipment and flow"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        try:

            flow_module = _flow()

            remove_flow = _get_flow_removal_function(
                flow_module
            )

            remove_flow()

            _utilities().clear_e102_model()

            self.report(
                {"INFO"},
                "E-102 model and flow visualization removed"
            )

            return {"FINISHED"}

        except AttributeError as error:

            # Flow visualization may not have been generated yet.
            if "flow.py must provide" not in str(error):
                _report_exception(
                    self,
                    "Removal failed",
                    error
                )
                return {"CANCELLED"}

            try:
                _utilities().clear_e102_model()

                self.report(
                    {"INFO"},
                    "E-102 equipment removed"
                )

                return {"FINISHED"}

            except Exception as cleanup_error:

                _report_exception(
                    self,
                    "Removal failed",
                    cleanup_error
                )

                return {"CANCELLED"}

        except Exception as error:

            _report_exception(
                self,
                "Removal failed",
                error
            )

            return {"CANCELLED"}


# ============================================================
# OPERATOR 4: BUILD FLOW VISUALIZATION
# ============================================================

class E102_OT_ShowFlow(bpy.types.Operator):

    bl_idname = "e102.show_flow"
    bl_label = "Build Flow Visualization"
    bl_description = "Generate WCO and selected heating-medium flow paths (schematic)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        try:

            result = _flow().build_flow_visualization(
                scene=context.scene,
                clear_previous=True
            )

            if not result:
                self.report(
                    {"WARNING"},
                    "Flow visualization did not return a result"
                )
                return {"CANCELLED"}

            medium_key = _properties().get_e102_properties(context.scene).heating_medium_type
            medium_labels = {
                "hot_water": "HOT WATER",
                "steam": "SATURATED STEAM",
                "thermal_oil": "THERMAL OIL",
                "glycol_water": "GLYCOL-WATER",
                "hot_air": "HOT AIR",
                "flue_gas": "FLUE GAS",
                "molten_salt": "MOLTEN SALT",
            }
            medium_label = medium_labels.get(medium_key, "HEATING MEDIUM")
            medium_label_obj = result.get("hot_water_label")
            if medium_label_obj is not None and medium_label_obj.type == "FONT":
                medium_label_obj.data.body = f"{medium_label} FLOW"
            for key in ("hot_water_path", "hot_water_particles", "hot_water_label"):
                obj = result.get(key)
                if obj is not None:
                    obj["fluid_service"] = medium_key
                    obj["fluid_service_label"] = medium_label

            self.report(
                {"INFO"},
                "E-102 flow visualization generated"
            )

            return {"FINISHED"}

        except Exception as error:

            _report_exception(
                self,
                "Flow generation failed",
                error
            )

            return {"CANCELLED"}


# ============================================================
# OPERATOR 5: HIDE FLOW
# ============================================================

class E102_OT_HideFlow(bpy.types.Operator):

    bl_idname = "e102.hide_flow"
    bl_label = "Hide Flow Visualization"
    bl_description = "Hide E-102 flow paths and particles"

    def execute(self, context):

        try:

            success = _flow().set_flow_visibility(False)

            if not success:
                self.report(
                    {"WARNING"},
                    "No flow visualization collection was found"
                )

                return {"CANCELLED"}

            self.report(
                {"INFO"},
                "Flow visualization hidden"
            )

            return {"FINISHED"}

        except Exception as error:

            _report_exception(
                self,
                "Could not hide flow",
                error
            )

            return {"CANCELLED"}


# ============================================================
# OPERATOR 6: SHOW EXISTING FLOW
# ============================================================

class E102_OT_ShowFlowVisibility(bpy.types.Operator):

    bl_idname = "e102.show_flow_visibility"
    bl_label = "Show Flow Visualization"
    bl_description = "Make the existing flow visualization visible"

    def execute(self, context):

        try:

            success = _flow().set_flow_visibility(True)

            if not success:
                self.report(
                    {"WARNING"},
                    "Build the flow visualization first"
                )

                return {"CANCELLED"}

            self.report(
                {"INFO"},
                "Flow visualization visible"
            )

            return {"FINISHED"}

        except Exception as error:

            _report_exception(
                self,
                "Could not show flow",
                error
            )

            return {"CANCELLED"}


# ============================================================
# OPERATOR 7: PLAY / PAUSE FLOW ANIMATION
# ============================================================

class E102_OT_ToggleFlowAnimation(bpy.types.Operator):

    bl_idname = "e102.toggle_flow_animation"
    bl_label = "Play / Pause Flow"
    bl_description = "Start or pause the Blender timeline animation"

    def execute(self, context):

        try:

            if context.screen is None:
                self.report(
                    {"ERROR"},
                    "No active Blender screen is available"
                )

                return {"CANCELLED"}

            bpy.ops.screen.animation_play()

            return {"FINISHED"}

        except Exception as error:

            _report_exception(
                self,
                "Animation control failed",
                error
            )

            return {"CANCELLED"}


# ============================================================
# OPERATOR 8: RESET FLOW ANIMATION
# ============================================================

class E102_OT_ResetFlowAnimation(bpy.types.Operator):

    bl_idname = "e102.reset_flow_animation"
    bl_label = "Reset Animation"
    bl_description = "Return the animation to its first frame"

    def execute(self, context):

        try:

            screen = context.screen

            if (
                screen is not None
                and screen.is_animation_playing
            ):
                bpy.ops.screen.animation_play()

            context.scene.frame_set(
                context.scene.frame_start
            )

            self.report(
                {"INFO"},
                "Animation reset to first frame"
            )

            return {"FINISHED"}

        except Exception as error:

            _report_exception(
                self,
                "Animation reset failed",
                error
            )

            return {"CANCELLED"}


# ============================================================
# OPERATOR 9: EXPLODE EQUIPMENT
# ============================================================

class E102_OT_ExplodeEquipment(bpy.types.Operator):

    bl_idname = "e102.explode_equipment"
    bl_label = "Explode E-102"
    bl_description = "Animate the exchanger components into an exploded view"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        try:

            result = _assembly().explode_equipment(
                scene=context.scene
            )

            if result is False:
                self.report(
                    {"WARNING"},
                    "No E-102 equipment objects were found"
                )

                return {"CANCELLED"}

            self.report(
                {"INFO"},
                "Exploded view animation created. Play the timeline."
            )

            return {"FINISHED"}

        except Exception as error:

            _report_exception(
                self,
                "Explode operation failed",
                error
            )

            return {"CANCELLED"}


# ============================================================
# OPERATOR 10: ASSEMBLE EQUIPMENT
# ============================================================

class E102_OT_AssembleEquipment(bpy.types.Operator):

    bl_idname = "e102.assemble_equipment"
    bl_label = "Assemble E-102"
    bl_description = "Animate all exchanger components back to their original positions"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        try:

            result = _assembly().assemble_equipment(
                scene=context.scene
            )

            if result is False:
                self.report(
                    {"WARNING"},
                    "No E-102 equipment objects were found"
                )

                return {"CANCELLED"}

            self.report(
                {"INFO"},
                "Assembly animation created. Play the timeline."
            )

            return {"FINISHED"}

        except Exception as error:

            _report_exception(
                self,
                "Assembly operation failed",
                error
            )

            return {"CANCELLED"}


# ============================================================
# OPERATOR 11: RESTORE EQUIPMENT IMMEDIATELY
# ============================================================

class E102_OT_RestoreEquipment(bpy.types.Operator):

    bl_idname = "e102.restore_equipment"
    bl_label = "Restore Equipment"
    bl_description = "Immediately return equipment to its original assembled position"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        try:

            result = _assembly().restore_equipment_immediately(
                scene=context.scene
            )

            if result is False:
                self.report(
                    {"WARNING"},
                    "No E-102 equipment objects were found"
                )

                return {"CANCELLED"}

            self.report(
                {"INFO"},
                "Equipment restored to assembled position"
            )

            return {"FINISHED"}

        except Exception as error:

            _report_exception(
                self,
                "Equipment restoration failed",
                error
            )

            return {"CANCELLED"}


# ============================================================
# OPERATOR CLASSES
# ============================================================

CLASSES = (
    E102_OT_BuildEquipment,
    E102_OT_RunCalculations,
    E102_OT_RemoveEquipment,

    E102_OT_ShowFlow,
    E102_OT_HideFlow,
    E102_OT_ShowFlowVisibility,
    E102_OT_ToggleFlowAnimation,
    E102_OT_ResetFlowAnimation,

    E102_OT_ExplodeEquipment,
    E102_OT_AssembleEquipment,
    E102_OT_RestoreEquipment,
)


# ============================================================
# REGISTRATION
# ============================================================

_REGISTERED_CLASSES = []


def _get_registered_class(class_name):
    """Find an operator class already registered in Blender."""

    return getattr(
        bpy.types,
        class_name,
        None
    )


def register():
    """Register all E-102 operators."""

    global _REGISTERED_CLASSES

    if _REGISTERED_CLASSES:
        return

    try:

        for cls in CLASSES:

            existing = _get_registered_class(
                cls.__name__
            )

            if existing is not None:
                if existing is cls:
                    _REGISTERED_CLASSES.append(cls)
                    continue

                # Remove an older class left by a script reload.
                try:
                    bpy.utils.unregister_class(existing)
                except RuntimeError:
                    pass

            bpy.utils.register_class(cls)

            _REGISTERED_CLASSES.append(cls)

            print(
                f"E-102: Registered operator {cls.__name__}"
            )

    except Exception:

        traceback.print_exc()

        for cls in reversed(_REGISTERED_CLASSES):

            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                pass

        _REGISTERED_CLASSES.clear()

        raise


def unregister():
    """Unregister all E-102 operators."""

    global _REGISTERED_CLASSES

    for cls in reversed(CLASSES):

        registered = _get_registered_class(
            cls.__name__
        )

        if registered is not None:

            try:
                bpy.utils.unregister_class(registered)

                print(
                    f"E-102: Unregistered operator {cls.__name__}"
                )

            except Exception as error:

                print(
                    f"E-102: Could not unregister "
                    f"{cls.__name__}: {error}"
                )

    _REGISTERED_CLASSES.clear()
