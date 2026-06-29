# Varaha Plantation Model Portal

A GIS-powered field tool for visualising and validating plantation layouts on enrolled farmer plots (kyaaris) across Andhra Pradesh and Tamil Nadu.

Live app: **https://plantation-model-kyaari.streamlit.app**
Source: **https://github.com/rohyeeet/varaha-plantation-portal**

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
| Visualise on satellite | Plots every tree as a coloured dot on satellite imagery at real GPS coordinates |
| Count trees | Shows species-by-species placed count that exactly equals the dots on the map |
| Model comparison | Surveyor can switch model to see how the layout changes for the same plot |
| Plot metadata | Shows area, verification status, RS status, surveyor, species, and per-model carbon credit estimate |

---

## Plantation Models

<img width="1454" height="917" alt="image" src="https://github.com/user-attachments/assets/ae6c5d07-16bd-4bf5-ab4f-5078c6858913" />

All 13 models are derived from the South India Multispecies Plantation specification (*South India Multispecies Models — For ULU.xlsx* and *3 species designs South India*). Spacings and densities are calibrated directly against those documents.

### Model Reference

| Model | Type | Boundary | Interior | Farm size |
|---|---|---|---|---|
| M1 | Boundary + Top/Bottom Alley | Red Sanders · 3 m | Mango 6×6 m · Coconut 9×5 m (top/bottom rows) | > 0.8 ha |
| M2 | Boundary + Side Alley | Red Sanders · 3 m | Mango 6×6 m · Coconut 9×5 m (left/right columns) | > 0.8 ha |
| M3 | Boundary + Equal Block | Teak · 3 m | Mango 6×6 m : Cashew 6×6 m (1:1 rows) | ≤ 0.8 ha |
| M4 | Boundary + 3:1 Block | Teak · 3 m | Mango 6×6 m : Cashew 6×6 m (3:1 rows) | ≤ 0.8 ha |
| M5 | Boundary + Equal Block | Red Sanders · 3 m | Mango 6×6 m : Sapota 6×6 m (1:1 rows) | ≤ 0.8 ha |
| M6 | Boundary + 3:1 Block | Teak · 3 m | Mango 6×6 m : Sapota 6×6 m (3:1 rows) | ≤ 0.8 ha |
| M7 | Boundary + Equal Block | Teak · 3 m | Mango 6×6 m : Jamun 6×6 m (1:1 rows) | ≤ 0.8 ha |
| M8 | Boundary + 2:1 Block | Red Sanders · 3 m | Mango 6×6 m : Jamun 6×6 m (2:1 rows) | ≤ 0.8 ha |
| M9 | Three-Zone Block | — | Jackfruit 5×5 m (40%) · Sapota 6×6 m (36%) · Jamun 5×5 m (24%) | > 0.8 ha |
| M10 | Coconut Edge + 3:1 Block | — | Coconut 9×5 m (top/bottom) · Jackfruit 5×5 m : Jamun 5×5 m (3:1) | > 0.8 ha |
| M11 | Coconut Edge + 2:1 Block | — | Coconut 9×5 m (top/bottom) · Jackfruit 5×5 m : Sapota 5×5 m (2:1) | > 0.8 ha |
| M12 | Three-Zone Block | — | Jackfruit 5×5 m (40%) · Mango 6×6 m (36%) · Jamun 5×5 m (24%) | > 0.8 ha |
| M13 | Coconut 3-Side Edge + Equal Block | — | Coconut 9×5 m (3 sides) · Jackfruit 5×5 m : Citrus 5×5 m (1:1) | > 0.8 ha |

### Density Reference (trees/ha, from spec)

| Species | Spacing | Target density | Role |
|---|---|---|---|
| Red Sanders | 3 m boundary | 130 /ha | Boundary |
| Teak | 3 m boundary | 130 /ha | Boundary |
| Mango | 6×6 m | 184 /ha (M1/M2), 117.6 /ha (M3/M5/M7), 177.8 /ha (M4/M6), 156.7 /ha (M8), 100 /ha (M12) | Block |
| Coconut | 9×5 m | 42.2 /ha (M1/M2/M10/M11), 62.7 /ha (M13) | Alley |
| Cashew | 6×6 m | 117.6 /ha (M3), 57.3 /ha (M4) | Block |
| Sapota | 6×6 m or 5×5 m | 117.6 /ha (M5), 57.3 /ha (M6), 100 /ha (M9), 104.3 /ha (M11) | Block / Zone |
| Jamun | 6×6 m or 5×5 m | 117.6 /ha (M7), 78.4 /ha (M8), 94.4 /ha (M9/M12), 94.8 /ha (M10) | Block / Zone |
| Jackfruit | 5×5 m | 158.4 /ha (M9/M12), 218 /ha (M10), 208.6 /ha (M11), 136.6 /ha (M13) | Block / Zone |
| Citrus | 5×5 m | 136.6 /ha (M13) | Block |

---

## Placement Algorithm

<img width="1458" height="919" alt="image" src="https://github.com/user-attachments/assets/b548e181-851e-4fa7-b596-70e8e7a1ba3a" />

The algorithm works entirely in **relative metre coordinates** anchored at the polygon centroid, then converts back to lat/lng for display. All polygon operations use **Shapely**.

### Step 1 — Coordinate System

KML exports coordinates as `longitude, latitude, altitude`. The app:
1. Strips the closing duplicate vertex (KML LinearRings close on themselves)
2. Computes the mean lat/lng as the **anchor point**
3. Converts each vertex to metres relative to the anchor:
   ```
   x = (lng − anchor_lng) × 111320 × cos(anchor_lat°)
   y = (anchor_lat − lat) × 111320
   ```
   Flat-Earth haversine approximation — accurate to < 1 m for plots under 10 km.

All placement runs in this metre space. Results convert back via the inverse formula.

### Step 2 — Polygon Insets (Shapely buffer)

Two inset polygons are derived using `Polygon.buffer(-d, join_style='mitre')`:

- **Inner ring** (`d = 1 m`): minimum edge clearance. Boundary species walk this ring; non-boundary models use it as the outer limit of the planting zone.
- **Block zone** (`d = 5 m`): used only for models **with boundary species** (M1–M8). The 5 m setback clears the physical space occupied by the boundary tree ring before placing interior species.

Models without boundary species (M9–M13) use the 1 m inner ring as their block zone. Using a 5 m setback on these models would unnecessarily remove ~19% of plantable area.

### Step 3 — Boundary Species (M1–M8)

Species with `role = "boundary"` (Red Sanders or Teak at 3 m) are placed by walking the inner ring:

```
target_count = round(area_ha × perHa)
spacing      = perimeter(inner_ring) / target_count
walk perimeter at spacing → one dot per step
```

Spacing is calibrated to hit the target count exactly, regardless of perimeter length. The placed count matches `area × 130` within ±1 tree.

### Step 4 — Alley Species (Coconut — M1, M2, M10, M11, M13)

<img width="1467" height="919" alt="image" src="https://github.com/user-attachments/assets/0bc049fd-cfe8-4e04-adc3-ef1eee494a95" />

Coconut is placed in parallel rows (`alley`) or columns (`alley-long` / `alley-3`).

**Spacing convention for 9×5 m Coconut:**
- `9 m` = separation between row pairs (or column pairs)
- `5 m` = tree-to-tree spacing within each row (or column)

In code: `sx = 5` (within-row spacing), `sy = 9` (row-pair separation). This distinction matters: using 9 m as the within-row spacing would produce half the intended tree count.

**Top/bottom rows** (`alley`):
```
trees_per_row = block_width / sx                 # block_width / 5
num_pairs     = round(target / (2 × trees_per_row))
row_y0        = block_y0 + sy/2                  # 4.5 m from edge
row_y1        = block_y1 − sy/2
y_exclusion   = [row_y − sy/2, row_y + sy/2]    # 9 m band around each row
```

**Left/right columns** (`alley-long`, used for M2 and tall plots):
- Same logic along x-axis; exclusion zones become x-bands.

**Three-side** (`alley-3`, M13): places three pairs of rows/columns instead of two.

Exclusion zones prevent block species from overlapping alley positions.

### Step 5 — Block Species (M1–M8, M10–M11, M13)

Species with `role = "block-a"` or `"block-b"` fill the remaining block area in a grid. Row assignment uses a **Bresenham-style distribution** to hit the correct A:B ratio on any number of available rows:

```
R    = rows available (not in any y-exclusion band)
nB   = R − round(R × wA / (wA + wB))    # target B-species rows
step = R / nB
b_indices = { floor(k × step + step/2) for k in range(nB) }
```

For each row: assign B if `row_index ∈ b_indices`, else A. For each x in the row: skip any x-exclusion band, then test `Polygon.contains(Point(x, y))`.

This Bresenham distribution achieves the spec ratio (e.g. 3:1 Mango to Cashew) even on plots with as few as 4 available rows.

### Step 6 — Zone Models (M9, M12)

The block zone is split into three vertical strips by width fraction `zs`:

```
Zone A: x ∈ [x0,       x0 + W × zs_A]
Zone B: x ∈ [above,    above + W × zs_B]
Zone C: x ∈ [above,    x1]
```

Zone fractions are derived from the design spec target density and the species grid spacing:

```
zs = perHa_target / (10000 / sx / sy)
```

For M9 / M12 this gives: Jackfruit `0.399`, Sapota/Mango `0.363`, Jamun `0.238`. These fractions are normalised to sum to 1.0 so no planting area is lost. Each zone is filled independently at its own spacing. White dashed lines on the map mark zone boundaries.

### Placed Count vs. Theoretical Density

**The count shown on the cards = the dots on the map** — always. There is no separate formula. Counts come from `len(placed_points)` after the algorithm runs.

Boundary species match the theoretical `area × perHa` very closely (within ±2%) because spacing is calibrated to the target. Interior species will differ from the flat-area formula for two reasons that are both geometrically correct:

1. The boundary setback (1 m or 5 m) reduces the plantable area
2. Irregular polygon shapes cause partial rows/columns at the edges
3. Alley exclusion bands remove a strip of block rows near Coconut rows

These are real constraints that the algorithm respects. A surveyor seeing fewer trees than the model brochure expects is seeing an honest count for that specific plot shape.

---

## System Design

```
┌──────────────────────────────────────────────────────────────┐
│  Browser (field surveyor's phone or tablet)                 │
│  https://plantation-model-kyaari.streamlit.app              │
└─────────────────────┬────────────────────────────────────────┘
                      │ HTTPS
┌─────────────────────▼────────────────────────────────────────┐
│  Streamlit Community Cloud                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  app.py                                              │   │
│  │                                                      │   │
│  │  load_kyaaris()  ← kyaaris.kml (bundled in repo)    │   │
│  │  @st.cache_resource  (parsed once per cold start)    │   │
│  │                                                      │   │
│  │  compute_groups() ← Shapely + placement algorithm    │   │
│  │  @st.cache_data   (cached per kyaari_id × model_id) │   │
│  │                                                      │   │
│  │  build_map()      ← Folium + satellite tile layer    │   │
│  └──────────────────────────────────────────────────────┘   │
│  Secrets: GMAPS_KEY (Streamlit Cloud secrets dashboard)     │
└─────────────────────────────────────────────────────────────┘
                      │
                      ▼
          Google Maps Satellite Tiles  (preferred)
          Esri World Imagery           (fallback, no key needed)
```

### Data Flow

1. **Cold start** — `load_kyaaris('kyaaris.kml')` parses all 828 Placemarks from XML, converts lat/lng → metre polygons, extracts metadata (farmer, village, district, species, area, RS/verification status). Cached with `@st.cache_resource` — runs once per server process.

2. **Kyaari + model selected** — `_cached_groups(kyaari_id, model_id, kyaari)` runs the placement algorithm in metre space. Result is cached with `@st.cache_data` keyed on `(kyaari_id, model_id)` — repeated selections for the same pair are instant.

3. **Map render** — `build_map()` converts placed metre positions back to lat/lng via `_m2ll()`, creates a Folium map with `folium.Circle` objects (one per tree), embeds it via `st_folium`. Rebuilt every render (~50 ms), not cached, so map tiles always load fresh.

4. **No backend** — all computation is server-side Python. No database. No API calls except Google Maps tile fetches.

### Key Libraries

| Library | Version | Purpose |
|---|---|---|
| `streamlit` | ≥ 1.32 | Web UI, state management, secrets |
| `folium` | ≥ 0.15 | Leaflet.js map wrapper |
| `streamlit-folium` | ≥ 0.20 | Embeds Folium map in Streamlit |
| `shapely` | ≥ 2.0 | Polygon inset, area, perimeter, point-in-polygon |
| `xml.etree.ElementTree` | stdlib | KML parsing (no extra dependency) |

### Caching Strategy

| Cache | Scope | Key | Notes |
|---|---|---|---|
| `@st.cache_resource` | KML parse | Once per server process | Shared across all users |
| `@st.cache_data` | Tree placement | `(kyaari_id, model_id)` | Per unique kyaari × model pair |
| Folium map | Not cached | Rebuilt every render | ~50 ms, avoids stale tile state |

---

## Project Structure

```
Plantation Model/
├── app.py              # Main Streamlit application (~600 lines)
├── kyaaris.kml         # KML export from Varaha backend (828 kyaaris, May–June 2026)
├── requirements.txt    # Python dependencies
├── .streamlit/
│   └── secrets.toml    # Local Google Maps API key (gitignored)
├── .gitignore
└── README.md
```

---

## Local Development

```bash
# Clone
git clone https://github.com/rohyeeet/varaha-plantation-portal.git
cd varaha-plantation-portal

# Install dependencies
pip install streamlit folium streamlit-folium shapely

# Add your Google Maps API key (optional — falls back to Esri without it)
mkdir -p .streamlit
echo 'GMAPS_KEY = "YOUR_KEY_HERE"' > .streamlit/secrets.toml

# Run
streamlit run app.py
# → http://localhost:8501
```

## Deployment (Streamlit Community Cloud)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select this repo, branch `main`, file `app.py`
3. Under **Advanced settings → Secrets**, paste:
   ```toml
   GMAPS_KEY = "YOUR_GOOGLE_MAPS_API_KEY"
   ```
4. Deploy — live in ~2 minutes

Without the secret, the app falls back to Esri World Imagery (free, no key needed).

---

## Algorithm Calibration Notes

The algorithm was calibrated against *South India Multispecies Models — For ULU.xlsx* and *3 species designs South India (PDF)*. Three corrections were made during calibration:

| Issue | Root cause | Fix |
|---|---|---|
| Coconut tree count ~50% of spec | `sx=9` (9 m within-row spacing) instead of `sx=5`. "9×5 m" means 9 m between rows, 5 m between plants. | Swapped to `sx=5, sy=9` across M1, M2, M10, M11, M13 |
| Zone widths wrong for M9/M12 | Zone fractions were taken from the "% of total trees" column (e.g. Jackfruit 44.9%), not the physical width fraction | Recomputed as `perHa / (10000/sx/sy)`: Jackfruit 0.399, Sapota 0.363, Jamun 0.238 |
| Block area too small for M10/M11/M13 | 5 m setback applied to all non-zone models, but this is only correct when boundary species (Teak/Red Sanders) physically occupy the outer ring | 5 m setback only when `has_boundary`; else 1 m |

Placed counts will still differ slightly from the Excel theoretical values because the Excel uses flat area formulas (density × area) while this algorithm does real grid placement on the actual polygon shape. The algorithm is more accurate because it accounts for edge effects, irregular polygon shapes, and alley exclusion bands.

---

## Next Steps (Backend Integration)

The current build uses a static KML file for field validation. Production integration path:

1. **Live kyaari API** — `load_kyaaris()` reads a file; swap for a REST call to the Varaha backend returning GeoJSON or KML for enrolled kyaaris
2. **Persist model assignments** — write the surveyor's selected model back to the kyaari record
3. **Staking export** — generate a CSV of tree lat/lng positions for GPS upload to field staking devices
4. **Role-based access** — Streamlit Cloud supports Google/GitHub OAuth; add surveyor login so each surveyor sees only their assigned kyaaris

---

*Built for Varaha · June 2026*
