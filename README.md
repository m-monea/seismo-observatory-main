# Seismo Observatory

An open, continuously updating observatory for global earthquake activity, built on USGS data and designed for transparent, reproducible analysis.

This project is **not** an earthquake prediction system.  
It focuses on **monitoring, exploration, and probabilistic reasoning** about seismicity using public catalogs.

## Live observatory

This repository is deployed as a public website using **GitHub Pages** (served from the `/docs` folder).

The site automatically updates as new earthquakes are reported.

## What it does

- Fetches real earthquake data from the USGS Earthquake Hazards Program
- Stores events in a structured machine-readable format
- Publishes a lightweight, interactive public dashboard
- Updates itself automatically using GitHub Actions

## Data source

All events come from the **USGS Earthquake Hazards Program** (FDSN Event Web Service, GeoJSON format).

Earthquake records may be revised over time as locations and magnitudes are refined.  
Event IDs provided by USGS are treated as the authoritative identifiers.

## Repository layout

.
├── src/ # Data ingestion and processing
│ └── fetch_usgs.py
├── docs/ # GitHub Pages root
│ ├── index.html
│ ├── events.json # Auto-generated
│ └── .nojekyll
├── .github/workflows/ # Automation
│ └── update.yml
├── README.md
└── requirements.txt


## Running locally

Requires Python 3.9 or newer.

```bash
python src/fetch_usgs.py

This regenerates:

docs/events.json

Open docs/index.html in a browser to view the dashboard.
Automation

A GitHub Actions workflow runs on a schedule and on manual trigger to:

    Download the latest USGS earthquake catalog

    Regenerate the dataset

    Commit and publish the updated data

The website therefore stays continuously synchronized with the live seismic record.
Scientific philosophy

Earthquakes are chaotic physical processes governed by complex fracture mechanics and stress transfer in the Earth's crust.

This project treats seismicity as a stochastic system:
it does not attempt to produce deterministic predictions, but instead aims to explore
patterns, rates, uncertainty, and evolving seismic risk.
Roadmap

Planned extensions include:

    Interactive maps and regional filtering

    Magnitude–frequency statistics (Gutenberg–Richter)

    Aftershock and sequence modeling (ETAS / Hawkes)

    Probabilistic forecasting and calibration metrics

    Model comparison against statistical baselines

Author

Created and maintained by M. Monea
License

MIT License