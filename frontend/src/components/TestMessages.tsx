import React, { useState, useEffect } from 'react';

// This component is purely for debugging WebSocket messages
const TestMessages: React.FC = () => {
  const [messages, setMessages] = useState<any[]>([]);
  
  // Function to intercept and store WebSocket messages
  useEffect(() => {
    const originalWebSocket = window.WebSocket;
    
    // Store the original WebSocket
    class InterceptedWebSocket extends originalWebSocket {
      constructor(url: string | URL, protocols?: string | string[]) {
        super(url, protocols);
        
        // Intercept the onmessage event
        this.addEventListener('message', (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WebSocket received:', data);
            
            // Add the message to our state
            setMessages(prev => [data, ...prev].slice(0, 20)); // Keep last 20 messages
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        });
      }
    }
    
    // Replace the WebSocket with our intercepted version
    window.WebSocket = InterceptedWebSocket as any;
    
    // Clean up on unmount - restore original WebSocket
    return () => {
      window.WebSocket = originalWebSocket;
    };
  }, []);
  
  // Reset messages
  const handleClear = () => {
    setMessages([]);
  };
  
  return (
    <div className="test-messages">
      <div className="test-header">
        <h3>Debug WebSocket Messages</h3>
        <button onClick={handleClear}>Clear</button>
      </div>
      
      {messages.length === 0 ? (
        <p>No messages yet</p>
      ) : (
        <div className="message-list">
          {messages.map((msg, index) => (
            <div key={index} className="debug-message">
              <div className="debug-type">Type: {msg.type}</div>
              <pre className="debug-content">{JSON.stringify(msg.content, null, 2)}</pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TestMessages;
