from .google_drive import GoogleDriveClient

class CloudServiceFactory:
    _providers = {
        'google': GoogleDriveClient,
        #TODO 'dropbox': DropboxClient, # Not implemented
        #TODO 'onedrive': OneDriveClient  # Not implemented
    }

    @staticmethod
    def create(provider):
        if provider in CloudServiceFactory._providers:
            return CloudServiceFactory._providers[provider]()
        raise ValueError(f"Unsupported provider: {provider}")
