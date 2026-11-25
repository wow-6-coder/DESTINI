# DESTINI – Delhi Bus Journey Planner

DESTINI is a bus journey-planning application developed to make travelling by public transport in Delhi easier and more convenient.

The project focuses on helping passengers find suitable bus connections between two locations and get a better idea of how long their journey might take. It uses public transport schedules and historical GPS data to provide route suggestions and estimated travel times.

Our aim is to make bus travel more predictable by using data to improve everyday journey planning.

## Features

### Journey Planning

- Search for bus journeys between Delhi bus stops.
- Find direct bus connections.
- Find journeys that require one bus transfer.
- View boarding, destination and interchange stops.
- Compare different journey options.

### Travel Time Prediction

DESTINI uses historical GPS observations to estimate travel time between bus stops.

- Uses historical GPS data for supported routes.
- Combines prediction results with scheduled travel times.
- Uses schedule-based estimates when GPS prediction data is unavailable.

### Route Maps

- View bus routes on an interactive map.
- See origin and destination locations.
- Identify interchange points for transfer journeys.
- Explore route information using GTFS data.

### Journey Information

- View departure and estimated arrival times.
- Check journey duration.
- See route and stop details.
- Understand where to change buses during a transfer journey.

## How It Works

DESTINI combines public transport data with historical GPS observations to help passengers plan their journeys.

The process is straightforward:

1. The passenger selects their starting point and destination.
2. The application searches for available direct and transfer connections.
3. Suitable bus trips are identified using the journey-planning system.
4. Historical GPS-based estimates are used where prediction data is available.
5. Scheduled travel times are used as a fallback when necessary.
6. The passenger can view the available journeys, estimated timings and route maps.

## Travel Time Prediction

One of the main parts of DESTINI is its historical GPS-based travel time prediction system.

We used historical Delhi DTC bus GPS observations to study travel times between bus stops. The model was trained using data from one day and evaluated using data from a separate day to check how well it performed on unseen observations.

### Initial Evaluation: Route 764DOWN

| Metric | Result |
|---|---:|
| Training date | October 1 |
| Testing date | October 2 |
| Evaluated observations | 1,838 |
| GPS prediction coverage | 100% |
| Schedule-only MAE | 51.10 seconds |
| GPS model with schedule fallback MAE | 21.56 seconds |
| Improvement in MAE | 57.82% |

These results are from an initial evaluation of one route over two separate days. Further testing across more routes and dates is required before making broader performance claims.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main application development |
| Streamlit | Web application interface |
| Pandas | Data processing and analysis |
| SQLite | Historical GPS data storage |
| Folium | Interactive maps |
| Streamlit-Folium | Displaying maps in Streamlit |
| GTFS | Public transport schedules and route information |
| Machine Learning | Travel time prediction |

## Project Structure

```text
DTC-GPS-Prediction/
|
|-- backend/
|
|-- frontend/
|   |-- app.py
|
|-- data/
|   |-- historical_gps/
|   |-- static_gtfs/
|   |-- live_gtfs_rt/
|   |-- processed/
|
|-- src/
|   |-- ingestion/
|   |-- preprocessing/
|   |-- map_matching/
|   |-- prediction/
|   |-- journey_planner/
|
|-- models/
|
|-- reports/
|
|-- .gitignore
|-- README.md
```

## Installation and Setup

### Requirements

- Python 3.10 or later
- Git
- Visual Studio Code (recommended)

### 1. Clone the repository

```bash
git clone https://github.com/wow-6-coder/DESTINI.git
```

### 2. Open the project directory

```bash
cd DESTINI
```

### 3. Create a virtual environment

For Windows:

```powershell
python -m venv .venv
```

### 4. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Install the required packages

```powershell
pip install streamlit pandas folium streamlit-folium
```

If a requirements.txt file is available, use:

```powershell
pip install -r requirements.txt
```

### 6. Prepare the datasets

DESTINI requires GTFS data and processed journey and prediction datasets.

Some of the historical GPS and processed files are large and may need to be downloaded or prepared separately. They are not necessarily included in the GitHub repository.

### 7. Run the application

```powershell
python -m streamlit run frontend/app.py
```

The application will open in your default browser.

## Data Sources

The project uses the following data:

**GTFS data:** Used for bus stops, routes, trips, schedules and route shapes.

Source: [India GTFS – Delhi Bus Data](https://github.com/reclaimchennai/India_GTFS)

**Historical GPS data:** Used to analyse bus movement and estimate travel times between stops.

**Processed datasets:** Used by the journey planner and prediction system.

Data availability and freshness can vary, so the original sources should be checked before relying on schedules for actual travel.

## Current Limitations

DESTINI is still under development. Some features are not yet fully implemented.

- Historical GPS-based predictions are not live bus tracking.
- GPS prediction is currently available only for supported routes and stop pairs.
- Other routes use schedule-based estimates.
- Transfer journey estimates are currently schedule-based.
- Real-time bus location and live arrival updates are not yet implemented.
- Prediction accuracy may vary depending on the route, date and traffic conditions.

## Future Improvements

We plan to improve DESTINI in several areas:

- Add live DTC bus tracking.
- Expand GPS-based predictions to more routes.
- Improve arrival time estimates.
- Support more transfer combinations.
- Add saved journeys and passenger notifications.
- Improve the handling of delays and changing traffic conditions.
- Make the application more accessible on mobile devices.

## Our Goal

DESTINI started with a simple idea: bus passengers should have a better understanding of their journeys before they start travelling.

By combining historical travel data, public transport schedules and journey planning, we hope to make everyday bus travel more predictable and convenient.

## Repository

GitHub: https://github.com/wow-6-coder/DESTINI

DESTINI is an ongoing project, and we welcome feedback and suggestions for improvement.
