# ARPA FVG Climate Analytics  
**Open-source, reproducible analysis of local climate change in Friuli Venezia Giulia**

---

## Overview

This project is an open-source initiative for **local climate analysis** based on historical meteorological data published by the *Osservatorio Meteorologico Regionale del Friuli Venezia Giulia (ARPA FVG)*.

The goal is to build a **transparent, modular, and reproducible pipeline** that starts from raw public weather data and produces:

- long-term climate trend analyses,
- detection of anomalous periods,
- similarity-based comparisons between months and years,
- interactive visualizations for non-technical users.

The project is **not** designed as an academic benchmark or a production system, but as a **research-grade, applied artifact** that emphasizes data understanding, methodological clarity, and interpretability.

---

## Motivation

Climate change is often discussed at a global scale, but its effects are more tangible and understandable when observed **locally**.

This project focuses on **regional and micro-territorial climate dynamics**, aiming to:

- make local climate data accessible and interpretable,
- empirically show how seasonal patterns evolve over time,
- experiment with machine learning techniques on real, imperfect time-series data,
- practice end-to-end ML system design beyond isolated modeling.

---

## Data Source

The data used in this project comes from the **public ARPA FVG meteorological archive**, which provides daily historical observations from multiple weather stations across the region.

Typical variables include:
- temperature (mean/min/max),
- precipitation,
- humidity,
- wind,
- pressure,
- radiation (when available).

> **Important:**  
> Raw data is **not included** in this repository.  
> Instructions to download and reproduce the dataset are provided below.

---

## Project Scope (What this project does)

✔ Automated and reproducible data ingestion  
✔ Explicit handling of data quality issues  
✔ Long-term trend and seasonality analysis  
✔ Unsupervised ML for anomaly detection  
✔ Similarity-based retrieval of comparable months/years  
✔ Interpretable feature engineering  
✔ Interactive visualization for exploration  

---

## Non-goals (What this project does *not* do)

✘ Climate forecasting or prediction  
✘ Causal attribution of climate change  
✘ High-resolution physical climate modeling  
✘ Real-time data ingestion  
✘ Production-grade ML deployment  

This project focuses on **analysis, interpretation, and methodological clarity**, not operational forecasting.

---
