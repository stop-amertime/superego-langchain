import React, { useState, KeyboardEvent } from 'react';
import './ChatInput.css';

interface ChatInputProps {
  onSubmit: (message: string) => void;
  isConnected: boolean;
  isSending: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSubmit, isConnected, isSending }) => {
  const [input, setInput] = useState<string>('');

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isSending) return;
    
    onSubmit(input);
    setInput('');
  };
  
  // Handle keyboard events
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter without Shift key
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent default to avoid newline
      
      if (input.trim() && isConnected && !isSending) {
        onSubmit(input);
        setInput('');
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="chat-input-form">
      <textarea 
        value={input} 
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
        disabled={!isConnected || isSending}
        rows={3}
      />
      <button 
        type="submit" 
        disabled={!input.trim() || !isConnected || isSending}
        className="btn btn-primary send-button"
      >
        Send
      </button>
    </form>
  );
};

export default ChatInput;
