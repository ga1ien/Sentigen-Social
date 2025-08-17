"""Utility functions for TikClip.ai."""
import os
import logging
from flask import request

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_site_domain():
    """
    Get the correct domain for the site, prioritizing:
    1. The actual host from the request (tikclip.ai)
    2. The EXTERNAL_DOMAIN environment variable if on Replit
    3. The request host
    
    This ensures Stripe callbacks go to the correct domain whether in development or production.
    """
    # First, get the current domain from the request
    domain = request.host_url.rstrip('/')
    
    # If we're on a Replit domain and have an external domain set
    if 'replit' in domain and os.environ.get('EXTERNAL_DOMAIN'):
        # Use tikclip.ai or whatever domain is set
        domain = f"https://{os.environ.get('EXTERNAL_DOMAIN')}"
        logger.debug(f"Using EXTERNAL_DOMAIN: {domain}")
    elif os.environ.get('EXTERNAL_DOMAIN'):
        # If no domain is detected but EXTERNAL_DOMAIN is set, still prefer it
        # This handles cases where the request domain doesn't match the desired callback domain
        domain = f"https://{os.environ.get('EXTERNAL_DOMAIN')}"
        logger.debug(f"Falling back to EXTERNAL_DOMAIN: {domain}")
    else:
        logger.debug(f"Using request host domain: {domain}")
    
    return domain