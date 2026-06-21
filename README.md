# Varaha Plantation Model Portal

A GIS-powered field tool for visualising and validating plantation layouts on enrolled farmer plots (kyaaris) across Andhra Pradesh and Tamil Nadu.

---

## Business Context

Varaha enrolls smallholder farmers into carbon sequestration programmes. Each farmer's land parcel — a **kyaari** — is surveyed in the field, digitised as a GPS polygon, and assigned a **plantation model** that specifies which tree species to plant, at what spacing, and in what spatial pattern.

Before planting begins, field surveyors need to:
1. Verify the GPS polygon is accurate and the area is usable
2. Confirm the correct plantation model is assigned for the plot size and species mix
3. Estimate how many trees of each species will actually fit given the real polygon shape
4. Use these numbers to plan nursery sourcing and on-ground staking

This portal replaces manual estimation (spreadsheets + mental geometry) with a live satellite map that shows exact tree positions computed from the real polygon.

---

## What the Tool Does

| Capability | Detail |
|---|---|
| Load real kyaari data | Parses a KML export from the Varaha backend (828 kyaaris, May–June 2026) |
| Search | Filter by kyaari ID, farmer name, village, or district |
| Auto-assign model | Matches the KML species list to the best-fit plantation model automatically |
| Visualise on satellite | Plots every tree as a dot on Google Maps satellite imagery at real GPS coordinates |
| Count trees | Shows species-by-species placed count that exactly equals the dots on the map |
| Model comparison | Surveyor can switch model to see how the layout changes for the same plot |

---

## Plantation Models

13 models are supported, derived from the South India Multispecies Plantation specifications:

| Model | Type | Species | Size |
|---|---|---|---|
| M1 | Boundary + Alley Block | Mango · Red Sanders · Coconut | > 0.8 ha |
| M2 | Boundary + Alley Block (long-edge) | Mango · Red Sanders · Coconut | > 0.8 ha |
| M3 | Boundary + Equal Block (1:1) | Mango · Cashew · Teak | ≤ 0.8 ha |
| M4 | Boundary + Block (3:1) | Mango · Cashew · Teak | ≤ 0.8 ha |
| M5 | Boundary + Equal Block (1:1) | Mango · Sapota · Red Sanders | ≤ 0.8 ha |
| M6 | Boundary + Block (3:1) | Mango · Sapota · Teak | ≤ 0.8 ha |
| M7 | Boundary + Equal Block (1:1) | Mango · Jamun · Teak | ≤ 0.8 ha |
| M8 | Boundary + Block (2:1) | Mango · Jamun · Red Sanders | ≤ 0.8 ha |
| M9 | Three-Zone Block | Jackfruit · Sapota · Jamun | > 0.8 ha |
| M10 | Coconut Edge + Block (3:1) | Coconut · Jackfruit · Jamun | > 0.8 ha |
| M11 | Coconut Edge + Block (2:1) | Coconut · Jackfruit · Sapota | > 0.8 ha |
| M12 | Three-Zone Block | Mango · Jackfruit · Jamun | > 0.8 ha |
| M13 | Coconut Edge + Equal Block | Coconut · Jackfruit · Citrus | > 0.8 ha |

---

## Placement Algorithm — In Depth

The algorithm works entirely in **relative metre coordinates** anchored at the polygon centroid, then converts back to lat/lng for display. All polygon operations use **Shapely** (the standard Python GIS library).

### Step 1 — Coordinate System

KML exports coordinates as `longitude, latitude, altitude`. The app:
1. Strips the closing duplicate vertex (KML LinearRings close on themselves)
2. Computes the mean lat/lng as the **anchor point**
3. Converts each vertex to metres relative to the anchor using a haversine approximation:
   ```
   x = (lng - anchor_lng) × 111320 × cos(anchor_lat°)
   y = (anchor_lat - lat)  × 111320
   ```
   This gives a flat-Earth metre space that is accurate to < 1 m for plots up to ~10 km across.

All placement runs in this metre space; results are converted back to lat/lng for the map.

### Step 2 — Polygon Insets (Shapely buffer)

Two inset polygons are derived from the kyaari boundary using `Polygon.buffer(-d, join_style='mitre')`:

- **Inner ring** (`d = 1 m`): minimum edge setback. Boundary species walk along this ring.
- **Block zone** (`d = 5 m`): interior planting area after boundary species clearance. Block and alley species fill this zone.

Zone models (M9, M12) use only the 1 m inset (no boundary species).

### Step 3 — Boundary Species

Species with `role = "boundary"` (Red Sanders, Teak) are placed by walking the inner ring perimeter:

```
target_count = round(area_ha × perHa)          # from model spec, e.g. 130 trees/ha
spacing      = perimeter(inner_ring) / target_count
walk perimeter at this spacing → one dot per spacing metres
```

Spacing is **calibrated to hit the target count** exactly, regardless of perimeter length. This matches real agronomic practice where boundary trees are evenly distributed around the plot edge.

### Step 4 — Alley Species (Coconut rows/columns)

Species with `role = "alley"` or `"alley-long"` are placed in parallel rows or columns inside the block zone:

**Top/bottom rows** (`alley`):
- Compute `trees_per_row = block_width / sx`
- `num_pairs = round(target / (2 × trees_per_row))`
- Place a row band at `y₀ = block_y0 + sy/2` and a symmetric band at `y₁ = block_y1 − sy/2`
- Each band is recorded as a **y-exclusion zone** `[y − sy/2, y + sy/2]`

**Left/right columns** (`alley-long`):
- Same logic but for x-direction
- Each column becomes an **x-exclusion zone** `[x − sy/2, x + sy/2]`

These exclusion zones prevent any block species from being placed on top of alley positions — this was a key bug fixed in this build.

### Step 5 — Block Species

Species with `role = "block-a"` or `"block-b"` fill the remaining block area in a grid. Row assignment uses a **Bresenham-style distribution** to achieve the correct A:B ratio even on small plots:

```
R    = number of available rows (not in any y-exclusion zone)
nB   = R − round(R × wA / (wA + wB))          # target B rows
step = R / nB
b_indices = { floor(k × step + step/2) for k in range(nB) }
```

For each row y:
- If row index `ri ∈ b_indices` → assign to species B
- Otherwise → species A

For each x in the row: skip if `x` falls in any x-exclusion zone, then test `Polygon.contains(Point(x, y))` to confirm the point is inside the block.

This Bresenham distribution ensures the placed A:B ratio matches the model specification (e.g., 3:1 Mango to Sapota) even when the plot has only 5–7 available rows.

### Step 6 — Zone Models (M9, M12)

The block zone is split into vertical strips by fraction `zs`:

```
Zone A: x ∈ [block_x0,  block_x0 + W × zs_A]
Zone B: x ∈ above,      above    + W × zs_B]
Zone C: remainder
```

Each zone gets its own grid at its own spacing. A vertical white dashed line marks each zone boundary on the map.

### Prediction Numbers vs. Map Dots

**The count shown = the dots on the map** — always. There is no separate formula that generates a different number. The counts come from `len(placed_points)` after the algorithm runs, not from `area × density`.

Boundary species counts are calibrated to match the theoretical `area × perHa`, so they should be very close. Block species may differ from the area formula because the 5 m boundary setback reduces the usable block area — this is geometrically correct, not a discrepancy.

---

## System Design

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (field surveyor's phone or tablet)                │
│  https://plantation-model-kyaari.streamlit.app             │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼────────────────────────────────────────┐
│  Streamlit Community Cloud                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  app.py                                             │   │
│  │                                                     │   │
│  │  load_kyaaris()   ← kyaaris.kml (bundled in repo)   │   │
│  │  @st.cache_resource  (parsed once on cold start)    │   │
│  │                                                     │   │
│  │  compute_groups()  ← Shapely + custom walk algo     │   │
│  │  @st.cache_data    (cached per kyaari_id × model)  │   │
│  │                                                     │   │
│  │  build_map()       ← Folium + Google Maps tiles     │   │
│  └─────────────────────────────────────────────────────┘   │
│  Secrets: GMAPS_KEY (set in Streamlit Cloud dashboard)     │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
         Google Maps Satellite Tiles
         (mt1.google.com, key-authenticated)
```

### Data Flow

1. **Cold start**: `load_kyaaris('kyaaris.kml')` parses all 828 Placemarks from XML, converts lat/lng → metre polygons, extracts metadata. Cached with `@st.cache_resource` — runs once per Streamlit server instance.

2. **User selects kyaari + model**: `compute_groups(kyaari, model)` runs the placement algorithm in metre space. Result is cached with `@st.cache_data` keyed on `(kyaari_id, model_id)` — subsequent requests for the same pair are instant.

3. **Map render**: `build_map()` converts all placed metre coordinates back to lat/lng using `_m2ll()`, creates a Folium map with `folium.Circle` objects, embeds it with `st_folium`.

4. **No backend**: all computation happens server-side in Python. No database, no API calls (except Google Maps tile fetch).

### Key Libraries

| Library | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `folium` + `streamlit-folium` | Interactive Leaflet map embedded in Streamlit |
| `shapely` | Polygon inset (buffer), area/perimeter, point-in-polygon |
| `xml.etree.ElementTree` | KML parsing (stdlib, no extra dependency) |

### Caching Strategy

| Cache | Scope | Key |
|---|---|---|
| `@st.cache_resource` | KML parse | once per server process |
| `@st.cache_data` | Tree placement | `(kyaari_id, model_id)` |
| Folium map | Not cached | rebuilt on every render (fast, ~50 ms) |

---

## Project Structure

```
Plantation Model/
├── app.py              # Main Streamlit application
├── kyaaris.kml         # KML export from Varaha backend (828 kyaaris)
├── requirements.txt    # Python dependencies
├── .streamlit/
│   └── secrets.toml    # Local secrets (not committed to git)
├── .gitignore
└── README.md
```

---

## Local Development

```bash
# Install dependencies
pip install streamlit folium streamlit-folium shapely

# Add your Google Maps API key
mkdir -p .streamlit
echo 'GMAPS_KEY = "YOUR_KEY_HERE"' > .streamlit/secrets.toml

# Run
streamlit run app.py
```

## Deployment (Streamlit Community Cloud)

1. Push to GitHub (this repo)
2. Go to share.streamlit.io → New app → select this repo, `app.py`
3. In Advanced settings → Secrets, add:
   ```toml
   GMAPS_KEY = "YOUR_GOOGLE_MAPS_API_KEY"
   ```
4. Deploy — live in ~2 minutes

The app falls back to Esri World Imagery (free) if no API key is set.

---

## Next Steps (Backend Integration)

The current build uses a static KML file for validation. Production integration:

1. **Replace `kyaaris.kml` with a live API call** — `load_kyaaris()` currently reads a file; swap the parser for a REST call to the Varaha backend that returns GeoJSON or KML for enrolled kyaaris
2. **Persist model assignments** — write the selected model back to the kyaari record so surveyors' choices are saved
3. **Add staking export** — generate a CSV of tree lat/lng positions for GPS upload to field staking devices
4. **Role-based access** — Streamlit Cloud supports Google/GitHub OAuth; add surveyor login

---

*Built for Varaha · June 2026*
