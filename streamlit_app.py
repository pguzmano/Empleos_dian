import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import google.generativeai as genai
import plotly.express as px

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
        # Instead of stopping, we return None to indicate no connection
        return None
        
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"Failed to create Supabase client: {e}")
        return None

supabase = init_connection()

# City Coordinates Mapping (Colombia)
CITY_COORDINATES = {
    "Bogotá D.C.": {"lat": 4.7110, "lon": -74.0721},
    "Medellín": {"lat": 6.2442, "lon": -75.5812},
    "Cali": {"lat": 3.4516, "lon": -76.5320},
    "Barranquilla": {"lat": 10.9685, "lon": -74.7813},
    "Cartagena": {"lat": 10.3910, "lon": -75.4794},
    "Cartagena De Indias": {"lat": 10.3910, "lon": -75.4794},
    "Cúcuta": {"lat": 7.8939, "lon": -72.5078},
    "Bucaramanga": {"lat": 7.1193, "lon": -73.1227},
    "Pereira": {"lat": 4.8133, "lon": -75.6961},
    "Santa Marta": {"lat": 11.2408, "lon": -74.1990},
    "Ibagué": {"lat": 4.4389, "lon": -75.2322},
    "Villavicencio": {"lat": 4.1420, "lon": -73.6266},
    "Manizales": {"lat": 5.0703, "lon": -75.5138},
    "Neiva": {"lat": 2.9273, "lon": -75.2819},
    "Armenia": {"lat": 4.5339, "lon": -75.6811},
    "Pasto": {"lat": 1.2136, "lon": -77.2811},
    "Montería": {"lat": 8.7479, "lon": -75.8814},
    "Sincelejo": {"lat": 9.3047, "lon": -75.3978},
    "Popayán": {"lat": 2.4382, "lon": -76.6132},
    "Tunja": {"lat": 5.5353, "lon": -73.3678},
    "Riohacha": {"lat": 11.5444, "lon": -72.9072},
    "Valledupar": {"lat": 10.4631, "lon": -73.2532},
    "Quibdó": {"lat": 5.6947, "lon": -76.6611},
    "Florencia": {"lat": 1.6175, "lon": -75.6062},
    "Yopal": {"lat": 5.3378, "lon": -72.3959},
    "Arauca": {"lat": 7.0847, "lon": -70.7591},
    "San Andrés": {"lat": 12.5847, "lon": -81.7006},
    "Leticia": {"lat": -4.2153, "lon": -69.9406},
    "Puerto Carreño": {"lat": 6.1890, "lon": -67.4859},
    "Inírida": {"lat": 3.8653, "lon": -67.9239},
    "Mitú": {"lat": 1.1983, "lon": -70.1733},
    "Mocoa": {"lat": 1.1462, "lon": -76.6461},
    "San José del Guaviare": {"lat": 2.5729, "lon": -72.6378},
    "Tumaco": {"lat": 1.7986, "lon": -78.8156},
    "Buenaventura": {"lat": 3.8801, "lon": -77.0312},
    "Barrancabermeja": {"lat": 7.0653, "lon": -73.8547},
    "Ipiales": {"lat": 0.8248, "lon": -77.6441},
    "Palmira": {"lat": 3.5394, "lon": -76.3036},
    "Tuluá": {"lat": 4.0847, "lon": -76.1969},
    "Girardot": {"lat": 4.3091, "lon": -74.8016},
    "Sogamoso": {"lat": 5.7145, "lon": -72.9339},
    "Duitama": {"lat": 5.8245, "lon": -73.0341}
}

# Load data
@st.cache_data(ttl=600)
def load_data():
    # Helper to process/normalize dataframe
    def process_dataframe(df_input):
        # Map columns if they come from Supabase (Spanish names)
        column_mapping = {
            'Denominación': 'cargo',
            'Asignación Salarial': 'salario',
            'Vacantes': 'ciudad_raw',
            'Opec': 'opec',
            'Categoria': 'categoria',
            'categoria': 'categoria',
            'Convocatoria': 'convocatoria',
            'convocatoria': 'convocatoria',
            'Descripción': 'descripcion',
            'Descripci\u00f3n': 'descripcion',
            'Estudio': 'estudio',
            'Experiencia': 'experiencia'
        }
        
        # Rename columns if they exist
        df_input = df_input.rename(columns=column_mapping)
        
        # Ensure we have the required columns
        if 'cargo' not in df_input.columns and 'Denominación' in df_input.columns:
             df_input['cargo'] = df_input['Denominación']
             
        if 'salario' not in df_input.columns:
             if 'Asignación Salarial' in df_input.columns:
                 df_input['salario'] = df_input['Asignación Salarial']
             else:
                 df_input['salario'] = 0

        # Extract process from 'descripcion' if available
        if 'descripcion' in df_input.columns:
            def extract_proceso(val):
                if not isinstance(val, str):
                    return "Desconocido"
                # Look for pattern like XX-XX-XXXX at start
                import re
                # User wants first 4 letters with hyphen: IT-IT
                match = re.search(r'^([A-Z]{2}-[A-Z]{2})', val)
                if match:
                    return match.group(1)
                
                # Fallback: simple split
                parts = val.split('-')
                if len(parts) > 1 and len(parts[0].strip()) == 2 and len(parts[1].strip()) == 2:
                    return f"{parts[0].strip()}-{parts[1].strip()}"
                
                return "Otros"
            
            df_input['proceso'] = df_input['descripcion'].apply(extract_proceso)
        elif 'proceso' not in df_input.columns:
            df_input['proceso'] = "Desconocido"

        # Extract 'NBC' (Núcleo Básico de Conocimiento) from 'estudio' if available
        if 'estudio' in df_input.columns:
            def extract_nbc(val):
                if not isinstance(val, str):
                    return []
                # Pattern: "NBC: PROFESION"
                # Normalize spaces
                val = val.replace('\n', ' ').strip()
                parts = val.split("NBC:")
                extracted = []
                for part in parts[1:]:
                    # Clean up each part, stopping at separators like " ,O,"
                    clean_part = part.strip().split(" ,O,")[0]
                    # Also strip common trailing chars
                    clean_part = clean_part.strip(" .")
                    if clean_part:
                        extracted.append(clean_part)
                return list(set(extracted))
            
            df_input['estudios_parsed'] = df_input['estudio'].apply(extract_nbc)
        else:
            df_input['estudios_parsed'] = df_input.apply(lambda x: [], axis=1)

        # Extract city and vacancy count from 'Vacantes' or 'ciudad_raw'
        if 'ciudad' not in df_input.columns:
            if 'ciudad_raw' in df_input.columns:
                # Explode the dataframe to handle multiple cities per row
                # Format: "3 - Armenia..., 4 - Cali..." separated by commas
                df_input['ciudad_raw'] = df_input['ciudad_raw'].astype(str).str.split(',')
                df_input = df_input.explode('ciudad_raw')
                df_input['ciudad_raw'] = df_input['ciudad_raw'].str.strip()

                # Format usually: "2 - Bogotá D.C. - DONDE SE UBIQUE..."
                def extract_info(val):
                    city = "Desconocido"
                    vacancies = 1
                    
                    if isinstance(val, str):
                        parts = val.split(' - ')
                        # Try to extract vacancies count from first part
                        try:
                            if len(parts) > 0:
                                vacancies = int(parts[0].strip())
                        except ValueError:
                            pass
                        
                        # Try to extract city from second part
                        if len(parts) >= 2:
                            city = parts[1].strip()
                            
                    return pd.Series([city, vacancies])
                
                df_input[['ciudad', 'vacantes_count']] = df_input['ciudad_raw'].apply(extract_info)
            else:
                df_input['ciudad'] = "Desconocido"
                df_input['vacantes_count'] = 1

        # Ensure numeric salary
        if 'salario' in df_input.columns:
            df_input['salario'] = pd.to_numeric(df_input['salario'], errors='coerce').fillna(0)
            
        # Map cities to coordinates
        def get_lat(city):
            return CITY_COORDINATES.get(city, {}).get("lat", None)
        
        def get_lon(city):
            return CITY_COORDINATES.get(city, {}).get("lon", None)

        df_input['latitud'] = df_input['ciudad'].apply(get_lat)
        df_input['longitud'] = df_input['ciudad'].apply(get_lon)
            
        return df_input

    # Try Supabase first
    try:
        if supabase:
            response = supabase.table("Empleados Dian").select("*").execute()
            df = pd.DataFrame(response.data)
            if not df.empty:
                return process_dataframe(df)
    except Exception as e:
        # Log error to console but don't show to user unless debugging
        print(f"Supabase connection failed: {e}")
    
    # Fallback to local file
    try:
        local_file = "EmpleosDIAN_2025.xlsx"
        if os.path.exists(local_file):
            if supabase is None or 'response' in locals() or 'e' in locals():
                 # Only show warning if really offline to avoid clutter
                 pass
                 # st.toast("⚠️ Usando datos locales (Offline)", icon="📂")
                 
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
            categoria_col = get_col(['categoria', 'categor'])
            convocatoria_col = get_col(['convocatoria'])
            convocatoria_col = get_col(['convocatoria'])
            descripcion_col = get_col(['descripci'])
            estudio_col = get_col(['estudio'])
            experiencia_col = get_col(['experiencia'])
            
            new_df = pd.DataFrame()
            if cargo_col: new_df['cargo'] = df[cargo_col]
            if salario_col: new_df['salario'] = df[salario_col]
            if ciudad_col: 
                new_df['ciudad_raw'] = df[ciudad_col]
            if categoria_col:
                new_df['categoria'] = df[categoria_col]
            if convocatoria_col:
                new_df['convocatoria'] = df[convocatoria_col]
            if descripcion_col:
                new_df['descripcion'] = df[descripcion_col]
            if estudio_col:
                new_df['estudio'] = df[estudio_col]
            if experiencia_col:
                new_df['experiencia'] = df[experiencia_col]
            
            # Process the dataframe to extract city, vacancies and coords
            return process_dataframe(new_df)
            
    except Exception as e:
        st.error(f"Error cargando datos locales: {e}")
    
    return pd.DataFrame()

# Layout
st.title("Dashboard de Empleos DIAN")

# Load data
df = load_data()

# Show offline indicator if applicable
if 'supabase' not in globals() or supabase is None:
    st.markdown("""
        <div style="background-color: #f0f2f6; padding: 0.5rem; border-radius: 0.5rem; margin-bottom: 1rem; border-left: 5px solid #ffa500;">
            <span style="color: #555; font-weight: bold;">⚠️ Modo Offline:</span>
            <span style="color: #666;"> Se están mostrando datos locales porque no se pudo establecer conexión con la base de datos.</span>
        </div>
    """, unsafe_allow_html=True)

# Gemini Assistant Functions
def generate_data_summary(dataframe):
    """Generate a summary of the employment data using Gemini"""
    if not gemini_enabled or dataframe.empty:
        return None
    
    try:
        # Prepare data context
        total_jobs = len(dataframe)
        total_vacancies = dataframe['vacantes_count'].sum() if 'vacantes_count' in dataframe.columns else total_jobs
        cities = dataframe['ciudad'].value_counts().head(20).to_dict() # Increased context
        top_positions = dataframe['cargo'].value_counts().head(20).to_dict() # Increased context
        avg_salary = dataframe['salario'].mean()
        
        prompt = f"""Analiza estos datos de empleos de la DIAN en Colombia y genera un resumen ejecutivo detallado en español:
        
- Total de empleos (registros): {total_jobs}
- Total de vacantes: {total_vacancies}
- Ciudades principales (top 20): {cities}
- Cargos más comunes (top 20): {top_positions}
- Salario promedio: ${avg_salary:,.0f}

Incluye insights profundos sobre patrones geográficos, distribución de cargos, disparidades salariales y cualquier tendencia notable. No limites la longitud de tu respuesta, sé exhaustivo."""

        # Try multiple models in order of preference based on available models
        models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-1.5-flash']
        response = None
        errors = []
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                break # If successful, exit loop
            except Exception as e:
                errors.append(f"{model_name}: {str(e)}")
                continue
                
        if response:
            return response.text
        else:
            error_msg = "\n".join(errors)
            st.error(f"Error generando resumen. Detalles técnicos:\n{error_msg}")
            return None
    except Exception as e:
        st.error(f"Error general: {e}")
        return None

def chat_with_data(user_question, dataframe):
    """Answer questions about the employment data using Gemini"""
    if not gemini_enabled or dataframe.empty:
        return "El asistente de IA no está configurado. Agrega tu GEMINI_API_KEY al archivo .env"
    
    try:
        # Prepare data context - Increased limits for Pro model
        unique_cities = dataframe['ciudad'].unique().tolist()
        unique_cargos = dataframe['cargo'].unique().tolist()
        
        # If lists are too long, we still truncate but much less than before
        cities_str = str(unique_cities[:100]) + ("..." if len(unique_cities) > 100 else "")
        cargos_str = str(unique_cargos[:100]) + ("..." if len(unique_cargos) > 100 else "")
        
        data_summary = f"""Datos de empleos DIAN disponibles:
- Total registros: {len(dataframe)}
- Total vacantes: {dataframe['vacantes_count'].sum() if 'vacantes_count' in dataframe.columns else 'N/A'}
- Ciudades disponibles: {cities_str}
- Cargos disponibles: {cargos_str}
- Rango salarial: ${dataframe['salario'].min():,.0f} - ${dataframe['salario'].max():,.0f}
"""
        
        prompt = f"""{data_summary}

Pregunta del usuario: {user_question}

Responde la pregunta en español de forma completa y detallada basándote en los datos disponibles. Si la respuesta requiere una lista larga, proporciónala."""

        # Try multiple models in order of preference based on available models
        models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash', 'gemini-1.5-flash']
        response = None
        errors = []
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                break # If successful, exit loop
            except Exception as e:
                errors.append(f"{model_name}: {str(e)}")
                continue
        
        if response:
            return response.text
        else:
            error_msg = "\n".join(errors)
            return f"Error: No se pudo obtener respuesta. Detalles:\n{error_msg}"
    except Exception as e:
        return f"Error: {e}"

if not df.empty:
    # Handle Map Selection State
    # Check if a selection was made on the map (available in session state from previous run)
    if "map_selection" in st.session_state:
        selection = st.session_state.map_selection
        
        # Extract the currently selected city from the map selection
        current_map_city = None
        if selection and "selection" in selection and "points" in selection["selection"]:
            points = selection["selection"]["points"]
            if points:
                current_map_city = points[0]["hovertext"]
        
        # Initialize last_processed_map_city if not present
        if "last_processed_map_city" not in st.session_state:
            st.session_state.last_processed_map_city = None

        # Check if the extracted city has changed compared to what we last processed
        if current_map_city != st.session_state.last_processed_map_city:
            st.session_state.last_processed_map_city = current_map_city
            
            # Only update the widget if we have a valid city selection
            if current_map_city is not None:
                st.session_state.city_filter_widget = [current_map_city]
                st.rerun()

    # Sidebar Filters

    with st.sidebar:
        st.header("Filtros")
        
        # --- Dynamic Filters ---
        # Filters are applied sequentially to narrow down options
        
        # 1. City Filter (Top Level)
        cities = sorted(df["ciudad"].dropna().unique())
        if "city_filter_widget" not in st.session_state:
            st.session_state.city_filter_widget = cities
            
        selected_cities = st.multiselect("Seleccionar Ciudad", cities, key="city_filter_widget")
        
        # Filter data for next steps
        df_filtered_context = df.copy()
        if selected_cities:
            df_filtered_context = df_filtered_context[df_filtered_context["ciudad"].isin(selected_cities)]

        # 2. Category Filter
        if 'categoria' in df.columns:
            # Show only categories available in selected cities
            categorias = sorted(df_filtered_context["categoria"].dropna().unique())
            selected_categorias = st.multiselect("Seleccionar Categoría", categorias, default=categorias)
            if selected_categorias:
                df_filtered_context = df_filtered_context[df_filtered_context["categoria"].isin(selected_categorias)]
        else:
            selected_categorias = None
            
        # 3. Convocatoria Filter
        if 'convocatoria' in df.columns:
            convocatorias = sorted(df_filtered_context["convocatoria"].dropna().unique())
            selected_convocatoria = st.multiselect("Seleccionar Convocatoria", convocatorias, default=convocatorias)
            if selected_convocatoria:
                 df_filtered_context = df_filtered_context[df_filtered_context["convocatoria"].isin(selected_convocatoria)]
        else:
            selected_convocatoria = None

        # 4. Ficha (Proceso) Filter
        if 'proceso' in df.columns:
            procesos = sorted(df_filtered_context["proceso"].dropna().unique())
            selected_procesos = st.multiselect("Filtrar por Ficha", procesos, default=procesos)
            if selected_procesos:
                df_filtered_context = df_filtered_context[df_filtered_context["proceso"].isin(selected_procesos)]
        else:
            selected_procesos = None
            
        # 5. Study Filter
        if 'estudios_parsed' in df.columns:
            # Flatten list of lists to get unique values from the CURRENT filtered context
            current_nbcs = sorted(list(set([item for sublist in df_filtered_context['estudios_parsed'] for item in sublist])))
            selected_estudios = st.multiselect("Filtrar por Estudio", current_nbcs)
        else:
            selected_estudios = None
        
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

        # Diagnostic Section
        with st.expander("🛠️ Diagnóstico de Conexión IA"):
            st.write(f"Versión de librería: {genai.__version__}")
            if st.button("Listar Modelos Disponibles"):
                try:
                    models = list(genai.list_models())
                    model_names = [m.name for m in models]
                    st.write("Modelos encontrados:", model_names)
                except Exception as e:
                    st.error(f"Error listando modelos: {e}")

    # Apply Filters
    filtered_df = df[
        (df["ciudad"].isin(selected_cities)) &
        (df["salario"] >= selected_salary[0]) &
        (df["salario"] <= selected_salary[1])
    ]
    
    # Apply category filter if available
    if selected_categorias is not None and 'categoria' in df.columns:
        filtered_df = filtered_df[filtered_df["categoria"].isin(selected_categorias)]

    # Apply convocatoria filter if available
    if selected_convocatoria is not None and 'convocatoria' in df.columns:
        filtered_df = filtered_df[filtered_df["convocatoria"].isin(selected_convocatoria)]

    # Apply process filter if available
    if selected_procesos is not None and 'proceso' in df.columns:
        filtered_df = filtered_df[filtered_df["proceso"].isin(selected_procesos)]
        
    # Apply Study filter if available
    if selected_estudios and 'estudios_parsed' in df.columns:
        # Check if any selected study is in the row's list of studies
        filtered_df = filtered_df[filtered_df['estudios_parsed'].apply(lambda x: any(s in selected_estudios for s in x))]

    # Create a separate dataframe for the map that ignores the city filter
    # This allows the map to show all cities matching other filters, so users can select them
    map_df = df.copy()
    
    # Apply Salary Filter to map_df
    map_df = map_df[
        (map_df["salario"] >= selected_salary[0]) &
        (map_df["salario"] <= selected_salary[1])
    ]
    
    # Apply Category Filter to map_df
    if selected_categorias is not None and 'categoria' in map_df.columns:
        map_df = map_df[map_df["categoria"].isin(selected_categorias)]
        
    # Apply Convocatoria Filter to map_df
    if selected_convocatoria is not None and 'convocatoria' in map_df.columns:
        map_df = map_df[map_df["convocatoria"].isin(selected_convocatoria)]

    # Apply Process Filter to map_df
    # Apply Process Filter to map_df
    if selected_procesos is not None and 'proceso' in map_df.columns:
        map_df = map_df[map_df["proceso"].isin(selected_procesos)]
        
    # Apply Study filter to map_df
    if selected_estudios and 'estudios_parsed' in map_df.columns:
        map_df = map_df[map_df['estudios_parsed'].apply(lambda x: any(s in selected_estudios for s in x))]

    # Main Content
    
    # AI-Generated Summary
    if gemini_enabled:
        with st.expander("📊 Resumen Generado por IA", expanded=True):
            if st.button("🔄 Generar Resumen con Gemini", use_container_width=True):
                with st.spinner("Generando análisis con IA..."):
                    summary = generate_data_summary(filtered_df)
                    if summary:
                        st.markdown(summary)
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Use unique OPEC for total jobs since we exploded the dataframe
        total_empleos = filtered_df['opec'].nunique() if 'opec' in filtered_df.columns else len(filtered_df)
        st.metric("Total de Empleos (OPEC)", total_empleos)
    
    with col2:
        total_vacantes = filtered_df['vacantes_count'].sum() if 'vacantes_count' in filtered_df.columns else 0
        st.metric("Total de Vacantes", int(total_vacantes))
    
    with col3:
        ciudades_unicas = filtered_df['ciudad'].nunique() if 'ciudad' in filtered_df.columns else 0
        st.metric("Ciudades", ciudades_unicas)
    
    with col4:
        # Calculate average salary based on unique jobs to avoid weighting by number of cities
        salario_promedio = 0
        if 'salario' in filtered_df.columns:
            if 'opec' in filtered_df.columns:
                salario_promedio = filtered_df.drop_duplicates('opec')['salario'].mean()
            else:
                salario_promedio = filtered_df['salario'].mean()
        
        st.metric("Salario Promedio", f"${salario_promedio:,.0f}")
    
    # Map
    st.subheader("Mapa de Vacantes")
    # Ensure lat/lon columns exist and are numeric
    map_cols = ["latitud", "longitud"]
    if all(col in map_df.columns for col in map_cols):
        # Drop rows with NaN in lat/lon for the map
        map_data = map_df.dropna(subset=map_cols)
        
        if not map_data.empty:
            # Group by coordinates to count vacancies per location
            map_data_grouped = map_data.groupby(['latitud', 'longitud', 'ciudad'])['vacantes_count'].sum().reset_index()
            
            # Rename columns to match Plotly's expected names
            map_data_grouped = map_data_grouped.rename(columns={
                'latitud': 'lat',
                'longitud': 'lon',
                'vacantes_count': 'vacantes'
            })
            
            # Create interactive map with Plotly
            fig = px.scatter_mapbox(
                map_data_grouped,
                lat='lat',
                lon='lon',
                size='vacantes',
                color='vacantes',
                hover_name='ciudad',
                hover_data={'lat': False, 'lon': False, 'vacantes': True},
                color_continuous_scale='Viridis',
                size_max=30,
                zoom=5,
                center={'lat': 4.5709, 'lon': -74.2973},  # Centro de Colombia
                mapbox_style='open-street-map',
                title='Haz clic en una ciudad para filtrar'
            )
            
            fig.update_layout(
                height=500,
                margin={"r": 0, "t": 40, "l": 0, "b": 0}
            )
            
            # Display the map
            selected_points = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key="map_selection")
            
            st.caption(f"Mostrando {len(map_data_grouped)} ubicaciones en el mapa. Haz clic en un punto para filtrar por esa ciudad.")
            
            # Handle map selection
            if selected_points and 'selection' in selected_points and 'points' in selected_points['selection']:
                points = selected_points['selection']['points']
                if points:
                    # Get the selected city from the clicked point
                    selected_city = points[0]['hovertext']
                    st.info(f"Ciudad seleccionada en mapa: {selected_city}")
                    # The actual filtering happens at the top of the script on the next rerun
        else:
            st.info("No hay datos de ubicación válidos para mostrar en el mapa.")
    else:
        st.warning("El conjunto de datos no contiene columnas de 'latitud' y 'longitud'.")

    # Bar Chart
    st.subheader("Empleos por Cargo")
    
    # Initialize bar selection state if not present
    if "bar_selection_cargo" not in st.session_state:
        st.session_state.bar_selection_cargo = None

    if not filtered_df.empty:
        # Prepare data for Plotly
        jobs_by_cargo = filtered_df["cargo"].value_counts().head(20).reset_index()
        jobs_by_cargo.columns = ["cargo", "count"]
        
        # Create interactive bar chart
        fig_bar = px.bar(
            jobs_by_cargo, 
            x="cargo", 
            y="count",
            labels={"cargo": "Cargo", "count": "Cantidad de Vacantes"},
            color="count",
            color_continuous_scale='Viridis'
        )
        
        # Update layout for better UX
        fig_bar.update_layout(
            clickmode='event+select',
            xaxis_tickangle=-45,
            margin=dict(b=100) # Give space for labels
        )
        
        # Display chart with selection enabled
        selected_bar = st.plotly_chart(fig_bar, use_container_width=True, on_select="rerun", key="bar_selection")
        
        # Handle selection
        if selected_bar and "selection" in selected_bar and "points" in selected_bar["selection"]:
            points = selected_bar["selection"]["points"]
            if points:
                # Get selected cargo
                selected_cargo = points[0]["x"]
                st.session_state.bar_selection_cargo = selected_cargo
                st.info(f"Filtrando por cargo: {selected_cargo}")
            else:
                # Deselection
                st.session_state.bar_selection_cargo = None
        else:
            # Also handle case where selection is cleared via UI interaction that returns empty selection
            st.session_state.bar_selection_cargo = None

    else:
        st.info("No hay datos para mostrar con los filtros seleccionados.")

    # Apply Bar Chart Filter to the main dataframe for the table view
    if st.session_state.bar_selection_cargo:
        filtered_df = filtered_df[filtered_df["cargo"] == st.session_state.bar_selection_cargo]

    # Dataframe
    st.subheader("Detalle de Empleos")
    
    # Prepare dataframe for display
    display_df = filtered_df.copy()
    
    # Rename columns
    display_df = display_df.rename(columns={
        'vacantes_count': 'Vacantes Ciudad Seleccionada',
        'cargo': 'Cargo',
        'salario': 'Salario',
        'ciudad': 'Ciudad',
        'categoria': 'Categoría',
        'convocatoria': 'Convocatoria',
        'opec': 'OPEC',
        'estudio': 'Estudio',
        'experiencia': 'Experiencia',
        'Cantidad de Vacantes': 'Numero de vacantes del proceso',
        'cantidad de vacantes': 'Numero de vacantes del proceso',
        'proceso': 'Ficha',
        'Proceso': 'Ficha',
        'descripcion': 'Descripción',
        'Descripción': 'Descripción'
    })
    
    # Drop unnecessary columns
    # User requested to hide 'proceso' from the table but keep 'estudio' and 'experiencia'
    cols_to_drop = ['latitud', 'longitud', 'ciudad_raw', 'Grado', 'Código Empleo', 'Codigo Empleo', 'codigo_empleo', 'Nivel', 'vacantes_raw', 'estudios_parsed']
    # Drop columns case-insensitive
    for col in display_df.columns:
        if any(drop_col.lower() == col.lower() for drop_col in cols_to_drop):
            display_df = display_df.drop(columns=[col])
            
    st.dataframe(display_df, use_container_width=True)

else:
    st.info("No hay datos disponibles o no se pudo conectar a la base de datos.")
