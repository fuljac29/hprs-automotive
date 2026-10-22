import math
import streamlit as st

st.set_page_config(
    page_title="HPRS Automotive — Plasma Carbon-Retention Engine",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Reference constants — V1 uses n-octane as a transparent gasoline surrogate.
C_ATOMIC = 12.011
H_ATOMIC = 1.008
H2_MOLAR = 2.016
OCTANE_C = 8
OCTANE_H = 18
OCTANE_MOLAR_KG = (OCTANE_C * C_ATOMIC + OCTANE_H * H_ATOMIC) / 1000.0

# Ideal non-oxidative decomposition: C8H18 -> 8 C(s) + 9 H2
H2_KG_PER_KG_FUEL_IDEAL = ((OCTANE_H / 2) * H2_MOLAR / 1000.0) / OCTANE_MOLAR_KG
C_KG_PER_KG_FUEL_IDEAL = (OCTANE_C * C_ATOMIC / 1000.0) / OCTANE_MOLAR_KG

# NIST Chemistry WebBook gives ΔfH°(liquid n-octane) near -250 kJ/mol.
# Standard-state products H2(g) and graphite C(s) have ΔfH° = 0.
# The ideal standard-state decomposition floor is therefore ~+250 kJ/mol.
OCTANE_DECOMP_KJ_PER_MOL = 250.0
THERMO_MIN_KWH_PER_KG_H2 = (
    OCTANE_DECOMP_KJ_PER_MOL / 3600.0
) / (((OCTANE_H / 2) * H2_MOLAR) / 1000.0)

H2_LHV_KWH_KG = 33.3  # U.S. DOE
CO2_PER_C = 44.0095 / 12.011
CO2_KG_PER_KG_FUEL_COMPLETE_OX = C_KG_PER_KG_FUEL_IDEAL * CO2_PER_C

st.markdown(
    """
    <style>
    :root{--ink:#0b1724;--muted:#587084;--cyan:#0ea5d8;--green:#49a52e;--orange:#f36b19;--line:#d8e5ee;--soft:#f4f8fb;}
    .block-container{max-width:1500px;padding-top:1.1rem;padding-bottom:2.2rem;}
    h1,h2,h3{color:var(--ink);}
    .horg-kicker{display:inline-block;color:var(--green);font-size:.76rem;font-weight:900;letter-spacing:.13rem;text-transform:uppercase;margin-bottom:.45rem;}
    .horg-hero{padding:1.3rem 1.45rem;border:1px solid var(--line);border-radius:20px;background:linear-gradient(135deg,#fff 0%,#eef9ff 58%,#f4fbef 100%);margin-bottom:1rem;}
    .horg-hero h1{margin:.15rem 0 .6rem;font-size:2.35rem;line-height:1.04;font-weight:900;}
    .horg-hero p{color:var(--muted);font-size:1.03rem;line-height:1.65;margin:0;}
    .horg-chip{display:inline-block;margin:.45rem .35rem 0 0;padding:.32rem .58rem;border-radius:999px;background:#fff;border:1px solid var(--line);font-size:.76rem;font-weight:800;color:var(--ink);}
    .horg-callout{padding:1rem 1.1rem;border-radius:16px;border:1px solid rgba(243,107,25,.25);background:#fff7ed;color:#5c6f7f;line-height:1.6;}
    .horg-eq{padding:1rem 1.15rem;border-radius:16px;background:#06111f;color:#fff;border:1px solid rgba(14,165,216,.3);font-size:1.1rem;font-weight:800;text-align:center;margin:.6rem 0 1rem;}
    .horg-note{padding:.9rem 1rem;border-radius:14px;background:#f7fbfd;border:1px solid var(--line);color:var(--muted);line-height:1.55;font-size:.9rem;}
    div[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);padding:.65rem .8rem;border-radius:14px;}
    div[data-testid="stMetricLabel"]{color:#6b8294;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="horg-hero">
      <span class="horg-kicker">HydrogenOrg · HPRS Automotive V2.2</span>
      <h1>Plasma Carbon-Retention Engine</h1>
      <p>
        Research simulator for an onboard hydrocarbon-to-hydrogen pathway in which a gasoline
        surrogate is decomposed before combustion, hydrogen feeds an H₂-capable internal-combustion
        engine, and carbon is retained as a solid instead of intentionally oxidized to CO₂.
      </p>
      <span class="horg-chip">Research-stage model</span>
      <span class="horg-chip">n-octane surrogate</span>
      <span class="horg-chip">Mass & energy balance</span>
      <span class="horg-chip">Conventional ICE benchmark</span>
      <span class="horg-chip">Pulsed plasma control</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="horg-eq">C₈H₁₈ → 8 C(s) + 9 H₂ &nbsp;&nbsp; | &nbsp;&nbsp; No O₂ is produced by this reaction</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Model assumptions")
    st.caption("Scenario inputs — not validated reactor performance.")

    gross_engine_kw = st.slider(
        "Gross H₂-engine shaft power (kW)", 10, 250, 100, 5,
        help="Mechanical output before subtracting plasma/auxiliary parasitic power.",
    )
    engine_eff = st.slider(
        "H₂ engine brake efficiency (%)", 20, 50, 38, 1
    ) / 100.0

    conventional_eff = st.slider(
        "Conventional gasoline engine efficiency (%)", 20, 45, 30, 1,
        help="Reference brake efficiency for the conventional gasoline benchmark.",
    ) / 100.0

    reactor_conversion = st.slider(
        "Overall fuel conversion after recycle (%)", 60, 100, 92, 1,
        help="Net fraction of fuel converted through the modeled plasma pathway.",
    ) / 100.0

    h2_recovery = st.slider(
        "H₂ recovery to engine (%)", 70, 100, 96, 1
    ) / 100.0

    carbon_capture = st.slider(
        "Solid-carbon collection (%)", 70, 100, 96, 1
    ) / 100.0

    st.divider()
    st.subheader("Plasma mode")

    plasma_mode = st.radio(
        "Electrical model",
        ["Continuous reference", "Pulsed plasma"],
        index=0,
        help=(
            "Continuous mode uses a specific electricity value. Pulsed mode "
            "calculates average electrical power from pulse energy, frequency "
            "and active cells."
        ),
    )

    pulse_energy_mj = None
    pulse_frequency_khz = None
    pulse_width_ns = None
    active_cells = None
    derived_pulse_power_kw = None
    pulse_peak_power_kw_per_cell = None
    pulse_duty_cycle = None

    if plasma_mode == "Continuous reference":
        plasma_sei = st.slider(
            "Plasma electricity (kWh/kg H₂)",
            float(round(THERMO_MIN_KWH_PER_KG_H2, 1)),
            35.0,
            8.0,
            0.1,
            help=(
                "Gross electrical input per kg H₂. Lower bound is the ideal "
                "standard-state n-octane decomposition floor."
            ),
        )
    else:
        st.caption(
            "Exploratory control parameters — not validated automotive reactor specifications."
        )

        pulse_energy_mj = st.number_input(
            "Energy per pulse per cell (mJ)",
            min_value=0.1,
            max_value=500.0,
            value=20.0,
            step=1.0,
            format="%.1f",
        )

        pulse_frequency_khz = st.number_input(
            "Pulse frequency per cell (kHz)",
            min_value=0.1,
            max_value=200.0,
            value=20.0,
            step=1.0,
            format="%.1f",
        )

        pulse_width_ns = st.number_input(
            "Pulse width (ns)",
            min_value=10.0,
            max_value=5000.0,
            value=200.0,
            step=10.0,
            format="%.0f",
            help="Used to estimate instantaneous peak power and duty cycle.",
        )

        active_cells = st.slider(
            "Active plasma cells",
            1, 200, 50, 1,
        )

        # Pavg = Epulse * frequency * active cells
        derived_pulse_power_kw = (
            pulse_energy_mj * 1e-3
            * pulse_frequency_khz * 1e3
            * active_cells
            / 1000.0
        )

        pulse_peak_power_kw_per_cell = (
            (pulse_energy_mj * 1e-3)
            / (pulse_width_ns * 1e-9)
            / 1000.0
        )

        pulse_duty_cycle = (
            pulse_width_ns * 1e-9
            * pulse_frequency_khz * 1e3
            * 100.0
        )

    recovery_offset = st.slider(
        "Validated recovered-energy offset (%)", 0, 80, 20, 1,
        help=(
            "Fraction of gross plasma electrical demand genuinely covered by "
            "recovered energy; not free energy."
        ),
    ) / 100.0

    generator_eff = st.slider(
        "Generator / power-electronics efficiency (%)", 70, 98, 90, 1
    ) / 100.0

    fuel_density = st.number_input(
        "Fuel density (kg/L)", 0.68, 0.82, 0.745, 0.005, format="%.3f"
    )

    gasoline_lhv = st.number_input(
        "Fuel LHV reference (kWh/kg)", 10.0, 14.0, 12.0, 0.1
    )

h2_required_engine_kg_h = gross_engine_kw / (engine_eff * H2_LHV_KWH_KG)
effective_h2_yield = H2_KG_PER_KG_FUEL_IDEAL * reactor_conversion * h2_recovery
fuel_kg_h = h2_required_engine_kg_h / effective_h2_yield if effective_h2_yield > 0 else math.inf
fuel_l_h = fuel_kg_h / fuel_density

h2_gross_kg_h = fuel_kg_h * H2_KG_PER_KG_FUEL_IDEAL * reactor_conversion
h2_to_engine_kg_h = h2_gross_kg_h * h2_recovery

carbon_generated_kg_h = fuel_kg_h * C_KG_PER_KG_FUEL_IDEAL * reactor_conversion
carbon_captured_kg_h = carbon_generated_kg_h * carbon_capture
carbon_uncaptured_kg_h = carbon_generated_kg_h * (1.0 - carbon_capture)

if plasma_mode == "Continuous reference":
    plasma_gross_kw = h2_gross_kg_h * plasma_sei
    effective_plasma_sei = plasma_sei
else:
    plasma_gross_kw = derived_pulse_power_kw
    effective_plasma_sei = (
        plasma_gross_kw / h2_gross_kg_h
        if h2_gross_kg_h > 0
        else math.inf
    )

plasma_external_kw = plasma_gross_kw * (1.0 - recovery_offset)
shaft_draw_for_plasma_kw = (
    plasma_external_kw / generator_eff
    if generator_eff > 0
    else math.inf
)
net_shaft_kw = gross_engine_kw - shaft_draw_for_plasma_kw

thermo_floor_power_kw = h2_gross_kg_h * THERMO_MIN_KWH_PER_KG_H2
thermo_adequacy_ratio = (
    plasma_gross_kw / thermo_floor_power_kw
    if thermo_floor_power_kw > 0
    else math.inf
)
max_h2_at_thermo_floor_kg_h = (
    plasma_gross_kw / THERMO_MIN_KWH_PER_KG_H2
)

h2_chemical_kw = h2_to_engine_kg_h * H2_LHV_KWH_KG
fuel_chemical_kw = fuel_kg_h * gasoline_lhv
hprs_net_eff = (
    net_shaft_kw / fuel_chemical_kw
    if fuel_chemical_kw > 0
    else 0.0
)

co2_retention_equiv_kg_h = carbon_captured_kg_h * CO2_PER_C
uncaptured_c_oxidation_potential_kg_h = carbon_uncaptured_kg_h * CO2_PER_C
ideal_h2_energy_fraction = H2_KG_PER_KG_FUEL_IDEAL * H2_LHV_KWH_KG / gasoline_lhv

# Conventional gasoline benchmark — same nominal shaft output.
conv_same_gross_fuel_kg_h = (
    gross_engine_kw / (conventional_eff * gasoline_lhv)
)
conv_same_gross_fuel_l_h = conv_same_gross_fuel_kg_h / fuel_density
conv_same_gross_co2_kg_h = (
    conv_same_gross_fuel_kg_h * CO2_KG_PER_KG_FUEL_COMPLETE_OX
)

# Same useful net shaft output as HPRS after plasma burden.
same_net_target_kw = max(net_shaft_kw, 0.0)
conv_same_net_fuel_kg_h = (
    same_net_target_kw / (conventional_eff * gasoline_lhv)
    if same_net_target_kw > 0
    else 0.0
)
conv_same_net_fuel_l_h = (
    conv_same_net_fuel_kg_h / fuel_density
    if fuel_density > 0
    else 0.0
)
conv_same_net_co2_kg_h = (
    conv_same_net_fuel_kg_h * CO2_KG_PER_KG_FUEL_COMPLETE_OX
)
fuel_ratio_same_net = (
    fuel_kg_h / conv_same_net_fuel_kg_h
    if conv_same_net_fuel_kg_h > 0
    else math.inf
)

# Performance-target calculator: work backwards from desired net shaft power.
def max_plasma_gross_power_for_target(target_net_kw):
    available_shaft_kw = gross_engine_kw - target_net_kw
    if available_shaft_kw <= 0:
        return 0.0
    if (1.0 - recovery_offset) <= 0:
        return math.inf
    return available_shaft_kw * generator_eff / (1.0 - recovery_offset)

def max_plasma_sei_for_target(target_net_kw):
    allowed_plasma_kw = max_plasma_gross_power_for_target(target_net_kw)
    if h2_gross_kg_h <= 0:
        return math.inf
    return allowed_plasma_kw / h2_gross_kg_h

# Engineering checkpoints requested for comparison.
target_levels_kw = [x for x in (60.0, 80.0, 100.0) if x <= gross_engine_kw]
if float(gross_engine_kw) not in target_levels_kw:
    target_levels_kw.append(float(gross_engine_kw))
target_levels_kw = sorted(set(target_levels_kw))

# Best-case net shaft if plasma operates exactly at the ideal thermodynamic floor.
plasma_floor_kw = h2_gross_kg_h * THERMO_MIN_KWH_PER_KG_H2
plasma_floor_external_kw = plasma_floor_kw * (1.0 - recovery_offset)
plasma_floor_shaft_burden_kw = (
    plasma_floor_external_kw / generator_eff
    if generator_eff > 0
    else math.inf
)
max_net_at_thermo_floor_kw = gross_engine_kw - plasma_floor_shaft_burden_kw

st.subheader("Scenario result")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Fuel to reactor", f"{fuel_kg_h:.1f} kg/h", f"{fuel_l_h:.1f} L/h")
c2.metric("H₂ to engine", f"{h2_to_engine_kg_h:.2f} kg/h")
c3.metric("Solid C captured", f"{carbon_captured_kg_h:.1f} kg/h")
c4.metric("Net shaft after plasma", f"{net_shaft_kw:.1f} kW")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Gross plasma demand", f"{plasma_gross_kw:.1f} kW")
c6.metric("Effective plasma SEI", f"{effective_plasma_sei:.2f} kWh/kg H₂")
c7.metric("CO₂-equivalent carbon retained*", f"{co2_retention_equiv_kg_h:.1f} kg/h")
c8.metric("HPRS net fuel-to-shaft efficiency", f"{100*hprs_net_eff:.1f}%")

st.caption(
    "*CO₂-equivalent carbon retained is the CO₂ mass the captured carbon could form if fully oxidized. "
    "It is not a lifecycle-emissions claim or a measured tailpipe value."
)

if thermo_adequacy_ratio < 1.0:
    st.error(
        "RED — below thermodynamic floor. The selected plasma electrical input "
        "is below the ideal standard-state decomposition floor for the modeled "
        "hydrogen production."
    )
elif net_shaft_kw <= 0:
    st.error(
        "RED — plasma burden exceeds shaft output. The equivalent shaft demand "
        "required to supply the plasma is greater than the gross H₂-engine output."
    )
elif hprs_net_eff >= conventional_eff:
    st.success(
        "GREEN — favourable within selected assumptions. The simplified HPRS "
        "net efficiency reaches or exceeds the selected conventional benchmark. "
        "This is a scenario result, not validated hardware performance."
    )
else:
    st.warning(
        "ORANGE — carbon retention remains interesting, but the simplified net "
        "fuel-to-shaft efficiency is below the selected conventional gasoline benchmark."
    )

st.subheader("Pulsed Plasma Control")

if plasma_mode == "Pulsed plasma":
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Average pulsed electrical power", f"{derived_pulse_power_kw:.2f} kW")
    p2.metric("Peak power per active cell", f"{pulse_peak_power_kw_per_cell:.1f} kW")
    p3.metric("Per-cell electrical duty cycle", f"{pulse_duty_cycle:.3f}%")
    p4.metric("Thermodynamic adequacy", f"{100*thermo_adequacy_ratio:.1f}%")

    st.markdown(
        f"""
        <div class="horg-note">
        <b>Pulse-power equation:</b>
        P<sub>avg</sub> = E<sub>pulse</sub> × f × N<sub>cells</sub>.<br><br>
        {pulse_energy_mj:.1f} mJ/pulse ×
        {pulse_frequency_khz:.1f} kHz ×
        {active_cells} cells =
        <b>{derived_pulse_power_kw:.2f} kW average electrical power</b>.<br>
        At the current modeled H₂ production this corresponds to
        <b>{effective_plasma_sei:.2f} kWh/kg H₂</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if thermo_adequacy_ratio < 1.0:
        st.error(
            f"Even at the ideal thermodynamic floor, these pulse settings could "
            f"support at most about {max_h2_at_thermo_floor_kg_h:.2f} kg H₂/h, "
            f"while the model currently assumes {h2_gross_kg_h:.2f} kg H₂/h gross production."
        )
else:
    st.markdown(
        f"""
        <div class="horg-note">
        Continuous reference mode uses
        <b>{effective_plasma_sei:.2f} kWh/kg H₂</b>.
        Select <b>Pulsed plasma</b> in the sidebar to calculate average power
        from pulse energy, frequency and active cell count.
        </div>
        """,
        unsafe_allow_html=True,
    )

left, right = st.columns([1.05, 0.95])
with left:
    st.subheader("Mass balance")
    st.dataframe(
        {
            "Stream": [
                "Fuel to plasma reactor",
                "Gross H₂ produced",
                "H₂ delivered to engine",
                "Solid carbon generated",
                "Solid carbon captured",
                "Uncaptured solid-carbon fraction",
            ],
            "kg/h": [
                fuel_kg_h,
                h2_gross_kg_h,
                h2_to_engine_kg_h,
                carbon_generated_kg_h,
                carbon_captured_kg_h,
                carbon_uncaptured_kg_h,
            ],
        },
        use_container_width=True,
        hide_index=True,
    )
    st.markdown(
        f"""
        <div class="horg-note">
        <b>Ideal stoichiometry per 1 kg n-octane:</b><br>
        H₂ = {H2_KG_PER_KG_FUEL_IDEAL:.3f} kg · C(s) = {C_KG_PER_KG_FUEL_IDEAL:.3f} kg.<br><br>
        With {reactor_conversion*100:.0f}% overall conversion and {h2_recovery*100:.0f}% H₂ recovery,
        the effective scenario yield is {effective_h2_yield:.3f} kg H₂/kg fuel.
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.subheader("Energy balance")
    st.dataframe(
        {
            "Quantity": [
                "Fuel chemical input (reference LHV)",
                "H₂ chemical energy to engine",
                "Gross H₂-engine shaft output",
                "Gross plasma electricity",
                "Recovered-energy offset",
                "External plasma electricity",
                "Equivalent shaft draw for plasma",
                "Net shaft after plasma burden",
            ],
            "kW": [
                fuel_chemical_kw,
                h2_chemical_kw,
                gross_engine_kw,
                plasma_gross_kw,
                plasma_gross_kw * recovery_offset,
                plasma_external_kw,
                shaft_draw_for_plasma_kw,
                net_shaft_kw,
            ],
        },
        use_container_width=True,
        hide_index=True,
    )
    st.markdown(
        f"""
        <div class="horg-note">
        <b>Thermodynamic floor:</b> ideal standard-state n-octane decomposition requires about
        <b>{THERMO_MIN_KWH_PER_KG_H2:.2f} kWh/kg H₂</b> before real reactor, heat-transfer,
        separation and auxiliary losses.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.subheader("Required Plasma Efficiency to Reach Target Power")
st.caption(
    "Works backwards from desired net shaft power to the maximum plasma burden "
    "the system can tolerate under the selected recovery and generator assumptions."
)

# Show up to three requested engineering target cards.
target_cols = st.columns(min(3, max(1, len(target_levels_kw))))
for idx, target_kw in enumerate(target_levels_kw[:3]):
    allowed_kw = max_plasma_gross_power_for_target(target_kw)
    allowed_sei = max_plasma_sei_for_target(target_kw)
    delta_txt = (
        "above thermodynamic floor"
        if allowed_sei >= THERMO_MIN_KWH_PER_KG_H2
        else "below thermodynamic floor"
    )
    target_cols[idx].metric(
        f"Target {target_kw:.0f} kW net",
        f"{allowed_sei:.2f} kWh/kg H₂",
        delta_txt,
    )

target_table = []
for target_kw in target_levels_kw:
    allowed_kw = max_plasma_gross_power_for_target(target_kw)
    allowed_sei = max_plasma_sei_for_target(target_kw)
    reduction_needed = (
        max(0.0, 1.0 - allowed_sei / effective_plasma_sei) * 100.0
        if effective_plasma_sei > 0 and math.isfinite(allowed_sei)
        else 0.0
    )
    target_table.append({
        "Target net shaft": f"{target_kw:.0f} kW",
        "Max gross plasma power": f"{allowed_kw:.2f} kW",
        "Max plasma SEI": f"{allowed_sei:.2f} kWh/kg H₂",
        "SEI reduction vs current": f"{reduction_needed:.1f}%",
        "Thermodynamic check": (
            "Potentially compatible"
            if allowed_sei >= THERMO_MIN_KWH_PER_KG_H2
            else "Below thermodynamic floor"
        ),
    })

st.dataframe(target_table, use_container_width=True, hide_index=True)

st.markdown(
    f"""
    <div class="horg-note">
    <b>Best-case thermodynamic ceiling for the current operating point:</b><br>
    At the ideal standard-state decomposition floor of
    <b>{THERMO_MIN_KWH_PER_KG_H2:.2f} kWh/kg H₂</b>,
    the plasma would consume about <b>{plasma_floor_kw:.2f} kW</b> gross electricity.
    With the selected recovered-energy offset and generator efficiency,
    a {gross_engine_kw:.0f} kW gross H₂ engine would then leave about
    <b>{max_net_at_thermo_floor_kw:.1f} kW net shaft power</b>.
    This is an ideal thermodynamic ceiling, not a realistic reactor prediction.
    </div>
    """,
    unsafe_allow_html=True,
)

default_target = int(min(80.0, float(gross_engine_kw)))
target_net_kw = st.slider(
    "Custom target net shaft power (kW)",
    min_value=0,
    max_value=int(gross_engine_kw),
    value=default_target,
    step=5,
)

custom_allowed_plasma_kw = max_plasma_gross_power_for_target(target_net_kw)
custom_allowed_sei = max_plasma_sei_for_target(target_net_kw)
custom_reduction_pct = (
    max(0.0, 1.0 - custom_allowed_sei / effective_plasma_sei) * 100.0
    if effective_plasma_sei > 0 and math.isfinite(custom_allowed_sei)
    else 0.0
)

q1, q2, q3, q4 = st.columns(4)
q1.metric("Allowed gross plasma power", f"{custom_allowed_plasma_kw:.2f} kW")
q2.metric("Required max plasma SEI", f"{custom_allowed_sei:.2f} kWh/kg H₂")
q3.metric("SEI reduction vs current", f"{custom_reduction_pct:.1f}%")
q4.metric("Ideal thermodynamic floor", f"{THERMO_MIN_KWH_PER_KG_H2:.2f} kWh/kg H₂")

if custom_allowed_sei >= THERMO_MIN_KWH_PER_KG_H2:
    target_margin = custom_allowed_sei / THERMO_MIN_KWH_PER_KG_H2
    st.success(
        f"The {target_net_kw:.0f} kW net target is not excluded by the model's "
        f"standard-state thermodynamic floor. Plasma electricity would need to be "
        f"no more than {custom_allowed_sei:.2f} kWh/kg H₂ gross, giving a "
        f"{target_margin:.2f}× margin over the ideal floor."
    )
else:
    st.error(
        f"The {target_net_kw:.0f} kW net target would require only "
        f"{custom_allowed_sei:.2f} kWh/kg H₂, below the ideal standard-state "
        f"floor of {THERMO_MIN_KWH_PER_KG_H2:.2f} kWh/kg H₂. With the current "
        f"gross engine power and selected recovery assumptions, this target is "
        f"not reachable in the simplified model."
    )

if plasma_mode == "Pulsed plasma":
    per_cell_avg_kw = (
        pulse_energy_mj * 1e-3
        * pulse_frequency_khz * 1e3
        / 1000.0
    )
    max_cells_for_target = (
        math.floor(custom_allowed_plasma_kw / per_cell_avg_kw)
        if per_cell_avg_kw > 0 and math.isfinite(custom_allowed_plasma_kw)
        else 0
    )
    required_pulse_energy_mj_at_current_cells = (
        custom_allowed_plasma_kw * 1000.0
        / (pulse_frequency_khz * 1e3 * active_cells)
        * 1000.0
        if pulse_frequency_khz > 0 and active_cells > 0
        else math.inf
    )
    st.markdown(
        f"""
        <div class="horg-note">
        <b>Pulsed-plasma translation for the selected target:</b><br>
        At the current pulse energy and frequency, one active cell averages
        <b>{per_cell_avg_kw:.4f} kW</b> electrical power.
        To remain below the {target_net_kw:.0f} kW net-power ceiling, the purely
        electrical model allows approximately <b>{max_cells_for_target} active cells</b>.<br><br>
        Alternatively, keeping {active_cells} cells and {pulse_frequency_khz:.1f} kHz,
        the average pulse energy would need to be no more than about
        <b>{required_pulse_energy_mj_at_current_cells:.2f} mJ per pulse per cell</b>.<br><br>
        These are electrical ceilings only. They do not establish reactor throughput,
        conversion, hydrogen yield or carbon-removal performance.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# WHAT MUST CHANGE TO REACH THE SELECTED TARGET?
# ============================================================

st.subheader("What must change to reach the selected target?")

st.caption(
    "Design diagnosis: each lever is varied one at a time while the other current "
    "assumptions are held fixed. These are model requirements, not validated hardware predictions."
)

def net_fraction_for_specific_plasma_energy(
    sei_kwh_per_kg_h2,
    engine_efficiency,
    recovery_fraction,
):
    """
    Fraction of gross H2-engine shaft power left after the modeled plasma
    electrical burden, assuming plasma specific electricity scales with H2 flow.
    """
    if (
        engine_efficiency <= 0
        or h2_recovery <= 0
        or generator_eff <= 0
    ):
        return -math.inf

    plasma_burden_fraction = (
        sei_kwh_per_kg_h2
        * (1.0 - recovery_fraction)
        / (
            generator_eff
            * engine_efficiency
            * H2_LHV_KWH_KG
            * h2_recovery
        )
    )
    return 1.0 - plasma_burden_fraction


# 1) Gross engine power required if current plasma specific electricity is kept.
current_specific_net_fraction = net_fraction_for_specific_plasma_energy(
    effective_plasma_sei,
    engine_eff,
    recovery_offset,
)

required_gross_engine_current_sei_kw = (
    target_net_kw / current_specific_net_fraction
    if target_net_kw > 0 and current_specific_net_fraction > 0
    else (0.0 if target_net_kw == 0 else math.inf)
)

# 2) Gross engine power required in the ideal thermodynamic-floor case.
floor_specific_net_fraction = net_fraction_for_specific_plasma_energy(
    THERMO_MIN_KWH_PER_KG_H2,
    engine_eff,
    recovery_offset,
)

required_gross_engine_floor_kw = (
    target_net_kw / floor_specific_net_fraction
    if target_net_kw > 0 and floor_specific_net_fraction > 0
    else (0.0 if target_net_kw == 0 else math.inf)
)

# 3) H2 engine efficiency required at current gross engine power and current plasma SEI.
if target_net_kw < gross_engine_kw:
    required_engine_eff = (
        gross_engine_kw
        * effective_plasma_sei
        * (1.0 - recovery_offset)
        / (
            (gross_engine_kw - target_net_kw)
            * H2_LHV_KWH_KG
            * h2_recovery
            * generator_eff
        )
    )
elif (
    target_net_kw == gross_engine_kw
    and effective_plasma_sei == 0
):
    required_engine_eff = engine_eff
else:
    required_engine_eff = math.inf

# Same calculation if the plasma could reach the ideal thermodynamic floor.
if target_net_kw < gross_engine_kw:
    required_engine_eff_at_floor = (
        gross_engine_kw
        * THERMO_MIN_KWH_PER_KG_H2
        * (1.0 - recovery_offset)
        / (
            (gross_engine_kw - target_net_kw)
            * H2_LHV_KWH_KG
            * h2_recovery
            * generator_eff
        )
    )
else:
    required_engine_eff_at_floor = math.inf

# 4) Recovered-energy offset required at current gross engine power and current plasma SEI.
current_plasma_power_at_specific_sei_kw = (
    gross_engine_kw
    * effective_plasma_sei
    / (
        engine_eff
        * H2_LHV_KWH_KG
        * h2_recovery
    )
    if engine_eff > 0 and h2_recovery > 0
    else math.inf
)

if target_net_kw <= gross_engine_kw and current_plasma_power_at_specific_sei_kw > 0:
    required_recovery_offset = (
        1.0
        - (
            (gross_engine_kw - target_net_kw)
            * generator_eff
            / current_plasma_power_at_specific_sei_kw
        )
    )
    required_recovery_offset = max(0.0, required_recovery_offset)
else:
    required_recovery_offset = math.inf

# Same recovered-energy calculation at the thermodynamic-floor plasma input.
floor_plasma_power_at_current_gross_kw = (
    gross_engine_kw
    * THERMO_MIN_KWH_PER_KG_H2
    / (
        engine_eff
        * H2_LHV_KWH_KG
        * h2_recovery
    )
    if engine_eff > 0 and h2_recovery > 0
    else math.inf
)

if target_net_kw <= gross_engine_kw and floor_plasma_power_at_current_gross_kw > 0:
    required_recovery_offset_at_floor = (
        1.0
        - (
            (gross_engine_kw - target_net_kw)
            * generator_eff
            / floor_plasma_power_at_current_gross_kw
        )
    )
    required_recovery_offset_at_floor = max(
        0.0,
        required_recovery_offset_at_floor,
    )
else:
    required_recovery_offset_at_floor = math.inf


def fmt_requirement(value, unit="", digits=1):
    if not math.isfinite(value):
        return "Not finite"
    return f"{value:.{digits}f}{unit}"


d1, d2, d3, d4 = st.columns(4)

d1.metric(
    "Gross H₂ engine needed @ current SEI",
    (
        f"{required_gross_engine_current_sei_kw:.1f} kW"
        if math.isfinite(required_gross_engine_current_sei_kw)
        else "Not reachable"
    ),
)

d2.metric(
    "Gross H₂ engine needed @ thermo floor",
    (
        f"{required_gross_engine_floor_kw:.1f} kW"
        if math.isfinite(required_gross_engine_floor_kw)
        else "Not reachable"
    ),
)

d3.metric(
    "H₂ engine efficiency needed @ current SEI",
    (
        f"{100*required_engine_eff:.1f}%"
        if math.isfinite(required_engine_eff)
        else "Not reachable"
    ),
)

d4.metric(
    "Recovered-energy offset needed @ current SEI",
    (
        f"{100*required_recovery_offset:.1f}%"
        if math.isfinite(required_recovery_offset)
        else "Not reachable"
    ),
)

diagnosis_rows = []

# Plasma-SEI lever
if custom_allowed_sei < THERMO_MIN_KWH_PER_KG_H2:
    sei_status = "Not physically reachable by SEI reduction alone"
else:
    sei_status = "Not excluded by thermodynamic floor"

diagnosis_rows.append(
    {
        "Design lever": "Plasma specific electricity",
        "Current": f"{effective_plasma_sei:.2f} kWh/kg H₂",
        "Required for target": f"≤ {custom_allowed_sei:.2f} kWh/kg H₂",
        "Model diagnosis": sei_status,
    }
)

# Gross-engine lever, using current SEI
if not math.isfinite(required_gross_engine_current_sei_kw):
    gross_status = "Not reachable at current specific plasma burden"
elif required_gross_engine_current_sei_kw <= 250:
    gross_status = "Within current simulator power range; throughput must scale too"
else:
    gross_status = "Above current simulator power range"

diagnosis_rows.append(
    {
        "Design lever": "Gross H₂-engine shaft power",
        "Current": f"{gross_engine_kw:.0f} kW",
        "Required for target": (
            f"≥ {required_gross_engine_current_sei_kw:.1f} kW"
            if math.isfinite(required_gross_engine_current_sei_kw)
            else "Not finite"
        ),
        "Model diagnosis": gross_status,
    }
)

# Engine-efficiency lever
if not math.isfinite(required_engine_eff):
    engine_eff_status = "Not reachable at current gross power"
elif required_engine_eff > 1.0:
    engine_eff_status = "Physically impossible (>100%)"
elif required_engine_eff > 0.50:
    engine_eff_status = "Above current simulator efficiency range"
else:
    engine_eff_status = "Within current simulator efficiency range"

diagnosis_rows.append(
    {
        "Design lever": "H₂ engine brake efficiency",
        "Current": f"{100*engine_eff:.1f}%",
        "Required for target": (
            f"≥ {100*required_engine_eff:.1f}%"
            if math.isfinite(required_engine_eff)
            else "Not finite"
        ),
        "Model diagnosis": engine_eff_status,
    }
)

# Recovery-offset lever
if not math.isfinite(required_recovery_offset):
    recovery_status = "Not reachable"
elif required_recovery_offset > 1.0:
    recovery_status = "Physically impossible (>100%)"
elif required_recovery_offset > 0.80:
    recovery_status = "Above current simulator recovery range"
else:
    recovery_status = "Within model range; requires experimental validation"

diagnosis_rows.append(
    {
        "Design lever": "Recovered-energy offset",
        "Current": f"{100*recovery_offset:.1f}%",
        "Required for target": (
            f"≥ {100*required_recovery_offset:.1f}%"
            if math.isfinite(required_recovery_offset)
            else "Not finite"
        ),
        "Model diagnosis": recovery_status,
    }
)

st.dataframe(
    diagnosis_rows,
    use_container_width=True,
    hide_index=True,
)

# A concise engineering interpretation.
if custom_allowed_sei < THERMO_MIN_KWH_PER_KG_H2:
    st.warning(
        f"Plasma efficiency alone cannot deliver {target_net_kw:.0f} kW net at "
        f"{gross_engine_kw:.0f} kW gross: the required "
        f"{custom_allowed_sei:.2f} kWh/kg H₂ is below the ideal floor of "
        f"{THERMO_MIN_KWH_PER_KG_H2:.2f} kWh/kg H₂."
    )
else:
    st.success(
        f"At {gross_engine_kw:.0f} kW gross, the {target_net_kw:.0f} kW target "
        f"is not excluded by the thermodynamic floor if plasma electricity can "
        f"be reduced to ≤ {custom_allowed_sei:.2f} kWh/kg H₂."
    )

st.markdown(
    f"""
    <div class="horg-note">
    <b>Alternative paths for the selected {target_net_kw:.0f} kW target:</b><br><br>

    • Keeping the current plasma specific electricity of
    <b>{effective_plasma_sei:.2f} kWh/kg H₂</b>, the simplified model requires
    approximately <b>{fmt_requirement(required_gross_engine_current_sei_kw, " kW", 1)}</b>
    gross H₂-engine shaft power.<br>

    • If the plasma could approach the ideal thermodynamic floor, the required
    gross H₂-engine power falls to approximately
    <b>{fmt_requirement(required_gross_engine_floor_kw, " kW", 1)}</b>.<br>

    • Holding gross engine power and plasma SEI fixed, the required H₂-engine
    brake efficiency is
    <b>{fmt_requirement(100*required_engine_eff, "%", 1)}</b>.<br>

    • Holding gross engine power, engine efficiency and plasma SEI fixed, the
    required recovered-energy offset is
    <b>{fmt_requirement(100*required_recovery_offset, "%", 1)}</b>.<br><br>

    Each line varies one lever independently. Combining moderate improvements
    across several levers can be more realistic than forcing any single
    parameter to an extreme value.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Ideal-floor cross-check for the selected target"):
    st.markdown(
        f"""
        If the plasma specific electricity were exactly the ideal
        **{THERMO_MIN_KWH_PER_KG_H2:.2f} kWh/kg H₂** floor:

        - gross H₂-engine power needed: **{
            required_gross_engine_floor_kw:.1f
            if math.isfinite(required_gross_engine_floor_kw)
            else float("nan")
        } kW**
        - H₂-engine efficiency needed at the current gross power:
          **{
            100*required_engine_eff_at_floor:.1f
            if math.isfinite(required_engine_eff_at_floor)
            else float("nan")
        }%**
        - recovered-energy offset needed at the current gross power:
          **{
            100*required_recovery_offset_at_floor:.1f
            if math.isfinite(required_recovery_offset_at_floor)
            else float("nan")
        }%**

        These are idealized model boundaries, not predictions of achievable
        reactor, engine or heat-recovery hardware.
        """
    )

st.subheader("Conventional Engine Benchmark")
st.caption("Same fuel reference. Same engine-scale comparison. Different carbon pathway.")

b1, b2, b3, b4 = st.columns(4)
b1.metric("Conventional efficiency", f"{100*conventional_eff:.0f}%")
b2.metric(
    "Gasoline for same gross shaft",
    f"{conv_same_gross_fuel_kg_h:.1f} kg/h",
    f"{conv_same_gross_fuel_l_h:.1f} L/h",
)
b3.metric(
    "Theoretical CO₂ at same gross shaft",
    f"{conv_same_gross_co2_kg_h:.1f} kg/h",
)
b4.metric(
    "HPRS / conventional net efficiency",
    f"{(hprs_net_eff/conventional_eff):.2f}×",
)

st.dataframe(
    {
        "Metric": [
            "Power basis",
            "Fuel flow",
            "Fuel volume",
            "Reference fuel-to-shaft efficiency",
            "Direct complete-oxidation CO₂",
            "Captured solid carbon",
            "Plasma equivalent shaft burden",
        ],
        "Conventional gasoline ICE": [
            f"{gross_engine_kw:.1f} kW gross shaft",
            f"{conv_same_gross_fuel_kg_h:.2f} kg/h",
            f"{conv_same_gross_fuel_l_h:.2f} L/h",
            f"{100*conventional_eff:.1f}%",
            f"{conv_same_gross_co2_kg_h:.2f} kg/h",
            "0 kg/h",
            "0 kW",
        ],
        "HPRS Automotive": [
            f"{net_shaft_kw:.1f} kW net after plasma",
            f"{fuel_kg_h:.2f} kg/h",
            f"{fuel_l_h:.2f} L/h",
            f"{100*hprs_net_eff:.1f}%",
            "Not calculated as tailpipe CO₂",
            f"{carbon_captured_kg_h:.2f} kg/h",
            f"{shaft_draw_for_plasma_kw:.2f} kW",
        ],
    },
    use_container_width=True,
    hide_index=True,
)

st.markdown(
    f"""
    <div class="horg-note">
    <b>Same-net-power comparison:</b><br>
    HPRS currently leaves <b>{same_net_target_kw:.1f} kW</b> net shaft power.
    A conventional gasoline engine at {100*conventional_eff:.0f}% brake efficiency
    would require about <b>{conv_same_net_fuel_kg_h:.2f} kg/h</b>
    ({conv_same_net_fuel_l_h:.2f} L/h) to deliver the same useful shaft output,
    corresponding to about <b>{conv_same_net_co2_kg_h:.2f} kg/h</b>
    theoretical complete-oxidation CO₂ for the n-octane surrogate.<br><br>
    Under the selected assumptions HPRS uses
    <b>{fuel_ratio_same_net:.2f}×</b> the fuel mass of that same-net-power
    conventional benchmark.
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Carbon-retention interpretation")
r1, r2, r3 = st.columns(3)
r1.metric("Carbon collection", f"{carbon_capture*100:.0f}%")
r2.metric("Captured carbon", f"{carbon_captured_kg_h:.1f} kg/h")
r3.metric("Uncaptured-C oxidation potential", f"{uncaptured_c_oxidation_potential_kg_h:.1f} kg CO₂/h")

st.markdown(
    """
    <div class="horg-callout">
    <b>Scientific boundary:</b> this model does not calculate NOₓ, transient reactor behavior,
    catalyst/electrode life, carbon morphology, soot filtration, startup energy, safety systems,
    fuel impurities, compressor demand, hydrogen-purity specifications, thermal-management hardware,
    lifecycle emissions or regulatory compliance. Hydrogen combustion with air can still form NOₓ.
    A real claim of “non-polluting” operation therefore requires measured emissions and independent validation.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Model basis and references"):
    st.markdown(
        f"""
        **Stoichiometric model**  
        `C8H18 → 8 C(s) + 9 H2`

        Ideal n-octane surrogate yield: **{H2_KG_PER_KG_FUEL_IDEAL:.3f} kg H₂** and
        **{C_KG_PER_KG_FUEL_IDEAL:.3f} kg solid carbon** per kg fuel.

        **Reference constants**
        - NIST Chemistry WebBook, n-octane: standard liquid enthalpy of formation ≈ **−250 kJ/mol**.
          This gives a standard-state decomposition floor of ≈ **{THERMO_MIN_KWH_PER_KG_H2:.2f} kWh/kg H₂**.
        - U.S. Department of Energy: hydrogen LHV = **33.3 kWh/kg H₂**.

        **Design-target diagnosis**

        The V2.2 design diagnosis varies one lever at a time and solves the
        simplified balance backwards for the selected net-power target.
        It can estimate the required gross engine power, H₂-engine efficiency,
        recovered-energy offset, or plasma specific electricity. A value being
        mathematically reachable in the model is not evidence that the required
        hardware performance is experimentally achievable.

        **Pulsed-plasma interpretation**  
`P_avg = energy_per_pulse × pulse_frequency × active_cells`  
Pulse width is used to estimate instantaneous peak power and electrical duty cycle. These values are research controls, not validated automotive reactor specifications.

**Boundary:** gasoline is a mixture. n-octane is only a transparent first surrogate;
        real fuel requires species-resolved chemistry and laboratory data.
        """
    )

st.caption("HPRS Automotive V2.2 · HydrogenOrg research model · Simulation → laboratory validation → proof of concept")
