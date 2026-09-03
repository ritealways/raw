"""
Creates sample Excel files so you have something to test with right away.

RUN THIS ONCE, BEFORE STARTING THE SERVER:
    python generate_sample_excel.py

It creates:
  data/anaplan_source/input_data.xlsx
      -> Pretend data sitting inside Anaplan. This is what the IMPORT
         endpoint (/api/import-from-anaplan) will read.

  data/to_export/output_data.xlsx
      -> A sample "processed" file. Upload THIS file in Postman to test
         the EXPORT endpoint (/api/export-to-anaplan).
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    source_folder = os.path.join(BASE_DIR, "data", "anaplan_source")
    to_export_folder = os.path.join(BASE_DIR, "data", "to_export")
    os.makedirs(source_folder, exist_ok=True)
    os.makedirs(to_export_folder, exist_ok=True)

    # Sample "input" data - pretend this is what Anaplan is exporting to us
    input_df = pd.DataFrame({
        "Region": ["North", "South", "East", "West"],
        "Product": ["Widget A", "Widget B", "Widget A", "Widget C"],
        "Month": ["Jan-2026", "Jan-2026", "Feb-2026", "Feb-2026"],
        "Actuals": [12000, 8500, 15300, 9800],
    })
    input_path = os.path.join(source_folder, "input_data.xlsx")
    input_df.to_excel(input_path, index=False)
    print(f"Created sample source file: {input_path}")

    # Sample "output" data - pretend this is what we want to push back to Anaplan
    output_df = pd.DataFrame({
        "Region": ["North", "South", "East", "West"],
        "Product": ["Widget A", "Widget B", "Widget A", "Widget C"],
        "Month": ["Jan-2026", "Jan-2026", "Feb-2026", "Feb-2026"],
        "Forecast": [12500, 9000, 15800, 10200],
    })
    output_path = os.path.join(to_export_folder, "output_data.xlsx")
    output_df.to_excel(output_path, index=False)
    print(f"Created sample output file: {output_path}")

    print("\nDone. You're ready to start the server and test with Postman.")


if __name__ == "__main__":
    main()
