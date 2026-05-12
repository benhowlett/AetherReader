import requests, os, io
import xml.etree.ElementTree as ET

class CloudBridge:
    def __init__(self, token, provider, instance_url=None):
        self.token = token
        self.provider = provider
        self.instance_url = instance_url
        self.headers = {'Authorization': f'Bearer {token}'}

    def list_folders(self, path="/"):
        if self.provider == 'nextcloud':
            return self._list_nextcloud(path)
        elif self.provider == 'google':
            return self._list_google(path)
        elif self.provider == 'dropbox':
            return self._list_dropbox(path)

    def _list_nextcloud(self, path):
        # WebDAV uses the PROPFIND method to list files
        url = f"{self.instance_url}/remote.php/dav/files/{os.getenv('NEXTCLOUD_USER')}{path}"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Depth': '1' # Only look in the current folder
        }
        response = requests.request('PROPFIND', url, headers=headers)
        
        # Parse the XML response (Simplified for AetherReader)
        items = []
        root = ET.fromstring(response.content)
        for response in root.findall('{DAV:}response'):
            href = response.find('{DAV:}href').text
            # Basic logic to differentiate folders from files
            is_dir = href.endswith('/')
            items.append({
                "name": href.split('/')[-2 if is_dir else -1],
                "path": href,
                "is_folder": is_dir
            })
        return items[1:] # Skip the first item as it's the folder itself
    
    def get_book_content(self, file_id_or_path):
        """Fetches the actual file data for the reader"""
        if self.provider == 'nextcloud':
            url = f"{self.instance_url}/remote.php/dav/files/{os.getenv('NEXTCLOUD_USER')}{file_id_or_path}"
            return requests.get(url, headers=self.headers, stream=True)

        elif self.provider == 'google':
            # Google uses File IDs rather than paths
            url = f"https://www.googleapis.com/drive/v3/files/{file_id_or_path}?alt=media"
            return requests.get(url, headers=self.headers, stream=True)

        elif self.provider == 'dropbox':
            # Dropbox uses a separate content URL for downloading
            url = "https://content.dropboxapi.com/2/files/download"
            headers = {
                **self.headers,
                'Dropbox-API-Arg': json.dumps({"path": file_id_or_path})
            }
            return requests.post(url, headers=headers, stream=True)
        
    def list_files(self, folder_id_or_path):
        """Lists only folders (for selection) or only books (for the library)"""
        if self.provider == 'google':
            # Query for items inside the specific folder that are either folders or ebooks
            query = f"'{folder_id_or_path}' in parents and (mimeType = 'application/vnd.google-apps.folder' or name contains '.epub' or name contains '.pdf')"
            url = f"https://www.googleapis.com/drive/v3/files?q={query}&fields=files(id, name, mimeType)"
            res = requests.get(url, headers=self.headers).json()
            return [{
                "name": f['name'],
                "path": f['id'],
                "is_folder": f['mimeType'] == 'application/vnd.google-apps.folder'
            } for f in res.get('files', [])]

        elif self.provider == 'dropbox':
            url = "https://api.dropboxapi.com/2/files/list_folder"
            data = {"path": "" if folder_id_or_path == "/" else folder_id_or_path}
            res = requests.post(url, headers=self.headers, json=data).json()
            return [{
                "name": f['name'],
                "path": f['path_lower'],
                "is_folder": f['.tag'] == 'folder'
            } for f in res.get('entries', [])]
    