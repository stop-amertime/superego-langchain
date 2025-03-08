import React, { useState } from 'react';
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

  return (
    <form onSubmit={handleSubmit} className="chat-input-form">
      <textarea 
        value={input} 
        onChange={handleInputChange} 
        placeholder="Type your message here..."
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
