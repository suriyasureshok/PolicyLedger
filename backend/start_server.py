#!/usr/bin/env python3
"""
Start the PolicyLedger Backend Server

This script starts the FastAPI server with WebSocket support for real-time training.
"""

import uvicorn
import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 Starting PolicyLedger Backend Server")
    print("=" * 80)
    print("📡 REST API: http://localhost:8000")
    print("🔌 WebSocket: ws://localhost:8000/ws/train/{agent_id}")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 80)
    print()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
