# BESS Streamlit Dashboard

This is a Streamlit conversion of the HTML-based BESS dashboard.

## Features

- JSON-based component database
- Dynamic C-rate profiles
- Dynamic DC bus current
- Dynamic containers per PCS
- Dynamic PCS utilisation
- Single Line Diagram section
- Electrical Connection Path section
- Component library editor
- Excel import page
- JSON editor page
- Image assets separated into folders

## Folder structure

```text
bess-streamlit-dashboard/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/
│   └── db.json
├── assets/
│   ├── styles/
│   │   └── dashboard.css
│   └── images/
│       ├── logos/
│       └── equipment/
├── src/
│   ├── paths.py
│   ├── store.py
│   ├── assets.py
│   ├── calculations.py
│   ├── ui.py
│   └── excel_importer.py
└── scripts/
    └── bootstrap_from_excel.py