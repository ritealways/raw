"""
Import Input from Anaplan (Mock)
This script simulates reading/importing data from Anaplan.
It can:
1. Read an Excel file from a source folder (mocking Anaplan export)
2. Copy it to the input_from_anaplan folder
3. Display file contents and statistics

Run: python import_from_anaplan.py
"""

import pandas as pd
import os
import shutil
from datetime import datetime
import argparse

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, "input_from_anaplan")
SOURCE_FOLDER = os.path.join(BASE_DIR, "source_files")  # Mock Anaplan source

def ensure_folders():
    """Create necessary folders if they don't exist"""
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(SOURCE_FOLDER, exist_ok=True)
    print(f"✅ Folders ready:")
    print(f"   Source: {SOURCE_FOLDER}")
    print(f"   Input:  {INPUT_FOLDER}")

def create_sample_source_file():
    """Create a sample Excel file in source folder for testing"""
    sample_data = {
        'Product': ['Laptop', 'Mouse', 'Keyboard', 'Monitor', 'Headphones'],
        'Category': ['Electronics', 'Accessories', 'Accessories', 'Electronics', 'Accessories'],
        'Quantity': [100, 500, 300, 150, 200],
        'Unit_Price': [999.99, 29.99, 59.99, 299.99, 89.99],
        'Region': ['North', 'South', 'East', 'West', 'North'],
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May']
    }

    df = pd.DataFrame(sample_data)

    # Add calculated column
    df['Total_Value'] = df['Quantity'] * df['Unit_Price']

    sample_file = os.path.join(SOURCE_FOLDER, "anaplan_sales_data.xlsx")
    df.to_excel(sample_file, index=False, sheet_name='Sales Data')

    print(f"✅ Sample source file created: {sample_file}")
    print(f"   Rows: {len(df)}, Columns: {len(df.columns)}")
    return sample_file

def import_from_anaplan(source_file_path=None, auto_create_sample=True):
    """
    Import data from Anaplan (mock)

    Args:
        source_file_path: Path to the source Excel file (mock Anaplan export)
        auto_create_sample: If True and no source file, create a sample file

    Returns:
        dict: Import result with file info
    """
    print("\n" + "=" * 60)
    print("  IMPORT FROM ANAPLAN (MOCK)")
    print("=" * 60)

    ensure_folders()

    # If no source file provided, create sample
    if source_file_path is None or not os.path.exists(source_file_path):
        if auto_create_sample:
            print("\n⚠️  No source file found. Creating sample data...")
            source_file_path = create_sample_source_file()
        else:
            print("❌ Error: Source file not found and auto_create_sample is False")
            return {"success": False, "error": "Source file not found"}

    try:
        # Read the source file
        print(f"\n📥 Reading source file: {source_file_path}")

        if source_file_path.endswith('.csv'):
            df = pd.read_csv(source_file_path)
        else:
            df = pd.read_excel(source_file_path)

        # Display file info
        print(f"\n📊 File Contents Preview:")
        print("-" * 60)
        print(df.head(10).to_string())
        print("-" * 60)
        print(f"   Total Rows: {len(df)}")
        print(f"   Total Columns: {len(df.columns)}")
        print(f"   Column Names: {list(df.columns)}")
        print(f"   Data Types:")
        for col, dtype in df.dtypes.items():
            print(f"      {col}: {dtype}")

        # Copy to input folder with timestamp
        filename = os.path.basename(source_file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"imported_{timestamp}_{filename}"
        destination_path = os.path.join(INPUT_FOLDER, new_filename)

        shutil.copy2(source_file_path, destination_path)

        print(f"\n✅ File imported successfully!")
        print(f"   Saved as: {new_filename}")
        print(f"   Location: {destination_path}")

        # Generate summary statistics
        summary = {
            "success": True,
            "original_file": source_file_path,
            "imported_file": new_filename,
            "imported_path": destination_path,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "statistics": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "column_names": list(df.columns),
                "numeric_columns": list(df.select_dtypes(include=['int64', 'float64']).columns),
                "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
            }
        }

        # Save summary to JSON
        summary_file = os.path.join(INPUT_FOLDER, f"summary_{timestamp}.json")
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"   Summary saved: {summary_file}")

        return summary

    except Exception as e:
        print(f"\n❌ Import failed: {str(e)}")
        return {"success": False, "error": str(e)}

def list_imported_files():
    """List all files in the input folder"""
    print("\n" + "=" * 60)
    print("  IMPORTED FILES")
    print("=" * 60)

    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(('.xlsx', '.xls', '.csv'))]

    if not files:
        print("No imported files found.")
        return

    print(f"\nTotal imported files: {len(files)}\n")

    for i, filename in enumerate(sorted(files, reverse=True), 1):
        filepath = os.path.join(INPUT_FOLDER, filename)
        file_stat = os.stat(filepath)
        size_kb = round(file_stat.st_size / 1024, 2)
        modified = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{i}. {filename}")
        print(f"   Size: {size_kb} KB")
        print(f"   Modified: {modified}")
        print()

# ==================== MAIN ====================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import data from Anaplan (Mock)')
    parser.add_argument('--file', '-f', type=str, help='Path to source Excel file')
    parser.add_argument('--list', '-l', action='store_true', help='List all imported files')
    parser.add_argument('--no-sample', action='store_true', help='Do not create sample file if source missing')

    args = parser.parse_args()

    if args.list:
        list_imported_files()
    else:
        result = import_from_anaplan(
            source_file_path=args.file,
            auto_create_sample=not args.no_sample
        )

        if result["success"]:
            print("\n" + "=" * 60)
            print("  IMPORT COMPLETE ✓")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("  IMPORT FAILED ✗")
            print("=" * 60)
