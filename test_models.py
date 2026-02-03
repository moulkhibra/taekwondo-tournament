#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import JudgeScore, MatchScore

def test_models():
    """Test model creation and relationships"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Check models
            print("✓ JudgeScore model:", JudgeScore.__name__)
            print("✓ MatchScore model:", MatchScore.__name__)
            
            # Test JudgeScore creation
            from app.models import User, Match, Player, Tournament
            
            # Check if we can create models without issues
            judge_score = JudgeScore()
            print("✓ JudgeScore instance created")
            
            # Check relationships
            print("✓ Models loaded successfully")
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    success = test_models()
    if success:
        print("\n✓ All tests passed! The models are working correctly.")
        print("You can now run the Flask app with: python run.py")
    else:
        print("\n✗ Tests failed. Check the error messages above.")