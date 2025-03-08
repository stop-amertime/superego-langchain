import { getWebSocketClient } from './websocketClient';
import { debugMessageTypes } from './debugHelper';

/**
 * WebSocket Diagnostics Tool
 * 
 * This tool helps diagnose issues with WebSocket connections by providing:
 * - Connection status checks
 * - Message flow monitoring
 * - Raw message logging
 * - Error reporting
 */

export const runDiagnosticTest = (): void => {
  debugMessageTypes.log('WebSocket Diagnostics', 'Starting diagnostic test');
  
  // Check if WebSocket is supported
  if (!window.WebSocket) {
    debugMessageTypes.error('WebSocket Diagnostics', 'WebSocket is not supported in this browser');
    return;
  }
  
  // Test connection
  try {
    const wsClient = getWebSocketClient({
      onOpen: () => {
        debugMessageTypes.log('WebSocket Diagnostics', '✅ Connection successful');
      },
      onClose: () => {
        debugMessageTypes.error('WebSocket Diagnostics', '❌ Connection closed');
      },
      onConnectionError: (error) => {
        debugMessageTypes.error('WebSocket Diagnostics', `❌ Connection error: ${error}`);
      },
      onSystemMessage: (content) => {
        debugMessageTypes.log('WebSocket Diagnostics', `System message received: ${content}`);
      },
      onSuperEgoEvaluation: (evaluation) => {
        debugMessageTypes.log('WebSocket Diagnostics', `✅ SuperEgo evaluation received: ${JSON.stringify(evaluation, null, 2)}`);
      },
      onAssistantMessage: (message) => {
        debugMessageTypes.log('WebSocket Diagnostics', `✅ Assistant message received: ${JSON.stringify(message, null, 2)}`);
      },
      onError: (error) => {
        debugMessageTypes.error('WebSocket Diagnostics', `❌ Error message received: ${error}`);
      },
      onMessage: (message) => {
        // Inspect raw message
        debugMessageTypes.log('WebSocket Diagnostics', `Raw message received: ${JSON.stringify(message, null, 2)}`);
      }
    });
    
    wsClient.connect();
    
    // Send a test message after a short delay
    setTimeout(() => {
      if (wsClient.isConnected()) {
        debugMessageTypes.log('WebSocket Diagnostics', 'Sending test message');
        wsClient.sendMessage('Hello, this is a diagnostic test message');
      } else {
        debugMessageTypes.error('WebSocket Diagnostics', 'Cannot send test message - not connected');
      }
    }, 1000);
  } catch (error) {
    debugMessageTypes.error('WebSocket Diagnostics', `Error running diagnostic: ${error}`);
  }
};

/**
 * Checks browser network logs specifically for WebSocket issues
 */
export const checkNetworkLogs = (): void => {
  debugMessageTypes.log('WebSocket Diagnostics', 
    'Network logs check: Please open browser DevTools (F12), go to the Network tab, and filter by "WS" to view WebSocket connections');
};

/**
 * Runs a quick self-test of the WebSocket client
 */
export const runSelfTest = async (): Promise<{
  success: boolean;
  issues: string[];
}> => {
  const issues: string[] = [];
  
  // 1. Check if we're using a secure connection for WebSockets from a secure page
  if (window.location.protocol === 'https:' && 
      !getWebSocketClient().connect.toString().includes('wss://')) {
    issues.push('WARNING: Secure page (HTTPS) is trying to connect to an insecure WebSocket (WS)');
  }
  
  // 2. Check for proper URL formation
  try {
    // Test if we can create a WebSocket with the URL
    const testSocket = new WebSocket('ws://localhost:8000/ws/test-id');
    testSocket.close();
  } catch (error) {
    issues.push(`WebSocket URL format error: ${error}`);
  }
  
  // 3. Check if WebSocket endpoint is functioning
  const pingPromise = new Promise<void>((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      reject(new Error('WebSocket connection attempt timed out'));
    }, 5000);
    
    try {
      const testSocket = new WebSocket('ws://localhost:8000/ws/test-id');
      
      testSocket.onopen = () => {
        clearTimeout(timeoutId);
        testSocket.close();
        resolve();
      };
      
      testSocket.onerror = (event) => {
        clearTimeout(timeoutId);
        reject(new Error('Error connecting to WebSocket server'));
      };
    } catch (error) {
      clearTimeout(timeoutId);
      reject(error);
    }
  });
  
  try {
    await pingPromise;
  } catch (error: any) {
    issues.push(`WebSocket connectivity issue: ${error.message || 'Unknown error'}`);
  }
  
  return {
    success: issues.length === 0,
    issues
  };
};

/**
 * Utility to monitor message flow between client and server
 */
export const monitorWebSocketTraffic = (enable: boolean = true): void => {
  const original = WebSocket.prototype.send;
  
  if (enable) {
    // Patch WebSocket send method to log all outgoing messages
    WebSocket.prototype.send = function(data) {
      try {
        const parsedData = typeof data === 'string' ? JSON.parse(data) : data;
        debugMessageTypes.websocket.sent('INTERCEPTED', parsedData);
      } catch (e) {
        debugMessageTypes.websocket.sent('INTERCEPTED', data);
      }
      return original.call(this, data);
    };
    
    debugMessageTypes.log('WebSocket Diagnostics', 'WebSocket traffic monitoring enabled');
  } else {
    // Restore original method
    WebSocket.prototype.send = original;
    debugMessageTypes.log('WebSocket Diagnostics', 'WebSocket traffic monitoring disabled');
  }
};

/**
 * Export a function that can be called from a browser console to diagnose issues
 */
(window as any).diagnoseWebSocketIssues = () => {
  console.clear();
  console.log('%c WebSocket Diagnostic Tool ', 'background: #007BFF; color: white; font-size: 16px; padding: 5px 10px; border-radius: 5px;');
  console.log('Running diagnostic tests...');
  
  // Enable traffic monitoring
  monitorWebSocketTraffic(true);
  
  // Run self-test
  runSelfTest().then(result => {
    if (result.success) {
      console.log('%c Self-test passed ✅ ', 'background: #28a745; color: white; padding: 3px 5px; border-radius: 3px;');
    } else {
      console.log('%c Self-test found issues ⚠️ ', 'background: #ffc107; color: black; padding: 3px 5px; border-radius: 3px;');
      result.issues.forEach(issue => console.warn(`- ${issue}`));
    }
    
    // Run the full diagnostic
    runDiagnosticTest();
    
    // Remind to check network logs
    checkNetworkLogs();
  });
  
  return "Diagnostic tests initiated. Check console for results.";
};
