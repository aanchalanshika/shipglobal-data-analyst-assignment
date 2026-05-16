# ShipGlobal - Coffee Shop Sales Analytics Dashboard

Repository: https://github.com/aanchalanshika/shipglobal-data-analyst-assignment

## Project Overview

A Streamlit dashboard for cleaning, exploring, and reporting coffee shop sales data. Features include:

- Data cleaning and preprocessing
- KPI reporting (revenue, orders, quantity, AOV)
- Trend analysis (daily / monthly)
- Category, store, hourly, and heatmap analyses
- Download cleaned CSV

## Files

- `app.py` - Main Streamlit app (entry point).
- `Coffee Shop Sales.xlsx` - source data (do not commit large datasets to GitHub; consider cloud storage).
- `requirements.txt` - Python dependencies.

## Prerequisites

- Python 3.10+ (Conda recommended)
- Git
- Docker (optional, for container deployment)

## Quick local run (recommended: use the Conda environment already configured)

From the project folder:

```powershell
cd "D:\shipglobal assignmnet"
# (optional) use the conda Python that already has dependencies installed
D:/anaconda3/python.exe -m streamlit run "D:\shipglobal assignmnet\app.py"
```

Or, using your active python environment after installing dependencies:

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Open the URL shown in the terminal (usually http://localhost:8501).

## Connect local repo to your GitHub repository

If you haven't pushed this project to GitHub yet, run:

```bash
cd "D:\shipglobal assignmnet"
git init
git add .
git commit -m "Initial dashboard"
# replace USERNAME/REPO with your repo
git remote add origin https://github.com/aanchalanshika/shipglobal-data-analyst-assignment.git
git branch -M main
git push -u origin main
```

If you already have the remote set up on GitHub, just push your commits:

```bash
git add README.md
git commit -m "Add README"
git push
```

## Deploy to Streamlit Community Cloud (fast, free for demos)

1. Push the repository to GitHub (see above).
2. Go to https://share.streamlit.io and log in with GitHub.
3. Click "New app" → choose the repo `aanchalanshika/shipglobal-data-analyst-assignment`, branch `main`, and `app.py` as the file.
4. Click "Deploy". Streamlit will install dependencies from `requirements.txt` and start the app.

Notes:
- Do NOT commit large binaries (Excel files). For production, store data in cloud storage and fetch it at runtime.
- Use the Streamlit Cloud Secrets UI to store credentials if you use S3/Azure Blob.

## Docker deployment (optional)

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
EXPOSE 8080
CMD ["streamlit", "run", "app.py", "--server.port", "8080", "--server.headless", "true"]
```

Build and run locally:

```bash
docker build -t shipglobal-dashboard .
docker run -p 8080:8080 shipglobal-dashboard
# open http://localhost:8080
```

Deploy the image to a container platform (Render, Azure App Service, Google Cloud Run, etc.).

## CI / Auto-deploy

I can add a GitHub Actions workflow that builds the Docker image and pushes to a registry or triggers a Render/Azure deploy on merges to `main`.

## Screenshots

### Dashboard Overview
![Dashboard Hero](assests/Screenshot%202026-05-16%20115453.png)

### Data Upload & Raw Preview
![Data Upload](assests/Screenshot%202026-05-16%20115502.png)

### Cleaning Summary
![Cleaning Summary](assests/Screenshot%202026-05-16%20115512.png)

### KPI Cards
![KPI Cards](assests/Screenshot%202026-05-16%20115519.png)

### Daily Trend Analysis
![Daily Trends](assests/Screenshot%202026-05-16%20115531.png)

### Category & Store Analysis
![Category & Store](assests/Screenshot%202026-05-16%20115538.png)

### Hourly Heatmap & Insights
![Hourly Heatmap](assests/Screenshot%202026-05-16%20115544.png)

## Troubleshooting

- `ModuleNotFoundError: openpyxl` → ensure `openpyxl` is installed (already in `requirements.txt`).
- If Streamlit fails to start due to port in use, pass `--server.port 8502`.
- If your Excel file is large, the app may take time to load. For production, switch to preprocessed CSV or a database.

