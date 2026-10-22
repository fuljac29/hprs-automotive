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
      <span class="horg-kicker">HydrogenOrg · HPRS Automotive</span>
      <h1>Plasma Carbon-Retention Engine</h1>
      <p>
        Research simulator for an onboard hydrocarbon-to-hydrogen pathway in which a gasoline
        surrogate is decomposed before combustion, hydrogen feeds an H₂-capable internal-combustion
        engine, and carbon is retained as a solid instead of intentionally oxidized to CO₂.
      </p>
      <span class="horg-chip">Research-stage model</span>
      <span class="horg-chip">n-octane surrogate</span>
      <span class="horg-chip">Mass & energy balance</span>
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
    engine_eff = st.slider("H₂ engine brake efficiency (%)", 20, 50, 38, 1) / 100.0
    reactor_conversion = st.slider(
        "Overall fuel conversion after recycle (%)", 60, 100, 92, 1,
        help="Net fraction of fuel converted through the modeled plasma pathway.",
    ) / 100.0
    h2_recovery = st.slider("H₂ recovery to engine (%)", 70, 100, 96, 1) / 100.0
    carbon_capture = st.slider("Solid-carbon collection (%)", 70, 100, 96, 1) / 100.0
    plasma_sei = st.slider(
        "Plasma electricity (kWh/kg H₂)",
        float(round(THERMO_MIN_KWH_PER_KG_H2, 1)), 30.0, 8.0, 0.1,
        help="Gross electrical input per kg H₂. Lower bound is the ideal standard-state n-octane decomposition floor.",
    )
    recovery_offset = st.slider(
        "Validated recovered-energy offset (%)", 0, 80, 20, 1,
        help="Fraction of gross plasma electrical demand genuinely covered by recovered energy; not free energy.",
    ) / 100.0
    generator_eff = st.slider("Generator / power-electronics efficiency (%)", 70, 98, 90, 1) / 100.0
    fuel_density = st.number_input("Fuel density (kg/L)", 0.68, 0.82, 0.745, 0.005, format="%.3f")
    gasoline_lhv = st.number_input("Fuel LHV reference (kWh/kg)", 10.0, 14.0, 12.0, 0.1)

h2_required_engine_kg_h = gross_engine_kw / (engine_eff * H2_LHV_KWH_KG)
effective_h2_yield = H2_KG_PER_KG_FUEL_IDEAL * reactor_conversion * h2_recovery
fuel_kg_h = h2_required_engine_kg_h / effective_h2_yield if effective_h2_yield > 0 else math.inf
fuel_l_h = fuel_kg_h / fuel_density

h2_gross_kg_h = fuel_kg_h * H2_KG_PER_KG_FUEL_IDEAL * reactor_conversion
h2_to_engine_kg_h = h2_gross_kg_h * h2_recovery

carbon_generated_kg_h = fuel_kg_h * C_KG_PER_KG_FUEL_IDEAL * reactor_conversion
carbon_captured_kg_h = carbon_generated_kg_h * carbon_capture
carbon_uncaptured_kg_h = carbon_generated_kg_h * (1.0 - carbon_capture)

plasma_gross_kw = h2_gross_kg_h * plasma_sei
plasma_external_kw = plasma_gross_kw * (1.0 - recovery_offset)
shaft_draw_for_plasma_kw = plasma_external_kw / generator_eff if generator_eff > 0 else math.inf
net_shaft_kw = gross_engine_kw - shaft_draw_for_plasma_kw

h2_chemical_kw = h2_to_engine_kg_h * H2_LHV_KWH_KG
fuel_chemical_kw = fuel_kg_h * gasoline_lhv
co2_retention_equiv_kg_h = carbon_captured_kg_h * CO2_PER_C
uncaptured_c_oxidation_potential_kg_h = carbon_uncaptured_kg_h * CO2_PER_C
ideal_h2_energy_fraction = H2_KG_PER_KG_FUEL_IDEAL * H2_LHV_KWH_KG / gasoline_lhv

st.subheader("Scenario result")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Fuel to reactor", f"{fuel_kg_h:.1f} kg/h", f"{fuel_l_h:.1f} L/h")
c2.metric("H₂ to engine", f"{h2_to_engine_kg_h:.2f} kg/h")
c3.metric("Solid C captured", f"{carbon_captured_kg_h:.1f} kg/h")
c4.metric("Net shaft after plasma", f"{net_shaft_kw:.1f} kW")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Gross plasma demand", f"{plasma_gross_kw:.1f} kW")
c6.metric("External plasma demand", f"{plasma_external_kw:.1f} kW")
c7.metric("CO₂-equivalent carbon retained*", f"{co2_retention_equiv_kg_h:.1f} kg/h")
c8.metric("Ideal H₂ share of fuel LHV", f"{100*ideal_h2_energy_fraction:.1f}%")

st.caption(
    "*CO₂-equivalent carbon retained is the CO₂ mass the captured carbon could form if fully oxidized. "
    "It is not a lifecycle-emissions claim or a measured tailpipe value."
)

if net_shaft_kw > 0:
    st.success(
        f"Under these assumptions the model leaves {net_shaft_kw:.1f} kW of shaft power "
        "after converting the modeled external plasma electricity to an equivalent shaft burden."
    )
else:
    st.error(
        "Under these assumptions the modeled plasma power burden exceeds the gross engine shaft output. "
        "This scenario is not self-sustaining on an engine-driven electrical supply."
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

        **Boundary:** gasoline is a mixture. n-octane is only a transparent first surrogate;
        real fuel requires species-resolved chemistry and laboratory data.
        """
    )

st.caption("HPRS Automotive V1 · HydrogenOrg research model · Simulation → validation → proof of concept")
