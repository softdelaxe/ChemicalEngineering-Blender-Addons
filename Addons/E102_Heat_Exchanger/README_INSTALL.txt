E-102 HEAT EXCHANGER DESIGNER - VERSION 1.1.1
Blender target: 5.2+

INSTALLATION
1. In Blender, open Edit > Preferences > Add-ons.
2. Disable and remove the previous E-102 Heat Exchanger Designer copy.
3. Click Install from Disk and select this ZIP file.
4. Enable E-102 Heat Exchanger Designer.
5. Move the pointer over the 3D Viewport and press N.
6. Open the E-102 tab in the sidebar.

IMPORTANT UPDATE
The panel now exposes the selected heating medium and its operating-condition
fields. The calculation module supports hot water, saturated steam, thermal
oil, glycol-water, hot air, flue gas and molten salt.

WORKFLOW
1. Enter WCO process conditions.
2. Select the shell-side heating medium.
3. Enter optional heating-medium overrides. A value of 0 means use the
   illustrative default stored for that medium.
4. Set thermal and geometry inputs.
5. Click Run Design Calculations.
6. Review the duty, LMTD, required/installed area, estimated tube count,
   hydraulics and screening findings.
7. Click Build E-102 Equipment. The build operation runs the calculation and
   creates the exchanger using the calculated tube count and geometry inputs.
8. The build operation also creates the flat base platform.

FLOW VISUALIZATION UPDATE
The shell-side flow visualization now changes its material colour, particle
scale, line thickness and label according to the selected heating medium:
hot water, steam, thermal oil, glycol-water, hot air, flue gas or molten salt.
The illustrative shell-side path uses the configured baffle count as a visual
guide. Object metadata records the selected service and explicitly marks the
objects as non-CFD schematic results.

This remains an engineering schematic, not CFD. It does not calculate local
velocity fields, temperature fields, turbulence, phase change distribution,
baffle leakage, bypass streams or pressure drop. The WCO path is still a
simplified pass-through because physical tube-pass partitions and return
bends are not yet part of the exchanger geometry.

ENGINEERING LIMITATIONS
This is a preliminary educational/design-screening tool, not a TEMA rating
program, ASME pressure-vessel design, or fabrication package. Heating-medium
properties are illustrative starting values and must be replaced with
validated data for actual operating temperature, pressure and composition.
The module does not calculate shell-side heat-transfer coefficients,
pressure drops, vibration, nozzle losses or mechanical integrity. The
simplified bundle estimate is not a detailed TEMA bundle design. A
CONDITIONAL or FEASIBLE_SCREENING result is not code approval.

GEOMETRY NOTES
The uploaded geometry.py already contains the saddle orientation correction:
the saddle cylinder axis is parallel to the shell axis (X), forming a lower
cradle under the shell. The integration module adds the flat rectangular
platform beneath the saddle base plates.

TEST STATUS
Python syntax checks and standalone calculation checks were performed for
all seven heating-medium selections. Blender 5.3 registration, UI rendering
and 3D generation have not been executed in this environment; please test
inside Blender and share any traceback if a runtime issue appears.


VERSION 1.1.2 UPDATE
- Adds selectable cold/process-side fluid presets: waste cooking oil,
  vegetable oil, palm oil, water, biodiesel, diesel, crude oil,
  crude glycerol, ethanol, methanol, ethylene glycol, propylene glycol,
  brine, sugar syrup, milk, and custom/user-defined.
- Selecting a preset fills illustrative Cp, density and viscosity values.
  These must be checked against the actual fluid composition and operating
  temperature before engineering use.
- Build, Explode and Assemble are grouped together in Equipment Controls.
- Corrects the invalid HEAT panel icon that prevented the results panel
  from drawing in Blender.
