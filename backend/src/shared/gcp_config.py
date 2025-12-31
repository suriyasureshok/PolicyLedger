"""
Google Cloud Platform Configuration
Handles Firestore, Vertex AI, and Gemini API initialization
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GCPConfig:
    """Google Cloud Platform configuration"""
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "policyledger-dev")
        self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY"))
        self.firestore_database = os.getenv("FIRESTORE_DATABASE", "(default)")
        self.enable_gcp = os.getenv("ENABLE_GCP", "false").lower() == "true"
        
    @property
    def is_configured(self) -> bool:
        """Check if GCP is properly configured"""
        return self.enable_gcp and self.project_id is not None
    
    @property
    def firestore_enabled(self) -> bool:
        """Check if Firestore is enabled"""
        return self.is_configured
    
    @property
    def vertex_ai_enabled(self) -> bool:
        """Check if Vertex AI is enabled"""
        return self.is_configured
    
    @property
    def gemini_enabled(self) -> bool:
        """Check if Gemini API is configured"""
        return self.gemini_api_key is not None


# Global configuration instance
gcp_config = GCPConfig()


def get_firestore_client():
    """Get Firestore client if available"""
    if not gcp_config.firestore_enabled:
        return None
    
    try:
        from google.cloud import firestore
        return firestore.Client(
            project=gcp_config.project_id,
            database=gcp_config.firestore_database
        )
    except Exception as e:
        print(f"Warning: Failed to initialize Firestore client: {e}")
        return None


def get_vertex_ai_client():
    """Get Vertex AI client if available"""
    if not gcp_config.vertex_ai_enabled:
        return None
    
    try:
        from google.cloud import aiplatform
        aiplatform.init(
            project=gcp_config.project_id,
            location=gcp_config.location
        )
        return aiplatform
    except Exception as e:
        print(f"Warning: Failed to initialize Vertex AI client: {e}")
        return None


def get_gemini_client():
    """Get Gemini API client if available"""
    if not gcp_config.gemini_enabled:
        return None
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=gcp_config.gemini_api_key)
        return genai
    except Exception as e:
        print(f"Warning: Failed to initialize Gemini client: {e}")
        return None
