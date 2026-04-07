export interface EBookMetadata {
  path: string;
  name: string;
  size: number;
  lastModified: string;
  mimeType?: string;
}

export interface ReadingProgress {
  bookPath: string;
  position: string; // CFI for EPUB, Page Number for PDF
  lastReadAt: number;
}

export interface NextcloudConfig {
  serverUrl: string;
  username: string;
  appPassword: string;
}
