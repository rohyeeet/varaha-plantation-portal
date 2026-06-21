import streamlit as st
import folium
from streamlit_folium import st_folium
import math
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

/* Header */
.portal-header{
  display:flex;align-items:baseline;gap:10px;
  padding:18px 0 10px;border-bottom:1px solid #D8DDD0;margin-bottom:14px
}
.portal-brand{font-size:11px;font-weight:800;letter-spacing:.15em;
  color:#2D7A1A;text-transform:uppercase}
.portal-title{font-size:20px;font-weight:800;color:#0F2218;margin:0}

/* Selector labels */
.sel-label{font-size:10px;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:#7A8E78;margin-bottom:3px}
.stSelectbox label{display:none!important}
.stSelectbox [data-baseweb="select"]{border-radius:8px!important}

/* Species card */
.sp-card{background:#fff;border-radius:10px;padding:14px 16px;
  border-top:4px solid var(--c);box-shadow:0 1px 3px rgba(0,0,0,.07)}
.sp-card-name{font-size:11px;font-weight:700;color:#4A6A48;margin-bottom:2px}
.sp-card-num{font-size:34px;font-weight:900;color:#0F2218;line-height:1}
.sp-card-sub{font-size:10px;color:#9AA898;margin-top:3px}

/* Total card */
.total-card{background:#0F2218;border-radius:10px;padding:14px 16px;
  display:flex;flex-direction:column;justify-content:space-between;
  box-shadow:0 1px 3px rgba(0,0,0,.15)}
.total-card-label{font-size:10px;font-weight:700;letter-spacing:.08em;
  color:#6DB87A;text-transform:uppercase}
.total-card-num{font-size:34px;font-weight:900;color:#fff;line-height:1;margin-top:4px}
.total-card-sub{font-size:10px;color:#4A7A54;margin-top:3px}

/* Info row */
.info-card{background:#fff;border-radius:10px;padding:14px 16px;
  box-shadow:0 1px 3px rgba(0,0,0,.07)}
.info-label{font-size:10px;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;color:#7A8E78;margin-bottom:8px}
.info-row{font-size:13px;color:#2A3A28;line-height:1.8}
.info-row b{color:#0F2218}

.credit-big{font-size:28px;font-weight:900;color:#1A5A1A}
.credit-unit{font-size:11px;color:#4A7A4A;font-weight:600}
.credit-meta{font-size:12px;color:#5A8A58;margin-top:6px;line-height:1.7}

/* Model desc */
.model-desc{font-size:12px;color:#5A6E58;background:#EEF2EA;border-radius:8px;
  padding:10px 14px;margin-top:10px;line-height:1.6}
.model-desc b{color:#2A4A28}
</style>
""", unsafe_allow_html=True)

# ─── DATA ────────────────────────────────────────────────────────

KYAARIS = [
    {"id":"K001","label":"K001 — Nandyal Block A","farmer":"Rajan Kumar",
     "dist":"Nandyal, AP","shape":"Rectangle",
     "anchor":(15.4780,78.4840),
     "polygon":[[0,0],[100,0],[100,50],[0,50]],
     "farmPoly":[[-18,-18],[118,-18],[118,68],[-18,68]]},
    {"id":"K002","label":"K002 — Kurnool Block C","farmer":"Suresh Reddy",
     "dist":"Kurnool, AP","shape":"Irregular Quad",
     "anchor":(15.8200,78.0350),
     "polygon":[[0,0],[120,10],[110,80],[-10,70]],
     "farmPoly":[[-24,-18],[144,5],[130,100],[-26,90]]},
    {"id":"K003","label":"K003 — Chittoor Block B","farmer":"Lakshmi Devi",
     "dist":"Chittoor, AP","shape":"Triangle",
     "anchor":(13.2150,79.1000),
     "polygon":[[0,0],[120,0],[60,80]],
     "farmPoly":[[-16,-16],[136,-16],[78,100],[-16,100]]},
    {"id":"K004","label":"K004 — Prakasam Block A","farmer":"Venkat Rao",
     "dist":"Prakasam, AP","shape":"Pentagon",
     "anchor":(15.3400,79.5500),
     "polygon":[[20,0],[130,0],[150,60],[80,100],[0,60]],
     "farmPoly":[[5,-18],[145,-18],[170,70],[82,122],[-16,70]]},
    {"id":"K005","label":"K005 — Nellore Block D","farmer":"Bala Krishna",
     "dist":"Nellore, AP","shape":"Hexagon",
     "anchor":(14.4450,79.9860),
     "polygon":[[0,20],[30,0],[150,0],[160,30],[140,110],[10,100]],
     "farmPoly":[[-16,8],[18,-18],[165,-18],[180,26],[156,128],[-2,122]]},
]

MODELS = [
    {"id":1,"name":"Model 1","sub":"Mango · Red Sanders · Coconut",
     "type":"Boundary + Alley Block","size":">0.8 ha","credit":6.744,"totalPerHa":356.22,
     "desc":"Red Sanders boundary at 3 m. Mango fills block at 6×6 m. Coconut in top/bottom alley rows at 9×5 m.",
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
     "desc":"No boundary. Three vertical zones: Jackfruit 45% at 5×5 m, Sapota 28% at 6×6 m, Jamun 27% at 5×5 m.",
     "sp":[
        {"name":"Jackfruit","col":"#1E8449","spacing":"5×5 m","perHa":158.4,"role":"zone","sx":5,"sy":5,"zs":.449},
        {"name":"Sapota","col":"#8E44AD","spacing":"6×6 m","perHa":100,"role":"zone","sx":6,"sy":6,"zs":.283},
        {"name":"Jamun","col":"#6C3483","spacing":"5×5 m","perHa":94.4,"role":"zone","sx":5,"sy":5,"zs":.268},
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
     "desc":"No boundary. Three vertical zones: Jackfruit 45% at 5×5 m, Mango 28% at 6×6 m, Jamun 27% at 5×5 m.",
     "sp":[
        {"name":"Jackfruit","col":"#1E8449","spacing":"5×5 m","perHa":158.4,"role":"zone","sx":5,"sy":5,"zs":.449},
        {"name":"Mango","col":"#E8940A","spacing":"6×6 m","perHa":100,"role":"zone","sx":6,"sy":6,"zs":.283},
        {"name":"Jamun","col":"#6C3483","spacing":"5×5 m","perHa":94.4,"role":"zone","sx":5,"sy":5,"zs":.268},
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

# ─── GIS ENGINE ──────────────────────────────────────────────────

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
    return dict(x0=min(xs), x1=max(xs), y0=min(ys), y1=max(ys))

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
            pts.append([p1[0]+dx*ep, p1[1]+dy*ep])
        cum+=el-ep
    return pts

def _walk_boundary_targeted(coords, target):
    if target<=0: return []
    return _walk_boundary(coords, _perim(coords)/target)

def _in_bands(v, bands):
    return any(lo<=v<=hi for lo,hi in bands)

def _place_alley(block, sx, sy, role, bb, target):
    """
    Place alley trees and return (pts, y_exclusion_bands, x_exclusion_bands).
    y_bands: row y-ranges blocked for block-a/b species (alley / alley-3)
    x_bands: col x-ranges blocked for block-a/b species (alley-long)
    """
    pts=[]; y_bands=[]; x_bands=[]
    W=bb['x1']-bb['x0']; H=bb['y1']-bb['y0']
    is_long = (role=='alley-long') or (W < H)

    if is_long:
        # Alley columns run along left and right long edges (walk in y)
        col_spacing = sy   # distance between adjacent alley column centres
        tpr = max(1, int(H/sx))              # trees per column (walk in y at sx)
        base = max(1, round(target/(2*tpr)))
        npairs = base
        for p in range(npairs):
            x0=bb['x0']+col_spacing/2+p*col_spacing
            x1=bb['x1']-col_spacing/2-p*col_spacing
            if x0>=x1: break
            # Exclusion bands in x (half a spacing either side of the column centre)
            x_bands.append([x0-col_spacing/2, x0+col_spacing/2])
            if abs(x1-x0)>col_spacing:
                x_bands.append([x1-col_spacing/2, x1+col_spacing/2])
            y=bb['y0']+sx/2
            while y<=bb['y1']:
                if _pip([x0,y],block): pts.append([x0,y])
                if abs(x1-x0)>col_spacing and _pip([x1,y],block): pts.append([x1,y])
                y+=sx
    else:
        # Alley rows run along top and bottom (walk in x)
        row_spacing = sy   # distance between adjacent alley row centres
        tpr = max(1, int(W/sx))
        base = max(1, round(target/(2*tpr)))
        npairs = max(3, base) if role=='alley-3' else base
        for p in range(npairs):
            y0=bb['y0']+row_spacing/2+p*row_spacing
            y1=bb['y1']-row_spacing/2-p*row_spacing
            if y0>=y1: break
            y_bands.append([y0-row_spacing/2, y0+row_spacing/2])
            if y1-y0>row_spacing:
                y_bands.append([y1-row_spacing/2, y1+row_spacing/2])
            x=bb['x0']+sx/2
            while x<=bb['x1']:
                if _pip([x,y0],block): pts.append([x,y0])
                if y1-y0>row_spacing and _pip([x,y1],block): pts.append([x,y1])
                x+=sx

    return pts, y_bands, x_bands

def _bresenham_b(R, wa, wb):
    """Row indices assigned to species B, evenly distributed."""
    if wb==0 or R==0: return set()
    nB=max(0, R-round(R*wa/(wa+wb)))
    if nB==0: return set()
    step=R/nB
    return {int(k*step+step/2) for k in range(nB)}

def compute_groups(k_idx, m_idx):
    kyaari=KYAARIS[k_idx]; model=MODELS[m_idx]
    poly=kyaari['polygon']
    area_ha=_area(poly)/10000
    inner=_safe_inset(poly,1)
    has_zones=any(s['role']=='zone' for s in model['sp'])
    block=inner if has_zones else _safe_inset(poly,5)
    bb=_bbox(block)
    groups=[{'sp':s,'pts':[]} for s in model['sp']]

    # ── Boundary ──────────────────────────────────────────────────
    for i,s in enumerate(model['sp']):
        if s['role']=='boundary':
            groups[i]['pts']=_walk_boundary_targeted(inner, round(area_ha*s['perHa']))

    # ── Zone models (M9, M12) ─────────────────────────────────────
    if has_zones:
        W=bb['x1']-bb['x0']; xc=bb['x0']
        for s in model['sp']:
            if s['role']!='zone': continue
            i=model['sp'].index(s); xe=xc+W*s['zs']
            pts=[]
            y=bb['y0']+s['sy']/2
            while y<=bb['y1']:
                x=bb['x0']+s['sx']/2
                while x<=bb['x1']:
                    if xc-1e-6<=x<xe-1e-6 and _pip([x,y],block):
                        pts.append([x,y])
                    x+=s['sx']
                y+=s['sy']
            groups[i]['pts']=pts; xc=xe
        return groups

    # ── Alley rows/columns ────────────────────────────────────────
    y_bands=[]; x_bands=[]
    for s in model['sp']:
        if not s['role'].startswith('alley'): continue
        i=model['sp'].index(s)
        tc=round(area_ha*s['perHa'])
        pts,yb,xb=_place_alley(block,s['sx'],s['sy'],s['role'],bb,tc)
        groups[i]['pts']=pts; y_bands.extend(yb); x_bands.extend(xb)

    # ── Block grid (no overlap with alley bands) ──────────────────
    sa=next((s for s in model['sp'] if s['role']=='block-a'),None)
    sb=next((s for s in model['sp'] if s['role']=='block-b'),None)
    if sa:
        ia=model['sp'].index(sa); ib=model['sp'].index(sb) if sb else -1
        wa=sa.get('aw',1); wb=sb.get('aw',1) if sb else 0
        sx,sy=sa['sx'],sa['sy']

        # Collect rows not occupied by y-band alley rows
        all_y=[]
        y=bb['y0']+sy/2
        while y<=bb['y1']:
            if not _in_bands(y,y_bands): all_y.append(y)
            y+=sy

        b_rows=_bresenham_b(len(all_y),wa,wb)
        for ri,row_y in enumerate(all_y):
            ti=ib if (ri in b_rows and ib>=0) else ia
            x=bb['x0']+sx/2
            while x<=bb['x1']:
                # Skip x positions occupied by alley-long columns
                if not _in_bands(x,x_bands) and _pip([x,row_y],block):
                    groups[ti]['pts'].append([x,row_y])
                x+=sx

    return groups

# ─── GEO UTILS ───────────────────────────────────────────────────

def _m2ll(pt, anchor):
    x,y=pt; lat0,lng0=anchor
    return [lat0-y/111320, lng0+x/(111320*math.cos(math.radians(lat0)))]

def _poly2ll(coords, anchor):
    return [_m2ll(c,anchor) for c in coords]

# ─── MAP ─────────────────────────────────────────────────────────

GMAPS_KEY = st.secrets.get("GMAPS_KEY", "")

def build_map(k_idx, m_idx, groups):
    kyaari=KYAARIS[k_idx]; model=MODELS[m_idx]
    anchor=kyaari['anchor']
    center=_m2ll(_centroid(kyaari['polygon']),anchor)

    fm=folium.Map(location=center,zoom_start=18,tiles=None,prefer_canvas=True)
    folium.TileLayer(
        tiles=f"https://mt1.google.com/vt/lyrs=s&x={{x}}&y={{y}}&z={{z}}&key={GMAPS_KEY}",
        attr="Google Maps",name="Satellite",max_zoom=21,max_native_zoom=20,
    ).add_to(fm)

    # Farm outer boundary
    folium.Polygon(
        locations=_poly2ll(kyaari['farmPoly'],anchor),
        color='#C8A050',weight=1.5,fill=False,dash_array='10,6',opacity=0.6,
    ).add_to(fm)

    # Kyaari boundary
    folium.Polygon(
        locations=_poly2ll(kyaari['polygon'],anchor),
        color='#27AE60',weight=2.5,fill=True,fill_color='#27AE60',fill_opacity=0.05,
    ).add_to(fm)

    # Zone dividers (M9, M12)
    if any(s['role']=='zone' for s in model['sp']):
        bloc=_safe_inset(kyaari['polygon'],1); bb2=_bbox(bloc)
        W=bb2['x1']-bb2['x0']; xc=bb2['x0']
        for s in [z for z in model['sp'] if z['role']=='zone'][:-1]:
            xc+=W*s['zs']
            folium.PolyLine(
                [_m2ll([xc,bb2['y0']],anchor),_m2ll([xc,bb2['y1']],anchor)],
                color='white',weight=1.5,dash_array='5,4',opacity=0.65,
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
                location=_m2ll(pt,anchor),radius=r,
                color='rgba(255,255,255,0.4)',weight=0.5,
                fill=True,fill_color=sp['col'],fill_opacity=0.9,
                tooltip=f"{sp['name']} · {sp['spacing']}",
            ).add_to(fm)
    return fm

# ─── CACHED COMPUTE ──────────────────────────────────────────────

@st.cache_data(show_spinner="Computing…")
def _cached_groups(k_idx, m_idx):
    return compute_groups(k_idx, m_idx)

ROLE_LABEL={
    'boundary':'Boundary','alley':'Alley rows','alley-long':'Alley cols',
    'alley-3':'3-side alley','block-a':'Block','block-b':'Block','zone':'Zone',
}

# ─── UI ──────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="portal-header">
  <span class="portal-brand">Varaha</span>
  <span class="portal-title">Plantation Portal</span>
</div>
""", unsafe_allow_html=True)

# Selectors row
sc1, sc2 = st.columns([1,2], gap="medium")
with sc1:
    st.markdown('<div class="sel-label">Field Plot</div>', unsafe_allow_html=True)
    k_idx = st.selectbox("fp", range(len(KYAARIS)),
                          format_func=lambda i: KYAARIS[i]['label'],
                          label_visibility="collapsed")
with sc2:
    st.markdown('<div class="sel-label">Plantation Model</div>', unsafe_allow_html=True)
    m_idx = st.selectbox("pm", range(len(MODELS)),
                          format_func=lambda i: f"M{MODELS[i]['id']} · {MODELS[i]['sub']}",
                          label_visibility="collapsed")

kyaari=KYAARIS[k_idx]; model=MODELS[m_idx]
area_ha=round(_area(kyaari['polygon'])/10000,2)

# Compute positions
groups=_cached_groups(k_idx,m_idx)
total=sum(len(g['pts']) for g in groups)

# ── MAP (full width, hero element) ───────────────────────────────
fm=build_map(k_idx,m_idx,groups)
st_folium(fm, height=520, use_container_width=True, returned_objects=[])

# ── SPECIES CARDS ────────────────────────────────────────────────
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
n=len(groups)
card_cols=st.columns(n+1, gap="small")

for i,(col,g) in enumerate(zip(card_cols,groups)):
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
      <div class="total-card-label">Total</div>
      <div class="total-card-num">{total}</div>
      <div class="total-card-sub">trees on map</div>
    </div>""", unsafe_allow_html=True)

# ── PLOT INFO + MODEL PERFORMANCE ────────────────────────────────
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
ic1, ic2 = st.columns([1,1], gap="small")

with ic1:
    st.markdown(f"""
    <div class="info-card">
      <div class="info-label">Plot Info</div>
      <div class="info-row">
        <b>{kyaari['dist']}</b><br>
        {kyaari['farmer']}<br>
        {area_ha} ha &nbsp;·&nbsp; {kyaari['shape']}<br>
        ID: {kyaari['id']}
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

# ── MODEL DESCRIPTION ────────────────────────────────────────────
st.markdown(f"""
<div class="model-desc">
  <b>{model['type']}</b> &nbsp;·&nbsp; {model['desc']}
</div>""", unsafe_allow_html=True)
