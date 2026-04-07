import { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Set up the worker for react-pdf
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

interface PdfReaderProps {
  url: string;
  initialPage?: string | null;
  onPageChange: (pageNumber: string) => void;
}

export function PdfReader({ url, initialPage, onPageChange }: PdfReaderProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [containerWidth, setContainerWidth] = useState<number>(window.innerWidth);

  useEffect(() => {
    if (initialPage) {
      const page = parseInt(initialPage, 10);
      if (!isNaN(page)) {
        setPageNumber(page);
      }
    }
  }, [initialPage]);

  useEffect(() => {
    const handleResize = () => setContainerWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
  }

  function changePage(offset: number) {
    setPageNumber(prevPageNumber => {
      const newPage = Math.min(Math.max(1, prevPageNumber + offset), numPages);
      if (newPage !== prevPageNumber) {
        onPageChange(newPage.toString());
      }
      return newPage;
    });
  }

  return (
    <div className="pdf-reader">
      <div className="pdf-controls">
        <button
          disabled={pageNumber <= 1}
          onClick={() => changePage(-1)}
          className="pdf-nav-button"
        >
          Previous
        </button>
        <span className="pdf-page-info">
          Page {pageNumber} of {numPages}
        </span>
        <button
          disabled={pageNumber >= numPages}
          onClick={() => changePage(1)}
          className="pdf-nav-button"
        >
          Next
        </button>
      </div>
      <div className="pdf-document-container">
        <Document
          file={url}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={<p>Loading PDF...</p>}
        >
          <Page 
            pageNumber={pageNumber} 
            width={Math.min(containerWidth * 0.9, 800)}
            renderAnnotationLayer={true}
            renderTextLayer={true}
          />
        </Document>
      </div>
    </div>
  );
}
