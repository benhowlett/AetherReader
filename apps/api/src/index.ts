import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import { WebDAVService } from './services/WebDAVService.js';
import { ProgressService } from './services/ProgressService.js';
import { NextcloudConfig, ReadingProgress } from '@aetherreader/shared';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = process.env.PORT || 3001;
const dbPath = process.env.DB_PATH || 'sqlite.db';

app.use(cors());
app.use(express.json());

const ncConfig: NextcloudConfig = {
  serverUrl: process.env.NEXTCLOUD_URL || '',
  username: process.env.NEXTCLOUD_USERNAME || '',
  appPassword: process.env.NEXTCLOUD_PASSWORD || '',
};

const webdav = new WebDAVService(ncConfig);
const progressService = new ProgressService(dbPath);

// API routes
app.get('/api/books', async (req, res) => {
  try {
    const folder = (req.query.folder as string) || '/';
    const books = await webdav.listBooks(folder);
    res.json(books);
  } catch (error) {
    console.error('Error listing books:', error);
    res.status(500).json({ error: 'Failed to list books' });
  }
});

app.get('/api/books/stream', async (req, res) => {
  try {
    const path = req.query.path as string;
    if (!path) return res.status(400).json({ error: 'Path is required' });
    
    const stream = await webdav.getFileStream(path);
    stream.pipe(res);
  } catch (error) {
    console.error('Error streaming book:', error);
    res.status(500).json({ error: 'Failed to stream book' });
  }
});

app.get('/api/progress', async (req, res) => {
  try {
    const path = req.query.path as string;
    if (!path) return res.status(400).json({ error: 'Path is required' });
    
    const progress = await progressService.getProgress(path);
    res.json(progress || null);
  } catch (error) {
    console.error('Error getting progress:', error);
    res.status(500).json({ error: 'Failed to get progress' });
  }
});

app.post('/api/progress', async (req, res) => {
  try {
    const item = req.body as ReadingProgress;
    await progressService.saveProgress(item);
    res.json({ success: true });
  } catch (error) {
    console.error('Error saving progress:', error);
    res.status(500).json({ error: 'Failed to save progress' });
  }
});

// Serve frontend in production
if (process.env.NODE_ENV === 'production') {
  // Path to built frontend (assuming app is built into dist/)
  const staticPath = path.join(__dirname, '../../web/dist');
  app.use(express.static(staticPath));
  
  // SPA fallback
  app.get('*', (req, res) => {
    res.sendFile(path.join(staticPath, 'index.html'));
  });
}

app.listen(port, () => {
  console.log(`API listening at http://localhost:${port}`);
});
