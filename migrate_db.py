#!/usr/bin/env python3
"""
Database migration script for adding new Player fields
"""
from app import create_app, db
from app.models import Player, RegistrationType
import os

def migrate_database():
    """Add new columns to existing Player table"""
    app = create_app()
    
    with app.app_context():
        # Check if new columns exist
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('player')]
        
        print("Current Player table columns:", columns)
        
        # Add new columns if they don't exist
        new_columns = [
            ('coach', 'VARCHAR(100)'),
            ('registration_type', 'VARCHAR(20)'),
            ('team_members', 'TEXT'),
            ('birthdate', 'DATE')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                print(f"Adding column: {column_name}")
                try:
                    # Use raw SQL to add column
                    db.session.execute(f'ALTER TABLE player ADD COLUMN {column_name} {column_type}')
                    db.session.commit()
                    print(f"Successfully added column: {column_name}")
                except Exception as e:
                    print(f"Error adding column {column_name}: {e}")
                    db.session.rollback()
            else:
                print(f"Column {column_name} already exists")
        
        print("Migration completed!")

if __name__ == '__main__':
    migrate_database()