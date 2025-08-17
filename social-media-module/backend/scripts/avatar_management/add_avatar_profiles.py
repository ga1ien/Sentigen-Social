"""
Database migration script to add the avatar_profiles table and insert Cody's profile.
"""
import os
import sys
import datetime
import logging
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, MetaData, Table, ForeignKey, create_engine
from sqlalchemy.sql import text
from dotenv import load_dotenv
from flask import Flask
from main import app
from models import db, AvatarProfile

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_avatar_profiles():
    """Run database migrations to add avatar profiles table and insert Cody's profile."""
    with app.app_context():
        try:
            # Create the tables first
            db.create_all()
            logger.info("Database tables created or confirmed to exist")
            
            # Check if any avatar profiles exist 
            existing_profiles = AvatarProfile.query.count()
            
            if existing_profiles == 0:
                logger.info("No avatar profiles found. Adding Cody's profile...")
                
                # Create default profile for Cody
                cody_profile = AvatarProfile(
                    name="Cody in Car",
                    avatar_id="a58345668aa2444c8229923ef67a3e76",  # Cody's avatar ID
                    voice_id="b54cd1be94d848879a0acd2f7138fd3c",   # Cody's authentic voice ID
                    display_order=0,
                    is_default=True,
                    description="Cody talking from his car with his authentic voice"
                )
                
                # Add and commit
                db.session.add(cody_profile)
                db.session.commit()
                logger.info(f"Added Cody's profile with ID: {cody_profile.id}")
                
                # Add a second profile option as a variation
                cody_profile2 = AvatarProfile(
                    name="Cody (Higher Pitch)",
                    avatar_id="a58345668aa2444c8229923ef67a3e76",  # Cody's avatar ID
                    voice_id="b54cd1be94d848879a0acd2f7138fd3c",   # Cody's authentic voice ID
                    display_order=1,
                    is_default=False,
                    description="Cody with a slightly higher-pitched voice for more energetic videos"
                )
                
                # Add and commit
                db.session.add(cody_profile2)
                db.session.commit()
                logger.info(f"Added second Cody profile with ID: {cody_profile2.id}")
                
                return True
            else:
                logger.info(f"Found {existing_profiles} existing avatar profiles. No migration needed.")
                return False
                
        except Exception as e:
            logger.error(f"Error during avatar profiles migration: {str(e)}")
            return False

if __name__ == "__main__":
    # Execute the migration
    result = migrate_avatar_profiles()
    
    if result:
        print("✅ Avatar profiles migration completed successfully")
        sys.exit(0)
    else:
        print("⚠️ No migration needed or an error occurred")
        sys.exit(1)