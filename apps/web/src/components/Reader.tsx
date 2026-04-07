import { useState, useEffect, useCallback } from 'react';
import { ReactReader } from 'react-reader';
import axios from 'axios';
import { EBookMetadata, ReadingProgress } from '@aetherreader/shared';

interface ReaderProps {
  book: EBookMetadata;
  onBack: () => void;
}

export function Reader({ book, onBack }: ReaderProps) {
  const [location, setLocation] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProgress();
  }, [book.path]);

  const fetchProgress = async () => {
    try {
      const response = await axios.get<ReadingProgress | null>('/api/progress', {
        params: { path: book.path }
      });
      if (response.data) {
        setLocation(response.data.position);
      }
    } catch (error) {
      console.error('Error fetching progress:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveProgress = useCallback(async (newLocation: string) => {
    try {
      await axios.post('/api/progress', {
        bookPath: book.path,
        position: newLocation,
        lastReadAt: Date.now(),
      } as ReadingProgress);
      setLocation(newLocation);
    } catch (error) {
      console.error('Error saving progress:', error);
    }
  }, [book.path]);

  const renderReader = () => {
    const ext = book.name.split('.').pop()?.toLowerCase();
    const streamUrl = `/api/books/stream?path=${encodeURIComponent(book.path)}`;

    if (ext === 'epub') {
      return (
        <ReactReader
          url={streamUrl}
          location={location || undefined}
          locationChanged={saveProgress}
          epubOptions={{
            flow: 'paginated',
            manager: 'default',
          }}
        />
      );
    }

    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <h2>Unsupported Format: {ext}</h2>
        <p>Currently only EPUB is supported. PDF and MOBI support coming soon!</p>
      </div>
    );
  };

  if (loading) return <div className="reader-container"><p>Loading progress...</p></div>;

  return (
    <div className="reader-container">
      <div className="reader-header">
        <button className="back-button" onClick={onBack}>←</button>
        <span className="book-title">{book.name}</span>
        <div style={{ width: '40px' }}></div> {/* Spacer */}
      </div>
      <div className="reader-content">
        {renderReader()}
      </div>
    </div>
  );
}
