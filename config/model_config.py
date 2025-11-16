"""
AI Model Configuration
"""
import google.generativeai as genai
from .settings import settings

# Configure Google AI
genai.configure(api_key=settings.GOOGLE_API_KEY)


class ModelConfig:
    """AI Model configurations"""
    
    @staticmethod
    def get_embedding_model():
        """Get embedding model name"""
        return settings.EMBEDDING_MODEL
    
    @staticmethod
    def get_summary_model():
        """Get configured summary generation model"""
        return genai.GenerativeModel(
            settings.SUMMARY_MODEL,
            generation_config={
                "temperature": settings.SUMMARY_TEMPERATURE,
                "top_p": 0.95,
            }
        )
    
    @staticmethod
    def get_qa_model():
        """Get configured Q&A model"""
        return genai.GenerativeModel(
            settings.QA_MODEL,
            generation_config={
                "temperature": settings.QA_TEMPERATURE,
                "top_p": 0.9,
            }
        )
    
    @staticmethod
    def get_streaming_model(temperature: float = 0.7):
        """Get model configured for streaming"""
        return genai.GenerativeModel(
            settings.QA_MODEL,
            generation_config={
                "temperature": temperature,
                "top_p": 0.95,
            }
        )


# Singleton instances
model_config = ModelConfig()