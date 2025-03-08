import { v4 as uuidv4 } from 'uuid';
import { WebSocketMessageType, WebSocketMessage, Message, SuperegoEvaluation, AssistantResponse } from '../types';
import { debugMessageTypes, messageFlowTracker } from './debugHelper';

// Default WebSocket URL
const WS_URL = 'ws://localhost:8000/ws';

export interface WebSocketClientCallbacks {
  onOpen?: () => void;
  onClose?: () => void;
  onConnectionError?: (error: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onSuperEgoEvaluation?: (evaluation: SuperegoEvaluation) => void;
  onAssistantMessage?: (message: AssistantResponse) => void;
  onAssistantToken?: (id: string, token: string) => void;
  onSystemMessage?: (content: string) => void;
  onError?: (error: string) => void;
  onReconnectAttempt?: (attempt: number, maxAttempts: number) => void;
  onConnecting?: () => void;
  onConversationUpdate?: (messages: any[], replace: boolean) => void;
}

export class WebSocketClient {
  private socket: WebSocket | null = null;
  private clientId: string;
  private connected = false;
  private connecting = false;
  private queue: string[] = [];
  private callbacks: WebSocketClientCallbacks;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10; // Increased from 5
  private reconnectDelay = 1000; // Base delay in ms
  private reconnectTimeout: number | null = null;
  private url: string;
  private lastConnectionAttempt = 0;
  private currentConversationId: string | null = null;

  constructor(callbacks: WebSocketClientCallbacks = {}, url: string = WS_URL) {
    this.clientId = uuidv4();
    this.callbacks = callbacks;
    this.url = url;
    debugMessageTypes.log('WebSocketClient.constructor', `Created new client with ID: ${this.clientId}`);
  }

  public getReconnectAttempts(): number {
    return this.reconnectAttempts;
  }

  public getMaxReconnectAttempts(): number {
    return this.maxReconnectAttempts;
  }

  public isConnecting(): boolean {
    return this.connecting;
  }

  public connect(): void {
    // Avoid rapid reconnection attempts
    const now = Date.now();
    if (now - this.lastConnectionAttempt < 1000) {
      debugMessageTypes.warn('WebSocketClient.connect', 'Throttling connection attempts');
      return;
    }
    this.lastConnectionAttempt = now;

    if (this.socket?.readyState === WebSocket.OPEN || this.socket?.readyState === WebSocket.CONNECTING) {
      debugMessageTypes.websocket.connection('ALREADY_CONNECTED');
      return;
    }

    // Set connecting state
    this.connecting = true;
    if (this.callbacks.onConnecting) {
      this.callbacks.onConnecting();
    }

    try {
      // Connect with the client ID
      const wsUrl = `${this.url}/${this.clientId}`;
      debugMessageTypes.websocket.connection('CONNECTING', { url: wsUrl });
      console.log('Connecting to WebSocket:', wsUrl);
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = this.handleOpen.bind(this);
      this.socket.onclose = this.handleClose.bind(this);
      this.socket.onerror = this.handleError.bind(this);
      this.socket.onmessage = this.handleMessage.bind(this);
    } catch (error) {
      debugMessageTypes.error('WebSocketClient.connect', error);
      this.handleError(new Event('error'));
    }
  }

  public disconnect(): void {
    if (this.socket) {
      debugMessageTypes.websocket.connection('DISCONNECTING');
      this.socket.close();
      this.socket = null;
      this.connected = false;
    }

    // Clear any reconnect timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  /**
   * Sets the current active conversation ID for this client
   */
  public setConversationId(conversationId: string): void {
    this.currentConversationId = conversationId;
    debugMessageTypes.log('WebSocketClient.setConversationId', `Set conversation ID to ${conversationId}`);
  }

  /**
   * Gets the current active conversation ID
   */
  public getConversationId(): string | null {
    return this.currentConversationId;
  }

  /**
   * Send a command to the server
   * @param type The command type
   * @param payload The command payload
   * @param conversationId Optional conversation ID (uses current conversation ID if not provided)
   */
  public sendCommand(type: string | WebSocketMessageType, payload: Record<string, any> = {}, conversationId?: string): void {
    const messageId = uuidv4();
    messageFlowTracker.startTracking(messageId, `Command: ${type}`);
    
    // Use provided conversation ID or fall back to the client's current one
    const actualConversationId = conversationId || this.currentConversationId;
    
    // Create the complete command with all necessary fields
    const command = {
      type: type,
      ...payload,
      conversation_id: actualConversationId,
      client_message_id: messageId
    };
    
    const data = JSON.stringify(command);
    
    messageFlowTracker.addStep(messageId, `Preparing to send command: ${type}`, command);
    
    // Check if socket is in a valid state
    if (this.connected && this.socket?.readyState === WebSocket.OPEN) {
      try {
        debugMessageTypes.websocket.sent(type, { command, messageId });
        this.socket.send(data);
        messageFlowTracker.addStep(messageId, 'Command sent to server');
      } catch (error) {
        debugMessageTypes.error('WebSocketClient.sendCommand', `Error sending command: ${error}`);
        this.queue.push(data);
        this.reconnect();
      }
    } else {
      debugMessageTypes.websocket.connection('NOT_CONNECTED_QUEUING');
      this.queue.push(data);
      messageFlowTracker.addStep(messageId, 'Command queued, connection not ready');
      this.connect();
    }
  }
  
  /**
   * Send a user message to the server
   */
  public sendMessage(message: string, conversationId?: string): void {
    const messageId = uuidv4();
    messageFlowTracker.startTracking(messageId, 'User Message');
    
    // Use provided conversation ID or fall back to the client's current one
    const actualConversationId = conversationId || this.currentConversationId;
    
    const data = JSON.stringify({
      type: WebSocketMessageType.USER_MESSAGE,
      content: message,
      conversation_id: actualConversationId,
      client_message_id: messageId // Added for tracking
    });

    messageFlowTracker.addStep(messageId, 'Preparing to send message', {
      type: WebSocketMessageType.USER_MESSAGE,
      content: message,
      conversation_id: actualConversationId
    });

    // Check if socket is in a valid state
    if (this.connected && this.socket?.readyState === WebSocket.OPEN) {
      try {
        debugMessageTypes.websocket.sent('USER_MESSAGE', { message, conversationId, messageId });
        this.socket.send(data);
        messageFlowTracker.addStep(messageId, 'Message sent to server');
      } catch (error) {
        debugMessageTypes.error('WebSocketClient.sendMessage', `Error sending message: ${error}`);
        this.queue.push(data);
        this.reconnect();
      }
    } else {
      debugMessageTypes.websocket.connection('NOT_CONNECTED_QUEUING');
      this.queue.push(data);
      messageFlowTracker.addStep(messageId, 'Message queued, connection not ready');
      this.connect();
    }
  }

  private handleOpen(event: Event): void {
    debugMessageTypes.websocket.connection('ESTABLISHED');
    this.connected = true;
    this.connecting = false;
    this.reconnectAttempts = 0;

    console.log('WebSocket connection established');

    // Call onOpen callback immediately to update UI
    if (this.callbacks.onOpen) {
      this.callbacks.onOpen();
    }

    // Process any queued messages immediately
    const queuedCount = this.queue.length;
    if (queuedCount > 0) {
      debugMessageTypes.log('WebSocketClient.handleOpen', `Processing ${queuedCount} queued messages`);
    }
    
    while (this.queue.length > 0) {
      const message = this.queue.shift();
      if (message && this.socket && this.socket.readyState === WebSocket.OPEN) {
        try {
          debugMessageTypes.websocket.sent('QUEUED_MESSAGE', { message });
          this.socket.send(message);
        } catch (error) {
          debugMessageTypes.error('WebSocketClient.handleOpen', `Error sending queued message: ${error}`);
          // Put the message back in the queue
          this.queue.unshift(message);
          break;
        }
      } else if (message) {
        // Put the message back in the queue if we can't send it yet
        this.queue.unshift(message);
        break;
      }
    }
  }

  private handleClose(event: CloseEvent): void {
    debugMessageTypes.websocket.connection('CLOSED', { code: event.code, reason: event.reason });
    this.connected = false;
    this.socket = null;

    console.log('WebSocket connection closed:', event.code, event.reason);

    // Attempt to reconnect if not a normal closure and not at max attempts
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      
      // Notify about reconnect attempt
      if (this.callbacks.onReconnectAttempt) {
        this.callbacks.onReconnectAttempt(this.reconnectAttempts, this.maxReconnectAttempts);
      }
      
      // Exponential backoff with jitter to avoid thundering herd
      const jitter = Math.random() * 0.3 + 0.85; // Random factor between 0.85 and 1.15
      const delay = Math.min(this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts) * jitter, 30000);
      
      debugMessageTypes.websocket.connection('RECONNECT_SCHEDULED', { 
        delay, 
        attempt: this.reconnectAttempts,
        maxAttempts: this.maxReconnectAttempts
      });
      
      this.reconnectTimeout = window.setTimeout(() => {
        debugMessageTypes.log('WebSocketClient.reconnect', `Attempting reconnect #${this.reconnectAttempts}`);
        this.connect();
      }, delay);
    } else {
      debugMessageTypes.error('WebSocketClient.handleClose', 
        `Maximum reconnection attempts (${this.maxReconnectAttempts}) reached. Giving up.`);
      this.connecting = false;
    }

    if (this.callbacks.onClose) {
      this.callbacks.onClose();
    }
  }

  private handleError(event: Event): void {
    debugMessageTypes.error('WebSocketClient.handleError', event);
    console.error('WebSocket error:', event);
    
    this.connecting = false;
    
    if (this.callbacks.onConnectionError) {
      this.callbacks.onConnectionError(event);
    }
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data) as WebSocketMessage;
      
      // General message handler
      if (this.callbacks.onMessage) {
        this.callbacks.onMessage(message);
      }
      
      // Type-specific handlers
      switch (message.type) {
        case WebSocketMessageType.CONVERSATION_UPDATE:
          if (this.callbacks.onConversationUpdate) {
            debugMessageTypes.log('WebSocketClient.handleMessage', 'Processing CONVERSATION_UPDATE');
            // Handle conversation update message
            if (typeof message.content === 'object' && message.content !== null) {
              const { messages, replace } = message.content;
              if (Array.isArray(messages)) {
                this.callbacks.onConversationUpdate(messages, replace === true);
              } else {
                debugMessageTypes.error('WebSocketClient.handleMessage', {
                  error: 'Invalid CONVERSATION_UPDATE content format',
                  content: message.content
                });
              }
            } else {
              debugMessageTypes.error('WebSocketClient.handleMessage', {
                error: 'Invalid CONVERSATION_UPDATE content format',
                content: message.content
              });
            }
          }
          break;
          
        case WebSocketMessageType.CREATE_CONSTITUTION:
        case WebSocketMessageType.UPDATE_CONSTITUTION:
        case WebSocketMessageType.DELETE_CONSTITUTION:
          // These are outgoing message types, not incoming
          break;
          
        case WebSocketMessageType.SUPEREGO_EVALUATION:
          if (this.callbacks.onSuperEgoEvaluation) {
            debugMessageTypes.log('WebSocketClient.handleMessage', 'Processing SUPEREGO_EVALUATION');
            // Ensure the content is properly formatted as SuperegoEvaluation
            if (typeof message.content === 'object' && message.content !== null) {
              this.callbacks.onSuperEgoEvaluation(message.content as SuperegoEvaluation);
            } else {
              debugMessageTypes.error('WebSocketClient.handleMessage', {
                error: 'Invalid SUPEREGO_EVALUATION content format',
                content: message.content
              });
            }
          }
          break;
        
        case WebSocketMessageType.CONSTITUTIONS_RESPONSE:
          debugMessageTypes.log('WebSocketClient.handleMessage', 'Processing CONSTITUTIONS_RESPONSE');
          // This is handled by the onMessage callback, no specific handler needed
          break;
        
        case WebSocketMessageType.ASSISTANT_MESSAGE:
          if (this.callbacks.onAssistantMessage) {
            debugMessageTypes.log('WebSocketClient.handleMessage', 'Processing ASSISTANT_MESSAGE');
            // Ensure the content is properly formatted as AssistantResponse
            if (typeof message.content === 'object' && message.content !== null) {
              this.callbacks.onAssistantMessage(message.content as AssistantResponse);
            } else {
              debugMessageTypes.error('WebSocketClient.handleMessage', {
                error: 'Invalid ASSISTANT_MESSAGE content format',
                content: message.content
              });
            }
          }
          break;
          
        case WebSocketMessageType.ASSISTANT_TOKEN:
          if (this.callbacks.onAssistantToken) {
            debugMessageTypes.log('WebSocketClient.handleMessage', 'Processing ASSISTANT_TOKEN');
            // Ensure the content is properly formatted
            if (typeof message.content === 'object' && message.content !== null) {
              const { id, token } = message.content;
              if (id && token) {
                this.callbacks.onAssistantToken(id, token);
              } else {
                debugMessageTypes.error('WebSocketClient.handleMessage', {
                  error: 'Invalid ASSISTANT_TOKEN content format',
                  content: message.content
                });
              }
            } else {
              debugMessageTypes.error('WebSocketClient.handleMessage', {
                error: 'Invalid ASSISTANT_TOKEN content format',
                content: message.content
              });
            }
          }
          break;
        
        case WebSocketMessageType.SYSTEM_MESSAGE:
          if (this.callbacks.onSystemMessage) {
            debugMessageTypes.log('WebSocketClient.handleMessage', 'Processing SYSTEM_MESSAGE');
            this.callbacks.onSystemMessage(message.content as string);
          }
          break;
        
        case WebSocketMessageType.ERROR:
          if (this.callbacks.onError) {
            debugMessageTypes.error('WebSocketClient.handleMessage', 'Processing ERROR message');
            this.callbacks.onError(message.content as string);
          }
          break;
      }
    } catch (error) {
      debugMessageTypes.error('WebSocketClient.handleMessage', { 
        error, 
        data: event.data,
        message: 'Error parsing WebSocket message'
      });
    }
  }

  // Force a reconnection, useful for error handling
  private reconnect(): void {
    this.disconnect();
    // Minimal delay to avoid immediate reconnection
    setTimeout(() => this.connect(), 250);
  }

  public isConnected(): boolean {
    return this.connected;
  }

  public getClientId(): string {
    return this.clientId;
  }
  
  // Method to update callbacks without recreating the WebSocket connection
  public updateCallbacks(callbacks: WebSocketClientCallbacks): void {
    debugMessageTypes.log('WebSocketClient.updateCallbacks', 'Updating callbacks');
    this.callbacks = {
      ...this.callbacks,
      ...callbacks
    };
  }
}

// Singleton instance
let instance: WebSocketClient | null = null;
let registeredCallbacks: WebSocketClientCallbacks = {};

export const getWebSocketClient = (callbacks?: WebSocketClientCallbacks): WebSocketClient => {
  // Update registered callbacks if provided
  if (callbacks) {
    debugMessageTypes.log('getWebSocketClient', 'Updating callbacks');
    registeredCallbacks = {
      ...registeredCallbacks,
      ...callbacks
    };
  }
  
  if (!instance) {
    // First time initialization - create a new instance with the current callbacks
    debugMessageTypes.log('getWebSocketClient', 'Creating new WebSocketClient instance');
    instance = new WebSocketClient(registeredCallbacks);
  } else if (callbacks) {
    // Only update the internal callbacks of the existing instance
    // but DO NOT recreate the entire client
    debugMessageTypes.log('getWebSocketClient', 'Updating existing WebSocketClient callbacks');
    instance.updateCallbacks(registeredCallbacks);
  }
  
  return instance;
};
