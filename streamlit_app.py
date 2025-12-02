import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables if present
load_dotenv()

# Page config
st.set_page_config(page_title="Empleos DIAN", layout="wide")

# Configure Gemini
# Configure Gemini
gemini_api_key = os.environ.get("GEMINI_API_KEY")

# Check secrets if not in env
if not gemini_api_key and "GEMINI_API_KEY" in st.secrets:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]

if gemini_api_key and "tu_gemini_api_key_aqui" not in gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    gemini_enabled = True
else:
    gemini_enabled = False

# Initialize connection
@st.cache_resource
def init_connection():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    # Fallback to st.secrets if not in os.environ (useful for Streamlit Cloud)
    try:
        if not url and "SUPABASE_URL" in st.secrets:
            url = st.secrets["SUPABASE_URL"]
        if not key and "SUPABASE_KEY" in st.secrets:
            key = st.secrets["SUPABASE_KEY"]
    except FileNotFoundError:
        pass # No secrets file found, just ignore
    except Exception:
        pass # Other errors accessing secrets
        
    if not url or not key or "tu_supabase_url_aqui" in url:
        st.error("⚠️ Falta configuración: Por favor configura SUPABASE_URL y SUPABASE_KEY en el archivo .env o .streamlit/secrets.toml")
        st.stop()
        
    return create_client(url, key)

supabase = init_connection()

# Load data
# Load data
@st.cache_data(ttl=600)
def load_data():
    # Try Supabase first
    try:
        response = supabase.table("empleos_dian").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            return df
    except Exception as e:
        print(f"Supabase connection failed: {e}")
    
    # Fallback to local file
    try:
        local_file = "EmpleosDIAN_2025.xlsx"
        if os.path.exists(local_file):
            st.warning("⚠️ Modo Offline: Usando datos locales (Excel) debido a error de conexión con la base de datos.")
            df = pd.read_excel(local_file)
            
            # Helper to find col by keyword
            def get_col(keywords, exclude=None):
                for col in df.columns:
                    if any(k in col.lower() for k in keywords):
                        if exclude and any(e in col.lower() for e in exclude):
                            continue
                        return col
                return None

            cargo_col = get_col(['denominac', 'cargo'])
            salario_col = get_col(['asignaci', 'salarial', 'sueldo'])
            # Exclude 'cantidad' to avoid picking 'Cantidad de Vacantes'
            ciudad_col = get_col(['vacantes', 'ubicacion', 'ciudad'], exclude=['cantidad']) 
            
            new_df = pd.DataFrame()
            if cargo_col: new_df['cargo'] = df[cargo_col]
            if salario_col: new_df['salario'] = df[salario_col]
            if ciudad_col: 
                # Clean up city data if it contains multiple locations or formatting
                new_df['ciudad'] = df[ciudad_col].astype(str).apply(lambda x: x.split('-')[1].strip() if '-' in x else x)
            
            # Add missing cols for compatibility
            new_df['latitud'] = None
            new_df['longitud'] = None
            
            return new_df
    except Exception as e:
        st.error(f"Error cargando datos locales: {e}")
    
    return pd.DataFrame()

# Layout
st.title("Dashboard de Empleos DIAN")

# Load data
df = load_data()

# Gemini Assistant Functions
def generate_data_summary(dataframe):
    """Generate a summary of the employment data using Gemini"""
    if not gemini_enabled or dataframe.empty:
        return None
    
    try:
        # Prepare data context
        total_jobs = len(dataframe)
        cities = dataframe['ciudad'].value_counts().head(5).to_dict()
        top_positions = dataframe['cargo'].value_counts().head(5).to_dict()
        avg_salary = dataframe['salario'].mean()
        
        prompt = f"""Analiza estos datos de empleos de la DIAN en Colombia y genera un resumen ejecutivo en español (máximo 150 palabras):
        
- Total de empleos: {total_jobs}
- Ciudades principales: {cities}
- Cargos más comunes: {top_positions}
- Salario promedio: ${avg_salary:,.0f}

Incluye insights relevantes sobre patrones geográficos, distribución de cargos y tendencias salariales."""

        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generando resumen: {e}")
        return None

def chat_with_data(user_question, dataframe):
    """Answer questions about the employment data using Gemini"""
    if not gemini_enabled or dataframe.empty:
        return "El asistente de IA no está configurado. Agrega tu GEMINI_API_KEY al archivo .env"
    
    try:
        # Prepare data context
        data_summary = f"""Datos de empleos DIAN disponibles:
- Total registros: {len(dataframe)}
- Ciudades: {dataframe['ciudad'].unique().tolist()[:10]}
- Cargos: {dataframe['cargo'].unique().tolist()[:10]}
- Rango salarial: ${dataframe['salario'].min():,.0f} - ${dataframe['salario'].max():,.0f}
"""
        
        prompt = f"""{data_summary}

Pregunta del usuario: {user_question}

Responde la pregunta en español de forma clara y concisa basándote en los datos disponibles."""

        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

if not df.empty:
    # Sidebar Filters
    with st.sidebar:
        st.header("Filtros")
        
        # City Filter
        cities = sorted(df["ciudad"].dropna().unique())
        selected_cities = st.multiselect("Seleccionar Ciudad", cities, default=cities)
        
        # Salary Filter
        min_salary = int(df["salario"].min())
        max_salary = int(df["salario"].max())
        selected_salary = st.slider("Rango de Salario", min_salary, max_salary, (min_salary, max_salary))
        
        # AI Assistant
        st.divider()
        st.header("🤖 Asistente IA")
        
        if gemini_enabled:
            st.success("✅ Gemini activado")
            
            # Chat interface
            user_question = st.text_area(
                "Hazle una pregunta a la IA sobre los datos:",
                placeholder="Ej: ¿Cuál es el cargo mejor pagado en Bogotá?",
                height=100
            )
            
            if st.button("Preguntar", use_container_width=True):
                if user_question.strip():
                    with st.spinner("Analizando..."):
                        answer = chat_with_data(user_question, df)
                        st.info(answer)
                else:
                    st.warning("Por favor escribe una pregunta")
        else:
            st.warning("⚠️ Gemini no configurado")
            st.caption("Agrega tu GEMINI_API_KEY al archivo .env para activar el asistente de IA")

    # Apply Filters
    filtered_df = df[
        (df["ciudad"].isin(selected_cities)) &
        (df["salario"] >= selected_salary[0]) &
        (df["salario"] <= selected_salary[1])
    ]

    # Main Content
    
    # AI-Generated Summary
    if gemini_enabled:
        with st.expander("📊 Resumen Generado por IA", expanded=True):
            if st.button("🔄 Generar Resumen con Gemini", use_container_width=True):
                with st.spinner("Generando análisis con IA..."):
                    summary = generate_data_summary(filtered_df)
                    if summary:
                        st.markdown(summary)
    
    # KPI
    st.metric("Total de Empleos", len(filtered_df))
    
    # Bar Chart
    st.subheader("Empleos por Cargo")
    if not filtered_df.empty:
        jobs_by_cargo = filtered_df["cargo"].value_counts()
        st.bar_chart(jobs_by_cargo)
    else:
        st.info("No hay datos para mostrar con los filtros seleccionados.")

    # Map
    st.subheader("Ubicación de Empleos")
    # Ensure lat/lon columns exist and are numeric
    map_cols = ["latitud", "longitud"]
    if all(col in filtered_df.columns for col in map_cols):
        # Drop rows with NaN in lat/lon for the map
        map_data = filtered_df.dropna(subset=map_cols)
        if not map_data.empty:
            st.map(map_data)
            st.caption(f"Mostrando {len(map_data)} ubicaciones en el mapa.")
        else:
            st.info("No hay datos de ubicación válidos para mostrar en el mapa.")
    else:
        st.warning("El conjunto de datos no contiene columnas de 'latitud' y 'longitud'.")

    # Dataframe
    st.subheader("Detalle de Empleos")
    st.dataframe(filtered_df, use_container_width=True)

else:
    st.info("No hay datos disponibles o no se pudo conectar a la base de datos.")
