Here is the final, portfolio-ready `README.md` that incorporates your complete ML pipeline, the corrected Docker architecture, and the new Streamlit Cloud deployment instructions.

Copy this entire block and replace your current `README.md`.

```markdown
# 🛡️ Enterprise Real-Time Fraud Detection System

An end-to-end, real-time financial fraud detection platform. This system combines asynchronous Machine Learning inference, a PostgreSQL transactional ledger, Redis feature caching, and a live Streamlit dashboard. 

It demonstrates a production-ready architecture where hard database constraints and predictive AI work seamlessly together to process, analyze, and secure financial transactions in milliseconds.

---

## ✨ Key Features

* **Real-Time Transaction Processing:** FastAPI asynchronous backend handles concurrent payloads without blocking.
* **Dual-Layer Fraud Detection:**
  * 🔴 **Database Triggers:** Hard business rules (e.g., velocity limits, suspended accounts) enforced instantly via PostgreSQL.
  * 🟠 **ML Inference:** Isolation Forest (anomaly detection) + XGBoost classifier running asynchronously.
* **Ultra-Fast Feature Store:** Redis caches behavioral context (geographic velocity, 10-minute transaction counts) for sub-millisecond lookups.
* **Explainable AI (XAI):** Integrated SHAP (SHapley Additive exPlanations) to interpret model decisions.
* **Live Admin Dashboard:** Streamlit UI polling real-time system metrics, ML flags, and database writes.

---

## 🏗️ System Architecture

```text
[ Streamlit UI ] ──(HTTP)──> [ FastAPI Backend ]
                               │          │
               ┌───────────────┘          └──────────────────────┐
      (Instant Write)                                  (Async Risk Eval)
               ▼                                                 ▼
  ┌─────────────────────┐                          ┌──────────────────────────┐
  │     PostgreSQL      │                          │        ML Engine         │
  │  (Core Ledger DB)   │                          │  Isolation Forest + XGB  │
  │                     │                          │                          │
  │ • SQL Triggers      │                          │ • Reads Redis context    │
  │ • Audit Logs        │                          │ • Computes risk score    │
  │ • Partitioning      │                          └──────────┬───────────────┘
  └─────────────────────┘                                     │
                                         (If Fraud → Update DB + Alert UI)

```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
| --- | --- | --- |
| **Frontend / Dashboard** | Streamlit | Interactive UI, real-time polling, analytics charting |
| **Backend API** | FastAPI (Async) | REST endpoints, background task queues |
| **Core Database** | PostgreSQL 16 | ACID ledger, trigger enforcement, table partitioning |
| **Cache / Feature Store** | Redis 7 | Behavioral context, velocity tracking |
| **Data Science / ML** | Scikit-learn, XGBoost, SHAP | Anomaly detection, Supervised classification, Model Explainability |

---

## 📁 Repository Structure

```text
fraud-detection-system/
│
├── backend/                        # FastAPI REST API & ML Inference Engine
│   ├── app/
│   │   ├── api/                    # Route handlers (transactions, admin)
│   │   ├── models/                 # SQLAlchemy ORM & Pydantic schemas
│   │   ├── services/               # Business logic (Ledger & Fraud services)
│   │   └── ml/                     # ML predict wrappers & compiled artifacts
│   ├── Dockerfile
│   └── requirements.txt
│
├── ml_pipeline/                    # Data Science Lab
│   ├── notebooks/
│   │   ├── 01_EDA.ipynb            # Data exploration and imbalance analysis
│   │   ├── 02_Feature_Engineering.ipynb # Generating geo_velocity, z-scores, etc.
│   │   └── 03_Model_Training.ipynb # Model training, SHAP analysis, & artifact export
│   └── data/                       
│
├── streamlit_app/                  # Frontend Dashboard
│   ├── app.py                      
│   ├── Dockerfile                  
│   └── requirements.txt            
│
├── docker/                         # Database Configurations
│   ├── init.sql                    # PostgreSQL schema & triggers
│   └── redis.conf                  
│
├── docker-compose.yml              # Local infrastructure orchestration
└── README.md

```

---

## 🚀 Quick Start Guide (Local Development)

### Prerequisites

* Docker & Docker Compose
* Python 3.11+
* Git

### 1. Start the Databases

Spin up PostgreSQL and Redis in the background:

```bash
docker-compose up -d postgres redis

```

### 2. Train the ML Models

Before the backend can run, you must generate the machine learning artifacts:

1. Open the `ml_pipeline/notebooks/` folder.
2. Run `01_EDA.ipynb` to generate the raw synthetic data.
3. Run `02_Feature_Engineering.ipynb` to engineer behavioral features.
4. Run `03_Model_Training.ipynb` to train the XGBoost/Isolation Forest models and export the `.pkl` files directly into the backend directory.

### 3. Start the Backend API

```bash
cd backend
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

```

*(The interactive API documentation is available at `http://localhost:8000/docs`)*

### 4. Launch the Streamlit Dashboard

Open a new terminal tab:

```bash
cd streamlit_app
python -m venv env
source env/bin/activate
pip install -r requirements.txt
streamlit run app.py

```

*(The dashboard will automatically open at `http://localhost:8501`)*

---

## 🌐 Cloud Deployment

This project's frontend is configured for seamless deployment on **Streamlit Community Cloud**.

1. Push this repository to your public GitHub account.
2. Log into [Streamlit Cloud](https://share.streamlit.io/).
3. Click **New app**.
4. Select your repository, set the branch to `main`, and set the Main file path to `streamlit_app/app.py`.
5. Click **Deploy**.

*Note: For full end-to-end functionality in the cloud, the FastAPI backend and PostgreSQL database must be hosted on a cloud provider (e.g., Render, Heroku, AWS).*

---

## 🧠 Machine Learning & Feature Engineering

The system utilizes a dual-model approach to catch fraud:

1. **Isolation Forest (Unsupervised):** Detects spatial and temporal anomalies without labeled data, acting as an early warning system for novel attack vectors.
2. **XGBoost Classifier (Supervised):** Trained on historical fraud data, weighted heavily to account for extreme class imbalance (typically < 2% fraud rate).

**Engineered Behavioral Features:**

* `geo_velocity`: Distance between the current and last transaction location (catches impossible travel speeds).
* `tx_count_10m`: Volume of transactions attempted in the last 10 minutes (catches automated card testing).
* `amount_z_score`: Standardized deviation from the specific account's historical average spending.

```

```
