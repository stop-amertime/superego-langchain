import React from 'react';
import './StreamingMessage.css';

interface StreamingMessageProps {
  content: string;
}

const StreamingMessage: React.FC<StreamingMessageProps> = ({ content }) => {
  return (
    <div className="message-bubble assistant streaming">
      <div className="message-header">
        <div className="message-info">
          <span className="message-sender">Step 4: Generating response</span>
          <span className="message-time">{new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })}</span>
        </div>
      </div>
      <div className="message-content">
        {content}
        <span className="cursor-blink">|</span>
      </div>
    </div>
  );
};

export default StreamingMessage;
