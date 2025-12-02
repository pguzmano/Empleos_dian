import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

print("Querying table to see what columns exist...")
try:
    # Get one row to see the structure
    response = supabase.table("Empleados Dian").select("*").limit(1).execute()
    
    if response.data and len(response.data) > 0:
        print(f"\nColumns in the table:")
        for col in response.data[0].keys():
            print(f"  - {col}")
    else:
        print("\nTable is empty. Let me try to insert a test row to see what columns are expected...")
        # Try inserting an empty dict to see what error we get
        try:
            test_response = supabase.table("Empleados Dian").insert({}).execute()
        except Exception as e:
            print(f"\nError: {e}")
            
except Exception as e:
    print(f"Error: {e}")
