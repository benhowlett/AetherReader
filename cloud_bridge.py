import requests
import os
import xml.etree.ElementTree as ET

class CloudBridge:
    def __init__(self, token, provider, instance_url=None):
        self.token = token
        self.provider = provider
        self.instance_url = instance_url

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