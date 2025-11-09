# 🔬 Robot Physicist: Explorador Interactivo de Parámetros de ATLAS (H $\to \gamma\gamma$)

**Autor:** [Tu Nombre / Nombre de la Organización]
**Licencia:** **Creative Commons CC0 (Datos) & MIT (Código)**
[![GitHub Workflow Status - Analysis](https://github.com/tu-usuario/tu-repo/actions/workflows/analysis.yaml/badge.svg)](https://github.com/tu-usuario/tu-repo/actions/workflows/analysis.yaml)

---

## 🌟 Introducción

Este proyecto es una herramienta de **Análisis de Física de Partículas** automatizada. Procesa datos abiertos del experimento **ATLAS** del CERN, enfocándose en la búsqueda y estudio de eventos de **dos fotones** ($\gamma\gamma$).

El proceso de análisis completo se ejecuta de forma reproducible mediante **GitHub Actions**, instalando las librerías nativas de Python (`uproot`, `awkward`, `numpy`, etc.) necesarias para manejar los archivos de datos de física (`.root`). Los resultados (gráficos y estadísticas) se publican en una interfaz web simple para su exploración interactiva.

---

## 🧐 Marco Teórico: El Bosón de Higgs y $\gamma\gamma$

El análisis se centra en el canal de decaimiento del **Bosón de Higgs** ($H \to \gamma\gamma$). Este canal es clave para la física de partículas.

El script de análisis (`Scripts/analysis.py`) aplica **criterios de selección (cuts)** rigurosos para aislar los eventos de interés a partir del archivo de datos ROOT (`data_D.GamGam.root`):

* **Selección de Partículas:** Identificación estricta (`photon_isTightID`) y restricciones de pseudorapidez ($\eta$).
* **Momento Transverso ($p_T$):** Ambos fotones deben tener un $p_T$ mayor a un umbral mínimo configurable (10-100 GeV).
* **Aislamiento:** Se verifica que los fotones estén aislados para mitigar el ruido de fondo.
* **Cálculo de Variables:** Utiliza las librerías de Python para el manejo de vectores (`awkward`, `numpy`) para calcular dinámicamente la **Masa Invariante ($m_{\gamma\gamma}$)**, el **$p_T$ Sumado** y otros observables cruciales.

La herramienta web permite variar el **umbral mínimo de $p_T$** para estudiar cómo afecta la distribución de estas variables.

---

## ⚙️ Flujo de Trabajo CI/CD: Automatización con GitHub Actions

El núcleo de la automatización reside en el archivo `.github/workflows/analysis.yaml`. Este flujo de trabajo garantiza que el análisis se ejecute y los resultados se actualicen automáticamente con cada cambio en el código.

### **✨ Enfoque en `analysis.yaml` (Flujo de Ejecución de Python)**

El *workflow* `analysis.yaml` se ejecuta en un ambiente Ubuntu y se encarga de todo, **sin depender de un contenedor Docker externo**, asegurando que las librerías de física necesarias estén disponibles.

| Paso | Descripción | Código Clave |
| :--- | :--- | :--- |
| **Setup Python 3.10** | Configura el ambiente de Python en la máquina virtual. | `uses: actions/setup-python@v3` |
| **Install Dependencies** | Instala todas las librerías necesarias para el análisis (incluyendo `uproot`, `awkward`, `matplotlib`, `wget`) definidas en `requirements.txt`. | `pip install -r requirements.txt` |
| **Run Analysis** | Ejecuta el script principal (`Scripts/analysis.py`) que descarga los datos, aplica los cortes, realiza los cálculos vectoriales y genera todos los archivos de resultados (`.png` y `.js`). | `python Scripts/analysis.py` |
| **Commit and Push Changes** | Este paso es **crucial**. Sube los resultados generados automáticamente (`.png`, `.js`) de vuelta al repositorio, haciendo que la interfaz web quede actualizada y refleje el último análisis. | `git commit -m "Auto update from GitHub Action"` |

### Flujo de Datos

1.  **Datos:** El script descarga el archivo ROOT de la URL especificada en `url.txt`.
2.  **Procesamiento:** `analysis.py` (usando `uproot` y `awkward`) lee y procesa los datos.
3.  **Salida:** Los gráficos y las estadísticas descriptivas (JSON incrustado en `.js`) se guardan en `data_D.GamGam/`.
4.  **Web:** La interfaz (`index.html` y `js/frontpage.js`) carga dinámicamente estos archivos de salida para la exploración del usuario.

---

## 💻 Uso Local y Visualización

Para ejecutar el análisis manualmente o para visualizar la interfaz web:

### Requisitos

* Python 3.10+
* Librerías de `requirements.txt`.

### Instalación

```bash
# Instalar las dependencias de Python
pip install -r requirements.txt
