from flask import Flask, Response

app = Flask(__name__)

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Geo Regreen | Operational Mine Rehabilitation Screening</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
:root{--bg:#070f14;--panel:#0e1b23;--panel2:#12232d;--line:#203742;--text:#eaf2f4;--muted:#8da3ad;--mint:#71e0bd;--blue:#7ec0ff;--amber:#f3c16a;--red:#ff7d76;--radius:16px}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(600px at 80% -20%,#13433d 0%,transparent 60%),var(--bg);color:var(--text);font:14px/1.5 Inter,system-ui,sans-serif}
.shell{max-width:1480px;margin:auto;padding:20px 22px}
.top{display:flex;justify-content:space-between;align-items:center;gap:16px;border-bottom:1px solid var(--line);padding-bottom:16px}
.brand{display:flex;gap:12px;align-items:center}.mark{width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,#71e0bd,#2f8d82);display:grid;place-items:center;font-weight:900;color:#05201c;font-size:22px}
.kpi-row{display:flex;gap:10px;flex-wrap:wrap}.kpi{border:1px solid var(--line);background:var(--panel);padding:8px 12px;border-radius:999px;font-size:11px;letter-spacing:.06em}.kpi b{color:var(--mint)}
.grid{display:grid;grid-template-columns:1.25fr .75fr;gap:14px;margin-top:18px}
.card{background:linear-gradient(180deg,#13232d,#0e1b23);border:1px solid var(--line);border-radius:var(--radius);padding:16px;box-shadow:0 20px 60px #00000040}
.card h2{margin:0;font-size:14px;letter-spacing:-.02em}.sub{color:var(--muted);font-size:11px}
#map{height:460px;border-radius:12px;border:1px solid #2a4a56;background:#0a1a20}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.btn{border:1px solid var(--line);background:#0c1a20;color:var(--text);padding:8px 11px;border-radius:10px;font-size:11px;font-weight:600;cursor:pointer}
.btn.active{background:#14332e;color:var(--mint);border-color:#2d6b5d}
.metric-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px}
.metric{border:1px solid var(--line);background:#0a1820;border-radius:12px;padding:12px}.metric span{color:var(--muted);font-size:10px;display:block}.metric strong{font-size:22px;display:block}
.table{width:100%;border-collapse:collapse;margin-top:10px;font-size:11px}.table th{color:var(--muted);text-align:left;font-weight:600;border-bottom:1px solid var(--line);padding:8px}.table td{padding:10px 8px;border-bottom:1px solid #1a2f38}
.badge{padding:3px 8px;border-radius:999px;font-size:10px;font-weight:800}.b-red{background:#3d2220;color:var(--red)}.b-amber{background:#3a2d1a;color:var(--amber)}.b-green{background:#132e27;color:var(--mint)}
.timeline-wrap{margin-top:14px}.range{width:100%;accent-color:var(--mint)}
.foot{display:flex;justify-content:space-between;color:var(--muted);font-size:10px;margin-top:18px;border-top:1px solid var(--line);padding-top:12px}
@media(max-width:1000px){.grid{grid-template-columns:1fr}.metric-grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="shell">
<header class="top">
<div class="brand"><div class="mark">G</div><div><strong style="letter-spacing:.14em;font-size:13px">GEO REGREEN</strong><div class="sub">Operational Screening Platform · Mpumalanga Pilot</div></div></div>
<div class="kpi-row">
<span class="kpi">FEED: <b>SENTINEL-2 L2A · 10m</b> · 2026-10-26</span>
<span class="kpi">COVERAGE: <b>1,240 ha</b> · 3 SITES</span>
<span class="kpi">STATUS: <b style="color:var(--amber)">FIELD VALIDATION REQUIRED</b></span>
</div>
</header>
<div style="display:flex;justify-content:space-between;gap:16px;align-items:end;margin:18px 0">
<div><div style="color:var(--mint);font-size:10px;letter-spacing:.15em;font-weight:800">MINE REHABILITATION INTELLIGENCE</div><h1 style="font-size:clamp(28px,3.2vw,40px);line-height:1.05;margin:8px 0;letter-spacing:-.04em">Find the failure before<br>the audit does.</h1><p class="sub" style="max-width:720px">Live screening from public satellite + client site records. Every flag shows source, date, confidence and next field action. No black box.</p></div>
<div><button class="btn" id="exportBtn">Export CSV · Inspection Pack</button></div>
</div>
<div class="grid">
<div class="card">
<div style="display:flex;justify-content:space-between"><div><h2>Operational Screening Map</h2><div class="sub">Khwezela Colliery · AOI v1.3 · Public data demo</div></div><span class="badge b-amber">18.6 ha FLAGGED FOR REVIEW</span></div>
<div id="map"></div>
<div class="toolbar">
<button class="btn active" data-layer="risk">Risk Priority</button>
<button class="btn" data-layer="ndvi">NDVI Recovery</button>
<button class="btn" data-layer="water">Surface Water</button>
<button class="btn" data-layer="disturb">Disturbance Change</button>
<button class="btn" data-layer="ghg">GHG Layer · Plug-in Ready</button>
</div>
<div class="timeline-wrap"><div class="sub" style="display:flex;justify-content:space-between"><span>Observation window: 90 days</span><span id="dateLabel">Day 90 · 2026-10-26</span></div><input class="range" type="range" id="timeSlider" min="0" max="90" value="90"></div>
<div class="metric-grid">
<div class="metric"><span>Flags requiring inspection</span><strong>3 zones</strong><span style="color:var(--amber)">Confidence 0.72 - 0.84</span></div>
<div class="metric"><span>Last clear observation</span><strong>2 days ago</strong><span>Source: S2 · Cloud <12%</span></div>
<div class="metric"><span>Next scheduled check</span><strong>Daily scan</strong><span>Automated · Slack alert</span></div>
</div>
</div>
<div class="card">
<h2>Priority Inspection Queue</h2><div class="sub">Actionable, not analytical. For env manager + rehab contractor.</div>
<table class="table" id="queueTable">
<tr><th>Zone</th><th>Signal</th><th>Conf</th><th>Action</th></tr>
<tr><td><span class="badge b-red">ZONE B</span></td><td>Land change vs baseline +84% | NDVI drop 0.31 | Date: 2026-10-24</td><td>0.84</td><td>Drone + soil</td></tr>
<tr><td><span class="badge b-amber">ZONE A</span></td><td>Water extent +22% vs 30d | Rainfall 18mm | Date: 2026-10-22</td><td>0.76</td><td>Drainage check</td></tr>
<tr><td><span class="badge b-green">ZONE D</span></td><td>NDVI recovery +0.18 | Below target 0.45 | Date: 2026-10-26</td><td>0.72</td><td>Verify species</td></tr>
</table>
<div style="margin-top:16px"><h2>Evidence & Provenance</h2><div class="sub" id="provText">Every detection includes: sensor, resolution, cloud cover, observation date, baseline period, and confidence. Required for audit trail.</div>
<div style="margin-top:12px;border:1px dashed #2e4a56;border-radius:10px;padding:12px;font-size:11px;color:var(--muted)">
<b style="color:var(--text)">GHG Module:</b> Architecture ready for licensed CH4/CO2 products (GHGSat, CarbonMapper). UI shows resolution, detection threshold, uncertainty. No gas data rendered until licensed feed connected.
</div>
</div>
</div>
</div>
<footer class="foot"><span>© Geo Regreen · Operational pilot · Data: Copernicus Sentinel-2 · Field verification required before compliance use</span><span>Built for rehab managers, not for papers</span></footer>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const map = L.map('map',{zoomControl:false}).setView([-26.15,29.2],12);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'© OSM'}).addTo(map);
const zones = [
L.polygon([[-26.08,29.1],[-26.07,29.18],[-26.11,29.2],[-26.13,29.14]],{color:'#ff7d76',fillOpacity:.25}).addTo(map).bindPopup('ZONE B · High priority · 0.84'),
L.polygon([[-26.12,29.05],[-26.10,29.09],[-26.14,29.12],[-26.16,29.07]],{color:'#f3c16a',fillOpacity:.22}).addTo(map).bindPopup('ZONE A · Monitor'),
L.polygon([[-26.20,29.15],[-26.18,29.22],[-26.22,29.25],[-26.24,29.18]],{color:'#f3c16a',fillOpacity:.18}).addTo(map),
L.polygon([[-26.18,29.08],[-26.16,29.12],[-26.19,29.15],[-26.21,29.10]],{color:'#71e0bd',fillOpacity:.22}).addTo(map),
];
document.querySelectorAll('[data-layer]').forEach(b=>b.onclick=()=>{
document.querySelectorAll('[data-layer]').forEach(x=>x.classList.remove('active'));b.classList.add('active');
const texts={risk:'Risk priority combines NDVI trend, water change and disturbance. Confidence from cloud cover + baseline length.',ndvi:'NDVI L2A 10m · Cloud <12% · Baseline: 2026-07-26 to 2026-10-26 · Seasonal correction applied.',water:'Surface water: Sentinel-2 NDWI + rainfall overlay. Flag if extent >20% vs 30d median.',disturb:'Disturbance: Land-cover change vs approved mine plan boundary. Requires mine plan upload.',ghg:'GHG: Plug-in architecture. Requires licensed feed, shows detection limit (ppb), wind, uncertainty.'}
document.getElementById('provText').textContent=texts[b.dataset.layer];
const colors={risk:'#ff7d76',ndvi:'#71e0bd',water:'#7ec0ff',disturb:'#f3c16a',ghg:'#bda7ff'};
zones.forEach(p=>p.setStyle({color:colors[b.dataset.layer]||'#71e0bd'}));
});
document.getElementById('timeSlider').oninput=e=>{document.getElementById('dateLabel').textContent='Day '+e.target.value+' · 2026-10-26';};
document.getElementById('exportBtn').onclick=()=>{
let csv='zone,signal,confidence,date,source,action\\nB,Land change 84%,0.84,2026-10-24,S2 L2A,Drone+soil\\nA,Water +22%,0.76,2026-10-22,S2 NDWI,Drainage\\nD,NDVI recovery,0.72,2026-10-26,S2 NDVI,Verify';
let blob=new Blob([csv],{type:'text/csv'});let a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='georegreen_inspection_pack.csv';a.click();
};
</script>
</body>
</html>
"""

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    return Response(HTML, mimetype='text/html')

# Vercel requires this
app = app