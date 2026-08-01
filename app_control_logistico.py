import streamlit as st
import pandas as pd
import datetime
import os
import re
from PIL import Image
import easyocr
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="El Corte Inglés - Envíos 55653919", page_icon="🟢", layout="wide")

EXCEL_MAESTRO = os.path.expanduser("~/Desktop/Control_Envios_Logistica_55653919.xlsx")

# Cargar lector OCR
@st.cache_resource
def cargar_lector_ocr():
    return easyocr.Reader(['es'], gpu=False)

reader = cargar_lector_ocr()

def cargar_datos(pestana, columnas):
    if os.path.exists(EXCEL_MAESTRO):
        try:
            return pd.read_excel(EXCEL_MAESTRO, sheet_name=pestana)
        except Exception:
            return pd.DataFrame(columns=columnas)
    else:
        return pd.DataFrame(columns=columnas)

def guardar_datos(df, pestana):
    if os.path.exists(EXCEL_MAESTRO):
        with pd.ExcelWriter(EXCEL_MAESTRO, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=pestana, index=False)
    else:
        with pd.ExcelWriter(EXCEL_MAESTRO, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=pestana, index=False)

def extraer_numero_doc(imagen_pil):
    img_array = np.array(imagen_pil)
    resultados = reader.readtext(img_array, detail=0)
    texto_completo = " ".join(resultados)
    
    # Extraer únicamente el número de documento/vale
    patron_numero = re.search(r'([A-Z]{2}-\d+|\d{6,8})', texto_completo)
    num_detectado = patron_numero.group(0) if patron_numero else "Revisar foto"
    
    return num_detectado

# --- ENCABEZADO CORPORATIVO CON LOGO OFICIAL ---
col_logo_1, col_logo_2, col_logo_3 = st.columns([1, 2, 1])
with col_logo_2:
    if os.path.exists("el-corte-ingles-logo-png_seeklogo-365743.png"):
        st.image("el-corte-ingles-logo-png_seeklogo-365743.png", use_container_width=True)
    else:
        # Enlace alternativo de respaldo mientras subes la imagen
        st.image("https://seeklogo.com/images/E/el-corte-ingles-logo-365743.png", use_container_width=True)

st.markdown("<h3 style='text-align: center; margin-top: -10px; color: #006633;'>Envíos 55653919</h3>", unsafe_allow_html=True)
st.caption("<p style='text-align: center;'>Registro automático con fecha de escaneo en tiempo real</p>", unsafe_allow_html=True)
st.markdown("---")

tab_rechazos, tab_traspasos, tab_tienda, tab_recogidas = st.tabs([
    "📦 Vales de Rechazo", "🔄 Traspasos", "🏬 Envíos a Tienda", "🚛 Recogidas"
])

secciones = [
    ("📦 Vales de Rechazo", tab_rechazos, "Vales_Rechazo", ["Nº Vale de Rechazo", "Destino", "Fecha Escaneo", "Foto / Captura", "Estado / Observaciones"]),
    ("🔄 Traspasos", tab_traspasos, "Traspasos", ["Nº Traspaso", "Destino", "Fecha Escaneo", "Foto / Captura", "Estado / Observaciones"]),
    ("🏬 Envíos a Tienda", tab_tienda, "Envios_Tienda", ["Nº Operación", "Destino", "Fecha Escaneo", "Foto / Captura", "Estado / Observaciones"]),
    ("🚛 Recogidas", tab_recogidas, "Recogidas", ["Nº Recogida", "Destino", "Fecha Escaneo", "Foto / Captura", "Estado / Observaciones"])
]

for titulo, tab, hoja, columnas in secciones:
    with tab:
        df_historico = cargar_datos(hoja, columnas)
        c_cam, c_res = st.columns([1, 1])
        
        with c_cam:
            st.subheader("📸 Haz la foto al documento")
            foto = st.camera_input(f"Escaneo rápido para {titulo}", key=f"cam_{hoja}")
            
        with c_res:
            st.subheader("⚡ Datos de Entrada")
            if foto:
                img = Image.open(foto)
                with st.spinner("Leyendo número de documento..."):
                    num_extraido = extraer_numero_doc(img)
                
                # Asignación automática de la fecha actual de escaneo
                fecha_escaneo_hoy = datetime.date.today().strftime("%d/%m/%Y")
                
                st.success(f"📅 Fecha de escaneo asignada: **{fecha_escaneo_hoy}**")
                
                num_doc = st.text_input("Nº Documento / Vale:", value=num_extraido, key=f"num_{hoja}")
                destino = st.text_input("Destino:", value="Eminencia / CSL", key=f"dest_{hoja}")
                
                if st.button("💾 Guardar Registro", key=f"btn_{hoja}"):
                    nueva_fila = {
                        columnas[0]: num_doc,
                        "Destino": destino,
                        "Fecha Escaneo": fecha_escaneo_hoy,
                        "Foto / Captura": "Capturada",
                        "Estado / Observaciones": "Registrado en el momento del escaneo"
                    }
                    df_historico = pd.concat([df_historico, pd.DataFrame([nueva_fila])], ignore_index=True)
                    guardar_datos(df_historico, hoja)
                    st.balloons()
                    st.success("✅ Fila guardada con la fecha de hoy.")

        st.markdown("---")
        st.subheader("Histórico de Registros")
        st.data_editor(df_historico, use_container_width=True, key=f"ed_{hoja}", num_rows="dynamic")
