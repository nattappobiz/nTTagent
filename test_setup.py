#!/usr/bin/env python3
"""Test script to verify that the setup is working correctly."""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all necessary modules can be imported."""
    try:
        # Test FastAPI import
        from fastapi import FastAPI
        print("[PASS] FastAPI import successful")
        
        # Test Pydantic import
        from pydantic import BaseModel
        print("[PASS] Pydantic import successful")
        
        # Test schema imports
        from app.schemas.citizen import CitizenBase, CitizenCreate, CitizenUpdate, CitizenOut
        print("[PASS] Schema imports successful")
        
        # Test model imports
        from app.models.models import Citizen, Batch, FileStatus
        print("[PASS] Model imports successful")
        
        # Test service imports
        from app.services.utils import parse_thai_date, validate_thai_cid
        print("[PASS] Service imports successful")
        
        # Test route imports
        from app.routes.citizens import router
        print("[PASS] Route imports successful")
        
        print("\nAll imports successful! The setup is working correctly.")
        return True
        
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False

if __name__ == "__main__":
    if test_imports():
        print("\nSetup verification passed!")
        sys.exit(0)
    else:
        print("\nSetup verification failed!")
        sys.exit(1)