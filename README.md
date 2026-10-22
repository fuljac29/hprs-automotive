# HPRS Automotive — Plasma Carbon-Retention Engine

Package for the planned HydrogenOrg page:

`https://hydrogenorg.ch/hprs-automotive/`

## Files

- `app.py` — HPRS Automotive V1 simulator
- `requirements.txt` — Streamlit dependency
- `.streamlit/config.toml` — HydrogenOrg-style light theme
- `wordpress-snippet.html` — complete WordPress page snippet with Streamlit embed placeholder

## Scientific basis

V1 uses n-octane (`C8H18`) as a transparent gasoline surrogate:

`C8H18 -> 8 C(s) + 9 H2`

Ideal stoichiometric yields are about 0.159 kg H2 and 0.841 kg solid carbon per kg n-octane.

Reference data:

- NIST Chemistry WebBook, n-octane standard liquid enthalpy of formation ≈ -250 kJ/mol: https://webbook.nist.gov/cgi/cbook.cgi?ID=C111659&Mask=2
- U.S. DOE hydrogen LHV = 33.3 kWh/kg: https://www.energy.gov/cmei/fuels/doe-technical-targets-onboard-hydrogen-storage-light-duty-vehicles

The ideal standard-state n-octane decomposition floor is about 3.83 kWh/kg H2. Real reactor electricity must be higher after plasma, thermal, separation and auxiliary losses.

## GitHub + Streamlit Community Cloud

1. Create a GitHub repository, suggested name: `hprs-automotive`.
2. Upload this folder's contents.
3. In Streamlit Community Cloud, deploy the repository with `app.py` as the entrypoint.
4. Copy the public `*.streamlit.app` URL.
5. Use the embed form: `https://YOUR-APP.streamlit.app/?embed=true&embed_options=light_theme`.
6. In `wordpress-snippet.html`, remove the placeholder block, uncomment the iframe, and replace `STREAMLIT_APP_URL`.
7. Paste the snippet into the WordPress code editor for `HPRS Automotive — Plasma Carbon-Retention Engine`.

Streamlit officially supports iframe embedding for public Community Cloud apps through `?embed=true`.

## Research boundary

This is an exploratory mass/energy-balance simulator, not a validated reactor or vehicle-performance claim. It does not validate plasma efficiency, NOx, startup/transient behavior, carbon morphology/fouling, H2 purification hardware, lifecycle emissions, road safety or homologation.
