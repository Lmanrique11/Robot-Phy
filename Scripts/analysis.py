import os
import sys
import numpy as np
import uproot
import awkward as ak
import matplotlib.pyplot as plt
import json
import wget

# === Helper: Load URLs ===

def load_urls(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        return [line.strip() for line in f if line.strip()]

# === Helper: Save URLs ===
def append_url(file_path, url):
    with open(file_path, "a") as f:
        f.write(url + "\n")

# === Physics Analysis for a Single File ===
def process_root_file(url, output_dir):
    print(f"\n🔹 Processing: {url}")

    # Create output directories
    plots_dir = os.path.join(output_dir, "plots")
    js_dir = os.path.join(output_dir, "JavaScript")
    os.makedirs(plots_dir, exist_ok=True)
    os.makedirs(js_dir, exist_ok=True)

    # --- Load ROOT data --
    filename = wget.download(url, out = "./")
    tree = uproot.open(filename)["mini"]
    branches = [
        "trigP",
        "photon_pt", "photon_eta", "photon_phi", "photon_E",
        "photon_isTightID", "photon_ptcone30", "photon_etcone20", "photon_n"
    ]
    events = tree.arrays(branches)

    # Convert to GeV
    events["photon_pt"] = events["photon_pt"] / 1000.0
    events["photon_E"] = events["photon_E"] / 1000.0

    # Apply trigger
    events = events[events.trigP]

    # Photon selection
    mask_tight = events.photon_isTightID
    mask_pt = events.photon_pt > 10.0
    mask_eta = (abs(events.photon_eta) < 2.37) & (
        (abs(events.photon_eta) < 1.37) | (abs(events.photon_eta) > 1.52)
    )
    good_mask = mask_tight & mask_pt & mask_eta
    events = events[good_mask]
    events = events[ak.num(events.photon_pt) == 2]

    # Isolation
    iso_mask = (
        (events.photon_ptcone30 / events.photon_pt < 0.065)
        & (events.photon_etcone20 / events.photon_pt < 0.065)
    )
    events = events[ak.all(iso_mask, axis=1)]

    # Extract variables
    pt = ak.to_numpy(events.photon_pt)
    eta = ak.to_numpy(events.photon_eta)
    phi = ak.to_numpy(events.photon_phi)
    E = ak.to_numpy(events.photon_E)

    # Loop over GeV thresholds
    for GeV_min in range(10, 105, 5):
        mask = (pt[:, 0] > GeV_min) & (pt[:, 1] > GeV_min)
        if not np.any(mask):
            continue

        pt_sel, eta_sel, phi_sel, E_sel = pt[mask], eta[mask], phi[mask], E[mask]

        px = pt_sel * np.cos(phi_sel)
        py = pt_sel * np.sin(phi_sel)
        pz = pt_sel * np.sinh(eta_sel)
        px_sum, py_sum, pz_sum, E_sum = map(lambda x: np.sum(x, axis=1), (px, py, pz, E_sel))

        pt_sum = np.sqrt(px_sum**2 + py_sum**2)
        delta_eta = eta_sel[:, 0] - eta_sel[:, 1]
        delta_phi = np.arctan2(np.sin(phi_sel[:, 0] - phi_sel[:, 1]),
                               np.cos(phi_sel[:, 0] - phi_sel[:, 1]))
        masses = np.sqrt(np.maximum(E_sum**2 - (px_sum**2 + py_sum**2 + pz_sum**2), 0))

        variables = {
            "pt_sum_GeV": pt_sum,
            "delta_eta": delta_eta,
            "delta_phi": delta_phi,
            "E_sum_GeV": E_sum,
            "mass_GeV": masses
        }

        # Describe function
        def describe(arr):
            return {
                "len": len(arr),
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "median": float(np.median(arr)),
                "q1": float(np.percentile(arr, 25)),
                "q3": float(np.percentile(arr, 75)),
            }

        stats = {k: describe(v) for k, v in variables.items()}

        # Save stats as JS
        js_path = os.path.join(js_dir, f"photon_{GeV_min}GeV_stats.js")
        with open(js_path, "w") as f:
            f.write(f"const photon_{GeV_min}_stats = {json.dumps(stats, indent=2)};\n")

        # Plot histograms
        for name, arr in variables.items():
            low, high = np.percentile(arr, [2, 98])
            bins = np.histogram_bin_edges(arr, bins="fd", range=(low, high))
            plt.figure(figsize=(6, 4))
            plt.hist(arr, bins=bins, histtype="step", color="blue", linewidth=1.5)
            plt.xlabel(name)
            plt.ylabel("Events")
            plt.title(f"{name} Distribution (>{GeV_min} GeV)")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(plots_dir, f"{name}_{GeV_min}GeV.png"))
            plt.close()

        print(f"✅ Done {GeV_min} GeV ({len(masses)} events)")

# === Main Script ===
if __name__ == "__main__":
    urls_file = "./url.txt"
    aux_file = "./url_aux.txt"

    urls = load_urls(urls_file)
    done_urls = load_urls(aux_file)
    print(len(urls))
    for url in urls:
        if url in done_urls:
            print(f"⚠️ Skipping already processed URL: {url}")
            continue

        # Folder name based on file
        filename = os.path.basename(url).replace(".root", "")
        output_dir = os.path.join(".", filename)

        process_root_file(url, output_dir)
        append_url(aux_file, url)

    print("\n🎉 All files processed successfully.")
