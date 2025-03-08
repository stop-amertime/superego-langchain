import React from 'react';
import './ChatHeader.css';

interface ChatHeaderProps {
  isConnected: boolean;
  isConnecting: boolean;
  connectionFailed: boolean;
  reconnectAttempt: number;
  maxReconnectAttempts: number;
  isSending: boolean;
  onCancelProcessing: () => void;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({
  isConnected,
  isConnecting,
  connectionFailed,
  reconnectAttempt,
  maxReconnectAttempts,
  isSending,
  onCancelProcessing
}) => {
  return (
    <div className="chat-header">
      <h2>Chat</h2>
      <div className="connection-controls">
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
          <span className={isConnecting ? 'connecting-text' : connectionFailed ? 'disconnected-text' : ''}>
            {isConnected ? 'Connected' : 'Connecting'}
          </span>
          
          {/* Connection details box that appears directly below the status */}
          {isConnecting && (
            <div className="connection-status-details">
              {reconnectAttempt > 0 ? (
                <div className="connection-attempt-info">
                  Attempting to reconnect ({reconnectAttempt}/{maxReconnectAttempts})...
                </div>
              ) : (
                <div className="connection-attempt-info">
                  Waiting for server response...
                </div>
              )}
            </div>
          )}
        </div>
        {isSending && (
          <button 
            onClick={onCancelProcessing}
            className="reset-button"
            title="Cancel message processing"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  );
};

export default ChatHeader;
