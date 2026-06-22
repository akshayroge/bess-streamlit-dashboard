from typing import Any, Dict

from src.assets import asset_to_data_uri
from src.calculations import calculate_dashboard, fmt, selected_objects


def kv(label: str, value: str) -> str:
    return f"""
    <div class="kv">
      <span>{label}</span>
      <b>{value}</b>
    </div>
    """


def eval_row(label: str, value: str) -> str:
    return f"""
    <div class="eval">
      <span>{label}</span>
      <b>{value}</b>
    </div>
    """


def render_dashboard_html(db: Dict[str, Any], c_rate_key: str) -> str:
    objs = selected_objects(db)

    cell = objs["cell"]
    pack = objs["pack"]
    rack = objs["rack"]
    container = objs["container"]
    pcs = objs["pcs"]
    protection = objs["protection"]

    calc = calculate_dashboard(db, c_rate_key)

    container_img = asset_to_data_uri(container.get("image"), "BESS CONTAINER")
    pcs_img = asset_to_data_uri(pcs.get("image"), "PCS")

    clou_logo = asset_to_data_uri(
        db.get("ui", {}).get("logos", {}).get("clou"),
        "CLOU"
    )

    midea_logo = asset_to_data_uri(
        db.get("ui", {}).get("logos", {}).get("midea"),
        "MIDEA"
    )

    pack_fuse = protection.get("pack_fuse", {}).get("rating_a", pack.get("fuse_a", 400))
    rack_hvcb = protection.get("rack_hvcb", {}).get("rating_a", rack.get("hvcb_a", 350))
    system_fuse = protection.get("system_fuse", {}).get("rating_a", 1800)

    return f"""
<div class="bess-shell">

  <div class="bess-top">
    <div class="bess-title">
      <h1>{db["project"]["name"]}</h1>
      <p>{db["project"]["system_type"]} · Selected C-rate: <b>{c_rate_key}</b></p>
    </div>

    <div class="logo-row">
      <div class="logo-box">
        <img src="{clou_logo}" alt="CLOU"/>
      </div>
      <div class="logo-box">
        <img src="{midea_logo}" alt="Midea"/>
      </div>
    </div>
  </div>

  <div class="grid3">

    <section class="card battery">
      <div class="card-head">
        <div>
          <h3>Battery Cell / Pack / Rack</h3>
          <p class="footer-note">Cell to string architecture</p>
        </div>
        <span class="tag">LFP</span>
      </div>

      <div class="imgband">
        <div class="placeholder-icon">
          <div class="big-symbol">▦</div>
          <b>Cell → Pack → Rack</b>
        </div>
      </div>

      {kv("Cell Voltage", f'{fmt(cell["nominal_voltage_v"], 1)} V')}
      {kv("Cell Capacity", f'{fmt(cell["capacity_ah"], 0)} Ah')}
      {kv("Pack Configuration", f'{pack["cells_series"]}S')}
      {kv("Pack Energy", f'{fmt(calc["pack_kwh"], 1)} kWh')}
      {kv("Rack Voltage", f'{fmt(calc["rack_v"], 1)} V')}
      {kv("Rack Energy", f'{fmt(calc["rack_kwh"], 1)} kWh')}
    </section>

    <section class="card container">
      <div class="card-head">
        <div>
          <h3>Container Parameters</h3>
          <p class="footer-note">{container["name"]}</p>
        </div>
        <span class="tag">BESS</span>
      </div>

      <div class="imgband">
        <img src="{container_img}" alt="BESS Container"/>
      </div>

      {kv("Total Energy", f'{fmt(calc["container_mwh"], 2)} MWh')}
      {kv("Racks / Container", f'{container["racks_per_container"]}')}
      {kv("DC Window", calc["dc_window_text"])}
      {kv("DC Bus Current", f'{fmt(calc["dc_bus_current_a"], 1)} A')}
      {kv("Power @ C-rate", f'{fmt(calc["power_kw"], 0)} kW')}
      {kv("Cooling", container.get("cooling", "Liquid"))}
    </section>

    <section class="card pcs">
      <div class="card-head">
        <div>
          <h3>PCS Parameters</h3>
          <p class="footer-note">{pcs["model"]}</p>
        </div>
        <span class="tag">PCS</span>
      </div>

      <div class="imgband">
        <img src="{pcs_img}" alt="PCS"/>
      </div>

      {kv("Rated Power", f'{fmt(pcs["rating_kva"], 0)} kVA')}
      {kv("AC Voltage", f'{fmt(pcs["ac_voltage_v"], 0)} V')}
      {kv("DC Window", f'{int(pcs["dc_window_min_v"])}-{int(pcs["dc_window_max_v"])} V')}
      {kv("Efficiency", f'{fmt(pcs["efficiency_percent"], 1)} %')}
      {kv("Containers / PCS", f'{calc["containers_per_pcs"]}')}
      {kv("Utilisation", f'{fmt(calc["pcs_utilization"], 1)} %')}
    </section>

  </div>

  <div class="summary">
    <div class="sum-box">
      <span>Container Energy</span>
      <b>{fmt(calc["container_mwh"], 2)} MWh</b>
    </div>
    <div class="sum-box">
      <span>Power @ C-rate</span>
      <b>{fmt(calc["power_kw"], 0)} kW</b>
    </div>
    <div class="sum-box">
      <span>DC Bus Current</span>
      <b>{fmt(calc["dc_bus_current_a"], 1)} A</b>
    </div>
    <div class="sum-box">
      <span>Containers / PCS</span>
      <b>{calc["containers_per_pcs"]}</b>
    </div>
    <div class="sum-box">
      <span>Duration</span>
      <b>{fmt(calc["duration_h"], 1)} h</b>
    </div>
  </div>

  <section class="sld-wrap">

    <div class="section-title">
      <div>
        <h2>Single Line Diagram</h2>
        <p>Electrical connection from string to rack combiner to DC bus to CC panel to PCS</p>
      </div>
      <div class="tag">DC Window {calc["dc_window_text"]}</div>
    </div>

    <div class="chain">

      <div class="cn">
        <h3>Cell</h3>
        <div class="ico">CELL</div>
        <div class="ckv"><span>Voltage</span><b>{fmt(cell["nominal_voltage_v"], 1)} V</b></div>
        <div class="ckv"><span>Capacity</span><b>{fmt(cell["capacity_ah"], 0)} Ah</b></div>
        <div class="ckv"><span>Energy</span><b>{fmt(calc["cell_kwh"], 3)} kWh</b></div>
      </div>

      <div class="conn"><div class="ar">→</div><small>×104S</small></div>

      <div class="cn">
        <h3>Pack</h3>
        <div class="ico">PACK</div>
        <div class="ckv"><span>Voltage</span><b>{fmt(calc["pack_v"], 1)} V</b></div>
        <div class="ckv"><span>Capacity</span><b>{fmt(pack["capacity_ah"], 0)} Ah</b></div>
        <div class="ckv"><span>Energy</span><b>{fmt(calc["pack_kwh"], 1)} kWh</b></div>
      </div>

      <div class="conn"><div class="ar">→</div><small>×4 series</small></div>

      <div class="cn">
        <h3>Rack / String</h3>
        <div class="ico">RACK</div>
        <div class="ckv"><span>Voltage</span><b>{fmt(calc["rack_v"], 1)} V</b></div>
        <div class="ckv"><span>Energy</span><b>{fmt(calc["rack_kwh"], 1)} kWh</b></div>
        <div class="ckv"><span>HVCB</span><b>{rack_hvcb} A</b></div>
      </div>

      <div class="conn"><div class="ar">→</div><small>×12 parallel</small></div>

      <div class="cn">
        <h3>Container</h3>
        <div class="ico"><img src="{container_img}" alt="Container"/></div>
        <div class="ckv"><span>Energy</span><b>{fmt(calc["container_mwh"], 2)} MWh</b></div>
        <div class="ckv"><span>Bus V</span><b>{calc["dc_window_text"]}</b></div>
        <div class="ckv"><span>Current</span><b>{fmt(calc["dc_bus_current_a"], 1)} A</b></div>
      </div>

      <div class="conn"><div class="ar">→</div><small>DC Bus</small></div>

      <div class="cn">
        <h3>PCS</h3>
        <div class="ico"><img src="{pcs_img}" alt="PCS"/></div>
        <div class="ckv"><span>Rating</span><b>{fmt(pcs["rating_kva"], 0)} kVA</b></div>
        <div class="ckv"><span>AC</span><b>{fmt(pcs["ac_voltage_v"], 0)} V</b></div>
        <div class="ckv"><span>Efficiency</span><b>{fmt(pcs["efficiency_percent"], 1)} %</b></div>
      </div>

      <div class="conn"><div class="ar">→</div><small>AC</small></div>

      <div class="cn">
        <h3>AC Grid</h3>
        <div class="ico">GRID</div>
        <div class="ckv"><span>Type</span><b>3-Phase</b></div>
        <div class="ckv"><span>Voltage</span><b>{fmt(pcs["ac_voltage_v"], 0)} Vac</b></div>
        <div class="ckv"><span>Output</span><b>UL1741</b></div>
      </div>

    </div>

    <div class="econn">

      <div class="section-title">
        <div>
          <h2>Electrical Connection Path</h2>
          <p>String to rack combiner to DC bus to CC panel to PCS</p>
        </div>
      </div>

      <div class="egrid">

        <div class="eblock">
          <h5>Rack String</h5>
          <div class="subv">4 packs in series</div>

          <div class="packline">
            <div class="packbox"><b>Pack 1</b><span>{fmt(calc["pack_v"], 1)} V</span></div>
            <div class="packbox"><b>Pack 2</b><span>{fmt(calc["pack_v"], 1)} V</span></div>
            <div class="packbox"><b>Pack 3</b><span>{fmt(calc["pack_v"], 1)} V</span></div>
            <div class="packbox"><b>Pack 4</b><span>{fmt(calc["pack_v"], 1)} V</span></div>
          </div>

          <div class="fusebar">Pack Fuse {pack_fuse} A · Rack HVCB {rack_hvcb} A</div>
        </div>

        <div class="earrow">→</div>

        <div class="eblock">
          <h5>Rack Combiner</h5>
          <div class="subv">12 parallel strings</div>
          {eval_row("Rack Voltage", f'{fmt(calc["rack_v"], 1)} V')}
          {eval_row("Rack Energy", f'{fmt(calc["rack_kwh"], 1)} kWh')}
          {eval_row("Racks", f'{container["racks_per_container"]}')}
        </div>

        <div class="earrow">→</div>

        <div class="eblock">
          <h5>DC Bus</h5>
          <div class="subv">Container bus</div>
          {eval_row("Voltage", calc["dc_window_text"])}
          {eval_row("Current", f'{fmt(calc["dc_bus_current_a"], 1)} A')}
          {eval_row("Energy", f'{fmt(calc["container_mwh"], 2)} MWh')}
        </div>

        <div class="earrow">→</div>

        <div class="eblock">
          <h5>CC Panel</h5>
          <div class="subv">Protection coordination</div>
          {eval_row("Main Fuse", f'{system_fuse} A')}
          {eval_row("DC Current", f'{fmt(calc["dc_bus_current_a"], 1)} A')}
          {eval_row("BMU / BCMU", f'{rack["bmu_count"]} / {rack["bcmu_count"]}')}
        </div>

        <div class="earrow">→</div>

        <div class="eblock">
          <h5>PCS</h5>
          <div class="subv">DC/AC conversion</div>
          <div class="pcs-photo-wrap">
            <img src="{pcs_img}" alt="PCS"/>
          </div>
          {eval_row("Rating", f'{fmt(pcs["rating_kva"], 0)} kVA')}
          {eval_row("AC Voltage", f'{fmt(pcs["ac_voltage_v"], 0)} V')}
          {eval_row("Utilisation", f'{fmt(calc["pcs_utilization"], 1)} %')}
        </div>

      </div>

      <div class="footer-note">
        Container-to-PCS architecture:
        <b>{calc["architecture_text"]}</b>.
        Max racks per PCS:
        <b>{calc["max_racks_per_pcs"]}</b>.
      </div>

    </div>

  </section>

</div>
"""