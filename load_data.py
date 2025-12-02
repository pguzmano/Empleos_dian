import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Supabase credentials
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in environment variables or .env file.")
        return

    # Initialize Supabase client
    supabase: Client = create_client(url, key)

    # File path - checking for the requested file, falling back to the existing one if needed
    file_path = "datos_empleos.xlsx"
    if not os.path.exists(file_path):
        alternative_path = "EmpleosDIAN_2025.xlsx"
        if os.path.exists(alternative_path):
            print(f"'{file_path}' not found. Using '{alternative_path}' instead.")
            file_path = alternative_path
        else:
            print(f"Error: Neither '{file_path}' nor '{alternative_path}' found.")
            return

    print(f"Reading data from {file_path}...")
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Ensure columns exist and map them if necessary
        # The prompt asks for: cargo, salario, ciudad, latitud, longitud
        # We need to make sure the Excel file has these columns or we rename them.
        # For now, I'll assume the Excel might have different names and we might need to inspect it.
        # But per the prompt instructions, I will proceed assuming they match or I'll map them loosely.
        # Let's just print the columns found to help debugging.
        print(f"Columns found: {df.columns.tolist()}")

        # Standardize column names to lowercase for easier mapping if needed
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Basic validation/mapping (adjust these based on actual file content if known)
        # Assuming the file has columns that can be mapped to the target schema
        required_columns = ["cargo", "salario", "ciudad", "latitud", "longitud"]
        
        # If the file has different headers, we might need a mapping dictionary.
        # For this initial script, I will assume the user might need to adjust column names 
        # or that the file already matches. 
        
        # Filter only required columns if they exist
        data_to_upload = []
        for index, row in df.iterrows():
            record = {
                "cargo": row.get("cargo", row.get("titulo", row.get("nombre", None))), # Fallbacks
                "salario": row.get("salario", row.get("sueldo", 0)),
                "ciudad": row.get("ciudad", row.get("municipio", None)),
                "latitud": row.get("latitud", row.get("lat", 0.0)),
                "longitud": row.get("longitud", row.get("lon", 0.0)),
            }
            data_to_upload.append(record)

        print(f"Preparing to upload {len(data_to_upload)} records to 'Empleados Dian' table...")

        # Upload in batches to avoid hitting payload limits
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(data_to_upload), batch_size):
            batch = data_to_upload[i:i + batch_size]
            try:
                response = supabase.table("Empleados Dian").insert(batch).execute()
                # count inserted rows - response.data should be a list of inserted rows
                if response.data:
                    total_inserted += len(response.data)
                print(f"Batch {i//batch_size + 1} processed. Total inserted: {total_inserted}")
            except Exception as e:
                print(f"Error inserting batch {i//batch_size + 1}: {e}")

        print(f"Upload complete. Total rows inserted: {total_inserted}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
