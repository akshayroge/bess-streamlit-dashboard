from typing import Any, Dict

from src.assets import asset_to_data_uri
from src.calculations import calculate_dashboard, fmt, selected_objects


def dash(value: Any, fallback: str = "—") -> str:
    if value is None:
        return fallback

    if isinstance(value, str) and value.strip() == "":
        return fallback

    return str(value)


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


def get_dashboard_objects(db: Dict[str, Any], c_rate_key: str) -> Dict[str, Any]:
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

    pack_fuse = protection.get("pack_fuse", {}).get("rating_a", pack.get("fuse_a", 400))
    rack_hvcb = protection.get("rack_hvcb", {}).get("rating_a", rack.get("hvcb_a", 350))
    system_fuse = protection.get("system_fuse", {}).get("rating_a", 1800)

    pack_config = pack.get("configuration")
    if not pack_config:
        pack_config = f'{pack.get("cells_series", 104)}S x {pack.get("cells_parallel", 1)}P'

    rack_dc_window = (
        f'{fmt(rack.get("minimum_voltage_v", container.get("dc_window_min_v", 0)), 0)}-'
        f'{fmt(rack.get("maximum_voltage_v", container.get("dc_window_max_v", 0)), 0)} V'
    )

    pack_tag = f'{pack.get("cells_series", 104)}S x {pack.get("cells_parallel", 1)}P'
    rack_tag = f'{rack.get("packs_series", rack.get("modules_per_string", 4))} packs series'
    container_tag = f'{container.get("racks_per_container", 0)} racks'
    pcs_tag = pcs.get("model", pcs.get("name", "PCS"))

    return {
        "cell": cell,
        "pack": pack,
        "rack": rack,
        "container": container,
        "pcs": pcs,
        "calc": calc,
        "container_img": container_img,
        "pcs_img": pcs_img,
        "pack_fuse": pack_fuse,
        "rack_hvcb": rack_hvcb,
        "system_fuse": system_fuse,
        "pack_config": pack_config,
        "rack_dc_window": rack_dc_window,
        "pack_tag": pack_tag,
        "rack_tag": rack_tag,
        "container_tag": container_tag,
        "pcs_tag": pcs_tag,
    }


def render_cards_html(db: Dict[str, Any], c_rate_key: str) -> str:
    ctx = get_dashboard_objects(db, c_rate_key)

    cell = ctx["cell"]
    pack = ctx["pack"]
    rack = ctx["rack"]
    container = ctx["container"]
    pcs = ctx["pcs"]
    calc = ctx["calc"]

    container_img = ctx["container_img"]
    pcs_img = ctx["pcs_img"]

    pack_config = ctx["pack_config"]
    rack_dc_window = ctx["rack_dc_window"]
    pack_tag = ctx["pack_tag"]
    rack_tag = ctx["rack_tag"]
    container_tag = ctx["container_tag"]
    pcs_tag = ctx["pcs_tag"]
    rack_hvcb = ctx["rack_hvcb"]

    return f"""
<div class="bess-shell">

  <div class="grid5">

    <section class="card cell module-card">
      <div class="card-head">
        <div>
          <h3>CELL</h3>
        </div>
        <span class="tag">LFP</span>
      </div>

      <div class="imgband module-imgband label-imgband">
        <div class="module-visual-label">
          <div class="module-visual-icon">▦</div>
          <b>CELL</b>
        </div>
      </div>

      <div class="module-param-title">CELL PARAMETERS</div>
      {kv("Chemistry", dash(cell.get("chemistry"), "LFP"))}
      {kv("Nominal Voltage", f'{fmt(cell.get("nominal_voltage_v", 0), 1)} V')}
      {kv("Capacity", f'{fmt(cell.get("capacity_ah", 0), 0)} Ah')}
      {kv("Energy", f'{fmt(calc["cell_kwh"], 3)} kWh')}
      {kv("Max Voltage", f'{fmt(cell.get("maximum_cell_voltage_v", 3.65), 2)} V')}
      {kv("Min Voltage", f'{fmt(cell.get("minimum_cell_voltage_v", 2.5), 2)} V')}
    </section>

    <section class="card pack module-card">
      <div class="card-head">
        <div>
          <h3>PACK</h3>
        </div>
        <span class="tag">{pack_tag}</span>
      </div>

      <div class="imgband module-imgband label-imgband">
        <div class="module-visual-label">
          <div class="module-visual-icon">▤</div>
          <b>PACK</b>
        </div>
      </div>

      <div class="module-param-title">PACK PARAMETERS</div>
      {kv("Configuration", str(pack_config))}
      {kv("Series", f'{pack.get("cells_series", 104)} S')}
      {kv("Parallel", f'{pack.get("cells_parallel", 1)} P')}
      {kv("Voltage", f'{fmt(calc["pack_v"], 1)} V')}
      {kv("Capacity", f'{fmt(pack.get("capacity_ah", cell.get("capacity_ah", 0)), 0)} Ah')}
      {kv("Energy", f'{fmt(calc["pack_kwh"], 1)} kWh')}
    </section>

    <section class="card rack module-card">
      <div class="card-head">
        <div>
          <h3>RACK</h3>
        </div>
        <span class="tag">{rack_tag}</span>
      </div>

      <div class="imgband module-imgband label-imgband">
        <div class="module-visual-label">
          <div class="module-visual-icon">▥</div>
          <b>RACK</b>
        </div>
      </div>

      <div class="module-param-title">RACK (STRING) PARAMETERS</div>
      {kv("Modules / String", f'{rack.get("modules_per_string", rack.get("packs_series", 4))}')}
      {kv("Voltage", f'{fmt(calc["rack_v"], 1)} V')}
      {kv("DC Window", rack_dc_window)}
      {kv("Capacity", f'{fmt(rack.get("capacity_ah", pack.get("capacity_ah", 0)), 0)} Ah')}
      {kv("Energy", f'{fmt(calc["rack_kwh"], 1)} kWh')}
      {kv("HVCB", f'{rack_hvcb} A')}
    </section>

    <section class="card container module-card">
      <div class="card-head">
        <div>
          <h3>CONTAINER</h3>
        </div>
        <span class="tag">{container_tag}</span>
      </div>

      <div class="imgband module-imgband">
        <img src="{container_img}" alt="BESS Container"/>
      </div>

      <div class="module-param-title">CONTAINER PARAMETERS</div>
      {kv("Model", dash(container.get("name")))}
      {kv("Total Energy", f'{fmt(calc["container_mwh"], 2)} MWh')}
      {kv("Racks / Container", f'{container["racks_per_container"]}')}
      {kv("DC Window", calc["dc_window_text"])}
      {kv("DC Bus Current", f'{fmt(calc["dc_bus_current_a"], 1)} A')}
      {kv("Cooling", container.get("cooling", "Liquid Cooling"))}
    </section>

    <section class="card pcs module-card">
      <div class="card-head">
        <div>
          <h3>PCS</h3>
        </div>
        <span class="tag">{pcs_tag}</span>
      </div>

      <div class="imgband module-imgband">
        <img src="{pcs_img}" alt="PCS"/>
      </div>

      <div class="module-param-title">PCS PARAMETERS</div>
      {kv("Rated Power", f'{fmt(pcs["rating_kva"], 0)} kVA')}
      {kv("AC Voltage", f'{fmt(pcs["ac_voltage_v"], 0)} V')}
      {kv("DC Window", f'{int(pcs["dc_window_min_v"])}-{int(pcs["dc_window_max_v"])} V')}
      {kv("DC Inputs", f'{pcs.get("dc_inputs", 2)}')}
      {kv("Efficiency", f'{fmt(pcs["efficiency_percent"], 1)} %')}
      {kv("Utilisation", f'{fmt(calc["pcs_utilization"], 1)} %')}
    </section>

  </div>

</div>
"""


def render_sld_html(db: Dict[str, Any], c_rate_key: str) -> str:
    ctx = get_dashboard_objects(db, c_rate_key)

    cell = ctx["cell"]
    pack = ctx["pack"]
    rack = ctx["rack"]
    container = ctx["container"]
    pcs = ctx["pcs"]
    calc = ctx["calc"]

    container_img = ctx["container_img"]
    pcs_img = ctx["pcs_img"]

    pack_fuse = ctx["pack_fuse"]
    rack_hvcb = ctx["rack_hvcb"]
    system_fuse = ctx["system_fuse"]
    pack_config = ctx["pack_config"]

    return f"""
<div class="bess-shell">

  <section class="sld-wrap">

    <div class="section-title">
      <div>
        <h2>Single Line Diagram</h2>
        <p>Electrical connection from cell to pack to rack, rack combiner, DC bus, CC panel, PCS and AC grid</p>
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

      <div class="conn"><div class="ar">→</div><small>{pack.get("cells_series", 104)}S</small></div>

      <div class="cn">
        <h3>Pack</h3>
        <div class="ico">PACK</div>
        <div class="ckv"><span>Config</span><b>{pack_config}</b></div>
        <div class="ckv"><span>Voltage</span><b>{fmt(calc["pack_v"], 1)} V</b></div>
        <div class="ckv"><span>Energy</span><b>{fmt(calc["pack_kwh"], 1)} kWh</b></div>
      </div>

      <div class="conn"><div class="ar">→</div><small>x{rack.get("packs_series", 4)} series</small></div>

      <div class="cn">
        <h3>Rack</h3>
        <div class="ico">RACK</div>
        <div class="ckv"><span>Voltage</span><b>{fmt(calc["rack_v"], 1)} V</b></div>
        <div class="ckv"><span>Energy</span><b>{fmt(calc["rack_kwh"], 1)} kWh</b></div>
        <div class="ckv"><span>HVCB</span><b>{rack_hvcb} A</b></div>
      </div>

      <div class="conn"><div class="ar">→</div><small>x{container["racks_per_container"]} parallel</small></div>

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
          <div class="subv">{rack.get("packs_series", 4)} packs in series</div>

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
          <div class="subv">{container["racks_per_container"]} parallel strings</div>
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


def render_dashboard_html(db: Dict[str, Any], c_rate_key: str) -> str:
    return render_cards_html(db, c_rate_key) + render_sld_html(db, c_rate_key)
