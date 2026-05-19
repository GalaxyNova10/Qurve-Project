#!/usr/bin/env python3
"""
Simple script to start Braket worker without shell parsing issues
"""

import uvicorn
from braket_worker import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8011)
