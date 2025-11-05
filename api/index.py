"""
Vercel serverless function handler for Flask app
This is the entry point for Vercel serverless functions
"""
from app_ui import app

# Vercel expects the Flask app to be accessible
# The app will be automatically detected by @vercel/python

