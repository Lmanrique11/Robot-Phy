#  Robot Physicist: Explorador Interactivo de Parámetros de ATLAS (H $\to \gamma\gamma$)

**Autor: Tulio Muñoz Magaña, Jonatan Garcias y Leonardo Manrique  / Coafina 2025**

**Licencia:** **Creative Commons CC0 (Datos) & MIT (Código)**

---

## Demostración del Proyecto

Mira este video para entender rápidamente el flujo de trabajo, cómo se ejecuta el análisis en la nube y cómo funciona la interfaz interactiva para explorar los resultados de la física.

**https://youtu.be/BHWIh_kFpGM**

Puedes ver la interfaz interactiva con los resultados del análisis y probar los diferentes cortes de $p_T$ directamente en la siguiente dirección:

https://lmanrique11.github.io/Robot-Phy/

##  Introducción

Este proyecto es una herramienta de **Análisis de Física de Partículas** automatizada. Procesa datos abiertos del experimento **ATLAS** del CERN, enfocándose en la búsqueda y estudio de eventos de **dos fotones** ($\gamma\gamma$).

El proceso de análisis completo se ejecuta de forma reproducible mediante **GitHub Actions**, instalando las librerías nativas de Python (`uproot`, `awkward`, `numpy`, etc.) necesarias para manejar los archivos de datos de física (`.root`). Los resultados (gráficos y estadísticas) se publican en una interfaz web simple para su exploración interactiva.

---
## Marco Teorico: Análisis de Fotones en ATLAS

El objetivo principal del análisis es estudiar los eventos en los que la colisión de protones produce un sistema de **dos fotones** ($\gamma\gamma$), crucial para la búsqueda del **Bosón de Higgs ($H$)**.

### El Bosón de Higgs y la Masa Invariante 🔬

Si un evento $\gamma\gamma$ proviene de un Bosón de Higgs, la **masa invariante ($m_{\gamma\gamma}$)** del sistema debe ser aproximadamente **$125\text{ GeV}$**. El análisis calcula esta variable dinámicamente.

### La Necesidad de Cortes (Cuts) ✂️

Para aislar la señal de eventos raros del inmenso **fondo** de otras colisiones, el script (`Scripts/analysis.py`) aplica rigurosos **cortes de selección**:

| Criterio | Variable Clave | Justificación Física |
| :--- | :--- | :--- |
| **Identificación Estricta** | `photon_isTightID` | Asegura que la señal registrada sea un fotón de alta calidad. |
| **Energía Mínima** | **$p_T > [10-100]\text{ GeV}$** | El **Momento Transverso ($p_T$)** alto reduce drásticamente el fondo de fotones de baja energía. |
| **Aislamiento** | `ptcone30`, `etcone20` | Los fotones de la señal son **limpios**. Este corte elimina fotones rodeados de otras partículas, minimizando el ruido. |

Al ajustar el **umbral mínimo de $p_T$** en la interfaz, el usuario simula la **optimización de cortes** que realizan los físicos para maximizar la visibilidad de la señal.


---

##  Flujo de Trabajo CI/CD: Automatización con GitHub Actions

El núcleo de la automatización reside en el archivo `.github/workflows/analysis.yaml`. Este flujo de trabajo garantiza que el análisis se ejecute y los resultados se actualicen automáticamente con cada cambio en el código.

###  Enfoque en `analysis.yaml` (Flujo de Ejecución de Python)



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

##  Uso Local y Visualización

Para ejecutar el análisis manualmente o para visualizar la interfaz web:

### Requisitos

* Python 3.10+
* Librerías de `requirements.txt`.

### Instalación

```bash
# Instalar las dependencias de Python
pip install -r requirements.txt
