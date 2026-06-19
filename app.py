from __future__ import annotations

import base64
import html
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DATA_PATH = APP_DIR / "data" / "bess_dataset.json"
ASSET_DIR = APP_DIR / "assets"


st.set_page_config(
    page_title="BESS System Dashboard",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CSS — reference UI styling
# ============================================================

st.markdown(
    """
<style>
:root{
    --bg:#06101d;
    --panel:#0b1728;
    --line:#173b62;
    --txt:#f7fbff;
    --muted:#9bbad3;
    --cyan:#11cfe3;
    --green:#00c785;
    --amber:#f0b000;
    --violet:#756cff;
    --pink:#ff517c;
    --orange:#ffb165;
}

html, body, [data-testid="stAppViewContainer"]{
    background:
        radial-gradient(circle at 20% 0,rgba(9,93,127,.24),transparent 32%),
        linear-gradient(180deg,#07111f,#05101c);
    color:var(--txt);
}

[data-testid="stHeader"]{
    background:rgba(0,0,0,0);
}

.block-container{
    max-width:1240px;
    padding-top:18px;
    padding-bottom:24px;
}

h1,h2,h3,h4,p{
    margin:0;
}

.bess-title{
    text-align:center;
    font-size:28px;
    line-height:34px;
    color:white;
    font-weight:900;
    text-shadow:0 2px 12px #000;
}

.bess-subtitle{
    text-align:center;
    color:#a8dfff;
    font-size:13px;
    margin-top:3px;
    margin-bottom:12px;
}

.control-shell{
    border:1px solid #16456b;
    border-radius:9px;
    background:rgba(9,22,39,.92);
    padding:10px 16px 12px;
    box-shadow:0 12px 30px rgba(0,0,0,.25);
    margin-bottom:10px;
}

div[data-testid="stSelectbox"] label{
    color:#b6d8ee !important;
    font-size:12px !important;
    font-weight:700 !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div{
    background:#06101d !important;
    color:white !important;
    border:1px solid var(--cyan) !important;
    border-radius:7px !important;
    min-height:36px !important;
    box-shadow:0 0 10px rgba(17,207,227,.20);
}

div[data-testid="stSelectbox"] span{
    color:white !important;
    font-weight:900 !important;
    font-size:14px !important;
}

.stTabs [data-baseweb="tab-list"]{
    justify-content:center;
    gap:8px;
    margin-bottom:10px;
}

.stTabs [data-baseweb="tab"]{
    min-width:170px;
    height:39px;
    border:1px solid #1f3c5d;
    border-radius:8px;
    background:#0a1829;
    color:#dbeafe;
    font-weight:900;
}

.stTabs [aria-selected="true"]{
    background:linear-gradient(90deg,#13cfd5,#0fd0aa) !important;
    color:#031421 !important;
    border:0 !important;
}

.flow-grid{
    display:grid;
    grid-template-columns:1fr 22px 1fr 22px 1fr 22px 1.08fr 22px 1fr;
    gap:0;
    align-items:stretch;
}

.arrow{
    display:flex;
    align-items:center;
    justify-content:center;
    color:#38cfff;
    font-size:28px;
    font-weight:900;
    text-shadow:0 0 12px #38cfff;
}

.card{
    border-radius:8px;
    padding:10px 10px 9px;
    background:linear-gradient(180deg,rgba(14,30,51,.96),rgba(7,16,29,.98));
    box-shadow:0 12px 24px rgba(0,0,0,.35);
    overflow:hidden;
    min-height:512px;
}

.cell{border:1px solid #0bbe8a;background:linear-gradient(180deg,rgba(2,75,58,.88),rgba(3,34,35,.98));}
.pack{border:1px solid #b87900;background:linear-gradient(180deg,rgba(59,42,7,.9),rgba(9,22,29,.98));}
.rack{border:1px solid #625cff;background:linear-gradient(180deg,rgba(39,39,99,.9),rgba(8,18,34,.98));}
.container{border:1px solid #f0b000;background:linear-gradient(180deg,rgba(65,47,12,.9),rgba(8,20,24,.98));}
.pcs{border:1px solid #ff517c;background:linear-gradient(180deg,rgba(66,23,42,.9),rgba(10,16,31,.98));}

.card-head{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:8px;
}

.card-title{
    color:white;
    font-size:16px;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.2px;
}

.badge{
    font-size:10px;
    font-weight:900;
    padding:3px 8px;
    border-radius:999px;
    background:#1e708c;
    color:#bdf8ff;
}

.hero{
    height:100px;
    border:1px solid rgba(160,203,230,.15);
    border-radius:7px;
    background:rgba(7,16,29,.42);
    margin-bottom:8px;
    display:flex;
    align-items:center;
    justify-content:center;
    overflow:hidden;
}

.hero img{
    max-width:100%;
    max-height:92px;
    object-fit:contain;
    filter:drop-shadow(0 8px 10px rgba(0,0,0,.6));
}

.placeholder-icon{
    width:88px;
    height:64px;
    border-radius:8px;
    display:flex;
    align-items:center;
    justify-content:center;
    color:white;
    font-size:34px;
    background:linear-gradient(135deg,rgba(31,207,227,.24),rgba(255,255,255,.04));
    border:1px solid rgba(120,220,255,.22);
}

.section-title{
    color:#8ecfff;
    font-size:11px;
    font-weight:900;
    margin:5px 0 5px;
    text-transform:uppercase;
}

.table{
    border:1px solid rgba(160,203,230,.15);
    border-radius:7px;
    overflow:hidden;
    background:rgba(7,16,29,.45);
    margin-bottom:8px;
}

.row{
    display:grid;
    grid-template-columns:1fr auto;
    gap:8px;
    border-bottom:1px solid rgba(160,203,230,.12);
    padding:6px 8px;
    min-height:29px;
}

.row:last-child{
    border-bottom:0;
}

.row span{
    color:#a8d2e9;
    font-size:11px;
    line-height:15px;
}

.row b{
    color:white;
    font-size:13px;
    line-height:15px;
    text-align:right;
}

.energy-box{
    border:1px solid rgba(160,203,230,.17);
    border-radius:7px;
    background:rgba(7,16,29,.55);
    padding:9px;
    margin-top:7px;
}

.energy-box span{
    display:block;
    color:#a8bed1;
    font-size:10px;
    margin-bottom:4px;
}

.energy-box b{
    display:block;
    font-size:26px;
    line-height:28px;
    font-weight:900;
}

.green-text{color:#68ffaf;}
.orange-text{color:#ffb165;}
.yellow-text{color:#ffd84f;}
.cyan-text{color:#68e8ff;}
.pink-text{color:#ff7e9a;}
.violet-text{color:#b39cff;}

.metric-strip{
    display:grid;
    grid-template-columns:repeat(6,1fr);
    border:1px solid #173b62;
    border-radius:8px;
    background:rgba(9,22,39,.92);
    margin-top:12px;
    overflow:hidden;
}

.metric{
    padding:12px 14px;
    border-right:1px solid rgba(120,190,240,.18);
}

.metric:last-child{
    border-right:0;
}

.metric span{
    display:block;
    color:#9fdcff;
    font-size:11px;
    margin-bottom:7px;
}

.metric b{
    display:block;
    color:white;
    font-size:18px;
    font-weight:900;
    line-height:20px;
}

.metric small{
    color:#d9ecff;
    font-size:10px;
}

.architecture{
    border:1px solid #f2b600;
    border-radius:999px;
    background:linear-gradient(180deg,#322502,#101923);
    color:#ffdf60;
    padding:9px 20px;
    margin:12px auto 0;
    text-align:center;
    font-size:16px;
    font-weight:900;
    width:max-content;
    max-width:100%;
    box-shadow:0 0 14px rgba(242,182,0,.22);
}

.summary-grid{
    display:grid;
    grid-template-columns:1.15fr .85fr;
    gap:12px;
    margin-top:12px;
}

.summary-panel{
    border:1px solid #173b62;
    border-radius:8px;
    background:rgba(9,22,39,.92);
    padding:13px 16px;
}

.summary-panel h3{
    color:#8ecfff;
    font-size:14px;
    text-transform:uppercase;
    margin-bottom:10px;
}

.summary-cells{
    display:grid;
    grid-template-columns:repeat(5,1fr);
    gap:18px;
}

.summary-item span{
    display:block;
    color:#9fdcff;
    font-size:11px;
    margin-bottom:6px;
}

.summary-item b{
    color:white;
    font-size:18px;
    font-weight:900;
}

.config-row{
    display:grid;
    grid-template-columns:1fr 18px 1.5fr;
    gap:8px;
    border-bottom:1px solid rgba(160,203,230,.12);
    padding:6px 0;
}

.config-row:last-child{
    border-bottom:0;
}

.config-row span{
    color:#d9ecff;
    font-size:12px;
}

.config-row b{
    color:white;
    font-size:12px;
}

.sld-frame{
    border:1px solid #16cbe7;
    border-radius:10px;
    background:radial-gradient(circle at 45% 0,rgba(13,209,232,.15),transparent 36%),linear-gradient(180deg,#071a2d 0%,#03101d 100%);
    box-shadow:0 18px 42px rgba(0,0,0,.45), inset 0 0 0 1px rgba(20,220,255,.08);
    padding:16px;
    color:white;
}

.sld-head{
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    border-bottom:1px solid rgba(130,210,255,.22);
    padding-bottom:10px;
    margin-bottom:12px;
}

.sld-head h2{
    font-size:24px;
    font-weight:900;
    color:white;
}

.sld-meta{
    color:#a9eaff;
    font-size:12px;
    text-align:right;
    line-height:18px;
}

.sld-chain{
    display:grid;
    grid-template-columns:1fr 30px 1fr 30px 1fr 30px 1.1fr 30px 1fr 30px .9fr;
    gap:0;
    align-items:stretch;
    margin-bottom:14px;
}

.sld-node{
    border-radius:9px;
    background:linear-gradient(180deg,rgba(12,31,50,.96),rgba(4,13,24,.96));
    border:1px solid #22d9ff;
    padding:12px;
    min-height:160px;
    box-shadow:inset 0 0 18px rgba(0,217,255,.08),0 10px 22px rgba(0,0,0,.25);
}

.sld-node h3{
    color:white;
    font-size:15px;
    font-weight:900;
    text-transform:uppercase;
    margin-bottom:8px;
}

.sld-arrow{
    display:flex;
    align-items:center;
    justify-content:center;
    color:#25dfff;
    font-size:25px;
    font-weight:900;
    text-shadow:0 0 10px #25dfff;
}

.sld-kv{
    display:grid;
    grid-template-columns:1fr auto;
    gap:4px 8px;
}

.sld-kv span{
    color:#aee6ff;
    font-size:11px;
}

.sld-kv b{
    color:white;
    font-size:12px;
    text-align:right;
}

.electrical-grid{
    display:grid;
    grid-template-columns:repeat(6,1fr);
    gap:10px;
    margin-top:12px;
}

.electrical-box{
    border:1px dashed rgba(30,215,255,.58);
    border-radius:9px;
    background:linear-gradient(180deg,rgba(8,23,39,.86),rgba(4,12,22,.9));
    padding:11px;
    min-height:135px;
}

.electrical-box h4{
    color:#9edfff;
    font-size:13px;
    font-weight:900;
    text-transform:uppercase;
    text-align:center;
    margin-bottom:7px;
}

.electrical-box p{
    color:#d7efff;
    font-size:11px;
    line-height:15px;
    margin:4px 0;
}

.warn{
    border-left:4px solid #ffbc62;
    background:rgba(255,188,98,.10);
    border-radius:8px;
    padding:10px 12px;
    color:#ffe2b5;
    font-size:12px;
    margin-bottom:10px;
}

@media(max-width:1100px){
    .flow-grid,
    .sld-chain,
    .electrical-grid,
    .metric-strip,
    .summary-grid,
    .summary-cells{
        grid-template-columns:1fr;
    }
    .arrow,
    .sld-arrow{
        display:none;
    }
    .card{
        min-height:auto;
        margin-bottom:10px;
    }
}
</style>
""",
    unsafe_allow_html=True,
)



# ============================================================
# CSS — polished dashboard and single-line diagram overrides
# ============================================================

st.markdown(
    """
<style>
/* ---------- Global polish ---------- */
:root{
    --navy-950:#030b14;
    --navy-900:#05101d;
    --navy-850:#071827;
    --navy-800:#091b2d;
    --stroke:#1a4770;
    --stroke-soft:rgba(111,185,232,.22);
    --text:#f7fbff;
    --muted:#a6cbe4;
    --muted-2:#77a7c6;
    --cyan:#16d9ec;
    --cyan-2:#38f3ff;
    --green:#26e996;
    --amber:#ffc52e;
    --orange:#ffb463;
    --violet:#8882ff;
    --pink:#ff5b88;
}

#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"]{
    visibility:hidden;
    height:0;
}

.block-container{
    max-width:1180px;
    padding-top:8px;
    padding-left:18px;
    padding-right:18px;
    padding-bottom:18px;
}

.bess-title{
    font-size:24px;
    line-height:28px;
    letter-spacing:.2px;
    margin-top:-4px;
}

.bess-subtitle{
    font-size:11px;
    line-height:15px;
    margin-top:1px;
    margin-bottom:8px;
    color:#b9e8ff;
}

/* Streamlit column row containing selectboxes becomes the control shell. */
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]){
    border:1px solid #1c527d;
    border-radius:8px;
    background:linear-gradient(180deg,rgba(9,28,46,.96),rgba(5,17,30,.96));
    padding:7px 14px 8px;
    box-shadow:0 12px 30px rgba(0,0,0,.23), inset 0 0 0 1px rgba(20,220,255,.04);
    margin-bottom:8px;
}

div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]) > div{
    padding-left:5px;
    padding-right:5px;
}

div[data-testid="stSelectbox"] label{
    color:#a9d9f2 !important;
    font-size:10px !important;
    font-weight:800 !important;
    letter-spacing:.15px;
    margin-bottom:2px;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div{
    min-height:34px !important;
    border-radius:6px !important;
    border:1px solid #23618e !important;
    background:#06111f !important;
    box-shadow:inset 0 0 0 1px rgba(22,217,236,.03) !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within{
    border-color:var(--cyan) !important;
    box-shadow:0 0 0 1px rgba(22,217,236,.55),0 0 16px rgba(22,217,236,.16) !important;
}

div[data-testid="stSelectbox"] span{
    font-size:12px !important;
    font-weight:900 !important;
}

.stTabs [data-baseweb="tab-list"]{
    gap:8px;
    justify-content:center;
    margin-top:0;
    margin-bottom:10px;
}

.stTabs [data-baseweb="tab"]{
    height:36px;
    min-width:166px;
    padding-left:22px;
    padding-right:22px;
    border-radius:8px;
    background:linear-gradient(180deg,#0c1b2e,#071321);
    border:1px solid #244a70;
    color:#e6f6ff;
    font-size:12px;
    font-weight:900;
    letter-spacing:.05px;
}

.stTabs [aria-selected="true"]{
    background:linear-gradient(90deg,#19d4d7,#13d7ae) !important;
    color:#021521 !important;
    border-color:transparent !important;
    box-shadow:0 9px 22px rgba(16,215,190,.18);
}

/* ---------- Dashboard card polish ---------- */
.flow-grid{
    grid-template-columns:minmax(0,1fr) 22px minmax(0,1fr) 22px minmax(0,1fr) 22px minmax(0,1.05fr) 22px minmax(0,1fr);
}

.card{
    min-height:500px;
    padding:10px;
    border-radius:8px;
}

.card-title{
    font-size:15px;
    letter-spacing:.1px;
}

.badge{
    font-size:9px;
    padding:3px 7px;
    white-space:nowrap;
}

.hero{
    height:96px;
    margin-bottom:7px;
}

.row{
    padding:5px 8px;
    min-height:27px;
}

.row span{
    font-size:10.5px;
}

.row b{
    font-size:12px;
}

.section-title{
    font-size:10.5px;
    letter-spacing:.35px;
}

.energy-box b{
    font-size:24px;
    line-height:26px;
}

.metric-strip{
    margin-top:10px;
}

.metric{
    padding:10px 13px;
}

.metric span{
    font-size:10px;
    margin-bottom:6px;
}

.metric b{
    font-size:17px;
}

.metric small{
    font-size:10px;
    line-height:13px;
    display:block;
}

.warn{
    border:1px solid rgba(255,188,98,.28);
    border-left:4px solid #ffbc62;
    background:rgba(255,188,98,.08);
}

/* ---------- CSS equipment artwork fallback ---------- */
.equip-art{
    position:relative;
    width:100%;
    height:100%;
    min-height:56px;
    display:flex;
    align-items:center;
    justify-content:center;
    overflow:hidden;
    color:white;
    isolation:isolate;
}

.equip-art:before{
    content:"";
    position:absolute;
    inset:8px 16px;
    border-radius:14px;
    background:radial-gradient(circle at 40% 15%,rgba(255,255,255,.18),transparent 32%);
    opacity:.55;
    z-index:-1;
}

.art-label{
    position:absolute;
    right:8px;
    bottom:6px;
    color:rgba(255,255,255,.72);
    font-size:9px;
    font-weight:900;
    letter-spacing:.5px;
}

.art-cell .cell-can{
    position:relative;
    width:78px;
    height:54px;
    transform:skewY(8deg) rotate(-3deg);
    background:linear-gradient(135deg,#0f63ce 0%,#0f4aa0 58%,#083275 100%);
    border:1px solid rgba(180,220,255,.56);
    box-shadow:0 12px 20px rgba(0,0,0,.45), inset 0 0 18px rgba(255,255,255,.08);
}

.art-cell .cell-can:before{
    content:"";
    position:absolute;
    left:7px;
    top:-8px;
    width:62px;
    height:12px;
    background:linear-gradient(90deg,#d8dfe8,#778293);
    border:1px solid rgba(255,255,255,.5);
    border-radius:50%;
}

.art-cell .cell-can:after{
    content:"";
    position:absolute;
    right:10px;
    top:22px;
    width:18px;
    height:20px;
    border:1px solid rgba(255,255,255,.48);
    border-radius:2px;
}

.art-pack .pack-body{
    position:relative;
    width:118px;
    height:58px;
    transform:perspective(160px) rotateX(8deg) rotateY(-14deg);
    background:linear-gradient(135deg,#1b222b,#090d13 70%);
    border:1px solid rgba(220,240,255,.25);
    box-shadow:0 14px 18px rgba(0,0,0,.5);
}

.art-pack .pack-body:before{
    content:"";
    position:absolute;
    inset:8px 8px auto 8px;
    height:14px;
    background:repeating-linear-gradient(90deg,#222d38 0 13px,#121820 13px 17px);
    border:1px solid rgba(255,255,255,.1);
}

.art-pack .pack-body:after{
    content:"";
    position:absolute;
    inset:auto 10px 8px 10px;
    height:22px;
    background:repeating-linear-gradient(90deg,#090c10 0 18px,#212a33 18px 21px);
    border-top:2px solid rgba(255,150,50,.6);
}

.art-rack .rack-body{
    position:relative;
    width:80px;
    height:74px;
    background:linear-gradient(180deg,#262d33,#0b0e13);
    border:2px solid rgba(180,220,255,.25);
    box-shadow:0 14px 18px rgba(0,0,0,.55), inset 0 0 16px rgba(255,255,255,.04);
}

.art-rack .rack-body:before{
    content:"";
    position:absolute;
    inset:8px;
    background:repeating-linear-gradient(180deg,#12171e 0 9px,#c66b29 9px 11px,#10141b 11px 18px);
    border:1px solid rgba(255,255,255,.12);
}

.art-rack .rack-body:after{
    content:"";
    position:absolute;
    left:50%;
    top:8px;
    bottom:8px;
    width:1px;
    background:rgba(255,255,255,.16);
}

.art-container .container-body{
    position:relative;
    width:132px;
    height:62px;
    background:linear-gradient(90deg,#e8ecef,#bfc6cc 55%,#9fa8b0);
    border:2px solid rgba(255,255,255,.8);
    box-shadow:0 14px 20px rgba(0,0,0,.48);
}

.art-container .container-body:before{
    content:"";
    position:absolute;
    inset:8px;
    background:repeating-linear-gradient(90deg,rgba(80,90,100,.42) 0 2px,transparent 2px 18px);
}

.art-container .container-body:after{
    content:"BESS";
    position:absolute;
    right:12px;
    top:12px;
    color:#d21730;
    font-size:9px;
    font-weight:900;
}

.art-pcs .pcs-body{
    position:relative;
    width:104px;
    height:66px;
    transform:perspective(160px) rotateY(-10deg);
    background:linear-gradient(135deg,#f4f5f5,#b7b9bd 60%,#767b82);
    border:1px solid rgba(255,255,255,.8);
    box-shadow:0 13px 18px rgba(0,0,0,.5);
}

.art-pcs .pcs-body:before{
    content:"";
    position:absolute;
    left:12px;
    top:12px;
    width:36px;
    height:38px;
    border:1px solid rgba(30,40,50,.35);
    background:repeating-linear-gradient(180deg,rgba(60,70,80,.4) 0 2px,transparent 2px 7px);
}

.art-pcs .pcs-body:after{
    content:"";
    position:absolute;
    right:12px;
    top:14px;
    width:36px;
    height:36px;
    border-radius:50%;
    border:5px solid rgba(70,80,90,.48);
    box-shadow:inset 0 0 0 2px rgba(255,255,255,.55);
}

.art-grid .tower{
    position:relative;
    width:70px;
    height:76px;
}

.art-grid .tower:before{
    content:"";
    position:absolute;
    left:50%;
    top:0;
    width:2px;
    height:76px;
    background:#23def2;
    transform:translateX(-50%);
    box-shadow:0 0 10px rgba(35,222,242,.4);
}

.art-grid .tower:after{
    content:"";
    position:absolute;
    left:14px;
    top:8px;
    width:42px;
    height:60px;
    border-left:2px solid #23def2;
    border-right:2px solid #23def2;
    border-bottom:2px solid #23def2;
    transform:perspective(80px) rotateX(0deg) skewX(-16deg);
}

/* ---------- Enhanced single-line diagram ---------- */
.singleline-frame{
    border:1px solid var(--cyan);
    border-radius:8px;
    background:
        radial-gradient(circle at 50% -12%,rgba(18,215,236,.18),transparent 35%),
        linear-gradient(180deg,#081c2e 0%,#04111f 100%);
    box-shadow:0 18px 42px rgba(0,0,0,.44), inset 0 0 0 1px rgba(20,220,255,.08);
    padding:14px;
    color:white;
}

.sle-head{
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    border-bottom:1px solid rgba(130,210,255,.25);
    padding-bottom:9px;
    margin-bottom:11px;
}

.sle-head h2{
    font-size:22px;
    line-height:26px;
    font-weight:950;
    color:#fff;
}

.sle-sub{
    color:#b7eaff;
    font-size:11px;
    margin-top:2px;
    font-weight:650;
}

.sle-meta{
    color:#b7eaff;
    font-size:10px;
    line-height:15px;
    text-align:right;
    font-weight:800;
}

.sle-chain{
    display:grid;
    grid-template-columns:minmax(0,1fr) 26px minmax(0,1fr) 26px minmax(0,1fr) 26px minmax(0,1.1fr) 26px minmax(0,1fr) 26px minmax(0,.9fr);
    gap:0;
    align-items:stretch;
    margin-bottom:12px;
}

.sle-node{
    border-radius:7px;
    padding:9px;
    background:linear-gradient(180deg,rgba(10,28,48,.95),rgba(4,13,24,.98));
    border:1px solid #1ecdf0;
    min-height:138px;
    box-shadow:inset 0 0 18px rgba(0,217,255,.07),0 10px 20px rgba(0,0,0,.25);
}

.sle-node.cell{border-color:#10ddaa;}
.sle-node.pack{border-color:#ffc027;}
.sle-node.rack{border-color:#827cff;}
.sle-node.container{border-color:#ffe000;}
.sle-node.pcs{border-color:#ff5b88;}
.sle-node.grid{border-color:#21ddef;}

.sle-node h3{
    font-size:13px;
    line-height:16px;
    margin-bottom:5px;
    text-transform:uppercase;
    font-weight:950;
    color:#fff;
}

.sle-art{
    height:54px;
    border-radius:5px;
    border:1px solid rgba(160,203,230,.14);
    background:rgba(5,13,23,.38);
    display:flex;
    align-items:center;
    justify-content:center;
    overflow:hidden;
    margin-bottom:6px;
}

.sle-art img,
.path-art img{
    max-height:100%;
    max-width:100%;
    object-fit:contain;
    filter:drop-shadow(0 8px 10px rgba(0,0,0,.55));
}

.sle-kv{
    display:grid;
    grid-template-columns:1fr auto;
    gap:2px 7px;
}

.sle-kv span{
    color:#aee6ff;
    font-size:9.5px;
    line-height:12px;
}

.sle-kv b{
    color:#fff;
    font-size:10px;
    line-height:12px;
    text-align:right;
    white-space:nowrap;
}

.sle-arrow{
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    color:#27dfff;
    text-shadow:0 0 10px #27dfff;
    font-weight:950;
}

.sle-arrow span{
    font-size:21px;
    line-height:22px;
}

.sle-arrow small{
    margin-top:2px;
    color:#9ceeff;
    font-size:7.5px;
    line-height:9px;
    text-align:center;
    text-shadow:none;
    font-weight:900;
}

.sle-section-title{
    display:flex;
    justify-content:space-between;
    gap:12px;
    align-items:center;
    color:#8edbff;
    font-size:12px;
    font-weight:950;
    text-transform:uppercase;
    margin:8px 0 7px;
}

.sle-section-title small{
    color:#d4f4ff;
    font-size:9px;
    text-transform:none;
    text-align:right;
}

.path-grid{
    display:grid;
    grid-template-columns:minmax(0,2.05fr) 26px minmax(0,1.28fr) 26px minmax(0,.82fr) 26px minmax(0,1.28fr) 26px minmax(0,1fr);
    gap:0;
    align-items:stretch;
}

.path-box{
    border:1px solid #1bcff0;
    border-radius:7px;
    background:linear-gradient(180deg,rgba(7,24,41,.9),rgba(3,12,23,.95));
    padding:10px;
    min-height:134px;
    box-shadow:inset 0 0 16px rgba(20,220,255,.06);
}

.path-box h4{
    color:#a8e8ff;
    font-size:11px;
    line-height:14px;
    font-weight:950;
    text-transform:uppercase;
    margin-bottom:6px;
}

.path-box p{
    color:#d6efff;
    font-size:9.5px;
    line-height:13px;
    margin:3px 0;
}

.path-arrow{
    display:flex;
    align-items:center;
    justify-content:center;
    color:#ff6f6f;
    font-size:15px;
    font-weight:950;
    text-shadow:0 0 8px rgba(255,95,95,.45);
}

.series-packs{
    display:grid;
    grid-template-columns:repeat(4,minmax(0,1fr));
    gap:6px;
    margin-top:5px;
}

.series-pack{
    border:1px solid #12e1f4;
    border-radius:5px;
    background:#071525;
    padding:5px 4px;
    text-align:center;
}

.series-pack .pack-top{
    height:22px;
    border:1px solid #f0a000;
    border-radius:4px;
    margin-bottom:4px;
    background:repeating-linear-gradient(90deg,#11c683 0 6px,#103e35 6px 10px);
}

.series-pack b{
    display:block;
    color:white;
    font-size:9px;
    line-height:11px;
}

.series-pack span{
    display:block;
    color:#bdefff;
    font-size:8px;
    line-height:10px;
}

.series-pack em{
    display:block;
    margin-top:3px;
    color:#ffd8bf;
    font-size:7.5px;
    line-height:9px;
    font-style:normal;
    border:1px solid #ff4d4d;
    border-radius:3px;
    padding:1px;
}

.bus-pill{
    border-radius:6px;
    background:linear-gradient(180deg,#235dce,#123176);
    color:#fff;
    text-align:center;
    font-weight:950;
    font-size:12px;
    padding:14px 5px;
    margin:8px 2px 7px;
    box-shadow:inset 0 0 12px rgba(255,255,255,.12);
}

.cc-line{
    height:1px;
    background:rgba(200,240,255,.26);
    margin:10px 0;
}

.path-art{
    height:50px;
    border-radius:5px;
    border:1px solid rgba(255,255,255,.12);
    background:rgba(255,255,255,.06);
    display:flex;
    align-items:center;
    justify-content:center;
    overflow:hidden;
    margin:5px 0 6px;
}

.detail-grid{
    display:grid;
    grid-template-columns:1.35fr 1.08fr 1.18fr;
    gap:12px;
    margin-top:12px;
}

.detail-panel{
    border:1px solid #1f527d;
    border-radius:7px;
    background:rgba(7,22,38,.82);
    padding:10px;
    min-height:160px;
}

.detail-panel h4{
    color:#8edbff;
    font-size:12px;
    line-height:14px;
    text-transform:uppercase;
    font-weight:950;
    margin-bottom:8px;
}

.micro-packs{
    display:flex;
    align-items:center;
    gap:6px;
    margin-bottom:8px;
}

.micro-pack{
    width:48px;
    height:26px;
    border:2px solid #f6b800;
    border-radius:4px;
    background:repeating-linear-gradient(90deg,#0fc583 0 7px,#0c4538 7px 11px);
    box-shadow:inset 0 0 10px rgba(0,0,0,.2);
}

.micro-caption{
    color:#ffd958;
    font-size:9px;
    font-weight:900;
    line-height:11px;
}

.protection-row{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:7px;
}

.protection-chip{
    border:1px dashed #827cff;
    border-radius:6px;
    background:rgba(130,124,255,.08);
    text-align:center;
    padding:8px 6px;
}

.protection-chip span{
    color:#e4e2ff;
    display:block;
    font-size:8.5px;
    line-height:11px;
}

.protection-chip b{
    color:#fff;
    display:block;
    font-size:11px;
    margin-top:3px;
}

.note-band{
    border-left:3px solid #ffb463;
    border-radius:6px;
    background:rgba(255,180,99,.09);
    color:#ffddb5;
    font-size:9px;
    line-height:13px;
    padding:7px 8px;
    margin-top:7px;
}

.dc-bus-visual{
    border:1px solid #f6d000;
    border-radius:7px;
    padding:8px;
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:8px;
    align-items:center;
    background:linear-gradient(180deg,rgba(75,53,5,.42),rgba(6,15,24,.55));
}

.energy-bar{
    height:14px;
    border-radius:999px;
    background:linear-gradient(90deg,#21d2ff,#24f09f);
    box-shadow:0 0 12px rgba(33,210,255,.28);
    margin-bottom:8px;
}

.detail-metrics{
    display:grid;
    grid-template-columns:repeat(2,1fr);
    gap:7px;
    margin-top:8px;
}

.detail-metric{
    border:1px solid rgba(160,203,230,.18);
    border-radius:6px;
    background:rgba(5,15,27,.65);
    padding:8px;
}

.detail-metric span{
    display:block;
    color:#9edfff;
    font-size:8.5px;
    margin-bottom:4px;
}

.detail-metric b{
    color:#fff;
    font-size:14px;
    font-weight:950;
}

.fuse-flow{
    display:grid;
    grid-template-columns:1fr 18px 1fr 18px 1fr;
    align-items:center;
    gap:4px;
}

.fuse-card{
    border:1px solid #ffc052;
    border-radius:6px;
    background:rgba(255,192,82,.1);
    padding:8px 6px;
    text-align:center;
}

.fuse-card span{
    display:block;
    color:#ffdfaa;
    font-size:8px;
    line-height:10px;
}

.fuse-card b{
    display:block;
    color:#ffe36c;
    font-size:16px;
    line-height:18px;
    font-weight:950;
    margin:2px 0;
}

.fuse-arrow{
    color:#ff9538;
    text-align:center;
    font-size:16px;
    font-weight:950;
}

.bms-row{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:7px;
    margin-top:8px;
}

.bms-card{
    border:1px solid #244e75;
    border-radius:5px;
    background:rgba(8,19,34,.8);
    text-align:center;
    padding:7px 4px;
}

.bms-card span{
    display:block;
    color:#9fc8df;
    font-size:8px;
}

.bms-card b{
    display:block;
    color:#fff;
    font-size:10px;
    margin-top:3px;
}

.sle-footer{
    display:grid;
    grid-template-columns:repeat(6,1fr);
    border:1px solid #1f527d;
    border-radius:7px;
    background:rgba(5,16,29,.72);
    overflow:hidden;
    margin-top:10px;
}

.sle-foot-item{
    padding:10px 12px;
    border-right:1px solid rgba(120,190,240,.18);
}

.sle-foot-item:last-child{border-right:0;}

.sle-foot-item span{
    display:block;
    color:#9edfff;
    font-size:9px;
    margin-bottom:5px;
}

.sle-foot-item b{
    display:block;
    color:#fff;
    font-size:14px;
    line-height:16px;
    font-weight:950;
}

@media(max-width:1100px){
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stSelectbox"]){
        padding:10px;
    }
    .sle-chain,
    .path-grid,
    .detail-grid,
    .sle-footer,
    .series-packs{
        grid-template-columns:1fr;
    }
    .sle-arrow,
    .path-arrow{
        display:none;
    }
    .sle-node,
    .path-box,
    .detail-panel{
        min-height:auto;
        margin-bottom:8px;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# Utility functions
# ============================================================

def esc(value: Any) -> str:
    if value is None:
        return "N/A"
    return html.escape(str(value))


def to_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return None
        return number

    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned.lower() in {"", "na", "n/a", "none", "null", "-"}:
            return None

        match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
        if not match:
            return None

        try:
            return float(match.group(0))
        except ValueError:
            return None

    return None


def prefer(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def prefer_float(*values: Any) -> Optional[float]:
    for value in values:
        number = to_float(value)
        if number is not None:
            return number
    return None


def fmt_num(value: Any, decimals: int = 1, na: str = "N/A") -> str:
    number = to_float(value)
    if number is None:
        return na

    text = f"{number:,.{decimals}f}"

    if "." in text:
        text = text.rstrip("0").rstrip(".")

    return text


def fmt_unit(value: Any, unit: str, decimals: int = 1) -> str:
    number = to_float(value)
    if number is None:
        return "N/A"
    return f"{fmt_num(number, decimals)} {unit}"


def fmt_range(min_value: Any, max_value: Any, unit: str, decimals: int = 0) -> str:
    min_number = to_float(min_value)
    max_number = to_float(max_value)

    if min_number is None and max_number is None:
        return "N/A"
    if min_number is None:
        return f"≤ {fmt_unit(max_number, unit, decimals)}"
    if max_number is None:
        return f"≥ {fmt_unit(min_number, unit, decimals)}"

    return f"{fmt_num(min_number, decimals)}–{fmt_num(max_number, decimals)} {unit}"


def get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = data

    for key in path.split("."):
        if not isinstance(current, dict):
            return default

        current = current.get(key)

        if current is None:
            return default

    return current


def parse_c_rate(value: Any) -> Optional[float]:
    if value is None:
        return None

    match = re.search(r"(\d+(?:\.\d+)?)", str(value))
    if not match:
        return None

    return float(match.group(1))


def plural(value: Any, singular: str, plural_word: Optional[str] = None) -> str:
    number = to_float(value)
    if number == 1:
        return singular
    return plural_word or f"{singular}s"


def get_image_src(record: Dict[str, Any], image_key: str) -> Optional[str]:
    """
    Optional JSON support:
    "images": {
        "cell": "assets/cell.png",
        "pack": "assets/pack.png"
    }

    Also supports direct base64/data URLs.
    """

    images = record.get("images")

    if not isinstance(images, dict):
        return None

    raw = images.get(image_key)

    if not raw:
        return None

    raw_text = str(raw)

    if raw_text.startswith("data:image"):
        return raw_text

    path = APP_DIR / raw_text

    if not path.exists():
        path = ASSET_DIR / raw_text

    if not path.exists():
        return None

    suffix = path.suffix.lower().replace(".", "")
    mime = "png" if suffix not in {"jpg", "jpeg", "webp", "png"} else suffix
    if mime == "jpg":
        mime = "jpeg"

    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/{mime};base64,{encoded}"


def equipment_art_html(key: str, fallback_label: str = "") -> str:
    label = fallback_label or key.upper()

    if key == "cell":
        return (
            f'<div class="equip-art art-cell">'
            f'<div class="cell-can"><span class="art-label">{esc(label)}</span></div>'
            f'</div>'
        )

    if key == "pack":
        return (
            f'<div class="equip-art art-pack">'
            f'<div class="pack-body"><span class="art-label">{esc(label)}</span></div>'
            f'</div>'
        )

    if key == "rack":
        return (
            f'<div class="equip-art art-rack">'
            f'<div class="rack-body"><span class="art-label">{esc(label)}</span></div>'
            f'</div>'
        )

    if key == "container":
        return (
            f'<div class="equip-art art-container">'
            f'<div class="container-body"><span class="art-label">{esc(label)}</span></div>'
            f'</div>'
        )

    if key == "pcs":
        return (
            f'<div class="equip-art art-pcs">'
            f'<div class="pcs-body"><span class="art-label">{esc(label)}</span></div>'
            f'</div>'
        )

    if key == "grid":
        return (
            f'<div class="equip-art art-grid">'
            f'<div class="tower"><span class="art-label">{esc(label)}</span></div>'
            f'</div>'
        )

    return f'<div class="placeholder-icon">{esc(fallback_label or "▣")}</div>'


def art_html(record: Dict[str, Any], key: str, fallback_label: str = "") -> str:
    src = get_image_src(record, key)

    if src:
        return f'<img src="{esc(src)}" alt="{esc(key)} image"/>'

    return equipment_art_html(key, fallback_label)


def hero_html(record: Dict[str, Any], key: str, emoji: str) -> str:
    # The emoji argument is retained for backward compatibility with calls in
    # the renderers; polished CSS artwork is used when no asset is supplied.
    fallback = {
        "cell": "CELL",
        "pack": "PACK",
        "rack": "RACK",
        "container": "BESS",
        "pcs": "PCS",
        "grid": "GRID",
    }.get(key, emoji)
    return art_html(record, key, fallback)

def row_html(label: str, value: Any) -> str:
    return f"""
    <div class="row">
        <span>{esc(label)}</span>
        <b>{esc(value)}</b>
    </div>
    """


def table_html(rows: List[Tuple[str, Any]]) -> str:
    return '<div class="table">' + "".join(row_html(label, value) for label, value in rows) + "</div>"


# ============================================================
# Data loading and validation
# ============================================================

@st.cache_data(show_spinner=False)
def load_dataset() -> Dict[str, Any]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {DATA_PATH}. "
            "Place your JSON at data/bess_dataset.json."
        )

    with DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def active_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [row for row in records if row.get("active", True) is not False]


def find_by_id(records: List[Dict[str, Any]], row_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if row_id is None:
        return None

    for row in records:
        if str(row.get("id")) == str(row_id):
            return row

    return None


def validate_dataset(data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    required_sections = ["battery_containers", "c_rate_cases", "pcs_models"]

    for section in required_sections:
        if section not in data:
            errors.append(f"Missing top-level JSON section: {section}")
        elif not isinstance(data[section], list):
            errors.append(f"Top-level JSON section must be a list: {section}")

    if errors:
        return errors, warnings

    battery_ids = set()

    for index, battery in enumerate(data["battery_containers"], start=1):
        battery_id = battery.get("id")
        if not battery_id:
            errors.append(f"battery_containers row {index} is missing id.")
        elif battery_id in battery_ids:
            errors.append(f"Duplicate battery id: {battery_id}")
        else:
            battery_ids.add(battery_id)

        if not battery.get("display_name"):
            warnings.append(f"Battery row {battery_id or index} is missing display_name.")

        if to_float(get_nested(battery, "container.racks_per_container")) is None:
            warnings.append(f"Battery row {battery_id or index} is missing container.racks_per_container.")

        if to_float(get_nested(battery, "cell.nominal_voltage_v")) is None:
            warnings.append(f"Battery row {battery_id or index} is missing cell.nominal_voltage_v.")

        if to_float(get_nested(battery, "cell.nominal_capacity_ah")) is None:
            warnings.append(f"Battery row {battery_id or index} is missing cell.nominal_capacity_ah.")

    pcs_ids = set()

    for index, pcs in enumerate(data["pcs_models"], start=1):
        pcs_id = pcs.get("id")
        if not pcs_id:
            errors.append(f"pcs_models row {index} is missing id.")
        elif pcs_id in pcs_ids:
            errors.append(f"Duplicate PCS id: {pcs_id}")
        else:
            pcs_ids.add(pcs_id)

        if not pcs.get("display_name"):
            warnings.append(f"PCS row {pcs_id or index} is missing display_name.")

    for index, case in enumerate(data["c_rate_cases"], start=1):
        case_id = case.get("id", f"row {index}")
        battery_id = case.get("battery_container_id")

        if not battery_id:
            errors.append(f"C-rate case {case_id} is missing battery_container_id.")
        elif battery_id not in battery_ids:
            errors.append(
                f"C-rate case {case_id} references unknown battery_container_id: {battery_id}"
            )

        if not case.get("c_rate"):
            errors.append(f"C-rate case {case_id} is missing c_rate.")

    return errors, warnings


# ============================================================
# Calculation engine
# ============================================================

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

    dc_bus_current_a = prefer_float(
        c_case.get("dc_bus_current_a"),
        container.get("dc_bus_current_a"),
        None if power_kw is None or nominal_dc_bus_v in (None, 0) else power_kw * 1000 / nominal_dc_bus_v,
    )

    if c_case.get("dc_bus_current_a") is None:
        warnings.append(
            "DC Bus Current is missing in the selected C-rate row; app used container value or fallback calculation."
        )

    rack_current_a = prefer_float(
        rack.get("rack_current_a"),
        None if dc_bus_current_a is None or racks_per_container in (None, 0) else dc_bus_current_a / racks_per_container,
    )

    rack_power_kw = None
    if power_kw is not None and racks_per_container not in (None, 0):
        rack_power_kw = power_kw / racks_per_container

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

    pcs_utilisation_percent = prefer_float(
        c_case.get("pcs_utilisation_percent"),
        None if power_into_pcs_kw is None or pcs_rating_kw in (None, 0) else power_into_pcs_kw / pcs_rating_kw * 100,
    )

    max_racks_per_pcs = prefer_float(pcs.get("max_racks_per_pcs"))

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
        "dc_bus_current_a": dc_bus_current_a,

        "pcs_rating_kw": pcs_rating_kw,
        "containers_per_pcs": containers_per_pcs,
        "racks_per_pcs": racks_per_pcs,
        "power_into_pcs_kw": power_into_pcs_kw,
        "pcs_utilisation_percent": pcs_utilisation_percent,
        "max_racks_per_pcs": max_racks_per_pcs,
    }, warnings


# ============================================================
# HTML card renderers
# ============================================================

def render_dashboard_cards(state: Dict[str, Any]) -> None:
    battery = state["battery"]
    cell = state["cell"]
    pack = state["pack"]
    rack = state["rack"]
    container = state["container"]
    pcs = state["pcs"]

    cell_card = f"""
    <section class="card cell">
        <div class="card-head">
            <div class="card-title">Cell</div>
            <div class="badge">{esc(battery.get("chemistry") or "LFP")}</div>
        </div>
        <div class="hero">{hero_html(battery, "cell", "🔋")}</div>
        <div class="section-title">Cell Parameters</div>
        {table_html([
            ("Nominal Capacity", fmt_unit(state["cell_cap_ah"], "Ah", 0)),
            ("Nominal Voltage", fmt_unit(state["cell_nom_v"], "V", 2)),
            ("Energy per Cell", fmt_unit(state["cell_energy_wh"], "Wh", 1)),
            ("Max Cell Voltage", fmt_unit(state["cell_max_v"], "V", 2)),
            ("Min Cell Voltage", fmt_unit(state["cell_min_v"], "V", 2)),
            ("Internal Resistance (DCIR)", fmt_unit(cell.get("internal_resistance_mohm"), "mΩ", 2)),
        ])}
        <div class="section-title">Cell Energy</div>
        <div class="energy-box">
            <span>Nominal capacity × nominal voltage</span>
            <b class="green-text">{esc(fmt_num(state["cell_energy_kwh"], 3))}</b>
            <span>kWh</span>
        </div>
    </section>
    """

    pack_card = f"""
    <section class="card pack">
        <div class="card-head">
            <div class="card-title">Pack</div>
            <div class="badge">{esc(fmt_num(state["pack_series"], 0))}S × {esc(fmt_num(state["pack_parallel"], 0))}P</div>
        </div>
        <div class="hero">{hero_html(battery, "pack", "🧱")}</div>
        <div class="section-title">Pack Parameters</div>
        {table_html([
            ("Configuration", f"{fmt_num(state['pack_series'],0)}S × {fmt_num(state['pack_parallel'],0)}P"),
            ("Total Cells", fmt_num(state["pack_total_cells"], 0)),
            ("Nominal Voltage", fmt_unit(state["pack_nom_v"], "V", 1)),
            ("Capacity", fmt_unit(state["pack_cap_ah"], "Ah", 0)),
            ("Nominal Energy", fmt_unit(state["pack_energy_kwh"], "kWh", 2)),
            ("Protection", pack.get("protection") or "BMU + Fuse"),
        ])}
        <div class="section-title">Pack Energy</div>
        <div class="energy-box">
            <span>Voltage × capacity</span>
            <b class="orange-text">{esc(fmt_num(state["pack_energy_kwh"], 2))}</b>
            <span>kWh</span>
        </div>
    </section>
    """

    rack_card = f"""
    <section class="card rack">
        <div class="card-head">
            <div class="card-title">Rack</div>
            <div class="badge">{esc(fmt_num(state["packs_per_rack"], 0))} packs series</div>
        </div>
        <div class="hero">{hero_html(battery, "rack", "🗄️")}</div>
        <div class="section-title">Rack (String) Parameters</div>
        {table_html([
            ("Packs in Series", fmt_num(state["packs_per_rack"], 0)),
            ("Total Series Cells", fmt_num(state["rack_total_series_cells"], 0)),
            ("Nominal Voltage", fmt_unit(state["rack_nom_v"], "V", 1)),
            ("Voltage Window", fmt_range(state["rack_min_v"], state["rack_max_v"], "V", 0)),
            ("Capacity", fmt_unit(state["rack_cap_ah"], "Ah", 0)),
            ("Nominal Energy", fmt_unit(state["rack_energy_kwh"], "kWh", 1)),
        ])}
        <div class="section-title">Rack @ C-rate</div>
        <div class="table">
            {row_html("String Current", fmt_unit(state["rack_current_a"], "A", 1))}
            {row_html("Rack Power", fmt_unit(state["rack_power_kw"], "kW", 1))}
            {row_html("Rack Fuse", fmt_unit(rack.get("rack_fuse_a"), "A", 0))}
        </div>
    </section>
    """

    container_card = f"""
    <section class="card container">
        <div class="card-head">
            <div class="card-title">Container</div>
            <div class="badge">{esc(fmt_num(state["racks_per_container"], 0))} racks</div>
        </div>
        <div class="hero">{hero_html(battery, "container", "▤")}</div>
        <div class="section-title">Container Parameters</div>
        {table_html([
            ("Racks (Strings) in Parallel", fmt_num(state["racks_per_container"], 0)),
            ("DC Window", fmt_range(state["dc_window_min_v"], state["dc_window_max_v"], "V", 0)),
            ("Total Energy", fmt_unit(state["container_energy_mwh"], "MWh", 2)),
            ("Power @ C-rate", fmt_unit(state["power_kw"], "kW", 0)),
            ("DC Bus Current", fmt_unit(state["dc_bus_current_a"], "A", 1)),
            ("Cooling", container.get("cooling_type") or "N/A"),
        ])}
        <div class="section-title">Discharge Duration</div>
        <div class="energy-box">
            <span>Energy ÷ power at selected C-rate</span>
            <b class="yellow-text">{esc(fmt_num(state["duration_hr"], 1))}</b>
            <span>h</span>
        </div>
    </section>
    """

    pcs_status = "OK"
    if state["pcs_utilisation_percent"] is not None and state["pcs_utilisation_percent"] > 100:
        pcs_status = "Overloaded"

    pcs_card = f"""
    <section class="card pcs">
        <div class="card-head">
            <div class="card-title">PCS</div>
            <div class="badge">{esc(pcs.get("model") or "PCS")}</div>
        </div>
        <div class="hero">{hero_html(pcs, "pcs", "⚡")}</div>
        <div class="section-title">PCS Parameters</div>
        {table_html([
            ("Rated Power", fmt_unit(state["pcs_rating_kw"], "kVA", 0)),
            ("AC Voltage", fmt_unit(pcs.get("ac_voltage_v"), "V", 0)),
            ("DC Window", fmt_range(state["dc_window_min_v"], state["dc_window_max_v"], "V", 0)),
            ("DC Inputs", fmt_num(pcs.get("dc_inputs"), 0)),
            ("Efficiency", fmt_unit(pcs.get("efficiency_percent"), "%", 1)),
            ("Max Racks / PCS", fmt_num(state["max_racks_per_pcs"], 0)),
        ])}
        <div class="section-title">PCS Utilisation</div>
        <div class="table">
            {row_html("Containers / PCS", fmt_num(state["containers_per_pcs"], 0))}
            {row_html("Racks / PCS", fmt_num(state["racks_per_pcs"], 0))}
            {row_html("Utilisation", fmt_unit(state["pcs_utilisation_percent"], "%", 1))}
            {row_html("Status", pcs_status)}
        </div>
    </section>
    """

    st.markdown(
        f"""
        <div class="flow-grid">
            {cell_card}
            <div class="arrow">→</div>
            {pack_card}
            <div class="arrow">→</div>
            {rack_card}
            <div class="arrow">→</div>
            {container_card}
            <div class="arrow">→</div>
            {pcs_card}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_strip(state: Dict[str, Any]) -> None:
    topology = (
        f"Cell → {fmt_num(state['pack_series'],0)}S Pack → "
        f"{fmt_num(state['packs_per_rack'],0)}S Rack → "
        f"{fmt_num(state['racks_per_container'],0)}P Container → PCS"
    )

    st.markdown(
        f"""
        <div class="metric-strip">
            <div class="metric">
                <span>System Energy</span>
                <b>{esc(fmt_unit(state["container_energy_mwh"], "MWh", 2))}</b>
            </div>
            <div class="metric">
                <span>System Power</span>
                <b>{esc(fmt_unit(state["power_kw"], "kW", 0))}</b>
            </div>
            <div class="metric">
                <span>DC Bus Voltage</span>
                <b>{esc(fmt_unit(state["rack_max_v"], "V", 1))}</b>
            </div>
            <div class="metric">
                <span>DC Bus Current</span>
                <b>{esc(fmt_unit(state["dc_bus_current_a"], "A", 1))}</b>
            </div>
            <div class="metric">
                <span>Duration</span>
                <b>{esc(fmt_unit(state["duration_hr"], "h", 1))}</b>
            </div>
            <div class="metric">
                <span>Topology</span>
                <small>{esc(topology)}</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary(state: Dict[str, Any]) -> None:
    battery = state["battery"]
    pcs = state["pcs"]

    st.markdown(
        f"""
        <div class="summary-grid">
            <div class="summary-panel">
                <h3>System Summary</h3>
                <div class="summary-cells">
                    <div class="summary-item"><span>Total Energy</span><b>{esc(fmt_unit(state["container_energy_mwh"], "MWh", 2))}</b></div>
                    <div class="summary-item"><span>Total Power</span><b>{esc(fmt_unit(state["power_kw"], "kW", 0))}</b></div>
                    <div class="summary-item"><span>Duration</span><b>{esc(fmt_unit(state["duration_hr"], "h", 1))}</b></div>
                    <div class="summary-item"><span>Containers</span><b>{esc(fmt_num(state["containers_per_pcs"], 0))}</b></div>
                    <div class="summary-item"><span>Racks / PCS</span><b>{esc(fmt_num(state["racks_per_pcs"], 0))}</b></div>
                </div>
            </div>
            <div class="summary-panel">
                <h3>System Configuration</h3>
                <div class="config-row"><span>Battery Container</span><span>:</span><b>{esc(battery.get("display_name"))}</b></div>
                <div class="config-row"><span>C-rate</span><span>:</span><b>{esc(state["c_rate_label"])}</b></div>
                <div class="config-row"><span>PCS Model</span><span>:</span><b>{esc(pcs.get("display_name"))}</b></div>
                <div class="config-row"><span>DC Architecture</span><span>:</span><b>Cell → Pack → Rack → Container → PCS → AC Grid</b></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sld(state: Dict[str, Any]) -> None:
    battery = state["battery"]
    pack = state["pack"]
    rack = state["rack"]
    container = state["container"]
    pcs = state["pcs"]
    c_case = state["c_case"]

    def safe_int(value: Any, default: int = 0) -> int:
        number = to_float(value)
        return default if number is None else int(round(number))

    def spec_text(*values: Any, default: str = "N/A") -> str:
        value = prefer(*values)
        if value is None or str(value).strip() == "":
            return default
        return str(value)

    pack_fuse_a = prefer_float(
        pack.get("pack_fuse_a"),
        pack.get("fuse_a"),
        get_nested(battery, "protection.pack_fuse_a"),
        get_nested(battery, "sld.pack_fuse_a"),
    )
    rack_fuse_a = prefer_float(
        rack.get("rack_fuse_a"),
        rack.get("fuse_a"),
        get_nested(battery, "protection.rack_fuse_a"),
        get_nested(battery, "sld.rack_fuse_a"),
    )
    combiner_fuse_a = prefer_float(
        container.get("combiner_fuse_a"),
        get_nested(battery, "protection.combiner_fuse_a"),
        get_nested(battery, "sld.combiner_fuse_a"),
        rack_fuse_a,
    )
    main_fuse_a = prefer_float(
        container.get("main_fuse_a"),
        container.get("cc_panel_main_fuse_a"),
        c_case.get("main_fuse_a"),
        get_nested(battery, "protection.main_fuse_a"),
        get_nested(battery, "sld.main_fuse_a"),
    )
    system_fuse_a = prefer_float(
        container.get("system_fuse_a"),
        container.get("system_breaker_a"),
        c_case.get("system_fuse_a"),
        c_case.get("system_breaker_a"),
        get_nested(battery, "protection.system_fuse_a"),
        get_nested(battery, "sld.system_fuse_a"),
        main_fuse_a,
    )
    short_circuit_ka = prefer_float(
        container.get("short_circuit_ka"),
        get_nested(battery, "protection.short_circuit_ka"),
        get_nested(battery, "sld.short_circuit_ka"),
    )

    rack_contactor = spec_text(
        rack.get("contactor"),
        rack.get("rack_contactor"),
        get_nested(battery, "protection.rack_contactor"),
        get_nested(battery, "sld.rack_contactor"),
        default="HVCB",
    )
    imd_precharge = spec_text(
        rack.get("imd_precharge"),
        rack.get("imd_pre_charge"),
        get_nested(battery, "protection.imd_precharge"),
        default="IMD + Pre-charge",
    )
    bus_cable = spec_text(
        container.get("dc_bus_cable"),
        get_nested(battery, "sld.dc_bus_cable"),
        default="Configured per project",
    )
    output_cable = spec_text(
        container.get("output_cable"),
        get_nested(battery, "sld.output_cable"),
        default="Configured per project",
    )
    bmu_label = spec_text(
        get_nested(battery, "bms.bmu_per_string"),
        get_nested(battery, "sld.bmu_per_string"),
        default="4 / string",
    )
    bcmu_label = spec_text(
        get_nested(battery, "bms.bcmu_per_string"),
        get_nested(battery, "sld.bcmu_per_string"),
        default="1 / string",
    )
    bamu_label = spec_text(
        get_nested(battery, "bms.bamu_per_container"),
        get_nested(battery, "sld.bamu_per_container"),
        default="1 / container",
    )
    grid_connection = spec_text(
        pcs.get("grid_connection"),
        pcs.get("connection"),
        get_nested(pcs, "grid.connection"),
        default="3-phase",
    )
    grid_standard = spec_text(
        pcs.get("grid_standard"),
        pcs.get("standard"),
        get_nested(pcs, "grid.standard"),
        default="UL 1741",
    )

    pack_count = max(1, safe_int(state["packs_per_rack"], 1))
    display_pack_count = min(pack_count, 4)

    def sld_node(title: str, art_key: str, rows: List[Tuple[str, Any]], css_class: str, record: Optional[Dict[str, Any]] = None) -> str:
        image_record = record if record is not None else battery
        return f"""
        <div class="sle-node {esc(css_class)}">
            <h3>{esc(title)}</h3>
            <div class="sle-art">{art_html(image_record, art_key, title)}</div>
            <div class="sle-kv">
                {''.join(f'<span>{esc(label)}</span><b>{esc(value)}</b>' for label, value in rows)}
            </div>
        </div>
        """

    def chain_arrow(label: str) -> str:
        return f'<div class="sle-arrow"><span>→</span><small>{esc(label)}</small></div>'

    pack_cards = "".join(
        f"""
        <div class="series-pack">
            <div class="pack-top"></div>
            <b>Pack {idx}</b>
            <span>{esc(fmt_unit(state["pack_nom_v"], "V", 1))}</span>
            <span>{esc(fmt_unit(state["pack_cap_ah"], "Ah", 0))}</span>
            <em>Fuse {esc(fmt_unit(pack_fuse_a, "A", 0))}</em>
        </div>
        """
        for idx in range(1, display_pack_count + 1)
    )

    if pack_count > display_pack_count:
        pack_cards += f"""
        <div class="series-pack">
            <div class="pack-top"></div>
            <b>+{esc(pack_count - display_pack_count)}</b>
            <span>additional</span>
            <span>packs</span>
            <em>series</em>
        </div>
        """

    micro_pack_count = min(pack_count, 4)
    micro_packs = "".join('<div class="micro-pack"></div>' for _ in range(micro_pack_count))

    bus_voltage_display = prefer_float(state["dc_window_max_v"], state["rack_max_v"], state["nominal_dc_bus_v"])
    bus_voltage_text = fmt_unit(bus_voltage_display, "V", 1)
    topology_text = (
        f"Cell → {fmt_num(state['pack_series'],0)}S Pack → "
        f"{fmt_num(state['packs_per_rack'],0)}S Rack → "
        f"{fmt_num(state['racks_per_container'],0)}P Container → PCS"
    )
    short_circuit_text = ""
    if short_circuit_ka is not None:
        short_circuit_text = f" / {fmt_num(short_circuit_ka, 0)} kA"

    st.markdown(
        f"""
        <div class="singleline-frame">
            <div class="sle-head">
                <div>
                    <h2>Single Line Diagram</h2>
                    <div class="sle-sub">
                        {esc(battery.get("display_name"))} | {esc(state["c_rate_label"])} - {esc(pcs.get("display_name"))}
                    </div>
                </div>
                <div class="sle-meta">
                    System: {esc(fmt_unit(state["container_energy_mwh"], "MWh", 2))} · {esc(fmt_unit(state["power_kw"], "kW", 0))}<br>
                    DC Bus: {esc(bus_voltage_text)} · {esc(fmt_unit(state["dc_bus_current_a"], "A", 1))}
                </div>
            </div>

            <div class="sle-chain">
                {sld_node("Cell", "cell", [
                    ("Capacity", fmt_unit(state["cell_cap_ah"], "Ah", 0)),
                    ("Voltage", fmt_unit(state["cell_nom_v"], "V", 2)),
                    ("Energy", fmt_unit(state["cell_energy_kwh"], "kWh", 3)),
                ], "cell")}
                {chain_arrow(f'×{fmt_num(state["pack_series"],0)}S')}
                {sld_node("Pack", "pack", [
                    ("Config", f'{fmt_num(state["pack_series"],0)}S×{fmt_num(state["pack_parallel"],0)}P'),
                    ("Voltage", fmt_unit(state["pack_nom_v"], "V", 1)),
                    ("Energy", fmt_unit(state["pack_energy_kwh"], "kWh", 1)),
                ], "pack")}
                {chain_arrow(f'×{fmt_num(state["packs_per_rack"],0)} series')}
                {sld_node("Rack / String", "rack", [
                    ("Voltage", bus_voltage_text),
                    ("Current", fmt_unit(state["rack_current_a"], "A", 1)),
                    ("Energy", fmt_unit(state["rack_energy_kwh"], "kWh", 1)),
                ], "rack")}
                {chain_arrow(f'×{fmt_num(state["racks_per_container"],0)} parallel')}
                {sld_node("Container", "container", [
                    ("Energy", fmt_unit(state["container_energy_mwh"], "MWh", 2)),
                    ("Bus V", fmt_range(state["dc_window_min_v"], state["dc_window_max_v"], "V", 0)),
                    ("Bus I", fmt_unit(state["dc_bus_current_a"], "A", 1)),
                ], "container")}
                {chain_arrow("DC")}
                {sld_node("PCS", "pcs", [
                    ("Rating", fmt_unit(state["pcs_rating_kw"], "kVA", 0)),
                    ("AC", fmt_unit(pcs.get("ac_voltage_v"), "V", 0)),
                    ("Eff", fmt_unit(pcs.get("efficiency_percent"), "%", 1)),
                ], "pcs", pcs)}
                {chain_arrow("AC")}
                {sld_node("AC Grid", "grid", [
                    ("Connection", grid_connection),
                    ("Voltage", fmt_unit(pcs.get("ac_voltage_v"), "V", 0)),
                    ("Std", grid_standard),
                ], "grid", {})}
            </div>

            <div class="sle-section-title">
                <span>Electrical Connection Path</span>
                <small>Cells → Packs → String/Rack → Rack Combiner → DC Bus → CC Panel → PCS</small>
            </div>

            <div class="path-grid">
                <div class="path-box">
                    <h4>String / Rack</h4>
                    <p>{esc(fmt_num(state["packs_per_rack"], 0))} packs connected in series per string</p>
                    <div class="series-packs">{pack_cards}</div>
                </div>
                <div class="path-arrow">→</div>

                <div class="path-box">
                    <h4>Rack Combiner</h4>
                    <p>One combiner per rack string</p>
                    <div class="cc-line"></div>
                    <p><b>Combiner fuse</b> &nbsp; {esc(fmt_unit(combiner_fuse_a, "A", 0))}{esc(short_circuit_text)}</p>
                    <p><b>Rack output</b> &nbsp; {esc(bus_voltage_text)}</p>
                    <p><b>String current</b> &nbsp; {esc(fmt_unit(state["rack_current_a"], "A", 1))}</p>
                </div>
                <div class="path-arrow">→</div>

                <div class="path-box">
                    <h4>DC Bus</h4>
                    <div class="bus-pill">{esc(bus_voltage_text)}</div>
                    <p><b>Cable</b> &nbsp; {esc(bus_cable)}</p>
                    <p><b>Total current</b> &nbsp; {esc(fmt_unit(state["dc_bus_current_a"], "A", 1))}</p>
                </div>
                <div class="path-arrow">→</div>

                <div class="path-box">
                    <h4>CC Panel</h4>
                    <p>DC collection and protection panel</p>
                    <div class="cc-line"></div>
                    <p><b>Main fuse</b> &nbsp; {esc(fmt_unit(main_fuse_a, "A", 0))}{esc(short_circuit_text)}</p>
                    <p><b>Output cable</b> &nbsp; {esc(output_cable)}</p>
                </div>
                <div class="path-arrow">→</div>

                <div class="path-box">
                    <h4>PCS</h4>
                    <p>DC/AC conversion</p>
                    <div class="path-art">{art_html(pcs, "pcs", "PCS")}</div>
                    <p><b>Rating</b> &nbsp; {esc(fmt_unit(state["pcs_rating_kw"], "kVA", 0))}</p>
                    <p><b>Utilisation</b> &nbsp; {esc(fmt_unit(state["pcs_utilisation_percent"], "%", 1))}</p>
                </div>
            </div>

            <div class="detail-grid">
                <div class="detail-panel">
                    <h4>String / Rack Detail</h4>
                    <div class="micro-packs">
                        {micro_packs}
                        <div class="micro-caption">{esc(fmt_num(state["packs_per_rack"], 0))} packs in series<br>{esc(bus_voltage_text)}</div>
                    </div>
                    <div class="protection-row">
                        <div class="protection-chip"><span>Fuse</span><b>{esc(fmt_unit(rack_fuse_a, "A", 0))}</b></div>
                        <div class="protection-chip"><span>Contactor</span><b>{esc(rack_contactor)}</b></div>
                        <div class="protection-chip"><span>IMD + Pre-charge</span><b>{esc(imd_precharge)}</b></div>
                    </div>
                    <div class="note-band">
                        HVCB = high-voltage control box. Each string isolates independently; rack fuse trips before pack fuse where reverse coordination is required.
                    </div>
                </div>

                <div class="detail-panel">
                    <h4>DC Bus &amp; Container</h4>
                    <div class="energy-bar"></div>
                    <div class="dc-bus-visual">
                        <div class="path-art" style="height:74px;margin:0;">{art_html(battery, "container", "BESS")}</div>
                        <div>
                            <p><b>{esc(fmt_num(state["racks_per_container"], 0))} racks in parallel</b></p>
                            <p>Bus V: {esc(fmt_range(state["dc_window_min_v"], state["dc_window_max_v"], "V", 0))}</p>
                            <p>Energy: {esc(fmt_unit(state["container_energy_mwh"], "MWh", 2))}</p>
                        </div>
                    </div>
                    <div class="detail-metrics">
                        <div class="detail-metric"><span>Power @ C-rate</span><b>{esc(fmt_unit(state["power_kw"], "kW", 0))}</b></div>
                        <div class="detail-metric"><span>Duration</span><b>{esc(fmt_unit(state["duration_hr"], "h", 1))}</b></div>
                    </div>
                </div>

                <div class="detail-panel">
                    <h4>Protection Coordination</h4>
                    <div class="fuse-flow">
                        <div class="fuse-card"><span>Pack Fuse</span><b>{esc(fmt_unit(pack_fuse_a, "A", 0))}</b><span>Pack level</span></div>
                        <div class="fuse-arrow">→</div>
                        <div class="fuse-card"><span>Rack Fuse</span><b>{esc(fmt_unit(rack_fuse_a, "A", 0))}</b><span>String level</span></div>
                        <div class="fuse-arrow">→</div>
                        <div class="fuse-card"><span>System</span><b>{esc(fmt_unit(system_fuse_a, "A", 0))}</b><span>DC bus</span></div>
                    </div>
                    <div class="note-band">
                        Confirm final fuse, breaker, and cable ratings against NEC / IEC requirements, available fault current, and manufacturer coordination curves.
                    </div>
                    <div class="bms-row">
                        <div class="bms-card"><span>BMU</span><b>{esc(bmu_label)}</b></div>
                        <div class="bms-card"><span>BCMU</span><b>{esc(bcmu_label)}</b></div>
                        <div class="bms-card"><span>BAMU</span><b>{esc(bamu_label)}</b></div>
                    </div>
                </div>
            </div>

            <div class="sle-footer">
                <div class="sle-foot-item"><span>System Energy</span><b>{esc(fmt_unit(state["container_energy_mwh"], "MWh", 2))}</b></div>
                <div class="sle-foot-item"><span>System Power</span><b>{esc(fmt_unit(state["power_kw"], "kW", 0))}</b></div>
                <div class="sle-foot-item"><span>Bus Voltage</span><b>{esc(bus_voltage_text)}</b></div>
                <div class="sle-foot-item"><span>Bus Current</span><b>{esc(fmt_unit(state["dc_bus_current_a"], "A", 1))}</b></div>
                <div class="sle-foot-item"><span>Duration</span><b>{esc(fmt_unit(state["duration_hr"], "h", 1))}</b></div>
                <div class="sle-foot-item"><span>PCS Utilisation</span><b>{esc(fmt_unit(state["pcs_utilisation_percent"], "%", 1))}</b></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



# ============================================================
# Main app
# ============================================================

try:
    data = load_dataset()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()
except json.JSONDecodeError as exc:
    st.error(f"Invalid JSON file: {exc}")
    st.stop()
except Exception as exc:
    st.error(f"Unexpected dataset loading error: {exc}")
    st.stop()


errors, data_warnings = validate_dataset(data)

if errors:
    st.error("Dataset has blocking errors.")
    for error in errors:
        st.error(error)
    st.stop()


battery_records = active_records(data.get("battery_containers", []))
pcs_records = active_records(data.get("pcs_models", []))
c_rate_records = data.get("c_rate_cases", [])

if not battery_records:
    st.error("No active battery containers found in JSON.")
    st.stop()

if not pcs_records:
    st.error("No active PCS models found in JSON.")
    st.stop()


rules = data.get("dashboard_rules", {})
default_battery_id = rules.get("selected_battery_container")
default_pcs_id = rules.get("selected_pcs")
default_c_rate = rules.get("selected_c_rate")


battery_display_map = {
    str(row.get("display_name") or row.get("id")): row for row in battery_records
}
pcs_display_map = {
    str(row.get("display_name") or row.get("id")): row for row in pcs_records
}


battery_names = list(battery_display_map.keys())
pcs_names = list(pcs_display_map.keys())

default_battery_record = find_by_id(battery_records, default_battery_id)
default_pcs_record = find_by_id(pcs_records, default_pcs_id)

default_battery_name = (
    str(default_battery_record.get("display_name") or default_battery_record.get("id"))
    if default_battery_record
    else battery_names[0]
)

default_pcs_name = (
    str(default_pcs_record.get("display_name") or default_pcs_record.get("id"))
    if default_pcs_record
    else pcs_names[0]
)


def ensure_session_option(key: str, options: List[str], default_value: Optional[str] = None) -> Optional[str]:
    if not options:
        return None

    default = default_value if default_value in options else options[0]

    if st.session_state.get(key) not in options:
        st.session_state[key] = default

    return st.session_state[key]


ensure_session_option("bess_battery_name", battery_names, default_battery_name)
ensure_session_option("bess_pcs_name", pcs_names, default_pcs_name)

selected_battery_name = st.session_state["bess_battery_name"]
selected_pcs_name = st.session_state["bess_pcs_name"]
selected_battery = battery_display_map[selected_battery_name]
selected_pcs = pcs_display_map[selected_pcs_name]

matching_cases = [
    row for row in c_rate_records
    if str(row.get("battery_container_id")) == str(selected_battery.get("id"))
]
matching_cases = sorted(
    matching_cases,
    key=lambda row: parse_c_rate(row.get("c_rate")) if parse_c_rate(row.get("c_rate")) is not None else 999,
)
c_rate_options = [str(row.get("c_rate")) for row in matching_cases]
ensure_session_option("bess_c_rate", c_rate_options, default_c_rate)

selected_case = None
if c_rate_options:
    selected_case = next(
        row for row in matching_cases
        if str(row.get("c_rate")) == str(st.session_state["bess_c_rate"])
    )

if selected_case is None:
    subtitle = f"{selected_battery.get('display_name')} | No C-rate case | {selected_pcs.get('display_name')}"
    state = None
    calculation_warnings: List[str] = []
else:
    state, calculation_warnings = calculate_state(selected_battery, selected_case, selected_pcs)
    subtitle = (
        f"{selected_battery.get('display_name')} | "
        f"{state['c_rate_label']} | "
        f"{selected_pcs.get('display_name')} | "
        f"{fmt_unit(state['container_energy_mwh'], 'MWh', 2)} | "
        f"{fmt_unit(state['power_kw'], 'kW', 0)}"
    )

st.markdown('<div class="bess-title">BESS System Dashboard</div>', unsafe_allow_html=True)
st.markdown(f'<div class="bess-subtitle">{esc(subtitle)}</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.35, 0.7, 1.08])

with col1:
    selected_battery_name = st.selectbox(
        "Battery Container",
        battery_names,
        key="bess_battery_name",
    )

# Rebuild the C-rate list immediately after the battery widget value so a user
# switching battery containers always sees compatible C-rate cases on rerun.
selected_battery = battery_display_map[selected_battery_name]
matching_cases = [
    row for row in c_rate_records
    if str(row.get("battery_container_id")) == str(selected_battery.get("id"))
]
matching_cases = sorted(
    matching_cases,
    key=lambda row: parse_c_rate(row.get("c_rate")) if parse_c_rate(row.get("c_rate")) is not None else 999,
)
c_rate_options = [str(row.get("c_rate")) for row in matching_cases]
ensure_session_option("bess_c_rate", c_rate_options, default_c_rate)

with col2:
    if c_rate_options:
        selected_c_rate = st.selectbox(
            "C-rate",
            c_rate_options,
            key="bess_c_rate",
        )
    else:
        selected_c_rate = st.selectbox(
            "C-rate",
            ["No C-rate rows found"],
            disabled=True,
        )

with col3:
    selected_pcs_name = st.selectbox(
        "PCS Inverter",
        pcs_names,
        key="bess_pcs_name",
    )

selected_pcs = pcs_display_map[selected_pcs_name]

if not c_rate_options:
    st.error(
        "The selected battery container has no C-rate cases. "
        "Add matching rows under c_rate_cases in data/bess_dataset.json."
    )
    st.stop()

selected_case = next(row for row in matching_cases if str(row.get("c_rate")) == str(selected_c_rate))
state, calculation_warnings = calculate_state(selected_battery, selected_case, selected_pcs)

all_warnings = data_warnings + calculation_warnings
if all_warnings:
    with st.expander("Calculation notices", expanded=False):
        for warning in all_warnings:
            st.markdown(f'<div class="warn">{esc(warning)}</div>', unsafe_allow_html=True)


dashboard_tab, sld_tab = st.tabs(["Dashboard", "Single Line Diagram"])

with dashboard_tab:
    render_dashboard_cards(state)
    render_metric_strip(state)

with sld_tab:
    render_sld(state)
