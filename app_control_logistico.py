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

# Inicializar lector OCR (en español)
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

def extraer_datos_de_foto(imagen_pil):
    # Convertir imagen PIL a array para EasyOCR
    img_array = np.array(imagen_pil)
    resultados = reader.readtext(img_array, detail=0)
    texto_completo = " ".join(resultados)
    
    # Buscar patrones numéricos (Ej. VR-123456, 55653919, o números de 6 a 8 dígitos)
    patron_numero = re.search(r'([A-Z]{2}-\d+|\d{6,8})', texto_completo)
    num_detectado = patron_numero.group(0) if patron_numero else "Revisar foto"
    
    return num_detectado, texto_completo

# --- ENCABEZADO CORPORATIVO EL CORTE INGLÉS ---
st.markdown("<h1 style='text-align: center; font-style: italic; font-weight: bold; color: #006633;'>El Corte Inglés</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; margin-top: -15px;'>Envíos 55653919 — Escáner Automático OCR</h3>", unsafe_allow_html=True)
st.markdown("---")

tab_rechazos, tab_traspasos, tab_tienda, tab_recogidas = st.tabs([
    "📦 Vales de Rechazo", "🔄 Traspasos", "🏬 Envíos a Tienda", "🚛 Recogidas"
])

# ---------------------------------------------------------
# PROCESAMIENTO AUTOMÁTICO DE FOTOS POR SECCIÓN
# ---------------------------------------------------------
secciones = [
    ("📦 Vales de Rechazo", tab_rechazos, "Vales_Rechazo", ["Nº Vale de Rechazo", "Destino", "Fecha", "Foto / Captura", "Estado / Observaciones"]),
    ("🔄 Traspasos", tab_traspasos, "Traspasos", ["Nº Traspaso", "Destino", "Fecha", "Foto / Captura", "Estado / Observaciones"]),
    ("🏬 Envíos a Tienda", tab_tienda, "Envios_Tienda", ["Nº Operación", "Destino", "Fecha", "Foto / Captura", "Estado / Observaciones"]),
    ("🚛 Recogidas", tab_recogidas, "Recogidas", ["Nº Recogida", "Destino", "Fecha", "Foto / Captura", "Estado / Observaciones"])
]

for titulo, tab, hoja, columnas in secciones:
    with tab:
        df_historico = cargar_datos(hoja, columnas)
        c_cam, c_res = st.columns([1, 1])
        
        with c_cam:
            st.subheader("📸 Haz la foto al papel o etiqueta")
            foto = st.camera_input(f"Capturar documento para {titulo}", key=f"cam_{hoja}")
            
        with c_res:
            st.subheader("⚡ Lectura Automática")
            if foto:
                img = Image.open(foto)
                with st.spinner("Escaneando e identificando datos con IA..."):
                    num_extraido, texto_detectado = extraer_datos_de_foto(img)
                
                st.success("¡Texto detectado con éxito!")
                num_doc = st.text_input("Nº Documento / Vale (Detectado):", value=num_extraido, key=f"num_{hoja}")
                destino = st.text_input("Destino:", value="Eminencia / CSL", key=f"dest_{hoja}")
                fecha_doc = st.date_input("Fecha:", value=datetime.date.today(), format="DD/MM/YYYY", key=f"fec_{hoja}")
                
                if st.button("💾 Confirmar y Guardar en Excel", key=f"btn_{hoja}"):
                    nueva_fila = {
                        columnas[0]: num_doc,
                        "Destino": destino,
                        "Fecha": fecha_doc.strftime("%d/%m/%Y"),
                        "Foto / Captura": "Capturada",
                        "Estado / Observaciones": "Extraído automáticamente por foto"
                    }
                    df_historico = pd.concat([df_historico, pd.DataFrame([nueva_fila])], ignore_index=True)
                    guardar_datos(df_historico, hoja)
                    st.balloons()
                    st.success("✅ Guardado en el Excel maestro.")

        st.markdown("---")
        st.subheader("Histórico de Registros")
        st.data_editor(df_historico, use_container_width=True, key=f"ed_{hoja}", num_rows="dynamic")