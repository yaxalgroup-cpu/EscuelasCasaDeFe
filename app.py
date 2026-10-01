
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
    return hash_pin(pin) == str(hashed)

def configured():
    return all(k in st.secrets for k in [
        "APPS_SCRIPT_URL", "API_SECRET", "ADMIN_EMAIL", "ADMIN_PIN"
    ])

@st.cache_resource(show_spinner=False)
def http_session():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

def api_call(action, table=None, rows=None, timeout=20):
    payload = {
        "secret": st.secrets["API_SECRET"],
        "action": action,
    }
    if table is not None:
        payload["table"] = table
    if rows is not None:
        payload["rows"] = rows

    response = http_session().post(
        st.secrets["APPS_SCRIPT_URL"],
        json=payload,
        timeout=timeout,
        allow_redirects=True,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("error", "Error de Apps Script"))
    return data

def _normalize_table(name, rows):
    if not rows:
        return pd.DataFrame(columns=TABLES[name])
    df = pd.DataFrame(rows)
    for c in TABLES[name]:
        if c not in df.columns:
            df[c] = ""
    return df[TABLES[name]].fillna("")

@st.cache_data(ttl=12, show_spinner=False)
def _read_table_cached(name):
    rows = api_call("read", table=name)["data"]["rows"]
    return _normalize_table(name, rows)

def read_table(name, fresh=False):
    if fresh:
        rows = api_call("read", table=name)["data"]["rows"]
        return _normalize_table(name, rows)
    # Copy avoids one user/session mutating the cached dataframe object.
    return _read_table_cached(name).copy()

def invalidate_data_cache():
    _read_table_cached.clear()

def write_table(name, df):
    headers = TABLES[name]
    clean = df.copy()
    for c in headers:
        if c not in clean.columns:
            clean[c] = ""
    clean = clean[headers].fillna("").astype(str)
    api_call("replace", table=name, rows=clean.to_dict("records"))
    invalidate_data_cache()

def append_rows(name, rows):
    if not rows:
        return
    headers = TABLES[name]
    prepared = []
    for row in rows:
        if isinstance(row, dict):
            prepared.append({h: str(row.get(h, "")) for h in headers})
        else:
            prepared.append({h: str(v) for h, v in zip(headers, row)})
    api_call("append", table=name, rows=prepared)
    invalidate_data_cache()

def next_student_id(df):
    if df.empty:
        return 1
    nums = pd.to_numeric(df["No_Control"], errors="coerce")
    return int(nums.max()) + 1 if nums.notna().any() else 1

def log_movement(before, after, movement_type, motivo="", observaciones="", usuario=""):
    row = [
        "MOV-" + uuid.uuid4().hex[:12].upper(),
        dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        str(after.get("No_Control","")),
        str(after.get("Nombre","")),
        movement_type,
        str(before.get("Estado_Alumno","")),
        str(after.get("Estado_Alumno","")),
        str(before.get("Maestro","")),
        str(after.get("Maestro","")),
        str(before.get("Modulo","")),
        str(after.get("Modulo","")),
        str(before.get("Modalidad","")),
        str(after.get("Modalidad","")),
        str(motivo),
        str(observaciones),
        str(usuario),
    ]
    append_rows("HistorialAcademico", [row])

@st.cache_resource(show_spinner=False)
def bootstrap():
    # The structure is checked once per Streamlit process instead of on every click.
    api_call("init")

    alumnos = read_table("Alumnos", fresh=True)
    if alumnos.empty:
        write_table("Alumnos", pd.DataFrame(SEED_ALUMNOS))

    maestros = read_table("Maestros", fresh=True)
    if maestros.empty:
        write_table("Maestros", pd.DataFrame(SEED_MAESTROS, columns=TABLES["Maestros"]))

    cursos = read_table("Cursos", fresh=True)
    if cursos.empty:
        write_table("Cursos", pd.DataFrame(SEED_CURSOS, columns=TABLES["Cursos"]))

    usuarios = read_table("Usuarios", fresh=True)
    admin_email = normalize_email(st.secrets["ADMIN_EMAIL"])
    if usuarios.empty or admin_email not in usuarios["Email"].astype(str).str.lower().tolist():
        usuarios = pd.concat([usuarios, pd.DataFrame([{
            "Email": admin_email,
            "Nombre": "Administrador",
            "Rol": "Administrador",
            "Maestro": "",
            "No_Control": "",
            "PIN_Hash": hash_pin(st.secrets["ADMIN_PIN"]),
            "Activo": "Sí",
        }])], ignore_index=True)
        write_table("Usuarios", usuarios)
    return True

def current_user():
    return st.session_state.get("user")

def user_roles(user=None):
    u = user or current_user()
    if not u:
        return []
    raw = str(u.get("Rol", "")).strip()
    roles = []
    for part in re.split(r"[,;/|]+", raw):
        role = part.strip()
        if role and role not in roles:
            roles.append(role)
    return roles

def active_role():
    roles = user_roles()
    selected = st.session_state.get("active_role")
    if selected in roles:
        return selected
    if "Administrador" in roles:
        return "Administrador"
    if "Maestro" in roles:
        return "Maestro"
    if roles:
        return roles[0]
    return ""

def is_admin():
    return active_role() == "Administrador"

def is_teacher():
    return active_role() == "Maestro"

def is_student():
    return active_role() == "Alumno"

def logout():
    st.session_state.pop("user", None)
    st.session_state.pop("active_role", None)
    st.rerun()

def safe_student_scope(df):
    """Aplica aislamiento de datos según el rol activo."""
    u = current_user()
    role = active_role()
    if not u:
        return df.iloc[0:0]

    if role in ["Administrador", "Consulta"]:
        return df

    if role == "Maestro":
        teacher = str(u.get("Maestro","")).strip()
        return df[df["Maestro"].astype(str) == teacher].copy()

    if role == "Alumno":
        control = str(u.get("No_Control","")).strip()
        return df[df["No_Control"].astype(str) == control].copy()

    return df.iloc[0:0]

# =========================================================
# REGISTRO PÚBLICO
# =========================================================
def public_registration_page():
    st.markdown('<div class="main-header">📝 Registro de Alumno</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Casa de Fe Mérida · Registro inicial para Escuelas</div>',
        unsafe_allow_html=True
    )
    st.info(
        "Tu registro ingresará automáticamente al sistema como **Pendiente de asignación**. "
        "Después la coordinación te asignará maestro, módulo y modalidad."
    )

    with st.form("public_registration"):
        nombre = st.text_input("Nombre completo *")
        c1, c2 = st.columns(2)
        celular = c1.text_input("Celular *")
        email = c2.text_input("Correo electrónico *")
        c3, c4 = st.columns(2)
        sexo = c3.selectbox("Sexo", ["","Hombre","Mujer","Prefiero no indicar"])
        fecha_nac = c4.date_input(
            "Fecha de nacimiento (opcional)",
            value=None,
            min_value=dt.date(1940,1,1),
            max_value=dt.date.today()
        )
        red = st.selectbox(
            "Red / grupo de referencia",
            ["","Matrimonios","Jóvenes","Prejuveniles","Otro"]
        )
        pin = st.text_input(
            "Crea un PIN de acceso (mínimo 6 caracteres) *",
            type="password",
            help="Después podrás entrar como alumno para consultar únicamente tu propia información."
        )
        observ = st.text_area("Comentario u observación (opcional)")
        acepta = st.checkbox(
            "Confirmo que los datos proporcionados son correctos y autorizo su uso "
            "para la gestión de las Escuelas Casa de Fe."
        )
        submit = st.form_submit_button("Enviar registro", type="primary")

    if submit:
        if not nombre.strip() or not celular.strip() or not email.strip():
            st.error("Nombre, celular y correo son obligatorios.")
            return
        if len(pin) < 6:
            st.error("El PIN debe tener al menos 6 caracteres.")
            return
        if not acepta:
            st.error("Debes confirmar la autorización para continuar.")
            return

        alumnos = read_table("Alumnos", fresh=True)
        usuarios = read_table("Usuarios", fresh=True)

        phone_norm = re.sub(r"\D","",celular)
        email_norm = normalize_email(email)

        dup_phone = alumnos["Celular"].astype(str).str.replace(r"\D","",regex=True) == phone_norm
        dup_email = alumnos["Email"].astype(str).str.lower().str.strip() == email_norm
        if (dup_phone | dup_email).any():
            st.warning(
                "Ya existe un registro con ese celular o correo. "
                "Comunícate con coordinación para evitar duplicados."
            )
            return

        if email_norm in usuarios["Email"].astype(str).str.lower().tolist():
            st.warning("Ese correo ya tiene acceso al sistema.")
            return

        nid = next_student_id(alumnos)
        student = {
            "No_Control": str(nid),
            "Nombre": nombre.strip(),
            "Sexo": sexo,
            "Fecha_Nacimiento": str(fecha_nac) if fecha_nac else "",
            "Celular": celular.strip(),
            "Email": email_norm,
            "Red": red,
            "Maestro": "",
            "Modulo": "",
            "Modalidad": "",
            "Estado_Alumno": "Pendiente de asignación",
            "Fecha_Registro": str(dt.date.today()),
            "Origen_Registro": "Registro público",
            "Encuentro": "No",
            "Pasos12": "",
            "Liberacion": "No",
            "Esencia_B1": "",
            "Esencia_B2": "",
            "Esencia_B3": "",
            "Lanzamiento": "No",
            "Fechas_Eventos": observ.strip(),
            "Activo": "Sí",
        }

        alumnos = pd.concat([alumnos, pd.DataFrame([student])], ignore_index=True)
        write_table("Alumnos", alumnos)

        usuarios = pd.concat([usuarios, pd.DataFrame([{
            "Email": email_norm,
            "Nombre": nombre.strip(),
            "Rol": "Alumno",
            "Maestro": "",
            "No_Control": str(nid),
            "PIN_Hash": hash_pin(pin),
            "Activo": "Sí",
        }])], ignore_index=True)
        write_table("Usuarios", usuarios)

        log_movement(
            {}, student, "Registro público",
            motivo="Alta inicial",
            observaciones=observ.strip(),
            usuario=email_norm
        )

        st.success(
            f"✅ Registro recibido. Tu número de control es **{nid}**. "
            "Ya puedes entrar al portal con tu correo y PIN."
        )
        st.caption(
            "Mientras coordinación realiza la asignación, tu portal mostrará únicamente "
            "tu estado como Pendiente de asignación."
        )

# =========================================================
# CONFIGURACIÓN / INICIALIZACIÓN
# =========================================================
st.sidebar.image("https://img.icons8.com/color/96/church.png", width=64)
st.sidebar.title("Casa de Fe Mérida")
st.sidebar.caption("Portal de Gestión Escolar")

if not configured():
    st.error("⚙️ Falta configurar la conexión con Google Apps Script en Streamlit Secrets.")
    st.markdown("""
En **Streamlit → App → Settings → Secrets** agrega:

```toml
APPS_SCRIPT_URL = "TU_URL_TERMINADA_EN_/exec"
API_SECRET = "LA_MISMA_CLAVE_PRIVADA_DEL_APPS_SCRIPT"
ADMIN_EMAIL = "tu-correo@ejemplo.com"
ADMIN_PIN = "un-pin-inicial-seguro"
```
""")
    st.stop()

try:
    bootstrap()
except Exception as e:
    st.error("No pude conectarme a Google Sheets mediante Apps Script.")
    st.exception(e)
    st.stop()

# Link público: https://TU-APP.streamlit.app/?registro=1
if str(st.query_params.get("registro","")) == "1":
    public_registration_page()
    st.stop()

# =========================================================
# LOGIN
# =========================================================
if "user" not in st.session_state:
    st.markdown('<div class="main-header">⛪ Casa de Fe Mérida</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Portal de Escuelas</div>', unsafe_allow_html=True)

    with st.form("login"):
        email = st.text_input("Correo electrónico")
        pin = st.text_input("PIN", type="password")
        btn = st.form_submit_button("Ingresar", type="primary")

    if btn:
        usuarios = read_table("Usuarios", fresh=True)
        usuarios["Email_norm"] = usuarios["Email"].astype(str).str.lower().str.strip()
        hit = usuarios[usuarios["Email_norm"] == normalize_email(email)]
        if hit.empty:
            st.error("Usuario no autorizado.")
        else:
            row = hit.iloc[0].to_dict()
            if not yes(row.get("Activo")):
                st.error("Este usuario está desactivado.")
            elif check_pin(pin, row.get("PIN_Hash")):
                row.pop("Email_norm", None)
                st.session_state.user = row
                roles = user_roles(row)
                if "Administrador" in roles:
                    st.session_state.active_role = "Administrador"
                elif "Maestro" in roles:
                    st.session_state.active_role = "Maestro"
                elif roles:
                    st.session_state.active_role = roles[0]
                st.rerun()
            else:
                st.error("PIN incorrecto.")
    st.caption("Los alumnos nuevos deben usar el enlace de registro proporcionado por coordinación.")
    st.stop()

user = current_user()
roles = user_roles(user)
if len(roles) > 1:
    current = active_role()
    idx = roles.index(current) if current in roles else 0
    selected_role = st.sidebar.selectbox("Ver portal como", roles, index=idx, key="role_switcher")
    if selected_role != active_role():
        st.session_state.active_role = selected_role
        st.rerun()
elif roles:
    st.session_state.active_role = roles[0]

st.sidebar.success(f"{user['Nombre']} · {active_role()}")
if st.sidebar.button("🔄 Actualizar datos", help="Fuerza una lectura inmediata de la base de datos"):
    invalidate_data_cache()
    st.rerun()
if is_teacher() and user.get("Maestro"):
    st.sidebar.caption(f"Maestro: {user['Maestro']}")
if is_student() and user.get("No_Control"):
    st.sidebar.caption(f"No. Control: {user['No_Control']}")
if st.sidebar.button("Cerrar sesión"):
    logout()

# =========================================================
# MENÚ POR ROL (aislamiento estricto)
# =========================================================
if is_admin():
    menu = [
        "🏠 Inicio",
        "📝 Pase de Lista",
        "👤 Expedientes",
        "👨‍🏫 Maestros y Asignaciones",
        "🔐 Usuarios y Permisos",
        "🎓 Cursos y Materiales",
        "📜 Historial de Asistencia",
        "🧾 Historial Académico",
    ]
elif is_teacher():
    menu = [
        "🏠 Mi grupo",
        "📝 Pase de Lista",
        "👤 Mis alumnos",
        "🎓 Material de mi módulo",
        "📜 Mi historial de asistencia",
    ]
elif is_student():
    menu = [
        "🏠 Mi perfil",
        "📚 Mi módulo y material",
        "📜 Mi asistencia",
    ]
else:  # Consulta
    menu = [
        "🏠 Inicio",
        "👤 Expedientes",
        "🎓 Cursos y Materiales",
        "📜 Historial de Asistencia",
    ]

opcion = st.sidebar.radio("Navegación", menu)

# =========================================================
# ADMIN / CONSULTA: INICIO
# =========================================================
if opcion == "🏠 Inicio":
    st.markdown('<div class="main-header">📊 Panel General</div>', unsafe_allow_html=True)
    alumnos = read_table("Alumnos")
    maestros = read_table("Maestros")
    asist = read_table("Asistencias")

    act = alumnos[alumnos["Activo"].apply(yes)] if not alumnos.empty else alumnos
    mact = maestros[maestros["Activo"].apply(yes)] if not maestros.empty else maestros

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Alumnos activos", len(act))
    c2.metric("Maestros activos", len(mact))
    c3.metric("Sin maestro", int((act["Maestro"].astype(str).str.strip()=="").sum()) if not act.empty else 0)
    c4.metric("Pendientes", int((act["Estado_Alumno"].astype(str)=="Pendiente de asignación").sum()) if not act.empty else 0)
    c5.metric("Asistencias registradas", len(asist))

    a,b = st.columns(2)
    with a:
        st.subheader("Por módulo")
        if not act.empty:
            st.bar_chart(act["Modulo"].replace("", "Sin asignar").value_counts())
    with b:
        st.subheader("Por red")
        if not act.empty:
            st.bar_chart(act["Red"].replace("", "Sin red").value_counts())

# =========================================================
# MAESTRO: MI GRUPO
# =========================================================
elif opcion == "🏠 Mi grupo":
    st.markdown('<div class="main-header">👨‍🏫 Mi grupo</div>', unsafe_allow_html=True)
    alumnos = safe_student_scope(read_table("Alumnos"))
    alumnos = alumnos[alumnos["Activo"].apply(yes)]
    st.metric("Alumnos asignados", len(alumnos))
    if alumnos.empty:
        st.info("No tienes alumnos asignados actualmente.")
    else:
        st.dataframe(
            alumnos[["No_Control","Nombre","Modulo","Modalidad","Estado_Alumno"]],
            use_container_width=True, hide_index=True
        )
    st.caption("No puedes consultar alumnos, métricas o grupos de otros maestros.")

# =========================================================
# ALUMNO: MI PERFIL
# =========================================================
elif opcion == "🏠 Mi perfil":
    st.markdown('<div class="main-header">👤 Mi perfil</div>', unsafe_allow_html=True)
    alumnos = safe_student_scope(read_table("Alumnos"))
    if alumnos.empty:
        st.error("No encontramos un expediente vinculado a tu usuario.")
        st.stop()
    a = alumnos.iloc[0]

    st.markdown(f"""
    <div class="card">
      <h3>{a['Nombre']}</h3>
      <b>No. Control:</b> {a['No_Control']}<br>
      <b>Estado:</b> {a['Estado_Alumno']}<br>
      <b>Red:</b> {a['Red'] or 'Pendiente'}<br>
      <b>Maestro:</b> {a['Maestro'] or 'Pendiente de asignación'}<br>
      <b>Módulo:</b> {a['Modulo'] or 'Pendiente de asignación'}<br>
      <b>Modalidad:</b> {a['Modalidad'] or 'Pendiente de asignación'}
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Mi ruta")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Encuentro", a["Encuentro"] or "—")
    c2.metric("12 Pasos", a["Pasos12"] or "—")
    c3.metric("Liberación", a["Liberacion"] or "—")
    c4.metric("Lanzamiento", a["Lanzamiento"] or "—")
    st.caption("Tu cuenta únicamente permite consultar tu propio expediente y contenido asignado.")

# =========================================================
# PASE DE LISTA
# =========================================================
elif opcion == "📝 Pase de Lista":
    st.markdown('<div class="main-header">📝 Pase de Lista</div>', unsafe_allow_html=True)
    alumnos = read_table("Alumnos")
    alumnos = alumnos[alumnos["Activo"].apply(yes)].copy()

    if is_teacher():
        maestro_sel = str(user.get("Maestro","")).strip()
        if not maestro_sel:
            st.error("Tu usuario no está vinculado a un maestro.")
            st.stop()
        st.info(f"Maestro: **{maestro_sel}**")
    elif is_admin():
        maestros = read_table("Maestros")
        names = maestros[maestros["Activo"].apply(yes)]["Nombre"].astype(str).tolist()
        maestro_sel = st.selectbox("Maestro", names)
    else:
        st.error("No tienes permiso para pasar lista.")
        st.stop()

    grupo = alumnos[alumnos["Maestro"].astype(str) == maestro_sel].copy()
    modulos = sorted([x for x in grupo["Modulo"].astype(str).unique().tolist() if x.strip()])
    if not modulos:
        st.warning("No hay módulos asignados a este maestro.")
        st.stop()

    c1,c2 = st.columns(2)
    modulo = c1.selectbox("Módulo", modulos)
    fecha = c2.date_input("Fecha", dt.date.today())

    lista = grupo[grupo["Modulo"].astype(str)==modulo]
    editor = pd.DataFrame({
        "No_Control": lista["No_Control"].astype(str),
        "Alumno": lista["Nombre"].astype(str),
        "Asistencia": [True]*len(lista),
        "Observaciones": [""]*len(lista),
    })

    edited = st.data_editor(
        editor, hide_index=True, use_container_width=True,
        disabled=["No_Control","Alumno"],
        column_config={
            "Asistencia": st.column_config.CheckboxColumn("Presente"),
            "Observaciones": st.column_config.TextColumn("Observaciones"),
        }
    )

    if st.button("💾 Guardar asistencia", type="primary"):
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows = []
        for _,r in edited.iterrows():
            rows.append([
                now,str(fecha),maestro_sel,modulo,str(r["No_Control"]),str(r["Alumno"]),
                "Presente" if bool(r["Asistencia"]) else "Ausente",
                str(r["Observaciones"]),str(user["Email"])
            ])
        append_rows("Asistencias", rows)
        st.success(f"✅ Se guardaron {len(rows)} registros.")

# =========================================================
# EXPEDIENTES ADMIN / CONSULTA / MAESTRO
# =========================================================
elif opcion in ["👤 Expedientes","👤 Mis alumnos"]:
    title = "👤 Mis alumnos" if is_teacher() else "👤 Expedientes"
    st.markdown(f'<div class="main-header">{title}</div>', unsafe_allow_html=True)

    alumnos = safe_student_scope(read_table("Alumnos"))
    if is_teacher():
        alumnos = alumnos[alumnos["Activo"].apply(yes)]

    if alumnos.empty:
        st.info("No hay alumnos disponibles.")
        st.stop()

    nombre = st.selectbox("Alumno", sorted(alumnos["Nombre"].astype(str).tolist()))
    a = alumnos[alumnos["Nombre"].astype(str)==nombre].iloc[0]

    st.markdown(f"""
    <div class="card">
      <h3>{a['Nombre']}</h3>
      <b>No. Control:</b> {a['No_Control']} |
      <b>Estado:</b> {a['Estado_Alumno']} |
      <b>Red:</b> {a['Red']}<br>
      <b>Maestro:</b> {a['Maestro'] or 'Sin asignar'} |
      <b>Módulo:</b> {a['Modulo'] or 'Sin asignar'} |
      <b>Modalidad:</b> {a['Modalidad'] or 'Sin asignar'}
    </div>
    """, unsafe_allow_html=True)

    if is_teacher():
        st.caption("Vista de consulta. No puedes editar expedientes ni ver alumnos de otros maestros.")

    if is_admin():
        maestros = read_table("Maestros")
        active_teachers = [""] + maestros[maestros["Activo"].apply(yes)]["Nombre"].astype(str).tolist()

        st.subheader("✏️ Edición administrativa")
        with st.form("edit_student"):
            c1,c2,c3 = st.columns(3)
            red = c1.text_input("Red", value=str(a["Red"]))
            maestro = c2.selectbox(
                "Maestro", active_teachers,
                index=active_teachers.index(str(a["Maestro"])) if str(a["Maestro"]) in active_teachers else 0
            )
            modulo = c3.text_input("Módulo", value=str(a["Modulo"]))
            modalidades = ["","PRESENCIAL","ONLINE"]
            modalidad = c1.selectbox(
                "Modalidad", modalidades,
                index=modalidades.index(str(a["Modalidad"])) if str(a["Modalidad"]) in modalidades else 0
            )
            estados = [
                "Pendiente de asignación","Activo","Baja temporal","Inactivo",
                "Baja definitiva","Reingreso","Reinicio de módulo"
            ]
            estado_actual = str(a["Estado_Alumno"]) or "Activo"
            estado = c2.selectbox(
                "Estado", estados,
                index=estados.index(estado_actual) if estado_actual in estados else 1
            )
            motivo = c3.text_input("Motivo del movimiento")
            encuentro = c1.text_input("Encuentro", value=str(a["Encuentro"]))
            pasos = c2.text_input("12 Pasos", value=str(a["Pasos12"]))
            liber = c3.text_input("Liberación", value=str(a["Liberacion"]))
            eb1 = c1.text_input("Esencia B1", value=str(a["Esencia_B1"]))
            eb2 = c2.text_input("Esencia B2", value=str(a["Esencia_B2"]))
            eb3 = c3.text_input("Esencia B3", value=str(a["Esencia_B3"]))
            lanz = c1.text_input("Lanzamiento", value=str(a["Lanzamiento"]))
            obs = c2.text_input("Observaciones")
            save = st.form_submit_button("Guardar cambios", type="primary")

        if save:
            full = read_table("Alumnos")
            mask = full["No_Control"].astype(str)==str(a["No_Control"])
            before = full[mask].iloc[0].to_dict()

            updates = {
                "Red":red,"Maestro":maestro,"Modulo":modulo,"Modalidad":modalidad,
                "Estado_Alumno":estado,"Encuentro":encuentro,"Pasos12":pasos,
                "Liberacion":liber,"Esencia_B1":eb1,"Esencia_B2":eb2,
                "Esencia_B3":eb3,"Lanzamiento":lanz
            }
            for k,v in updates.items():
                full.loc[mask,k] = v
            full.loc[mask,"Activo"] = "No" if estado in ["Inactivo","Baja definitiva"] else "Sí"
            after = full[mask].iloc[0].to_dict()
            write_table("Alumnos", full)

            if any(str(before.get(k,"")) != str(after.get(k,"")) for k in [
                "Estado_Alumno","Maestro","Modulo","Modalidad"
            ]):
                movement = "Actualización académica"
                if estado == "Baja temporal": movement = "Baja temporal"
                elif estado == "Baja definitiva": movement = "Baja definitiva"
                elif estado == "Reingreso": movement = "Reingreso"
                elif estado == "Reinicio de módulo": movement = "Reinicio de módulo"
                elif str(before.get("Maestro","")) != str(after.get("Maestro","")): movement = "Cambio de maestro"
                elif str(before.get("Modulo","")) != str(after.get("Modulo","")): movement = "Cambio de módulo"
                log_movement(before, after, movement, motivo, obs, user["Email"])
            st.success("Expediente actualizado.")
            st.rerun()

# =========================================================
# ADMIN: MAESTROS / ASIGNACIONES / ALTAS
# =========================================================
elif opcion == "👨‍🏫 Maestros y Asignaciones":
    if not is_admin():
        st.error("Acceso restringido.")
        st.stop()

    st.markdown('<div class="main-header">👨‍🏫 Maestros y Asignaciones</div>', unsafe_allow_html=True)
    tabs = st.tabs([
        "Maestros","Promover alumno a maestro","Reasignar alumnos","Nuevo alumno",
        "Pendientes de asignación","Estados de alumnos"
    ])

    with tabs[0]:
        maestros = read_table("Maestros")
        st.dataframe(maestros, use_container_width=True, hide_index=True)

        with st.form("new_teacher"):
            st.subheader("Agregar maestro")
            nombre = st.text_input("Nombre")
            email = st.text_input("Correo")
            red = st.text_input("Red")
            add = st.form_submit_button("Agregar maestro", type="primary")
        if add:
            if not nombre.strip():
                st.error("Escribe el nombre.")
            else:
                mid = f"M{len(maestros)+1:03d}"
                maestros = pd.concat([maestros, pd.DataFrame([{
                    "ID_Maestro":mid,"Nombre":nombre.strip(),"Email":normalize_email(email),
                    "Red":red.strip(),"Activo":"Sí"
                }])], ignore_index=True)
                write_table("Maestros", maestros)
                st.success("Maestro agregado.")
                st.rerun()

        if not maestros.empty:
            st.subheader("Activar / desactivar maestro")
            t = st.selectbox("Maestro", maestros["Nombre"].astype(str).tolist())
            row = maestros[maestros["Nombre"].astype(str)==t].iloc[0]
            est = st.radio("Estatus", ["Activo","Inactivo"], index=0 if yes(row["Activo"]) else 1, horizontal=True)
            if st.button("Guardar estatus"):
                maestros.loc[maestros["Nombre"].astype(str)==t,"Activo"] = "Sí" if est=="Activo" else "No"
                write_table("Maestros", maestros)
                st.success("Estatus actualizado.")
                st.rerun()

    with tabs[1]:
        st.subheader("Promover alumno a maestro")
        st.caption("El alumno conserva su expediente y obtiene también el rol de Maestro. Después podrá cambiar entre vista Alumno y Maestro.")

        alumnos = read_table("Alumnos", fresh=True)
        usuarios = read_table("Usuarios", fresh=True)
        maestros = read_table("Maestros", fresh=True)

        alumno_options = {f"{r['No_Control']} · {r['Nombre']}": str(r["No_Control"]) for _, r in alumnos.iterrows()}
        selected_label = st.selectbox("Alumno", list(alumno_options.keys()), key="promote_student") if alumno_options else None
        red_default = ""
        temp_pin = st.text_input("PIN temporal (solo se usa si el alumno todavía no tiene usuario)", type="password", key="promote_pin")

        c1, c2 = st.columns(2)
        promote = c1.button("⬆️ Promover a maestro", type="primary", use_container_width=True)
        remove_teacher = c2.button("↩️ Quitar rol de maestro", use_container_width=True)

        if selected_label:
            sid = alumno_options[selected_label]
            student_mask = alumnos["No_Control"].astype(str) == sid
            student = alumnos[student_mask].iloc[0].to_dict()
            student_name = str(student.get("Nombre", "")).strip()
            student_email = normalize_email(student.get("Email", ""))

            if promote:
                # 1) Alta/activación en Maestros
                teacher_match = maestros["Nombre"].astype(str).str.strip().str.lower() == student_name.lower()
                if teacher_match.any():
                    maestros.loc[teacher_match, "Activo"] = "Sí"
                    if student_email:
                        maestros.loc[teacher_match, "Email"] = student_email
                    if str(student.get("Red", "")).strip():
                        maestros.loc[teacher_match, "Red"] = str(student.get("Red", "")).strip()
                else:
                    nums = pd.to_numeric(maestros["ID_Maestro"].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
                    next_mid = int(nums.max()) + 1 if nums.notna().any() else len(maestros) + 1
                    maestros = pd.concat([maestros, pd.DataFrame([{
                        "ID_Maestro": f"M{next_mid:03d}",
                        "Nombre": student_name,
                        "Email": student_email,
                        "Red": str(student.get("Red", "")).strip(),
                        "Activo": "Sí",
                    }])], ignore_index=True)
                write_table("Maestros", maestros)

                # 2) Actualizar usuario conservando Alumno + Maestro
                user_mask = usuarios["No_Control"].astype(str) == sid
                if not user_mask.any() and student_email:
                    user_mask = usuarios["Email"].astype(str).str.lower().str.strip() == student_email

                if user_mask.any():
                    ui = usuarios[user_mask].index[0]
                    roles_existing = [x.strip() for x in re.split(r"[,;/|]+", str(usuarios.at[ui, "Rol"])) if x.strip()]
                    for role in ["Alumno", "Maestro"]:
                        if role not in roles_existing:
                            roles_existing.append(role)
                    usuarios.at[ui, "Rol"] = ",".join(roles_existing)
                    usuarios.at[ui, "Maestro"] = student_name
                    usuarios.at[ui, "No_Control"] = sid
                    usuarios.at[ui, "Activo"] = "Sí"
                    if student_email:
                        usuarios.at[ui, "Email"] = student_email
                else:
                    if not student_email:
                        st.error("Este alumno no tiene correo. Agrégalo primero al expediente.")
                        st.stop()
                    if len(temp_pin) < 6:
                        st.error("Este alumno no tiene usuario. Define un PIN temporal de al menos 6 caracteres.")
                        st.stop()
                    usuarios = pd.concat([usuarios, pd.DataFrame([{
                        "Email": student_email,
                        "Nombre": student_name,
                        "Rol": "Alumno,Maestro",
                        "Maestro": student_name,
                        "No_Control": sid,
                        "PIN_Hash": hash_pin(temp_pin),
                        "Activo": "Sí",
                    }])], ignore_index=True)
                write_table("Usuarios", usuarios)
                log_movement(student, student, "Promoción a maestro", "Alta de rol Maestro", "Conserva rol Alumno", user["Email"])
                st.success(f"{student_name} ahora tiene roles Alumno y Maestro.")
                st.rerun()

            if remove_teacher:
                user_mask = usuarios["No_Control"].astype(str) == sid
                if not user_mask.any() and student_email:
                    user_mask = usuarios["Email"].astype(str).str.lower().str.strip() == student_email
                if user_mask.any():
                    ui = usuarios[user_mask].index[0]
                    roles_existing = [x.strip() for x in re.split(r"[,;/|]+", str(usuarios.at[ui, "Rol"])) if x.strip()]
                    roles_existing = [r for r in roles_existing if r != "Maestro"]
                    if "Alumno" not in roles_existing:
                        roles_existing.insert(0, "Alumno")
                    usuarios.at[ui, "Rol"] = ",".join(roles_existing)
                    usuarios.at[ui, "Maestro"] = ""
                    usuarios.at[ui, "No_Control"] = sid
                    write_table("Usuarios", usuarios)

                teacher_match = maestros["Nombre"].astype(str).str.strip().str.lower() == student_name.lower()
                if teacher_match.any():
                    maestros.loc[teacher_match, "Activo"] = "No"
                    write_table("Maestros", maestros)

                log_movement(student, student, "Baja de rol maestro", "Se retira rol Maestro", "Conserva rol Alumno", user["Email"])
                st.success(f"Se retiró el rol Maestro de {student_name}; conserva su acceso como Alumno.")
                st.rerun()

    with tabs[2]:
        alumnos = read_table("Alumnos")
        maestros = read_table("Maestros")
        teacher_names = maestros[maestros["Activo"].apply(yes)]["Nombre"].astype(str).tolist()

        filtro = st.selectbox("Mostrar", ["Todos","Pendientes de asignación","Sin maestro"] + teacher_names)
        vista = alumnos.copy()
        if filtro == "Pendientes de asignación":
            vista = vista[vista["Estado_Alumno"].astype(str)=="Pendiente de asignación"]
        elif filtro == "Sin maestro":
            vista = vista[vista["Maestro"].astype(str).str.strip()==""]
        elif filtro != "Todos":
            vista = vista[vista["Maestro"].astype(str)==filtro]

        options = {f"{r['No_Control']} · {r['Nombre']}":str(r["No_Control"]) for _,r in vista.iterrows()}
        selected = st.multiselect("Selecciona alumnos", list(options.keys()))
        new_teacher = st.selectbox("Nuevo maestro", [""] + teacher_names)
        new_module = st.text_input("Nuevo módulo")
        new_mode = st.selectbox("Modalidad", ["Sin cambio","PRESENCIAL","ONLINE"])
        movement_type = st.selectbox(
            "Tipo de movimiento",
            ["Asignación","Cambio de maestro","Cambio de módulo","Reingreso","Reinicio de módulo"]
        )
        motivo = st.text_input("Motivo / comentario")

        if st.button("Aplicar movimiento", type="primary"):
            if not selected:
                st.warning("Selecciona al menos un alumno.")
            else:
                ids = [options[x] for x in selected]
                for sid in ids:
                    mask = alumnos["No_Control"].astype(str)==sid
                    before = alumnos[mask].iloc[0].to_dict()
                    if new_teacher != "":
                        alumnos.loc[mask,"Maestro"] = new_teacher
                    if new_module.strip():
                        alumnos.loc[mask,"Modulo"] = new_module.strip()
                    if new_mode != "Sin cambio":
                        alumnos.loc[mask,"Modalidad"] = new_mode
                    alumnos.loc[mask,"Estado_Alumno"] = "Reinicio de módulo" if movement_type=="Reinicio de módulo" else "Activo"
                    alumnos.loc[mask,"Activo"] = "Sí"
                    after = alumnos[mask].iloc[0].to_dict()
                    log_movement(before, after, movement_type, motivo, "", user["Email"])
                write_table("Alumnos", alumnos)
                st.success(f"Movimiento aplicado a {len(ids)} alumno(s).")
                st.rerun()

    with tabs[3]:
        alumnos = read_table("Alumnos")
        maestros = read_table("Maestros")
        teacher_names = [""] + maestros[maestros["Activo"].apply(yes)]["Nombre"].astype(str).tolist()

        with st.form("new_student_admin"):
            c1,c2,c3 = st.columns(3)
            nombre = c1.text_input("Nombre completo")
            sexo = c2.selectbox("Sexo", ["","Hombre","Mujer"])
            celular = c3.text_input("Celular")
            email = c1.text_input("Correo")
            red = c2.text_input("Red")
            maestro = c3.selectbox("Maestro", teacher_names)
            modulo = c1.text_input("Módulo")
            modalidad = c2.selectbox("Modalidad", ["","PRESENCIAL","ONLINE"])
            add_student = st.form_submit_button("Agregar alumno", type="primary")

        if add_student:
            nid = next_student_id(alumnos)
            student = {
                "No_Control":str(nid),"Nombre":nombre.strip(),"Sexo":sexo,"Fecha_Nacimiento":"",
                "Celular":celular.strip(),"Email":normalize_email(email),"Red":red.strip(),
                "Maestro":maestro,"Modulo":modulo.strip(),"Modalidad":modalidad,
                "Estado_Alumno":"Activo","Fecha_Registro":str(dt.date.today()),
                "Origen_Registro":"Alta administrativa","Encuentro":"No","Pasos12":"",
                "Liberacion":"No","Esencia_B1":"","Esencia_B2":"","Esencia_B3":"",
                "Lanzamiento":"No","Fechas_Eventos":"","Activo":"Sí"
            }
            alumnos = pd.concat([alumnos, pd.DataFrame([student])], ignore_index=True)
            write_table("Alumnos", alumnos)
            log_movement({}, student, "Alta administrativa", "Nuevo alumno", "", user["Email"])
            st.success(f"Alumno agregado con No. Control {nid}.")
            st.rerun()

    with tabs[4]:
        alumnos = read_table("Alumnos")
        pending = alumnos[alumnos["Estado_Alumno"].astype(str)=="Pendiente de asignación"]
        if pending.empty:
            st.success("No hay alumnos pendientes.")
        else:
            st.dataframe(
                pending[["No_Control","Nombre","Celular","Email","Red","Fecha_Registro"]],
                use_container_width=True, hide_index=True
            )
        st.info("Enlace público: agrega **?registro=1** al final de la URL de tu app.")

    with tabs[5]:
        alumnos = read_table("Alumnos")
        estado = st.selectbox(
            "Filtrar por estado",
            ["Todos","Activo","Pendiente de asignación","Baja temporal","Inactivo","Baja definitiva","Reingreso","Reinicio de módulo"]
        )
        view = alumnos if estado=="Todos" else alumnos[alumnos["Estado_Alumno"].astype(str)==estado]
        st.dataframe(
            view[["No_Control","Nombre","Estado_Alumno","Maestro","Modulo","Modalidad","Activo"]],
            use_container_width=True, hide_index=True
        )

# =========================================================# ADMIN: USUARIOS Y PERMISOS
# =========================================================
elif opcion == "🔐 Usuarios y Permisos":
    if not is_admin():
        st.error("Acceso restringido.")
        st.stop()

    st.markdown('<div class="main-header">🔐 Usuarios y Permisos</div>', unsafe_allow_html=True)
    usuarios = read_table("Usuarios")
    st.dataframe(usuarios.drop(columns=["PIN_Hash"], errors="ignore"), use_container_width=True, hide_index=True)

    maestros = read_table("Maestros")
    alumnos = read_table("Alumnos")
    teacher_names = [""] + maestros[maestros["Activo"].apply(yes)]["Nombre"].astype(str).tolist()
    student_opts = [""] + [f"{r['No_Control']} · {r['Nombre']}" for _,r in alumnos.iterrows()]

    with st.form("new_user"):
        st.subheader("Crear usuario")
        email = st.text_input("Correo")
        nombre = st.text_input("Nombre")
        rol = st.selectbox("Rol", ["Alumno","Maestro","Alumno,Maestro","Consulta","Administrador"])
        maestro = st.selectbox("Vincular a maestro", teacher_names)
        alumno_ref = st.selectbox("Vincular a alumno", student_opts)
        pin = st.text_input("PIN inicial", type="password")
        create = st.form_submit_button("Crear usuario", type="primary")

    if create:
        no_control = alumno_ref.split(" · ")[0] if alumno_ref else ""
        email_n = normalize_email(email)
        if not email_n or len(pin) < 6:
            st.error("Correo y PIN (mínimo 6 caracteres) son obligatorios.")
        elif email_n in usuarios["Email"].astype(str).str.lower().tolist():
            st.error("Ese correo ya existe.")
        else:
            usuarios = pd.concat([usuarios, pd.DataFrame([{
                "Email":email_n,"Nombre":nombre.strip(),"Rol":rol,
                "Maestro":maestro if "Maestro" in rol else "",
                "No_Control":no_control if "Alumno" in rol else "",
                "PIN_Hash":hash_pin(pin),"Activo":"Sí"
            }])], ignore_index=True)
            write_table("Usuarios", usuarios)
            st.success("Usuario creado.")
            st.rerun()

    if not usuarios.empty:
        st.subheader("Activar / desactivar / cambiar PIN")
        target = st.selectbox("Usuario", usuarios["Email"].astype(str).tolist())
        row = usuarios[usuarios["Email"].astype(str)==target].iloc[0]
        state = st.radio("Estatus", ["Activo","Inactivo"], index=0 if yes(row["Activo"]) else 1, horizontal=True)
        new_pin = st.text_input("Nuevo PIN (opcional)", type="password")
        if st.button("Guardar usuario"):
            mask = usuarios["Email"].astype(str)==target
            usuarios.loc[mask,"Activo"] = "Sí" if state=="Activo" else "No"
            if new_pin:
                usuarios.loc[mask,"PIN_Hash"] = hash_pin(new_pin)
            write_table("Usuarios", usuarios)
            st.success("Usuario actualizado.")
            st.rerun()

# =========================================================
# CURSOS / MATERIALES ADMIN / CONSULTA
# =========================================================
elif opcion == "🎓 Cursos y Materiales":
    st.markdown('<div class="main-header">🎓 Cursos y Materiales</div>', unsafe_allow_html=True)
    cursos = read_table("Cursos")
    materiales = read_table("Materiales")
    active = cursos[cursos["Activo"].apply(yes)]

    if not active.empty:
        cmap = dict(zip(active["Nombre"].astype(str), active["Curso_ID"].astype(str)))
        cname = st.selectbox("Curso", list(cmap.keys()))
        cid = cmap[cname]
        mats = materiales[
            (materiales["Curso_ID"].astype(str)==cid) &
            (materiales["Visible"].apply(yes))
        ]
        for _,m in mats.iterrows():
            st.markdown(
                f"""<div class="card"><b>{m['Modulo']} · {m['Titulo']}</b><br>
                <span class="small-muted">{m['Descripcion']}</span><br><br>
                <a href="{m['URL']}" target="_blank">📄 Abrir / descargar material</a></div>""",
                unsafe_allow_html=True
            )
        if mats.empty:
            st.info("Aún no hay materiales visibles.")

    if is_admin():
        st.divider()
        tab1,tab2 = st.tabs(["Nuevo curso","Agregar material"])
        with tab1:
            with st.form("new_course"):
                name = st.text_input("Nombre del curso")
                desc = st.text_area("Descripción")
                save = st.form_submit_button("Crear curso", type="primary")
            if save:
                cid = f"C{len(cursos)+1:03d}"
                cursos = pd.concat([cursos,pd.DataFrame([{
                    "Curso_ID":cid,"Nombre":name.strip(),"Descripcion":desc.strip(),"Activo":"Sí"
                }])], ignore_index=True)
                write_table("Cursos", cursos)
                st.success("Curso creado.")
                st.rerun()
        with tab2:
            cursos = read_table("Cursos")
            cmap = dict(zip(cursos["Nombre"].astype(str), cursos["Curso_ID"].astype(str)))
            with st.form("new_material"):
                cname = st.selectbox("Curso", list(cmap.keys()))
                modulo = st.text_input("Módulo / Unidad")
                title = st.text_input("Título")
                desc = st.text_area("Descripción")
                url = st.text_input("Enlace de Google Drive / recurso")
                tipo = st.selectbox("Tipo", ["PDF","Documento","Video","Presentación","Otro"])
                visible = st.checkbox("Visible", value=True)
                save = st.form_submit_button("Agregar material", type="primary")
            if save:
                mid = f"MAT{len(materiales)+1:04d}"
                materiales = pd.concat([materiales,pd.DataFrame([{
                    "Material_ID":mid,"Curso_ID":cmap[cname],"Modulo":modulo.strip(),
                    "Titulo":title.strip(),"Descripcion":desc.strip(),"URL":url.strip(),
                    "Tipo":tipo,"Fecha":str(dt.date.today()),"Visible":"Sí" if visible else "No"
                }])], ignore_index=True)
                write_table("Materiales", materiales)
                st.success("Material agregado.")
                st.rerun()

# =========================================================
# MAESTRO: MATERIAL DE SU MÓDULO
# =========================================================
elif opcion == "🎓 Material de mi módulo":
    st.markdown('<div class="main-header">📚 Material de mi módulo</div>', unsafe_allow_html=True)
    alumnos = safe_student_scope(read_table("Alumnos"))
    modules = sorted([x for x in alumnos["Modulo"].astype(str).unique().tolist() if x.strip()])
    materiales = read_table("Materiales")
    if not modules:
        st.info("No tienes módulos asignados.")
    else:
        mod = st.selectbox("Módulo", modules)
        mats = materiales[
            (materiales["Modulo"].astype(str)==mod) &
            (materiales["Visible"].apply(yes))
        ]
        if mats.empty:
            st.info("No hay material visible para este módulo.")
        else:
            for _,m in mats.iterrows():
                st.markdown(
                    f"""<div class="card"><b>{m['Titulo']}</b><br>{m['Descripcion']}<br><br>
                    <a href="{m['URL']}" target="_blank">📄 Abrir / descargar</a></div>""",
                    unsafe_allow_html=True
                )
    st.caption("Solo se muestran materiales vinculados a tus módulos actuales.")

# =========================================================
# ALUMNO: SU MÓDULO Y MATERIAL
# =========================================================
elif opcion == "📚 Mi módulo y material":
    st.markdown('<div class="main-header">📚 Mi módulo y material</div>', unsafe_allow_html=True)
    alumnos = safe_student_scope(read_table("Alumnos"))
    if alumnos.empty:
        st.error("No encontramos tu expediente.")
        st.stop()
    a = alumnos.iloc[0]
    st.info(
        f"**Maestro:** {a['Maestro'] or 'Pendiente'}  \n"
        f"**Módulo:** {a['Modulo'] or 'Pendiente'}  \n"
        f"**Modalidad:** {a['Modalidad'] or 'Pendiente'}"
    )

    if not str(a["Modulo"]).strip():
        st.warning("Aún no tienes un módulo asignado.")
    else:
        mats = read_table("Materiales")
        mats = mats[
            (mats["Modulo"].astype(str)==str(a["Modulo"])) &
            (mats["Visible"].apply(yes))
        ]
        if mats.empty:
            st.info("Aún no hay material visible para tu módulo.")
        else:
            for _,m in mats.iterrows():
                st.markdown(
                    f"""<div class="card"><b>{m['Titulo']}</b><br>{m['Descripcion']}<br><br>
                    <a href="{m['URL']}" target="_blank">📄 Abrir / descargar</a></div>""",
                    unsafe_allow_html=True
                )
    st.caption("No puedes ver alumnos, maestros distintos, métricas generales ni otros módulos.")

# =========================================================
# HISTORIAL DE ASISTENCIA SEGÚN ROL
# =========================================================
elif opcion in ["📜 Historial de Asistencia","📜 Mi historial de asistencia","📜 Mi asistencia"]:
    st.markdown('<div class="main-header">📜 Historial de Asistencia</div>', unsafe_allow_html=True)
    asist = read_table("Asistencias")

    if is_teacher():
        asist = asist[asist["Maestro"].astype(str)==str(user.get("Maestro",""))]
    elif is_student():
        asist = asist[asist["No_Control"].astype(str)==str(user.get("No_Control",""))]

    if asist.empty:
        st.info("Aún no hay registros.")
    else:
        if is_student():
            st.dataframe(
                asist[["Fecha","Modulo","Asistencia","Observaciones"]].sort_values("Fecha", ascending=False),
                use_container_width=True, hide_index=True
            )
        elif is_teacher():
            st.dataframe(
                asist[["Fecha","Modulo","Alumno","Asistencia","Observaciones"]].sort_values("Fecha", ascending=False),
                use_container_width=True, hide_index=True
            )
        else:
            st.dataframe(asist.sort_values("Fecha", ascending=False), use_container_width=True, hide_index=True)

# =========================================================
# ADMIN: HISTORIAL ACADÉMICO
# =========================================================
elif opcion == "🧾 Historial Académico":
    if not is_admin():
        st.error("Acceso restringido.")
        st.stop()
    st.markdown('<div class="main-header">🧾 Historial Académico</div>', unsafe_allow_html=True)
    hist = read_table("HistorialAcademico")
    if hist.empty:
        st.info("Aún no hay movimientos.")
    else:
        st.dataframe(hist.sort_values("Timestamp", ascending=False), use_container_width=True, hide_index=True)
