"""
Script to check avatar profiles in the database.
"""
import os
import logging
from dotenv import load_dotenv
from flask import Flask
from models import db, AvatarProfile

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create a minimal Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
db.init_app(app)

def check_avatar_profiles():
    """Check avatar profiles in the database."""
    with app.app_context():
        profiles = AvatarProfile.query.all()
        
        if not profiles:
            logger.warning("No avatar profiles found in the database")
            return
        
        logger.info(f"Found {len(profiles)} avatar profiles")
        
        for profile in profiles:
            logger.info(f"ID: {profile.id}, Name: {profile.name}, "
                       f"Avatar ID: {profile.avatar_id}, "
                       f"Voice ID: {profile.voice_id}, "
                       f"Type: {getattr(profile, 'avatar_type', 'Unknown')}, "
                       f"Preview URL: {profile.preview_url}")

if __name__ == "__main__":
    check_avatar_profiles()