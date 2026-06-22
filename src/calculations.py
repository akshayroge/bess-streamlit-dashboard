from typing import Any, Dict


def selected_objects(db: Dict[str, Any]) -> Dict[str, Any]:
    selected = db["selected_components"]

    return {
        "cell": db["catalog"]["cells"][selected["cell"]],
        "pack": db["catalog"]["packs"][selected["pack"]],
        "rack": db["catalog"]["racks"][selected["rack"]],
        "container": db["catalog"]["containers"][selected["container"]],
        "pcs": db["catalog"]["pcs"][selected["pcs"]],
        "protection": db["catalog"].get("protection_devices", {})
    }


def calculate_dashboard(db: Dict[str, Any], c_rate_key: str) -> Dict[str, Any]:
    objs = selected_objects(db)

    cell = objs["cell"]
    pack = objs["pack"]
    rack = objs["rack"]
    container = objs["container"]
    pcs = objs["pcs"]

    profile = db["profiles"]["c_rate_profiles"][c_rate_key]

    cell_kwh = float(cell.get("energy_kwh", 0))
    if cell_kwh == 0:
        cell_kwh = float(cell["nominal_voltage_v"]) * float(cell["capacity_ah"]) / 1000

    pack_v = float(pack.get("nominal_voltage_v", 0))
    if pack_v == 0:
        pack_v = float(cell["nominal_voltage_v"]) * float(pack["cells_series"])

    pack_kwh = float(pack.get("energy_kwh", 0))
    if pack_kwh == 0:
        pack_kwh = cell_kwh * float(pack["cells_series"]) * float(pack.get("cells_parallel", 1))

    rack_v = float(rack.get("nominal_voltage_v", 0))
    if rack_v == 0:
        rack_v = pack_v * float(rack.get("packs_series", 1))

    rack_kwh = float(rack.get("energy_kwh", 0))
    if rack_kwh == 0:
        rack_kwh = pack_kwh * float(rack.get("packs_series", 1))

    racks_per_container = int(container.get("racks_per_container", 12))

    container_kwh = float(container.get("energy_kwh", 0))
    if container_kwh == 0:
        container_kwh = rack_kwh * racks_per_container

    container_mwh = container_kwh / 1000

    power_kw = float(profile.get("power_kw", 0))
    dc_bus_current_a = float(profile.get("dc_bus_current_a", 0))
    containers_per_pcs = int(profile.get("containers_per_pcs", 1))

    duration_h = container_kwh / power_kw if power_kw > 0 else 0

    pcs_rating_kw = float(pcs.get("rated_power_kw", pcs.get("rating_kva", 0)))
    pcs_total_power_kw = containers_per_pcs * power_kw
    pcs_utilization = pcs_total_power_kw / pcs_rating_kw * 100 if pcs_rating_kw > 0 else 0

    max_racks_per_pcs = containers_per_pcs * racks_per_container

    dc_window_text = (
        f"{int(container['dc_window_min_v'])}-"
        f"{int(container['dc_window_max_v'])} V"
    )

    return {
        "profile": profile,
        "cell_kwh": cell_kwh,
        "pack_v": pack_v,
        "pack_kwh": pack_kwh,
        "rack_v": rack_v,
        "rack_kwh": rack_kwh,
        "container_kwh": container_kwh,
        "container_mwh": container_mwh,
        "power_kw": power_kw,
        "duration_h": duration_h,
        "dc_bus_current_a": dc_bus_current_a,
        "containers_per_pcs": containers_per_pcs,
        "architecture_text": (
            f"{containers_per_pcs} "
            f"{'container' if containers_per_pcs == 1 else 'containers'} "
            f"connected to 1 PCS"
        ),
        "pcs_total_power_kw": pcs_total_power_kw,
        "pcs_utilization": pcs_utilization,
        "max_racks_per_pcs": max_racks_per_pcs,
        "dc_window_text": dc_window_text
    }


def fmt(value: Any, decimals: int = 1) -> str:
    try:
        value = float(value)
    except Exception:
        return str(value)

    if decimals == 0:
        return f"{round(value):,.0f}"

    return f"{value:,.{decimals}f}"