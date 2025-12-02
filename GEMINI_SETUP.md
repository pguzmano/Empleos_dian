# 🤖 Configuración de Gemini AI para Dashboard de Empleos DIAN

## ✅ Características Implementadas

Tu dashboard ahora incluye las siguientes funcionalidades de IA:

### 1. **Asistente de Chat Interactivo**
   - Ubicado en la barra lateral (sidebar)
   - Permite hacer preguntas sobre los datos de empleos
   - Ejemplos:
     - "¿Cuál es el cargo mejor pagado en Bogotá?"
     - "¿Cuántos empleos hay disponibles en Medellín?"
     - "¿Cuál es el rango salarial promedio?"

### 2. **Resumen Automático con IA**
   - Genera análisis ejecutivos de los datos filtrados
   - Identifica patrones geográficos y tendencias salariales
   - Muestra insights sobre distribución de cargos

## 🔑 Cómo Obtener tu API Key de Gemini

### Paso 1: Acceder a Google AI Studio
1. Ve a [https://aistudio.google.com](https://aistudio.google.com)
2. Inicia sesión con tu cuenta de Google (la que tiene Gemini Plus)

### Paso 2: Crear API Key
1. En la barra lateral izquierda, haz clic en **"Get API key"**
2. Haz clic en **"Create API key"**
3. Selecciona tu proyecto de Google Cloud (o crea uno nuevo)
4. Copia la API key generada

### Paso 3: Configurar en tu Proyecto
1. Abre el archivo `.env` en tu proyecto
2. Agrega la siguiente línea (reemplaza con tu API key real):
   ```
   GEMINI_API_KEY=tu_api_key_aqui
   ```
3. Guarda el archivo

## 📝 Ejemplo de Archivo .env Completo

```env
# Supabase Configuration
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_supabase_anon_key

# Google Gemini Configuration
GEMINI_API_KEY=AIzaSyD-XXXXXXXXXXXXXXXXXXXXXXXXXX
```

## 🚀 Cómo Usar el Asistente de IA

### Chat Interactivo
1. Abre tu dashboard de Streamlit
2. En la barra lateral, encontrarás la sección "🤖 Asistente IA"
3. Si está configurado correctamente, verás "✅ Gemini activado"
4. Escribe tu pregunta en el cuadro de texto
5. Haz clic en "Preguntar"
6. Espera la respuesta de la IA

### Resumen Automático
1. En la parte superior del dashboard principal
2. Verás una sección expandible "📊 Resumen Generado por IA"
3. Haz clic en "🔄 Generar Resumen con Gemini"
4. La IA analizará los datos filtrados y generará insights

## ⚠️ Solución de Problemas

### El asistente muestra "⚠️ Gemini no configurado"
- Verifica que agregaste `GEMINI_API_KEY` en tu archivo `.env`
- Asegúrate de que no dejaste el valor por defecto `tu_gemini_api_key_aqui`
- Reinicia el servidor de Streamlit después de modificar `.env`

### Error de autenticación
- Verifica que copiaste la API key completa
- Asegúrate de que tu cuenta de Google tenga acceso a Gemini
- Revisa que no haya espacios extra al inicio o final de la API key

### El análisis no funciona
- Verifica que tengas datos cargados en Supabase
- Asegúrate de tener conexión a internet
- Revisa los logs de la consola para errores específicos

## 💡 Consejos de Uso

1. **Preguntas específicas**: Formula preguntas claras y específicas para mejores resultados
2. **Filtros primero**: Aplica los filtros de ciudad y salario antes de generar el resumen con IA
3. **Límites de API**: Gemini tiene límites gratuitos, úsalo con moderación
4. **Privacidad**: La IA solo recibe resúmenes estadísticos, no datos personales individuales

## 📚 Recursos Adicionales

- [Documentación de Gemini AI](https://ai.google.dev/docs)
- [Google AI Studio](https://aistudio.google.com)
- [Límites y quotas de API](https://ai.google.dev/pricing)

## 🎯 Próximos Pasos

Puedes extender las funcionalidades de IA:
1. Agregar visualizaciones generadas por IA
2. Implementar recomendaciones personalizadas
3. Crear reportes automáticos en PDF
4. Análisis predictivo de tendencias
