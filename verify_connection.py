import toml
from supabase import create_client
import sys

try:
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets.get("SUPABASE_URL")
    key = secrets.get("SUPABASE_KEY")
    
    print(f"Testing URL: {url}")
    print(f"Testing Key: {key}")

    if "supabase.com/dashboard" in url:
        print("\n[ERROR] The URL provided seems to be the Dashboard URL, not the API URL.")
        print("The API URL usually looks like: https://<project_id>.supabase.co")
        print(f"Based on your URL, it might be: https://lzkerhnoypdfudipmjvm.supabase.co")
    
    if len(key) < 20:
        print("\n[WARNING] The key provided is very short. It might be a password instead of the API Key.")
        print("The API Key (anon/public) is usually a long string starting with 'eyJ...'.")

    try:
        supabase = create_client(url, key)
        # Try a simple request
        supabase.table("Empleados Dian").select("*").limit(1).execute()
        print("\n[SUCCESS] Connection successful!")
    except Exception as e:
        print(f"\n[FAILURE] Connection failed: {e}")

except Exception as e:
    print(f"Error reading secrets or running test: {e}")
