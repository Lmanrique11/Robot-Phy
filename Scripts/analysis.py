import json
import numpy as np
import uproot
import awkward as ak
from atlasopenmagic import download
import os

# --- Lógica de la Física (H -> gamma gamma) ---

def calcular_masa_invariante_gamma_gamma(data, pt_min_corte, eta_max_corte):
    """
    Simula la selección y el cálculo de Masa Invariante para el decaimiento H -> gamma gamma (dos fotones).
    Usa el dataset de muones de ejemplo como sustituto de los fotones, aplicando el corte pT_min.
    """
    
    # Se recomienda usar 'el_' (electrones) como sustituto de 'gamma' (fotones)
    # en la data abierta de ATLAS, ya que comparten más características que los muones.
    # Usaremos 'mu_' aquí para asegurar que el dataset de ejemplo sea compatible.
    
    # 1. Cargar las variables de los muones
    leptons = ak.zip({
        "pt": data['mu_pt'],
        "eta": data['mu_eta'],
        "phi": data['mu_phi'],
        "E": data['mu_E']
    })
    
    # 2. Aplicar el corte de pT parametrizado y el corte base de eta
    # Nota: Los cortes están en MeV.
    corte_pt = (leptons.pt > pt_min_corte)
    corte_eta = (np.abs(leptons.eta) < eta_max_corte)
    leptons_filtrados = leptons[corte_pt & corte_eta]
    
    # 3. Requerir al menos dos partículas después de los cortes
    eventos_validos = (ak.num(leptons_filtrados) >= 2)
    leptons_validos = leptons_filtrados[eventos_validos]
    
    # 4. Formar pares (simulando los dos fotones) y calcular la Masa Invariante
    pares = ak.combinations(leptons_validos, 2, fields=["p1", "p2"])
    
    # Fórmula de la Masa Invariante (M^2 = (E1+E2)^2 - |p1+p2|^2)
    # Nota: Para una implementación completa y precisa en Python, se recomienda la librería `vector`.
    # Aquí usamos una aproximación basada en la suma de las magnitudes al cuadrado:
    masa_invariante_aprox = np.sqrt(
        (pares.p1.E + pares.p2.E)**2 - (
            (pares.p1.pt * np.cos(pares.p1.phi) + pares.p2.pt * np.cos(pares.p2.phi))**2 + # Suma de Px
            (pares.p1.pt * np.sin(pares.p1.phi) + pares.p2.pt * np.sin(pares.p2.phi))**2 + # Suma de Py
            (pares.p1.pt * np.sinh(pares.p1.eta) + pares.p2.pt * np.sinh(pares.p2.eta))**2 # Suma de Pz
        )
    )

    return ak.flatten(masa_invariante_aprox)


# --- Script Principal del Robot ---

def run_analysis():
    # 1. Leer la configuración de settings.json
    try:
        with open('settings.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: No se encontró settings.json.")
        exit(1)

    pt_config = config['analysis_parameters']
    base_config = config.get('CORTES_BASE', {})
    
    # 2. Manejo Flexible: Calcular el número de corridas a partir del paso (Tu Mejora)
    pt_inicio = pt_config['pt_min']
    pt_fin = pt_config['pt_max']
    pt_step_definido = pt_config.get('pt_step')

    # --- Lógica de Cálculo Flexible ---
    if pt_step_definido is None or pt_step_definido <= 0:
        # 2a. Si el usuario no define el paso, usamos un paso por defecto (ej., 2500 MeV = 2.5 GeV)
        pt_step_calculado = 2500 
        print(f"⚠️ pT_step no definido. Usando un paso por defecto de {pt_step_calculado} MeV.")
    else:
        pt_step_calculado = pt_step_definido

    # Generar la lista de cortes de pT
    # Usamos un pequeño margen para asegurar que el pt_max sea incluido
    cortes_pt = np.arange(pt_inicio, pt_fin + pt_step_calculado / 2, pt_step_calculado)
    num_corridas = len(cortes_pt)
    
    print(f"✅ Rango explorado: {pt_inicio/1000} a {pt_fin/1000} GeV. Paso: {pt_step_calculado/1000} GeV.")
    print(f"✅ Total de corridas a ejecutar (calculado): {num_corridas}.")
    
    # Crear la carpeta results si no existe
    os.makedirs('results', exist_ok=True)

    # 3. Descargar datos 
    print("⏳ Descargando y cargando datos del CERN (mc_361106_Zee)...")
    try:
        archivo_root_path = download("mc_361106_Zee", 2017) 
        data = uproot.open(archivo_root_path)['mini']
    except Exception as e:
        print(f"Error en la descarga/lectura de datos: {e}")
        # En un sistema automatizado, es mejor fallar aquí
        exit(1)


    # 4. Bucle de ejecución y consolidación
    resultados_consolidados = []
    print(f"🔬 Ejecutando {num_corridas} análisis...")
    
    # Definir cortes de histograma desde config (si existen)
    bins = base_config.get('NUM_BINES', 50)
    rango = [base_config.get('MASA_INVARIANTE_MIN', 50000), base_config.get('MASA_INVARIANTE_MAX', 170000)]
    eta_max = base_config.get('ETA_MAX', 2.5)
    
    for i, corte_pt_actual in enumerate(cortes_pt):
        # 4a. Ejecutar la física con el corte actual
        masa_invariante = calcular_masa_invariante_gamma_gamma(
            data, 
            pt_min_corte=corte_pt_actual, 
            eta_max_corte=eta_max
        )

        # 4b. Calcular el histograma
        counts, edges = np.histogram(masa_invariante, bins=bins, range=rango)
        
        # 4c. Consolidar el resultado
        resultados_consolidados.append({
            "run_id": i + 1,
            "corte_pt": float(corte_pt_actual),
            "counts": counts.tolist(),
            "edges": edges.tolist(),
            "num_eventos": int(np.sum(counts)) 
        })
        
        if (i + 1) % 10 == 0 or i == num_corridas - 1:
            print(f"   -> Corrida {i+1}/{num_corridas} completada con pT_min = {corte_pt_actual/1000:.2f} GeV.")

    # 5. Guardar el resumen consolidado (para el Dashboard)
    output_filename = config['output_file']
    
    final_output = {
        "metadata": {
            "title": config['analysis_name'],
            "eje_x_title": f"Masa Invariante ({config['units']['pt_min']})",
            "eje_y_title": "Eventos / Bin",
            "pt_range_tested": [pt_inicio, pt_fin],
            "pt_step_used": pt_step_calculado,
            "num_steps": num_corridas
        },
        "histograms": resultados_consolidados
    }
    
    with open(output_filename, 'w') as f:
        json.dump(final_output, f, indent=4)
        
    print(f"✅ Análisis parametrizado completado. Resumen guardado en {output_filename}")


if __name__ == '__main__':
    # Este bloque asegura que las configuraciones base existan antes de ejecutar
    try:
        with open('settings.json', 'r') as f:
            settings_data = json.load(f)
        
        if 'CORTES_BASE' not in settings_data:
            settings_data['CORTES_BASE'] = {
                "ETA_MAX": 2.5,
                "MASA_INVARIANTE_MIN": 50000,
                "MASA_INVARIANTE_MAX": 170000,
                "NUM_BINES": 50
            }
            with open('settings.json', 'w') as f:
                json.dump(settings_data, f, indent=4)
                
    except Exception as e:
        # Esto previene que el robot falle si el settings.json no es válido
        print(f"Error al verificar/ajustar settings.json: {e}")
        exit(1)
        
    run_analysis()
