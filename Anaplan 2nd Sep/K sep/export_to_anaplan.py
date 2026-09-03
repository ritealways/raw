"""
Export Output to Anaplan (Mock)
This script simulates creating and exporting data to Anaplan.
It can:
1. Read processed data from input/processed folder
2. Apply business logic/transformations
3. Save output to output_to_anaplan folder (mocking Anaplan import)
4. Generate export report

Run: python export_to_anaplan.py
"""

import pandas as pd
import os
import shutil
from datetime import datetime
import argparse
import json

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, "input_from_anaplan")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output_to_anaplan")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed_data")

def ensure_folders():
    """Create necessary folders if they don't exist"""
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)
    print(f"✅ Folders ready:")
    print(f"   Input:    {INPUT_FOLDER}")
    print(f"   Output:   {OUTPUT_FOLDER}")
    print(f"   Processed: {PROCESSED_FOLDER}")

def process_data_for_export(input_file_path):
    """
    Process input data and prepare for export to Anaplan
    This simulates business logic/transformations
    """
    print(f"\n🔧 Processing data for export...")

    # Read input file
    if input_file_path.endswith('.csv'):
        df = pd.read_csv(input_file_path)
    else:
        df = pd.read_excel(input_file_path)

    print(f"   Original rows: {len(df)}")
    print(f"   Original columns: {list(df.columns)}")

    # Simulate business transformations
    # 1. Add export metadata
    df['export_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df['export_batch_id'] = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    df['data_source'] = "Mock Anaplan Integration"

    # 2. Data validation flags
    df['validation_status'] = 'VALID'

    # Example validation: flag rows with negative quantities
    if 'Quantity' in df.columns:
        df.loc[df['Quantity'] < 0, 'validation_status'] = 'INVALID_NEGATIVE_QTY'

    # 3. Calculate aggregates if applicable
    if 'Quantity' in df.columns and 'Unit_Price' in df.columns:
        if 'Total_Value' not in df.columns:
            df['Total_Value'] = df['Quantity'] * df['Unit_Price']

        # Add summary statistics per category
        if 'Category' in df.columns:
            category_summary = df.groupby('Category')['Total_Value'].sum().reset_index()
            category_summary.columns = ['Category', 'Category_Total_Value']
            df = df.merge(category_summary, on='Category', how='left')

    # 4. Sort by relevant columns
    if 'Region' in df.columns and 'Product' in df.columns:
        df = df.sort_values(['Region', 'Product'])

    print(f"   Processed rows: {len(df)}")
    print(f"   New columns added: {list(df.columns[-5:])}")  # Show last 5 columns

    return df

def export_to_anaplan(input_file_path=None, output_filename=None):
    """
    Export processed data to Anaplan (mock)

    Args:
        input_file_path: Path to the input file to process
        output_filename: Custom name for the output file

    Returns:
        dict: Export result with file info
    """
    print("\n" + "=" * 60)
    print("  EXPORT TO ANAPLAN (MOCK)")
    print("=" * 60)

    ensure_folders()

    # If no input file provided, use the most recent file from input folder
    if input_file_path is None or not os.path.exists(input_file_path):
        print("\n🔍 Looking for latest imported file...")

        input_files = [f for f in os.listdir(INPUT_FOLDER) 
                      if f.endswith(('.xlsx', '.xls', '.csv')) and not f.startswith('summary_')]

        if not input_files:
            print("⚠️  No input files found. Creating sample data...")
            # Create sample data
            sample_data = {
                'Product': ['Laptop', 'Mouse', 'Keyboard'],
                'Category': ['Electronics', 'Accessories', 'Accessories'],
                'Quantity': [100, 500, 300],
                'Unit_Price': [999.99, 29.99, 59.99],
                'Region': ['North', 'South', 'East']
            }
            df_sample = pd.DataFrame(sample_data)
            sample_file = os.path.join(INPUT_FOLDER, "sample_input.xlsx")
            df_sample.to_excel(sample_file, index=False)
            input_file_path = sample_file
            print(f"   Created sample: {sample_file}")
        else:
            # Get most recent file
            input_files.sort(key=lambda x: os.path.getmtime(os.path.join(INPUT_FOLDER, x)), reverse=True)
            input_file_path = os.path.join(INPUT_FOLDER, input_files[0])
            print(f"   Using latest file: {input_files[0]}")

    try:
        # Process the data
        processed_df = process_data_for_export(input_file_path)

        # Save processed version
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if output_filename is None:
            original_name = os.path.basename(input_file_path)
            name_without_ext = os.path.splitext(original_name)[0]
            output_filename = f"exported_{timestamp}_{name_without_ext}.xlsx"
        else:
            if not output_filename.endswith('.xlsx'):
                output_filename += '.xlsx'

        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        # Save with formatting
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            processed_df.to_excel(writer, sheet_name='Export Data', index=False)

            # Add summary sheet
            summary_data = {
                'Metric': [
                    'Export Timestamp',
                    'Total Rows',
                    'Total Columns',
                    'Source File',
                    'Export Status',
                    'Validation Passed',
                    'Validation Failed'
                ],
                'Value': [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    len(processed_df),
                    len(processed_df.columns),
                    os.path.basename(input_file_path),
                    'SUCCESS',
                    len(processed_df[processed_df['validation_status'] == 'VALID']),
                    len(processed_df[processed_df['validation_status'] != 'VALID'])
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Export Summary', index=False)

        print(f"\n📤 Export completed!")
        print(f"   Output file: {output_filename}")
        print(f"   Location: {output_path}")
        print(f"   Sheets: Export Data, Export Summary")

        # Generate export report
        report = {
            "success": True,
            "export_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input_file": os.path.basename(input_file_path),
            "output_file": output_filename,
            "output_path": output_path,
            "statistics": {
                "total_rows": len(processed_df),
                "total_columns": len(processed_df.columns),
                "column_names": list(processed_df.columns),
                "file_size_kb": round(os.path.getsize(output_path) / 1024, 2)
            },
            "validation": {
                "total_valid": int((processed_df['validation_status'] == 'VALID').sum()),
                "total_invalid": int((processed_df['validation_status'] != 'VALID').sum())
            }
        }

        # Save report
        report_file = os.path.join(OUTPUT_FOLDER, f"report_{timestamp}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"   Report saved: {report_file}")

        # Display preview
        print(f"\n📊 Output Preview:")
        print("-" * 60)
        print(processed_df.head().to_string())
        print("-" * 60)

        return report

    except Exception as e:
        print(f"\n❌ Export failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def list_exported_files():
    """List all files in the output folder"""
    print("\n" + "=" * 60)
    print("  EXPORTED FILES")
    print("=" * 60)

    files = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith(('.xlsx', '.xls', '.csv'))]

    if not files:
        print("No exported files found.")
        return

    print(f"\nTotal exported files: {len(files)}\n")

    for i, filename in enumerate(sorted(files, reverse=True), 1):
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        file_stat = os.stat(filepath)
        size_kb = round(file_stat.st_size / 1024, 2)
        modified = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{i}. {filename}")
        print(f"   Size: {size_kb} KB")
        print(f"   Modified: {modified}")
        print()

# ==================== MAIN ====================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export data to Anaplan (Mock)')
    parser.add_argument('--file', '-f', type=str, help='Path to input Excel file')
    parser.add_argument('--output', '-o', type=str, help='Custom output filename')
    parser.add_argument('--list', '-l', action='store_true', help='List all exported files')

    args = parser.parse_args()

    if args.list:
        list_exported_files()
    else:
        result = export_to_anaplan(
            input_file_path=args.file,
            output_filename=args.output
        )

        if result["success"]:
            print("\n" + "=" * 60)
            print("  EXPORT COMPLETE ✓")
            print("=" * 60)
            print(f"\n📋 Next Steps:")
            print(f"   1. Check output file: {result['output_path']}")
            print(f"   2. Open in Excel to verify data")
            print(f"   3. Use Postman to download via API")
        else:
            print("\n" + "=" * 60)
            print("  EXPORT FAILED ✗")
            print("=" * 60)
