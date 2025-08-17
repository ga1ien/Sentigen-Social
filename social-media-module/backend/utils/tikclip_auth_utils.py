"""Utility functions for authentication and authorization."""
from functools import wraps
from flask import request, flash, render_template, session, redirect, url_for
from flask_login import current_user
from forms import LoginForm
from models import AvatarProfile

def login_modal_required(f):
    """
    Custom decorator that shows a login modal instead of redirecting.
    If the user is not logged in, they'll stay on the same page with a modal popup.
    If they log in successfully, they'll be redirected to the originally requested page.
    If they dismiss the modal, they'll remain on the current page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return f(*args, **kwargs)
        else:
            # Store the original page URL in session for post-login redirect
            session['protected_url'] = request.path
            
            # Pass the login form to the template
            login_form = LoginForm()
            
            # Get all available avatar profiles for the homepage
            profiles = AvatarProfile.query.order_by(AvatarProfile.display_order).all()
            default_profile = AvatarProfile.query.filter_by(is_default=True).first()
            if not default_profile and profiles:
                default_profile = profiles[0]
            
            # Make all videos urls accessible
            from models import db
            for profile in profiles:
                # Ensure preview URL is correct
                file_extension = 'mp4' if profile.name in ['Cody', 'Tim', 'Kim', 'Noa'] else 'm4v'
                expected_url = f"/static/videos/{profile.name}.{file_extension}"
                
                # Check if file exists
                file_path = f"static/videos/{profile.name}.{file_extension}"
                import os
                if not os.path.exists(file_path):
                    # Try alternative extension
                    alt_extension = 'm4v' if file_extension == 'mp4' else 'mp4'
                    alt_path = f"static/videos/{profile.name}.{alt_extension}"
                    if os.path.exists(alt_path):
                        expected_url = f"/static/videos/{profile.name}.{alt_extension}"
                        
                # Update if needed
                if profile.preview_url != expected_url:
                    profile.preview_url = expected_url
                    db.session.add(profile)
            
            # Commit any changes
            db.session.commit()
            
            # Return the index page with a flag to show the login modal
            flash('Please log in to access this feature.', 'info')
            return render_template('new_index.html', 
                                  profiles=profiles,
                                  default_profile=default_profile,
                                  login_modal_enabled=True, 
                                  form=login_form, 
                                  login_modal_show=True)
    return decorated_function