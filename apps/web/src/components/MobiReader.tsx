import { useState, useEffect } from 'react';
import axios from 'axios';
import { MobiParser } from '@lingo-reader/mobi-parser';

interface MobiReaderProps {
  url: string;
  initialPosition?: string | null; // Placeholder for future scroll/index tracking
  onProgressChange: (position: string) => void;
}

export function MobiReader({ url, initialPosition, onProgressChange }: MobiReaderProps) {
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMobi() {
      try {
        setLoading(true);
        // Fetch as arraybuffer
        const response = await axios.get(url, { responseType: 'arraybuffer' });
        const buffer = response.data;
        
        const parser = new MobiParser(buffer);
        const html = await parser.parse();
        
        // The parser returns a HTML string of the book content
        setContent(html);
        setLoading(false);
      } catch (err) {
        console.error('Failed to parse MOBI:', err);
        setError('Failed to load MOBI file. This format might be DRM protected or corrupted.');
        setLoading(false);
      }
    }

    loadMobi();
  }, [url]);

  if (loading) return <div className="mobi-reader-loading">Parsing MOBI content...</div>;
  if (error) return <div className="mobi-reader-error">{error}</div>;

  return (
    <div className="mobi-reader">
      <div 
        className="mobi-content" 
        dangerouslySetInnerHTML={{ __html: content }} 
        onScroll={(e) => {
          // Simple scroll-based progress could be added here
          // const progress = e.currentTarget.scrollTop / e.currentTarget.scrollHeight;
          // onProgressChange(progress.toString());
        }}
      />
    </div>
  );
}
