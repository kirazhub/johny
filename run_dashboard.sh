#!/bin/bash
cd /Users/kiraz/Projects/johny
source venv/bin/activate
streamlit run johny_dashboard.py --server.port 8503 --server.headless true
