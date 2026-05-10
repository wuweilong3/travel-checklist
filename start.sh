#!/bin/bash
cd backend
pip install -r requirements.txt
uvicorn api.routes:app --host 0.0.0.0 --port $PORT