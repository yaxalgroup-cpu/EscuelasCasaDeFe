                cid = f"C{len(cursos)+1:03d}"
                cursos = pd.concat([cursos,pd.DataFrame([{
                    "Curso_ID":cid,"Nombre":name.strip(),"Descripcion":desc.strip(),"Activo":"Sí"
                }])], ignore_index=True)
                write_table("Cursos", cursos)
                st.success("Curso creado.")
                st.rerun()
        elif course_admin_section == "Agregar material":
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
