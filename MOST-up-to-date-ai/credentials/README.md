# Credentials Setup

This directory should contain your Google Cloud service account credentials file.

## Setup Instructions

1. Create a service account in the Google Cloud Console:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Add the "Google Sheets API" and "Google Drive API" permissions
   - Create a key (JSON format) and download it

2. Rename the downloaded file to `service_account_key.json` and place it in this directory.

3. The file should not be committed to version control (it's in .gitignore).

4. The `service_account_key.json.example` file shows the expected structure of the credentials file.

## Security Note

- Never commit actual credentials to version control
- Keep your service account key file secure
- Rotate keys regularly
- Restrict permissions to only what's necessary
