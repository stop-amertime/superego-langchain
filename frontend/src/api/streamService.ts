/**
 * Stream Service
 * Specialized service for handling Server-Sent Events (SSE) connections
 */
import { API_BASE_URL } from './apiUtils.js';

/**
 * Default reconnection options
 */
const DEFAULT_RECONNECTION_OPTIONS = {
  enableReconnect: true,
  maxReconnectAttempts: 5,
  initialBackoffMs: 1000,
  backoffMultiplier: 1.5
};

/**
 * Create an SSE connection with the specified endpoint
 * Handles reconnection logic and event parsing
 */
export function createEventSource(
  endpoint: string,
  params: Record<string, string>,
  eventHandlers: {
    onMessage?: (event: MessageEvent) => void;
    onEvent?: (type: string, data: any) => void;
    onOpen?: () => void;
    onError?: (error: any) => void;
    onReconnecting?: (attempt: number, maxAttempts: number, timeoutMs: number) => void;
    onMaxReconnectAttemptsReached?: () => void;
  },
  options: {
    enableReconnect?: boolean;
    maxReconnectAttempts?: number;
    initialBackoffMs?: number;
    backoffMultiplier?: number;
  } = {}
): { 
  close: () => void;
  reconnect: () => void;
  isConnected: () => boolean;
} {
  // Merge default options with provided options
  const reconnectOptions = {
    ...DEFAULT_RECONNECTION_OPTIONS,
    ...options
  };
  
  // EventSource and reconnection state
  let eventSource: EventSource | null = null;
  let isConnecting = false;
  let isClosed = false;
  let reconnectionState = {
    attempt: 0,
    maxAttempts: reconnectOptions.maxReconnectAttempts,
    backoffMs: reconnectOptions.initialBackoffMs,
    timer: null as number | null
  };
  
  // Create URL with query parameters
  function buildUrl(): string {
    // Create a URLSearchParams object for the query string
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value);
      }
    });
    
    // For EventSource, we need to use the /flow path directly
    // because Vite is configured to proxy /flow to the backend
    // This matches the pattern in flowService.ts which works
    return `/flow/execute?${searchParams}`;
  }
  
  // Function to create and set up the EventSource
  function setupEventSource() {
    if (eventSource) {
      eventSource.close();
    }
    
    if (isClosed) return;
    
    isConnecting = true;
    eventSource = new EventSource(buildUrl());
    
    // Generic message handler
    if (eventHandlers.onMessage) {
      eventSource.onmessage = eventHandlers.onMessage;
    }
    
    // Connection opened handler
    eventSource.onopen = () => {
      isConnecting = false;
      
      // Reset reconnection state on successful connection
      reconnectionState.attempt = 0;
      reconnectionState.backoffMs = reconnectOptions.initialBackoffMs;
      
      if (eventHandlers.onOpen) {
        eventHandlers.onOpen();
      }
    };
    
    // Error handler and reconnection logic
    eventSource.onerror = (error) => {
      // Handle immediate connection errors
      if (eventHandlers.onError) {
        eventHandlers.onError(error);
      }
      
      // Close connection if error occurred
      if (eventSource) {
        eventSource.close();
      }
      
      // Skip reconnection if manually closed or reconnection disabled
      if (isClosed || !reconnectOptions.enableReconnect) {
        return;
      }
      
      // Attempt reconnection if not at max attempts
      if (reconnectionState.attempt < reconnectionState.maxAttempts) {
        reconnectionState.attempt++;
        
        // Use exponential backoff for retry
        const timeoutMs = Math.floor(
          reconnectionState.backoffMs * 
          Math.pow(reconnectOptions.backoffMultiplier, reconnectionState.attempt - 1)
        );
        
        // Notify about reconnection attempt
        if (eventHandlers.onReconnecting) {
          eventHandlers.onReconnecting(
            reconnectionState.attempt,
            reconnectionState.maxAttempts,
            timeoutMs
          );
        }
        
        // Schedule reconnection
        if (reconnectionState.timer) {
          clearTimeout(reconnectionState.timer);
        }
        
        reconnectionState.timer = window.setTimeout(() => {
          setupEventSource();
        }, timeoutMs);
      } else if (eventHandlers.onMaxReconnectAttemptsReached) {
        // Maximum reconnection attempts reached
        eventHandlers.onMaxReconnectAttemptsReached();
      }
    };
    
    // Handle typed events (if event type handlers are provided)
    if (eventHandlers.onEvent) {
      // Setup for the three standard event types used by the backend
      ['partial_output', 'complete_step', 'error'].forEach(eventType => {
        eventSource?.addEventListener(eventType, (event: MessageEvent) => {
          try {
            // Only try to parse if data exists and is not undefined
            if (event.data) {
              const data = JSON.parse(event.data);
              eventHandlers.onEvent?.(eventType, data.data || data);
            } else if (eventType === 'error') {
              // Handle case where error event doesn't have data
              eventHandlers.onEvent?.(eventType, { message: 'Connection error' });
            }
          } catch (parseError) {
            console.error(`Error parsing ${eventType} event:`, parseError);
            // Still notify with a generic error if parsing fails
            if (eventType === 'error') {
              eventHandlers.onEvent?.(eventType, { message: 'Error processing server response' });
            }
          }
        });
      });
    }
  }
  
  // Initial EventSource setup
  setupEventSource();
  
  // Return control methods
  return {
    close: () => {
      isClosed = true;
      
      if (reconnectionState.timer) {
        clearTimeout(reconnectionState.timer);
        reconnectionState.timer = null;
      }
      
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
    },
    reconnect: () => {
      // Manual reconnection - reset state and reconnect
      reconnectionState.attempt = 0;
      reconnectionState.backoffMs = reconnectOptions.initialBackoffMs;
      
      if (reconnectionState.timer) {
        clearTimeout(reconnectionState.timer);
        reconnectionState.timer = null;
      }
      
      setupEventSource();
    },
    isConnected: () => {
      return eventSource !== null && 
             eventSource.readyState === EventSource.OPEN && 
             !isConnecting;
    }
  };
}

/**
 * Execute a flow with streaming using the createEventSource utility
 */
export function executeFlowStream(
  flowId: string, 
  input: string, 
  eventHandlers: {
    instanceId: string; // Required parameter for flow instance ID
    onPartialOutput?: (output: { partial_output: string; complete?: boolean }) => void;
    onCompleteStep?: (step: FlowStep) => void;
    onError?: (error: { message: string; code?: string }) => void;
    onOpen?: () => void;
    onReconnecting?: (attempt: number, maxAttempts: number, timeoutMs: number) => void;
    onMaxReconnectAttemptsReached?: () => void;
  },
  options?: {
    conversationId?: string;
    metadata?: Record<string, any>;
    enableReconnect?: boolean;
    maxReconnectAttempts?: number;
    initialBackoffMs?: number;
  }
) {
  // Prepare parameters
  const params: Record<string, string> = {
    flow_id: flowId,
    input: input,
    instance_id: eventHandlers.instanceId // Always include instance_id
  };
  
  if (options?.conversationId) {
    params.conversation_id = options.conversationId;
  }
  
  if (options?.metadata) {
    params.metadata = JSON.stringify(options.metadata);
  }
  
  // Create and return an event source with typed event handling
  return createEventSource(
    'flow/execute',
    params,
    {
      onEvent: (type, data) => {
        switch (type) {
          case 'partial_output':
            eventHandlers.onPartialOutput?.(data);
            break;
          case 'complete_step':
            eventHandlers.onCompleteStep?.(data);
            break;
          case 'error':
            eventHandlers.onError?.(data);
            break;
        }
      },
      onOpen: eventHandlers.onOpen,
      onError: (error) => {
        // Only call onError for non-reconnection errors
        // (reconnection is handled separately through onReconnecting)
        if (!options?.enableReconnect && eventHandlers.onError) {
          eventHandlers.onError({ 
            message: 'Connection error', 
            code: 'CONNECTION_ERROR' 
          });
        }
      },
      onReconnecting: eventHandlers.onReconnecting,
      onMaxReconnectAttemptsReached: eventHandlers.onMaxReconnectAttemptsReached
    },
    {
      enableReconnect: options?.enableReconnect,
      maxReconnectAttempts: options?.maxReconnectAttempts,
      initialBackoffMs: options?.initialBackoffMs
    }
  );
}
