### Important
* Human-in-the-loop is not activate/test
* RAG is not activate/test
* Create env file
```
.env

# LLM Configuration
GEMINI_KEY=
MODEL_CHOICE=gemini-2.0-flash

# Database Configuration
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
DB_NAME=

# Database Pool Settings (optional)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_ECHO=true

# MongoDB
MONGODB_ATLAS_CLUSTER_URI=
MONGODB_DB_NAME=
MONGODB_COLLECTION_NAME=
```
* Create postgresql DB
* Create Mongo DB
---
### How to test run
* Create venv
```
python -m venv myvenv
```
* Activate venv
```
myvenv\Scripts\activate
```
* Install dependencies
```
pip install -r requirements.txt
```
* Run endpoint
```
uvicorn api.api_2:app --reload
```
* Run streamlit
```
streamlit run streamlit_app.py
```