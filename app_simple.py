import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuración de la página
st.set_page_config(layout="wide", page_title="Capital Allocation Optimizer", page_icon="📊")
st.title("Strategic Capital Allocation Optimizer (Académico)")

st.write("Modelo simplificado de frontera eficiente para asignación de capital entre proyectos.")

# Barra lateral para parámetros
st.sidebar.header("Parámetros de Configuración")
simulaciones = st.sidebar.slider("Simulaciones Monte Carlo", 100, 5000, 1000, 100)
capital_total = st.sidebar.number_input("Capital disponible ($)", value=1000000.0, step=50000.0)

# Carga de archivo
archivo = st.file_uploader("Cargar archivo Excel con los proyectos", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)

    # Validar que las columnas requeridas existan
    columnas_requeridas = ["Proyecto", "CAPEX", "ROI esperado", "Volatilidad"]
    faltantes = [c for c in columnas_requeridas if c not in df.columns]

    if faltantes:
        st.error(f"❌ Error: El archivo no contiene las siguientes columnas requeridas: {faltantes}")
    else:
        st.subheader("📋 Datos de los Proyectos Cargados")
        st.dataframe(df.style.format({
            "CAPEX": "${:,.2f}",
            "ROI esperado": "{:.2%}",
            "Volatilidad": "{:.2%}"
        }))

        # Extraer variables para la simulación
        retornos = df["ROI esperado"].values
        riesgos = df["Volatilidad"].values
        n = len(df)

        resultados = []
        pesos_guardados = []

        # Simulación Monte Carlo
        for _ in range(simulaciones):
            pesos = np.random.random(n)
            pesos /= pesos.sum()  # Garantiza que sumen 100%

            retorno = np.dot(pesos, retornos)
            # Nota: Asume correlación cero entre proyectos para simplificar
            riesgo = np.sqrt(np.sum((pesos * riesgos) ** 2))
            sharpe = retorno / max(riesgo, 1e-6)

            resultados.append([retorno, riesgo, sharpe])
            pesos_guardados.append(pesos)

        # Crear DataFrame con los resultados de la simulación
        frontera = pd.DataFrame(resultados, columns=["Retorno", "Riesgo", "Sharpe"])
        idx = frontera["Sharpe"].idxmax()
        mejores_pesos = pesos_guardados[idx]

        # Gráfico de la Frontera Eficiente
        st.subheader("📈 Frontera Eficiente (Simulación)")
        fig = px.scatter(
            frontera,
            x="Riesgo",
            y="Retorno",
            color="Sharpe",
            labels={"Riesgo": "Volatilidad del Portafolio", "Retorno": "ROI Esperado"},
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Resultados de asignación
        st.subheader("🎯 Asignación de Capital Recomendada (Max Sharpe)")
        
        asignacion = pd.DataFrame({
            "Proyecto": df["Proyecto"],
            "Peso %": mejores_pesos * 100,
            "Capital Asignado": mejores_pesos * capital_total
        })

        st.dataframe(asignacion.style.format({
            "Peso %": "{:.2f}%",
            "Capital Asignado": "${:,.2f}"
        }))

        # Métricas destacadas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sharpe Máximo obtenido", round(frontera.loc[idx, "Sharpe"], 2))
        with col2:
            st.metric("ROI Esperado del Portafolio", f"{round(frontera.loc[idx, 'Retorno'] * 100, 2)}%")
        with col3:
            st.metric("Volatilidad del Portafolio", f"{round(frontera.loc[idx, 'Riesgo'] * 100, 2)}%")
else:
    st.info("💡 Por favor, carga un archivo Excel para iniciar la simulación.")