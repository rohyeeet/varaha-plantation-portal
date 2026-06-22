import streamlit as st
import folium
from streamlit_folium import st_folium
import math
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon as SPoly, Point as SPt, MultiPolygon

st.set_page_config(
    page_title="Plantation Portal · Varaha",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
[data-testid="stHeader"]{display:none}
footer{display:none}
.stApp,[data-testid="stAppViewContainer"]{background:#F4F5F0}
.block-container{padding:0 0 2rem!important;max-width:960px!important;margin:0 auto}

.portal-header{display:flex;align-items:baseline;gap:10px;
  padding:18px 0 10px;border-bottom:1px solid #D8DDD0;margin-bottom:12px}
.portal-brand{font-size:11px;font-weight:800;letter-spacing:.15em;
  color:#2D7A1A;text-transform:uppercase}
.portal-title{font-size:20px;font-weight:800;color:#0F2218;margin:0}

.sel-label{font-size:10px;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:#7A8E78;margin-bottom:3px}
.stSelectbox label,.stTextInput label{display:none!important}
.stSelectbox [data-baseweb="select"]{border-radius:8px!important}
.stTextInput input{border-radius:8px!important;border:1.5px solid #D0D8C8!important;
  font-size:13px!important;padding:8px 12px!important}
.stTextInput input:focus{border-color:#2D7A1A!important;box-shadow:0 0 0 2px #2D7A1A22!important}

.tag{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.05em;
  border-radius:4px;padding:2px 7px;margin-right:4px}
.tag-green{background:#E0F0DA;color:#1A5A1A}
.tag-red{background:#FDE8E8;color:#8B1A1A}
.tag-amber{background:#FDF3DC;color:#7A4A00}
.tag-grey{background:#EAEAEA;color:#666}

.sp-card{background:#fff;border-radius:10px;padding:14px 16px;
  border-top:4px solid var(--c);box-shadow:0 1px 3px rgba(0,0,0,.07)}
.sp-card-name{font-size:11px;font-weight:700;color:#4A6A48;margin-bottom:2px}
.sp-card-num{font-size:34px;font-weight:900;color:#0F2218;line-height:1}
.sp-card-sub{font-size:10px;color:#9AA898;margin-top:3px}

.total-card{background:#0F2218;border-radius:10px;padding:14px 16px;
  box-shadow:0 1px 3px rgba(0,0,0,.15)}
.total-card-label{font-size:10px;font-weight:700;letter-spacing:.08em;
  color:#6DB87A;text-transform:uppercase}
.total-card-num{font-size:34px;font-weight:900;color:#fff;line-height:1;margin-top:4px}
.total-card-sub{font-size:10px;color:#4A7A54;margin-top:3px}

.info-card{background:#fff;border-radius:10px;padding:14px 16px;
  box-shadow:0 1px 3px rgba(0,0,0,.07);height:100%}
.info-label{font-size:10px;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:#7A8E78;margin-bottom:8px}
.info-row{font-size:13px;color:#2A3A28;line-height:1.9}
.info-row b{color:#0F2218}
.credit-big{font-size:28px;font-weight:900;color:#1A5A1A}
.credit-unit{font-size:11px;color:#4A7A4A;font-weight:600}
.credit-meta{font-size:12px;color:#5A8A58;margin-top:6px;line-height:1.7}
.model-desc{font-size:12px;color:#5A6E58;background:#EEF2EA;border-radius:8px;
  padding:10px 14px;margin-top:10px;line-height:1.6}
.model-desc b{color:#2A4A28}
.no-kyaari{text-align:center;padding:40px;color:#7A8E78;font-size:14px}
</style>
""", unsafe_allow_html=True)

# ─── MODELS ──────────────────────────────────────────────────────

MODELS = [
    {"id":1,"name":"Model 1","sub":"Mango · Red Sanders · Coconut",
     "type":"Boundary + Alley Block","size":">0.8 ha","credit":6.744,"totalPerHa":356.22,
     "desc":"Red Sanders boundary at 3 m. Mango block at 6×6 m. Coconut top/bottom alley at 9×5 m.",
     "sp":[
        {"name":"Red Sanders","col":"#C0392B","spacing":"3 m","perHa":130,"role":"boundary","sal":3},
        {"name":"Mango","col":"#E8940A","spacing":"6×6 m","perHa":184,"role":"block-a","sx":6,"sy":6,"aw":3},
        {"name":"Coconut","col":"#2E86C1","spacing":"9×5 m","perHa":42.22,"role":"alley","sx":9,"sy":5},
     ]},
    {"id":2,"name":"Model 2","sub":"Mango · Red Sanders · Coconut (Long-edge)",
     "type":"Boundary + Alley Block","size":">0.8 ha","credit":7.508,"totalPerHa":356.22,
     "desc":"Same as Model 1 but Coconut alley columns run along the longer farm edges.",
     "sp":[
        {"name":"Red Sanders","col":"#C0392B","spacing":"3 m","perHa":130,"role":"boundary","sal":3},
        {"name":"Mango","col":"#E8940A","spacing":"6×6 m","perHa":184,"role":"block-a","sx":6,"sy":6,"aw":3},
        {"name":"Coconut","col":"#2E86C1","spacing":"9×5 m","perHa":42.22,"role":"alley-long","sx":9,"sy":5},
     ]},
    {"id":3,"name":"Model 3","sub":"Mango · Cashew · Teak",
     "type":"Boundary + Equal Block","size":"≤0.8 ha","credit":5.809,"totalPerHa":365.11,
     "desc":"Teak boundary at 3 m. Mango and Cashew in equal 50/50 alternating rows at 6×6 m.",
     "sp":[
        {"name":"Teak","col":"#27AE60","spacing":"3 m","perHa":130,"role":"boundary","sal":3},
        {"name":"Mango","col":"#E8940A","spacing":"6×6 m","perHa":117.56,"role":"block-a","sx":6,"sy":6,"aw":1},
        {"name":"Cashew","col":"#D35400","spacing":"6×6 m","perHa":117.56,"role":"block-b","sx":6,"sy":6,"aw":1},
     ]},
    {"id":4,"name":"Model 4","sub":"Mango · Teak · Cashew",
     "type":"Boundary + 3:1 Block","size":"≤0.8 ha","credit":5.907,"totalPerHa":365.11,
     "desc":"Teak boundary at 3 m. Mango dominant 3:1 over Cashew in block interior.",
     "sp":[
        {"name":"Teak","col":"#27AE60","spacing":"3 m","perHa":130,"role":"boundary","sal":3},
        {"name":"Mango","col":"#E8940A","spacing":"6×6 m","perHa":177.78,"role":"block-a","sx":6,"sy":6,"aw":3},
        {"name":"Cashew","col":"#D35400","spacing":"6×6 m","perHa":57.33,"role":"block-b","sx":6,"sy":6,"aw":1},
     ]},
    {"id":5,"name":"Model 5","sub":"Mango · Sapota · Red Sanders",
     "type":"Boundary + Equal Block","size":"≤0.8 ha","credit":7.424,"totalPerHa":365.11,
     "desc":"Red Sanders boundary at 3 m. Mango and Sapota in equal alternating rows at 6×6 m.",
     "sp":[
        {"name":"Red Sanders","col":"#C0392B","spacing":"3 m","perHa":130,"role":"boundary","sal":3},
        {"name":"Mango","col":"#E8940A","spacing":"6×6 m","perHa":117.56,"role":"block-a","sx":6,"sy":6,"aw":1},
        {"name":"Sapota","col":"#8E44AD","spacing":"6×6 m","perHa":117.56,"role":"block-b","sx":6,"sy":6,"aw":1},
     ]},
    {"id":6,"name":"Model 6","sub":"Mango · Sapota · Teak",
     "type":"Boundary + 3:1 Block","size":"≤0.8 ha","credit":6.796,"totalPerHa":365.11,
     "desc":"Teak boundary at 3 m. Mango dominant 3:1 over Sapota in block interior.",
     "sp":[
        {"name":"Teak","col":"#27AE60","spacing":"3 m","perHa":130,"role":"boundary","sal":3},
        {"name":"Mango","col":"#E8940A","spacing":"6×6 m","perHa":177.78,"role":"block-a","sx":6,"sy":6,"aw":3},
        {"name":"Sapota","col":"#8E44AD","spacing":"6×6 m","perHa":57.33,"role":"block-b","sx":6,"sy":6,"aw":1},
     ]},
    {"id":7,"name":"Model 7","sub":"Mango · Jamun · Teak",
     "type":"Boundary + Equal Block","size":"≤0.8 ha","credit":6.974,"totalPerHa":365.11,
     "desc":"Teak boundary at 3 m. Mango and Jamun in equal 50/50 alternating rows at 6×6 m.",
     "sp":[
        {"name":"Teak","col":"#27AE60","spacing":"3 m","perHa":130,"role":"boundary","sal":3},
        {"name":"Mango","col":"#E8940A","spacing":"6×6 m","perHa":117.56,"role":"block-a","sx":6,"sy":6,"aw":1},
        {"name":"Jamun","col":"#6C3483","spacing":"6×6 m","perHa":117.56,"role":"block-b","sx":6,"sy":6,"aw":1},
     ]},
    {"id":8,"name":"Model 8","sub":"Mango · Jamun · Red Sanders",
     "type":"Boundary + 2:1 Block","size":"≤0.8 ha","credit":6.974,"totalPerHa":365.11,
     "desc":"Red Sanders boundary at 3 m. Mango and Jamun in 2:1 alternating rows at 6×6 m.",
     "sp":[
        {"name":"Red Sanders","col":"#C0392B","spacing":"3 m","perHa":130,"role":"boundary","sal":3},
        {"name":"Mango","col":"#E8940A","spacing":"6×6 m","perHa":156.74,"role":"block-a","sx":6,"sy":6,"aw":2},
        {"name":"Jamun","col":"#6C3483","spacing":"6×6 m","perHa":78.37,"role":"block-b","sx":6,"sy":6,"aw":1},
     ]},
    {"id":9,"name":"Model 9","sub":"Jackfruit · Sapota · Jamun",
     "type":"Three-Zone Block","size":">0.8 ha","credit":7.424,"totalPerHa":352.8,
     "desc":"No boundary. Three vertical zones: Jackfruit 40% at 5×5 m, Sapota 36% at 6×6 m, Jamun 24% at 5×5 m.",
     "sp":[
        {"name":"Jackfruit","col":"#1E8449","spacing":"5×5 m","perHa":158.4,"role":"zone","sx":5,"sy":5,"zs":.399},
        {"name":"Sapota","col":"#8E44AD","spacing":"6×6 m","perHa":100,"role":"zone","sx":6,"sy":6,"zs":.363},
        {"name":"Jamun","col":"#6C3483","spacing":"5×5 m","perHa":94.4,"role":"zone","sx":5,"sy":5,"zs":.238},
     ]},
    {"id":10,"name":"Model 10","sub":"Coconut · Jackfruit · Jamun",
     "type":"Coconut Edge + 3:1 Block","size":">0.8 ha","credit":7.424,"totalPerHa":354.62,
     "desc":"Coconut top/bottom alley rows at 9×5 m. Jackfruit 3:1 over Jamun fills block at 5×5 m.",
     "sp":[
        {"name":"Coconut","col":"#2E86C1","spacing":"9×5 m","perHa":41.78,"role":"alley","sx":9,"sy":5},
        {"name":"Jackfruit","col":"#1E8449","spacing":"5×5 m","perHa":218.04,"role":"block-a","sx":5,"sy":5,"aw":3},
        {"name":"Jamun","col":"#6C3483","spacing":"5×5 m","perHa":94.8,"role":"block-b","sx":5,"sy":5,"aw":1},
     ]},
    {"id":11,"name":"Model 11","sub":"Coconut · Jackfruit · Sapota",
     "type":"Coconut Edge + 2:1 Block","size":">0.8 ha","credit":7.424,"totalPerHa":354.62,
     "desc":"Coconut top/bottom alley rows at 9×5 m. Jackfruit 2:1 over Sapota fills block at 5×5 m.",
     "sp":[
        {"name":"Coconut","col":"#2E86C1","spacing":"9×5 m","perHa":41.78,"role":"alley","sx":9,"sy":5},
        {"name":"Jackfruit","col":"#1E8449","spacing":"5×5 m","perHa":208.56,"role":"block-a","sx":5,"sy":5,"aw":2},
        {"name":"Sapota","col":"#8E44AD","spacing":"5×5 m","perHa":104.28,"role":"block-b","sx":5,"sy":5,"aw":1},
     ]},
    {"id":12,"name":"Model 12","sub":"Mango · Jackfruit · Jamun",
     "type":"Three-Zone Block","size":">0.8 ha","credit":7.029,"totalPerHa":352.8,
     "desc":"No boundary. Three vertical zones: Jackfruit 40% at 5×5 m, Mango 36% at 6×6 m, Jamun 24% at 5×5 m.",
     "sp":[
        {"name":"Jackfruit","col":"#1E8449","spacing":"5×5 m","perHa":158.4,"role":"zone","sx":5,"sy":5,"zs":.399},
        {"name":"Mango","col":"#E8940A","spacing":"6×6 m","perHa":100,"role":"zone","sx":6,"sy":6,"zs":.363},
        {"name":"Jamun","col":"#6C3483","spacing":"5×5 m","perHa":94.4,"role":"zone","sx":5,"sy":5,"zs":.238},
     ]},
    {"id":13,"name":"Model 13","sub":"Coconut · Jackfruit · Citrus",
     "type":"Coconut Edge + Equal Block","size":">0.8 ha","credit":7.424,"totalPerHa":335.91,
     "desc":"Coconut along three sides at 9×5 m. Jackfruit and Citrus in equal 50/50 rows at 5×5 m.",
     "sp":[
        {"name":"Coconut","col":"#2E86C1","spacing":"9×5 m","perHa":62.67,"role":"alley-3","sx":9,"sy":5},
        {"name":"Jackfruit","col":"#1E8449","spacing":"5×5 m","perHa":136.62,"role":"block-a","sx":5,"sy":5,"aw":1},
        {"name":"Citrus","col":"#5D8A00","spacing":"5×5 m","perHa":136.62,"role":"block-b","sx":5,"sy":5,"aw":1},
     ]},
]

# ─── SPECIES → MODEL MAPPING ──────────────────────────────────────

# Map normalised species sets from KML to best-matching model index in MODELS list
_SPECIES_MODEL = {
    frozenset(['COCONUT','MANGO','RED_SANDERS']):     0,   # M1
    frozenset(['MANGO','RED_SANDERS','SAPOTA']):       4,   # M5
    frozenset(['CITRUS','COCONUT','JACKFRUIT']):      12,   # M13
    frozenset(['MANGO','SAPOTA','TEAK']):              5,   # M6
    frozenset(['JAMUN','MANGO','RED_SANDERS']):        7,   # M8
    frozenset(['JAMUN','MANGO','TEAK']):               6,   # M7
    frozenset(['JACKFRUIT','JAMUN','MANGO']):         11,   # M12
    frozenset(['COCONUT','JACKFRUIT','JAMUN']):        9,   # M10
    frozenset(['COCONUT','JACKFRUIT','SAPOTA']):      10,   # M11
    frozenset(['CASHEW','MANGO','TEAK']):              3,   # M4
    frozenset(['JACKFRUIT','JAMUN','SAPOTA']):         8,   # M9
    frozenset(['CASHEW','MANGO']):                     2,   # M3 fallback
}

def _suggest_model(species_str: str) -> int:
    if not species_str: return 0
    sp = frozenset(s.strip().upper() for s in species_str.split(',') if s.strip())
    return _SPECIES_MODEL.get(sp, 0)

# ─── KML LOADER ───────────────────────────────────────────────────

def _ll2m(lng: float, lat: float, anchor_lat: float, anchor_lng: float):
    """Real lat/lng → relative [x, y] metres from anchor."""
    x = (lng - anchor_lng) * 111320 * math.cos(math.radians(anchor_lat))
    y = (anchor_lat - lat) * 111320
    return [x, y]

@st.cache_resource(show_spinner="Loading kyaari data…")
def load_kyaaris(kml_path: str):
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    tree = ET.parse(kml_path)
    root = tree.getroot()
    kyaaris = []
    kyaari_by_id = {}

    for pm in root.findall('.//kml:Placemark', ns):
        try:
            kyaari_id = pm.find('kml:name', ns).text.strip()
            data = {}
            for d in pm.findall('.//kml:Data', ns):
                v = d.find('kml:value', ns)
                data[d.get('name')] = (v.text or '').strip()

            # Parse coordinates (KML: lng,lat,alt)
            raw = pm.find('.//kml:coordinates', ns).text.strip().split()
            ll_pts = []
            for c in raw:
                parts = c.split(',')
                ll_pts.append((float(parts[0]), float(parts[1])))

            # Remove closing duplicate point
            if len(ll_pts) > 1 and ll_pts[0] == ll_pts[-1]:
                ll_pts = ll_pts[:-1]
            if len(ll_pts) < 3:
                continue

            # Anchor = mean lat/lng of vertices
            anchor_lat = sum(lat for _, lat in ll_pts) / len(ll_pts)
            anchor_lng = sum(lng for lng, _ in ll_pts) / len(ll_pts)

            # Convert to relative metres
            polygon_m = [_ll2m(lng, lat, anchor_lat, anchor_lng) for lng, lat in ll_pts]

            species_str  = data.get('Sapling Specie Names', '')
            farmer       = data.get('Farmer Name', '').strip().title()
            district     = data.get('District', '')
            state        = data.get('State', '')
            village      = data.get('Village', '').strip().title()

            try: area_ha = float(data.get('Total Area') or 0)
            except: area_ha = 0.0

            k = {
                'id':           kyaari_id,
                'label':        f"{kyaari_id} · {farmer}",
                'farmer':       farmer,
                'dist':         f"{district}, {state}",
                'village':      village,
                'shape':        'Polygon',
                'area_ha':      area_ha,
                'anchor':       (anchor_lat, anchor_lng),
                'polygon':      polygon_m,
                'species_str':  species_str,
                'model_type':   data.get('Plantation Model', ''),
                'rs_status':    data.get('RS Status', ''),
                'verif_status': data.get('Verification Status', ''),
                'surveyor':     data.get('Surveyor Name', ''),
                'org':          data.get('Organisation', ''),
                'total_plants': int(data.get('Total Number of Plants') or 0),
                'default_m':    _suggest_model(species_str),
            }
            kyaaris.append(k)
            kyaari_by_id[kyaari_id] = k
        except Exception:
            continue

    return kyaaris, kyaari_by_id

# ─── GIS ENGINE ───────────────────────────────────────────────────

def _shapely(coords):
    p = SPoly([(c[0], c[1]) for c in coords])
    return p if p.is_valid else p.buffer(0)

def _area(coords):  return _shapely(coords).area
def _perim(coords): return _shapely(coords).exterior.length
def _centroid(coords):
    c = _shapely(coords).centroid; return [c.x, c.y]

def _safe_inset(coords, d):
    try:
        r = _shapely(coords).buffer(-d, join_style=2, mitre_limit=10.0)
        if r.is_empty: return coords
        if isinstance(r, MultiPolygon): r = max(r.geoms, key=lambda g: g.area)
        return [[x, y] for x, y in r.exterior.coords[:-1]]
    except Exception: return coords

def _pip(pt, coords):
    return _shapely(coords).contains(SPt(pt[0], pt[1]))

def _bbox(coords):
    xs=[c[0] for c in coords]; ys=[c[1] for c in coords]
    return dict(x0=min(xs),x1=max(xs),y0=min(ys),y1=max(ys))

def _dist(a, b):
    return math.sqrt((b[0]-a[0])**2+(b[1]-a[1])**2)

def _walk_boundary(coords, spacing):
    pts=[]; cum=0; nxt=spacing/2; n=len(coords)
    for i in range(n):
        p1,p2=coords[i],coords[(i+1)%n]
        el=_dist(p1,p2)
        if el<1e-9: continue
        dx,dy=(p2[0]-p1[0])/el,(p2[1]-p1[1])/el; ep=0
        while ep+(nxt-cum)<=el+1e-9:
            ep+=nxt-cum; cum=nxt; nxt+=spacing
            pts.append([p1[0]+dx*ep,p1[1]+dy*ep])
        cum+=el-ep
    return pts

def _walk_boundary_targeted(coords, target):
    if target<=0: return []
    return _walk_boundary(coords, _perim(coords)/target)

def _in_bands(v, bands):
    return any(lo<=v<=hi for lo,hi in bands)

def _place_alley(block, sx, sy, role, bb, target, num_pairs=None):
    pts=[]; y_bands=[]; x_bands=[]
    W=bb['x1']-bb['x0']; H=bb['y1']-bb['y0']
    is_long=(role=='alley-long') or (W<H)

    if is_long:
        tpr=max(1,int(H/sx))
        base = num_pairs if num_pairs is not None else max(1,round(target/(2*tpr)))
        n_col=max(1,round(H/sx)); adj=H/n_col if abs(H/n_col-sx)/sx<=0.15 else sx
        for p in range(base):
            x0=bb['x0']+sy/2+p*sy; x1=bb['x1']-sy/2-p*sy
            if x0>=x1: break
            x_bands.append([x0-sy/2,x0+sy/2])
            if abs(x1-x0)>sy: x_bands.append([x1-sy/2,x1+sy/2])
            y=bb['y0']+adj/2
            while y<=bb['y1']+1e-6:
                if _pip([x0,y],block): pts.append([x0,y])
                if abs(x1-x0)>sy and _pip([x1,y],block): pts.append([x1,y])
                y+=adj
    else:
        tpr=max(1,int(W/sx))
        raw = num_pairs if num_pairs is not None else max(1,round(target/(2*tpr)))
        npairs=max(3,raw) if role=='alley-3' else raw
        n_row=max(1,round(W/sx)); adj=W/n_row if abs(W/n_row-sx)/sx<=0.15 else sx
        for p in range(npairs):
            y0=bb['y0']+sy/2+p*sy; y1=bb['y1']-sy/2-p*sy
            if y0>=y1: break
            y_bands.append([y0-sy/2,y0+sy/2])
            if y1-y0>sy: y_bands.append([y1-sy/2,y1+sy/2])
            x=bb['x0']+adj/2
            while x<=bb['x1']+1e-6:
                if _pip([x,y0],block): pts.append([x,y0])
                if y1-y0>sy and _pip([x,y1],block): pts.append([x,y1])
                x+=adj
    return pts,y_bands,x_bands

def _bresenham_b(R, wa, wb):
    if wb==0 or R==0: return set()
    nB=max(0,R-round(R*wa/(wa+wb)))
    if nB==0: return set()
    step=R/nB
    return {int(k*step+step/2) for k in range(nB)}

def _longest_edge_angle(coords):
    """Angle (radians) of the longest edge in the polygon — used to orient block grid rows."""
    best_sq, best_a = 0.0, 0.0
    n = len(coords)
    for i in range(n):
        p1, p2 = coords[i], coords[(i+1)%n]
        dx, dy = p2[0]-p1[0], p2[1]-p1[1]
        sq = dx*dx + dy*dy
        if sq > best_sq:
            best_sq, best_a = sq, math.atan2(dy, dx)
    return best_a

def _atul_row_pairs(perp_m):
    """Atul's coconut row-count rule: perpendicular side length (m) → number of row pairs per side.
    <75m→1, 75–125m→2, 125–175m→3, 175–225m→4, …"""
    return max(1, int((perp_m + 25) / 50))

def compute_groups(kyaari: dict, model: dict):
    poly    = kyaari['polygon']
    area_ha = kyaari.get('area_ha') or (_area(poly)/10000)
    inner        = _safe_inset(poly,1)
    has_boundary = any(s['role']=='boundary' for s in model['sp'])
    block        = _safe_inset(poly,5) if has_boundary else inner
    bb      = _bbox(block)
    groups  = [{'sp':s,'pts':[],'rows':[]} for s in model['sp']]

    for i,s in enumerate(model['sp']):
        if s['role']=='boundary':
            groups[i]['pts']=_walk_boundary_targeted(inner,round(area_ha*s['perHa']))

    has_zones = any(s['role']=='zone' for s in model['sp'])
    if has_zones:
        # Rotate zone grid to align with longest farm edge, then adjust spacing
        ez=_longest_edge_angle(block)
        cfwz,sfwz=math.cos(-ez),math.sin(-ez)
        cbkz,sbkz=math.cos(ez), math.sin(ez)
        def _trz(p): return [p[0]*cfwz-p[1]*sfwz, p[0]*sfwz+p[1]*cfwz]
        def _tiz(p): return [p[0]*cbkz-p[1]*sbkz, p[0]*sbkz+p[1]*cbkz]
        bb_rz=_bbox([_trz(p) for p in block])
        W_rz=bb_rz['x1']-bb_rz['x0']; H_rz=bb_rz['y1']-bb_rz['y0']
        xc_rz=bb_rz['x0']
        for s in model['sp']:
            if s['role']!='zone': continue
            i=model['sp'].index(s); xe_rz=xc_rz+W_rz*s['zs']
            W_z=xe_rz-xc_rz
            nx=max(1,round(W_z/s['sx'])); ny=max(1,round(H_rz/s['sy']))
            asx=W_z/nx if abs(W_z/nx-s['sx'])/s['sx']<=0.15 else s['sx']
            asy=H_rz/ny if abs(H_rz/ny-s['sy'])/s['sy']<=0.15 else s['sy']
            pts=[]
            y=bb_rz['y0']+asy/2
            while y<=bb_rz['y1']+1e-6:
                x=xc_rz+asx/2
                while x<=bb_rz['x1']+1e-6:
                    if xc_rz-1e-6<=x<xe_rz-1e-6:
                        pt=_tiz([x,y])
                        if _pip(pt,block): pts.append(pt)
                    x+=asx
                y+=asy
            groups[i]['pts']=pts; xc_rz=xe_rz
        return groups

    # Coconut alley: use Atul's perpendicular-side row-count formula
    y_bands=[]; x_bands=[]
    for s in model['sp']:
        if not s['role'].startswith('alley'): continue
        i=model['sp'].index(s)
        W_b=bb['x1']-bb['x0']; H_b=bb['y1']-bb['y0']
        is_long_s=(s['role']=='alley-long') or (W_b<H_b)
        perp = W_b if is_long_s else H_b
        num_p = _atul_row_pairs(perp) if s['role'] in ('alley','alley-long') else None
        pts,yb,xb=_place_alley(block,s['sx'],s['sy'],s['role'],bb,round(area_ha*s['perHa']),num_p)
        groups[i]['pts']=pts; y_bands.extend(yb); x_bands.extend(xb)

    # Block grid: rotated to align rows with the longest edge of the block polygon (Atul Step 3)
    sa=next((s for s in model['sp'] if s['role']=='block-a'),None)
    sb=next((s for s in model['sp'] if s['role']=='block-b'),None)
    if sa:
        ia=model['sp'].index(sa); ib=model['sp'].index(sb) if sb else -1
        wa=sa.get('aw',1); wb_=sb.get('aw',1) if sb else 0
        sx,sy=sa['sx'],sa['sy']

        ea = _longest_edge_angle(block)
        cfw,sfw = math.cos(-ea), math.sin(-ea)   # original → rotated
        cbk,sbk = math.cos(ea),  math.sin(ea)    # rotated  → original
        def _tr(p): return [p[0]*cfw-p[1]*sfw, p[0]*sfw+p[1]*cfw]
        def _ti(p): return [p[0]*cbk-p[1]*sbk, p[0]*sbk+p[1]*cbk]

        # Safe zone: subtract Coconut alley strips from block polygon.
        # Band-checking in original space fails for rotated grids (rotated rows
        # are diagonal, so only some trees per row fall inside axis-aligned bands).
        # Shapely difference is geometrically exact for any rotation angle.
        safe_sh = _shapely(block)
        for lo,hi in y_bands:
            safe_sh = safe_sh.difference(SPoly([(-9999,lo),(9999,lo),(9999,hi),(-9999,hi)]))
        for lo,hi in x_bands:
            safe_sh = safe_sh.difference(SPoly([(lo,-9999),(hi,-9999),(hi,9999),(lo,9999)]))
        if safe_sh.is_empty:
            safe_polys = []
        elif isinstance(safe_sh, MultiPolygon):
            safe_polys = [g for g in safe_sh.geoms if not g.is_empty]
        else:
            safe_polys = [safe_sh]

        bb_r=_bbox([_tr(p) for p in block])
        W_r=bb_r['x1']-bb_r['x0']; H_r=bb_r['y1']-bb_r['y0']
        nx=max(1,round(W_r/sx)); ny=max(1,round(H_r/sy))
        adj_sx=W_r/nx if abs(W_r/nx-sx)/sx<=0.15 else sx
        adj_sy=H_r/ny if abs(H_r/ny-sy)/sy<=0.15 else sy

        all_y=[]; y=bb_r['y0']+adj_sy/2
        while y<=bb_r['y1']+1e-6:
            all_y.append(y); y+=adj_sy

        b_rows=_bresenham_b(len(all_y),wa,wb_)
        for ri,row_y in enumerate(all_y):
            ti=ib if (ri in b_rows and ib>=0) else ia
            row_pts=[]
            x=bb_r['x0']+adj_sx/2
            while x<=bb_r['x1']+1e-6:
                pt=_ti([x,row_y])
                p=SPt(pt[0],pt[1])
                if any(s.contains(p) for s in safe_polys):
                    row_pts.append(pt)
                x+=adj_sx
            groups[ti]['pts'].extend(row_pts)
            if row_pts: groups[ti]['rows'].append(len(row_pts))
    return groups

# ─── GEO UTILS ────────────────────────────────────────────────────

def _m2ll(pt, anchor):
    x,y=pt; lat0,lng0=anchor
    return [lat0-y/111320, lng0+x/(111320*math.cos(math.radians(lat0)))]

def _poly2ll(coords, anchor):
    return [_m2ll(c,anchor) for c in coords]

# ─── MAP ──────────────────────────────────────────────────────────

GMAPS_KEY = st.secrets.get("GMAPS_KEY", "")

def build_map(kyaari: dict, model: dict, groups: list):
    anchor = kyaari['anchor']
    cen    = _centroid(kyaari['polygon'])
    center = _m2ll(cen, anchor)

    fm = folium.Map(location=center, zoom_start=18, tiles=None, prefer_canvas=True)

    tile_url = (
        f"https://mt1.google.com/vt/lyrs=s&x={{x}}&y={{y}}&z={{z}}&key={GMAPS_KEY}"
        if GMAPS_KEY else
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
    )
    folium.TileLayer(
        tiles=tile_url,
        attr="Google Maps" if GMAPS_KEY else "Esri World Imagery",
        name="Satellite", max_zoom=21, max_native_zoom=20,
    ).add_to(fm)

    # Kyaari polygon
    folium.Polygon(
        locations=_poly2ll(kyaari['polygon'], anchor),
        color='#27AE60', weight=2.5, fill=True,
        fill_color='#27AE60', fill_opacity=0.06,
    ).add_to(fm)

    # Zone dividers (M9, M12) — rotated to match farm orientation
    if any(s['role']=='zone' for s in model['sp']):
        bloc=_safe_inset(kyaari['polygon'],1)
        ez2=_longest_edge_angle(bloc)
        cfwz2,sfwz2=math.cos(-ez2),math.sin(-ez2)
        cbkz2,sbkz2=math.cos(ez2), math.sin(ez2)
        def _trdiv(p): return [p[0]*cfwz2-p[1]*sfwz2, p[0]*sfwz2+p[1]*cfwz2]
        def _tidiv(p): return [p[0]*cbkz2-p[1]*sbkz2, p[0]*sbkz2+p[1]*cbkz2]
        bb_d=_bbox([_trdiv(p) for p in bloc])
        W_d=bb_d['x1']-bb_d['x0']; xc_d=bb_d['x0']
        for s in [z for z in model['sp'] if z['role']=='zone'][:-1]:
            xc_d+=W_d*s['zs']
            p1=_tidiv([xc_d,bb_d['y0']]); p2=_tidiv([xc_d,bb_d['y1']])
            folium.PolyLine(
                [_m2ll(p1,anchor),_m2ll(p2,anchor)],
                color='white',weight=1.5,dash_array='6,4',opacity=0.65,
            ).add_to(fm)

    # Boundary guide rings
    if any(s['role']=='boundary' for s in model['sp']):
        for d,col,da in [(1,'#C0392B','3,4'),(5,'#2C6040','5,4')]:
            ring=_safe_inset(kyaari['polygon'],d)
            if _area(ring)>0:
                folium.Polygon(
                    locations=_poly2ll(ring,anchor),
                    color=col,weight=1,fill=False,dash_array=da,opacity=0.3,
                ).add_to(fm)

    # Tree dots
    RADII={'boundary':0.8,'alley':1.5,'alley-long':1.5,'alley-3':1.5,
           'block-a':1.2,'block-b':1.2,'zone':1.2}
    for g in groups:
        sp=g['sp']; r=RADII.get(sp['role'],1.2)
        for pt in g['pts']:
            folium.Circle(
                location=_m2ll(pt,anchor), radius=r,
                color='rgba(255,255,255,0.4)', weight=0.5,
                fill=True, fill_color=sp['col'], fill_opacity=0.9,
                tooltip=f"{sp['name']} · {sp['spacing']}",
            ).add_to(fm)
    return fm

# ─── CACHED COMPUTE ───────────────────────────────────────────────

@st.cache_data(show_spinner="Computing tree positions…")
def _cached_groups(kyaari_id: str, model_id: int, _kyaari: dict):
    _v = 5  # bump this whenever compute_groups changes to bust stale cache
    model = next(m for m in MODELS if m['id']==model_id)
    return compute_groups(_kyaari, model)

ROLE_LABEL={
    'boundary':'Boundary','alley':'Alley rows','alley-long':'Alley cols',
    'alley-3':'3-side alley','block-a':'Block','block-b':'Block','zone':'Zone',
}

STATUS_STYLE = {
    'ACCEPTED': 'tag-green', 'PENDING': 'tag-amber',
    'REJECTED': 'tag-red',   'None': 'tag-grey', '': 'tag-grey',
}

# ─── LOAD DATA ────────────────────────────────────────────────────

KYAARIS_ALL, KYAARI_BY_ID = load_kyaaris('kyaaris.kml')

# ─── UI ───────────────────────────────────────────────────────────

st.markdown("""
<div class="portal-header">
  <span class="portal-brand">Varaha</span>
  <span class="portal-title">Plantation Portal</span>
</div>""", unsafe_allow_html=True)

# ── SEARCH + SELECTORS ────────────────────────────────────────────
sc1, sc2, sc3 = st.columns([1, 2, 2], gap="small")

with sc1:
    st.markdown('<div class="sel-label">Search Kyaari</div>', unsafe_allow_html=True)
    query = st.text_input("search", placeholder="ID / farmer / district",
                           label_visibility="collapsed")

# Filter kyaaris
if query.strip():
    q = query.strip().lower()
    filtered = [k for k in KYAARIS_ALL
                if q in k['id'].lower()
                or q in k['farmer'].lower()
                or q in k['dist'].lower()
                or q in k['village'].lower()]
else:
    filtered = KYAARIS_ALL

with sc2:
    st.markdown('<div class="sel-label">Kyaari</div>', unsafe_allow_html=True)
    if not filtered:
        st.warning("No kyaaris match your search.")
        st.stop()
    k_sel = st.selectbox(
        "kyaari", range(len(filtered)),
        format_func=lambda i: filtered[i]['label'],
        label_visibility="collapsed",
    )

kyaari = filtered[k_sel]

with sc3:
    st.markdown('<div class="sel-label">Plantation Model</div>', unsafe_allow_html=True)
    m_sel = st.selectbox(
        "model", range(len(MODELS)),
        index=kyaari['default_m'],
        format_func=lambda i: f"M{MODELS[i]['id']} · {MODELS[i]['sub']}",
        label_visibility="collapsed",
    )

model = MODELS[m_sel]
area_ha = kyaari['area_ha'] or (_area(kyaari['polygon'])/10000)

# ── COMPUTE ───────────────────────────────────────────────────────
groups = _cached_groups(kyaari['id'], model['id'], kyaari)
total  = sum(len(g['pts']) for g in groups)

# ── MAP ───────────────────────────────────────────────────────────
fm = build_map(kyaari, model, groups)
st_folium(fm, height=520, use_container_width=True, returned_objects=[])

# ── SPECIES CARDS ─────────────────────────────────────────────────
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
card_cols = st.columns(len(groups)+1, gap="small")

for i, (col, g) in enumerate(zip(card_cols, groups)):
    sp=g['sp']; count=len(g['pts'])
    with col:
        st.markdown(f"""
        <div class="sp-card" style="--c:{sp['col']}">
          <div class="sp-card-name">{sp['name']}</div>
          <div class="sp-card-num">{count}</div>
          <div class="sp-card-sub">{ROLE_LABEL.get(sp['role'],'')} · {sp['spacing']}</div>
        </div>""", unsafe_allow_html=True)

with card_cols[-1]:
    st.markdown(f"""
    <div class="total-card">
      <div class="total-card-label">Total Trees</div>
      <div class="total-card-num">{total}</div>
      <div class="total-card-sub">{area_ha:.2f} ha plot</div>
    </div>""", unsafe_allow_html=True)

# ── ROW BREAKDOWN (shown when block rows ≥ 7 — Atul Step 5a) ─────
block_groups = [g for g in groups if g['sp']['role'] in ('block-a','block-b') and g.get('rows')]
if block_groups and max(len(g['rows']) for g in block_groups) >= 7:
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    rows_html = '<div class="info-card"><div class="info-label">Row Breakdown</div><div style="display:flex;gap:20px;flex-wrap:wrap">'
    for g in block_groups:
        sp=g['sp']
        row_lines = ''.join(
            f'<span style="display:inline-block;min-width:56px;font-size:11px;color:#2A3A28">'
            f'Row {ri+1}: <b>{cnt}</b></span>'
            for ri,cnt in enumerate(g['rows'])
        )
        rows_html += (
            f'<div><div style="font-size:10px;font-weight:700;color:{sp["col"]};'
            f'text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px">'
            f'{sp["name"]} — {len(g["rows"])} rows</div>'
            f'<div style="line-height:1.8">{row_lines}</div></div>'
        )
    rows_html += '</div></div>'
    st.markdown(rows_html, unsafe_allow_html=True)

# ── INFO + PERFORMANCE ────────────────────────────────────────────
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
ic1, ic2 = st.columns([1,1], gap="small")

rs_cls    = STATUS_STYLE.get(kyaari['rs_status'],    'tag-grey')
ver_cls   = STATUS_STYLE.get(kyaari['verif_status'], 'tag-grey')
kml_sp    = kyaari['species_str'] or '—'

with ic1:
    st.markdown(f"""
    <div class="info-card">
      <div class="info-label">Kyaari Info</div>
      <div class="info-row">
        <b>ID {kyaari['id']}</b> &nbsp;·&nbsp; {kyaari['village']}, {kyaari['dist']}<br>
        Farmer: <b>{kyaari['farmer']}</b><br>
        Area: <b>{area_ha:.2f} ha</b> &nbsp;·&nbsp; {kyaari['total_plants']} plants recorded<br>
        Species: {kml_sp}
      </div>
      <div style="margin-top:8px">
        <span class="tag {rs_cls}">RS: {kyaari['rs_status'] or '—'}</span>
        <span class="tag {ver_cls}">Verified: {kyaari['verif_status'] or '—'}</span>
      </div>
    </div>""", unsafe_allow_html=True)

with ic2:
    st.markdown(f"""
    <div class="info-card">
      <div class="info-label">Model Performance</div>
      <div class="credit-big">{model['credit']}</div>
      <div class="credit-unit">tCO₂e / ha / yr</div>
      <div class="credit-meta">
        {model['totalPerHa']:.0f} trees / ha target<br>
        Recommended: {model['size']}
      </div>
    </div>""", unsafe_allow_html=True)

st.markdown(f"""
<div class="model-desc">
  <b>{model['type']}</b> &nbsp;·&nbsp; {model['desc']}
</div>""", unsafe_allow_html=True)
