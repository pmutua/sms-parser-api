import os
import re
from datetime import datetime
import logging
from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import GoogleAuthError

# Set up logging
logger = logging.getLogger(__name__)

class GoogleDriveClient:
    """Google Drive client for retrieving SMS backup files."""

    def __init__(self):
        """Initialize the Google Drive client with authenticated credentials."""
        self.service = self._authenticate()

    def _authenticate(self):
        """Handles authentication and returns the Google Drive service."""
        credentials = self._get_credentials()
        if not credentials:
            logger.error("Authentication failed. Credentials are missing.")
            return None

        try:
            service = build("drive", "v3", credentials=credentials)
            logger.info("Service created successfully.")
            return service
        except HttpError as error:
            logger.error(f"Google Drive API error: {error}")
            return None

    def _get_credentials(self):
        """Retrieves stored credentials or generates new ones."""
        # Check if we're in production environment
        if os.environ.get('ENVIRONMENT') == 'PROD':
            logger.info("Using production credentials from environment variable")
            
            # Create credentials directory if it doesn't exist
            credentials_dir = os.path.dirname(settings.GOOGLE_CREDENTIALS_PATH)
            os.makedirs(credentials_dir, exist_ok=True)
            
            # Get credentials from environment variable
            credentials_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            
            if credentials_json:
                # Write credentials to the expected file location
                try:
                    with open(settings.GOOGLE_CREDENTIALS_PATH, "w") as f:
                        f.write(credentials_json)
                    logger.info(f"Successfully wrote credentials to {settings.GOOGLE_CREDENTIALS_PATH}")
                except Exception as e:
                    logger.error(f"Failed to write credentials file: {e}")
                    return None
            else:
                logger.error("GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not found")
                return None
                
        # Check if credentials file exists regardless of environment
        if not os.path.exists(settings.GOOGLE_CREDENTIALS_PATH):
            logger.error(f"Credentials file not found: {settings.GOOGLE_CREDENTIALS_PATH}")
            return None

        try:
            creds = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_CREDENTIALS_PATH,
                scopes=settings.GOOGLE_DRIVE_SCOPES
            )
            return creds
        except GoogleAuthError as e:
            logger.error(f"Google authentication error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while retrieving credentials: {e}")
        
        return None

    @staticmethod
    def _parse_timestamp(filename):
        """Extracts timestamp from filename."""
        match = re.match(r'sms-(\d{14})\.xml', filename)
        return datetime.strptime(match.group(1), '%Y%m%d%H%M%S') if match else None

    def get_latest_sms_backup(self):
        """Fetches the latest SMS backup file from Google Drive."""
        if not self.service:
            logger.error("Google Drive service is not initialized.")
            raise RuntimeError("Google Drive service is not initialized")

        try:
            # Query for the most recent files containing 'sms-' in the name and '.xml' extension
            response = self.service.files().list(
                q="name contains 'sms-' and name contains '.xml'",
                fields="files(id, name, createdTime)",
                orderBy="createdTime desc",
                pageSize=10  # Limiting to top 10 files
            ).execute()

            files = response.get('files', [])
            if not files:
                logger.warning("No SMS backup files found.")
                return None

            # Filter files with valid timestamps
            valid_files = [(self._parse_timestamp(f['name']), f) for f in files if self._parse_timestamp(f['name'])]
            
            if not valid_files:
                logger.warning("No valid SMS backup files with timestamp found.")
                return None

            # Get the latest valid file
            latest_file = max(valid_files, key=lambda x: x[0])

            # Retrieve the file content
            file_content = self.service.files().get_media(fileId=latest_file[1]['id']).execute()
            logger.info(f"Retrieved file: {latest_file[1]['name']}")
            return file_content

        except HttpError as error:
            logger.error(f"Error retrieving SMS backups: {error}")
            return None
        except Exception as error:
            logger.error(f"Unexpected error: {error}")
            return None