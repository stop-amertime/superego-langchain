import { useState, useEffect } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Chat from './components/Chat.tsx'
import TestMessages from './components/TestMessages.tsx'
import InstanceSidebar from './components/InstanceSidebar'
import ParallelFlowsView from './components/ParallelFlowsView'
import ConstitutionManager from './components/ConstitutionManager'
import './App.css'
import './components/TestMessages.css'
import { getWebSocketClient } from './api/websocketClient'
import { WebSocketMessageType } from './types'
import { useCreateFlowInstance, queryClient } from './api/queryHooks'

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
  PARALLEL_FLOWS = 'parallel_flows',
  CONSTITUTIONS = 'constitutions'
}
function App() {
  const [apiKeySet, setApiKeySet] = useState<boolean>(false)
  const [showSidebar, setShowSidebar] = useState<boolean>(true)
  const [appMode, setAppMode] = useState<AppMode>(AppMode.CHAT)
  const [selectedInstanceId, setSelectedInstanceId] = useState<string | null>(null)
  const [currentFlowInstanceId, setCurrentFlowInstanceId] = useState<string | null>(null)
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
  
  // Fetch flow instances and configs from backend
  useEffect(() => {
    const wsClient = getWebSocketClient()
    
    // Ensure connection is established
    if (!wsClient.isConnected()) {
      wsClient.connect()
    }
    
    // Setup message handler for responses
    const onMessage = (message: any) => {
      console.log("App received WebSocket message:", message.type);
      
      if (message.type === 'flow_instances_response' || 
          message.type === WebSocketMessageType.FLOW_INSTANCES_RESPONSE) {
        console.log("Received flow instances:", message.content);
        // Store instances when we receive them
        if (message.content && Array.isArray(message.content)) {
          setFlowInstances(message.content);
          setInstancesLoading(false);
          
          // If there's a selected instance ID, ensure the flow instance ID is updated
          if (selectedInstanceId) {
            const instance = message.content.find((inst: FlowInstance) => inst.id === selectedInstanceId);
            if (instance && instance.conversation_id) {
              setCurrentFlowInstanceId(instance.conversation_id);
              // Update the WebSocketClient with this flow instance ID
              const wsClient = getWebSocketClient();
              wsClient.setFlowInstanceId(instance.conversation_id);
              console.log(`Updated flow instance ID to ${instance.conversation_id} from instance ${selectedInstanceId}`);
            }
          }
        }
      }
      else if (message.type === 'flow_configs_response' || 
              message.type === WebSocketMessageType.FLOW_CONFIGS_RESPONSE ||
              // For backward compatibility:
              (message.type === 'flows_response' && message.content && 
               message.content.length > 0 && !('flow_instance_id' in message.content[0]))) {
        console.log("Received flow configs:", message.content);
        if (message.content && Array.isArray(message.content)) {
          setFlowConfigs(message.content);
          setConfigsLoading(false);
        }
      }
      else if (message.type === 'flows_response' && message.content && 
               message.content.length > 0 && 'flow_instance_id' in message.content[0]) {
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
      // Request configs and instances
      wsClient.sendCommand('get_flow_configs');
      wsClient.sendCommand('get_flow_instances');
    }
    
    return () => {
      // Clean up by removing our specific message handler
      wsClient.updateCallbacks({ onMessage: undefined });
    }
  }, [selectedInstanceId])
  
  // Handle instance selection
  const handleSelectInstance = (instanceId: string) => {
    setSelectedInstanceId(instanceId);
    
    // Find the selected instance in our state
    const selectedInstance = flowInstances.find(instance => instance.id === instanceId);
    
    if (selectedInstance) {
      // Use the actual conversation_id from the instance, not the instance ID
      const flowInstanceId = selectedInstance.conversation_id;
      setCurrentFlowInstanceId(flowInstanceId);
      
      // Update the WebSocketClient's flow instance ID for future messages
      const wsClient = getWebSocketClient();
      wsClient.setFlowInstanceId(flowInstanceId);
      
      console.log(`Selected instance ${instanceId} with flow instance ID ${flowInstanceId}`);
    } else {
      console.error(`Could not find instance with ID ${instanceId}`);
    }
  };
  
  // Create instance mutation
  const createInstanceMutation = useCreateFlowInstance();
  
  // Function to create default instance if needed
  const createDefaultInstanceIfNeeded = () => {
    // Only proceed if we have configs but no instances
    if (flowConfigs.length === 0 || flowInstances.length > 0) {
      return;
    }
    
    console.log("Creating default instance since we have configs but no instances");
    
    // Find a config with superego enabled (preferably) or just take the first one
    const standardConfig = flowConfigs.find(c => c.superego_enabled) || flowConfigs[0];
    
    // Create a default instance using the REST API
    const newInstanceData = {
      name: "Default Session",
      flow_config_id: standardConfig.id,
      description: "Automatically created default session"
    };
    
    createInstanceMutation.mutate(newInstanceData as any, {
      onSuccess: (data) => {
        // Invalidate the flow instances query to refresh the list
        queryClient.invalidateQueries({ queryKey: ['flowInstances'] });
        
        // Select the newly created instance
        if (data && data.id) {
          setSelectedInstanceId(data.id);
          
          // Set the flow instance ID for WebSocket communication
          if (data.conversation_id) {
            setCurrentFlowInstanceId(data.conversation_id);
            const wsClient = getWebSocketClient();
            wsClient.setFlowInstanceId(data.conversation_id);
          }
        }
      }
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
    // Create the instance via REST API
    createInstanceMutation.mutate(newInstanceData as any, {
      onSuccess: (data) => {
        // Invalidate the flow instances query to refresh the list
        queryClient.invalidateQueries({ queryKey: ['flowInstances'] });
        
        // Select the newly created instance
        if (data && data.id) {
          setSelectedInstanceId(data.id);
          
          // Set the flow instance ID for WebSocket communication
          if (data.conversation_id) {
            setCurrentFlowInstanceId(data.conversation_id);
            const wsClient = getWebSocketClient();
            wsClient.setFlowInstanceId(data.conversation_id);
          }
        }
      }
    });
  };
  
  // Handle user input changes (for the parallel flows view)
  const handleUserInputChange = (input: string) => {
    setUserInput(input);
  };

  // Handle sidebar toggle
  const handleToggleSidebar = () => {
    setShowSidebar(!showSidebar);
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
              className={`mode-toggle ${appMode === AppMode.CONSTITUTIONS ? 'active' : ''}`}
              onClick={() => setAppMode(AppMode.CONSTITUTIONS)}
            >
              Constitutions
            </button>
          </nav>
        </div>
      </header>
      
      <div className={`app-content ${showSidebar ? 'with-sidebar' : ''}`}>
        {showSidebar && (
          <InstanceSidebar 
            selectedInstanceId={selectedInstanceId}
            onSelectInstance={handleSelectInstance}
            onCreateInstance={handleCreateInstance}
            onToggleSidebar={handleToggleSidebar}
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
              flowInstanceId={currentFlowInstanceId}
              onUserInputChange={handleUserInputChange}
            />
          )}
          
          {appMode === AppMode.PARALLEL_FLOWS && (
            <ParallelFlowsView 
              userInput={userInput}
              flowInstanceId={currentFlowInstanceId}
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
          
          {appMode === AppMode.CONSTITUTIONS && (
            <ConstitutionManager />
          )}
        </main>
      </div>
    </div>
  )
}

export default App
