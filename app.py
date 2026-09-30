import streamlit as st
import pandas as pd
import datetime

# Page configuration
st.set_page_config(
    page_title="Casa de Fe Mérida - Portal de Escuelas",
    page_icon="⛪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .card {
        background-color: #F3F4F6;
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 5px solid #1E3A8A;
        margin-bottom: 1rem;
    }
    .stMetric {
        background-color: #FFFFFF;
        padding: 0.8rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATA INITIALIZATION (Session State / Local / GSheets ready)
# ---------------------------------------------------------
@st.cache_data
def load_initial_data():
    # Base data prepared from Casa de Fe Mérida records
    data = [
        {"No_Control": 1, "Nombre": "Abraham yañez", "Maestro": "Perla", "Modulo": "ESENCIA G8", "Modalidad": "ONLINE", "Red": "Matrimonios", "Celular": "9993616494", "Encuentro": "Sí", "12_Pasos": "En curso", "Liberacion": "No", "Esencia_B1": "Sí", "Esencia_B2": "En curso", "Esencia_B3": "No", "Lanz": "No"},
        {"No_Control": 2, "Nombre": "Adiel Caamal", "Maestro": "Perla", "Modulo": "12 PASOS", "Modalidad": "PRESENCIAL", "Red": "Jóvenes", "Celular": "9994859100", "Encuentro": "Sí", "12_Pasos": "En curso", "Liberacion": "Sí", "Esencia_B1": "No", "Esencia_B2": "No", "Esencia_B3": "No", "Lanz": "No"},
        {"No_Control": 3, "Nombre": "Ana Pech", "Maestro": "Sin Asignar", "Modulo": "Sin Asignar", "Modalidad": "PRESENCIAL", "Red": "Matrimonios", "Celular": "9992630938", "Encuentro": "No", "12_Pasos": "No", "Liberacion": "No", "Esencia_B1": "No", "Esencia_B2": "No", "Esencia_B3": "No", "Lanz": "No"},
        {"No_Control": 4, "Nombre": "Brenda Hiselle Osorio Martinez", "Maestro": "Pastora", "Modulo": "ESENCIA G9", "Modalidad": "ONLINE", "Red": "Matrimonios", "Celular": "9933043710", "Encuentro": "Sí", "12_Pasos": "Sí", "Liberacion": "Sí", "Esencia_B1": "Sí", "Esencia_B2": "Sí", "Esencia_B3": "En curso", "Lanz": "No"},
        {"No_Control": 5, "Nombre": "Carlos Omar Gavira Juarez", "Maestro": "Pastor", "Modulo": "12 PASOS", "Modalidad": "ONLINE", "Red": "Matrimonios", "Celular": "9616378652", "Encuentro": "Sí", "12_Pasos": "En curso", "Liberacion": "Sí", "Esencia_B1": "No", "Esencia_B2": "No", "Esencia_B3": "No", "Lanz": "No"},
        {"No_Control": 6, "Nombre": "Claudia Dzul", "Maestro": "Perla", "Modulo": "12 PASOS", "Modalidad": "PRESENCIAL", "Red": "Matrimonios", "Celular": "9997497652", "Encuentro": "Sí", "12_Pasos": "En curso", "Liberacion": "No", "Esencia_B1": "No", "Esencia_B2": "No", "Esencia_B3": "No", "Lanz": "No"},
        {"No_Control": 7, "Nombre": "Claudia Lucia Mariscal Vazquez", "Maestro": "Perla", "Modulo": "ESENCIA G8", "Modalidad": "ONLINE", "Red": "Jóvenes", "Celular": "9933251394", "Encuentro": "Sí", "12_Pasos": "Sí", "Liberacion": "Sí", "Esencia_B1": "Sí", "Esencia_B2": "En curso", "Esencia_B3": "No", "Lanz": "No"},
        {"No_Control": 8, "Nombre": "Corina Galeana Navarrete", "Maestro": "Pastora", "Modulo": "ESENCIA G9", "Modalidad": "ONLINE", "Red": "Matrimonios", "Celular": "9993398482", "Encuentro": "Sí", "12_Pasos": "Sí", "Liberacion": "Sí", "Esencia_B1": "Sí", "Esencia_B2": "Sí", "Esencia_B3": "En curso", "Lanz": "No"},
        {"No_Control": 9, "Nombre": "Cristina Franco", "Maestro": "Perla", "Modulo": "12 PASOS", "Modalidad": "PRESENCIAL", "Red": "Matrimonios", "Celular": "9992734336", "Encuentro": "Sí", "12_Pasos": "En curso", "Liberacion": "Sí", "Esencia_B1": "No", "Esencia_B2": "No", "Esencia_B3": "No", "Lanz": "No"},
        {"No_Control": 10, "Nombre": "Delta Noemi Ruz Dominguez", "Maestro": "Perla", "Modulo": "12 PASOS", "Modalidad": "PRESENCIAL", "Red": "Matrimonios", "Celular": "9992193059", "Encuentro": "Sí", "12_Pasos": "En curso", "Liberacion": "No", "Esencia_B1": "No", "Esencia_B2": "No", "Esencia_B3": "No", "Lanz": "No"},
        {"No_Control": 11, "Nombre": "Fernanda Peña", "Maestro": "Perla", "Modulo": "12 PASOS", "Modalidad": "PRESENCIAL", "Red": "Matrimonios", "Celular": "5611928734", "Encuentro": "Sí", "12_Pasos": "En curso", "Liberacion": "No", "Esencia_B1": "No", "Esencia_B2": "No", "Esencia_B3": "No", "Lanz": "No"},
        {"No_Control": 12, "Nombre": "Fernando Castillo Gomez", "Maestro": "Pastor", "Modulo": "12 PASOS", "Modalidad": "ONLINE", "Red": "Jóvenes", "Celular": "9381376589", "Encuentro": "Sí", "12_Pasos": "En curso", "Liberacion": "Sí", "Esencia_B1": "No", "Esencia_B2": "No", "Esencia_B3": "No", "Lanz": "No"},
        {"No_Control": 15, "Nombre": "Gregory Jaramillo Martinez", "Maestro": "Perla", "Modulo": "ESENCIA G8", "Modalidad": "ONLINE", "Red": "Matrimonios", "Celular": "9993249284", "Encuentro": "Sí", "12_Pasos": "Sí", "Liberacion": "Sí", "Esencia_B1": "Sí", "Esencia_B2": "En curso", "Esencia_B3": "No", "Lanz": "No"},
        {"No_Control": 18, "Nombre": "Jhazeel Andrea Jiménez Medina", "Maestro": "Reina", "Modulo": "ESENCIA G10", "Modalidad": "PRESENCIAL", "Red": "Jóvenes", "Celular": "9993655426", "Encuentro": "Sí", "12_Pasos": "Sí", "Liberacion": "Sí", "Esencia_B1": "Sí", "Esencia_B2": "Sí", "Esencia_B3": "En curso", "Lanz": "No"},
        {"No_Control": 25, "Nombre": "Marcela Juarez", "Maestro": "Pastor", "Modulo": "12 PASOS", "Modalidad": "ONLINE", "Red": "Matrimonios", "Celular": "5537229785", "Encuentro": "Sí", "12_Pasos": "En curso", "Liberacion": "Sí", "Esencia_B1": "No", "Esencia_B2": "No", "Esencia_B3": "No", "Lanz": "No"},
        {"No_Control": 26, "Nombre": "Marco Antonio Castillo Escudero", "Maestro": "Pastor", "Modulo": "12 PASOS", "Modalidad": "ONLINE", "Red": "Matrimonios", "Celular": "9383851762", "Encuentro": "Sí", "12_Pasos": "En curso", "Liberacion": "Sí", "Esencia_B1": "No", "Esencia_B2": "No", "Esencia_B3": "No", "Lanz": "No"},
        {"No_Control": 31, "Nombre": "Sahily Yañez Galeana", "Maestro": "Reina", "Modulo": "ESENCIA G10", "Modalidad": "PRESENCIAL", "Red": "Prejuveniles", "Celular": "4271193870", "Encuentro": "Sí", "12_Pasos": "Sí", "Liberacion": "Sí", "Esencia_B1": "Sí", "Esencia_B2": "Sí", "Esencia_B3": "En curso", "Lanz": "No"},
        {"No_Control": 36, "Nombre": "Zaid Emilio Rivera Torres", "Maestro": "Reina", "Modulo": "ESENCIA G10", "Modalidad": "PRESENCIAL", "Red": "Jóvenes", "Celular": "9933912465", "Encuentro": "Sí", "12_Pasos": "Sí", "Liberacion": "Sí", "Esencia_B1": "Sí", "Esencia_B2": "Sí", "Esencia_B3": "En curso", "Lanz": "No"}
    ]
    return pd.DataFrame(data)

if "df_alumnos" not in st.session_state:
    st.session_state.df_alumnos = load_initial_data()

if "df_asistencia" not in st.session_state:
    st.session_state.df_asistencia = pd.DataFrame(columns=[
        "Fecha", "Maestro", "Modulo", "Alumno", "Asistencia", "Observaciones"
    ])

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/color/96/church.png", width=70)
st.sidebar.title("Casa de Fe Mérida")
st.sidebar.caption("Portal de Gestión Escolar")

opcion_menu = st.sidebar.radio(
    "Navegación Principal",
    ["📝 Pase de Lista (Maestros)", "👤 Expediente del Alumno", "📊 Dashboard y Métricas", "📜 Historial de Asistencia", "⚙️ Configuración Nube"]
)

# ---------------------------------------------------------
# MÓDULO 1: PASE DE LISTA INTERACTIVO PARA MAESTROS
# ---------------------------------------------------------
if opcion_menu == "📝 Pase de Lista (Maestros)":
    st.markdown('<div class="main-header">📝 Toma de Asistencia Dominical</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Selecciona tu grupo, marca la asistencia de tus alumnos y guarda el registro directamente en el expediente.</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        maestro_sel = st.selectbox("Selecciona tu nombre (Maestro/Líder):", ["Pastor", "Pastora", "Perla", "Reina"])
    
    # Filter modules by teacher
    modulos_maestro = st.session_state.df_alumnos[st.session_state.df_alumnos["Maestro"] == maestro_sel]["Modulo"].unique()
    with col2:
        modulo_sel = st.selectbox("Módulo / Clase:", modulos_maestro if len(modulos_maestro) > 0 else ["12 PASOS"])
    
    with col3:
        fecha_sel = st.date_input("Fecha de la Clase:", datetime.date.today())

    st.markdown("---")
    
    # Filter students for selected teacher and module
    alumnos_grupo = st.session_state.df_alumnos[
        (st.session_state.df_alumnos["Maestro"] == maestro_sel) & 
        (st.session_state.df_alumnos["Modulo"] == modulo_sel)
    ].copy()

    if len(alumnos_grupo) == 0:
        st.warning("No se encontraron alumnos asignados a este maestro y módulo.")
    else:
        st.subheader(f"Lista de Alumnos - {maestro_sel} ({modulo_sel})")
        st.info("💡 Marca la casilla para registrar **Presente**. Desmárcala para **Ausente**.")

        # Interactive attendance dataframe editor
        df_editor = pd.DataFrame({
            "No_Control": alumnos_grupo["No_Control"].values,
            "Alumno": alumnos_grupo["Nombre"].values,
            "Red": alumnos_grupo["Red"].values,
            "Modalidad": alumnos_grupo["Modalidad"].values,
            "Asistencia": [True] * len(alumnos_grupo),
            "Observaciones": [""] * len(alumnos_grupo)
        })

        edited_df = st.data_editor(
            df_editor,
            column_config={
                "Asistencia": st.column_config.CheckboxColumn("Presente", default=True),
                "Observaciones": st.column_config.TextColumn("Notas / Motivo de falta", width="medium"),
                "No_Control": st.column_config.NumberColumn("ID", disabled=True),
                "Alumno": st.column_config.TextColumn("Nombre completo", disabled=True)
            },
            disabled=["No_Control", "Alumno", "Red", "Modalidad"],
            hide_index=True,
            use_container_width=True
        )

        if st.button("💾 Guardar Asistencia de Hoy", type="primary"):
            nuevos_registros = []
            for idx, row in edited_df.iterrows():
                nuevos_registros.append({
                    "Fecha": fecha_sel.strftime("%Y-%m-%d"),
                    "Maestro": maestro_sel,
                    "Modulo": modulo_sel,
                    "Alumno": row["Alumno"],
                    "Asistencia": "Presente" if row["Asistencia"] else "Ausente",
                    "Observaciones": row["Observaciones"]
                })
            
            df_nuevos = pd.DataFrame(nuevos_registros)
            st.session_state.df_asistencia = pd.concat([st.session_state.df_asistencia, df_nuevos], ignore_index=True)
            st.success(f"✅ Asistencia del {fecha_sel} guardada exitosamente para {len(edited_df)} alumnos!")
            st.balloons()

# ---------------------------------------------------------
# MÓDULO 2: EXPEDIENTE Y FICHA DEL ALUMNO (EDICIÓN DIRECTA)
# ---------------------------------------------------------
elif opcion_menu == "👤 Expediente del Alumno":
    st.markdown('<div class="main-header">👤 Expediente Digital del Participante</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Consulta la trayectoria espiritual de cada alumno y actualiza sus avances en tiempo real.</div>', unsafe_allow_html=True)

    alumno_sel_nombre = st.selectbox(
        "🔍 Buscar y Seleccionar Alumno:",
        st.session_state.df_alumnos["Nombre"].sort_values().tolist()
    )

    # Get student record
    alumno_data = st.session_state.df_alumnos[st.session_state.df_alumnos["Nombre"] == alumno_sel_nombre].iloc[0]

    # Student Card Layout
    st.markdown(f"""
    <div class="card">
        <h3>{alumno_data['Nombre']}</h3>
        <p><b>No. Control:</b> #{alumno_data['No_Control']} | <b>Red:</b> {alumno_data['Red']} | <b>Celular:</b> {alumno_data['Celular']}</p>
        <p><b>Maestro Asignado:</b> {alumno_data['Maestro']} | <b>Módulo Actual:</b> {alumno_data['Modulo']} ({alumno_data['Modalidad']})</p>
    </div>
    """, unsafe_allow_html=True)

    # Calculate spiritual progress
    hit_cols = ["Encuentro", "12_Pasos", "Liberacion", "Esencia_B1", "Esencia_B2", "Esencia_B3", "Lanz"]
    completados = sum(1 for c in hit_cols if alumno_data[c] in ["Sí", "Completado"])
    porcentaje_avance = int((completados / len(hit_cols)) * 100)

    st.subheader("Progreso en la Ruta Espiritual")
    st.progress(porcentaje_avance / 100)
    st.caption(f"Avance global: **{porcentaje_avance}%** ({completados} de {len(hit_cols)} niveles completados)")

    st.subheader("✏️ Actualizar Estatus de Niveles y Clases")
    st.info("Puedes modificar los niveles que el alumno va acreditando y presionar 'Actualizar Expediente'.")

    with st.form("form_expediente"):
        col1, col2, col3 = st.columns(3)
        opciones_estatus = ["No", "En curso", "Sí"]

        with col1:
            encuentro = st.selectbox("Encuentro:", opciones_estatus, index=opciones_estatus.index(alumno_data["Encuentro"]) if alumno_data["Encuentro"] in opciones_estatus else 0)
            pasos12 = st.selectbox("12 Pasos:", opciones_estatus, index=opciones_estatus.index(alumno_data["12_Pasos"]) if alumno_data["12_Pasos"] in opciones_estatus else 0)
            liberacion = st.selectbox("Liberación:", opciones_estatus, index=opciones_estatus.index(alumno_data["Liberacion"]) if alumno_data["Liberacion"] in opciones_estatus else 0)

        with col2:
            esencia1 = st.selectbox("Esencia Bloque 1:", opciones_estatus, index=opciones_estatus.index(alumno_data["Esencia_B1"]) if alumno_data["Esencia_B1"] in opciones_estatus else 0)
            esencia2 = st.selectbox("Esencia Bloque 2:", opciones_estatus, index=opciones_estatus.index(alumno_data["Esencia_B2"]) if alumno_data["Esencia_B2"] in opciones_estatus else 0)
            esencia3 = st.selectbox("Esencia Bloque 3:", opciones_estatus, index=opciones_estatus.index(alumno_data["Esencia_B3"]) if alumno_data["Esencia_B3"] in opciones_estatus else 0)

        with col3:
            lanzamiento = st.selectbox("Lanzamiento:", opciones_estatus, index=opciones_estatus.index(alumno_data["Lanz"]) if alumno_data["Lanz"] in opciones_estatus else 0)
            nuevo_maestro = st.text_input("Cambiar Maestro:", value=str(alumno_data["Maestro"]))
            nuevo_modulo = st.text_input("Cambiar Módulo:", value=str(alumno_data["Modulo"]))

        btn_guardar_expediente = st.form_submit_button("💾 Guardar Cambios en Expediente")

        if btn_guardar_expediente:
            idx_alumno = st.session_state.df_alumnos[st.session_state.df_alumnos["Nombre"] == alumno_sel_nombre].index[0]
            st.session_state.df_alumnos.at[idx_alumno, "Encuentro"] = encuentro
            st.session_state.df_alumnos.at[idx_alumno, "12_Pasos"] = pasos12
            st.session_state.df_alumnos.at[idx_alumno, "Liberacion"] = liberacion
            st.session_state.df_alumnos.at[idx_alumno, "Esencia_B1"] = esencia1
            st.session_state.df_alumnos.at[idx_alumno, "Esencia_B2"] = esencia2
            st.session_state.df_alumnos.at[idx_alumno, "Esencia_B3"] = esencia3
            st.session_state.df_alumnos.at[idx_alumno, "Lanz"] = lanzamiento
            st.session_state.df_alumnos.at[idx_alumno, "Maestro"] = nuevo_maestro
            st.session_state.df_alumnos.at[idx_alumno, "Modulo"] = nuevo_modulo

            st.success(f"✅ Expediente de {alumno_sel_nombre} actualizado correctamente.")
            st.rerun()

# ---------------------------------------------------------
# MÓDULO 3: DASHBOARD Y MÉTRICAS EJECUTIVAS
# ---------------------------------------------------------
elif opcion_menu == "📊 Dashboard y Métricas":
    st.markdown('<div class="main-header">📊 Dashboard de Escuelas Dominicales</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Métricas consolidadas de asistencia, distribución de alumnos y crecimiento por red.</div>', unsafe_allow_html=True)

    df_a = st.session_state.df_alumnos

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Alumnos Activos", len(df_a))
    c2.metric("En Modi. Presencial", len(df_a[df_a["Modalidad"] == "PRESENCIAL"]))
    c3.metric("En Modi. Online", len(df_a[df_a["Modalidad"] == "ONLINE"]))
    c4.metric("Clases Registradas", len(st.session_state.df_asistencia))

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Distribución por Red")
        red_counts = df_a["Red"].value_counts()
        st.bar_chart(red_counts)

    with col_right:
        st.subheader("Alumnos por Módulo")
        mod_counts = df_a["Modulo"].value_counts()
        st.bar_chart(mod_counts)

# ---------------------------------------------------------
# MÓDULO 4: HISTORIAL COMPLETO DE ASISTENCIAS
# ---------------------------------------------------------
elif opcion_menu == "📜 Historial de Asistencia":
    st.markdown('<div class="main-header">📜 Registro Histórico de Asistencias</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Consulta los pases de lista enviados por los maestros con opción a exportar a Excel.</div>', unsafe_allow_html=True)

    if len(st.session_state.df_asistencia) == 0:
        st.info("Aún no se han registrado pases de lista en esta sesión. Ve al módulo '📝 Pase de Lista' para realizar el primero.")
    else:
        st.dataframe(st.session_state.df_asistencia, use_container_width=True)
        
        # Download as CSV button
        csv_data = st.session_state.df_asistencia.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte de Asistencia (CSV)",
            data=csv_data,
            file_name=f"asistencia_cdf_merida_{datetime.date.today()}.csv",
            mime="text/csv"
        )

# ---------------------------------------------------------
# MÓDULO 5: CONFIGURACIÓN Y NUBE (GOOGLE SHEETS)
# ---------------------------------------------------------
elif opcion_menu == "⚙️ Configuración Nube":
    st.markdown('<div class="main-header">⚙️ Conexión con Google Sheets</div>', unsafe_allow_html=True)
    st.markdown("""
    Para que las asistencias y modificaciones del expediente queden **guardadas permanentemente en la nube** (Google Drive), puedes vincular esta aplicación con una hoja de **Google Sheets** usando la integración oficial `st-gsheets-connection`.

    #### 📋 Pasos para activar la persistencia en Google Drive:
    1. Crea un libro en **Google Sheets** llamado `CDF_Merida_BD`.
    2. En **Streamlit Cloud**, ve a *Settings -> Secrets* y pega tus credenciales de Google Service Account.
    3. Reemplaza `st.session_state` por `conn.read()` y `conn.update()` para sincronizar en tiempo real cada vez que un maestro pasa lista.
    """)
    st.success("La estructura actual ya está 100% optimizada para conectarse a Google Sheets sin modificar la interfaz.")
