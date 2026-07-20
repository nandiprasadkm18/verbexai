from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://verbex:yourpassword@localhost:5432/verbex"
    DB_PASSWORD: str = "yourpassword"

    # JWT
    SECRET_KEY: str = "your-random-string-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


    # OpenAI
    OPENAI_API_KEY: str = ""



    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # GitHub
    GITHUB_TOKEN: str = ""
    GITHUB_REPO_OWNER: str = ""
    GITHUB_REPO_NAME: str = ""

    GITHUB_TOKEN1: str = ""
    GITHUB_REPO_OWNER1: str = ""
    GITHUB_REPO_NAME1: str = ""

    GITHUB_TOKEN2: str = ""
    GITHUB_REPO_OWNER2: str = ""
    GITHUB_REPO_NAME2: str = ""

    GITHUB_TOKEN3: str = ""
    GITHUB_REPO_OWNER3: str = ""
    GITHUB_REPO_NAME3: str = ""

    # Jira
    JIRA_EMAIL: str = ""
    JIRA_API_TOKEN: str = ""
    JIRA_DOMAIN: str = ""
    JIRA_PROJECT_KEY: str = ""

    JIRA_EMAIL1: str = ""
    JIRA_API_TOKEN1: str = ""
    JIRA_DOMAIN1: str = ""
    JIRA_PROJECT_KEY1: str = ""

    JIRA_EMAIL2: str = ""
    JIRA_API_TOKEN2: str = ""
    JIRA_DOMAIN2: str = ""
    JIRA_PROJECT_KEY2: str = ""

    JIRA_EMAIL3: str = ""
    JIRA_API_TOKEN3: str = ""
    JIRA_DOMAIN3: str = ""
    JIRA_PROJECT_KEY3: str = ""

    # App Config
    MAX_AUDIO_SIZE_MB: int = 500
    CONFIDENCE_AUTO_APPROVE: float = 0.75
    CONFIDENCE_REVIEW_THRESHOLD: float = 0.50

    def get_employee_credentials(self, emp_id: str | None) -> dict:
        """Returns the specific credentials for an employee"""
        # Default (Suman / EMP001)
        creds = {
            "gh_token": self.GITHUB_TOKEN,
            "gh_owner": self.GITHUB_REPO_OWNER,
            "gh_repo": self.GITHUB_REPO_NAME,
            "jira_email": self.JIRA_EMAIL,
            "jira_token": self.JIRA_API_TOKEN,
            "jira_domain": self.JIRA_DOMAIN,
            "jira_project": self.JIRA_PROJECT_KEY,
        }

        if emp_id == "EMP002": # Likhith
            creds.update({
                "gh_token": self.GITHUB_TOKEN1,
                "gh_owner": self.GITHUB_REPO_OWNER1,
                "gh_repo": self.GITHUB_REPO_NAME1,
                "jira_email": self.JIRA_EMAIL2,
                "jira_token": self.JIRA_API_TOKEN2,
                "jira_domain": self.JIRA_DOMAIN2,
                "jira_project": self.JIRA_PROJECT_KEY2,
            })
        elif emp_id == "EMP003": # Hemanth
            creds.update({
                "gh_token": self.GITHUB_TOKEN2,
                "gh_owner": self.GITHUB_REPO_OWNER2,
                "gh_repo": self.GITHUB_REPO_NAME2,
                "jira_email": self.JIRA_EMAIL3,
                "jira_token": self.JIRA_API_TOKEN3,
                "jira_domain": self.JIRA_DOMAIN3,
                "jira_project": self.JIRA_PROJECT_KEY3,
            })
        elif emp_id == "EMP004": # Nandi
            creds.update({
                "gh_token": self.GITHUB_TOKEN3,
                "gh_owner": self.GITHUB_REPO_OWNER3,
                "gh_repo": self.GITHUB_REPO_NAME3,
                "jira_email": self.JIRA_EMAIL1,
                "jira_token": self.JIRA_API_TOKEN1,
                "jira_domain": self.JIRA_DOMAIN1,
                "jira_project": self.JIRA_PROJECT_KEY1,
            })
        
        return creds

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure storage directory exists
os.makedirs("storage/audio", exist_ok=True)
