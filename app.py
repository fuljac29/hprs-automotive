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

# Steam-assisted n-octane reference pathways.
# A) Steam reforming to syngas:
# C8H18 + 8 H2O -> 8 CO + 17 H2
H2_KG_PER_KG_FUEL_STEAM_SYNGAS = (
    17.0 * H2_MOLAR / 1000.0
) / OCTANE_MOLAR_KG
WATER_KG_PER_KG_FUEL_STEAM_SYNGAS = (
    8.0 * 18.01528 / 1000.0
) / OCTANE_MOLAR_KG

# B) Steam reforming + complete water-gas shift:
# C8H18 + 16 H2O -> 8 CO2 + 25 H2
H2_KG_PER_KG_FUEL_STEAM_WGS = (
    25.0 * H2_MOLAR / 1000.0
) / OCTANE_MOLAR_KG
WATER_KG_PER_KG_FUEL_STEAM_WGS = (
    16.0 * 18.01528 / 1000.0
) / OCTANE_MOLAR_KG
CO2_KG_PER_KG_FUEL_STEAM_WGS = CO2_KG_PER_KG_FUEL_COMPLETE_OX

# Approximate standard-state reaction-enthalpy references for gaseous reactants.
# Steam reforming: ~1310 kJ/mol n-octane.
# Complete WGS adds ~8*(-41) kJ/mol, giving ~982 kJ/mol net.
STEAM_SYNGAS_REACTION_KJ_PER_MOL = 1310.0
STEAM_WGS_REACTION_KJ_PER_MOL = 982.0

STEAM_SYNGAS_REACTION_KWH_PER_KG_H2 = (
    STEAM_SYNGAS_REACTION_KJ_PER_MOL / 3600.0 / OCTANE_MOLAR_KG
) / H2_KG_PER_KG_FUEL_STEAM_SYNGAS

STEAM_WGS_REACTION_KWH_PER_KG_H2 = (
    STEAM_WGS_REACTION_KJ_PER_MOL / 3600.0 / OCTANE_MOLAR_KG
) / H2_KG_PER_KG_FUEL_STEAM_WGS

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
      <span class="horg-kicker">HydrogenOrg · HPRS Automotive V2.6</span>
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
      <span class="horg-chip">Same-net-power normalization</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="horg-eq">C₈H₁₈ → 8 C(s) + 9 H₂ &nbsp;&nbsp; | &nbsp;&nbsp; No O₂ is produced by this reaction</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="horg-path-grid">

      <div class="horg-path-card">
        <h4>1 · Conventional gasoline engine</h4>
        <p>
          Gasoline is combusted directly in the ICE.
          <strong>Reference benchmark</strong> for fuel use, shaft efficiency
          and theoretical CO₂.
        </p>
      </div>

      <div class="horg-path-card">
        <h4>2 · Dry HPRS carbon-retention</h4>
        <p>
          C₈H₁₈ → 8 C(s) + 9 H₂.
          Hydrogen feeds the engine while the model attempts to
          <strong>retain carbon as a solid</strong>.
        </p>
      </div>

      <div class="horg-path-card">
        <h4>3 · Gasoline + water / steam</h4>
        <p>
          Separate gasoline and water feeds are vaporized before the reactor.
          The model compares <strong>steam reforming / WGS</strong>,
          hydrogen yield, water demand, CO/CO₂ and operating cost.
        </p>
      </div>

    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "Three hypotheses are compared in V2.5.2: conventional gasoline, dry HPRS "
    "carbon-retention, and gasoline + water/steam. Water and gasoline are modeled "
    "as separate feeds, not as a stable liquid blend in one tank."
)

with st.sidebar:
    st.header("Model assumptions")
    st.caption("Scenario inputs — not validated reactor performance.")

    comparison_focus = st.radio(
        "Comparison focus",
        [
            "Show all three pathways",
            "Conventional gasoline",
            "Dry HPRS carbon-retention",
            "Gasoline + water / steam",
        ],
        index=0,
        help=(
            "This selector is for presentation focus. Core calculations remain "
            "available so the three pathways can still be compared."
        ),
    )


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

    st.divider()
    st.subheader("Scientific normalization")

    normalized_target_kw = st.slider(
        "Same net shaft power for comparison (kW)",
        min_value=10,
        max_value=150,
        value=50,
        step=5,
        help=(
            "All three pathways are rescaled to deliver this same net mechanical "
            "shaft power. This is the primary apples-to-apples comparison in V2.6."
        ),
    )

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

        st.markdown("#### Pulse frequency control")

        pulse_frequency_khz = st.slider(
            "Pulse frequency (kHz)",
            min_value=0.5,
            max_value=100.0,
            value=20.0,
            step=0.5,
            help=(
                "Electrical pulse repetition frequency for each active plasma cell. "
                "Average plasma power increases linearly with frequency when pulse "
                "energy and active-cell count are unchanged."
            ),
        )

        st.caption(
            f"Current pulse frequency: **{pulse_frequency_khz:.1f} kHz** "
            f"({pulse_frequency_khz*1000:.0f} pulses/s per active cell)"
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

    st.divider()
    st.subheader("Steam-assisted comparison")

    steam_route = st.radio(
        "Gasoline + steam pathway",
        [
            "Steam reforming + WGS",
            "Steam reforming to syngas",
        ],
        index=0,
        help=(
            "The WGS route maximizes H2 but converts the fuel carbon to CO2. "
            "The syngas route produces H2 + CO. Neither route is the same as "
            "the dry carbon-retention pathway."
        ),
    )

    steam_reaction_floor_input = (
        STEAM_WGS_REACTION_KWH_PER_KG_H2
        if steam_route == "Steam reforming + WGS"
        else STEAM_SYNGAS_REACTION_KWH_PER_KG_H2
    )

    steam_thermal_energy = st.number_input(
        "Steam-route thermal demand (kWh_th/kg H₂)",
        min_value=float(round(steam_reaction_floor_input, 2)),
        max_value=40.0,
        value=float(max(8.0, math.ceil(steam_reaction_floor_input * 2.0) / 2.0)),
        step=0.5,
        key=f"steam_thermal_{steam_route}",
        help=(
            "Gross thermal process demand. The lower limit is the approximate "
            "standard-state reaction-enthalpy reference for the selected idealized route."
        ),
    )

    steam_electrical_aux = st.number_input(
        "Steam-route electrical auxiliaries (kWh_e/kg H₂)",
        min_value=0.0,
        max_value=15.0,
        value=1.5,
        step=0.1,
        help=(
            "Exploratory electrical demand for pumps, controls, separation, compression "
            "and any electrically driven reactor auxiliaries."
        ),
    )

    steam_heat_recovery = st.slider(
        "Steam-route thermal recovery (%)",
        min_value=0,
        max_value=90,
        value=50,
        step=5,
        help=(
            "Fraction of gross thermal process demand supplied by recovered heat. "
            "This reduces external thermal demand, not the electrical auxiliary load."
        ),
    ) / 100.0

    water_recycle = st.slider(
        "Water recycle (%)",
        min_value=0,
        max_value=95,
        value=0,
        step=5,
        help="Fraction of gross steam/water feed recovered and reused.",
    ) / 100.0

    st.divider()
    st.subheader("Operating-cost inputs")

    gasoline_price_chf_l = st.number_input(
        "Gasoline price (CHF/L)",
        min_value=0.0,
        max_value=5.0,
        value=2.16,
        step=0.05,
        help="Editable cost assumption. Default is an illustrative Swiss 95-octane reference.",
    )

    electricity_price_chf_kwh = st.number_input(
        "Electricity price (CHF/kWh)",
        min_value=0.0,
        max_value=1.5,
        value=0.277,
        step=0.01,
        format="%.3f",
        help="Editable cost assumption for externally supplied process electricity.",
    )

    thermal_energy_price_chf_kwh = st.number_input(
        "Supplemental thermal-energy price (CHF/kWh_th)",
        min_value=0.0,
        max_value=1.5,
        value=0.0,
        step=0.01,
        format="%.3f",
        help=(
            "Optional marginal price for unrecovered steam-route process heat. "
            "Leave at 0 if you want to report the heat requirement without assigning a cost."
        ),
    )

    water_price_chf_m3 = st.number_input(
        "Water price (CHF/m³)",
        min_value=0.0,
        max_value=20.0,
        value=2.0,
        step=0.5,
        help="Editable water-cost assumption.",
    )

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

# ============================================================
# STEAM-ASSISTED GASOLINE + WATER COMPARISON
# ============================================================

if steam_route == "Steam reforming + WGS":
    steam_h2_yield_kg_per_kg_fuel = H2_KG_PER_KG_FUEL_STEAM_WGS
    steam_water_kg_per_kg_fuel = WATER_KG_PER_KG_FUEL_STEAM_WGS
    steam_reaction_floor_kwh_per_kg_h2 = STEAM_WGS_REACTION_KWH_PER_KG_H2
    steam_carbon_product = "CO2"
else:
    steam_h2_yield_kg_per_kg_fuel = H2_KG_PER_KG_FUEL_STEAM_SYNGAS
    steam_water_kg_per_kg_fuel = WATER_KG_PER_KG_FUEL_STEAM_SYNGAS
    steam_reaction_floor_kwh_per_kg_h2 = STEAM_SYNGAS_REACTION_KWH_PER_KG_H2
    steam_carbon_product = "CO"

steam_effective_h2_yield = (
    steam_h2_yield_kg_per_kg_fuel
    * reactor_conversion
    * h2_recovery
)

steam_fuel_kg_h = (
    h2_required_engine_kg_h / steam_effective_h2_yield
    if steam_effective_h2_yield > 0
    else math.inf
)

steam_fuel_l_h = (
    steam_fuel_kg_h / fuel_density
    if fuel_density > 0
    else math.inf
)

steam_h2_gross_kg_h = (
    steam_fuel_kg_h
    * steam_h2_yield_kg_per_kg_fuel
    * reactor_conversion
)

steam_h2_to_engine_kg_h = steam_h2_gross_kg_h * h2_recovery

steam_water_gross_kg_h = (
    steam_fuel_kg_h
    * steam_water_kg_per_kg_fuel
)

steam_water_makeup_kg_h = (
    steam_water_gross_kg_h
    * (1.0 - water_recycle)
)

# First-order density assumption for make-up water: 1 kg ~ 1 L.
steam_water_makeup_l_h = steam_water_makeup_kg_h

# V2.6 separates thermal and electrical process energy.
steam_thermal_gross_kw = (
    steam_h2_gross_kg_h
    * steam_thermal_energy
)

steam_thermal_external_kw = (
    steam_thermal_gross_kw
    * (1.0 - steam_heat_recovery)
)

steam_electrical_aux_kw = (
    steam_h2_gross_kg_h
    * steam_electrical_aux
)

steam_electrical_shaft_burden_kw = (
    steam_electrical_aux_kw / generator_eff
    if generator_eff > 0
    else math.inf
)

# Recovered/external process heat is reported separately and is not silently
# converted into shaft burden. Only electrical auxiliaries reduce shaft output.
steam_net_shaft_kw = gross_engine_kw - steam_electrical_shaft_burden_kw

steam_fuel_chemical_kw = steam_fuel_kg_h * gasoline_lhv

steam_net_eff = (
    steam_net_shaft_kw / steam_fuel_chemical_kw
    if steam_fuel_chemical_kw > 0
    else 0.0
)

if steam_route == "Steam reforming + WGS":
    steam_co2_kg_h = (
        steam_fuel_kg_h
        * CO2_KG_PER_KG_FUEL_STEAM_WGS
        * reactor_conversion
    )
    steam_co_kg_h = 0.0
else:
    CO_MOLAR = 28.0101
    steam_co_kg_per_kg_fuel = (
        (8.0 * CO_MOLAR / 1000.0)
        / OCTANE_MOLAR_KG
    )
    steam_co_kg_h = (
        steam_fuel_kg_h
        * steam_co_kg_per_kg_fuel
        * reactor_conversion
    )
    steam_co2_kg_h = 0.0

# Operating-cost views.
conventional_fuel_cost_chf_h = (
    conv_same_gross_fuel_l_h
    * gasoline_price_chf_l
)

dry_hprs_fuel_cost_chf_h = (
    fuel_l_h
    * gasoline_price_chf_l
)

dry_hprs_external_energy_cost_chf_h = (
    plasma_external_kw
    * electricity_price_chf_kwh
)

dry_hprs_cost_external_power_chf_h = (
    dry_hprs_fuel_cost_chf_h
    + dry_hprs_external_energy_cost_chf_h
)

steam_fuel_cost_chf_h = (
    steam_fuel_l_h
    * gasoline_price_chf_l
)

steam_water_cost_chf_h = (
    (steam_water_makeup_l_h / 1000.0)
    * water_price_chf_m3
)

steam_electrical_cost_chf_h = (
    steam_electrical_aux_kw
    * electricity_price_chf_kwh
)

steam_thermal_cost_chf_h = (
    steam_thermal_external_kw
    * thermal_energy_price_chf_kwh
)

steam_cost_external_power_chf_h = (
    steam_fuel_cost_chf_h
    + steam_water_cost_chf_h
    + steam_electrical_cost_chf_h
    + steam_thermal_cost_chf_h
)

conventional_cost_per_kwh_shaft = (
    conventional_fuel_cost_chf_h / gross_engine_kw
    if gross_engine_kw > 0
    else math.inf
)

dry_hprs_fuel_cost_per_net_kwh = (
    dry_hprs_fuel_cost_chf_h / net_shaft_kw
    if net_shaft_kw > 0
    else math.inf
)

dry_hprs_external_cost_per_net_kwh = (
    dry_hprs_cost_external_power_chf_h / net_shaft_kw
    if net_shaft_kw > 0
    else math.inf
)

steam_fuel_water_cost_per_net_kwh = (
    (steam_fuel_cost_chf_h + steam_water_cost_chf_h)
    / steam_net_shaft_kw
    if steam_net_shaft_kw > 0
    else math.inf
)

steam_external_cost_per_net_kwh = (
    steam_cost_external_power_chf_h
    / steam_net_shaft_kw
    if steam_net_shaft_kw > 0
    else math.inf
)

# ============================================================
# V2.6 SAME-NET-POWER NORMALIZATION
# ============================================================

comparison_net_kw = float(normalized_target_kw)

# Conventional gasoline: no modeled process parasitic load.
norm_conv_fuel_kg_h = comparison_net_kw / (conventional_eff * gasoline_lhv)
norm_conv_fuel_l_h = norm_conv_fuel_kg_h / fuel_density
norm_conv_co2_kg_h = norm_conv_fuel_kg_h * CO2_KG_PER_KG_FUEL_COMPLETE_OX
norm_conv_cost_chf_h = norm_conv_fuel_l_h * gasoline_price_chf_l

# Dry HPRS: use the current effective plasma SEI as a scalable specific-energy
# assumption. This is exact for the continuous-SEI model and a local scaling
# approximation for the pulsed operating point.
dry_h2_gross_per_kg_fuel = H2_KG_PER_KG_FUEL_IDEAL * reactor_conversion
dry_h2_delivered_per_kg_fuel = dry_h2_gross_per_kg_fuel * h2_recovery
dry_gross_shaft_per_kg_fuel = (
    dry_h2_delivered_per_kg_fuel * H2_LHV_KWH_KG * engine_eff
)
dry_plasma_gross_e_per_kg_fuel = dry_h2_gross_per_kg_fuel * effective_plasma_sei
dry_plasma_external_e_per_kg_fuel = (
    dry_plasma_gross_e_per_kg_fuel * (1.0 - recovery_offset)
)
dry_plasma_shaft_burden_per_kg_fuel = (
    dry_plasma_external_e_per_kg_fuel / generator_eff
    if generator_eff > 0 else math.inf
)
dry_net_shaft_per_kg_fuel = (
    dry_gross_shaft_per_kg_fuel - dry_plasma_shaft_burden_per_kg_fuel
)

if dry_net_shaft_per_kg_fuel > 0:
    norm_dry_fuel_kg_h = comparison_net_kw / dry_net_shaft_per_kg_fuel
    norm_dry_fuel_l_h = norm_dry_fuel_kg_h / fuel_density
    norm_dry_h2_gross_kg_h = norm_dry_fuel_kg_h * dry_h2_gross_per_kg_fuel
    norm_dry_h2_to_engine_kg_h = norm_dry_fuel_kg_h * dry_h2_delivered_per_kg_fuel
    norm_dry_plasma_external_kw = (
        norm_dry_fuel_kg_h * dry_plasma_external_e_per_kg_fuel
    )
    norm_dry_carbon_captured_kg_h = (
        norm_dry_fuel_kg_h
        * C_KG_PER_KG_FUEL_IDEAL
        * reactor_conversion
        * carbon_capture
    )
    norm_dry_uncaptured_c_kg_h = (
        norm_dry_fuel_kg_h
        * C_KG_PER_KG_FUEL_IDEAL
        * reactor_conversion
        * (1.0 - carbon_capture)
    )
    norm_dry_uncaptured_co2_potential_kg_h = (
        norm_dry_uncaptured_c_kg_h * CO2_PER_C
    )
    norm_dry_cost_chf_h = norm_dry_fuel_l_h * gasoline_price_chf_l
else:
    norm_dry_fuel_kg_h = math.inf
    norm_dry_fuel_l_h = math.inf
    norm_dry_h2_gross_kg_h = math.inf
    norm_dry_h2_to_engine_kg_h = math.inf
    norm_dry_plasma_external_kw = math.inf
    norm_dry_carbon_captured_kg_h = math.inf
    norm_dry_uncaptured_co2_potential_kg_h = math.inf
    norm_dry_cost_chf_h = math.inf

# Steam-assisted route. Thermal demand is reported separately; electrical
# auxiliaries are treated as an onboard parasitic shaft burden.
steam_h2_gross_per_kg_fuel = steam_h2_yield_kg_per_kg_fuel * reactor_conversion
steam_h2_delivered_per_kg_fuel = steam_h2_gross_per_kg_fuel * h2_recovery
steam_gross_shaft_per_kg_fuel = (
    steam_h2_delivered_per_kg_fuel * H2_LHV_KWH_KG * engine_eff
)
steam_electrical_per_kg_fuel = (
    steam_h2_gross_per_kg_fuel * steam_electrical_aux
)
steam_electrical_shaft_burden_per_kg_fuel = (
    steam_electrical_per_kg_fuel / generator_eff
    if generator_eff > 0 else math.inf
)
steam_net_shaft_per_kg_fuel = (
    steam_gross_shaft_per_kg_fuel - steam_electrical_shaft_burden_per_kg_fuel
)

if steam_net_shaft_per_kg_fuel > 0:
    norm_steam_fuel_kg_h = comparison_net_kw / steam_net_shaft_per_kg_fuel
    norm_steam_fuel_l_h = norm_steam_fuel_kg_h / fuel_density
    norm_steam_h2_gross_kg_h = norm_steam_fuel_kg_h * steam_h2_gross_per_kg_fuel
    norm_steam_h2_to_engine_kg_h = (
        norm_steam_fuel_kg_h * steam_h2_delivered_per_kg_fuel
    )
    norm_steam_water_gross_kg_h = (
        norm_steam_fuel_kg_h * steam_water_kg_per_kg_fuel
    )
    norm_steam_water_makeup_l_h = (
        norm_steam_water_gross_kg_h * (1.0 - water_recycle)
    )
    norm_steam_electrical_kw = (
        norm_steam_h2_gross_kg_h * steam_electrical_aux
    )
    norm_steam_thermal_gross_kw = (
        norm_steam_h2_gross_kg_h * steam_thermal_energy
    )
    norm_steam_thermal_external_kw = (
        norm_steam_thermal_gross_kw * (1.0 - steam_heat_recovery)
    )

    if steam_route == "Steam reforming + WGS":
        norm_steam_co2_kg_h = (
            norm_steam_fuel_kg_h
            * CO2_KG_PER_KG_FUEL_STEAM_WGS
            * reactor_conversion
        )
        norm_steam_co_kg_h = 0.0
        norm_steam_co2_equiv_from_co_kg_h = 0.0
    else:
        norm_steam_co_kg_h = (
            norm_steam_fuel_kg_h
            * steam_co_kg_per_kg_fuel
            * reactor_conversion
        )
        norm_steam_co2_kg_h = 0.0
        norm_steam_co2_equiv_from_co_kg_h = (
            norm_steam_co_kg_h * (44.0095 / 28.0101)
        )

    norm_steam_fuel_cost_chf_h = norm_steam_fuel_l_h * gasoline_price_chf_l
    norm_steam_water_cost_chf_h = (
        norm_steam_water_makeup_l_h / 1000.0 * water_price_chf_m3
    )
    norm_steam_thermal_cost_chf_h = (
        norm_steam_thermal_external_kw * thermal_energy_price_chf_kwh
    )
    # Electrical auxiliaries are modeled as onboard shaft burden in the main
    # normalized comparison, so their energy is already reflected in fuel use.
    norm_steam_cost_chf_h = (
        norm_steam_fuel_cost_chf_h
        + norm_steam_water_cost_chf_h
        + norm_steam_thermal_cost_chf_h
    )
else:
    norm_steam_fuel_kg_h = math.inf
    norm_steam_fuel_l_h = math.inf
    norm_steam_h2_gross_kg_h = math.inf
    norm_steam_h2_to_engine_kg_h = math.inf
    norm_steam_water_makeup_l_h = math.inf
    norm_steam_electrical_kw = math.inf
    norm_steam_thermal_gross_kw = math.inf
    norm_steam_thermal_external_kw = math.inf
    norm_steam_co2_kg_h = math.inf
    norm_steam_co_kg_h = math.inf
    norm_steam_co2_equiv_from_co_kg_h = math.inf
    norm_steam_cost_chf_h = math.inf

# Per-kWh-net indicators.
def per_net(value):
    return value / comparison_net_kw if comparison_net_kw > 0 else math.inf

norm_conv_l_per_kwh = per_net(norm_conv_fuel_l_h)
norm_conv_co2_per_kwh = per_net(norm_conv_co2_kg_h)
norm_conv_cost_per_kwh = per_net(norm_conv_cost_chf_h)

norm_dry_l_per_kwh = per_net(norm_dry_fuel_l_h)
norm_dry_h2_per_kwh = per_net(norm_dry_h2_to_engine_kg_h)
norm_dry_electric_per_kwh = per_net(norm_dry_plasma_external_kw)
norm_dry_captured_c_per_kwh = per_net(norm_dry_carbon_captured_kg_h)
norm_dry_uncaptured_co2_potential_per_kwh = per_net(
    norm_dry_uncaptured_co2_potential_kg_h
)
norm_dry_cost_per_kwh = per_net(norm_dry_cost_chf_h)

norm_steam_l_per_kwh = per_net(norm_steam_fuel_l_h)
norm_steam_h2_per_kwh = per_net(norm_steam_h2_to_engine_kg_h)
norm_steam_water_l_per_kwh = per_net(norm_steam_water_makeup_l_h)
norm_steam_electric_per_kwh = per_net(norm_steam_electrical_kw)
norm_steam_thermal_external_per_kwh = per_net(norm_steam_thermal_external_kw)
norm_steam_cost_per_kwh = per_net(norm_steam_cost_chf_h)

if steam_route == "Steam reforming + WGS":
    norm_steam_carbon_metric = f"{per_net(norm_steam_co2_kg_h):.3f} kg CO₂/kWh net"
else:
    norm_steam_carbon_metric = (
        f"{per_net(norm_steam_co_kg_h):.3f} kg CO/kWh net; "
        f"{per_net(norm_steam_co2_equiv_from_co_kg_h):.3f} kg CO₂-eq if oxidized"
    )

norm_conv_total_eff = comparison_net_kw / (
    norm_conv_fuel_kg_h * gasoline_lhv
)
norm_dry_total_eff = (
    comparison_net_kw / (norm_dry_fuel_kg_h * gasoline_lhv)
    if math.isfinite(norm_dry_fuel_kg_h) else 0.0
)
norm_steam_fuel_eff = (
    comparison_net_kw / (norm_steam_fuel_kg_h * gasoline_lhv)
    if math.isfinite(norm_steam_fuel_kg_h) else 0.0
)
norm_steam_total_input_kw = (
    norm_steam_fuel_kg_h * gasoline_lhv + norm_steam_thermal_external_kw
    if math.isfinite(norm_steam_fuel_kg_h) else math.inf
)
norm_steam_total_eff = (
    comparison_net_kw / norm_steam_total_input_kw
    if norm_steam_total_input_kw > 0 and math.isfinite(norm_steam_total_input_kw)
    else 0.0
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

st.caption(f"Current comparison focus: **{comparison_focus}**")

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
    p1.metric("Pulse frequency", f"{pulse_frequency_khz:.1f} kHz")
    p2.metric("Average pulsed electrical power", f"{derived_pulse_power_kw:.2f} kW")
    p3.metric("Per-cell duty cycle", f"{pulse_duty_cycle:.3f}%")
    p4.metric("Thermodynamic adequacy", f"{100*thermo_adequacy_ratio:.1f}%")

    p5, p6 = st.columns(2)
    p5.metric("Peak power per active cell", f"{pulse_peak_power_kw_per_cell:.1f} kW")
    p6.metric("Active plasma cells", f"{active_cells}")

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

    st.markdown(
        f"""
        <div class="horg-note">
        <b>Frequency sensitivity:</b><br>
        With pulse energy fixed at <b>{pulse_energy_mj:.1f} mJ</b> and
        <b>{active_cells}</b> active cells, every +1 kHz increases average
        plasma electrical power by approximately
        <b>{pulse_energy_mj * active_cells / 1000.0:.3f} kW</b>.
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
        width="stretch",
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
        width="stretch",
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

st.dataframe(target_table, width="stretch", hide_index=True)

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
    width="stretch",
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
    gross_floor_display = (
        f"{required_gross_engine_floor_kw:.1f} kW"
        if math.isfinite(required_gross_engine_floor_kw)
        else "Not finite"
    )

    engine_eff_floor_display = (
        f"{100 * required_engine_eff_at_floor:.1f}%"
        if math.isfinite(required_engine_eff_at_floor)
        else "Not finite"
    )

    recovery_floor_display = (
        f"{100 * required_recovery_offset_at_floor:.1f}%"
        if math.isfinite(required_recovery_offset_at_floor)
        else "Not finite"
    )

    st.markdown(
        f"""
        If the plasma specific electricity were exactly the ideal
        **{THERMO_MIN_KWH_PER_KG_H2:.2f} kWh/kg H₂** floor:

        - gross H₂-engine power needed: **{gross_floor_display}**
        - H₂-engine efficiency needed at the current gross power:
          **{engine_eff_floor_display}**
        - recovered-energy offset needed at the current gross power:
          **{recovery_floor_display}**

        These are idealized model boundaries, not predictions of achievable
        reactor, engine or heat-recovery hardware.
        """
    )


st.subheader("Hypothesis 3 — Gasoline + Water / Steam-Assisted Comparison")

st.caption(
    "Water and gasoline are modeled as separate feeds mixed after vaporization. "
    "The water does not remain a liquid blend in the gasoline tank."
)

s1, s2, s3, s4 = st.columns(4)

s1.metric(
    "Steam-route gasoline",
    f"{steam_fuel_l_h:.1f} L/h",
    f"{steam_fuel_kg_h:.1f} kg/h",
)

s2.metric(
    "Make-up water",
    f"{steam_water_makeup_l_h:.1f} L/h",
)

s3.metric(
    "H₂ to engine",
    f"{steam_h2_to_engine_kg_h:.2f} kg/h",
)

s4.metric(
    "Steam-route net shaft",
    f"{steam_net_shaft_kw:.1f} kW",
)

s5, s6, s7, s8 = st.columns(4)

s5.metric(
    "Ideal H₂ yield from fuel",
    f"{steam_h2_yield_kg_per_kg_fuel:.3f} kg/kg",
)

s6.metric(
    "Thermal process demand",
    f"{steam_thermal_energy:.1f} kWh_th/kg H₂",
)

s7.metric(
    "Reaction-enthalpy reference",
    f"{steam_reaction_floor_kwh_per_kg_h2:.2f} kWh/kg H₂",
)

if steam_route == "Steam reforming + WGS":
    s8.metric(
        "CO₂ produced in route",
        f"{steam_co2_kg_h:.1f} kg/h",
    )
else:
    s8.metric(
        "CO produced in syngas",
        f"{steam_co_kg_h:.1f} kg/h",
    )

se1, se2, se3 = st.columns(3)
se1.metric("Electrical auxiliaries", f"{steam_electrical_aux:.2f} kWh_e/kg H₂")
se2.metric("External thermal demand", f"{steam_thermal_external_kw:.1f} kW_th")
se3.metric("Electrical auxiliary demand", f"{steam_electrical_aux_kw:.1f} kW_e")

st.dataframe(
    {
        "Metric": [
            "Gross H₂-engine shaft",
            "Net shaft after process burden",
            "Gasoline flow",
            "Make-up water",
            "H₂ to engine",
            "Fuel-to-net-shaft efficiency",
            "Carbon pathway",
        ],
        "Conventional gasoline ICE": [
            f"{gross_engine_kw:.1f} kW",
            f"{gross_engine_kw:.1f} kW",
            f"{conv_same_gross_fuel_l_h:.2f} L/h",
            "0 L/h",
            "0 kg/h",
            f"{100*conventional_eff:.1f}%",
            f"{conv_same_gross_co2_kg_h:.2f} kg/h CO₂",
        ],
        "Dry HPRS carbon-retention": [
            f"{gross_engine_kw:.1f} kW",
            f"{net_shaft_kw:.1f} kW",
            f"{fuel_l_h:.2f} L/h",
            "0 L/h",
            f"{h2_to_engine_kg_h:.2f} kg/h",
            f"{100*hprs_net_eff:.1f}%",
            f"{carbon_captured_kg_h:.2f} kg/h solid C captured",
        ],
        "Gasoline + steam route": [
            f"{gross_engine_kw:.1f} kW",
            f"{steam_net_shaft_kw:.1f} kW",
            f"{steam_fuel_l_h:.2f} L/h",
            f"{steam_water_makeup_l_h:.2f} L/h",
            f"{steam_h2_to_engine_kg_h:.2f} kg/h",
            f"{100*steam_net_eff:.1f}%",
            (
                f"{steam_co2_kg_h:.2f} kg/h CO₂"
                if steam_route == "Steam reforming + WGS"
                else f"{steam_co_kg_h:.2f} kg/h CO in syngas"
            ),
        ],
    },
    width="stretch",
    hide_index=True,
)

st.subheader("V2.6 Scientific Comparison — Same Net Shaft Power")

st.caption(
    f"All three pathways below are normalized to the same useful mechanical output: "
    f"{comparison_net_kw:.0f} kW net shaft. This is the primary scientific comparison."
)

n1, n2, n3 = st.columns(3)
n1.metric(
    "Conventional gasoline",
    f"{norm_conv_l_per_kwh:.3f} L/kWh net",
    delta=None,
)
n2.metric(
    "Dry HPRS",
    (
        f"{norm_dry_l_per_kwh:.3f} L/kWh net"
        if math.isfinite(norm_dry_l_per_kwh) else "Not self-sustaining"
    ),
    delta=None,
)
n3.metric(
    "Gasoline + steam",
    (
        f"{norm_steam_l_per_kwh:.3f} L/kWh net"
        if math.isfinite(norm_steam_l_per_kwh) else "Not self-sustaining"
    ),
    delta=None,
)

st.dataframe(
    {
        "Normalized metric": [
            "Net shaft basis",
            "Gasoline consumption",
            "H₂ delivered to engine",
            "Make-up water",
            "Process electricity",
            "External process heat",
            "Fuel-to-net-shaft efficiency",
            "Total-energy-to-net efficiency",
            "Carbon / CO₂ indicator",
            "Solid carbon captured",
            "Operating cost",
        ],
        "Conventional gasoline ICE": [
            f"{comparison_net_kw:.0f} kW net",
            f"{norm_conv_l_per_kwh:.3f} L/kWh net",
            "0 kg/kWh net",
            "0 L/kWh net",
            "0 kWh_e/kWh net",
            "0 kWh_th/kWh net",
            f"{100*norm_conv_total_eff:.1f}%",
            f"{100*norm_conv_total_eff:.1f}%",
            f"{norm_conv_co2_per_kwh:.3f} kg CO₂/kWh net",
            "0 kg/kWh net",
            f"CHF {norm_conv_cost_per_kwh:.3f}/kWh net",
        ],
        "Dry HPRS carbon-retention": [
            f"{comparison_net_kw:.0f} kW net",
            (
                f"{norm_dry_l_per_kwh:.3f} L/kWh net"
                if math.isfinite(norm_dry_l_per_kwh) else "Not self-sustaining"
            ),
            (
                f"{norm_dry_h2_per_kwh:.4f} kg/kWh net"
                if math.isfinite(norm_dry_h2_per_kwh) else "—"
            ),
            "0 L/kWh net",
            (
                f"{norm_dry_electric_per_kwh:.3f} kWh_e/kWh net"
                if math.isfinite(norm_dry_electric_per_kwh) else "—"
            ),
            "Not modeled in V2.6",
            (
                f"{100*norm_dry_total_eff:.1f}%"
                if math.isfinite(norm_dry_fuel_kg_h) else "—"
            ),
            (
                f"{100*norm_dry_total_eff:.1f}%"
                if math.isfinite(norm_dry_fuel_kg_h) else "—"
            ),
            (
                f"{norm_dry_uncaptured_co2_potential_per_kwh:.3f} kg CO₂/kWh net "
                "uncaptured-C oxidation potential"
                if math.isfinite(norm_dry_uncaptured_co2_potential_per_kwh) else "—"
            ),
            (
                f"{norm_dry_captured_c_per_kwh:.3f} kg C/kWh net"
                if math.isfinite(norm_dry_captured_c_per_kwh) else "—"
            ),
            (
                f"CHF {norm_dry_cost_per_kwh:.3f}/kWh net"
                if math.isfinite(norm_dry_cost_per_kwh) else "—"
            ),
        ],
        "Gasoline + steam route": [
            f"{comparison_net_kw:.0f} kW net",
            (
                f"{norm_steam_l_per_kwh:.3f} L/kWh net"
                if math.isfinite(norm_steam_l_per_kwh) else "Not self-sustaining"
            ),
            (
                f"{norm_steam_h2_per_kwh:.4f} kg/kWh net"
                if math.isfinite(norm_steam_h2_per_kwh) else "—"
            ),
            (
                f"{norm_steam_water_l_per_kwh:.3f} L/kWh net"
                if math.isfinite(norm_steam_water_l_per_kwh) else "—"
            ),
            (
                f"{norm_steam_electric_per_kwh:.3f} kWh_e/kWh net"
                if math.isfinite(norm_steam_electric_per_kwh) else "—"
            ),
            (
                f"{norm_steam_thermal_external_per_kwh:.3f} kWh_th/kWh net"
                if math.isfinite(norm_steam_thermal_external_per_kwh) else "—"
            ),
            (
                f"{100*norm_steam_fuel_eff:.1f}%"
                if math.isfinite(norm_steam_fuel_kg_h) else "—"
            ),
            (
                f"{100*norm_steam_total_eff:.1f}%"
                if math.isfinite(norm_steam_fuel_kg_h) else "—"
            ),
            norm_steam_carbon_metric,
            "0 kg/kWh net in selected ideal steam chemistry",
            (
                f"CHF {norm_steam_cost_per_kwh:.3f}/kWh net"
                if math.isfinite(norm_steam_cost_per_kwh) else "—"
            ),
        ],
    },
    width="stretch",
    hide_index=True,
)

st.markdown(
    f"""
    <div class="horg-note">
    <b>How to read V2.6:</b><br>
    • Conventional gasoline is the reference at the same {comparison_net_kw:.0f} kW net.<br>
    • Dry HPRS includes its onboard plasma electrical burden through increased fuel demand.
      The displayed electrical value is the remaining plasma electricity after the selected
      recovered-energy offset; it is <b>not added again to cost</b>, avoiding double counting.<br>
    • The steam route includes electrical auxiliaries as onboard parasitic load, while thermal
      process demand is reported separately. Only unrecovered thermal demand is included in the
      total-energy efficiency, and it affects cost only if a non-zero thermal-energy price is entered.<br>
    • In pulsed-plasma mode, the normalized Dry-HPRS result assumes the current effective
      kWh/kg H₂ scales locally with hydrogen throughput; that scaling must be validated experimentally.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Current operating-point costs (non-normalized)"):
    st.write(
        f"Conventional gasoline: CHF {conventional_fuel_cost_chf_h:.2f}/h at "
        f"{gross_engine_kw:.1f} kW gross shaft."
    )
    st.write(
        f"Dry HPRS fuel: CHF {dry_hprs_fuel_cost_chf_h:.2f}/h at "
        f"{net_shaft_kw:.1f} kW net after plasma burden."
    )
    st.write(
        f"Steam route fuel + water: CHF "
        f"{(steam_fuel_cost_chf_h + steam_water_cost_chf_h):.2f}/h at "
        f"{steam_net_shaft_kw:.1f} kW net, excluding any priced supplemental heat."
    )
    if thermal_energy_price_chf_kwh > 0:
        st.write(
            f"Steam supplemental thermal cost: CHF {steam_thermal_cost_chf_h:.2f}/h."
        )

st.markdown(
    f"""
    <div class="horg-note">
    <b>Steam-route chemistry in the selected model:</b><br>
    {
        "C₈H₁₈ + 16 H₂O → 8 CO₂ + 25 H₂"
        if steam_route == "Steam reforming + WGS"
        else "C₈H₁₈ + 8 H₂O → 8 CO + 17 H₂"
    }<br><br>
    Ideal H₂ yield: <b>{steam_h2_yield_kg_per_kg_fuel:.3f} kg H₂/kg fuel</b>.<br>
    Stoichiometric gross water feed:
    <b>{steam_water_kg_per_kg_fuel:.3f} kg H₂O/kg fuel</b> before any recycle.<br>
    The thermal and electrical process inputs are separated in V2.6. The reaction-enthalpy
    reference is only an ideal thermodynamic reference and does not represent complete hardware losses.
    </div>
    """,
    unsafe_allow_html=True,
)

if steam_route == "Steam reforming + WGS":
    st.warning(
        "The steam + WGS route increases hydrogen yield because part of the hydrogen "
        "comes from water, but it converts the fuel carbon primarily to CO₂. "
        "It is therefore not a solid-carbon-retention pathway unless a separate CO₂ "
        "capture/conversion stage is added."
    )
else:
    st.warning(
        "The syngas route avoids full conversion to CO₂ in this simplified reaction, "
        "but produces substantial CO. CO is toxic and must be shifted, oxidized, "
        "separated or otherwise handled before any vehicle exhaust claim can be made."
    )

st.subheader("Hypothesis 1 — Conventional Gasoline Engine Benchmark")
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
    width="stretch",
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

st.subheader("Hypothesis 2 — Dry HPRS Carbon-Retention Interpretation")
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

        The V2.5.2 design diagnosis varies one lever at a time and solves the
        simplified balance backwards for the selected net-power target.
        It can estimate the required gross engine power, H₂-engine efficiency,
        recovered-energy offset, or plasma specific electricity. A value being
        mathematically reachable in the model is not evidence that the required
        hardware performance is experimentally achievable.

        **V2.6 same-net-power normalization**

        The primary comparison rescales all three pathways to the same selected net shaft power.  
        Dry-HPRS plasma electricity is treated as an onboard parasitic load.  
        Steam-route thermal demand and electrical auxiliaries are reported separately.  
        Unrecovered process heat is included in total-energy efficiency but is priced only when a thermal-energy price is entered.

        **Steam-assisted comparison**

        Two idealized n-octane references are available:

        `C8H18 + 8 H2O -> 8 CO + 17 H2`

        and, after complete water-gas shift:

        `C8H18 + 16 H2O -> 8 CO2 + 25 H2`

        The steam route increases hydrogen yield because water supplies additional
        hydrogen atoms. In the complete-WGS case, however, the fuel carbon becomes
        CO2 rather than retained solid carbon. The process-energy input and heat
        recovery are editable scenario assumptions.

        **Pulsed-plasma interpretation**  
`P_avg = energy_per_pulse × pulse_frequency × active_cells`  
Pulse width is used to estimate instantaneous peak power and electrical duty cycle. These values are research controls, not validated automotive reactor specifications.

**Boundary:** gasoline is a mixture. n-octane is only a transparent first surrogate;
        real fuel requires species-resolved chemistry and laboratory data.
        """
    )

st.caption("HPRS Automotive V2.6 · HydrogenOrg research model · Simulation → laboratory validation → proof of concept")
