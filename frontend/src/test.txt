# 🍛 Local Food Wastage Management System

## Setup & Run Instructions

### Step 1 — Create Database in pgAdmin
- Open pgAdmin
- Right-click Databases → Create → Database
- Name: `food_wastage` → Save

### Step 2 — Install Dependencies
Open terminal in the project folder and run:
```bash
pip install -r requirements.txt
```

### Step 3 — Generate CSV Datasets
```bash
python generate_data.py
```
This creates 4 CSV files inside the `data/` folder.

### Step 4 — Load Data into PostgreSQL
```bash
python setup_database.py
```
This creates all 4 tables and loads the data.

### Step 5 — Run the Streamlit App
```bash
streamlit run app/app.py
```

---

## Project Structure
```
food_wastage/
├── data/
│   ├── providers_data.csv
│   ├── receivers_data.csv
│   ├── food_listings_data.csv
│   └── claims_data.csv
├── app/
│   └── app.py          ← Main Streamlit Application
├── generate_data.py    ← Generates CSV datasets
├── setup_database.py   ← Creates DB tables & loads data
├── requirements.txt
└── README.md
```

## Features
- ✅ Dashboard with KPIs and visualizations
- ✅ 15 SQL Queries with output + charts
- ✅ Filter by City, Food Type, Meal Type, Provider Type
- ✅ CRUD Operations (Add / Update / Delete)
- ✅ View all 4 database tables
- ✅ Contact Directory for providers & receivers
