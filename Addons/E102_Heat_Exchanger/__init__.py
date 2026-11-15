
"""
============================================================
E-102 HEAT EXCHANGER DESIGNER
Shell-and-Tube Heat Exchanger Design and Visualization
Blender Add-on
============================================================

Author: Engr Peter Ebogha
Version: 1.1.2
Target: Blender 5.2+

Features:
    - Selectable cold/process-side fluid presets
    - Seven selectable heating media
    - Preliminary thermal calculations and tube-count screening
    - Equipment geometry generation
    - Fluid-specific animated flow schematics (not CFD)
    - Equipment inspection
    - Equipment assembly and explosion
    - Interactive engineering interface
"""

bl_info = {
    "name": "E-102 Heat Exchanger Designer",
    "author": "Engr Peter Ebogha",
    "version": (1, 1, 2),
    "blender": (5, 2, 0),
    "location": "3D Viewport > Sidebar > E-102",
    "description": (
        "Interactive shell-and-tube heat exchanger "
        "design, engineering calculations and visualization."
    ),
    "category": "3D View",
}


# ============================================================
# MODULE IMPORTS
# ============================================================

# Assembly is intentionally excluded here.
# It is imported only when an assembly operation is requested.
#
# This prevents a missing assembly.py file from stopping
# the entire add-on from loading.

from . import (
    properties,
    operators,
    ui,
)


# ============================================================
# REGISTRATION STATE
# ============================================================

_REGISTERED_MODULES = []


# ============================================================
# ADD-ON REGISTRATION
# ============================================================

def register():

    global _REGISTERED_MODULES

    if _REGISTERED_MODULES:
        print("E-102 is already registered.")
        return

    modules = (
        properties,
        operators,
        ui,
    )

    try:

        print("\n========================================")
        print("E-102 HEAT EXCHANGER DESIGNER")
        print("Starting add-on registration...")
        print("========================================")

        for module in modules:

            print(f"Registering: {module.__name__}")

            module.register()

            _REGISTERED_MODULES.append(module)

            print(
                f"Successfully registered: {module.__name__}"
            )

        print("----------------------------------------")
        print("E-102 ADD-ON SUCCESSFULLY REGISTERED")
        print("Open: 3D Viewport > Sidebar > E-102")
        print("========================================\n")

    except Exception as exc:

        print("\n========================================")
        print("E-102 REGISTRATION FAILED")
        print("Error:", exc)
        print("Rolling back registered modules...")
        print("========================================")

        for module in reversed(_REGISTERED_MODULES):

            try:
                module.unregister()

            except Exception as cleanup_error:

                print(
                    "Registration cleanup error:",
                    cleanup_error
                )

        _REGISTERED_MODULES.clear()

        raise


# ============================================================
# ADD-ON UNREGISTRATION
# ============================================================

def unregister():

    global _REGISTERED_MODULES

    print("\n========================================")
    print("UNREGISTERING E-102 HEAT EXCHANGER")
    print("========================================")

    for module in reversed(_REGISTERED_MODULES):

        try:

            module.unregister()

            print(f"Unregistered: {module.__name__}")

        except Exception as exc:

            print(
                f"Error unregistering "
                f"{module.__name__}: {exc}"
            )

    _REGISTERED_MODULES.clear()

    print("----------------------------------------")
    print("E-102 ADD-ON UNREGISTERED")
    print("========================================\n")


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":
    register()
