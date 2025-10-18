import React, { useState, useRef, useEffect } from 'react';
import { Button } from '../../../components/ui/Button';
import { Card } from '../../../components/ui/Card';

import styles from './ChatAssistant.module.css';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatAssistantProps {
  initialContext?: string;
  onClose?: () => void;
  className?: string;
}

const THINKING_MESSAGE = "🤔 Thinking...";

export function ChatAssistant({ initialContext, onClose, className }: ChatAssistantProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (initialContext) {
      setMessages([
        {
          role: 'assistant',
          content: "Hello! I'm your AI compliance assistant. How can I help you today?",
          timestamp: new Date()
        },
        {
          role: 'user',
          content: initialContext,
          timestamp: new Date()
        }
      ]);
    } else {
      setMessages([
        {
          role: 'assistant',
          content: "Hello! I'm your AI compliance assistant. How can I help you today?",
          timestamp: new Date()
        }
      ]);
    }
  }, [initialContext]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Add thinking message
    const thinkingMessage: ChatMessage = {
      role: 'assistant',
      content: THINKING_MESSAGE,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, thinkingMessage]);

    try {
      // Simulate API call - replace with actual chat API
      await new Promise(resolve => setTimeout(resolve, 2000));

      const aiResponse: ChatMessage = {
        role: 'assistant',
        content: generateMockResponse(userMessage.content),
        timestamp: new Date()
      };

      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = aiResponse;
        return newMessages;
      });
    } catch (error) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: "I apologize, but I'm having trouble processing your request right now. Please try again.",
        timestamp: new Date()
      };

      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = errorMessage;
        return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const generateMockResponse = (userInput: string): string => {
    const input = userInput.toLowerCase();

    if (input.includes('compliance') || input.includes('medicare')) {
      return "Based on Medicare guidelines, compliance documentation should include specific, measurable goals, objective findings, and clear medical necessity justification. Each visit should document progress toward functional outcomes.";
    }

    if (input.includes('documentation') || input.includes('note')) {
      return "Effective therapy documentation follows the SOAP format: Subjective (patient report), Objective (measurable findings), Assessment (clinical judgment), and Plan (next steps). Include functional outcome measures and patient response to treatment.";
    }

    if (input.includes('goal') || input.includes('objective')) {
      return "Goals should be SMART: Specific, Measurable, Achievable, Relevant, and Time-bound. Examples: 'Patient will ambulate 100 feet independently within 4 weeks' or 'Patient will improve grip strength by 20% in 6 weeks'.";
    }

    if (input.includes('billing') || input.includes('claim')) {
      return "For billing compliance, ensure documentation supports the CPT codes used, includes proper modifiers when applicable, and demonstrates medical necessity for each service provided. Document time spent and specific interventions.";
    }

    if (input.includes('progress') || input.includes('improvement')) {
      return "Progress notes should clearly demonstrate functional improvement or maintenance. Use objective measures like ROM, strength, balance scores, or functional assessments. Document setbacks and plan modifications.";
    }

    return "I can help you with compliance questions, documentation best practices, Medicare guidelines, billing requirements, and clinical documentation standards. What specific area would you like to know more about?";
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <Card title="🤖 AI Compliance Assistant" subtitle="Ask questions about documentation, compliance, and best practices" className={className}>
      <div className={styles.chatContainer}>
        <div className={styles.messagesContainer}>
          {messages.map((message, index) => (
            <div key={index} className={`${styles.message} ${styles[message.role]}`}>
              <div className={styles.messageContent}>
                {message.content === THINKING_MESSAGE ? (
                  <div className={styles.thinkingMessage}>
                    <span className={styles.thinkingDots}>...</span>
                    {message.content}
                  </div>
                ) : (
                  <div className={styles.messageText}>
                    {message.content.split('\n').map((line, i) => (
                      <p key={i}>{line}</p>
                    ))}
                  </div>
                )}
                <div className={styles.messageTime}>
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className={styles.inputContainer}>
          <div className={styles.inputWrapper}>
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about compliance, documentation tips, or specific findings..."
              className={styles.messageInput}
              rows={2}
              disabled={isLoading}
            />
            <Button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
              className={styles.sendButton}
            >
              {isLoading ? 'Sending...' : 'Send'}
            </Button>
          </div>

          <div className={styles.quickActions}>
            <Button
              variant="ghost"
              onClick={() => setInputValue("What are the key Medicare documentation requirements?")}
            >
              Medicare Requirements
            </Button>
            <Button
              variant="ghost"
              onClick={() => setInputValue("How should I write effective therapy goals?")}
            >
              Writing Goals
            </Button>
            <Button
              variant="ghost"
              onClick={() => setInputValue("What makes documentation compliant for billing?")}
            >
              Billing Compliance
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}