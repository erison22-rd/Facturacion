import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import plotly.express as px
from fpdf import FPDF

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="FIBERTELECOM",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. FUNCION GENERAR PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(16, 185, 129) # Verde Esmeralda
        self.cell(0, 10, 'FIBERTELECOM', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 5, 'Ubicación: San Cristóbal, Buen Pastor', 0, 1, 'C')
        self.ln(10)

def generar_factura_pdf(datos_venta):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Factura de Venta # {datos_venta['id']}", 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 10, f"Fecha: {datos_venta['fecha']}", 0, 1)
    pdf.cell(0, 10, f"Cliente: {datos_venta['cliente_nombre']}", 0, 1)
    pdf.ln(5)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(80, 10, 'Producto', 1, 0, 'C', True)
    pdf.cell(30, 10, 'Cant.', 1, 0, 'C', True)
    pdf.cell(40, 10, 'Precio Unit.', 1, 0, 'C', True)
    pdf.cell(40, 10, 'Subtotal', 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 11)
    precio_unit = datos_venta['monto'] / datos_venta['cantidad']
    pdf.cell(80, 10, str(datos_venta['producto']), 1)
    pdf.cell(30, 10, str(datos_venta['cantidad']), 1, 0, 'C')
    pdf.cell(40, 10, f"${precio_unit:,.2f}", 1, 0, 'C')
    pdf.cell(40, 10, f"${datos_venta['monto']:,.2f}", 1, 1, 'C')
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 10, 'TOTAL:', 0, 0, 'R')
    pdf.cell(40, 10, f"${datos_venta['monto']:,.2f}", 0, 1, 'C')
    
    pdf.ln(20)
    pdf.set_font('Arial', 'I', 12)
    pdf.cell(0, 10, '¡Gracias por preferirnos!', 0, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- 3. CSS PERSONALIZADO ---
st.markdown("""
    <style>
    .stApp { background-color: #0f131a !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #2d333b; }
    .brand-container { display: flex; align-items: center; gap: 10px; padding: 20px 0px; color: #10b981; font-size: 22px; font-weight: 800; }
    
    div[data-testid="stMetricValue"] { color: #10b981 !important; font-size: 38px !important; font-weight: 700 !important; }
    
    div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p {
        color: #10b981 !important; font-weight: 600 !important;
    }
    div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] label {
        background-color: transparent !important; border: 1px solid #2d333b !important;
        padding: 12px 15px !important; border-radius: 8px !important; margin-bottom: 12px !important;
    }
    div[data-testid="stSidebarUserContent"] .stRadio div[role="radiogroup"] label:has(input:checked) {
        background-color: rgba(16, 185, 129, 0.2) !important; border: 2px solid #10b981 !important;
    }

    .stButton > button, .stDownloadButton > button, div.stForm div.stButton > button { 
        background-color: #2d333b !important; color: #10b981 !important; 
        font-weight: 700 !important; border: 2px solid #10b981 !important;
        border-radius: 6px !important; width: 100% !important;
    }
    
    .stButton > button:hover, .stDownloadButton > button:hover {
        background-color: #3b424b !important; border-color: #ffffff !important; color: #ffffff !important;
    }

    .btn-eliminar-historial button {
        background-color: #ef4444 !important; color: white !important; border: none !important;
        padding: 5px !important; width: 40px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. BASE DE DATOS ---
def conectar_db():
    return sqlite3.connect('fiber_telecom.db', check_same_thread=False)

conn = conectar_db()
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS clientes (id TEXT PRIMARY KEY, nombre TEXT)')
# ACTUALIZACIÓN DE TABLA INVENTARIO PARA 2 PRECIOS
cursor.execute('''CREATE TABLE IF NOT EXISTS inventario 
                  (nombre TEXT PRIMARY KEY, cantidad INTEGER, minimo INTEGER, precio REAL, precio_especial REAL)''')
cursor.execute('CREATE TABLE IF NOT EXISTS ventas (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id TEXT, producto TEXT, cantidad INTEGER, monto REAL, pagado REAL, metodo TEXT, fecha TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS abonos (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER, monto_abono REAL, metodo_abono TEXT, fecha_abono TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS gastos (id INTEGER PRIMARY KEY AUTOINCREMENT, concepto TEXT, monto REAL, fecha TEXT)')

# Migración simple si la columna no existe
try:
    cursor.execute("ALTER TABLE inventario ADD COLUMN precio_especial REAL DEFAULT 0")
    conn.commit()
except:
    pass

conn.commit()

# --- 5. ACCESO Y NAVEGACIÓN ---
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center; color:#10b981;'>📡 FIBERTELECOM</h1>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        with st.form("login_form"):
            user = st.text_input("Usuario")
            pw = st.text_input("Contraseña", type="password")
            if st.form_submit_button("ACCEDER"):
                if user == "admin" and pw == "fiber2026":
                    st.session_state["autenticado"] = True
                    st.rerun()
                else: st.error("Acceso denegado")
    st.stop()

if "menu_option" not in st.session_state:
    st.session_state["menu_option"] = "🏠 Dashboard"

with st.sidebar:
    st.markdown('<div class="brand-container">📡 FIBERTELECOM</div>', unsafe_allow_html=True)
    st.markdown("---")
    opciones = ["🏠 Dashboard", "📦 Inventario", "🛒 Ventas", "👥 Clientes", "💸 Cobranza", "📉 Gastos", "📊 Historial"]
    sel = st.radio("Navegación", opciones, index=opciones.index(st.session_state["menu_option"]), key="sidebar_radio", on_change=lambda: st.session_state.update({"menu_option": st.session_state.sidebar_radio}), label_visibility="collapsed")
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🚪 CERRAR SESIÓN"):
        st.session_state["autenticado"] = False
        st.rerun()

opcion_actual = st.session_state["menu_option"]

# --- 6. SECCIONES ---
if opcion_actual == "🏠 Dashboard":
    st.markdown("### Dashboard")
    df_v = pd.read_sql("SELECT * FROM ventas", conn)
    df_a = pd.read_sql("SELECT * FROM abonos", conn)
    df_g = pd.read_sql("SELECT * FROM gastos", conn)
    v_total = df_v['monto'].sum() if not df_v.empty else 0
    cobrado = (df_v['pagado'].sum() if not df_v.empty else 0) + (df_a['monto_abono'].sum() if not df_a.empty else 0)
    gastos_tot = df_g['monto'].sum() if not df_g.empty else 0
    deuda_tot = v_total - cobrado
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Cobrado", f"${cobrado:,.0f}")
    c2.metric("Gastos", f"${gastos_tot:,.0f}")
    c3.metric("Deuda", f"${deuda_tot:,.0f}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns([1.5, 1]) 
    with g1:
        f1 = px.bar(x=["Cobrado", "Gastos"], y=[cobrado, gastos_tot], color=["Cobrado", "Gastos"], color_discrete_map={"Cobrado": "#10b981", "Gastos": "#ef4444"}, template="plotly_dark")
        f1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, height=300)
        st.plotly_chart(f1, use_container_width=True)
    with g2:
        f2 = px.pie(values=[cobrado, deuda_tot], names=["Cobrado", "Deuda"], hole=0.7, color_discrete_sequence=["#10b981", "#2d333b"], template="plotly_dark")
        f2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
        st.plotly_chart(f2, use_container_width=True)

elif opcion_actual == "📦 Inventario":
    st.title("📦 Inventario")
    col_add, col_del = st.columns(2)
    with col_add:
        st.subheader("Añadir / Editar")
        with st.form("f_inv"):
            n = st.text_input("Producto")
            p1 = st.number_input("Precio Normal", min_value=0.0)
            p2 = st.number_input("Precio Especial", min_value=0.0)
            s = st.number_input("Stock", min_value=0)
            m = st.number_input("Mínimo", min_value=0)
            if st.form_submit_button("💾 GUARDAR PRODUCTO"):
                cursor.execute("INSERT OR REPLACE INTO inventario VALUES (?,?,?,?,?)", (n, s, m, p1, p2))
                conn.commit(); st.rerun()
    with col_del:
        st.subheader("Eliminar")
        df_inv = pd.read_sql("SELECT nombre FROM inventario", conn)
        if not df_inv.empty:
            prod_borrar = st.selectbox("Seleccionar producto", df_inv['nombre'])
            if st.button("🗑️ ELIMINAR PRODUCTO"):
                cursor.execute("DELETE FROM inventario WHERE nombre = ?", (prod_borrar,))
                conn.commit(); st.rerun()
    st.dataframe(pd.read_sql("SELECT * FROM inventario", conn), use_container_width=True)

elif opcion_actual == "🛒 Ventas":
    st.title("🛒 Nueva Venta")
    df_cl = pd.read_sql("SELECT * FROM clientes", conn)
    df_in = pd.read_sql("SELECT * FROM inventario WHERE cantidad > 0", conn)
    
    if df_cl.empty or df_in.empty: 
        st.warning("Faltan clientes o inventario.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            cli = st.selectbox("Cliente", df_cl['id'] + " - " + df_cl['nombre'])
            pro = st.selectbox("Producto", df_in['nombre'])
        
        info = df_in[df_in['nombre'] == pro].iloc[0]
        
        with c2:
            tipo_p = st.radio("Tipo de Precio", ["Normal", "Especial"], horizontal=True)
            p_final = info['precio'] if tipo_p == "Normal" else info['precio_especial']
            can = st.number_input("Cantidad", 1, int(info['cantidad']))
        
        tot = p_final * can
        st.markdown(f"### TOTAL: :green[${tot:,.2f}] (Precio Unitario: ${p_final:,.2f})")
        
        with st.form("f_v"):
            met = st.selectbox("Método de Pago", ["Efectivo", "Transferencia", "Depósito", "Crédito"])
            abo = st.number_input("Monto Recibido / Inicial", 0.0, float(tot))
            confirmar_venta = st.form_submit_button("✅ CONFIRMAR VENTA")
            
            if confirmar_venta:
                fh = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("INSERT INTO ventas (cliente_id, producto, cantidad, monto, pagado, metodo, fecha) VALUES (?,?,?,?,?,?,?)", (cli.split(" - ")[0], pro, can, tot, abo, met, fh))
                cursor.execute("UPDATE inventario SET cantidad = cantidad - ? WHERE nombre = ?", (can, pro))
                conn.commit()
                st.session_state["venta_reciente"] = {
                    'id': cursor.lastrowid, 'fecha': fh, 'cliente_nombre': cli.split(" - ")[1], 
                    'producto': pro, 'cantidad': can, 'monto': tot
                }
                st.rerun()

elif opcion_actual == "👥 Clientes":
    st.title("👥 Clientes")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        with st.form("f_cli"):
            ic = st.text_input("ID / Cédula"); no = st.text_input("Nombre")
            if st.form_submit_button("👤 REGISTRAR CLIENTE"):
                cursor.execute("INSERT OR REPLACE INTO clientes VALUES (?,?)", (ic, no))
                conn.commit(); st.rerun()
    with col_c2:
        df_cli = pd.read_sql("SELECT id, nombre FROM clientes", conn)
        if not df_cli.empty:
            cli_borrar = st.selectbox("Borrar cliente", df_cli['id'] + " - " + df_cli['nombre'])
            if st.button("🗑️ ELIMINAR CLIENTE"):
                cursor.execute("DELETE FROM clientes WHERE id = ?", (cli_borrar.split(" - ")[0],))
                conn.commit(); st.rerun()
    st.dataframe(pd.read_sql("SELECT * FROM clientes", conn), use_container_width=True)

elif opcion_actual == "💸 Cobranza":
    st.title("💸 Cobranza Consolidada por Cliente")
    query_consolidada = """
    SELECT 
        c.id as 'ID Cliente',
        c.nombre as 'Nombre Cliente',
        SUM(v.monto) as 'Total Ventas',
        (SUM(v.pagado) + IFNULL((SELECT SUM(a.monto_abono) 
                                 FROM abonos a 
                                 JOIN ventas v2 ON a.venta_id = v2.id 
                                 WHERE v2.cliente_id = c.id), 0)) as 'Total Pagado'
    FROM clientes c
    JOIN ventas v ON c.id = v.cliente_id
    GROUP BY c.id
    """
    df_consolidado = pd.read_sql(query_consolidada, conn)
    df_consolidado['Deuda Pendiente'] = df_consolidado['Total Ventas'] - df_consolidado['Total Pagado']
    deudores = df_consolidado[df_consolidado['Deuda Pendiente'] > 0.1]
    st.dataframe(deudores, use_container_width=True)
    
    if not deudores.empty:
        st.markdown("---")
        st.subheader("Registrar Nuevo Abono")
        with st.form("f_abono_grupal"):
            cliente_sel = st.selectbox("Seleccionar Cliente para Abonar", 
                                       deudores['ID Cliente'] + " - " + deudores['Nombre Cliente'])
            c_id = cliente_sel.split(" - ")[0]
            monto_a = st.number_input("Monto del Abono", min_value=0.1)
            metodo_a = st.selectbox("Método", ["Efectivo", "Transferencia", "Depósito"])
            
            if st.form_submit_button("💰 APLICAR ABONO"):
                ventas_pendientes = pd.read_sql(f"""
                    SELECT id, (monto - (pagado + IFNULL((SELECT SUM(monto_abono) FROM abonos WHERE venta_id = ventas.id), 0))) as saldo
                    FROM ventas WHERE cliente_id = '{c_id}' AND saldo > 0.1 ORDER BY fecha ASC
                """, conn)
                monto_restante = monto_a
                for _, v_pend in ventas_pendientes.iterrows():
                    if monto_restante <= 0: break
                    pago_factura = min(monto_restante, v_pend['saldo'])
                    cursor.execute("INSERT INTO abonos (venta_id, monto_abono, metodo_abono, fecha_abono) VALUES (?,?,?,?)",
                                   (int(v_pend['id']), pago_factura, metodo_a, datetime.now().strftime("%Y-%m-%d")))
                    monto_restante -= pago_factura
                conn.commit()
                st.success(f"Abono de ${monto_a} aplicado correctamente.")
                st.rerun()

elif opcion_actual == "📉 Gastos":
    st.title("📉 Gastos")
    with st.form("f_gas"):
        con = st.text_input("Concepto"); mon = st.number_input("Monto")
        if st.form_submit_button("📉 GUARDAR GASTO"):
            cursor.execute("INSERT INTO gastos (concepto, monto, fecha) VALUES (?,?,?)", (con, mon, datetime.now().strftime("%Y-%m-%d")))
            conn.commit(); st.rerun()
    st.dataframe(pd.read_sql("SELECT * FROM gastos", conn), use_container_width=True)

elif opcion_actual == "📊 Historial":
    st.title("📊 Historial de Ventas")
    query_historial = """
    SELECT v.id, v.fecha, v.producto, v.cantidad, v.monto, c.nombre as 'cliente_nombre', v.metodo
    FROM ventas v
    JOIN clientes c ON v.cliente_id = c.id
    ORDER BY v.id DESC
    """
    df_h = pd.read_sql(query_historial, conn)
    
    if not df_h.empty:
        h_cols = st.columns([0.5, 1.2, 1.8, 0.8, 1.2, 2.0, 1.2, 0.8])
        h_cols[0].write("**ID**"); h_cols[1].write("**Fecha**"); h_cols[2].write("**Producto**")
        h_cols[3].write("**Cant.**"); h_cols[4].write("**Monto**"); h_cols[5].write("**Cliente**")
        h_cols[6].write("**Método**"); h_cols[7].write("**Acción**")
        st.markdown("---")
        
        for index, row in df_h.iterrows():
            r_cols = st.columns([0.5, 1.2, 1.8, 0.8, 1.2, 2.0, 1.2, 0.8])
            r_cols[0].write(f"{row['id']}")
            r_cols[1].write(f"{row['fecha']}")
            r_cols[2].write(f"{row['producto']}")
            r_cols[3].write(f"{row['cantidad']}")
            r_cols[4].write(f"${row['monto']:,.2f}")
            r_cols[5].write(f"{row['cliente_nombre']}")
            r_cols[6].write(f"{row['metodo']}")
            with r_cols[7]:
                st.markdown('<div class="btn-eliminar-historial">', unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{row['id']}"):
                    cursor.execute("UPDATE inventario SET cantidad = cantidad + ? WHERE nombre = ?", (row['cantidad'], row['producto']))
                    cursor.execute("DELETE FROM ventas WHERE id = ?", (row['id'],))
                    cursor.execute("DELETE FROM abonos WHERE venta_id = ?", (row['id'],))
                    conn.commit(); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        id_sel = st.selectbox("Seleccione ID para descargar comprobante", df_h['id'])
        v_data = df_h[df_h['id'] == id_sel].iloc[0].to_dict()
        st.download_button(f"📥 PDF #{id_sel}", generar_factura_pdf(v_data), f"Factura_{id_sel}.pdf", "application/pdf")

    else: st.info("No hay ventas registradas.")
import streamlit as st

# --- BOTÓN DE RESCATE DE DATOS ---
# Asegúrate de que estas líneas estén pegadas a la izquierda (sin espacios)
try:
    with open("tu_archivo.db", "rb") as file: # <--- CAMBIA ESTO por el nombre de tu archivo .db
        st.download_button(
            label="🟢 DESCARGAR DATOS REALES",
            data=file,
            file_name="datos_nube_actualizados.db",
            mime="application/octet-stream"
        )
except FileNotFoundError:
    st.error("No se encontró el archivo .db. Verifica el nombre.")"
    )



