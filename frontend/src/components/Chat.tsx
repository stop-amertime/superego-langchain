import { useState, useEffect, useRef, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { getWebSocketClient, WebSocketClientCallbacks } from '../api/websocketClient';
import { 
  useConstitutions, 
  useSysprompts, 
  useMessageStore,
  useUpdateMessageStore,
  useCreateMessageStore
} from '../api/queryHooks';
import { 
  Message, 
  MessageRole, 
  SuperegoEvaluation, 
  SuperegoDecision, 
  WebSocketMessageType, 
  AssistantResponse 
} from '../types';
import './Chat.css';
import MessageBubble from './MessageBubble';
import SuperegoEvaluationBox from './SuperegoEvaluationBox';
import ChatInput from './ChatInput';
import ChatHeader from './ChatHeader';
import ProcessingIndicator from './ProcessingIndicator';
import StreamingMessage from './StreamingMessage';
import { AppData } from '../App';

interface ChatProps {
  flowInstanceId?: string | null;
  onUserInputChange?: (input: string) => void;
}

const Chat: React.FC<ChatProps> = ({ flowInstanceId: propFlowInstanceId, onUserInputChange }) => {
  // Fetch data using React Query
  const { 
    data: constitutions = [], 
    isLoading: constitutionsLoading, 
    error: constitutionsError 
  } = useConstitutions();
  
  const { 
    data: sysprompts = [], 
    isLoading: syspromptsLoading, 
    error: syspromptsError 
  } = useSysprompts();
  
  // Create appData object from React Query results
  const appData: AppData = {
    constitutions: constitutions || [],
    sysprompts: sysprompts || [],
    constitutionsLoading,
    syspromptsLoading,
    constitutionsError: constitutionsError ? String(constitutionsError) : null,
    syspromptsError: syspromptsError ? String(syspromptsError) : null
  };
  // No need for input state anymore since ChatInput manages it
  
  // State for messages
  const [messages, setMessages] = useState<Message[]>([]);
  
  // State for streaming messages
  const [streamingMessage, setStreamingMessage] = useState<{id: string, content: string} | null>(null);
  const [streamingThinking, setStreamingThinking] = useState<{id: string, thinking: string} | null>(null);
  
  // State for WebSocket connection
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isConnecting, setIsConnecting] = useState<boolean>(true); // Start in connecting state
  const [connectionFailed, setConnectionFailed] = useState<boolean>(false);
  const [reconnectAttempt, setReconnectAttempt] = useState<number>(0);
  const [maxReconnectAttempts, setMaxReconnectAttempts] = useState<number>(10);
  
  // State for loading indicators
  const [isSending, setIsSending] = useState<boolean>(false);
  const [processingStep, setProcessingStep] = useState<number>(0);
  
  // Ref for tracking the timeout that will clear loading state as failsafe
  const loadingTimeoutRef = useRef<number | null>(null);
  
  // State for current superego evaluation
  const [currentEvaluation, setCurrentEvaluation] = useState<SuperegoEvaluation | null>(null);
  
  // Flow instance ID and prompt selections
  const [internalFlowInstanceId, setInternalFlowInstanceId] = useState<string | null>(null);
  const [selectedConstitutionId, setSelectedConstitutionId] = useState<string>('default');
  const [selectedSyspromptId, setSelectedSyspromptId] = useState<string>('assistant_default');
  
  // Use the flow instance ID from props if available, otherwise use internal state
  const flowInstanceId = propFlowInstanceId || internalFlowInstanceId;
  
  // System messages
  const [systemMessage, setSystemMessage] = useState<string | null>(null);
  
  // Ref for message container to auto-scroll
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Clear the loading timeout when component unmounts
  useEffect(() => {
    return () => {
      if (loadingTimeoutRef.current) {
        window.clearTimeout(loadingTimeoutRef.current);
      }
    };
  }, []);
  
  // Initialize flow instance ID and WebSocket client reference
  const wsClientRef = useRef<ReturnType<typeof getWebSocketClient> | null>(null);

  // Fetch message store history using React Query
  const { 
    data: messageStoreData, 
    isLoading: isLoadingMessageStore,
    error: messageStoreError
  } = useMessageStore(
    flowInstanceId || '', 
    undefined, // No limit
    undefined  // No offset
  );
  
  // Mutations for message store management
  const updateMessageStoreMutation = useUpdateMessageStore(flowInstanceId || '');
  const createMessageStoreMutation = useCreateMessageStore();
  
  // Initialize flow instance ID from props and fetch conversation history
  useEffect(() => {
    if (propFlowInstanceId) {
      setInternalFlowInstanceId(propFlowInstanceId);
      
      // Set the flow instance ID in the WebSocket client 
      const wsClient = getWebSocketClient();
      wsClient.setFlowInstanceId(propFlowInstanceId);
      
      // Clear messages when switching instances
      setMessages([]);
      setStreamingMessage(null);
      setStreamingThinking(null);
      setCurrentEvaluation(null);
      
      // System message is handled by the loading state of useMessageStore
      if (isLoadingMessageStore) {
        setSystemMessage('Loading message history...');
      }
    }
  }, [propFlowInstanceId]);
  
  // Handle 404 errors by creating a new message store
  useEffect(() => {
    if (messageStoreError && flowInstanceId) {
      console.log('Message store not found, creating a new one for flow instance:', flowInstanceId);
      createMessageStoreMutation.mutate(undefined, {
        onSuccess: (data) => {
          console.log('Created new message store:', data);
          // No need to do anything else, the message store will be loaded automatically
        }
      });
    }
  }, [messageStoreError, flowInstanceId, createMessageStoreMutation]);
  
  // Update messages when message store data changes
  useEffect(() => {
    if (messageStoreData && messageStoreData.messages) {
      // Convert the message data to our Message type format
      const convertedMessages = messageStoreData.messages.map((msgData: any) => ({
        id: msgData.id,
        role: msgData.role,
        content: msgData.content,
        timestamp: msgData.timestamp,
        decision: msgData.decision,
        constitutionId: msgData.constitutionId,
        thinking: msgData.thinking,
        thinkingTime: msgData.thinkingTime,
        withoutSuperego: msgData.withoutSuperego
      } as Message));
      
      setMessages(convertedMessages);
      setSystemMessage('Messages loaded');
    }
  }, [messageStoreData]);

  // Initialize WebSocket connection
  useEffect(() => {
    const callbacks: WebSocketClientCallbacks = {
      onOpen: () => {
        setIsConnected(true);
        setIsConnecting(false);
        setConnectionFailed(false);
        setReconnectAttempt(0);
        setSystemMessage('Connected to server');
      },
      onClose: () => {
        setIsConnected(false);
        setConnectionFailed(true);
        setIsConnecting(false);
        setSystemMessage('Disconnected from server');
      },
      onConnectionError: (error) => {
        setIsConnected(false);
        setIsConnecting(false);
        setConnectionFailed(true);
        setSystemMessage('Error connecting to server');
      },
      onConnecting: () => {
        setIsConnecting(true);
        setConnectionFailed(false);
        setSystemMessage('Connecting to server...');
      },
      onReconnectAttempt: (attempt, maxAttempts) => {
        setIsConnecting(true);
        setConnectionFailed(false);
        setReconnectAttempt(attempt);
        setMaxReconnectAttempts(maxAttempts);
        setSystemMessage(`Reconnecting (attempt ${attempt}/${maxAttempts})...`);
      },
      // We no longer need the onConversationUpdate handler as we're using REST API
      onSuperEgoEvaluation: (evaluation) => {
        // Validate the evaluation object
        if (!evaluation) {
          return;
        }
        
        // Check for duplicate evaluation to prevent loops
        if (evaluation.id && 
            evaluation.status === 'completed' && 
            messages.some(m => m.id === evaluation.id)) {
          return;
        }
        
        // Update processing step
        if (evaluation.status === 'started') {
          setProcessingStep(1); // Evaluation started
        }
        
        // Handle thinking status
        if (evaluation.status === 'thinking' && evaluation.thinking) {
          setStreamingThinking(prev => {
            const thinkingContent = evaluation.thinking || '';
            const evaluationId = evaluation.id || uuidv4();
            
            if (!prev || prev.id !== evaluationId) {
              return { id: evaluationId, thinking: thinkingContent };
            }
            
            return { id: prev.id, thinking: prev.thinking + thinkingContent };
          });
          
          setCurrentEvaluation(evaluation);
          return;
        }
        
        // Update the evaluation state
        setCurrentEvaluation(evaluation);
        
        // If evaluation is completed, add to messages
        if (evaluation.status === 'completed') {
          setProcessingStep(2); // Evaluation completed
          
          const evaluationId = evaluation.id || uuidv4();
          
          const superEgoMessage: Message = {
            id: evaluationId,
            role: MessageRole.SUPEREGO,
            content: evaluation.reason || '',
            timestamp: new Date().toISOString(),
            decision: evaluation.decision,
            thinking: evaluation.thinking
          };
          
          // Add to messages if not a duplicate
          setMessages(prev => {
            if (!prev.some(m => m.id === superEgoMessage.id)) {
              const newMessages = [...prev, superEgoMessage];
              
              // Update message store in the backend via REST API
              if (flowInstanceId) {
                // Convert Message objects to plain objects
                const messagesToSave = newMessages.map(msg => ({
                  id: msg.id,
                  role: msg.role,
                  content: msg.content,
                  timestamp: msg.timestamp,
                  decision: msg.decision,
                  constitutionId: msg.constitutionId,
                  syspromptId: msg.syspromptId,
                  thinking: msg.thinking,
                  thinkingTime: msg.thinkingTime,
                  withoutSuperego: msg.withoutSuperego
                }));
                updateMessageStoreMutation.mutate(messagesToSave);
              }
              
              return newMessages;
            }
            return prev;
          });
          
          setStreamingThinking(null);
        }
      },
      onAssistantToken: (id, token) => {
        // Mark processing step when we start getting tokens
        if (!streamingMessage) {
          setProcessingStep(3); // Generating response
        }
        
        // Update streaming message content
        setStreamingMessage(prev => {
          if (!prev || prev.id !== id) {
            return { id, content: token };
          }
          return { id, content: prev.content + token };
        });
      },
      
      onAssistantMessage: (message) => {
        // Validate message
        if (!message) {
          return;
        }
        
        // Check for duplicate message
        if (message.id && messages.some(m => m.id === message.id)) {
          return;
        }
        
        // Clear timeout and evaluation state
        if (loadingTimeoutRef.current) {
          window.clearTimeout(loadingTimeoutRef.current);
          loadingTimeoutRef.current = null;
        }
        
        setCurrentEvaluation(null);
        
        const messageId = message.id || uuidv4();
        
        const assistantMessage: Message = {
          id: messageId,
          role: MessageRole.ASSISTANT,
          content: typeof message.content === 'string' ? message.content : JSON.stringify(message.content),
          timestamp: new Date().toISOString()
        };
        
        // Add message if not a duplicate
        setMessages(prev => {
          if (!prev.some(m => m.id === assistantMessage.id)) {
            const newMessages = [...prev, assistantMessage];
            
            // Update message store in the backend via REST API
            if (flowInstanceId) {
              // Convert Message objects to plain objects
              const messagesToSave = newMessages.map(msg => ({
                id: msg.id,
                role: msg.role,
                content: msg.content,
                timestamp: msg.timestamp,
                decision: msg.decision,
                constitutionId: msg.constitutionId,
                syspromptId: msg.syspromptId,
                thinking: msg.thinking,
                thinkingTime: msg.thinkingTime,
                withoutSuperego: msg.withoutSuperego
              }));
              updateMessageStoreMutation.mutate(messagesToSave);
            }
            
            return newMessages;
          }
          return prev;
        });
        
        // Reset UI state
        setStreamingMessage(null);
        setIsSending(false);
      },
      onSystemMessage: (content) => {
        // Only update connection-related messages
        const connectionKeywords = ['Connected', 'Disconnected', 'Connecting', 'Reconnecting'];
        if (connectionKeywords.some(keyword => content.includes(keyword))) {
          setSystemMessage(content);
        }
      },
      onError: (error) => {
        // Clear loading state on error
        if (loadingTimeoutRef.current) {
          window.clearTimeout(loadingTimeoutRef.current);
          loadingTimeoutRef.current = null;
        }
        
        setSystemMessage(`Error: ${error}`);
        setIsSending(false);
      }
    };
    
    // Store the websocket client reference
    wsClientRef.current = getWebSocketClient(callbacks);
    wsClientRef.current.connect();
    
    return () => {
      // Only disconnect if the component is unmounting
      // Don't disconnect on dependency changes to avoid the connect/disconnect cycle
      if (wsClientRef.current) {
        console.log('Component unmounting, disconnecting WebSocket');
        wsClientRef.current.disconnect();
      }
    };
  }, []); // No dependencies to avoid re-runs
  
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentEvaluation]);
  
  // Function to manually reconnect
  const handleManualReconnect = () => {
    if (wsClientRef.current) {
      wsClientRef.current.connect();
    }
  };

  // Handle message submission
  const handleSendMessage = useCallback((message: string) => {
    if (!message.trim() || isSending) return;
    
    // Notify parent of input change if callback is provided
    if (onUserInputChange) {
      onUserInputChange(message);
    }
    
    // Add user message to UI
    const userMessage: Message = {
      id: uuidv4(),
      role: MessageRole.USER,
      content: message,
      timestamp: new Date().toISOString()
    };
    
    // Update messages state and persist to backend
    setMessages(prev => {
      const newMessages = [...prev, userMessage];
      
      // Update message store in the backend via REST API
      if (flowInstanceId) {
        // Convert Message objects to plain objects
        const messagesToSave = newMessages.map(msg => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp,
          decision: msg.decision,
          constitutionId: msg.constitutionId,
          syspromptId: msg.syspromptId,
          thinking: msg.thinking,
          thinkingTime: msg.thinkingTime,
          withoutSuperego: msg.withoutSuperego
        }));
        updateMessageStoreMutation.mutate(messagesToSave);
      }
      
      return newMessages;
    });
    
    // Send via WebSocket using the direct command sending method
    const wsClient = getWebSocketClient();
    wsClient.sendCommand('user_message', {
      content: message,
      constitution_id: selectedConstitutionId,
      sysprompt_id: selectedSyspromptId
    }, flowInstanceId || undefined);
    
    // Update UI state
    setIsSending(true);
    setProcessingStep(0);
    
    // Set timeout to clear loading state
    if (loadingTimeoutRef.current) {
      window.clearTimeout(loadingTimeoutRef.current);
    }
    
    const TIMEOUT_MS = 60000; // 60 seconds
    loadingTimeoutRef.current = window.setTimeout(() => {
      setIsSending(false);
      setCurrentEvaluation(null);
      setSystemMessage('Request timed out. Please try again.');
    }, TIMEOUT_MS);
  }, [flowInstanceId, isSending, selectedConstitutionId, selectedSyspromptId, onUserInputChange]);
  
  // Cancel message processing
  const handleCancelProcessing = useCallback(() => {
    if (loadingTimeoutRef.current) {
      window.clearTimeout(loadingTimeoutRef.current);
      loadingTimeoutRef.current = null;
    }
    setIsSending(false);
    setCurrentEvaluation(null);
    setSystemMessage('Message processing cancelled.');
  }, []);

  // Handle message rerun
  const handleRerun = useCallback((messageId: string, constitutionId: string, syspromptId: string) => {
    const wsClient = getWebSocketClient();
    
    // Use the direct command sending method
    wsClient.sendCommand('rerun_message', {
      message_id: messageId,
      constitution_id: constitutionId,
      sysprompt_id: syspromptId
    }, flowInstanceId || undefined);
    
    setIsSending(true);
    setProcessingStep(0);
  }, [flowInstanceId]);

  // Render the chat interface
  return (
    <div className="chat-container">
      <div className="chat-header-container">
        <ChatHeader 
          isConnected={isConnected}
          isConnecting={isConnecting}
          connectionFailed={connectionFailed}
          reconnectAttempt={reconnectAttempt}
          maxReconnectAttempts={maxReconnectAttempts}
          isSending={isSending}
          onCancelProcessing={handleCancelProcessing}
        />
      </div>
      
      <div className="messages-container">
        {messages.length === 0 && !currentEvaluation && !isSending && (
          <div className="empty-state">
            <p>Start a conversation with the AI assistant</p>
          </div>
        )}
        
        {messages.map(message => (
          <MessageBubble 
            key={message.id} 
            message={message}
            appData={appData}
            onRerun={handleRerun}
          />
        ))}
        
        {streamingThinking ? (
          <SuperegoEvaluationBox 
            evaluation={{
              ...currentEvaluation,
              status: 'thinking',
              thinking: streamingThinking.thinking,
              id: streamingThinking.id
            }} 
          />
        ) : currentEvaluation && (
          <SuperegoEvaluationBox evaluation={currentEvaluation} />
        )}
        
        {streamingMessage && (
          <StreamingMessage content={streamingMessage.content} />
        )}
        
        {isSending && !streamingMessage && !currentEvaluation && (
          <ProcessingIndicator processingStep={processingStep} />
        )}
        
        {systemMessage && !isSending && (
          <div className="system-message">
            {systemMessage}
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <ChatInput 
        onSubmit={handleSendMessage}
        isConnected={isConnected}
        isSending={isSending}
      />
    </div>
  );
};

export default Chat;
