import React, { useState, useEffect } from 'react';
import './ConnectionStatus.css';

interface ConnectionStatusProps {
  isConnected: boolean;
  isConnecting: boolean;
  reconnectAttempt: number;
  maxReconnectAttempts: number;
  onManualReconnect: () => void;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  isConnected,
  isConnecting,
  reconnectAttempt,
  maxReconnectAttempts,
  onManualReconnect
}) => {
  // Use modal for prolonged connection issues (multiple reconnect attempts)
  const [showFullModal, setShowFullModal] = useState(false);
  
  // Set a timer to show the full modal after a delay if still not connected
  useEffect(() => {
    let timer: number | null = null;

    // If we're disconnected and not in the process of connecting, 
    // or if we've had multiple reconnection attempts, show the full modal
    if (!isConnected && (!isConnecting || reconnectAttempt > 1)) {
      timer = window.setTimeout(() => {
        setShowFullModal(true);
      }, 3000); // Show full modal after 3 seconds of connection issues
    } else {
      setShowFullModal(false);
    }

    return () => {
      if (timer) {
        window.clearTimeout(timer);
      }
    };
  }, [isConnected, isConnecting, reconnectAttempt]);

  if (isConnected) {
    return null; // Don't show anything when connected
  }

  // For initial connection or first reconnect attempt, show inline status in chat UI
  if (!showFullModal) {
    return (
      <div className="connection-status-inline">
        <div className="connection-status-main">
          {isConnecting ? (
            <div className="connection-status-text connecting">Connecting</div>
          ) : (
            <div className="connection-status-text disconnected">Disconnected</div>
          )}
        </div>
        
        {isConnecting && (
          <div className="connection-status-details">
            <div className="connection-details-box">
              {reconnectAttempt > 0 
                ? `Attempting to reconnect (${reconnectAttempt}/${maxReconnectAttempts})...` 
                : "Waiting for server response..."}
            </div>
          </div>
        )}
      </div>
    );
  }

  // For prolonged connection issues, show the full modal
  return (
    <div className="connection-status-overlay">
      <div className="connection-status-modal">
        <div className="connection-status-header">
          <h3>Connection Status</h3>
        </div>
        <div className="connection-status-content">
          {isConnecting ? (
            <>
              <div className="connection-spinner"></div>
              <p>Connecting to server... Please wait.</p>
              {reconnectAttempt > 0 && (
                <p className="reconnect-attempt">
                  Reconnect attempt {reconnectAttempt} of {maxReconnectAttempts}
                </p>
              )}
            </>
          ) : (
            <>
              <div className="connection-error-icon">!</div>
              <p>Disconnected from server.</p>
              <p className="disconnected-message">
                Could not connect to the server. Please check your network connection.
              </p>
              <button
                className="reconnect-button"
                onClick={onManualReconnect}
              >
                Reconnect Now
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConnectionStatus;
