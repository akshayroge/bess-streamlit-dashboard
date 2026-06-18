from __future__ import annotations

import re
from pathlib import Path


APP_FILE = Path("app.py")
BACKUP_FILE = Path("app_backup_before_sld_update.py")


NEW_SLD_CSS_BLOCK = r'''
# ============================================================
# CSS — screenshot-style Single Line Diagram override
# ============================================================

st.markdown(
    """
<style>
/* ================= Screenshot-style Single Line Diagram ================= */

.sld-screen{
    border:1px solid #16cbe7;
    border-radius:9px;
    background:
        radial-gradient(circle at 44% 0,rgba(13,209,232,.14),transparent 34%),
        linear-gradient(180deg,#071a2d 0%,#03101d 100%);
    box-shadow:0 18px 42px rgba(0,0,0,.45), inset 0 0 0 1px rgba(20,220,255,.08);
    padding:16px 18px;
    color:white;
}
.sld-screen *{box-sizing:border-box;}

.sld-screen .sld-head{
    display:grid;
    grid-template-columns:1fr auto;
    align-items:start;
    border-bottom:1px solid rgba(130,210,255,.22);
    padding-bottom:12px;
    margin-bottom:14px;
}
.sld-screen .sld-head h2{
    font-size:24px;
    line-height:29px;
    font-weight:900;
    color:#fff;
    margin:0;
    text-shadow:0 0 16px rgba(0,229,255,.28);
}
.sld-sub{
    color:#b9edff;
    font-size:12px;
    line-height:18px;
    margin-top:4px;
}
.sld-screen .sld-meta{
    text-align:right;
    color:#a9eaff;
    font-size:12px;
    line-height:18px;
    font-weight:800;
}

/* Top SLD chain */
.sld-top-grid{
    display:grid;
    grid-template-columns:1fr 24px 1fr 24px 1fr 24px 1.08fr 24px 1fr 24px 1fr;
    gap:0;
    align-items:stretch;
    margin-bottom:14px;
}
.sld-screen .sld-arrow{
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    color:#25dfff;
    font-size:20px;
    font-weight:900;
    text-shadow:0 0 10px #25dfff;
    min-width:24px;
}
.sld-screen .sld-arrow small{
    color:#77eaff;
    font-size:9px;
    line-height:11px;
    margin-top:2px;
    text-shadow:none;
    white-space:normal;
    text-align:center;
}
.sld-screen .sld-node{
    position:relative;
    border-radius:8px;
    background:linear-gradient(180deg,rgba(12,31,50,.96),rgba(4,13,24,.96));
    border:1px solid #22d9ff;
    padding:10px 9px;
    min-height:158px;
    box-shadow:inset 0 0 18px rgba(0,217,255,.08),0 10px 22px rgba(0,0,0,.25);
    overflow:hidden;
}
.sld-screen .sld-node.cell{border-color:#08d39c;}
.sld-screen .sld-node.pack{border-color:#f1b000;}
.sld-screen .sld-node.rack{border-color:#756cff;}
.sld-screen .sld-node.container{border-color:#f0b900;}
.sld-screen .sld-node.pcs{border-color:#ff517c;}
.sld-screen .sld-node.grid{border-color:#29c8ff;}

.sld-screen .sld-node h3{
    margin:0 0 6px;
    color:#fff;
    font-size:14px;
    line-height:17px;
    text-transform:uppercase;
    font-weight:900;
}
.sld-tag{
    position:absolute;
    right:8px;
    top:7px;
    background:#1e708c;
    color:#bdf8ff!important;
    border-radius:999px;
    font-size:9px;
    font-weight:900;
    padding:3px 7px;
}
.sld-icon-area{
    height:52px;
    border-radius:6px;
    background:linear-gradient(135deg,rgba(255,255,255,.06),rgba(255,255,255,.02));
    border:1px solid rgba(255,255,255,.12);
    margin-bottom:7px;
    display:flex;
    align-items:center;
    justify-content:center;
    overflow:hidden;
}
.sld-icon-area img{
    max-width:100%;
    max-height:50px;
    object-fit:contain;
    filter:drop-shadow(0 7px 8px rgba(0,0,0,.55));
}
.sld-screen .sld-kv{
    display:grid;
    grid-template-columns:1fr auto;
    gap:2px 8px;
    font-size:10px;
    line-height:14px;
}
.sld-screen .sld-kv span{color:#aee6ff;}
.sld-screen .sld-kv b{color:#fff;text-align:right;font-weight:900;}

/* Top symbols */
.battery-symbol{
    width:25px;
    height:40px;
    border:3px solid #16d39b;
    border-radius:6px;
    background:#063528;
    position:relative;
    box-shadow:inset 0 0 0 4px rgba(22,211,155,.18);
}
.battery-symbol:before{
    content:'';
    position:absolute;
    top:-7px;
    left:8px;
    width:8px;
    height:5px;
    background:#9df6d3;
    border-radius:2px;
}
.battery-symbol:after{
    content:'LFP';
    position:absolute;
    left:5px;
    top:13px;
    color:#9dffd4;
    font-size:8px;
    font-weight:900;
}
.mini-pack{
    display:grid;
    grid-template-columns:repeat(6,12px);
    gap:4px;
}
.mini-pack span{
    height:30px;
    background:#22b37d;
    border:1px solid #5af0b1;
    border-radius:2px;
}
.rack-icon{
    display:grid;
    grid-template-columns:1fr;
    gap:3px;
    width:48px;
}
.rack-icon span{
    height:8px;
    border:1px solid #f0b000;
    background:#4a2f08;
    border-radius:2px;
}
.container-icon{
    width:74px;
    height:43px;
    border:2px solid #527799;
    border-radius:3px;
    background:repeating-linear-gradient(90deg,#0c1c2e 0 8px,#142f4b 8px 11px);
}
.pcs-placeholder{
    width:74px;
    height:45px;
    border:2px solid #6c7785;
    border-radius:3px;
    background:linear-gradient(135deg,#e2e6ea,#8c939b);
    box-shadow:inset -12px 0 18px rgba(0,0,0,.18);
}
.grid-tower{
    font-size:42px;
    color:#18e4ff;
    line-height:42px;
    font-weight:100;
}

/* Electrical connection path */
.econn{
    border:1px solid rgba(37,212,255,.58);
    border-radius:8px;
    background:rgba(0,0,0,.10);
    padding:13px 14px 12px;
    margin-bottom:12px;
}
.econn-head{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:10px;
}
.econn-head h3{
    color:#6edfff;
    font-size:13px;
    text-transform:uppercase;
    margin:0;
    font-weight:900;
}
.econn-head b{
    color:#fff;
    font-size:12px;
}
.econn-grid{
    display:grid;
    grid-template-columns:1.75fr 18px 1.15fr 18px .72fr 18px 1.2fr 18px .82fr;
    gap:0;
    align-items:stretch;
}
.econn-arrow{
    display:flex;
    align-items:center;
    justify-content:center;
    color:#ff3c2e;
    font-size:16px;
    font-weight:900;
    text-shadow:0 0 7px rgba(255,60,46,.8);
}
.e-card{
    border:1px solid #16cbe7;
    border-radius:7px;
    background:linear-gradient(180deg,rgba(8,23,39,.86),rgba(4,12,22,.9));
    padding:10px;
    min-height:165px;
    overflow:hidden;
}
.e-card h4{
    margin:0 0 8px;
    color:#fff;
    font-size:12px;
    text-transform:uppercase;
    font-weight:900;
}
.e-card .subline{
    color:#9edfff;
    font-size:10px;
    line-height:14px;
    margin-bottom:8px;
}
.packline{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:8px;
}
.packbox{
    border:1px solid #ff3c2e;
    border-radius:5px;
    background:#071522;
    padding:5px;
    min-height:78px;
    text-align:center;
}
.packbox .bars{
    display:flex;
    gap:3px;
    justify-content:center;
    margin-bottom:4px;
}
.packbox .bars i{
    width:8px;
    height:18px;
    background:#47ff8b;
    border-radius:2px;
    display:block;
}
.packbox b{
    display:block;
    color:#fff;
    font-size:10px;
    line-height:12px;
}
.packbox span{
    display:block;
    color:#c8eaff;
    font-size:8px;
    line-height:10px;
}
.fusebar{
    border:1px solid #ff3c2e;
    background:#9a0606;
    border-radius:3px;
    margin-top:4px;
    padding:2px;
    font-size:7px;
    line-height:9px;
    color:#fff;
    font-weight:900;
}
.kv-mini{
    display:grid;
    grid-template-columns:1fr auto;
    gap:4px 7px;
    font-size:10px;
    line-height:14px;
}
.kv-mini span{color:#aee6ff;}
.kv-mini b{
    color:#fff;
    text-align:right;
    font-weight:900;
}
.fuse-symbol{
    height:58px;
    position:relative;
    margin:2px 0 10px;
}
.fuse-symbol:before{
    content:'';
    position:absolute;
    left:35px;
    right:35px;
    top:31px;
    border-top:2px solid #b9dfff;
}
.fuse-symbol:after{
    content:'';
    position:absolute;
    right:40px;
    top:16px;
    width:42px;
    height:2px;
    background:#b9dfff;
    transform:rotate(-28deg);
    transform-origin:left center;
}
.fuse-circle{
    position:absolute;
    left:50%;
    top:25px;
    transform:translateX(-50%);
    width:13px;
    height:13px;
    border:2px solid #b9dfff;
    border-radius:50%;
    background:#071522;
}
.dc-bus-rect{
    width:70px;
    height:92px;
    margin:0 auto 8px;
    display:flex;
    align-items:center;
    justify-content:center;
    border:1px solid #6eb6ff;
    border-radius:7px;
    background:linear-gradient(180deg,#3374db,#184494);
    color:white;
    font-weight:900;
    font-size:12px;
}
.cc-panel-title{
    border-bottom:1px solid rgba(110,220,255,.3);
    padding-bottom:7px;
    color:#9edfff;
    text-align:center;
    font-size:10px;
    margin-bottom:18px;
}
.cc-panel-mid{
    height:38px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:13px;
    font-weight:900;
    color:#fff;
}
.e-pcs-img{
    height:72px;
    border:1px solid rgba(255,255,255,.12);
    border-radius:6px;
    display:flex;
    align-items:center;
    justify-content:center;
    margin-bottom:6px;
    background:rgba(255,255,255,.04);
}
.e-pcs-img img{
    width:100%;
    max-height:62px;
    object-fit:contain;
    border-radius:5px;
    filter:drop-shadow(0 7px 8px rgba(0,0,0,.55));
}
.e-stats{
    display:grid;
    grid-template-columns:1.15fr 1fr 1fr 1fr;
    gap:8px;
    margin-top:10px;
}
.e-stat{
    border:1px solid #173b62;
    border-radius:6px;
    background:rgba(9,22,39,.72);
    padding:8px 10px;
}
.e-stat span{
    display:block;
    color:#9edfff;
    font-size:10px;
    margin-bottom:3px;
}
.e-stat b{
    display:block;
    color:#fff;
    font-size:13px;
    font-weight:900;
}

/* Detail panels */
.detail-grid{
    display:grid;
    grid-template-columns:1.1fr .9fr 1fr;
    gap:14px;
    margin-bottom:12px;
}
.detail-panel{
    border:1px solid #173b62;
    border-radius:8px;
    background:rgba(9,22,39,.92);
    padding:12px 14px;
    min-height:225px;
}
.detail-panel h3{
    color:#6edfff;
    font-size:13px;
    text-transform:uppercase;
    margin:0 0 10px;
    font-weight:900;
}
.detail-pack-row{
    display:grid;
    grid-template-columns:repeat(4,1fr) 1.2fr;
    gap:8px;
    align-items:center;
    margin-bottom:9px;
}
.detail-pack{
    height:42px;
    border:1px solid #f0b000;
    border-radius:5px;
    background:#2d2509;
    display:flex;
    align-items:center;
    justify-content:center;
}
.detail-pack i{
    display:block;
    width:45px;
    height:18px;
    border:1px solid #00e983;
    background:repeating-linear-gradient(90deg,#38f26f 0 7px,transparent 7px 11px);
}
.series-copy{
    color:#ffdf60;
    font-size:11px;
    line-height:14px;
    font-weight:900;
}
.protect-row{
    display:grid;
    grid-template-columns:1fr 1fr 1fr;
    gap:0;
    border:1px dashed #765cff;
    border-radius:7px;
    overflow:hidden;
    margin-bottom:8px;
}
.protect-cell{
    padding:9px 7px;
    text-align:center;
    background:rgba(55,46,122,.12);
    border-right:1px dashed #765cff;
}
.protect-cell:last-child{border-right:0;}
.protect-cell span{
    display:block;
    color:#aee6ff;
    font-size:10px;
    margin-bottom:3px;
}
.protect-cell b{
    display:block;
    color:white;
    font-size:14px;
    font-weight:900;
}
.note-orange{
    border-left:3px solid #ff8a35;
    border-radius:5px;
    background:rgba(255,107,50,.10);
    padding:7px 8px;
    color:#fff;
    font-size:10px;
    line-height:14px;
}
.busbar{
    height:18px;
    border-radius:99px;
    background:linear-gradient(90deg,#25c5f4,#2df09c);
    box-shadow:0 0 16px rgba(39,223,207,.42);
    margin:2px 0 10px;
}
.bus-container-box{
    border:1px solid #f0b000;
    border-radius:7px;
    background:rgba(80,55,7,.25);
    padding:9px;
    display:grid;
    grid-template-columns:88px 1fr;
    gap:10px;
    align-items:center;
    margin-bottom:11px;
}
.bus-container-img{
    height:58px;
    border:1px solid rgba(255,255,255,.16);
    border-radius:5px;
    display:flex;
    align-items:center;
    justify-content:center;
    background:rgba(255,255,255,.04);
}
.bus-container-img img{
    width:100%;
    max-height:58px;
    object-fit:contain;
}
.bus-copy{
    font-size:10px;
    line-height:14px;
    color:#fff;
}
.bus-copy b{color:#ffdf60;}
.bus-tiles{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:8px;
}
.bus-tile{
    border:1px solid #173b62;
    border-radius:6px;
    background:#0a1d33;
    padding:9px;
}
.bus-tile span{
    display:block;
    color:#b9e9ff;
    font-size:10px;
    margin-bottom:5px;
}
.bus-tile b{
    display:block;
    color:#fff;
    font-size:18px;
    font-weight:900;
}
.coordination{
    display:grid;
    grid-template-columns:1fr 20px 1fr 20px 1fr;
    gap:8px;
    align-items:center;
    margin-bottom:10px;
}
.coord-box{
    border:1px solid #f0b000;
    border-radius:6px;
    background:linear-gradient(180deg,#403006,#141e29);
    text-align:center;
    padding:10px 6px;
    min-height:73px;
}
.coord-box span{
    display:block;
    color:#ffdd82;
    font-size:10px;
    margin-bottom:4px;
}
.coord-box b{
    display:block;
    color:white;
    font-size:18px;
    font-weight:900;
}
.coord-box small{
    color:#b9e9ff;
    font-size:8px;
}
.coord-arrow{
    color:#ffb84d;
    text-align:center;
    font-size:20px;
    font-weight:900;
}
.bmu-grid{
    display:grid;
    grid-template-columns:1fr 1fr 1fr;
    gap:8px;
    margin-top:10px;
}
.bmu-tile{
    border:1px solid #173b62;
    border-radius:6px;
    background:#0a1d33;
    padding:8px;
    text-align:center;
}
.bmu-tile span{
    display:block;
    color:#b9e9ff;
    font-size:10px;
}
.bmu-tile b{
    display:block;
    color:white;
    font-size:14px;
    margin-top:2px;
}

/* Bottom SLD summary */
.sld-bottom{
    display:grid;
    grid-template-columns:repeat(6,1fr);
    gap:1px;
    border:1px solid rgba(90,175,235,.35);
    border-radius:7px;
    background:rgba(8,23,39,.75);
    overflow:hidden;
}
.sld-sum{
    padding:11px 13px;
}
.sld-sum span{
    display:block;
    color:#9fdcff;
    font-size:11px;
    margin-bottom:6px;
}
.sld-sum b{
    display:block;
    color:#fff;
    font-size:16px;
    font-weight:900;
}

@media(max-width:1100px){
    .sld-top-grid,
    .econn-grid,
    .e-stats,
    .detail-grid,
    .sld-bottom{
        grid-template-columns:1fr !important;
    }
    .sld-screen .sld-arrow,
    .econn-arrow{
        display:none !important;
    }
    .sld-screen .sld-node{
        min-height:auto;
    }
    .econn-grid{
        gap:10px;
    }
}
</style>
""",
    unsafe_allow_html=True,
)
'''


NEW_CALCULATE_STATE = r'''
def calculate_state(
    battery: Dict[str, Any],
    c_case: Dict[str, Any],
    pcs: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[str]]:
    warnings: List[str] = []

    cell = battery.get("cell") or {}
    pack = battery.get("pack") or {}
    rack = battery.get("rack") or {}
    container = battery.get("container") or {}

    cell_nom_v = prefer_float(cell.get("nominal_voltage_v"))
    cell_min_v = prefer_float(cell.get("min_voltage_v"))
    cell_max_v = prefer_float(cell.get("max_voltage_v"))
    cell_cap_ah = prefer_float(cell.get("nominal_capacity_ah"))

    cell_energy_wh = prefer_float(
        cell.get("cell_energy_wh"),
        None if cell_nom_v is None or cell_cap_ah is None else cell_nom_v * cell_cap_ah,
    )

    cell_energy_kwh = None if cell_energy_wh is None else cell_energy_wh / 1000

    pack_series = prefer_float(pack.get("series_s"))
    pack_parallel = prefer_float(pack.get("parallel_p"), 1)

    pack_total_cells = prefer_float(
        pack.get("total_cells"),
        None if pack_series is None or pack_parallel is None else pack_series * pack_parallel,
    )

    pack_cap_ah = prefer_float(
        pack.get("nominal_capacity_ah"),
        None if cell_cap_ah is None or pack_parallel is None else cell_cap_ah * pack_parallel,
    )

    pack_nom_v = prefer_float(
        pack.get("nominal_voltage_v"),
        None if cell_nom_v is None or pack_series is None else cell_nom_v * pack_series,
    )

    pack_min_v = prefer_float(
        pack.get("min_voltage_v"),
        None if cell_min_v is None or pack_series is None else cell_min_v * pack_series,
    )

    pack_max_v = prefer_float(
        pack.get("max_voltage_v"),
        None if cell_max_v is None or pack_series is None else cell_max_v * pack_series,
    )

    pack_energy_kwh = prefer_float(
        pack.get("nominal_energy_kwh"),
        None if pack_nom_v is None or pack_cap_ah is None else pack_nom_v * pack_cap_ah / 1000,
    )

    packs_per_rack = prefer_float(rack.get("packs_per_rack"))
    rack_connection = str(rack.get("pack_connection") or "Series")

    rack_total_series_cells = prefer_float(
        rack.get("total_series_cells"),
        None if pack_series is None or packs_per_rack is None else pack_series * packs_per_rack,
    )

    rack_cap_ah = prefer_float(rack.get("nominal_capacity_ah"), pack_cap_ah)

    if rack_connection.lower().startswith("series"):
        calc_rack_nom_v = None if pack_nom_v is None or packs_per_rack is None else pack_nom_v * packs_per_rack
        calc_rack_min_v = None if pack_min_v is None or packs_per_rack is None else pack_min_v * packs_per_rack
        calc_rack_max_v = None if pack_max_v is None or packs_per_rack is None else pack_max_v * packs_per_rack
        calc_rack_energy = None if pack_energy_kwh is None or packs_per_rack is None else pack_energy_kwh * packs_per_rack
    else:
        calc_rack_nom_v = pack_nom_v
        calc_rack_min_v = pack_min_v
        calc_rack_max_v = pack_max_v
        calc_rack_energy = None if pack_energy_kwh is None or packs_per_rack is None else pack_energy_kwh * packs_per_rack

    rack_nom_v = prefer_float(rack.get("nominal_voltage_v"), calc_rack_nom_v)
    rack_min_v = prefer_float(rack.get("min_voltage_v"), calc_rack_min_v)
    rack_max_v = prefer_float(rack.get("max_voltage_v"), calc_rack_max_v)
    rack_energy_kwh = prefer_float(rack.get("nominal_energy_kwh"), calc_rack_energy)

    racks_per_container = prefer_float(container.get("racks_per_container"))

    container_energy_kwh = prefer_float(
        container.get("nominal_energy_kwh"),
        None if rack_energy_kwh is None or racks_per_container is None else rack_energy_kwh * racks_per_container,
    )

    container_energy_mwh = prefer_float(
        container.get("nominal_energy_mwh"),
        None if container_energy_kwh is None else container_energy_kwh / 1000,
    )

    c_rate_label = c_case.get("c_rate")
    c_rate_value = parse_c_rate(c_rate_label)

    power_kw = prefer_float(
        c_case.get("power_kw"),
        None if container_energy_kwh is None or c_rate_value is None else container_energy_kwh * c_rate_value,
    )

    duration_hr = prefer_float(
        c_case.get("duration_hr"),
        None if container_energy_kwh is None or power_kw in (None, 0) else container_energy_kwh / power_kw,
    )

    dc_window_min_v = prefer_float(
        pcs.get("dc_window_min_v"),
        container.get("dc_window_min_v"),
        rack_min_v,
    )

    dc_window_max_v = prefer_float(
        pcs.get("dc_window_max_v"),
        container.get("dc_window_max_v"),
        rack_max_v,
    )

    nominal_dc_bus_v = prefer_float(
        container.get("dc_bus_nominal_voltage_v"),
        rack_nom_v,
    )

    bus_voltage_v = prefer_float(
        rack_max_v,
        dc_window_max_v,
        nominal_dc_bus_v,
    )

    dc_bus_current_a = prefer_float(
        c_case.get("dc_bus_current_a"),
        container.get("dc_bus_current_a"),
        None if power_kw is None or nominal_dc_bus_v in (None, 0) else power_kw * 1000 / nominal_dc_bus_v,
    )

    if c_case.get("dc_bus_current_a") is None:
        warnings.append(
            "DC Bus Current is missing in the selected C-rate row; app used container value or fallback calculation."
        )

    rack_power_kw = None
    if power_kw is not None and racks_per_container not in (None, 0):
        rack_power_kw = power_kw / racks_per_container

    # Screenshot-style string current:
    # Rack Power / Rack Voltage. For Aqua 0.25C:
    # 104.5 kW / 1331.2 V ≈ 78.5 A.
    rack_current_a = prefer_float(
        rack.get("rack_current_a"),
        None if rack_power_kw is None or rack_nom_v in (None, 0) else rack_power_kw * 1000 / rack_nom_v,
    )

    pcs_rating_kw = prefer_float(pcs.get("rated_power_kw"), pcs.get("rated_power_kva"))

    containers_per_pcs = prefer_float(
        c_case.get("containers_per_pcs"),
        None if power_kw in (None, 0) or pcs_rating_kw is None else max(1, math.floor(pcs_rating_kw / power_kw)),
    )

    if c_case.get("containers_per_pcs") is None:
        warnings.append(
            "Containers / PCS is missing in JSON; app estimated it from PCS rating and selected C-rate power."
        )

    racks_per_pcs = prefer_float(
        c_case.get("racks_per_pcs"),
        None if containers_per_pcs is None or racks_per_container is None else containers_per_pcs * racks_per_container,
    )

    power_into_pcs_kw = None
    if containers_per_pcs is not None and power_kw is not None:
        power_into_pcs_kw = containers_per_pcs * power_kw

    max_racks_per_pcs = prefer_float(pcs.get("max_racks_per_pcs"))

    pcs_utilisation_percent = prefer_float(c_case.get("pcs_utilisation_percent"))

    # Screenshot-style PCS utilisation fallback:
    # Max Racks / PCS × Rack Power / PCS Rating.
    # For Aqua 0.25C with APCS4500DOUL:
    # 47 × 104.5 kW / 5000 kVA ≈ 98.2%.
    if pcs_utilisation_percent is None:
        if max_racks_per_pcs is not None and rack_power_kw is not None and pcs_rating_kw not in (None, 0):
            pcs_utilisation_percent = max_racks_per_pcs * rack_power_kw / pcs_rating_kw * 100
        elif power_into_pcs_kw is not None and pcs_rating_kw not in (None, 0):
            pcs_utilisation_percent = power_into_pcs_kw / pcs_rating_kw * 100

    if pcs_utilisation_percent is not None and pcs_utilisation_percent > 100:
        warnings.append(
            f"PCS utilisation is above 100%: {fmt_num(pcs_utilisation_percent, 1)}%. "
            "Check containers_per_pcs, power_kw, or PCS rating."
        )

    if racks_per_pcs is not None and max_racks_per_pcs is not None and racks_per_pcs > max_racks_per_pcs:
        warnings.append(
            f"Racks / PCS ({fmt_num(racks_per_pcs, 0)}) exceeds Max Racks / PCS "
            f"({fmt_num(max_racks_per_pcs, 0)})."
        )

    return {
        "battery": battery,
        "cell": cell,
        "pack": pack,
        "rack": rack,
        "container": container,
        "pcs": pcs,
        "c_case": c_case,

        "cell_nom_v": cell_nom_v,
        "cell_min_v": cell_min_v,
        "cell_max_v": cell_max_v,
        "cell_cap_ah": cell_cap_ah,
        "cell_energy_wh": cell_energy_wh,
        "cell_energy_kwh": cell_energy_kwh,

        "pack_series": pack_series,
        "pack_parallel": pack_parallel,
        "pack_total_cells": pack_total_cells,
        "pack_cap_ah": pack_cap_ah,
        "pack_nom_v": pack_nom_v,
        "pack_min_v": pack_min_v,
        "pack_max_v": pack_max_v,
        "pack_energy_kwh": pack_energy_kwh,

        "packs_per_rack": packs_per_rack,
        "rack_connection": rack_connection,
        "rack_total_series_cells": rack_total_series_cells,
        "rack_cap_ah": rack_cap_ah,
        "rack_nom_v": rack_nom_v,
        "rack_min_v": rack_min_v,
        "rack_max_v": rack_max_v,
        "rack_energy_kwh": rack_energy_kwh,
        "rack_current_a": rack_current_a,
        "rack_power_kw": rack_power_kw,

        "racks_per_container": racks_per_container,
        "container_energy_kwh": container_energy_kwh,
        "container_energy_mwh": container_energy_mwh,

        "c_rate_label": c_rate_label,
        "c_rate_value": c_rate_value,
        "power_kw": power_kw,
        "duration_hr": duration_hr,

        "dc_window_min_v": dc_window_min_v,
        "dc_window_max_v": dc_window_max_v,
        "nominal_dc_bus_v": nominal_dc_bus_v,
        "bus_voltage_v": bus_voltage_v,
        "dc_bus_current_a": dc_bus_current_a,

        "pcs_rating_kw": pcs_rating_kw,
        "containers_per_pcs": containers_per_pcs,
        "racks_per_pcs": racks_per_pcs,
        "power_into_pcs_kw": power_into_pcs_kw,
        "pcs_utilisation_percent": pcs_utilisation_percent,
        "max_racks_per_pcs": max_racks_per_pcs,
    }, warnings
'''


NEW_RENDER_SLD_BLOCK = r'''
def sld_image_or_icon(record: Dict[str, Any], key: str, fallback_html: str) -> str:
    src = get_image_src(record, key)
    if src:
        return f'<img src="{esc(src)}" alt="{esc(key)} image">'
    return fallback_html


def sld_kv(rows: List[Tuple[str, Any]]) -> str:
    return (
        '<div class="sld-kv">'
        + "".join(
            f"<span>{esc(label)}</span><b>{esc(value)}</b>"
            for label, value in rows
        )
        + "</div>"
    )


def render_sld_node(
    css_class: str,
    title: str,
    tag: Optional[str],
    icon_html: str,
    rows: List[Tuple[str, Any]],
) -> str:
    tag_html = f'<div class="sld-tag">{esc(tag)}</div>' if tag else ""
    return f"""
    <div class="sld-node {css_class}">
        <h3>{esc(title)}</h3>
        {tag_html}
        <div class="sld-icon-area">{icon_html}</div>
        {sld_kv(rows)}
    </div>
    """


def render_sld_packbox(idx: int, current: Any, fuse: Any) -> str:
    return f"""
    <div class="packbox">
        <div class="bars"><i></i><i></i><i></i><i></i></div>
        <b>Pack {idx}</b>
        <span>{esc(fmt_unit(current, "A", 1))}</span>
        <div class="fusebar">Fuse: {esc(fmt_unit(fuse, "A", 0))}</div>
    </div>
    """


def render_sld(state: Dict[str, Any]) -> None:
    battery = state["battery"]
    pcs = state["pcs"]
    rack = state["rack"]
    rack_protection = rack.get("protection") or {}

    bus_voltage_v = (
        state.get("bus_voltage_v")
        or state.get("rack_max_v")
        or state.get("dc_window_max_v")
        or state.get("nominal_dc_bus_v")
    )

    container_img = sld_image_or_icon(
        battery,
        "container",
        '<div class="container-icon"></div>',
    )

    pcs_img = sld_image_or_icon(
        pcs,
        "pcs",
        '<div class="pcs-placeholder"></div>',
    )

    pack_fuse_a = get_nested(battery, "protection.pack_fuse_a", None) or 400
    rack_fuse_a = rack.get("rack_fuse_a") or 350
    system_fuse_a = get_nested(battery, "protection.system_fuse_a", None) or 1800
    cc_main_fuse_a = get_nested(battery, "protection.cc_main_fuse_a", None) or 1100
    combiner_fuse_a = get_nested(battery, "protection.combiner_fuse_a", None) or 300
    combiner_power_ka = get_nested(battery, "protection.combiner_power_ka", None) or "25 kA"
    cable_count = get_nested(battery, "electrical.dc_bus_cable_count", None) or "1/0 AWG × 6"
    output_cable = get_nested(battery, "electrical.output_cable", None) or "600 kcmil × 6 runs"
    grid_std = get_nested(battery, "grid.connection_standard", None) or "UL 1741"
    ac_connection = get_nested(battery, "grid.connection", None) or "3-phase"

    bmu_per_string = rack_protection.get("bmu_per_string") or 4
    bcmu_per_string = rack_protection.get("bcmu_per_string") or 1
    bamu_per_container = rack_protection.get("bamu_per_container") or 1

    containers = state["containers_per_pcs"]
    container_word = plural(containers, "container")

    pack_count = int(to_float(state["packs_per_rack"]) or 4)
    pack_count = min(max(pack_count, 1), 4)

    packboxes = "".join(
        render_sld_packbox(i, state["rack_current_a"], rack_fuse_a)
        for i in range(1, pack_count + 1)
    )

    sld_top = f"""
    <div class="sld-top-grid">
        {render_sld_node(
            "cell",
            "Cell",
            None,
            '<div class="battery-symbol"></div>',
            [
                ("Capacity", fmt_unit(state["cell_cap_ah"], "Ah", 0)),
                ("Voltage", fmt_unit(state["cell_nom_v"], "V", 2)),
                ("Energy", fmt_unit(state["cell_energy_kwh"], "kWh", 3)),
            ],
        )}
        <div class="sld-arrow">→<small>×104S</small></div>

        {render_sld_node(
            "pack",
            "Pack",
            None,
            '<div class="mini-pack"><span></span><span></span><span></span><span></span><span></span><span></span></div>',
            [
                ("Config", f"{fmt_num(state['pack_series'],0)}S×{fmt_num(state['pack_parallel'],0)}P"),
                ("Voltage", fmt_unit(state["pack_nom_v"], "V", 1)),
                ("Energy", fmt_unit(state["pack_energy_kwh"], "kWh", 1)),
            ],
        )}
        <div class="sld-arrow">→<small>×4 series</small></div>

        {render_sld_node(
            "rack",
            "Rack / String",
            None,
            '<div class="rack-icon"><span></span><span></span><span></span><span></span></div>',
            [
                ("Voltage", fmt_unit(state["rack_nom_v"], "V", 0)),
                ("Current", fmt_unit(state["rack_current_a"], "A", 1)),
                ("Energy", fmt_unit(state["rack_energy_kwh"], "kWh", 0)),
            ],
        )}
        <div class="sld-arrow">→<small>×12 parallel</small></div>

        {render_sld_node(
            "container",
            "Container",
            None,
            container_img,
            [
                ("Energy", fmt_unit(state["container_energy_mwh"], "MWh", 2)),
                ("Bus V", fmt_unit(bus_voltage_v, "V", 1)),
                ("Bus I", fmt_unit(state["dc_bus_current_a"], "A", 1)),
            ],
        )}
        <div class="sld-arrow">→<small>DC</small></div>

        {render_sld_node(
            "pcs",
            "PCS",
            None,
            pcs_img,
            [
                ("Rating", fmt_unit(state["pcs_rating_kw"], "kVA", 0)),
                ("AC", fmt_unit(pcs.get("ac_voltage_v"), "V", 0)),
                ("Eff", fmt_unit(pcs.get("efficiency_percent"), "%", 1)),
            ],
        )}
        <div class="sld-arrow">→<small>AC</small></div>

        {render_sld_node(
            "grid",
            "AC Grid",
            None,
            '<div class="grid-tower">△</div>',
            [
                ("Connection", ac_connection),
                ("Voltage", fmt_unit(pcs.get("ac_voltage_v"), "V", 0)),
                ("Std", grid_std),
            ],
        )}
    </div>
    """

    econn = f"""
    <div class="econn">
        <div class="econn-head">
            <h3>Electrical Connection Path</h3>
            <b>Cells → Packs → String/Rack → Rack Combiner → DC Bus → CC Panel → PCS</b>
        </div>

        <div class="econn-grid">
            <div class="e-card">
                <h4>String / Rack</h4>
                <div class="subline">{esc(fmt_num(state["packs_per_rack"],0))} packs connected in series per string</div>
                <div class="packline">{packboxes}</div>
            </div>

            <div class="econn-arrow">→</div>

            <div class="e-card">
                <h4>Rack Combiner</h4>
                <div class="subline">One combiner per rack string</div>
                <div class="fuse-symbol"><div class="fuse-circle"></div></div>
                <div class="kv-mini">
                    <span>Combiner fuse</span><b>{esc(fmt_unit(combiner_fuse_a, "A", 0))} / {esc(combiner_power_ka)}</b>
                    <span>Rack output</span><b>{esc(fmt_unit(bus_voltage_v, "V", 1))}</b>
                    <span>String current</span><b>{esc(fmt_unit(state["rack_current_a"], "A", 1))}</b>
                </div>
            </div>

            <div class="econn-arrow">→</div>

            <div class="e-card">
                <h4>DC Bus</h4>
                <div class="dc-bus-rect">{esc(fmt_unit(bus_voltage_v, "V", 1))}</div>
                <div class="kv-mini">
                    <span>Cable</span><b>{esc(cable_count)}</b>
                    <span>Total current</span><b>{esc(fmt_unit(state["dc_bus_current_a"], "A", 1))}</b>
                </div>
            </div>

            <div class="econn-arrow">→</div>

            <div class="e-card">
                <h4>CC Panel</h4>
                <div class="cc-panel-title">DC collection and protection panel</div>
                <div class="cc-panel-mid">CC Panel</div>
                <div class="kv-mini">
                    <span>Main fuse</span><b>{esc(fmt_unit(cc_main_fuse_a, "A", 0))} / 25 kA</b>
                    <span>Output cable</span><b>{esc(output_cable)}</b>
                </div>
            </div>

            <div class="econn-arrow">→</div>

            <div class="e-card">
                <h4>PCS</h4>
                <div class="subline">DC/AC conversion</div>
                <div class="e-pcs-img">{pcs_img}</div>
                <div class="kv-mini">
                    <span>Rating</span><b>{esc(fmt_unit(state["pcs_rating_kw"], "kVA", 0))}</b>
                    <span>AC voltage</span><b>{esc(fmt_unit(pcs.get("ac_voltage_v"), "V", 0))}</b>
                    <span>Utilisation</span><b>{esc(fmt_unit(state["pcs_utilisation_percent"], "%", 1))}</b>
                </div>
            </div>
        </div>

        <div class="e-stats">
            <div class="e-stat">
                <span>Parallel strings / racks in container</span>
                <b>{esc(fmt_num(state["racks_per_container"],0))} racks in parallel</b>
            </div>
            <div class="e-stat">
                <span>Container-to-PCS architecture</span>
                <b>{esc(fmt_num(containers,0))} {container_word} connected to 1 PCS</b>
            </div>
            <div class="e-stat">
                <span>System power at {esc(state["c_rate_label"])}</span>
                <b>{esc(fmt_unit(state["power_kw"], "kW", 0))}</b>
            </div>
            <div class="e-stat">
                <span>Discharge duration</span>
                <b>{esc(fmt_unit(state["duration_hr"], "h", 1))}</b>
            </div>
        </div>
    </div>
    """

    details = f"""
    <div class="detail-grid">
        <div class="detail-panel">
            <h3>String / Rack Detail</h3>
            <div class="detail-pack-row">
                <div class="detail-pack"><i></i></div>
                <div class="detail-pack"><i></i></div>
                <div class="detail-pack"><i></i></div>
                <div class="detail-pack"><i></i></div>
                <div class="series-copy">
                    {esc(fmt_num(state["packs_per_rack"],0))} packs in series<br>
                    {esc(fmt_unit(bus_voltage_v, "V", 1))}
                </div>
            </div>

            <div class="protect-row">
                <div class="protect-cell"><span>Fuse</span><b>{esc(fmt_unit(rack_fuse_a, "A", 0))}</b></div>
                <div class="protect-cell"><span>Contactor</span><b>HVCB</b></div>
                <div class="protect-cell"><span>IMD + Pre-charge</span><b>BCMU</b></div>
            </div>

            <div class="note-orange">
                HVCB = high-voltage control box. Each string isolates independently;
                rack fuse trips before pack fuse under reverse coordination.
            </div>
        </div>

        <div class="detail-panel">
            <h3>DC Bus & Container</h3>
            <div class="busbar"></div>

            <div class="bus-container-box">
                <div class="bus-container-img">{container_img}</div>
                <div class="bus-copy">
                    <b>{esc(fmt_num(state["racks_per_container"],0))} racks in parallel</b><br>
                    Bus V: <b>{esc(fmt_unit(bus_voltage_v, "V", 1))}</b> ·
                    Bus I: <b>{esc(fmt_unit(state["dc_bus_current_a"], "A", 1))}</b><br>
                    Energy: <b>{esc(fmt_unit(state["container_energy_mwh"], "MWh", 2))}</b>
                </div>
            </div>

            <div class="bus-tiles">
                <div class="bus-tile">
                    <span>Power @ C-rate</span>
                    <b>{esc(fmt_unit(state["power_kw"], "kW", 0))}</b>
                </div>
                <div class="bus-tile">
                    <span>Duration</span>
                    <b>{esc(fmt_unit(state["duration_hr"], "h", 1))}</b>
                </div>
            </div>
        </div>

        <div class="detail-panel">
            <h3>Protection Coordination</h3>

            <div class="coordination">
                <div class="coord-box">
                    <span>Pack Fuse</span>
                    <b>{esc(fmt_unit(pack_fuse_a, "A", 0))}</b>
                    <small>CLOU · ISO kA AIC</small>
                </div>
                <div class="coord-arrow">></div>
                <div class="coord-box">
                    <span>Rack (HVCB)</span>
                    <b>{esc(fmt_unit(rack_fuse_a, "A", 0))}</b>
                    <small>Trips first</small>
                </div>
                <div class="coord-arrow"><</div>
                <div class="coord-box">
                    <span>System</span>
                    <b>{esc(fmt_unit(system_fuse_a, "A", 0))}</b>
                    <small>IEC 240.4(C)</small>
                </div>
            </div>

            <div class="note-orange">
                Reverse coordination: rack fuse is below pack and system fuse,
                so a string fault drops one rack, not the whole container.
            </div>

            <div class="bmu-grid">
                <div class="bmu-tile"><span>BMU</span><b>{esc(fmt_num(bmu_per_string,0))} / string</b></div>
                <div class="bmu-tile"><span>BCMU</span><b>{esc(fmt_num(bcmu_per_string,0))} / string</b></div>
                <div class="bmu-tile"><span>BAMU</span><b>{esc(fmt_num(bamu_per_container,0))} / container</b></div>
            </div>
        </div>
    </div>
    """

    bottom = f"""
    <div class="sld-bottom">
        <div class="sld-sum"><span>System Energy</span><b>{esc(fmt_unit(state["container_energy_mwh"], "MWh", 2))}</b></div>
        <div class="sld-sum"><span>System Power</span><b>{esc(fmt_unit(state["power_kw"], "kW", 0))}</b></div>
        <div class="sld-sum"><span>Bus Voltage</span><b>{esc(fmt_unit(bus_voltage_v, "V", 1))}</b></div>
        <div class="sld-sum"><span>Bus Current</span><b>{esc(fmt_unit(state["dc_bus_current_a"], "A", 1))}</b></div>
        <div class="sld-sum"><span>Duration</span><b>{esc(fmt_unit(state["duration_hr"], "h", 1))}</b></div>
        <div class="sld-sum"><span>PCS Utilisation</span><b>{esc(fmt_unit(state["pcs_utilisation_percent"], "%", 1))}</b></div>
    </div>
    """

    st.markdown(
        f"""
        <div class="sld-screen">
            <div class="sld-head">
                <div>
                    <h2>Single Line Diagram</h2>
                    <div class="sld-sub">
                        {esc(battery.get("display_name"))} · {esc(state["c_rate_label"])} · {esc(pcs.get("display_name"))}
                    </div>
                </div>
                <div class="sld-meta">
                    System: <b>{esc(fmt_unit(state["container_energy_mwh"], "MWh", 2))}</b> ·
                    <b>{esc(fmt_unit(state["power_kw"], "kW", 0))}</b><br>
                    DC bus: <b>{esc(fmt_unit(bus_voltage_v, "V", 1))}</b> ·
                    <b>{esc(fmt_unit(state["dc_bus_current_a"], "A", 1))}</b>
                </div>
            </div>

            {sld_top}
            {econn}
            {details}
            {bottom}
        </div>
        """,
        unsafe_allow_html=True,
    )
'''


def main() -> None:
    if not APP_FILE.exists():
        raise FileNotFoundError("app.py not found. Run this script in the same folder as app.py.")

    text = APP_FILE.read_text(encoding="utf-8")

    if not BACKUP_FILE.exists():
        BACKUP_FILE.write_text(text, encoding="utf-8")
        print(f"Backup created: {BACKUP_FILE}")
    else:
        print(f"Backup already exists: {BACKUP_FILE}")

    # 1) Insert screenshot-style SLD CSS after the existing main CSS block.
    if "CSS — screenshot-style Single Line Diagram override" not in text:
        marker = "# ============================================================\n# Utility functions\n# ============================================================"
        if marker not in text:
            raise RuntimeError("Could not find Utility functions marker to insert SLD CSS.")
        text = text.replace(marker, NEW_SLD_CSS_BLOCK + "\n\n" + marker, 1)
        print("Inserted screenshot-style SLD CSS.")
    else:
        print("SLD CSS already present; skipping CSS insert.")

    # 2) Replace calculate_state.
    calc_pattern = (
        r"def calculate_state\(\n"
        r"    battery: Dict\[str, Any\],\n"
        r"    c_case: Dict\[str, Any\],\n"
        r"    pcs: Dict\[str, Any\],\n"
        r"\) -> Tuple\[Dict\[str, Any\], List\[str\]\]:"
        r"[\s\S]*?"
        r"\n\n\n# ============================================================\n# HTML card renderers"
    )

    text, calc_count = re.subn(
        calc_pattern,
        NEW_CALCULATE_STATE + "\n\n\n# ============================================================\n# HTML card renderers",
        text,
        count=1,
    )

    if calc_count != 1:
        raise RuntimeError("Could not replace calculate_state function.")
    print("Replaced calculate_state function.")

    # 3) Replace existing render_sld with new helper functions + screenshot-style render_sld.
    sld_pattern = (
        r"def render_sld\(state: Dict\[str, Any\]\) -> None:"
        r"[\s\S]*?"
        r"\n\n\n# ============================================================\n# Main app"
    )

    text, sld_count = re.subn(
        sld_pattern,
        NEW_RENDER_SLD_BLOCK + "\n\n\n# ============================================================\n# Main app",
        text,
        count=1,
    )

    if sld_count != 1:
        raise RuntimeError("Could not replace render_sld function.")
    print("Replaced render_sld function.")

    APP_FILE.write_text(text, encoding="utf-8")
    print("Updated app.py successfully.")

    # Syntax check.
    compile(text, str(APP_FILE), "exec")
    print("Syntax check passed.")


if __name__ == "__main__":
    main()