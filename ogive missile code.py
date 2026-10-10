"""
ogive_spiral_array.py
------------------------------------------------------------------
Automated PyAEDT script for constructing an 8-Element Conformal 
Archimedean Spiral Antenna Array within a Ceramic Ogive Radome in HFSS.
------------------------------------------------------------------
"""

import math
from pyaedt import Hfss

def build_array_model():
    # 1. Initialize PyAEDT HFSS Session
    app = Hfss(
        specified_version="2025.2",  # Adjust to your installed version (e.g. "2024.1")
        solution_type="Terminal",
        new_desktop_session=True,
        close_on_exit=False
    )

    # 2. Design Variables
    app["r_inner"] = "1.7mm"       # Inner radius derived for lambda_g @ 18 GHz
    app["b1"] = "1.5mm"            # Growth rate factor (mm/rad)
    app["r_outer"] = "40mm"        # Outer footprint radius
    app["radome_thick"] = "4mm"    # Hollow ceramic ogive wall thickness
    app["cavity_depth"] = "4.5mm"  # Unlined cavity depth for phase matching
    app["sub_length"] = "9.5mm"    # Balun electrical length (y_base)
    app["sub_thick"] = "0.8mm"     # Substrate thickness
    app["num_elements"] = 8        # Total conformal array element count

    # Define Ceramic Material
    if "Ceramic_Ogive" not in app.materials.material_names:
        mat = app.materials.add_material("Ceramic_Ogive")
        mat.permittivity = 9.8     # Alumina dielectric constant

    # 3. Model Equation-Driven Archimedean Spiral Arm
    # Equation: r(t) = r_inner + b1 * t
    x_eq = "(r_inner + b1*_t)*cos(_t*2*pi)"
    y_eq = "(r_inner + b1*_t)*sin(_t*2*pi)"
    z_eq = "0"

    spiral_curve = app.modeler.create_equation_curve(
        x_t=x_eq,
        y_t=y_eq,
        z_t=z_eq,
        t_start=0,
        t_end=3.5,  # 3.5 total turns
        name="Spiral_Arm_1"
    )

    # Thicken curve into a copper trace
    app.modeler.thicken_sheet(spiral_curve.name, "0.4mm")
    app.modeler.assign_material(spiral_curve.name, "copper")

    # 4. Model Substrate and Metal Cavity Base
    substrate = app.modeler.create_box(
        origin=["-40mm", "-40mm", "-sub_thick"],
        sizes=["80mm", "80mm", "sub_thick"],
        name="substarte_1",
        material="Rogers RT/duroid 5880 (tm)"
    )

    cavity = app.modeler.create_box(
        origin=["-40mm", "-40mm", "-sub_thick - cavity_depth"],
        sizes=["80mm", "80mm", "cavity_depth"],
        name="metalcavity_1",
        material="pec"
    )

    # 5. Construct Hollow Ceramic Ogive Radome
    # Outer polyline profile on XZ plane
    poly_outer = app.modeler.create_polyline(
        points=[[0, 0, 0], [42, 0, 0], [0, 0, 120]],
        segment_type=["Line", "Arc"],
        name="Outer_Ogive_Polyline"
    )

    outer_solid = app.modeler.revolve(
        poly_outer.name,
        axis="Z",
        angle="360deg",
        name="outer_solid"
    )
    app.modeler.assign_material(outer_solid.name, "Ceramic_Ogive")

    # Inner polyline profile offset by 4mm wall thickness
    poly_inner = app.modeler.create_polyline(
        points=[[0, 0, 0], [38, 0, 0], [0, 0, 116]],
        segment_type=["Line", "Arc"],
        name="Inner_Ogive_Polyline"
    )

    inner_solid = app.modeler.revolve(
        poly_inner.name,
        axis="Z",
        angle="360deg",
        name="inner_solid"
    )

    # Single Boolean Subtraction to hollow out the radome base
    app.modeler.subtract(blank_list="outer_solid", tool_list="inner_solid", keep_originals=False)

    # 6. Create 8-Element Circular Array (45-degree increments)
    single_element_objects = ["Spiral_Arm_1", "substarte_1", "metalcavity_1"]
    app.modeler.duplicate_around_axis(
        assignment=single_element_objects,
        axis="Z",
        angle="45deg",
        clones=8,
        create_new_objects=True
    )

    # 7. Create Air Region and Apply Radiation Boundary
    app.modeler.create_air_region(
        x_pos=15, y_pos=15, z_pos=15,
        x_neg=15, y_neg=15, z_neg=15,
        is_percentage=True
    )
    app.assign_radiation_boundary_to_faces(app.modeler.get_outer_faces())

    # 8. Solution Setup (Optimized for Student Version Mesh Limits)
    setup = app.create_setup(name="Setup1", setup_type="HFSSDriven")
    setup.props["Frequency"] = "18GHz"
    setup.props["MaxDeltaS"] = 0.02
    setup.props["MaximumPasses"] = 12

    # Broadband Interpolating Frequency Sweep (2.0 GHz - 18.0 GHz)
    sweep = setup.create_frequency_sweep(
        name="Sweep1",
        unit="GHz",
        start_frequency=2.0,
        stop_frequency=18.0,
        num_of_freq_points=401,
        sweep_type="Interpolating"
    )

    # Save project file
    app.save_project("Conformal_8Element_Ogive_Array.aedt")
    print("HFSS Model generated and saved as Conformal_8Element_Ogive_Array.aedt")

if __name__ == "__main__":
    build_array_model()