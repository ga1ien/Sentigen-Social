#!/usr/bin/env python3
"""
Script to copy useful assets from TikClip to the main Sentigen Social app
"""

import os
import shutil
import json
from pathlib import Path

def copy_tikclip_assets():
    """Copy useful assets from TikClip folder to the main app"""
    
    tikclip_path = Path("TikClip")
    if not tikclip_path.exists():
        print("❌ TikClip folder not found")
        return
    
    # Create destination directories
    backend_path = Path("social-media-module/backend")
    frontend_path = Path("frontend")
    
    assets_copied = []
    
    # 1. Copy HeyGen avatar and voice data files
    heygen_files = [
        "heygen_avatars_response.json",
        "heygen_voices_response.json",
        "heygen_avatars_test_response.json"
    ]
    
    for file_name in heygen_files:
        src = tikclip_path / file_name
        if src.exists():
            dst = backend_path / "data" / file_name
            dst.parent.mkdir(exist_ok=True)
            shutil.copy2(src, dst)
            assets_copied.append(f"✅ Copied {file_name} to backend/data/")
    
    # 2. Copy useful Python utilities
    utility_files = [
        "utils.py",
        "auth_utils.py"
    ]
    
    for file_name in utility_files:
        src = tikclip_path / file_name
        if src.exists():
            dst = backend_path / "utils" / f"tikclip_{file_name}"
            shutil.copy2(src, dst)
            assets_copied.append(f"✅ Copied {file_name} to backend/utils/tikclip_{file_name}")
    
    # 3. Copy avatar management scripts (for reference)
    script_files = [
        "fetch_heygen_avatars.py",
        "add_avatar_profiles.py",
        "check_avatar_profiles.py",
        "update_avatar_profiles.py"
    ]
    
    scripts_dir = backend_path / "scripts" / "avatar_management"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    
    for file_name in script_files:
        src = tikclip_path / file_name
        if src.exists():
            dst = scripts_dir / file_name
            shutil.copy2(src, dst)
            assets_copied.append(f"✅ Copied {file_name} to backend/scripts/avatar_management/")
    
    # 4. Copy static assets (images, videos) that might be useful
    static_src = tikclip_path / "static"
    if static_src.exists():
        static_dst = frontend_path / "public" / "avatars"
        static_dst.mkdir(parents=True, exist_ok=True)
        
        # Copy image files
        for ext in ["*.jpg", "*.png", "*.gif"]:
            for img_file in static_src.glob(ext):
                shutil.copy2(img_file, static_dst / img_file.name)
                assets_copied.append(f"✅ Copied {img_file.name} to frontend/public/avatars/")
    
    # 5. Copy attached assets (avatar previews, etc.)
    attached_src = tikclip_path / "attached_assets"
    if attached_src.exists():
        attached_dst = frontend_path / "public" / "avatar_previews"
        attached_dst.mkdir(parents=True, exist_ok=True)
        
        # Copy PNG files (avatar previews)
        for png_file in attached_src.glob("*.png"):
            shutil.copy2(png_file, attached_dst / png_file.name)
            assets_copied.append(f"✅ Copied {png_file.name} to frontend/public/avatar_previews/")
    
    # 6. Extract useful configuration from TikClip
    config_data = {}
    
    # Extract HeyGen configuration
    main_py = tikclip_path / "main.py"
    if main_py.exists():
        with open(main_py, 'r') as f:
            content = f.read()
            
            # Extract HeyGen URLs
            if 'HEYGEN_VIDEO_URL' in content:
                config_data['heygen'] = {
                    'video_url': 'https://api.heygen.com/v2/video/generate',
                    'status_url': 'https://api.heygen.com/v1/video_status.get',
                    'avatars_url': 'https://api.heygen.com/v2/avatars',
                    'voices_url': 'https://api.heygen.com/v2/voices'
                }
            
            # Extract Claude model info
            if 'CLAUDE_MODEL' in content:
                config_data['ai'] = {
                    'claude_model': 'claude-3-5-sonnet-20241022',
                    'script_generation': True
                }
    
    # Save extracted configuration
    if config_data:
        config_file = backend_path / "config" / "tikclip_config.json"
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        assets_copied.append(f"✅ Created configuration file at backend/config/tikclip_config.json")
    
    # 7. Create a summary of what was integrated
    integration_summary = {
        "integration_date": "2024-12-19",
        "source": "TikClip",
        "features_integrated": [
            "Avatar profile management",
            "AI script generation using Claude",
            "HeyGen video creation",
            "Video status tracking",
            "User subscription limits",
            "Avatar usage analytics"
        ],
        "files_copied": len(assets_copied),
        "database_tables_added": [
            "avatar_profiles",
            "script_generations", 
            "video_generations",
            "video_analytics",
            "user_video_limits",
            "avatar_usage_stats"
        ],
        "api_endpoints_added": [
            "/api/avatars/profiles",
            "/api/avatars/scripts/generate",
            "/api/avatars/videos/create",
            "/api/avatars/sync-heygen"
        ],
        "frontend_pages_added": [
            "/dashboard/avatars"
        ]
    }
    
    summary_file = Path("TIKCLIP_INTEGRATION_SUMMARY.json")
    with open(summary_file, 'w') as f:
        json.dump(integration_summary, f, indent=2)
    
    # Print summary
    print("\n🎉 TikClip Integration Complete!")
    print(f"📁 Copied {len(assets_copied)} files/assets")
    print("\n📋 Assets copied:")
    for asset in assets_copied:
        print(f"   {asset}")
    
    print(f"\n📄 Integration summary saved to: {summary_file}")
    print("\n🚀 Next steps:")
    print("   1. Review the copied files and adapt them as needed")
    print("   2. Run the database migration: 004_avatar_system_schema.sql")
    print("   3. Set up HeyGen API credentials")
    print("   4. Test the avatar system endpoints")
    print("   5. Delete the TikClip folder when ready")
    
    return assets_copied

if __name__ == "__main__":
    copy_tikclip_assets()
