#!/bin/bash

echo "🚀 Starting FastAPI backend..."
uvicorn app:app --host 0.0.0.0 --port 8000 &
backend_pid=$!

echo "⏳ Waiting 300 seconds (5 minutes) for backend to start..."
sleep 300

echo "🚀 Starting Streamlit frontend..."
streamlit run frontend.py --server.port 8501 --server.address 0.0.0.0

# Optional: Cleanup
kill $backend_pid
