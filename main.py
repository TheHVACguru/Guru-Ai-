#!/usr/bin/env python3
"""
Main entry point for the Voice Assistant API
Optimized for deployment on Replit and Cloud Run
"""

import os
import uvicorn
from simple_api import app

def main():
    """Main function to start the Voice Assistant API server"""
    # Get port from environment (Cloud Run sets PORT automatically)
    port = int(os.environ.get("PORT", 5000))
    
    # Run the server
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()