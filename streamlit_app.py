import streamlit as st
import pandas as pd
from google.cloud import firestore
from google.oauth2 import service_account

import json

st.title("Netfilx app")

# Cache Firestore client
@st.cache_resource
def get_firestore_client():
    key_dict = json.loads(st.secrets["textkey"])
    creds = service_account.Credentials.from_service_account_info(key_dict)
    return firestore.Client(credentials=creds, project="proyecto-filmes")

# Cache Firestore data
@st.cache_data
def load_filmes_data():
  db = get_firestore_client() # Obtener el cliente cacheado
  collection_ref = db.collection('filmes') # Referencia hacia la colección de Filmes

  docs = list(collection_ref.stream()) # Leer documentos
  docs_dict = [doc.to_dict() for doc in docs] # Convertir a diccionario
  df = pd.DataFrame(docs_dict) #Convierte la lista en un diccionario de Python
  return df

# Load data
data_load_state = st.text('Cargando datos...')
data = load_filmes_data()
data_load_state.text('Done! (using st.cache)')


################################################################################
# SIDEBAR
################################################################################

# 1) ---Mostrar el dataframe completo con componente checkbox---
mostrar_df = st.sidebar.checkbox("Mostrar todos los filmes", value=False)

# 2) --- Búsqueda filme por título---
st.sidebar.subheader("Buscar filme por título")
titulo_busqueda = st.sidebar.text_input("Título del filme:")
boton_buscar = st.sidebar.button("Buscar filmes")

# 3) --- Selección de director ---
st.sidebar.subheader("Seleccionar director")
lista_directores = sorted(data["director"].dropna().unique()) # Obtener lista única de directores (limpia valores NaN)
director_seleccionado = st.sidebar.selectbox("Seleccionar Director:", options=lista_directores)
boton_filtrar_director = st.sidebar.button("Filtrar director")

# 4) --- Crear nuevo filme ---
st.sidebar.subheader("Crear nuevo filme")
lista_company = sorted(data["company"].dropna().unique())
lista_director = sorted(data["director"].dropna().unique())
lista_genre = sorted(data["genre"].dropna().unique())

with st.sidebar.form("form_nuevo_filme"):
    nuevo_name = st.text_input("Name")
    nuevo_company = st.selectbox("Company", lista_company)
    nuevo_director = st.selectbox("Director", lista_director)
    nuevo_genre = st.selectbox("Genre", lista_genre)

    boton_crear = st.form_submit_button("Crear nuevo filme")

    if boton_crear:
        if nuevo_name.strip() == "":
            st.warning("El campo Name no puede estar vacío.")
        else:
            try:
                db = get_firestore_client()
                db.collection("filmes").add({
                    "name": nuevo_name,
                    "company": nuevo_company,
                    "director": nuevo_director,
                    "genre": nuevo_genre
                })

                load_filmes_data.clear()
                data = load_filmes_data()

                st.success(f"Filme '{nuevo_name}' creado correctamente.")
            except Exception as e:
                st.error(f"Error al crear filme: {e}")

################################################################################
# Logica
################################################################################

# Solo se muestra el DataFrame si el usuario activa el checkbox
df_resultado = data.copy()

# 2) Búsqueda por título del filme--- ----------------------------------
if boton_buscar and titulo_busqueda.strip() != "":
    df_resultado = df_resultado[
        df_resultado["name"].str.contains(titulo_busqueda, case=False, na=False)
    ]
    st.subheader(f"Resultados de búsqueda para: '{titulo_busqueda}'")

# 3) Selección de director -----------------------------------
elif boton_filtrar_director:
    df_resultado = df_resultado[df_resultado["director"] == director_seleccionado]
    st.subheader(f"Filmes dirigidos por: {director_seleccionado}")

elif mostrar_df:
    st.subheader("Todos los filmes")

else:
    st.info("Usa el menú lateral para buscar, filtrar o crear filmes.")
    st.stop()

# Mostrar DataFrame (con o sin filtros)
st.dataframe(df_resultado)
