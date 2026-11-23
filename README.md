# Matrix Dashboard

An open-source Streamlit workbench for **AI-generated financial intelligence dashboards**. Uses public/synthetic structured data; no credentials or private client data.

## Deploy on Streamlit Community Cloud

1. Connect this GitHub repository at https://share.streamlit.io/.
2. Branch: `main`; main file: `app.py`.
3. Deploy. No secrets required for this demo.

## Dynamic dashboard generation

Add a new JSON document to `dashboards/<slug>.json` following the existing Suzlon example. The app automatically adds a new company dashboard with its own financial charts, DCF parameters, timeline and evidence table. An AI coding agent can also modify the Python UI when a new investigation needs a genuinely different layout.

The **first deployment is intentionally a static, public prototype**; it does not connect directly to private MatrixMCP/Composio credentials. Programmatic creation of future dashboards requires a separate authorized GitHub write action or generator. Only publish synthetic or publicly distributable evidence. All valuation outputs are scenario estimates and not investment advice.
