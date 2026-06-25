from typing import Any, Dict

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


def symbol_html(kind: str) -> str:
    """
    CSS-drawn component symbols used in cards and SLD.

    kind options:
      cell, pack, rack, container, pcs, grid, dc_bus, cc_panel, combiner
    """

    if kind == "cell":
        return """
        <div class="symbol symbol-cell">
          <div class="cell-plus"></div>
          <div class="cell-body">
            <span>LFP</span>
          </div>
        </div>
        """

    if kind == "pack":
        return """
        <div class="symbol symbol-pack">
          <div class="pack-shell">
            <span></span><span></span><span></span><span></span><span></span>
          </div>
        </div>
        """

    if kind == "rack":
        return """
        <div class="symbol symbol-rack">
          <div class="rack-cabinet">
            <span></span><span></span><span></span><span></span>
          </div>
        </div>
        """

    if kind == "container":
        return """
        <div class="symbol symbol-container">
          <div class="container-box">
            <div class="container-door"></div>
            <div class="container-lines"></div>
            <div class="container-vent"></div>
          </div>
        </div>
        """

    if kind == "pcs":
        return """
        <div class="symbol symbol-pcs">
          <div class="pcs-cabinet">
            <div class="pcs-screen"></div>
            <div class="pcs-wave">∿</div>
            <div class="pcs-vents"></div>
          </div>
        </div>
        """

    if kind == "grid":
        return """
        <div class="symbol symbol-grid">
          <div class="grid-triangle"></div>
          <div class="grid-line grid-line-1"></div>
          <div class="grid-line grid-line-2"></div>
          <div class="grid-line grid-line-3"></div>
        </div>
        """

    if kind == "dc_bus":
        return """
        <div class="symbol symbol-dc-bus">
          <div class="bus-bar"></div>
          <div class="bus-value">DC</div>
        </div>
        """

    if kind == "cc_panel":
        return """
        <div class="symbol symbol-cc-panel">
          <div class="panel-door">
            <span></span><span></span><span></span>
          </div>
        </div>
        """

    if kind == "combiner":
        return """
        <div class="symbol symbol-combiner">
          <div class="combiner-line"></div>
          <div class="combiner-node"></div>
          <div class="combiner-switch"></div>
        </div>
        """

    return """
    <div class="symbol symbol-generic">
      <span>●</span>
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

    try:
        c_rate = float(str(c_rate_key).replace("C", "").strip())
    except Exception:
        c_rate = float(calc.get("profile", {}).get("c_rate", 0.25))

    rack_capacity = float(rack.get("capacity_ah", pack.get("capacity_ah", cell.get("capacity_ah", 0))))
    string_current_a = rack_capacity * c_rate if rack_capacity > 0 else 0

    bus_voltage_v = container.get("dc_window_max_v", rack.get("maximum_voltage_v", 0))
    bus_voltage_text = f'{fmt(bus_voltage_v, 1)} V'

    return {
        "cell": cell,
        "pack": pack,
        "rack": rack,
        "container": container,
        "pcs": pcs,
        "calc": calc,
        "pack_fuse": pack_fuse,
        "rack_hvcb": rack_hvcb,
        "system_fuse": system_fuse,
        "pack_config": pack_config,
        "rack_dc_window": rack_dc_window,
        "pack_tag": pack_tag,
        "rack_tag": rack_tag,
        "container_tag": container_tag,
        "pcs_tag": pcs_tag,
        "c_rate": c_rate,
        "string_current_a": string_current_a,
        "bus_voltage_v": bus_voltage_v,
        "bus_voltage_text": bus_voltage_text
    }


def render_cards_html(db: Dict[str, Any], c_rate_key: str) -> str:
    ctx = get_dashboard_objects(db, c_rate_key)

    cell = ctx["cell"]
    pack = ctx["pack"]
    rack = ctx["rack"]
    container = ctx["container"]
    pcs = ctx["pcs"]
    calc = ctx["calc"]

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

      <div class="imgband module-imgband symbol-imgband">
        {symbol_html("cell")}
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

      <div class="imgband module-imgband symbol-imgband">
        {symbol_html("pack")}
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

      <div class="imgband module-imgband symbol-imgband">
        {symbol_html("rack")}
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

      <div class="imgband module-imgband symbol-imgband">
        {symbol_html("container")}
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

      <div class="imgband module-imgband symbol-imgband">
        {symbol_html("pcs")}
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

    pack_fuse = ctx["pack_fuse"]
    rack_hvcb = ctx["rack_hvcb"]
    system_fuse = ctx["system_fuse"]
    pack_config = ctx["pack_config"]
    c_rate = ctx["c_rate"]
    string_current_a = ctx["string_current_a"]
    bus_voltage_text = ctx["bus_voltage_text"]

    container_name = container.get("name", "Container")
    container_company = container.get("manufacturer", "")
    pcs_label = pcs.get("label", pcs.get("model", "PCS"))

    return f"""
<div class="bess-shell">

  <section class="sld-reference">

    <div class="sld-ref-header">
      <div>
        <h2>Single Line Diagram</h2>
        <p>{container_name} {f"({container_company})" if container_company else ""} · {c_rate_key}C · {pcs_label}</p>
      </div>
      <div class="sld-ref-meta">
        <div><b>System:</b> {fmt(calc["container_mwh"], 2)} MWh · {fmt(calc["power_kw"], 0)} kW</div>
        <div><b>DC Bus:</b> {bus_voltage_text} · {fmt(calc["dc_bus_current_a"], 1)} A</div>
      </div>
    </div>

    <div class="sld-main-flow">

      <div class="sld-flow-card cyan">
        <div class="sld-card-title">CELL</div>
        <div class="sld-card-symbol">
          {symbol_html("cell")}
        </div>
        <div class="sld-kv"><span>Capacity</span><b>{fmt(cell.get("capacity_ah", 0), 0)} Ah</b></div>
        <div class="sld-kv"><span>Voltage</span><b>{fmt(cell.get("nominal_voltage_v", 0), 2)} V</b></div>
        <div class="sld-kv"><span>Energy</span><b>{fmt(calc["cell_kwh"], 3)} kWh</b></div>
      </div>

      <div class="sld-arrow">
        <div>→</div>
        <small>x{pack.get("cells_series", 104)}S</small>
      </div>

      <div class="sld-flow-card yellow">
        <div class="sld-card-title">PACK</div>
        <div class="sld-card-symbol">
          {symbol_html("pack")}
        </div>
        <div class="sld-kv"><span>Config</span><b>{pack_config}</b></div>
        <div class="sld-kv"><span>Voltage</span><b>{fmt(calc["pack_v"], 1)} V</b></div>
        <div class="sld-kv"><span>Energy</span><b>{fmt(calc["pack_kwh"], 1)} kWh</b></div>
      </div>

      <div class="sld-arrow">
        <div>→</div>
        <small>x{rack.get("packs_series", 4)} series</small>
      </div>

      <div class="sld-flow-card purple">
        <div class="sld-card-title">RACK / STRING</div>
        <div class="sld-card-symbol">
          {symbol_html("rack")}
        </div>
        <div class="sld-kv"><span>Voltage</span><b>{fmt(calc["rack_v"], 0)} V</b></div>
        <div class="sld-kv"><span>Current</span><b>{fmt(string_current_a, 1)} A</b></div>
        <div class="sld-kv"><span>Energy</span><b>{fmt(calc["rack_kwh"], 0)} kWh</b></div>
      </div>

      <div class="sld-arrow">
        <div>→</div>
        <small>x{container.get("racks_per_container", 0)} parallel</small>
      </div>

      <div class="sld-flow-card yellow">
        <div class="sld-card-title">CONTAINER</div>
        <div class="sld-card-symbol">
          {symbol_html("container")}
        </div>
        <div class="sld-kv"><span>Energy</span><b>{fmt(calc["container_mwh"], 2)} MWh</b></div>
        <div class="sld-kv"><span>Bus V</span><b>{bus_voltage_text}</b></div>
        <div class="sld-kv"><span>Bus I</span><b>{fmt(calc["dc_bus_current_a"], 1)} A</b></div>
      </div>

      <div class="sld-arrow">
        <div>→</div>
        <small>DC</small>
      </div>

      <div class="sld-flow-card pink">
        <div class="sld-card-title">PCS</div>
        <div class="sld-card-symbol">
          {symbol_html("pcs")}
        </div>
        <div class="sld-kv"><span>Rating</span><b>{fmt(pcs.get("rating_kva", 0), 0)} kVA</b></div>
        <div class="sld-kv"><span>AC</span><b>{fmt(pcs.get("ac_voltage_v", 0), 0)} V</b></div>
        <div class="sld-kv"><span>Eff</span><b>{fmt(pcs.get("efficiency_percent", 0), 1)} %</b></div>
      </div>

      <div class="sld-arrow">
        <div>→</div>
        <small>AC</small>
      </div>

      <div class="sld-flow-card cyan">
        <div class="sld-card-title">AC GRID</div>
        <div class="sld-card-symbol">
          {symbol_html("grid")}
        </div>
        <div class="sld-kv"><span>Connection</span><b>3-phase</b></div>
        <div class="sld-kv"><span>Voltage</span><b>{fmt(pcs.get("ac_voltage_v", 0), 0)} V</b></div>
        <div class="sld-kv"><span>Std</span><b>UL 1741</b></div>
      </div>

    </div>

    <div class="sld-connection-block">
      <div class="sld-subhead">
        <h3>Electrical Connection Path</h3>
        <span>Cells → Packs → String/Rack → Rack Combiner → DC Bus → CC Panel → PCS</span>
      </div>

      <div class="sld-connection-grid">

        <div class="sld-conn-card string-card">
          <h4>STRING / RACK</h4>
          <p>{rack.get("packs_series", 4)} packs connected in series per string</p>

          <div class="mini-pack-row">
            <div class="mini-pack"><b>Pack 1</b><span>{fmt(calc["pack_v"], 0)} V</span><em>{fmt(pack.get("capacity_ah", cell.get("capacity_ah", 0)), 0)} Ah</em><small>Fuse: {pack_fuse} A</small></div>
            <div class="mini-pack"><b>Pack 2</b><span>{fmt(calc["pack_v"], 0)} V</span><em>{fmt(pack.get("capacity_ah", cell.get("capacity_ah", 0)), 0)} Ah</em><small>Fuse: {pack_fuse} A</small></div>
            <div class="mini-pack"><b>Pack 3</b><span>{fmt(calc["pack_v"], 0)} V</span><em>{fmt(pack.get("capacity_ah", cell.get("capacity_ah", 0)), 0)} Ah</em><small>Fuse: {pack_fuse} A</small></div>
            <div class="mini-pack"><b>Pack 4</b><span>{fmt(calc["pack_v"], 0)} V</span><em>{fmt(pack.get("capacity_ah", cell.get("capacity_ah", 0)), 0)} Ah</em><small>Fuse: {pack_fuse} A</small></div>
          </div>
        </div>

        <div class="sld-conn-arrow">→</div>

        <div class="sld-conn-card">
          <h4>RACK COMBINER</h4>
          <p>One combiner per rack string</p>
          <div class="sld-small-symbol">
            {symbol_html("combiner")}
          </div>
          <div class="sld-kv"><span>Combiner fuse</span><b>{rack_hvcb} A / 25 kA</b></div>
          <div class="sld-kv"><span>Rack output</span><b>{bus_voltage_text}</b></div>
          <div class="sld-kv"><span>String current</span><b>{fmt(string_current_a, 1)} A</b></div>
        </div>

        <div class="sld-conn-arrow">→</div>

        <div class="sld-conn-card dc-bus-card">
          <h4>DC BUS</h4>
          <p>Container bus</p>
          <div class="sld-small-symbol">
            {symbol_html("dc_bus")}
          </div>
          <div class="sld-kv"><span>Voltage</span><b>{bus_voltage_text}</b></div>
          <div class="sld-kv"><span>Total current</span><b>{fmt(calc["dc_bus_current_a"], 1)} A</b></div>
        </div>

        <div class="sld-conn-arrow">→</div>

        <div class="sld-conn-card">
          <h4>CC PANEL</h4>
          <p>DC collection and protection panel</p>
          <div class="sld-small-symbol">
            {symbol_html("cc_panel")}
          </div>
          <div class="sld-kv"><span>Main fuse</span><b>{system_fuse} A / 25 kA</b></div>
          <div class="sld-kv"><span>Output cable</span><b>600 kcmil x 6 runs</b></div>
        </div>

        <div class="sld-conn-arrow">→</div>

        <div class="sld-conn-card">
          <h4>PCS</h4>
          <p>DC/AC conversion</p>
          <div class="sld-small-symbol">
            {symbol_html("pcs")}
          </div>
          <div class="sld-kv"><span>Rating</span><b>{fmt(pcs.get("rating_kva", 0), 0)} kVA</b></div>
          <div class="sld-kv"><span>AC voltage</span><b>{fmt(pcs.get("ac_voltage_v", 0), 0)} V</b></div>
          <div class="sld-kv"><span>Utilisation</span><b>{fmt(calc["pcs_utilization"], 1)} %</b></div>
        </div>

      </div>

      <div class="sld-architecture-row">
        <div><span>Parallel strings / racks in container</span><b>{container.get("racks_per_container", 0)} racks in parallel</b></div>
        <div><span>Container-to-PCS architecture</span><b>{calc["architecture_text"]}</b></div>
        <div><span>System power at {c_rate_key}C</span><b>{fmt(calc["power_kw"], 0)} kW</b></div>
        <div><span>Discharge duration</span><b>{fmt(calc["duration_h"], 1)} h</b></div>
      </div>
    </div>

    <div class="sld-lower-grid">
      <div class="sld-lower-card">
        <h3>STRING / RACK DETAIL</h3>
        <div class="rack-detail-modules">
          <span></span><span></span><span></span><span></span>
          <b>{rack.get("packs_series", 4)} packs in series<br>{bus_voltage_text} · {fmt(string_current_a, 1)} A</b>
        </div>
        <div class="protection-row">
          <div><span>Fuse</span><b>{rack_hvcb} A</b></div>
          <div><span>Contactor</span><b>HVCB</b></div>
          <div><span>IMD + Pre-charge</span><b>BCMU</b></div>
        </div>
        <p class="note">HVCB = high-voltage control box. Each string isolates independently; rack fuse trips before pack fuse where coordinated.</p>
      </div>

      <div class="sld-lower-card">
        <h3>DC BUS & CONTAINER</h3>
        <div class="bus-gradient"></div>
        <div class="container-mini">
          <div class="container-mini-symbol">
            {symbol_html("container")}
          </div>
          <div>
            <b>{container.get("racks_per_container", 0)} racks in parallel</b>
            <span>Bus V: {calc["dc_window_text"]}</span>
            <span>Bus I: {fmt(calc["dc_bus_current_a"], 1)} A</span>
            <span>Energy: {fmt(calc["container_mwh"], 2)} MWh</span>
          </div>
        </div>
        <div class="power-duration-grid">
          <div><span>Power @ C-rate</span><b>{fmt(calc["power_kw"], 0)} kW</b></div>
          <div><span>Duration</span><b>{fmt(calc["duration_h"], 1)} h</b></div>
        </div>
      </div>

      <div class="sld-lower-card protection-card">
        <h3>PROTECTION COORDINATION <small>- basis NEC 706/240</small></h3>
        <div class="coordination-row">
          <div><span>Pack Fuse</span><b>{pack_fuse} A</b></div>
          <strong>&gt;</strong>
          <div><span>Rack HVCB</span><b>{rack_hvcb} A</b></div>
          <strong>&lt;</strong>
          <div><span>System</span><b>{system_fuse} A</b></div>
        </div>
        <p class="note warning-note">Reverse coordination: rack fuse / HVCB below system fuse so a string fault drops one rack, not the whole container.</p>
        <div class="bmu-row">
          <div><span>BMU</span><b>4 / string</b></div>
          <div><span>BCMU</span><b>1 / string</b></div>
          <div><span>BAMU</span><b>1 / container</b></div>
        </div>
      </div>
    </div>

    <div class="sld-bottom-summary">
      <div><span>System Energy</span><b>{fmt(calc["container_mwh"], 2)} MWh</b></div>
      <div><span>System Power</span><b>{fmt(calc["power_kw"], 0)} kW</b></div>
      <div><span>Bus Voltage</span><b>{bus_voltage_text}</b></div>
      <div><span>Bus Current</span><b>{fmt(calc["dc_bus_current_a"], 1)} A</b></div>
      <div><span>Duration</span><b>{fmt(calc["duration_h"], 1)} h</b></div>
      <div><span>PCS Utilization</span><b>{fmt(calc["pcs_utilization"], 1)} %</b></div>
    </div>

  </section>

</div>
"""


def render_dashboard_html(db: Dict[str, Any], c_rate_key: str) -> str:
    return render_cards_html(db, c_rate_key) + render_sld_html(db, c_rate_key)
