
import streamlit as st
import pandas as pd
import datetime as dt
import hashlib
import re
import uuid

import requests

st.set_page_config(
    page_title="Casa de Fe Mérida - Escuelas",
    page_icon="⛪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main-header {font-size:2.1rem;color:#1E3A8A;font-weight:800;margin-bottom:.2rem}
.sub-header {font-size:1rem;color:#64748B;margin-bottom:1.2rem}
.card {background:#F8FAFC;border:1px solid #E2E8F0;border-left:5px solid #1E3A8A;
       padding:1rem;border-radius:12px;margin-bottom:1rem}
.small-muted {color:#64748B;font-size:.9rem}
</style>
""", unsafe_allow_html=True)

# =========================================================
# ESQUEMA DE BASE DE DATOS
# =========================================================
TABLES = {
    "Alumnos": [
        "No_Control","Nombre","Sexo","Fecha_Nacimiento","Celular","Email","Red",
        "Maestro","Modulo","Modalidad","Estado_Alumno","Fecha_Registro","Origen_Registro",
        "Encuentro","Pasos12","Liberacion","Esencia_B1","Esencia_B2","Esencia_B3",
        "Lanzamiento","Fechas_Eventos","Activo"
    ],
    "Asistencias": [
        "Timestamp","Fecha","Maestro","Modulo","No_Control","Alumno",
        "Asistencia","Observaciones","Capturado_Por"
    ],
    "Maestros": ["ID_Maestro","Nombre","Email","Red","Activo"],
    "Usuarios": [
        "Email","Nombre","Rol","Maestro","No_Control","PIN_Hash","Activo"
    ],
    "Cursos": ["Curso_ID","Nombre","Descripcion","Activo"],
    "Materiales": [
        "Material_ID","Curso_ID","Modulo","Titulo","Descripcion",
        "URL","Tipo","Fecha","Visible"
    ],
    "HistorialAcademico": [
        "Movimiento_ID","Timestamp","No_Control","Alumno","Tipo_Movimiento",
        "Estado_Anterior","Estado_Nuevo","Maestro_Anterior","Maestro_Nuevo",
        "Modulo_Anterior","Modulo_Nuevo","Modalidad_Anterior","Modalidad_Nueva",
        "Motivo","Observaciones","Usuario"
    ],
}

SEED_MAESTROS = [
    ["M001","Pastor","","Matrimonios","Sí"],
    ["M002","Pastora","","Matrimonios","Sí"],
    ["M003","Perla","","","Sí"],
    ["M004","Reina","","","Sí"],
]

SEED_CURSOS = [
    ["C001","12 PASOS","Programa de formación 12 Pasos","Sí"],
    ["C002","ESENCIA","Programa Esencia","Sí"],
]

# Base inicial mínima. Si ya tienes alumnos en Google Sheets, se conserva lo existente.
SEED_ALUMNOS = [
    {
        "No_Control":"1","Nombre":"Abraham yañez","Sexo":"Hombre","Fecha_Nacimiento":"",
        "Celular":"9993616494","Email":"","Red":"Matrimonios","Maestro":"Perla",
        "Modulo":"ESENCIA G8","Modalidad":"ONLINE","Estado_Alumno":"Activo",
        "Fecha_Registro":str(dt.date.today()),"Origen_Registro":"Carga inicial",
        "Encuentro":"Si","Pasos12":"Clase 1-6","Liberacion":"Listo",
        "Esencia_B1":"Clase 1-6","Esencia_B2":"Clase 1-6","Esencia_B3":"",
        "Lanzamiento":"Si","Fechas_Eventos":"","Activo":"Sí"
    }
]

# =========================================================
# UTILIDADES GENERALES
# =========================================================
def yes(v):
    return str(v).strip().lower() in {"sí","si","true","1","activo","yes"}

def normalize_email(v):
    return str(v or "").strip().lower()

def hash_pin(pin):
    return hashlib.sha256(str(pin).encode("utf-8")).hexdigest()

def check_pin(pin, hashed):
