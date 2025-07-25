from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import os.path
import io
import pickle
import zipfile

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_google_drive_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def upload_file(file, branch, model_name):
    """
    Upload a file to Google Drive.
    Returns a dictionary containing the file's ID and webViewLink
    """
    try:
        service = get_google_drive_service()
        
        # Create folder structure if it doesn't exist
        branch_folder_id = get_or_create_folder(service, branch)
        model_folder_id = get_or_create_folder(service, model_name, parent_id=branch_folder_id)
        
        # Prepare the file metadata
        file_metadata = {
            'name': file.filename,
            'parents': [model_folder_id]
        }
        
        # Convert the file to BytesIO object
        file_content = file.read()
        file_io = io.BytesIO(file_content)
        
        # Upload the file
        media = MediaIoBaseUpload(
            file_io,
            mimetype=file.content_type,
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        return {
            'success': True,
            'url': file.get('webViewLink'),
            'public_id': file.get('id')
        }
        
    except Exception as e:
        print(f"Error uploading to Google Drive: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_or_create_folder(service, folder_name, parent_id=None):
    """
    Get or create a folder in Google Drive
    Returns the folder ID
    """
    # Search for existing folder
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    
    items = results.get('files', [])
    
    # Return existing folder ID if found
    if items:
        return items[0]['id']
    
    # Create new folder if not found
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_id:
        folder_metadata['parents'] = [parent_id]
    
    folder = service.files().create(
        body=folder_metadata,
        fields='id'
    ).execute()
    
    return folder.get('id')

def delete_file(file_id):
    """
    Delete a file from Google Drive
    """
    try:
        service = get_google_drive_service()
        service.files().delete(fileId=file_id).execute()
        return {'success': True}
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def create_zip_from_urls(files_info, zip_path):
    """
    Download files from Google Drive and create a ZIP file
    """
    try:
        service = get_google_drive_service()
        
        # Create a new ZIP file
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_info in files_info:
                file_id = file_info['public_id']
                filename = file_info['filename']
                branch = file_info['branch']
                model_name = file_info['model_name']
                
                # Download file from Google Drive
                request = service.files().get_media(fileId=file_id)
                file_content = io.BytesIO()
                downloader = MediaIoBaseDownload(file_content, request)
                
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                
                # Add file to ZIP
                file_content.seek(0)
                zip_path = f"{branch}/{model_name}/{filename}"
                zipf.writestr(zip_path, file_content.getvalue())
        
        return True
        
    except Exception as e:
        print(f"Error creating ZIP file: {str(e)}")
        return False
