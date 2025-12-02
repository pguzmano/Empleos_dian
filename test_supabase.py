import os
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd

# Load environment variables
load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print(f"URL: {url}")
print(f"Key (first 50 chars): {key[:50]}...")
print(f"Key length: {len(key)}")
print()

try:
    print("Creating Supabase client...")
    supabase = create_client(url, key)
    print("[OK] Client created successfully")
    print()
    
    print("Attempting to query 'Empleados Dian' table...")
    response = supabase.table("Empleados Dian").select("*").limit(5).execute()
    print(f"[OK] Query successful!")
    print(f"  Rows returned: {len(response.data)}")
    
    if response.data:
        df = pd.DataFrame(response.data)
        print(f"  Columns: {list(df.columns)}")
        print(f"\n  First row:")
        for col in df.columns:
            print(f"    {col}: {df.iloc[0][col]}")
    
except Exception as e:
    print(f"[ERROR] {type(e).__name__}")
    print(f"  Message: {str(e)}")
    import traceback
    print(f"\n  Full traceback:")
    traceback.print_exc()
