"""
Script to update avatar profiles with specific avatar and voice IDs.
"""
import os
import sys
from dotenv import load_dotenv
from flask import Flask
from models import db, AvatarProfile

# Load environment variables
load_dotenv()

def update_avatar_profiles():
    """Update all avatar profiles with specific avatar and voice IDs."""
    print("Updating avatar profiles with correct avatar and voice IDs...")
    
    # Create a minimal Flask app to interact with the database
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    db.init_app(app)
    
    # Valid avatar information based on user-provided IDs
    valid_avatars = {
        # Format: "name": {"avatar_id": "...", "voice_id": "..."},
        "Cody": {
            "avatar_id": "a58345668aa2444c8229923ef67a3e76", 
            "voice_id": "b54cd1be94d848879a0acd2f7138fd3c"
        },
        "Brody": {
            "avatar_id": "4906bbce5e1a49d9936a59403c2c8efe", 
            "voice_id": "05a6438db65442b0bbe31526e5fe8d80"
        },
        "Tim": {
            "avatar_id": "6d34d050b7794ff7801dc5acdee3410e",
            "voice_id": "29e5af5f7dd14b8e81fd87c777c8144b"
        },
        "Kim": {
            "avatar_id": "f36c72625d3246e49cb9896d3a5dd936",
            "voice_id": "2200cbba40b748218a91441bef2b5247"
        },
        "Gloria": {
            "avatar_id": "8b045a95ad714afeb6bfc4cae4b2a290",
            "voice_id": "09a3fec399484100accdeac9d81c6bd8"
        },
        "Emma": {
            "avatar_id": "e411cc565ea44f508a25dc64877f2b0a",
            "voice_id": "e2194035075d452bacfb382c0bd7e2b4"
        },
        "Dianne": {
            "avatar_id": "788c31f6618446a09c6baa8826d45e5a",
            "voice_id": "0d20de82b8c647c19d2c47854f048f3b"
        },
        "Bennett": {
            "avatar_id": "cb12fd55ee78430a97ae2bfa0e8d96c6",
            "voice_id": "e5c759075f7f44f492434bc975e577ff"
        },
        "Jase": {
            "avatar_id": "74a229e044504d558b427f3a3f8e5b78",
            "voice_id": "d67e5d44144b4043a5889e01cdfd1f09"
        },
        "Kumar": {
            "avatar_id": "c743aab5b25c478cb9abefd386e26fae",
            "voice_id": "3c4c9085dc874ca884b03a26c1a187b9"
        },
        "Dominic": {
            "avatar_id": "d4fcad0662de425fbdc650eeed22b22c",
            "voice_id": "04113e764d2148d691651d68357c9e75"
        },
        "Isabella": {
            "avatar_id": "fe6da4814baf47e8857df4baa6352f65",
            "voice_id": "041429df38fa4d46862653c71925a7bb"
        }
    }
    
    # List of profiles we want to update or create
    primary_profiles = ["Cody", "Brody", "Tim", "Kim", "Gloria", "Emma", "Dianne", "Bennett", "Jase", "Kumar", "Dominic", "Isabella"]
    
    with app.app_context():
        # Check if Cody exists as the default avatar
        cody = AvatarProfile.query.filter_by(name="Cody").first()
        
        if not cody:
            # Create Cody as the default
            cody = AvatarProfile(
                name="Cody",
                avatar_id=valid_avatars["Cody"]["avatar_id"],
                voice_id=valid_avatars["Cody"]["voice_id"],
                description="Friendly tech influencer with an engaging personality",
                is_default=True,
                display_order=1
            )
            db.session.add(cody)
            print(f"Created default avatar profile: Cody")
        else:
            # Update Cody with correct IDs
            cody.avatar_id = valid_avatars["Cody"]["avatar_id"]
            cody.voice_id = valid_avatars["Cody"]["voice_id"]
            cody.is_default = True
            cody.display_order = 1
            cody.description = cody.description or "Friendly tech influencer with an engaging personality"
            print(f"Updated default avatar profile: Cody")
        
        # Update or create other primary profiles
        for i, name in enumerate(primary_profiles):
            if name == "Cody":
                continue  # Skip Cody as we already handled it
                
            if name not in valid_avatars:
                print(f"Warning: No valid avatar information for {name}")
                continue
                
            profile = AvatarProfile.query.filter_by(name=name).first()
            
            if profile:
                # Update existing profile
                profile.avatar_id = valid_avatars[name]["avatar_id"]
                profile.voice_id = valid_avatars[name]["voice_id"]
                profile.display_order = i + 1
                print(f"Updated avatar profile: {name}")
            else:
                # Create new profile
                description = get_description_for_avatar(name)
                profile = AvatarProfile(
                    name=name,
                    avatar_id=valid_avatars[name]["avatar_id"],
                    voice_id=valid_avatars[name]["voice_id"],
                    description=description,
                    is_default=False,
                    display_order=i + 1
                )
                db.session.add(profile)
                print(f"Created avatar profile: {name}")
        
        # Commit changes
        db.session.commit()
        print("Avatar profiles updated successfully")
        
        # Display all profiles after update
        all_profiles = AvatarProfile.query.order_by(AvatarProfile.display_order).all()
        print("\nCurrent avatar profiles:")
        for profile in all_profiles:
            print(f"- {profile.name} (ID: {profile.id}, Order: {profile.display_order})")
            print(f"  Avatar ID: {profile.avatar_id}")
            print(f"  Voice ID: {profile.voice_id}")
            print(f"  Default: {'Yes' if profile.is_default else 'No'}")
            print(f"  Description: {profile.description}")
            print()

def get_description_for_avatar(name):
    """Get a suitable description for an avatar."""
    descriptions = {
        "Cody": "Friendly tech influencer with an engaging personality",
        "Gloria": "Confident corporate professional with a warm demeanor",
        "Emma": "Creative content creator with a fashionable style",
        "Tim": "Thoughtful business analyst with a straightforward approach",
        "Isabella": "Energetic lifestyle blogger with a trendy aesthetic",
        "Dominic": "Dynamic marketing strategist with a convincing style",
        "Bennett": "Charismatic educator with a clear communication style",
        "Jase": "Enthusiastic entrepreneur with a motivational approach",
        "Kumar": "Knowledgeable tech specialist with a friendly demeanor",
        "John": "Reliable business professional with a trustworthy presence",
        "Christopher": "Articulate presenter with a polished delivery"
    }
    
    return descriptions.get(name, f"Professional {name} avatar")

if __name__ == "__main__":
    update_avatar_profiles()