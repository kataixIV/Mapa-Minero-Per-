# ==========================================================
# Mapa interactivo de faenas mineras de Perú (Aplicación Dash)
# Versión 2.6 con Logo de Empresa
# ==========================================================
# Autor: Kataix & GPT-5 (Versión mejorada por Gemini)
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


# --- PASO 1: Cargar y preparar los datos ---

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
        print("→ Coordenadas guardadas en 'minas_per_geocodificado.xlsx'.")

    df.dropna(subset=['Latitud', 'Longitud'], inplace=True)

    cols_necesarias = ["Nombre", "Empresa", "Región", "Mineral principal", "Minerales secundarios", "Tipo de yacimiento", "Link",
                       "Tipo Cliente"]
    for col in cols_necesarias:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('nan', 'No disponible')
        else:
            df[col] = "No disponible"
    return df


df_minas = cargar_y_geocodificar_datos()

# --- PASO 2: Construir la aplicación Dash ---

app = dash.Dash(__name__)
server = app.server

# Creamos el mapa base que se mostrará en la aplicación
fig = px.scatter_geo(
    df_minas,
    lat="Latitud",
    lon="Longitud",
    hover_name="Nombre",
    color="Tipo de yacimiento",
    custom_data=["Nombre"],
    title="🪨 Mapa interactivo de faenas mineras en Perú (Haz clic en un punto)",
    projection="natural earth"
)
fig.update_layout(
    geo=dict(
        scope='south america', center=dict(lat=-9.19, lon=-75.01), projection_scale=6,
        showland=True, landcolor="lightgray", showcountries=True, countrycolor="white"
    ),
    title_font=dict(size=20),
    margin={"r":0,"t":40,"l":0,"b":0},
    # --- NUEVO: Añadimos el LOGO y la marca de agua al mapa inicial ---
    images=[
        dict(
            source="https://www.maptek.com/images/core/Maptek_Logo_OpenGraph_360x200.png", # <-- REEMPLAZA ESTA URL CON LA DE TU LOGO
            xref="paper", yref="paper",
            x=0.02, y=0.1,  # Posición (x: izquierda, y: arriba de la marca de texto)
            sizex=0.2, sizey=0.2, # Tamaño de la imagen
            xanchor="left", yanchor="bottom"
        )
    ],
    annotations=[
        dict(
            text="Creado por Francisco Gonzalez - Maptek",
            align='left',
            showarrow=False,
            xref='paper',
            yref='paper',
            x=0.02,
            y=0.02,
            font=dict(size=12, color="green"),
            opacity=0.7
        )
    ]
)
fig.update_traces(marker=dict(size=8, line=dict(width=1, color="DarkSlateGrey")))


# Opciones para los menús desplegables
opciones_region = [{'label': i, 'value': i} for i in sorted(df_minas['Región'].unique())]
opciones_mineral = [{'label': i, 'value': i} for i in sorted(df_minas['Mineral principal'].unique())]
opciones_tipo_cliente = [{'label': i, 'value': i} for i in sorted(df_minas['Tipo Cliente'].unique())]

app.layout = html.Div(style={'display': 'flex', 'height': '100vh', 'fontFamily': 'Arial'}, children=[

    html.Div(style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'backgroundColor': '#f9f9f9'}, children=[

        html.Div(style={'padding': '20px', 'backgroundColor': 'white', 'borderBottom': '1px solid #ddd'}, children=[
            html.H2("🪨 Visualizador de Faenas Mineras en Perú", style={'margin': '0'}),
            html.P("Utiliza los filtros para explorar el mapa y haz clic en un punto para ver detalles.",
                   style={'margin': '5px 0 0'})
        ]),

        # Panel de control con filtros
        html.Div(style={'display': 'flex', 'gap': '20px', 'padding': '20px', 'backgroundColor': 'white',
                        'borderBottom': '1px solid #ddd'}, children=[
            dcc.Dropdown(
                id='filtro-region',
                options=opciones_region,
                placeholder="Filtrar por Región",
                style={'flex': '1'}
            ),
            dcc.Dropdown(
                id='filtro-mineral',
                options=opciones_mineral,
                placeholder="Filtrar por Mineral",
                style={'flex': '1'}
            ),
            dcc.Dropdown(
                id='filtro-tipo-cliente',
                options=opciones_tipo_cliente,
                placeholder="Filtrar por Tipo Cliente",
                style={'flex': '1'}
            ),
            dcc.Input(
                id='filtro-nombre',
                type='text',
                placeholder="Buscar por nombre...",
                style={'flex': '1', 'padding': '8px'}
            )
        ]),

        html.Div(style={'flex': '1', 'position': 'relative'}, children=[
            dcc.Graph(id='mapa-minas', figure=fig, style={'height': '100%'})
        ])
    ]),

    html.Div(
        id='info-mina-div',
        style={'width': '300px', 'padding': '20px', 'backgroundColor': 'white',
               'boxShadow': '-2px 0 5px rgba(0,0,0,0.1)', 'overflowY': 'auto'},
        children=[
            html.H4("Información de la Faena", style={'marginTop': '0'}),
            html.Hr(),
            html.P("Haz clic sobre cualquier punto en el mapa para ver los detalles aquí.")
        ]
    )
])


# --- PASO 3: Definir la interactividad ---

# Callback para actualizar el mapa con filtros
@app.callback(
    Output('mapa-minas', 'figure'),
    [Input('filtro-region', 'value'),
     Input('filtro-mineral', 'value'),
     Input('filtro-tipo-cliente', 'value'),
     Input('filtro-nombre', 'value')]
)
def update_map(region_seleccionada, mineral_seleccionado, cliente_seleccionado, nombre_buscado):
    dff = df_minas.copy()

    # Aplicar filtros
    if region_seleccionada:
        dff = dff[dff['Región'] == region_seleccionada]
    if mineral_seleccionado:
        dff = dff[dff['Mineral principal'] == mineral_seleccionado]
    if cliente_seleccionado:
        dff = dff[dff['Tipo Cliente'] == cliente_seleccionado]
    if nombre_buscado:
        dff = dff[dff['Nombre'].str.contains(nombre_buscado, case=False, na=False)]

    fig = px.scatter_geo(
        dff,
        lat="Latitud",
        lon="Longitud",
        hover_name="Nombre",
        color="Tipo de yacimiento",
        custom_data=["Nombre"],
        projection="natural earth"
    )

    fig.update_layout(
        geo=dict(
            scope='south america', center=dict(lat=-9.19, lon=-75.01), projection_scale=6,
            showland=True, landcolor="lightgray", showcountries=True, countrycolor="white"
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend_title_text='Tipo de Yacimiento',
        # --- NUEVO: Añadimos el LOGO también al mapa actualizado ---
        images=[
            dict(
                source="https://www.maptek.com/wp-content/uploads/2023/10/Maptek-logo-standard-colour-1.png", # <-- REEMPLAZA ESTA URL CON LA DE TU LOGO
                xref="paper", yref="paper",
                x=0.02, y=0.1,
                sizex=0.2, sizey=0.2,
                xanchor="left", yanchor="bottom"
            )
        ],
        annotations=[
            dict(
                text="Creado por Francisco Gonzalez - Maptek",
                align='left',
                showarrow=False,
                xref='paper',
                yref='paper',
                x=0.02,
                y=0.02,
                font=dict(size=12, color="green"),
                opacity=0.7
            )
        ]
    )
    fig.update_traces(marker=dict(size=8, line=dict(width=1, color="DarkSlateGrey")))

    return fig


# Callback para mostrar la información al hacer clic
@app.callback(
    Output('info-mina-div', 'children'),
    Input('mapa-minas', 'clickData')
)
def display_click_data(clickData):
    if clickData is None:
        return [
            html.H4("Información de la Faena", style={'marginTop': '0'}),
            html.Hr(),
            html.P("Haz clic sobre cualquier punto en el mapa para ver los detalles aquí.")
        ]

    nombre_mina = clickData['points'][0]['customdata'][0]
    mina_info = df_minas[df_minas['Nombre'] == nombre_mina].iloc[0]

    link = mina_info['Link']
    if link != "No disponible" and link.startswith('http'):
        link_componente = dcc.Link("Abrir enlace", href=link, target="_blank", style={'color': '#007BFF'})
    else:
        link_componente = html.Span("No disponible")

    return [
        html.H4(f"📍 {mina_info['Nombre']}", style={'marginTop': '0'}),
        html.Hr(),
        html.B("Empresa: "), html.Span(mina_info['Empresa']), html.Br(), html.Br(),
        html.B("Región: "), html.Span(mina_info['Región']), html.Br(), html.Br(),
        html.B("Tipo Cliente: "), html.Span(mina_info['Tipo Cliente']), html.Br(), html.Br(),
        html.B("Mineral Principal: "), html.Span(mina_info['Mineral principal']), html.Br(), html.Br(),
        html.B("Minerales Secundarios: "), html.Span(mina_info['Minerales secundarios']), html.Br(), html.Br(),
        html.B("Tipo de Yacimiento: "), html.Span(mina_info['Tipo de yacimiento']), html.Br(), html.Br(),
        html.B("Link: "), link_componente
    ]


# --- PASO 4: Ejecutar la aplicación ---

if __name__ == '__main__':
    app.run(debug=True)
