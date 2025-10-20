# ==========================================================
# Mapa interactivo de faenas mineras de Perú (Aplicación Dash)
# ==========================================================
# Autor: Kataix & GPT-5 (Versión final con Dash por Gemini)
# Librerías necesarias:
# pip install pandas plotly geopy openpyxl tqdm dash

import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from tqdm import tqdm
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import webbrowser

# --- PASO 1: Cargar y preparar los datos (igual que antes) ---

def cargar_y_geocodificar_datos():
    """Función para encapsular la carga y preparación de datos."""
    try:
        df = pd.read_excel("minas_peru_geocodificado.xlsx")
        print("→ Se cargó el archivo con coordenadas preexistentes.")
    except FileNotFoundError:
        print("→ No se encontró archivo geocodificado. Procediendo a obtener coordenadas...")
        try:
            ruta_excel = "minas_peru_completo_reordenado.xlsx"
            df = pd.read_excel(ruta_excel)
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo base en la ruta '{ruta_excel}'.")
            return None

        df["Ubicación"] = df["Nombre"].astype(str) + ", " + df["Región"].astype(str) + ", Perú"
        geolocator = Nominatim(user_agent="mapa_minas_peru_dash")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

        latitudes = []
        longitudes = []
        for loc in tqdm(df["Ubicación"], desc="Obteniendo coordenadas..."):
            try:
                location = geocode(loc)
                latitudes.append(location.latitude if location else np.nan)
                longitudes.append(location.longitude if location else np.nan)
            except Exception:
                latitudes.append(np.nan)
                longitudes.append(np.nan)

        df["Latitud"] = latitudes
        df["Longitud"] = longitudes
        df.to_excel("minas_peru_geocodificado.xlsx", index=False)
        print("→ Coordenadas guardadas en 'minas_peru_geocodificado.xlsx'.")

    df.dropna(subset=['Latitud', 'Longitud'], inplace=True)

    # Aseguramos que las columnas existan y sean de tipo string
    cols_necesarias = ["Nombre", "Empresa", "Región", "Mineral principal", "Tipo de yacimiento", "Link"]
    for col in cols_necesarias:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('nan', 'No disponible')
        else:
            df[col] = "No disponible"

    return df

df_minas = cargar_y_geocodificar_datos()

# Creamos el mapa base que se mostrará en la aplicación
fig = px.scatter_geo(
    df_minas,
    lat="Latitud",
    lon="Longitud",
    hover_name="Nombre",
    color="Tipo de yacimiento",
    custom_data=["Nombre"], # Pasamos el nombre para identificar el punto clickeado
    title="🪨 Mapa interactivo de faenas mineras en Perú (Haz clic en un punto)",
    projection="natural earth"
)
fig.update_layout(
    geo=dict(
        scope='south america', center=dict(lat=-9.19, lon=-75.01), projection_scale=6,
        showland=True, landcolor="lightgray", showcountries=True, countrycolor="white"
    ),
    title_font=dict(size=20),
    margin={"r":0,"t":40,"l":0,"b":0}
)
fig.update_traces(marker=dict(size=8, line=dict(width=1, color="DarkSlateGrey")))


# --- PASO 2: Construir la aplicación Dash ---

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(style={'display': 'flex', 'fontFamily': 'Arial'}, children=[
    # Columna para el mapa
    html.Div(className="map-container", style={'width': '70%', 'display': 'inline-block', 'verticalAlign': 'top'}, children=[
        dcc.Graph(id='mapa-minas', figure=fig, style={'height': '100vh'})
    ]),

    # Columna para la información persistente
    html.Div(className="info-container", id='info-mina-div', style={'width': '30%', 'padding': '20px', 'display': 'inline-block'}, children=[
        html.H3("Información de la Faena"),
        html.Hr(),
        html.P("Haz clic sobre cualquier punto en el mapa para ver los detalles aquí.")
    ])
])

# --- PASO 3: Definir la interactividad (la "magia" de Dash) ---

@app.callback(
    Output('info-mina-div', 'children'), # El output es el contenido del panel de información
    Input('mapa-minas', 'clickData')     # El input es el evento de clic en el mapa
)
def display_click_data(clickData):
    # Si no se ha hecho clic en ningún punto todavía
    if clickData is None:
        return [
            html.H3("Información de la Faena"),
            html.Hr(),
            html.P("Haz clic sobre cualquier punto en el mapa para ver los detalles aquí.")
        ]

    # Si se hizo clic, extraemos la información
    # Obtenemos el nombre de la mina desde `custom_data`
    nombre_mina = clickData['points'][0]['customdata'][0]

    # Buscamos la fila completa de esa mina en nuestro DataFrame
    mina_info = df_minas[df_minas['Nombre'] == nombre_mina].iloc[0]

    # Creamos el componente de link
    link = mina_info['Link']
    if link != "No disponible" and link.startswith('http'):
        link_componente = dcc.Link("Abrir enlace", href=link, target="_blank")
    else:
        link_componente = html.Span("No disponible")

    # Devolvemos el panel de información formateado
    return [
        html.H3(f"📍 {mina_info['Nombre']}"),
        html.Hr(),
        html.B("Empresa: "), html.Span(mina_info['Empresa']),
        html.Br(), html.Br(),
        html.B("Región: "), html.Span(mina_info['Región']),
        html.Br(), html.Br(),
        html.B("Mineral Principal: "), html.Span(mina_info['Mineral principal']),
        html.Br(), html.Br(),
        html.B("Tipo de Yacimiento: "), html.Span(mina_info['Tipo de yacimiento']),
        html.Br(), html.Br(),
        html.B("Link: "), link_componente
    ]


# --- PASO 4: Ejecutar la aplicación ---

if __name__ == '__main__':
    # Abrimos el navegador automáticamente
    webbrowser.open("http://127.0.0.1:8050/")
    app.run(debug=False)
