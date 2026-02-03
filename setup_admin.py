#!/usr/bin/env python3
"""
Setup script for creating initial admin user
Run this script to create the first administrator account
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, UserRole

def create_admin_user():
    """Create initial admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(role=UserRole.ADMIN).first()
        if admin:
            print(f"Admin user already exists: {admin.username}")
            return
        
        # Get admin details
        print("Creating initial admin user...")
        username = input("Enter admin username: ").strip()
        email = input("Enter admin email: ").strip()
        full_name = input("Enter admin full name: ").strip()
        password = input("Enter admin password: ").strip()
        
        # Validate input
        if not all([username, email, full_name, password]):
            print("All fields are required!")
            return
        
        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=UserRole.ADMIN
        )
        admin_user.set_password(password)
        
        db.session.add(admin_user)
        db.session.commit()
        
        print(f"\n✅ Admin user '{username}' created successfully!")
        print(f"   Email: {email}")
        print(f"   Role: Administrator")
        print(f"\nYou can now log in at: http://localhost:5000/auth/login")

if __name__ == '__main__':
    create_admin_user()