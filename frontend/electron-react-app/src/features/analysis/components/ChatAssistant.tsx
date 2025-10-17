import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageSquare, Loader2, AlertCircle, RefreshCw } from '../../../components/ui/Icons';
import { useAppStore } from '../../../store/useAppStore';
import styles from './ChatAssistant.module.css';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  confidence?: number;
  sources?: string[];
}

interface ChatAssistantProps {
  analysisContext?: {
    documentName?: string;
    findings?: any[];
    complianceScore?: number;
  };
}

export const ChatAssistant: React.FC<ChatAssistantProps> = ({ analysisContext }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const token = useAppStore((state) => state.auth.token);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize WebSocket connection
  useEffect(() => {
    if (!token) return;

    const connectWebSocket = () => {
      try {
        const wsUrl = `ws://localhost:8000/api/chat/ws?token=${token}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setIsConnected(true);
          setError(null);
          console.log('Chat WebSocket connected');

          // Send initial context if available
          if (analysisContext) {
            ws.send(JSON.stringify({
              type: 'context',
              data: analysisContext
            }));
          }
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'message') {
              const newMessage: ChatMessage = {
                id: Date.now().toString(),
                role: 'assistant',
                content: data.content,
                timestamp: new Date(),
                confidence: data.confidence,
                sources: data.sources
              };

              setMessages(prev => [...prev, newMessage]);
              setIsLoading(false);
            } else if (data.type === 'error') {
              setError(data.message);
              setIsLoading(false);
            }
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
            setError('Failed to parse response');
            setIsLoading(false);
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          console.log('Chat WebSocket disconnected');
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setError('Connection error');
          setIsConnected(false);
          setIsLoading(false);
        };

        wsRef.current = ws;
      } catch (err) {
        console.error('Failed to create WebSocket:', err);
        setError('Failed to connect');
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [token, analysisContext]);

  const sendMessage = async () => {
    if (!inputValue.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      wsRef.current.send(JSON.stringify({
        type: 'message',
        content: inputValue.trim(),
        context: analysisContext
      }));

      setInputValue('');
    } catch (err) {
      console.error('Failed to send message:', err);
      setError('Failed to send message');
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const insertLatestFinding = () => {
    if (analysisContext?.findings && analysisContext.findings.length > 0) {
      const latestFinding = analysisContext.findings[0];
      const findingText = `Please explain this finding: "${latestFinding.issue || latestFinding.description || 'Latest compliance finding'}"`;
      setInputValue(findingText);
    }
  };

  const reconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    // The useEffect will automatically reconnect
  };

  return (
    <div className={styles.chatContainer}>
      <div className={styles.chatHeader}>
        <div className={styles.headerLeft}>
          <MessageSquare size={20} />
          <span>Compliance Copilot</span>
        </div>
        <div className={styles.headerRight}>
          <div className={`${styles.connectionStatus} ${isConnected ? styles.connected : styles.disconnected}`}>
            <div className={styles.statusDot} />
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
          {!isConnected && (
            <button onClick={reconnect} className={styles.reconnectBtn} title="Reconnect">
              <RefreshCw size={16} />
            </button>
          )}
        </div>
      </div>

      <div className={styles.messagesContainer}>
        {messages.length === 0 && (
          <div className={styles.welcomeMessage}>
            <MessageSquare size={48} className={styles.welcomeIcon} />
            <h3>Ask me about compliance!</h3>
            <p>I can help explain findings, suggest improvements, and answer documentation questions.</p>
            {analysisContext?.documentName && (
              <p className={styles.contextInfo}>
                Currently analyzing: <strong>{analysisContext.documentName}</strong>
              </p>
            )}
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`${styles.message} ${styles[message.role]}`}>
            <div className={styles.messageContent}>
              <div className={styles.messageText}>{message.content}</div>
              {message.confidence && (
                <div className={styles.messageMetadata}>
                  <span className={styles.confidence}>
                    Confidence: {Math.round(message.confidence * 100)}%
                  </span>
                </div>
              )}
              {message.sources && message.sources.length > 0 && (
                <div className={styles.sources}>
                  <strong>Sources:</strong> {message.sources.join(', ')}
                </div>
              )}
            </div>
            <div className={styles.messageTime}>
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className={`${styles.message} ${styles.assistant} ${styles.loading}`}>
            <div className={styles.messageContent}>
              <Loader2 size={16} className={styles.spinner} />
              <span>Thinking...</span>
            </div>
          </div>
        )}

        {error && (
          <div className={styles.errorMessage}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className={styles.inputContainer}>
        <div className={styles.inputActions}>
          {analysisContext?.findings && analysisContext.findings.length > 0 && (
            <button
              onClick={insertLatestFinding}
              className={styles.actionBtn}
              title="Insert latest finding"
            >
              Insert Latest Finding
            </button>
          )}
        </div>

        <div className={styles.inputRow}>
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about documentation gaps, compliance requirements, or specific findings..."
            className={styles.chatInput}
            rows={3}
            disabled={!isConnected || isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!inputValue.trim() || !isConnected || isLoading}
            className={styles.sendBtn}
            title="Send message"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};