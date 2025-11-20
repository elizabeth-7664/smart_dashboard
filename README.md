Smart Dashboard Backend

Project Purpose
Many SMEs in Kenya (and globally) waste hours managing fragmented sales, inventory, and customer data. They often rely on messy Excel sheets, manual accounting, and lack real-time insights.
Smart Dashboard solves this by:
Consolidating sales, inventory, and customer data in one system
Providing real-time reporting and actionable insights
Integrating payments (MPesa, bank) and notifications
Being scalable for small businesses

Project Structure

backend_project/
├── README.md
└── app/
    ├── __init__.py
    ├── main.py
    ├── database/
    │   ├── __init__.py
    │   ├── setup.py
    │   └── init_db.py
    ├── models/
    │   └── sales.py
    ├── routers/
    │   └── .gitkeep
    ├── schemas/
    │   └── .gitkeep
    └── services/
        └── .gitkeep
main.py → FastAPI entry point
database/ → Async Postgres engine setup, DB initialization
models/ → SQLAlchemy models (Sale)
routers/ → API endpoints
schemas/ → Pydantic validation
services/ → Business logic

Dependencies
Python 3.12+
Termux (Android)
FastAPI
SQLAlchemy (async)
asyncpg (Postgres driver)
pip install fastapi sqlalchemy asyncpg uvicorn

Database Setup

Postgres user and database

CREATE ROLE smartuser WITH LOGIN PASSWORD 'tom@2025' CREATEDB;
CREATE DATABASE smart_dashboard OWNER smartuser;
Database URL for async engine 

DATABASE_URL = "postgresql+asyncpg://smartuser:password@localhost:5432/smart_dashboard"

Initialize tables
python -m app.database.init_db
Creates sales table: id, date, product_name, quantity, cost_price, selling_price, payment_method, mpesa_transaction_id

Models
Sale model (app/models/sales.py)
Column
Type
Notes
id
SERIAL
Primary key
date
DATE
Sale date
product_name
VARCHAR
Product name
quantity
INTEGER
Quantity sold
cost_price
FLOAT
Cost per unit
selling_price
FLOAT
Selling price per unit
payment_method
VARCHAR
E.g., Mpesa, Cash
mpesa_transaction_id
VARCHAR
Optional transaction ID

Current Progress
Async Postgres backend set up on Termux
sales table exists
Project structure committed to GitHub (smart_dashboard)
Ready for: CSV upload, sales insertion, FastAPI routes

