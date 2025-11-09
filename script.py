import uproot
import awkward as ak
import numpy as np
import matplotlib.pyplot as plt
import os
import json
# --- Open the ATLAS open data ROOT file ---
# You can use a local file if you’ve downloaded it


with open("url.txt","r") as f:
    url = f.read()


file = uproot.Open(url)
#file = uproot.open("./data_D.GamGam.root")
tree = file["mini"]



# --- Load branches as Awkward Arrays ---

branches = [
    "trigP",
    "photon_pt", "photon_eta", "photon_phi", "photon_E",
    "photon_isTightID", "photon_ptcone30", "photon_etcone20", "photon_n"
]
events = tree.arrays(branches)

# Convert MeV to GeV
events["photon_pt"] = events["photon_pt"]
events["photon_E"] = events["photon_E"] 

# --- Apply trigger condition ---
events = events[events.trigP]

# --- Select "good" photons (same cuts as your ROOT code) ---
mask_tight = events.photon_isTightID
mask_pt = events.photon_pt > 10.0  # 10 GeV
mask_eta = (abs(events.photon_eta) < 2.37) & (
    (abs(events.photon_eta) < 1.37) | (abs(events.photon_eta) > 1.52)
)
good_photon_mask = mask_tight & mask_pt & mask_eta

# Apply mask
n_good = ak.sum(good_photon_mask, axis=1)
two_photon_events = events[n_good == 2]


# --- Isolation conditions ---
iso_mask = (
    (two_photon_events.photon_ptcone30 / two_photon_events.photon_pt < 0.065)
    & (two_photon_events.photon_etcone20 / two_photon_events.photon_pt < 0.065)
)
two_photon_events = two_photon_events[ak.all(iso_mask, axis=1)]
two_photon_events = two_photon_events[ak.num(two_photon_events.photon_pt) == 2]

pt = ak.to_numpy(two_photon_events.photon_pt)/1000.0

# Define your threshold in GeV
GeV_min = 50.0

# --- Create a mask that selects only events where both photons have pt > GeV_min ---
# ak.all checks the condition along the photon axis (axis=1)
mask_two_high_pt = ak.all(pt > GeV_min, axis=1)

# --- Apply mask to the original awkward array ---
selected_events = two_photon_events[mask_two_high_pt]
two_photon_events = selected_events

# --- Helper function: run full analysis for a given GeV_min ---
def analyze_for_threshold(GeV_min):
    output_dir = f"photon_analysis_outputs/photon_{GeV_min:.0f}GeV"
    os.makedirs("./", exist_ok=True)

    # --- Apply pT selection ---
    pt = ak.to_numpy(two_photon_events.photon_pt) / 1000.0  # MeV → GeV
    mask_two_high_pt = ak.all(pt > GeV_min, axis=1)
    selected_events = two_photon_events[mask_two_high_pt]

    if len(selected_events) == 0:
        #print(f"⚠️ No events above {GeV_min} GeV — skipping.")
        return

    # --- Extract variables ---
    pt = ak.to_numpy(selected_events.photon_pt) / 1000.0
    eta = ak.to_numpy(selected_events.photon_eta)
    phi = ak.to_numpy(selected_events.photon_phi)
    E   = ak.to_numpy(selected_events.photon_E) / 1000.0

    # --- Convert to Cartesian components ---
    px = pt * np.cos(phi)
    py = pt * np.sin(phi)
    pz = pt * np.sinh(eta)

    # --- Sum components event-wise ---
    px_sum = np.sum(px, axis=1)
    py_sum = np.sum(py, axis=1)
    pz_sum = np.sum(pz, axis=1)
    E_sum  = np.sum(E, axis=1)

    # --- Derived variables ---
    pt_sum = np.sqrt(px_sum**2 + py_sum**2)
    delta_eta = eta[:, 0] - eta[:, 1]
    delta_phi = np.arctan2(np.sin(phi[:, 0] - phi[:, 1]),
                           np.cos(phi[:, 0] - phi[:, 1]))
    masses = np.sqrt(np.maximum(E_sum**2 - (px_sum**2 + py_sum**2 + pz_sum**2), 0))

    # --- Organize all variables ---
    variables = {
        "pt_sum": pt_sum,
        "delta_eta": delta_eta,
        "delta_phi": delta_phi,
        "E_sum": E_sum,
        "masses": masses
    }
    labels = {
        "pt_sum": "$p_T$ [GeV]",
        "delta_eta": "$\\Delta\\eta$",
        "delta_phi": "$\\Delta\\phi$",
        "E_sum": "Energy [GeV]",
        "masses": "Invariant mass $m_{\\gamma\\gamma}$ [GeV]"
    }

    # --- Compute statistics for all variables ---
    stats_dict = {name: describe(arr) for name, arr in variables.items()}

    # --- Save JavaScript file with all stats in one object ---
    js_path = os.path.join("./", f"photon_{GeV_min:.0f}GeV_stats.js")
    js_obj = {name: stats for name, stats in stats_dict.items()}
    with open(js_path, "w") as f:
        f.write("// Auto-generated photon statistics\n\n")
        f.write(f"const photon_{GeV_min:.0f}GeV_stats = ")
        json.dump(js_obj, f, indent=2)
        f.write(";\n")
    print(f"✅ Saved JS stats for {GeV_min} GeV → {js_path}")

    # --- Plot and save each histogram individually ---
    for name, arr in variables.items():
        label = labels[name]
        low, high = np.percentile(arr, [2, 98])  # clip outliers
        bins = np.histogram_bin_edges(arr, bins="fd", range=(low, high))

        plt.figure(figsize=(6, 4))
        plt.hist(arr, bins=bins, histtype="step", color="blue", linewidth=1.5)
        plt.xlabel(label)
        plt.ylabel("Events")
        plt.title(f"Distribution of {label} ({GeV_min:.0f} GeV cut)")
        plt.grid(True)
        plt.tight_layout()

        safe_name = name.replace("$", "").replace("\\", "").replace("{", "").replace("}", "").replace(" ", "_")
        filename = f"photon_{GeV_min:.0f}GeV_distribution_{safe_name}.png"
        plt.savefig(os.path.join("./", filename))
        plt.close()



# --- MAIN LOOP ---
for GeV_min in range(10, 105, 5):  # 10, 15, 20, ..., 100
    analyze_for_threshold(GeV_min)

