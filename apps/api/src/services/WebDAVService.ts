import { createClient, WebDAVClient, FileStat } from 'webdav';
import { EBookMetadata, NextcloudConfig } from '@aetherreader/shared';

export class WebDAVService {
  private client: WebDAVClient;

  constructor(config: NextcloudConfig) {
    this.client = createClient(config.serverUrl, {
      username: config.username,
      password: config.appPassword,
    });
  }

  async listBooks(folderPath: string): Promise<EBookMetadata[]> {
    const contents = await this.client.getDirectoryContents(folderPath) as FileStat[];
    return contents
      .filter((item) => item.type === 'file' && this.isEBook(item.filename))
      .map((item) => ({
        path: item.filename,
        name: item.basename,
        size: item.size,
        lastModified: item.lastmod,
        mimeType: item.mime,
      }));
  }

  async getFileStream(filePath: string) {
    return this.client.createReadStream(filePath);
  }

  async getFileBuffer(filePath: string) {
    return this.client.getFileContents(filePath);
  }

  private isEBook(filename: string): boolean {
    const extensions = ['.epub', '.pdf', '.mobi', '.azw3'];
    return extensions.some((ext) => filename.toLowerCase().endsWith(ext));
  }
}
