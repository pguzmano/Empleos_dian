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
        st.error("⚠️ Falta configuración: Por favor configura SUPABASE_URL y SUPABASE_KEY en el archivo .env o .streamlit/secrets.toml")
        st.stop()
        
    return create_client(url, key)

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
            'convocatoria': 'convocatoria'
        }
        
        # Rename columns if they exist
        df_input = df_input.rename(columns=column_mapping)
        
        # Ensure we have the required columns
        if 'cargo' not in df_input.columns and 'Denominación' in df_input.columns:
             df_input['cargo'] = df_input['Denominación']
             
        if 'salario' not in df_input.columns and 'Asignación Salarial' in df_input.columns:
             df_input['salario'] = df_input['Asignación Salarial']

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
        response = supabase.table("Empleados Dian").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            return process_dataframe(df)
    except Exception as e:
        st.error(f"Error de conexión a Supabase: {str(e)}")
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
            categoria_col = get_col(['categoria', 'categor'])
            convocatoria_col = get_col(['convocatoria'])
            
            new_df = pd.DataFrame()
            if cargo_col: new_df['cargo'] = df[cargo_col]
            if salario_col: new_df['salario'] = df[salario_col]
            if ciudad_col: 
                new_df['ciudad_raw'] = df[ciudad_col]
            if categoria_col:
                new_df['categoria'] = df[categoria_col]
            if convocatoria_col:
                new_df['convocatoria'] = df[convocatoria_col]
            
            # Process the dataframe to extract city, vacancies and coords
            return process_dataframe(new_df)
            
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

        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

if not df.empty:
    # Handle Map Selection State
    # Check if a selection was made on the map (available in session state from previous run)
    if "map_selection" in st.session_state:
        selection = st.session_state.map_selection
        
        # Initialize last_map_selection if not present
        if "last_map_selection" not in st.session_state:
            st.session_state.last_map_selection = None

        # Check if the selection has changed
        if selection != st.session_state.last_map_selection:
            st.session_state.last_map_selection = selection
            
            if selection and "selection" in selection and "points" in selection["selection"]:
                points = selection["selection"]["points"]
                if points:
                    selected_city_from_map = points[0]["hovertext"]
                    # Update the city filter state
                    st.session_state.city_filter_widget = [selected_city_from_map]

    # Sidebar Filters

    with st.sidebar:
        st.header("Filtros")
        
        # City Filter
        cities = sorted(df["ciudad"].dropna().unique())
        # Initialize widget state if not present
        if "city_filter_widget" not in st.session_state:
            st.session_state.city_filter_widget = cities
            
        selected_cities = st.multiselect(
            "Seleccionar Ciudad", 
            cities, 
            key="city_filter_widget"
        )
        
        # Category Filter
        if 'categoria' in df.columns:
            categorias = sorted(df["categoria"].dropna().unique())
            selected_categorias = st.multiselect("Seleccionar Categoría", categorias, default=categorias)
        else:
            selected_categorias = None
            
        # Convocatoria Filter
        if 'convocatoria' in df.columns:
            convocatorias = sorted(df["convocatoria"].dropna().unique())
            selected_convocatoria = st.multiselect("Seleccionar Convocatoria", convocatorias, default=convocatorias)
        else:
            selected_convocatoria = None
        
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
    
    # Apply category filter if available
    if selected_categorias is not None and 'categoria' in df.columns:
        filtered_df = filtered_df[filtered_df["categoria"].isin(selected_categorias)]

    # Apply convocatoria filter if available
    if selected_convocatoria is not None and 'convocatoria' in df.columns:
        filtered_df = filtered_df[filtered_df["convocatoria"].isin(selected_convocatoria)]

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
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Use unique OPEC for total jobs since we exploded the dataframe
        total_empleos = filtered_df['opec'].nunique() if 'opec' in filtered_df.columns else len(filtered_df)
        st.metric("Total de Empleos (OPEC)", total_empleos)
    
    with col2:
        total_vacantes = filtered_df['vacantes_count'].sum() if 'vacantes_count' in filtered_df.columns else 0
        st.metric("Total de Vacantes", int(total_vacantes))
    
    with col3:
        ciudades_unicas = filtered_df['ciudad'].nunique()
        st.metric("Ciudades", ciudades_unicas)
    
    with col4:
        # Calculate average salary based on unique jobs to avoid weighting by number of cities
        if 'opec' in filtered_df.columns:
            salario_promedio = filtered_df.drop_duplicates('opec')['salario'].mean()
        else:
            salario_promedio = filtered_df['salario'].mean()
        st.metric("Salario Promedio", f"${salario_promedio:,.0f}")
    
    # Map
    st.subheader("Mapa de Vacantes")
    # Ensure lat/lon columns exist and are numeric
    map_cols = ["latitud", "longitud"]
    if all(col in filtered_df.columns for col in map_cols):
        # Drop rows with NaN in lat/lon for the map
        map_data = filtered_df.dropna(subset=map_cols)
        
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
    if not filtered_df.empty:
        jobs_by_cargo = filtered_df["cargo"].value_counts().head(20)
        st.bar_chart(jobs_by_cargo)
    else:
        st.info("No hay datos para mostrar con los filtros seleccionados.")

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
        'opec': 'OPEC'
    })
    
    # Drop unnecessary columns
    cols_to_drop = ['latitud', 'longitud', 'ciudad_raw', 'Grado', 'Código Empleo', 'Codigo Empleo', 'codigo_empleo', 'Nivel', 'Estudio', 'Experiencia']
    # Drop columns case-insensitive
    for col in display_df.columns:
        if any(drop_col.lower() == col.lower() for drop_col in cols_to_drop):
            display_df = display_df.drop(columns=[col])
            
    st.dataframe(display_df, use_container_width=True)

else:
    st.info("No hay datos disponibles o no se pudo conectar a la base de datos.")
