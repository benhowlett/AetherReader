import { useState, useEffect } from 'react';
import axios from 'axios';
import { EBookMetadata } from '@aetherreader/shared';
import { Reader } from './components/Reader';

function App() {
  const [books, setBooks] = useState<EBookMetadata[]>([]);
  const [currentFolder, setCurrentFolder] = useState('/');
  const [selectedBook, setSelectedBook] = useState<EBookMetadata | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBooks(currentFolder);
  }, [currentFolder]);

  const fetchBooks = async (folder: string) => {
    setLoading(true);
    try {
      const response = await axios.get<EBookMetadata[]>('/api/books', {
        params: { folder }
      });
      setBooks(response.data);
    } catch (error) {
      console.error('Error fetching books:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFileIcon = (name: string) => {
    const ext = name.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'epub': return '📚';
      case 'pdf': return '📄';
      case 'mobi': return '📱';
      case 'azw3': return '📱';
      default: return '📖';
    }
  };

  if (selectedBook) {
    return <Reader book={selectedBook} onBack={() => setSelectedBook(null)} />;
  }

  return (
    <div className="app-container">
      <header>
        <h1>AetherReader</h1>
      </header>
      <main>
        {loading ? (
          <p>Loading books...</p>
        ) : (
          <div className="book-grid">
            {books.map((book) => (
              <div 
                key={book.path} 
                className="book-card"
                onClick={() => setSelectedBook(book)}
              >
                <div className="book-cover-placeholder">
                  {getFileIcon(book.name)}
                </div>
                <div className="book-info">
                  <h3 className="book-title">{book.name}</h3>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
