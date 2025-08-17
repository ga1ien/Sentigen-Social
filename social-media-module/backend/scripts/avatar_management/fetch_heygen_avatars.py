"""
Script to fetch avatar information from HeyGen API and update preview URLs.
"""
import os
import sys
import json
import logging
import requests
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

def get_heygen_headers():
    """Get the appropriate headers for HeyGen API."""
    # Get HeyGen API key from environment
    heygen_api_key = os.environ.get("HEYGEN_API_KEY")
    
    if not heygen_api_key:
        logger.error("HEYGEN_API_KEY environment variable is not set")
        sys.exit("HEYGEN_API_KEY environment variable must be set")
    
    # Return headers with X-Api-Key (preferred method)
    return {
        "X-Api-Key": heygen_api_key,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def fetch_heygen_avatars():
    """Fetch avatars from HeyGen API and update our database."""
    try:
        headers = get_heygen_headers()
        HEYGEN_AVATARS_URL = "https://api.heygen.com/v2/avatars"
        
        # Make request to HeyGen API
        response = requests.get(HEYGEN_AVATARS_URL, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Save response to file for reference
        with open("heygen_avatars_response.json", "w") as f:
            json.dump(data, f, indent=2)
            
        # Get both standard avatars and talking photos
        avatars = data.get('data', {}).get('avatars', [])
        talking_photos = data.get('data', {}).get('talking_photos', [])
            
        logger.info(f"Fetched {len(avatars)} avatars and {len(talking_photos)} talking photos from HeyGen API")
        
        # Process and update our profiles
        with app.app_context():
            update_profiles_with_avatar_data(avatars, talking_photos)
            
    except Exception as e:
        logger.error(f"Error fetching HeyGen avatars: {str(e)}")
        
def update_profiles_with_avatar_data(avatars, talking_photos):
    """Update our avatar profiles with data from HeyGen API."""
    # Process standard avatars
    avatar_map = {avatar.get('avatar_id', ''): avatar for avatar in avatars}
    
    # Create a dictionary mapping talking_photo_id to talking photo data for quick lookup
    talking_photo_map = {photo.get('talking_photo_id', ''): photo for photo in talking_photos}
    
    logger.info(f"Processing {len(avatars)} avatars and {len(talking_photos)} talking photos")
    
    # Get all our profiles
    profiles = AvatarProfile.query.all()
    
    updated_count = 0
    for profile in profiles:
        # First try to find it as a standard avatar
        avatar_data = avatar_map.get(profile.avatar_id)
        
        # If not found, try to find it as a talking photo
        if not avatar_data:
            avatar_data = talking_photo_map.get(profile.avatar_id)
        
        # If we found it and it has a preview_video_url
        if avatar_data and avatar_data.get('preview_video_url'):
            # Update the preview URL with the direct video URL
            profile.preview_url = avatar_data['preview_video_url']
            logger.info(f"Updated {profile.name} with direct preview video URL from standard avatar")
            updated_count += 1
        # For talking photos, there might not be a preview_video_url but a preview_image_url
        elif avatar_data and avatar_data.get('preview_image_url'):
            # Use the image URL if no video URL is available
            profile.preview_url = avatar_data['preview_image_url']
            logger.info(f"Updated {profile.name} with preview image URL from talking photo")
            updated_count += 1
    
    # Commit changes if any profiles were updated
    if updated_count > 0:
        db.session.commit()
        logger.info(f"Updated {updated_count} profiles with direct preview video URLs")
    else:
        logger.warning("No matching avatars found to update preview URLs")

if __name__ == "__main__":
    fetch_heygen_avatars()