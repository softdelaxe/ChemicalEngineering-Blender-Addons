
"""
============================================================
E-102 SHELL-AND-TUBE HEAT EXCHANGER
properties.py

Blender 5.x compatible property definitions.

Includes:
    - Process fluid property database
    - Fluid reference temperatures
    - Fluid composition and grade information
    - Property source information
    - Property verification status
    - Heating medium selection
    - Thermal design inputs
    - Equipment geometry inputs
    - Mechanical screening inputs

TEMPERATURE CONVENTION:
    All temperature inputs and stored values are in degrees
    Celsius (°C).

    Blender temperature unit display is deliberately disabled
    for these properties to prevent automatic Kelvin display.

IMPORTANT:
    The fluid presets are preliminary screening data.
    They are not substitutes for supplier certificates,
    laboratory measurements or validated thermophysical data.
============================================================
"""

import bpy

from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)


# ============================================================
# 1. HEATING MEDIUM OPTIONS
# ============================================================

HEATING_MEDIUM_ITEMS = [
    ('hot_water', 'Hot water', 'Liquid hot-water heating'),
    ('steam', 'Saturated steam', 'Condensing saturated steam'),
    ('thermal_oil', 'Thermal oil', 'Thermal-oil heating'),
    ('glycol_water', 'Glycol-water', 'Glycol-water mixture'),
    ('hot_air', 'Hot air', 'Hot-air heating'),
    ('flue_gas', 'Flue gas', 'Flue-gas heating'),
    ('molten_salt', 'Molten salt', 'Molten-salt heating'),
]


# ============================================================
# 2. PROCESS FLUID PROPERTY DATABASE
# ============================================================

"""
Units:

Specific heat capacity:
    kJ/(kg.K)

Density:
    kg/m3

Dynamic viscosity:
    Pa.s

Reference temperature:
    degrees Celsius (°C)

Status definitions:

reference_backed:
    Values have a stated reference source and condition.
    Check individual property data before final design.

estimated:
    Preliminary engineering estimate.
    Replace with validated data.

user_defined:
    User supplies the property values.
"""


PROCESS_FLUID_PRESETS = {

    "wco": {
        "name": "Waste cooking oil",
        "cp": 3.40,
        "density": 900.0,
        "viscosity": 0.030,

        "reference_temp_c": 25.0,
        "composition": "Variable used cooking oil",

        "status": "estimated",

        "source": "Existing E-102 preliminary design assumption",

        "source_url": "",

        "note": (
            "Properties depend on feedstock, degradation, "
            "water content and food residues. "
            "Laboratory characterization is recommended."
        ),
    },

    "vegetable_oil": {
        "name": "Vegetable oil",
        "cp": 2.00,
        "density": 910.0,
        "viscosity": 0.050,

        "reference_temp_c": 25.0,
        "composition": "Generic edible vegetable oil",

        "status": "estimated",

        "source": "Preliminary vegetable-oil screening estimate",

        "source_url": "",

        "note": (
            "Specify the oil type, such as soybean, "
            "sunflower or canola. Properties vary by oil "
            "type and temperature."
        ),
    },

    "palm_oil": {
        "name": "Palm oil",
        "cp": 2.10,
        "density": 893.0,
        "viscosity": 0.0287,

        "reference_temp_c": 45.0,
        "composition": "Crude palm oil",

        "status": "estimated",

        "source": (
            "Malaysian Palm Oil Board, "
            "crude palm oil property information"
        ),

        "source_url": (
            "https://palmoilis.mpob.gov.my/"
            "publications/POEB/poeb106-data.pdf"
        ),

        "note": (
            "Screening values. Confirm each property against "
            "the original data and actual palm oil grade. "
            "Palm oil may be partly solid at lower temperatures."
        ),
    },

    "water": {
        "name": "Water",
        "cp": 4.18,
        "density": 997.0,
        "viscosity": 0.000890,

        "reference_temp_c": 25.0,
        "composition": "Pure liquid water",

        "status": "reference_backed",

        "source": "NIST Chemistry WebBook, SRD 69",

        "source_url": (
            "https://webbook.nist.gov/chemistry/fluid/"
        ),

        "note": (
            "Approximate liquid-water properties near 25 °C "
            "and atmospheric pressure. Use temperature- and "
            "pressure-specific values for final design."
        ),
    },

    "biodiesel": {
        "name": "Biodiesel",
        "cp": 2.00,
        "density": 880.0,
        "viscosity": 0.0045,

        "reference_temp_c": 25.0,
        "composition": "Generic fatty acid methyl ester",

        "status": "estimated",

        "source": "Preliminary biodiesel screening estimate",

        "source_url": "",

        "note": (
            "Specify feedstock and biodiesel grade. "
            "Properties depend on fatty acid composition "
            "and operating temperature."
        ),
    },

    "diesel": {
        "name": "Diesel",
        "cp": 2.10,
        "density": 840.0,
        "viscosity": 0.0030,

        "reference_temp_c": 25.0,
        "composition": "Generic petroleum diesel",

        "status": "estimated",

        "source": "Preliminary petroleum-fuel screening estimate",

        "source_url": "",

        "note": (
            "Specify diesel grade. Use supplier density "
            "and viscosity data at stated reference temperatures."
        ),
    },

    "crude_oil": {
        "name": "Crude oil",
        "cp": 2.00,
        "density": 900.0,
        "viscosity": 0.020,

        "reference_temp_c": 25.0,
        "composition": "Unspecified crude petroleum",

        "status": "estimated",

        "source": "Existing E-102 preliminary design assumption",

        "source_url": "",

        "note": (
            "Require crude assay, API gravity and "
            "viscosity-temperature information. "
            "Do not treat this as a universal crude-oil property set."
        ),
    },

    "glycerol": {
        "name": "Crude glycerol",
        "cp": 2.40,
        "density": 1200.0,
        "viscosity": 0.600,

        "reference_temp_c": 25.0,
        "composition": "Unspecified crude biodiesel glycerol",

        "status": "estimated",

        "source": "Crude glycerol characterization literature",

        "source_url": (
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC9978273/"
        ),

        "note": (
            "Highly composition-dependent. Determine glycerol, "
            "water, methanol, soap and ash content. "
            "The numerical preset is not a universal measured value."
        ),
    },

    "ethanol": {
        "name": "Ethanol",
        "cp": 2.44,
        "density": 789.2,
        "viscosity": 0.001074,

        "reference_temp_c": 25.0,
        "composition": "Near-pure liquid ethanol",

        "status": "reference_backed",

        "source": "NIST Chemistry WebBook, SRD 69",

        "source_url": (
            "https://webbook.nist.gov/cgi/cbook.cgi?ID=C64175"
        ),

        "note": (
            "Specific heat is based on liquid ethanol data "
            "near 298.15 K. Density and viscosity are approximate "
            "reference values near 25 °C. Verify all properties "
            "at the actual operating conditions."
        ),
    },

    "methanol": {
        "name": "Methanol",
        "cp": 2.53,
        "density": 792.0,
        "viscosity": 0.000600,

        "reference_temp_c": 25.0,
        "composition": "Near-pure liquid methanol",

        "status": "estimated",

        "source": "NIST Chemistry WebBook, SRD 69",

        "source_url": (
            "https://webbook.nist.gov/chemistry/fluid/"
        ),

        "note": (
            "Preliminary values. Retrieve and verify "
            "temperature-specific liquid properties before design."
        ),
    },

    "ethylene_glycol": {
        "name": "Ethylene glycol",
        "cp": 2.40,
        "density": 1110.0,
        "viscosity": 0.0161,

        "reference_temp_c": 25.0,
        "composition": "Near-pure ethylene glycol",

        "status": "estimated",

        "source": "NIST Chemistry WebBook and published property data",

        "source_url": (
            "https://webbook.nist.gov/chemistry/fluid/"
        ),

        "note": (
            "These values are for preliminary screening. "
            "Do not use them for aqueous glycol mixtures."
        ),
    },

    "propylene_glycol": {
        "name": "Propylene glycol",
        "cp": 2.50,
        "density": 1035.0,
        "viscosity": 0.0420,

        "reference_temp_c": 25.0,
        "composition": "Near-pure propylene glycol",

        "status": "estimated",

        "source": "NIST Chemistry WebBook and published property data",

        "source_url": (
            "https://webbook.nist.gov/chemistry/fluid/"
        ),

        "note": (
            "These values are for preliminary screening. "
            "Do not use them for aqueous glycol mixtures."
        ),
    },

    "brine": {
        "name": "Brine",
        "cp": 3.80,
        "density": 1030.0,
        "viscosity": 0.0015,

        "reference_temp_c": 20.0,
        "composition": "Unspecified aqueous sodium chloride solution",

        "status": "estimated",

        "source": "ASHRAE Handbook, Physical Properties of Secondary Coolants",

        "source_url": (
            "https://handbook.ashrae.org/"
        ),

        "note": (
            "These are illustrative values only. "
            "Specify sodium chloride concentration by mass "
            "and operating temperature."
        ),
    },

    "sugar_syrup": {
        "name": "Sugar syrup",
        "cp": 2.80,
        "density": 1300.0,
        "viscosity": 0.100,

        "reference_temp_c": 25.0,
        "composition": "Unspecified sucrose-water solution",

        "status": "estimated",

        "source": "Preliminary sucrose-solution screening estimate",

        "source_url": "",

        "note": (
            "Specify sugar concentration in degrees Brix. "
            "Density, heat capacity and viscosity depend "
            "strongly on concentration and temperature."
        ),
    },

    "milk": {
        "name": "Milk",
        "cp": 3.90,
        "density": 1030.0,
        "viscosity": 0.0020,

        "reference_temp_c": 25.0,
        "composition": "Generic whole milk",

        "status": "estimated",

        "source": "Preliminary food-fluid screening estimate",

        "source_url": "",

        "note": (
            "Specify whole, skimmed or other milk type, "
            "fat content and solids concentration."
        ),
    },
}


# ============================================================
# 3. PROCESS FLUID ENUMERATION
# ============================================================

PROCESS_FLUID_ITEMS = [

    (
        key,
        data["name"],
        "{} | {} | Reference temperature: {} °C".format(
            data["status"],
            data["composition"],
            data["reference_temp_c"],
        ),
    )

    for key, data in PROCESS_FLUID_PRESETS.items()

] + [

    (
        "custom",
        "Custom / user-defined",
        "Enter process-fluid properties manually",
    )

]


# ============================================================
# 4. PROCESS FLUID PRESET CALLBACK
# ============================================================

def _apply_process_fluid_preset(self, context):
    """
    Apply selected process-fluid properties.

    Legacy wco_* property names are retained to preserve
    compatibility with calculations.py.
    """

    selected = self.process_fluid_type

    preset = PROCESS_FLUID_PRESETS.get(selected)

    if preset is None:

        self.process_fluid_status = "user_defined"

        self.process_fluid_reference_temp_c = 0.0

        self.process_fluid_composition = (
            "User-defined composition"
        )

        self.process_fluid_source = (
            "User-supplied property data"
        )

        self.process_fluid_source_url = ""

        self.process_fluid_note = (
            "Enter validated properties for the actual fluid."
        )

        return

    # --------------------------------------------------------
    # APPLY NUMERICAL PROPERTIES
    # --------------------------------------------------------

    self.wco_cp_kj_kg_k = preset["cp"]

    self.wco_density_kg_m3 = preset["density"]

    self.wco_viscosity_pa_s = preset["viscosity"]

    # --------------------------------------------------------
    # APPLY PROPERTY METADATA
    # --------------------------------------------------------

    self.process_fluid_reference_temp_c = (
        preset["reference_temp_c"]
    )

    self.process_fluid_status = (
        preset["status"]
    )

    self.process_fluid_composition = (
        preset["composition"]
    )

    self.process_fluid_source = (
        preset["source"]
    )

    self.process_fluid_source_url = (
        preset["source_url"]
    )

    self.process_fluid_note = (
        preset["note"]
    )


# ============================================================
# 5. FLOW ARRANGEMENT
# ============================================================

FLOW_ARRANGEMENT_ITEMS = [

    (
        'counter_current',
        'Counter-current',
        'Counter-current flow',
    ),

]


# ============================================================
# 6. TUBE LAYOUT
# ============================================================

TUBE_LAYOUT_ITEMS = [

    (
        'triangular',
        'Triangular',
        'Triangular tube layout',
    ),

    (
        'square',
        'Square',
        'Square tube layout',
    ),

]


# ============================================================
# 7. E-102 PROPERTY GROUP
# ============================================================

class E102Properties(bpy.types.PropertyGroup):
    """
    User-editable preliminary process, thermal,
    geometry and mechanical inputs.

    All temperature values are stored in Celsius.
    """

    # --------------------------------------------------------
    # PROCESS FLUID SELECTION
    # --------------------------------------------------------

    process_fluid_type: EnumProperty(

        name='Cold / Process Fluid',

        items=PROCESS_FLUID_ITEMS,

        default='wco',

        update=_apply_process_fluid_preset,

    )

    custom_process_fluid_name: StringProperty(

        name='Custom Fluid Name',

        default='Custom process fluid',

    )

    # --------------------------------------------------------
    # PROCESS FLUID PROPERTY METADATA
    # --------------------------------------------------------

    process_fluid_reference_temp_c: FloatProperty(

        name='Preset Reference Temperature (°C)',

        default=25.0,

        precision=2,

        description='Reference temperature for the preset fluid properties, in Celsius',

    )

    process_fluid_status: StringProperty(

        name='Property Data Status',

        default='estimated',

    )

    process_fluid_composition: StringProperty(

        name='Preset Composition',

        default='Variable used cooking oil',

    )

    process_fluid_source: StringProperty(

        name='Property Data Source',

        default='Existing E-102 preliminary design assumption',

    )

    process_fluid_source_url: StringProperty(

        name='Property Source URL',

        default='',

    )

    process_fluid_note: StringProperty(

        name='Property Notes',

        default='Validate properties for actual fluid and conditions.',

    )

    # --------------------------------------------------------
    # PROCESS FLUID OPERATING CONDITIONS
    # --------------------------------------------------------

    # Legacy names retained for calculation compatibility.

    wco_mass_flow_kg_h: FloatProperty(

        name='Process Fluid Mass Flow (kg/h)',

        default=100.0,

        min=0.001,

        precision=2,

    )

    wco_inlet_temp_c: FloatProperty(

        name='Process Fluid Inlet Temperature (°C)',

        default=25.0,

        precision=2,

        description='Process fluid inlet temperature in degrees Celsius',

    )

    wco_outlet_temp_c: FloatProperty(

        name='Process Fluid Outlet Temperature (°C)',

        default=60.0,

        precision=2,

        description='Process fluid outlet temperature in degrees Celsius',

    )

    wco_cp_kj_kg_k: FloatProperty(

        name='Specific Heat (kJ/kg·K)',

        default=3.4,

        min=0.001,

        precision=4,

    )

    wco_density_kg_m3: FloatProperty(

        name='Density (kg/m³)',

        default=900.0,

        min=0.001,

        precision=2,

    )

    wco_viscosity_pa_s: FloatProperty(

        name='Dynamic Viscosity (Pa·s)',

        default=0.030,

        min=0.0000001,

        precision=6,

    )

    # --------------------------------------------------------
    # HEATING MEDIUM
    # --------------------------------------------------------

    heating_medium_type: EnumProperty(

        name='Heating Medium',

        items=HEATING_MEDIUM_ITEMS,

        default='hot_water',

    )

    heating_medium_inlet_temp_c: FloatProperty(

        name='Inlet Temperature (°C)',

        default=0.0,

        precision=2,

        description='Heating medium inlet temperature in Celsius. 0 uses the selected medium database default',

    )

    heating_medium_outlet_temp_c: FloatProperty(

        name='Outlet Temperature (°C)',

        default=0.0,

        precision=2,

        description='Heating medium outlet temperature in Celsius. 0 uses the selected medium database default',

    )

    heating_medium_cp_kj_kg_k: FloatProperty(

        name='Specific Heat (kJ/kg·K)',

        default=0.0,

        min=0.0,

        precision=4,

        description='0 uses the selected medium database default',

    )

    heating_medium_density_kg_m3: FloatProperty(

        name='Density (kg/m³)',

        default=0.0,

        min=0.0,

        precision=2,

        description='0 uses the selected medium database default',

    )

    heating_medium_viscosity_pa_s: FloatProperty(

        name='Dynamic Viscosity (Pa·s)',

        default=0.0,

        min=0.0,

        precision=6,

        description='0 uses the selected medium database default',

    )

    heating_medium_latent_heat_kj_kg: FloatProperty(

        name='Latent Heat (kJ/kg)',

        default=0.0,

        min=0.0,

        precision=2,

        description='Required for steam if overriding database value',

    )

    heating_medium_pressure_bar: FloatProperty(

        name='Operating Pressure (bar)',

        default=0.0,

        min=0.0,

        precision=3,

        description='0 uses the selected medium database default',

    )

    # --------------------------------------------------------
    # THERMAL DESIGN
    # --------------------------------------------------------

    design_factor: FloatProperty(

        name='Design Factor',

        default=1.20,

        min=1.0,

        max=3.0,

        precision=3,

    )

    overall_heat_transfer_coefficient_w_m2_k: FloatProperty(

        name='Overall U (W/m²·K)',

        default=150.0,

        min=1.0,

        max=5000.0,

        precision=2,

    )

    tube_fouling_resistance_m2_k_w: FloatProperty(

        name='Tube Fouling Resistance (m²·K/W)',

        default=0.0002,

        min=0.0,

        precision=6,

    )

    shell_fouling_resistance_m2_k_w: FloatProperty(

        name='Shell Fouling Resistance (m²·K/W)',

        default=0.0002,

        min=0.0,

        precision=6,

    )

    flow_arrangement: EnumProperty(

        name='Flow Arrangement',

        items=FLOW_ARRANGEMENT_ITEMS,

        default='counter_current',

    )

    # --------------------------------------------------------
    # TUBE GEOMETRY
    # --------------------------------------------------------

    tube_outside_diameter_m: FloatProperty(

        name='Tube Outside Diameter (m)',

        default=0.0127,

        min=0.003,

        precision=4,

    )

    tube_wall_thickness_m: FloatProperty(

        name='Tube Wall Thickness (m)',

        default=0.0009,

        min=0.0001,

        precision=4,

    )

    tube_length_m: FloatProperty(

        name='Tube Length (m)',

        default=1.5,

        min=0.1,

        precision=3,

    )

    number_of_tubes: IntProperty(

        name='Number of Tubes',

        default=16,

        min=1,

        max=10000,

    )

    auto_size_tubes: BoolProperty(

        name='Automatically Size Tube Count',

        default=True,

    )

    tube_passes: IntProperty(

        name='Tube Passes',

        default=4,

        min=1,

        max=100,

    )

    shell_passes: IntProperty(

        name='Shell Passes',

        default=1,

        min=1,

        max=1,

        description='Current geometry supports one shell pass',

    )

    tube_pitch_m: FloatProperty(

        name='Tube Pitch (m)',

        default=0.019,

        min=0.004,

        precision=4,

    )

    tube_layout: EnumProperty(

        name='Tube Layout',

        items=TUBE_LAYOUT_ITEMS,

        default='triangular',

    )

    # --------------------------------------------------------
    # SHELL GEOMETRY
    # --------------------------------------------------------

    shell_internal_diameter_m: FloatProperty(

        name='Shell Internal Diameter (m)',

        default=0.200,

        min=0.05,

        precision=4,

    )

    shell_wall_thickness_m: FloatProperty(

        name='Shell Wall Thickness (m)',

        default=0.004,

        min=0.001,

        precision=4,

    )

    channel_head_length_m: FloatProperty(

        name='Channel Head Length (m)',

        default=0.180,

        min=0.05,

        precision=3,

    )

    tubesheet_thickness_m: FloatProperty(

        name='Tubesheet Thickness (m)',

        default=0.025,

        min=0.003,

        precision=3,

    )

    baffle_count: IntProperty(

        name='Number of Baffles',

        default=4,

        min=0,

        max=100,

    )

    baffle_cut_fraction: FloatProperty(

        name='Baffle Cut Fraction',

        default=0.25,

        min=0.05,

        max=0.45,

        precision=3,

    )

    # --------------------------------------------------------
    # SCREENING AND MECHANICAL INPUTS
    # --------------------------------------------------------

    minimum_tube_velocity_m_s: FloatProperty(

        name='Minimum Tube Velocity (m/s)',

        default=0.30,

        min=0.001,

        precision=3,

    )

    maximum_tube_velocity_m_s: FloatProperty(

        name='Maximum Tube Velocity (m/s)',

        default=2.00,

        min=0.001,

        precision=3,

    )

    design_pressure_bar: FloatProperty(

        name='Design Pressure (bar)',

        default=5.0,

        min=0.001,

        precision=2,

    )

    design_temperature_c: FloatProperty(

        name='Design Temperature (°C)',

        default=120.0,

        precision=2,

        description='Mechanical design temperature in degrees Celsius',

    )

    corrosion_allowance_m: FloatProperty(

        name='Corrosion Allowance (m)',

        default=0.0015,

        min=0.0,

        precision=4,

    )


# ============================================================
# 8. PROPERTY ACCESS
# ============================================================

def get_e102_properties(scene=None):
    """Return the E-102 property group."""

    scene = scene or bpy.context.scene

    if scene is None or not hasattr(scene, 'e102_design'):

        raise RuntimeError(
            'E-102 properties are not registered. '
            'Check add-on registration.'
        )

    return scene.e102_design


# ============================================================
# 9. CALCULATION INPUT COLLECTION
# ============================================================

def get_calculation_inputs(scene=None):
    """
    Collect all E-102 inputs for calculations.py.

    Temperature values are passed in degrees Celsius.
    """

    p = get_e102_properties(scene)

    if p.process_fluid_type == 'custom':

        process_fluid_name = (
            p.custom_process_fluid_name.strip()
            or 'Custom process fluid'
        )

    else:

        process_fluid_name = (
            PROCESS_FLUID_PRESETS[p.process_fluid_type]["name"]
        )

    inputs = {

        # ----------------------------------------------------
        # PROCESS FLUID
        # ----------------------------------------------------

        'process_fluid_name': process_fluid_name,

        'wco_mass_flow_kg_h': p.wco_mass_flow_kg_h,

        'wco_inlet_temp_c': p.wco_inlet_temp_c,

        'wco_outlet_temp_c': p.wco_outlet_temp_c,

        'wco_cp_kj_kg_k': p.wco_cp_kj_kg_k,

        'wco_density_kg_m3': p.wco_density_kg_m3,

        'wco_viscosity_pa_s': p.wco_viscosity_pa_s,

        # ----------------------------------------------------
        # PROCESS FLUID METADATA
        # ----------------------------------------------------

        'process_fluid_type': p.process_fluid_type,

        'process_fluid_reference_temp_c':
            p.process_fluid_reference_temp_c,

        'process_fluid_status':
            p.process_fluid_status,

        'process_fluid_composition':
            p.process_fluid_composition,

        'process_fluid_source':
            p.process_fluid_source,

        'process_fluid_source_url':
            p.process_fluid_source_url,

        'process_fluid_note':
            p.process_fluid_note,

        # ----------------------------------------------------
        # HEATING MEDIUM
        # ----------------------------------------------------

        'heating_medium_type': p.heating_medium_type,

        # ----------------------------------------------------
        # THERMAL DESIGN
        # ----------------------------------------------------

        'design_factor': p.design_factor,

        'overall_heat_transfer_coefficient_w_m2_k':
            p.overall_heat_transfer_coefficient_w_m2_k,

        'tube_fouling_resistance_m2_k_w':
            p.tube_fouling_resistance_m2_k_w,

        'shell_fouling_resistance_m2_k_w':
            p.shell_fouling_resistance_m2_k_w,

        'flow_arrangement': p.flow_arrangement,

        # ----------------------------------------------------
        # TUBE GEOMETRY
        # ----------------------------------------------------

        'tube_outside_diameter_m':
            p.tube_outside_diameter_m,

        'tube_wall_thickness_m':
            p.tube_wall_thickness_m,

        'tube_length_m':
            p.tube_length_m,

        'tube_count':
            p.number_of_tubes,

        'auto_size_tubes':
            p.auto_size_tubes,

        'tube_passes':
            p.tube_passes,

        'shell_passes':
            p.shell_passes,

        'tube_pitch_m':
            p.tube_pitch_m,

        'tube_layout':
            p.tube_layout,

        # ----------------------------------------------------
        # SHELL GEOMETRY
        # ----------------------------------------------------

        'shell_internal_diameter_m':
            p.shell_internal_diameter_m,

        'shell_wall_thickness_m':
            p.shell_wall_thickness_m,

        'channel_head_length_m':
            p.channel_head_length_m,

        'tubesheet_thickness_m':
            p.tubesheet_thickness_m,

        'baffle_count':
            p.baffle_count,

        'baffle_cut_fraction':
            p.baffle_cut_fraction,

        # ----------------------------------------------------
        # SCREENING INPUTS
        # ----------------------------------------------------

        'minimum_tube_velocity_m_s':
            p.minimum_tube_velocity_m_s,

        'maximum_tube_velocity_m_s':
            p.maximum_tube_velocity_m_s,

        # ----------------------------------------------------
        # MECHANICAL INPUTS
        # ----------------------------------------------------

        'design_pressure_bar':
            p.design_pressure_bar,

        'design_temperature_c':
            p.design_temperature_c,

        'corrosion_allowance_m':
            p.corrosion_allowance_m,

        'construction_material':
            'Carbon steel (unverified)',

    }

    # --------------------------------------------------------
    # OPTIONAL HEATING-MEDIUM OVERRIDES
    # --------------------------------------------------------

    # Zero means use the heating-medium database default.

    optional = {

        'heating_medium_inlet_temp_c':
            p.heating_medium_inlet_temp_c,

        'heating_medium_outlet_temp_c':
            p.heating_medium_outlet_temp_c,

        'heating_medium_cp_kj_kg_k':
            p.heating_medium_cp_kj_kg_k,

        'heating_medium_density_kg_m3':
            p.heating_medium_density_kg_m3,

        'heating_medium_viscosity_pa_s':
            p.heating_medium_viscosity_pa_s,

        'heating_medium_latent_heat_kj_kg':
            p.heating_medium_latent_heat_kj_kg,

        'heating_medium_pressure_bar':
            p.heating_medium_pressure_bar,

    }

    for key, value in optional.items():

        inputs[key] = value if value > 0 else None

    return inputs


# ============================================================
# 10. CALCULATION INPUT VALIDATION
# ============================================================

def validate_calculation_inputs(scene=None):
    """Validate inputs using the engineering calculation module."""

    from . import calculations

    try:

        calculations.calculate_design(
            get_calculation_inputs(scene)
        )

        return True, ''

    except Exception as exc:

        return False, str(exc)


# ============================================================
# 11. BLENDER REGISTRATION
# ============================================================

CLASSES = (
    E102Properties,
)

_REGISTERED = []


def register():
    """Register E-102 properties."""

    global _REGISTERED

    if hasattr(bpy.types.Scene, 'e102_design'):

        try:
            del bpy.types.Scene.e102_design

        except Exception:
            pass

    for cls in CLASSES:

        try:
            bpy.utils.unregister_class(cls)

        except Exception:
            pass

        bpy.utils.register_class(cls)

        if cls not in _REGISTERED:
            _REGISTERED.append(cls)

    bpy.types.Scene.e102_design = PointerProperty(
        type=E102Properties
    )


def unregister():
    """Unregister E-102 properties."""

    global _REGISTERED

    if hasattr(bpy.types.Scene, 'e102_design'):

        del bpy.types.Scene.e102_design

    for cls in reversed(CLASSES):

        try:
            bpy.utils.unregister_class(cls)

        except Exception:
            pass

    _REGISTERED.clear()
