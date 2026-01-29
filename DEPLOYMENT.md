# 🚀 Guía de Despliegue en Streamlit Cloud

## Pasos para Desplegar la Aplicación

### 1. Preparar el Repositorio

El repositorio ya está configurado en GitHub:
- **URL**: https://github.com/pguzmano/Empleos_dian.git
- **Rama**: master

### 2. Acceder a Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Inicia sesión con tu cuenta de GitHub
3. Autoriza a Streamlit Cloud para acceder a tus repositorios

### 3. Crear Nueva Aplicación

1. Haz clic en **"New app"**
2. Selecciona:
   - **Repository**: `pguzmano/Empleos_dian`
   - **Branch**: `master`
   - **Main file path**: `streamlit_app.py`
3. Haz clic en **"Advanced settings"**

### 4. Configurar Secrets

En la sección de **Secrets**, copia y pega el siguiente contenido (reemplaza con tus credenciales reales):

```toml
# Configuración de credenciales de Supabase
SUPABASE_URL = "https://lzkerhnoypdfudipmjvm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx6a2VyaG5veXBkZnVkaXBtanZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQzNzYzMzgsImV4cCI6MjA3OTk1MjMzOH0.ExOon1XXisl15hOBXqTN_8iOxIM2kmlVKx83C3k2Ttc"

# Configuración de Gemini AI
GEMINI_API_KEY = "AIzaSyCJV_Are-gHFIowt_wtPXFrKiblgBAxWFs"
```

### 5. Desplegar

1. Haz clic en **"Deploy!"**
2. Espera a que Streamlit Cloud construya y despliegue tu aplicación
3. Una vez completado, recibirás una URL pública para tu aplicación

## 📝 Notas Importantes

- **Modo Offline**: La aplicación incluye un modo offline que carga datos desde `EmpleosDIAN_2025.xlsx` si Supabase no está disponible
- **Gemini AI**: Es opcional. Si no configuras `GEMINI_API_KEY`, la aplicación funcionará sin el asistente de IA
- **Actualizaciones**: Cada vez que hagas `git push` a la rama `master`, Streamlit Cloud actualizará automáticamente tu aplicación

## 🔧 Solución de Problemas

### Error: "Module not found"
- Verifica que `requirements.txt` esté actualizado
- Asegúrate de que todas las dependencias estén listadas

### Error: "Secrets not found"
- Verifica que hayas configurado los secrets en Streamlit Cloud
- Los nombres de las variables deben coincidir exactamente

### La aplicación no carga datos
- Verifica que `EmpleosDIAN_2025.xlsx` esté en el repositorio
- Revisa los logs en Streamlit Cloud para ver errores específicos

## 📊 Características de la Aplicación

- ✅ Mapa interactivo de vacantes por ciudad
- ✅ Gráficos de barras interactivos
- ✅ Filtros dinámicos (Ciudad, Categoría, Convocatoria, Ficha, Estudio, Salario)
- ✅ KPIs en tiempo real
- ✅ Asistente IA con Gemini (opcional)
- ✅ Modo offline con datos locales
- ✅ Tabla detallada con todos los datos

## 🌐 URL de la Aplicación

Una vez desplegada, tu aplicación estará disponible en:
`https://[tu-app-name].streamlit.app`

¡Disfruta de tu aplicación desplegada! 🎉
