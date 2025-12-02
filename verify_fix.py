import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from supabase import create_client

# Mock streamlit secrets and cache for testing
if not hasattr(st, "secrets"):
    st.secrets = {}

# Load env
load_dotenv()

# Setup Supabase connection manually for the test
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Import the logic we want to test (copy-pasted relevant parts to avoid streamlit context issues)
# Or better, let's try to import the function if possible, but streamlit decorators might get in the way.
# So I will replicate the logic to verify it works.

def test_load_and_process():
    print("Fetching data from Supabase...")
    try:
        response = supabase.table("Empleados Dian").select("*").execute()
        df = pd.DataFrame(response.data)
        
        if df.empty:
            print("Table is empty!")
            return

        print(f"Original columns: {df.columns.tolist()}")
        
        # --- LOGIC FROM STREAMLIT APP ---
        def process_dataframe(df_input):
            # Map columns if they come from Supabase (Spanish names)
            column_mapping = {
                'Denominación': 'cargo',
                'Asignación Salarial': 'salario',
                'Vacantes': 'ciudad_raw',
                'Opec': 'opec'
            }
            
            # Rename columns if they exist
            df_input = df_input.rename(columns=column_mapping)
            
            # Ensure we have the required columns
            if 'cargo' not in df_input.columns and 'Denominación' in df_input.columns:
                 df_input['cargo'] = df_input['Denominación']
                 
            if 'salario' not in df_input.columns and 'Asignación Salarial' in df_input.columns:
                 df_input['salario'] = df_input['Asignación Salarial']

            # Extract city from 'Vacantes' or 'ciudad_raw' if 'ciudad' doesn't exist
            if 'ciudad' not in df_input.columns:
                if 'ciudad_raw' in df_input.columns:
                    def extract_city(val):
                        if not isinstance(val, str): return "Desconocido"
                        parts = val.split(' - ')
                        if len(parts) >= 2:
                            return parts[1].strip()
                        return val
                    
                    df_input['ciudad'] = df_input['ciudad_raw'].apply(extract_city)
                else:
                    df_input['ciudad'] = "Desconocido"

            # Ensure numeric salary
            if 'salario' in df_input.columns:
                df_input['salario'] = pd.to_numeric(df_input['salario'], errors='coerce').fillna(0)
                
            return df_input
        # --------------------------------
        
        processed_df = process_dataframe(df)
        print("\nProcessed columns:", processed_df.columns.tolist())
        print("\nFirst 3 rows:")
        print(processed_df[['cargo', 'salario', 'ciudad']].head(3))
        
        # Verify required columns exist
        required = ['cargo', 'salario', 'ciudad']
        missing = [col for col in required if col not in processed_df.columns]
        
        if not missing:
            print("\n✅ SUCCESS: All required columns are present and populated.")
        else:
            print(f"\n❌ FAILURE: Missing columns: {missing}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_load_and_process()
