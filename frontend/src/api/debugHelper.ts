// Debug helper functions for WebSocket communication
export const debugMessageTypes = {
  log: (location: string, message: any) => {
    // Create a visually distinct log in the console
    console.log(
      `%c 🔍 DEBUG [${location}] %c ${typeof message === 'string' ? message : JSON.stringify(message, null, 2)}`,
      'background: #f0f0f0; color: #0066cc; font-weight: bold; padding: 3px 5px; border-radius: 3px;',
      'color: #333; font-weight: normal;'
    );
  },
  
  error: (location: string, message: any) => {
    console.error(
      `%c ❌ ERROR [${location}] %c ${typeof message === 'string' ? message : JSON.stringify(message, null, 2)}`,
      'background: #ffebee; color: #d32f2f; font-weight: bold; padding: 3px 5px; border-radius: 3px;',
      'color: #333; font-weight: normal;'
    );
  },
  
  warn: (location: string, message: any) => {
    console.warn(
      `%c ⚠️ WARNING [${location}] %c ${typeof message === 'string' ? message : JSON.stringify(message, null, 2)}`,
      'background: #fff8e1; color: #ff8f00; font-weight: bold; padding: 3px 5px; border-radius: 3px;',
      'color: #333; font-weight: normal;'
    );
  },
  
  websocket: {
    received: (type: string, data: any) => {
      console.log(
        `%c 📥 WS RECEIVED [${type}] %c`,
        'background: #e8f5e9; color: #2e7d32; font-weight: bold; padding: 3px 5px; border-radius: 3px;',
        'color: #333; font-weight: normal;'
      );
      console.dir(data);
    },
    
    sent: (type: string, data: any) => {
      console.log(
        `%c 📤 WS SENT [${type}] %c`,
        'background: #e3f2fd; color: #1565c0; font-weight: bold; padding: 3px 5px; border-radius: 3px;',
        'color: #333; font-weight: normal;'
      );
      console.dir(data);
    },
    
    connection: (status: string, details?: any) => {
      console.log(
        `%c 🔌 WS CONNECTION [${status}] %c ${details ? JSON.stringify(details, null, 2) : ''}`,
        'background: #f3e5f5; color: #6a1b9a; font-weight: bold; padding: 3px 5px; border-radius: 3px;',
        'color: #333; font-weight: normal;'
      );
    }
  }
};

// Helper to log message flows through the system
export const messageFlowTracker = {
  startTracking: (messageId: string, context: string) => {
    console.group(`🔄 Message Flow: ${messageId} - ${context}`);
    console.time(`Message Flow: ${messageId}`);
    return messageId;
  },
  
  addStep: (messageId: string, step: string, data?: any) => {
    console.log(
      `%c Step: ${step} %c`,
      'background: #ede7f6; color: #4527a0; font-weight: bold; padding: 2px 4px; border-radius: 3px;',
      'color: #333; font-weight: normal;'
    );
    if (data) console.dir(data);
  },
  
  endTracking: (messageId: string, status: 'success' | 'error' | 'warning' = 'success') => {
    console.timeEnd(`Message Flow: ${messageId}`);
    console.groupEnd();
    
    // Final status log
    const styles = {
      success: 'background: #e8f5e9; color: #2e7d32;',
      error: 'background: #ffebee; color: #d32f2f;',
      warning: 'background: #fff8e1; color: #ff8f00;'
    };
    
    console.log(
      `%c ✅ Flow Complete: ${messageId} - ${status.toUpperCase()} %c`,
      `${styles[status]} font-weight: bold; padding: 3px 5px; border-radius: 3px;`,
      'color: #333; font-weight: normal;'
    );
  }
};
