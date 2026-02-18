from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
import platform


class Settings(BaseSettings):
    """Application configuration"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'  # Ignore extra fields
    )
    
    # API Configuration
    APP_NAME: str = "TIA-Sales Personal Loan Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # HuggingFace Configuration - Support multiple env var names
    HF_API_KEY: Optional[str] = None
    HUGGINGFACEHUB_API_TOKEN: Optional[str] = None
    
    HF_MODEL_CLASSIFICATION: str = "mistralai/Mistral-7B-Instruct-v0.3"
    HF_MODEL_EXTRACTION: str = "mistralai/Mistral-7B-Instruct-v0.3"
    HF_MODEL_GENERATION: str = "mistralai/Mistral-7B-Instruct-v0.3"
    HF_API_URL: str = "https://api-inference.huggingface.co/models"
    HF_TIMEOUT: int = 30
    
    # Session Configuration
    SESSION_BACKEND: str = "memory"
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    SESSION_EXPIRY: int = 3600
    
    # OCR Configuration - Windows Auto-detection
    OCR_CONFIDENCE_THRESHOLD: float = 0.6
    TESSERACT_CMD: Optional[str] = None
    SUPPORTED_IMAGE_FORMATS: list = [".jpg", ".jpeg", ".png", ".pdf"]
    MAX_FILE_SIZE_MB: int = 10
    
    # PDF Generation
    OUTPUT_PDF_DIR: str = "./generated_documents"
    COMPANY_NAME: str = "TIA Personal Loans Pvt. Ltd."
    COMPANY_ADDRESS: str = "123 Finance Street, Mumbai, Maharashtra 400001"
    COMPANY_PHONE: str = "+91-22-1234-5678"
    COMPANY_EMAIL: str = "support@tialoans.com"
    
    # Loan Configuration
    MIN_LOAN_AMOUNT: float = 50000.0
    MAX_LOAN_AMOUNT: float = 5000000.0
    
    # Guardrails
    INPUT_MAX_LENGTH: int = 1000
    OFFENSIVE_KEYWORDS: list = ["hack", "bypass", "jailbreak", "ignore instructions"]
    
    def model_post_init(self, __context) -> None:
        """Post-initialization processing"""
        
        # Use HUGGINGFACEHUB_API_TOKEN if HF_API_KEY not set
        if not self.HF_API_KEY and self.HUGGINGFACEHUB_API_TOKEN:
            self.HF_API_KEY = self.HUGGINGFACEHUB_API_TOKEN
        
        # Validate that we have an API key
        if not self.HF_API_KEY:
            raise ValueError("HuggingFace API key is required. Set HF_API_KEY or HUGGINGFACEHUB_API_TOKEN in .env")
        
        # Auto-detect Tesseract on Windows if not set
        if platform.system() == "Windows" and not self.TESSERACT_CMD:
            self.TESSERACT_CMD = self._find_tesseract_windows()
        
        # Create output directory
        os.makedirs(self.OUTPUT_PDF_DIR, exist_ok=True)
    
    def _find_tesseract_windows(self) -> Optional[str]:
        """Auto-detect Tesseract installation on Windows"""
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Tesseract-OCR\tesseract.exe",
        ]
        
        # Check if tesseract is in PATH
        import shutil
        tesseract_path = shutil.which("tesseract")
        if tesseract_path:
            return tesseract_path
        
        # Check common installation paths
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None


settings = Settings()
