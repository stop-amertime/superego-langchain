/**
 * Flow Service
 * Handles API calls related to flows and flow execution
 */
import { API_BASE_URL, fetchWithTimeout, rateLimiter } from './apiUtils.js';

/**
 * Check API health status
 */
export async function checkHealth(): Promise<HealthResponse> {
  return fetchWithTimeout<HealthResponse>(`${API_BASE_URL}/health`);
}

/**
 * Get all available flow definitions
 */
export async function getFlowDefinitions(): Promise<FlowDefinition[]> {
  return fetchWithTimeout<FlowDefinition[]>(`${API_BASE_URL}/flows`);
}

/**
 * Get details for a specific flow definition
 */
export async function getFlowDefinition(flowId: string): Promise<FlowDetail> {
  return fetchWithTimeout<FlowDetail>(
    `${API_BASE_URL}/flow/${encodeURIComponent(flowId)}`
  );
}

/**
 * Get recent flow instances
 */
export async function getFlowInstances(): Promise<FlowInstance[]> {
  return fetchWithTimeout<FlowInstance[]>(`${API_BASE_URL}/flow/instances`);
}

/**
 * Get details for a specific flow instance
 */
export async function getFlowInstance(instanceId: string): Promise<FlowStep[]> {
  return fetchWithTimeout<FlowStep[]>(
    `${API_BASE_URL}/flow/instance/${encodeURIComponent(instanceId)}`
  );
}

/**
 * Create a new flow instance
 */
export async function createNewFlowInstance(flowId: string): Promise<FlowInstance> {
  return fetchWithTimeout<FlowInstance>(
    `${API_BASE_URL}/flow/create_instance`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ flow_id: flowId })
    }
  );
}

/**
 * Execute a flow with POST request
 */
export async function executeFlowSync(
  flowId: string, 
  input: string, 
  conversationId?: string,
  metadata?: Record<string, any>
): Promise<FlowStep[]> {
  const request: FlowExecuteRequest = {
    flow_id: flowId,
    input,
    ...(conversationId && { conversation_id: conversationId }),
    ...(metadata && { metadata })
  };
  
  return fetchWithTimeout<FlowStep[]>(
    `${API_BASE_URL}/flow/execute`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    },
    30000 // Longer timeout for flow execution
  );
}

/**
 * Execute a flow with Server-Sent Events for streaming
 * Returns a cleanup function and reconnection controls
 */
export function executeFlow(
  flowId: string, 
  input: string, 
  onEvent: (event: StreamingEvent) => void,
  options: {
    conversationId?: string;
    metadata?: Record<string, any>;
    enableReconnect?: boolean;
    maxReconnectAttempts?: number;
    initialBackoffMs?: number;
  } = {}
): { cleanup: () => void; reconnect: () => void } {
  // Default options
  const {
    conversationId,
    metadata,
    enableReconnect = true,
    maxReconnectAttempts = 5,
    initialBackoffMs = 1000
  } = options;
  
  // EventSource and reconnection state
  let eventSource: EventSource | null = null;
  let reconnectionState = {
    attempt: 0,
    maxAttempts: maxReconnectAttempts,
    backoffMs: initialBackoffMs,
    timer: null as number | null
  };
  
  // Create params for the request
  const params = new URLSearchParams({
    flow_id: flowId,
    input: input
  });
  
  if (conversationId) {
    params.append('conversation_id', conversationId);
  }
  
  if (metadata) {
    params.append('metadata', JSON.stringify(metadata));
  }
  
  // Function to create and set up EventSource
  function setupEventSource() {
    if (eventSource) {
      eventSource.close();
    }
    
    eventSource = new EventSource(`${API_BASE_URL}/flow/execute?${params}`);
    
    // Set up event listeners
    eventSource.addEventListener('partial_output', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        onEvent({
          type: 'partial_output',
          data: data.data
        });
        // Reset reconnection state on successful events
        reconnectionState.attempt = 0;
        reconnectionState.backoffMs = initialBackoffMs;
      } catch (error) {
        console.error('Error parsing partial_output event:', error);
      }
    });
    
    eventSource.addEventListener('complete_step', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        onEvent({
          type: 'complete_step',
          data: data.data
        });
        // Reset reconnection state on successful events
        reconnectionState.attempt = 0;
        reconnectionState.backoffMs = initialBackoffMs;
      } catch (error) {
        console.error('Error parsing complete_step event:', error);
      }
    });
    
    eventSource.addEventListener('error', (event: MessageEvent | Event) => {
      // Try to extract error data if possible
      let errorData = { message: 'Unknown error occurred' };
      
      try {
        if ('data' in event && event.data) {
          errorData = JSON.parse(event.data);
        }
      } catch (parseError) {
        console.error('Error parsing error event data:', parseError);
      }
      
      // Send error event to handler
      onEvent({
        type: 'error',
        data: errorData
      });
      
      // Handle connection errors
      if (eventSource && eventSource.readyState === EventSource.CLOSED) {
        eventSource.close();
        
        // Attempt reconnection if enabled
        if (enableReconnect && reconnectionState.attempt < reconnectionState.maxAttempts) {
          reconnectionState.attempt++;
          const backoff = reconnectionState.backoffMs * Math.pow(1.5, reconnectionState.attempt - 1);
          
          // Notify about reconnection attempt
          onEvent({
            type: 'error',
            data: {
              message: `Connection lost. Reconnecting in ${backoff / 1000} seconds (attempt ${reconnectionState.attempt}/${reconnectionState.maxAttempts})`,
              code: 'RECONNECTING'
            }
          });
          
          // Schedule reconnection
          if (reconnectionState.timer) {
            clearTimeout(reconnectionState.timer);
          }
          
          reconnectionState.timer = window.setTimeout(() => {
            setupEventSource();
          }, backoff);
        } else if (reconnectionState.attempt >= reconnectionState.maxAttempts) {
          // Maximum reconnection attempts reached
          onEvent({
            type: 'error',
            data: {
              message: 'Maximum reconnection attempts reached. Please try again later.',
              code: 'MAX_RECONNECT_ATTEMPTS'
            }
          });
        }
      }
    });
  }
  
  // Initial setup
  setupEventSource();
  
  // Return cleanup and reconnect functions
  return {
    cleanup: () => {
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
      // Manual reconnection
      reconnectionState.attempt = 0;
      reconnectionState.backoffMs = initialBackoffMs;
      if (reconnectionState.timer) {
        clearTimeout(reconnectionState.timer);
        reconnectionState.timer = null;
      }
      setupEventSource();
    }
  };
}
