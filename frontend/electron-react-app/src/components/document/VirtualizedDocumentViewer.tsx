import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { FixedSizeList } from 'react-window';

import { useDocumentProcessor, DocumentPage } from '../../lib/document/DocumentProcessor';

interface DocumentViewerProps {
  documentId: string;
  totalPages: number;
  onPageLoad: (pageNumber: number, signal: AbortSignal) => Promise<DocumentPage>;
  onPageClick?: (pageNumber: number) => void;
  highlightedText?: string;
  className?: string;
}

interface PageItemProps {
  index: number;
  style: React.CSSProperties;
  data: {
    pages: Map<number, DocumentPage>;
    onPageClick?: (pageNumber: number) => void;
    highlightedText?: string;
    loadPageRange: (start: number, end: number) => Promise<void>;
  };
}

const PageItem: React.FC<PageItemProps> = ({ index, style, data }) => {
  const pageNumber = index + 1;
  const page = data.pages.get(pageNumber);
  const [isVisible, setIsVisible] = useState(false);
  const pageRef = useRef<HTMLDivElement>(null);

  // Intersection observer for lazy loading
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isVisible) {
          setIsVisible(true);
          // Load this page and nearby pages
          const start = Math.max(1, pageNumber - 2);
          const end = Math.min(pageNumber + 2, data.pages.size || pageNumber + 2);
          data.loadPageRange(start, end);
        }
      },
      { threshold: 0.1, rootMargin: '100px' }
    );

    if (pageRef.current) {
      observer.observe(pageRef.current);
    }

    return () => {
      if (pageRef.current) {
        observer.unobserve(pageRef.current);
      }
    };
  }, [pageNumber, data.loadPageRange, isVisible]);

  const handleClick = useCallback(() => {
    data.onPageClick?.(pageNumber);
  }, [pageNumber, data.onPageClick]);

  const highlightText = useCallback((text: string, highlight?: string) => {
    if (!highlight || !text) return text;

    const regex = new RegExp(`(${highlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark key={index} className="document-highlight">
          {part}
        </mark>
      ) : (
        part
      )
    );
  }, []);

  const renderPageContent = () => {
    if (!page) {
      return (
        <div className="page-placeholder">
          <div className="page-skeleton">
            <div className="skeleton-line"></div>
            <div className="skeleton-line"></div>
            <div className="skeleton-line short"></div>
          </div>
        </div>
      );
    }

    if (page.isLoading) {
      return (
        <div className="page-loading">
          <div className="loading-spinner"></div>
          <p>Loading page {pageNumber}...</p>
        </div>
      );
    }

    if (page.error) {
      return (
        <div className="page-error">
          <p>Error loading page {pageNumber}</p>
          <p className="error-message">{page.error.message}</p>
        </div>
      );
    }

    if (!page.isLoaded || !page.content) {
      return (
        <div className="page-empty">
          <p>Page {pageNumber} - No content</p>
        </div>
      );
    }

    return (
      <div className="page-content">
        <div className="page-text">
          {highlightText(page.content, data.highlightedText)}
        </div>
        {page.metadata && (
          <div className="page-metadata">
            {Object.entries(page.metadata).map(([key, value]) => (
              <span key={key} className="metadata-item">
                {key}: {String(value)}
              </span>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      ref={pageRef}
      style={style}
      className={`document-page ${page?.isLoaded ? 'loaded' : 'loading'}`}
      onClick={handleClick}
    >
      <div className="page-header">
        <span className="page-number">Page {pageNumber}</span>
        {page?.isLoaded && (
          <span className="page-status">✓</span>
        )}
      </div>
      {renderPageContent()}
    </div>
  );
};

export const VirtualizedDocumentViewer: React.FC<DocumentViewerProps> = ({
  documentId,
  totalPages,
  onPageLoad,
  onPageClick,
  highlightedText,
  className = '',
}) => {
  const {
    processor,
    progress,
    pages,
    loadDocument,
    loadPageRange,
  } = useDocumentProcessor({
    chunkSize: 3,
    maxConcurrentPages: 2,
    cacheSize: 20,
    timeoutMs: 30000,
  });

  const [listHeight, setListHeight] = useState(600);
  const [itemHeight] = useState(400);
  const listRef = useRef<List>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Load document when component mounts or documentId changes
  useEffect(() => {
    if (documentId && totalPages > 0) {
      loadDocument(documentId, totalPages, onPageLoad);
    }
  }, [documentId, totalPages, onPageLoad, loadDocument]);

  // Update list height based on container size
  useEffect(() => {
    const updateHeight = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setListHeight(Math.max(400, rect.height - 100));
      }
    };

    updateHeight();
    window.addEventListener('resize', updateHeight);
    return () => window.removeEventListener('resize', updateHeight);
  }, []);

  // Scroll to specific page
  const scrollToPage = useCallback((pageNumber: number) => {
    if (listRef.current) {
      listRef.current.scrollToItem(pageNumber - 1, 'center');
    }
  }, []);

  // Memoized data for virtual list
  const listData = useMemo(() => ({
    pages,
    onPageClick,
    highlightedText,
    loadPageRange,
  }), [pages, onPageClick, highlightedText, loadPageRange]);

  const renderProgressBar = () => {
    if (progress.status === 'idle' || progress.status === 'completed') {
      return null;
    }

    return (
      <div className="document-progress">
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress.percentage}%` }}
          />
        </div>
        <div className="progress-text">
          {progress.status === 'loading' && (
            <span>Loading pages... {progress.loadedPages}/{progress.totalPages}</span>
          )}
          {progress.status === 'error' && (
            <span className="error">Error: {progress.error?.message}</span>
          )}
        </div>
      </div>
    );
  };

  const renderControls = () => (
    <div className="document-controls">
      <div className="document-info">
        <span>Total Pages: {totalPages}</span>
        <span>Loaded: {progress.loadedPages}</span>
        {progress.status === 'loading' && (
          <span>Loading: {progress.currentPage}</span>
        )}
      </div>

      <div className="document-actions">
        <button
          onClick={() => scrollToPage(1)}
          disabled={totalPages === 0}
          className="control-button"
        >
          First Page
        </button>
        <button
          onClick={() => scrollToPage(totalPages)}
          disabled={totalPages === 0}
          className="control-button"
        >
          Last Page
        </button>
        <button
          onClick={() => processor.clear()}
          className="control-button secondary"
        >
          Clear
        </button>
      </div>
    </div>
  );

  return (
    <div ref={containerRef} className={`virtualized-document-viewer ${className}`}>
      {renderControls()}
      {renderProgressBar()}

      <div className="document-list-container">
        {totalPages > 0 ? (
          <FixedSizeList
            ref={listRef}
            height={listHeight}
            itemCount={totalPages}
            itemSize={itemHeight}
            itemData={listData}
            overscanCount={2}
            className="document-list"
          >
            {PageItem}
          </FixedSizeList>
        ) : (
          <div className="document-empty">
            <p>No document loaded</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Hook for managing document viewer state
export const useDocumentViewer = () => {
  const [currentDocument, setCurrentDocument] = useState<{
    id: string;
    totalPages: number;
  } | null>(null);

  const [highlightedText, setHighlightedText] = useState<string>('');
  const [selectedPage, setSelectedPage] = useState<number | null>(null);

  const loadDocument = useCallback((documentId: string, totalPages: number) => {
    setCurrentDocument({ id: documentId, totalPages });
    setSelectedPage(null);
    setHighlightedText('');
  }, []);

  const highlightText = useCallback((text: string) => {
    setHighlightedText(text);
  }, []);

  const selectPage = useCallback((pageNumber: number) => {
    setSelectedPage(pageNumber);
  }, []);

  const clearDocument = useCallback(() => {
    setCurrentDocument(null);
    setSelectedPage(null);
    setHighlightedText('');
  }, []);

  return {
    currentDocument,
    highlightedText,
    selectedPage,
    loadDocument,
    highlightText,
    selectPage,
    clearDocument,
  };
};