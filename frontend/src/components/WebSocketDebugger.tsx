import React, { useState, useEffect, useRef } from 'react';
import { getWebSocketClient } from '../api/websocketClient';
import { debugMessageTypes } from '../api/debugHelper';
import { WebSocketMessageType, Message, MessageRole } from '../types';

interface LogEntry {
  type: 'connection' | 'sent' | 'received' | 'error';
  timestamp: string;
  content: string;
  details?: any;
}

const WebSocketDebugger: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [connected, setConnected] = useState<boolean>(false);
  const [testMessage, setTestMessage] = useState<string>('Hello, this is a test message!');
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  
  // Initialize with connection status
  useEffect(() => {
    // Log existing connection state
    const wsClient = getWebSocketClient();
    setConnected(wsClient.isConnected());
    
    // Add initial log
    addLog('connection', 'Debugger initialized', { connected: wsClient.isConnected() });
    
    // Set up listeners for WebSocket events
    const handleOpen = () => {
      setConnected(true);
      addLog('connection', 'WebSocket connection established');
    };
    
    const handleClose = () => {
      setConnected(false);
      addLog('connection', 'WebSocket connection closed');
    };
    
    const handleError = (err: any) => {
      addLog('error', 'WebSocket error occurred', { error: err });
    };
    
    const handleMessage = (message: any) => {
      addLog('received', `Message received (${message.type})`, message);
    };
    
    // Patch the WebSocket send method to log outgoing messages
    const originalSend = WebSocket.prototype.send;
    WebSocket.prototype.send = function(data) {
      try {
        const parsedData = typeof data === 'string' ? JSON.parse(data) : data;
        addLog('sent', 'Message sent', parsedData);
      } catch (e) {
        addLog('sent', 'Message sent (unparseable)', { raw: data });
      }
      return originalSend.call(this, data);
    };
    
    // Return cleanup function
    return () => {
      // Restore original WebSocket send method
      WebSocket.prototype.send = originalSend;
    };
  }, []);
  
  // Auto-scroll to bottom when logs change
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);
  
  // Function to add a log entry
  const addLog = (type: LogEntry['type'], content: string, details?: any) => {
    setLogs(prevLogs => [
      ...prevLogs,
      {
        type,
        timestamp: new Date().toISOString(),
        content,
        details
      }
    ]);
  };
  
  // Connect to WebSocket
  const handleConnect = () => {
    addLog('connection', 'Connecting to WebSocket server...');
    getWebSocketClient().connect();
  };
  
  // Disconnect from WebSocket
  const handleDisconnect = () => {
    addLog('connection', 'Disconnecting from WebSocket server...');
    getWebSocketClient().disconnect();
    setConnected(false);
  };
  
  // Send a test message
  const handleSendMessage = () => {
    if (!testMessage.trim()) {
      addLog('error', 'Cannot send empty message');
      return;
    }
    
    addLog('sent', 'Sending test message', { content: testMessage });
    getWebSocketClient().sendMessage(testMessage);
  };
  
  // Clear logs
  const handleClearLogs = () => {
    setLogs([]);
  };
  
  // Reconnect WebSocket
  const handleReconnect = () => {
    handleDisconnect();
    setTimeout(handleConnect, 500);
  };
  
  // Run full diagnostics
  const handleRunDiagnostics = () => {
    addLog('connection', 'Running full WebSocket diagnostics...');
    try {
      // @ts-ignore - This is defined as a global function in websocketDiagnostics.ts
      window.diagnoseWebSocketIssues();
    } catch (error) {
      addLog('error', 'Error running diagnostics', { error });
    }
  };
  
  // Force send a mock assistant message (to test UI handling)
  const handleForceMockAssistant = () => {
    addLog('sent', 'Injecting mock assistant message to UI');
    
    const mockAssistantMsg: Message = {
      id: `mock-${Date.now()}`,
      role: MessageRole.ASSISTANT,
      content: 'This is a mock assistant message for testing.',
      timestamp: new Date().toISOString()
    };
    
    // Add to logs
    addLog('received', 'Received mock assistant message', mockAssistantMsg);
  };
  
  return (
    <div className="websocket-debugger">
      <h2>WebSocket Debugger</h2>
      
      <div className="debugger-controls">
        <div className="connection-controls">
          <button 
            onClick={handleConnect}
            disabled={connected}
            className={`control-button ${connected ? 'disabled' : 'connect'}`}
          >
            Connect
          </button>
          <button 
            onClick={handleDisconnect}
            disabled={!connected}
            className={`control-button ${!connected ? 'disabled' : 'disconnect'}`}
          >
            Disconnect
          </button>
          <button 
            onClick={handleReconnect}
            className="control-button reconnect"
          >
            Reconnect
          </button>
          
          <div className="connection-status">
            <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`}></span>
            {connected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
        
        <div className="message-controls">
          <input
            type="text"
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            placeholder="Type a test message..."
            disabled={!connected}
          />
          <button 
            onClick={handleSendMessage}
            disabled={!connected || !testMessage.trim()}
            className="control-button send"
          >
            Send Test Message
          </button>
        </div>
        
        <div className="diagnostic-controls">
          <button 
            onClick={handleRunDiagnostics}
            className="control-button diagnostics"
          >
            Run Full Diagnostics
          </button>
          <button 
            onClick={handleForceMockAssistant}
            className="control-button mock"
          >
            Inject Mock Response
          </button>
          <button 
            onClick={handleClearLogs}
            className="control-button clear"
          >
            Clear Logs
          </button>
          <label className="auto-scroll-control">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            Auto-scroll
          </label>
        </div>
      </div>
      
      <div className="logs-container">
        <h3>WebSocket Logs</h3>
        <div className="logs">
          {logs.length === 0 ? (
            <div className="empty-logs">No logs yet. Connect to WebSocket server to begin.</div>
          ) : (
            logs.map((log, index) => (
              <div key={index} className={`log-entry ${log.type}`}>
                <div className="log-timestamp">[{new Date(log.timestamp).toLocaleTimeString()}]</div>
                <div className="log-type">[{log.type.toUpperCase()}]</div>
                <div className="log-content">{log.content}</div>
                {log.details && (
                  <pre className="log-details">{JSON.stringify(log.details, null, 2)}</pre>
                )}
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>
      
      <style>{`
        .websocket-debugger {
          background-color: #f5f5f5;
          border-radius: 8px;
          padding: 16px;
          margin-top: 20px;
          font-family: monospace;
        }
        
        h2 {
          margin-top: 0;
          color: #333;
        }
        
        .debugger-controls {
          display: flex;
          flex-direction: column;
          gap: 12px;
          margin-bottom: 16px;
        }
        
        .connection-controls, .message-controls, .diagnostic-controls {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          align-items: center;
        }
        
        .control-button {
          padding: 8px 12px;
          border-radius: 4px;
          cursor: pointer;
          font-weight: bold;
          transition: background-color 0.2s;
        }
        
        .control-button.connect { background-color: #4caf50; color: white; }
        .control-button.disconnect { background-color: #f44336; color: white; }
        .control-button.reconnect { background-color: #2196f3; color: white; }
        .control-button.send { background-color: #ff9800; color: white; }
        .control-button.diagnostics { background-color: #9c27b0; color: white; }
        .control-button.mock { background-color: #607d8b; color: white; }
        .control-button.clear { background-color: #795548; color: white; }
        .control-button.disabled { background-color: #e0e0e0; color: #9e9e9e; cursor: not-allowed; }
        
        input {
          padding: 8px;
          border-radius: 4px;
          border: 1px solid #ccc;
          flex-grow: 1;
        }
        
        .connection-status {
          margin-left: 16px;
          display: flex;
          align-items: center;
        }
        
        .status-indicator {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          margin-right: 8px;
        }
        
        .status-indicator.connected { background-color: #4caf50; }
        .status-indicator.disconnected { background-color: #f44336; }
        
        .logs-container {
          background-color: #272822;
          color: #f8f8f2;
          border-radius: 4px;
          padding: 12px;
        }
        
        .logs {
          height: 300px;
          overflow-y: auto;
          padding-right: 8px;
        }
        
        .log-entry {
          margin-bottom: 8px;
          padding: 8px;
          border-radius: 4px;
          display: flex;
          flex-wrap: wrap;
        }
        
        .log-entry.connection { background-color: #40407a; }
        .log-entry.sent { background-color: #227093; }
        .log-entry.received { background-color: #218c74; }
        .log-entry.error { background-color: #b33939; }
        
        .log-timestamp, .log-type {
          font-weight: bold;
          margin-right: 8px;
        }
        
        .log-details {
          width: 100%;
          margin-top: 4px;
          background-color: rgba(0, 0, 0, 0.3);
          padding: 8px;
          border-radius: 4px;
          white-space: pre-wrap;
          overflow-x: auto;
        }
        
        .empty-logs {
          color: #aaa;
          text-align: center;
          padding: 16px;
        }
        
        .auto-scroll-control {
          display: flex;
          align-items: center;
          margin-left: 16px;
          color: #555;
        }
        
        input[type="checkbox"] {
          margin-right: 8px;
        }
      `}</style>
    </div>
  );
};

export default WebSocketDebugger;
