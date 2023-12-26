#%%writefile app.py
import io
import streamlit as st
from google.colab import auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Authentication with Google Drive
auth.authenticate_user()
drive_service = build('drive', 'v3')

# Function to check if folder exists with given country name
def check_country_folder_exists(country_name):
    query = f"name='{country_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    response = drive_service.files().list(q=query).execute()
    folders = response.get('files', [])
    return folders

# Function to check if document number folder exists within the country folder
def check_document_folder_exists(country_name, document_number):
    country_folders = check_country_folder_exists(country_name)

    if country_folders:
        country_folder_id = country_folders[0]['id']
        query = f"'{country_folder_id}' in parents and name='{document_number}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        response = drive_service.files().list(q=query).execute()
        folders = response.get('files', [])
        return folders
    else:
        return None

# Function to upload file to document number folder within country folder and document type folder
def upload_to_document_folder(country_name, document_number, document_type, file_upload):
    document_folder_exists = check_document_folder_exists(country_name, document_number)

    if document_folder_exists:
        document_folder_id = document_folder_exists[0]['id']
    else:
        country_folders = check_country_folder_exists(country_name)
        country_folder_id = country_folders[0]['id']
        folder_metadata = {
            'name': document_number,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [country_folder_id]
        }
        created_folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
        document_folder_id = created_folder.get('id')

    # Check if document type folder exists within the document number folder
    document_type_folders = drive_service.files().list(
        q=f"'{document_folder_id}' in parents and name='{document_type}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    ).execute().get('files', [])

    if not document_type_folders:
        document_type_folder_metadata = {
            'name': document_type,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [document_folder_id]
        }
        created_document_type_folder = drive_service.files().create(body=document_type_folder_metadata, fields='id').execute()
        document_type_folder_id = created_document_type_folder.get('id')
    else:
        document_type_folder_id = document_type_folders[0]['id']

    media = MediaIoBaseUpload(io.BytesIO(file_upload.read()), mimetype=file_upload.type)
    file_metadata = {
        'name': file_upload.name,
        'parents': [document_type_folder_id],
    }

    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    st.write(f"File uploaded to Google Drive under {country_name}/{document_number}/{document_type} folder with ID: {uploaded_file.get('id')}")

# Mapping of emails to respective countries
user_credentials = {
    "a@gmail.com": {"password": "password_A", "country": "Country A"},
    "b@gmail.com": {"password": "password_B", "country": "Country B"},
    # Add more email-password-country mappings as needed
}

# Streamlit UI for email, password, and file upload
st.title("Upload Documents to Google Drive")

# Simulated login using email and password as identifier
user_email = st.text_input("Enter Your Email:")
user_password = st.text_input("Enter Your Password:", type="password")

# Check user credentials and display corresponding UI
if user_email in user_credentials:
    stored_password = user_credentials[user_email]["password"]
    country_name = user_credentials[user_email]["country"]

    if user_password == stored_password:
        st.write(f"Welcome, {user_email}! You belong to {country_name}")
        file_upload = st.file_uploader("Upload a file")

        # Using st.form to organize the input fields
        with st.form(key='document_form'):
            document_number = st.text_input("Enter Document Number:", max_chars=5)
            document_type = st.selectbox("Select Document Type:", ['Initial', 'Surveillance 1', 'Surveillance 2', 'Recertification'])
            submit_button = st.form_submit_button(label='Submit')

            # Process uploaded file upon form submission
            if submit_button and document_number and document_type:
                upload_to_document_folder(country_name, document_number, document_type, file_upload)
            elif submit_button and not document_number:
                st.warning("Please enter a document number.")
            elif submit_button and not document_type:
                st.warning("Please select a document type.")
        
    else:
        st.warning("Incorrect password. Please try again.")
else:
    st.warning("You are not authorized to access this application.")
