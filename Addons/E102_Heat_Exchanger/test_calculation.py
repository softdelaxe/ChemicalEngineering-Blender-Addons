
from calculations import calculate_design

result = calculate_design()

print("\n===== E-102 HEAT EXCHANGER TEST =====")

print("Process duty:",
      result["process"]["process_duty_kw"], "kW")

print("Design duty:",
      result["design"]["design_duty_kw"], "kW")

print("Actual heating-medium flow:",
      result["heating_medium"]["actual_mass_flow_kg_h"], "kg/h")

print("Design heating-medium flow:",
      result["heating_medium"]["design_mass_flow_kg_h"], "kg/h")

print("LMTD:",
      result["lmtd"]["lmtd_k"], "K")

print("Required heat-transfer area:",
      result["area"]["required_area_m2"], "m²")

print("\n===== TEST COMPLETED =====")
