import { useState, useEffect } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Chat from './components/Chat.tsx'
import TestMessages from './components/TestMessages.tsx'
import InstanceSidebar from './components/InstanceSidebar'
import ParallelFlowsView from './components/ParallelFlowsView'
import './App.css'
import './components/TestMessages.css'
import { getWebSocketClient } from './api/websocketClient'
import { WebSocketMessageType } from './types'

// Import the interfaces from the types folder for better organization
import { Constitution, Sysprompt, FlowInstance, FlowConfig } from './types'

// Define AppData interface for passing data to child components
export interface AppData {
  constitutions: Constitution[];
  sysprompts: Sysprompt[];
  constitutionsLoading: boolean;
  syspromptsLoading: boolean;
  constitutionsError: string | null;
  syspromptsError: string | null;
}

// Define UI modes for the application
export enum AppMode {
  CHAT = 'chat',
  PARALLEL_FLOWS = 'parallel_flows'
}

// Default data to use ONLY if we can't load from backend
// This should match what's in the backend files
const DEFAULT_CONSTITUTIONS = [
  {
    id: "default",
    name: "Default - Just the Rubric",
    content: "Default constitution content - would be filled with actual content"
  },
  {
    id: "none",
    name: "No Constitution",
    content: ""
  }
];

const DEFAULT_SYSPROMPTS = [
  {
    id: "assistant_default",
    name: "Assistant Default",
    content: "You are a helpful AI assistant with a Superego mechanism."
  }
];

function App() {
  const [apiKeySet, setApiKeySet] = useState<boolean>(false)
  const [showDebug, setShowDebug] = useState<boolean>(false)
  const [showSidebar, setShowSidebar] = useState<boolean>(true)
  const [appMode, setAppMode] = useState<AppMode>(AppMode.CHAT)
  const [selectedInstanceId, setSelectedInstanceId] = useState<string | null>(null)
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [userInput, setUserInput] = useState<string>('')
  
  // Data states with initial empty values
  const [constitutions, setConstitutions] = useState<Constitution[]>([])
  const [sysprompts, setSysprompts] = useState<Sysprompt[]>([])
  const [flowInstances, setFlowInstances] = useState<FlowInstance[]>([])
  const [flowConfigs, setFlowConfigs] = useState<FlowConfig[]>([])
  const [constitutionsLoading, setConstitutionsLoading] = useState(true)
  const [syspromptsLoading, setSyspromptsLoading] = useState(true)
  const [instancesLoading, setInstancesLoading] = useState(true)
  const [configsLoading, setConfigsLoading] = useState(true)
  const [constitutionsError, setConstitutionsError] = useState<string | null>(null)
  const [syspromptsError, setSyspromptsError] = useState<string | null>(null)

  // Check if API key is set in backend
  useEffect(() => {
    const checkApiKey = async () => {
      try {
        const response = await fetch('/api')
        const data = await response.json()
        // If we get a successful response, assume the backend is configured correctly
        setApiKeySet(true)
      } catch (error) {
        console.error('Error connecting to backend:', error)
        setApiKeySet(false)
      }
    }
    
    checkApiKey()
  }, [])
  
  // Fetch constitutions, system prompts, instances, and configs from backend
  useEffect(() => {
    const wsClient = getWebSocketClient()
    
    // Ensure connection is established
    if (!wsClient.isConnected()) {
      wsClient.connect()
    }
    
    // Handle data responses
    const handleDataResponse = (
      type: WebSocketMessageType, 
      content: any[],
      setData: React.Dispatch<React.SetStateAction<any[]>>,
      setLoading: React.Dispatch<React.SetStateAction<boolean>>,
      setError: React.Dispatch<React.SetStateAction<string | null>>,
      defaultData: any[],
      errorMessage: string
    ) => {
      if (content && Array.isArray(content)) {
        if (content.length > 0) {
          setData(content)
          setLoading(false)
          setError(null)
        } else {
          // If we got an empty array, use defaults but show an error
          setData(defaultData)
          setError(errorMessage)
          setLoading(false)
        }
      }
    }
    
    // Setup message handler for responses
    const onMessage = (message: any) => {
      console.log("App received WebSocket message:", message.type);
      
      if (message.type === WebSocketMessageType.CONSTITUTIONS_RESPONSE) {
        handleDataResponse(
          message.type,
          message.content,
          setConstitutions,
          setConstitutionsLoading,
          setConstitutionsError,
          DEFAULT_CONSTITUTIONS,
          "Received empty constitutions list from server"
        )
      }
      else if (message.type === WebSocketMessageType.SYSPROMPTS_RESPONSE) {
        handleDataResponse(
          message.type,
          message.content,
          setSysprompts,
          setSyspromptsLoading,
          setSyspromptsError,
          DEFAULT_SYSPROMPTS,
          "Received empty system prompts list from server"
        )
      }
      else if (message.type === 'flow_instances_response' || 
              message.type === WebSocketMessageType.FLOW_INSTANCES_RESPONSE) {
        console.log("Received flow instances:", message.content);
        // Store instances when we receive them
        if (message.content && Array.isArray(message.content)) {
          setFlowInstances(message.content);
          setInstancesLoading(false);
          
          // If there's a selected instance ID, ensure the conversation ID is updated
          if (selectedInstanceId) {
            const instance = message.content.find((inst: FlowInstance) => inst.id === selectedInstanceId);
            if (instance && instance.conversation_id) {
              setCurrentConversationId(instance.conversation_id);
              // Update the WebSocketClient with this conversation ID
              const wsClient = getWebSocketClient();
              wsClient.setConversationId(instance.conversation_id);
              console.log(`Updated conversation ID to ${instance.conversation_id} from instance ${selectedInstanceId}`);
            }
          }
        }
      }
      else if (message.type === 'flow_configs_response' || 
              message.type === WebSocketMessageType.FLOW_CONFIGS_RESPONSE ||
              // For backward compatibility:
              (message.type === 'flows_response' && message.content && 
               message.content.length > 0 && !('conversation_id' in message.content[0]))) {
        console.log("Received flow configs:", message.content);
        if (message.content && Array.isArray(message.content)) {
          setFlowConfigs(message.content);
          setConfigsLoading(false);
        }
      }
      else if (message.type === 'flows_response' && message.content && 
               message.content.length > 0 && 'conversation_id' in message.content[0]) {
        // Legacy support for instances via flows_response
        console.log("Received flow instances via legacy flow_response:", message.content);
        setFlowInstances(message.content);
        setInstancesLoading(false);
      }
      else if (message.type === 'system_message' && 
               message.content && message.content.message && 
               message.content.message.includes('Flow instance created')) {
        console.log("Flow instance created, refreshing instances");
        // Refresh instances after creation
        const wsClient = getWebSocketClient();
        wsClient.sendCommand('get_flow_instances');
      }
    }
    
    wsClient.updateCallbacks({ onMessage })
    
    // Request data if connected
    if (wsClient.isConnected()) {
      // Request constitutions
      wsClient.sendMessage(JSON.stringify({
        type: 'get_constitutions'
      }))
      
      // Request system prompts
      wsClient.sendMessage(JSON.stringify({
        type: 'get_sysprompts'
      }))
      
      // Request configs and instances
      wsClient.sendCommand('get_flow_configs');
      wsClient.sendCommand('get_flow_instances');
    }
    
    // Set timeouts for requests
    const TIMEOUT_MS = 5000
    
    const constitutionsTimeout = setTimeout(() => {
      if (constitutionsLoading) {
        setConstitutions(DEFAULT_CONSTITUTIONS)
        setConstitutionsError("Timed out waiting for constitutions from server")
        setConstitutionsLoading(false)
      }
    }, TIMEOUT_MS)
    
    const syspromptsTimeout = setTimeout(() => {
      if (syspromptsLoading) {
        setSysprompts(DEFAULT_SYSPROMPTS)
        setSyspromptsError("Timed out waiting for system prompts from server")
        setSyspromptsLoading(false)
      }
    }, TIMEOUT_MS)
    
    return () => {
      clearTimeout(constitutionsTimeout)
      clearTimeout(syspromptsTimeout)
    }
  }, [constitutionsLoading, syspromptsLoading, selectedInstanceId])
  
  // Handle instance selection
  const handleSelectInstance = (instanceId: string) => {
    setSelectedInstanceId(instanceId);
    
    // Find the selected instance in our state
    const selectedInstance = flowInstances.find(instance => instance.id === instanceId);
    
    if (selectedInstance) {
      // Use the actual conversation_id from the instance, not the instance ID
      const conversationId = selectedInstance.conversation_id;
      setCurrentConversationId(conversationId);
      
      // Update the WebSocketClient's conversation ID for future messages
      const wsClient = getWebSocketClient();
      wsClient.setConversationId(conversationId);
      
      console.log(`Selected instance ${instanceId} with conversation ID ${conversationId}`);
    } else {
      console.error(`Could not find instance with ID ${instanceId}`);
    }
  };
  
  // Function to create default instance if needed
  const createDefaultInstanceIfNeeded = () => {
    // Only proceed if we have configs but no instances
    if (flowConfigs.length === 0 || flowInstances.length > 0) {
      return;
    }
    
    console.log("Creating default instance since we have configs but no instances");
    
    // Find a config with superego enabled (preferably) or just take the first one
    const standardConfig = flowConfigs.find(c => c.superego_enabled) || flowConfigs[0];
    
    // Create a default instance
    const wsClient = getWebSocketClient();
    wsClient.sendCommand('create_flow_instance', {
      name: "Default Session",
      flow_config_id: standardConfig.id,
      description: "Automatically created default session"
    });
  };
  
  // Create default instance when configs and instances are loaded
  useEffect(() => {
    if (!configsLoading && !instancesLoading) {
      createDefaultInstanceIfNeeded();
    }
  }, [configsLoading, instancesLoading, flowConfigs, flowInstances]);
  
  // Handle creating a new instance
  const handleCreateInstance = (newInstanceData: {name: string, flow_config_id: string, description?: string}) => {
    // Create the instance via WebSocket
    const wsClient = getWebSocketClient();
    wsClient.sendCommand('create_flow_instance', newInstanceData);
    
    // Note: we'll select the instance when we receive the confirmation in the message handler
  };
  
  // Handle user input changes (for the parallel flows view)
  const handleUserInputChange = (input: string) => {
    setUserInput(input);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <h1>Superego LangGraph</h1>
          </div>
          <nav className="main-nav">
            <button 
              className={`mode-toggle ${appMode === AppMode.CHAT ? 'active' : ''}`}
              onClick={() => setAppMode(AppMode.CHAT)}
            >
              Chat
            </button>
            <button 
              className={`mode-toggle ${appMode === AppMode.PARALLEL_FLOWS ? 'active' : ''}`}
              onClick={() => setAppMode(AppMode.PARALLEL_FLOWS)}
            >
              Compare Flows
            </button>
            <button 
              className="sidebar-toggle"
              onClick={() => setShowSidebar(!showSidebar)}
            >
              {showSidebar ? 'Hide Sidebar' : 'Show Sidebar'}
            </button>
            <button 
              className="debug-toggle"
              onClick={() => setShowDebug(!showDebug)}
            >
              {showDebug ? 'Hide Debug' : 'Show Debug'}
            </button>
          </nav>
        </div>
      </header>
      
      {showDebug && <TestMessages />}
      
      <div className={`app-content ${showSidebar ? 'with-sidebar' : ''}`}>
        {showSidebar && (
          <InstanceSidebar 
            selectedInstanceId={selectedInstanceId}
            onSelectInstance={handleSelectInstance}
            onCreateInstance={handleCreateInstance}
            flowConfigs={flowConfigs}
            flowInstances={flowInstances}
            loading={configsLoading || instancesLoading}
          />
        )}
        
        <main className="app-main">
          {!apiKeySet && (
            <div className="api-key-warning">
              <h2>⚠️ API Key Required</h2>
              <p>Please set your OpenRouter API key in the backend .env file to use this application.</p>
              <code>OPENROUTER_API_KEY=your_key_here</code>
            </div>
          )}
          
          {appMode === AppMode.CHAT && (
            <Chat 
              appData={{
                constitutions,
                sysprompts,
                constitutionsLoading,
                syspromptsLoading,
                constitutionsError,
                syspromptsError
              }}
              conversationId={currentConversationId}
              onUserInputChange={handleUserInputChange}
            />
          )}
          
          {appMode === AppMode.PARALLEL_FLOWS && (
            <ParallelFlowsView 
              userInput={userInput}
              conversationId={currentConversationId}
              appData={{
                constitutions,
                sysprompts,
                constitutionsLoading,
                syspromptsLoading,
                constitutionsError,
                syspromptsError
              }}
            />
          )}
        </main>
      </div>
    </div>
  )
}

export default App
