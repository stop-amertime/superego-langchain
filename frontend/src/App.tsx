import { useState, useEffect } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Chat from './components/Chat.tsx'
import FlowChat from './components/FlowChat.tsx'
import TestMessages from './components/TestMessages.tsx'
import InstanceSidebar from './components/InstanceSidebar'
import ParallelFlowsView from './components/ParallelFlowsView'
import ConstitutionManager from './components/ConstitutionManager'
import './App.css'
import './components/TestMessages.css'
import { getWebSocketClient } from './api/websocketClient'
import { WebSocketMessageType } from './types'
import { 
  useCreateFlowInstance, 
  useFlowInstances, 
  useFlowConfigs, 
  queryClient 
} from './api/queryHooks'

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
  const [constitutionsLoading, setConstitutionsLoading] = useState(true)
  const [syspromptsLoading, setSyspromptsLoading] = useState(true)
  const [constitutionsError, setConstitutionsError] = useState<string | null>(null)
  const [syspromptsError, setSyspromptsError] = useState<string | null>(null)
  
  // Use React Query hooks for flow instances and configs
  const { 
    data: flowInstances = [], 
    isLoading: instancesLoading 
  } = useFlowInstances();
  
  const { 
    data: flowConfigs = [], 
    isLoading: configsLoading 
  } = useFlowConfigs();

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
  
  // Update flow instance ID when selected instance changes
  useEffect(() => {
    if (selectedInstanceId && flowInstances.length > 0) {
      // Find the selected instance in our data
      const selectedInstance = flowInstances.find(instance => instance.id === selectedInstanceId);
      
      if (selectedInstance) {
        // Use the actual message_store_id from the instance, not the instance ID
        const flowInstanceId = selectedInstance.message_store_id;
        setCurrentFlowInstanceId(flowInstanceId);
        
        // No need to update WebSocketClient's flow instance ID anymore
        // We'll pass it directly with each message
        
        console.log(`Selected instance ${selectedInstanceId} with flow instance ID ${flowInstanceId}`);
      }
    }
  }, [selectedInstanceId, flowInstances]);
  
  // Handle instance selection
  const handleSelectInstance = (instanceId: string) => {
    setSelectedInstanceId(instanceId);
    
    // Find the selected instance in our state
    const selectedInstance = flowInstances.find(instance => instance.id === instanceId);
    
    if (selectedInstance) {
      // Use the actual message_store_id from the instance, not the instance ID
      const flowInstanceId = selectedInstance.message_store_id;
      setCurrentFlowInstanceId(flowInstanceId);
      
      // No need to update WebSocketClient's flow instance ID anymore
      // We'll pass it directly with each message
      
      console.log(`Selected instance ${instanceId} with flow instance ID ${flowInstanceId}`);
    } else {
      console.error(`Could not find instance with ID ${instanceId}`);
    }
  };
  
  // Create instance mutation
  const createInstanceMutation = useCreateFlowInstance();
  
  // Function to select the first instance or create a new one if none exist
  const selectFirstInstanceOrCreateNew = () => {
    // If we already have a selected instance, do nothing
    if (selectedInstanceId) {
      return;
    }
    
    // If we have instances, select the first one
    if (flowInstances.length > 0) {
      const firstInstance = flowInstances[0];
      console.log(`Selecting first instance: ${firstInstance.id}`);
      setSelectedInstanceId(firstInstance.id);
      
      // Set the flow instance ID for WebSocket communication
      if (firstInstance.message_store_id) {
        setCurrentFlowInstanceId(firstInstance.message_store_id);
        // No need to update WebSocketClient's flow instance ID anymore
        // We'll pass it directly with each message
      }
      return;
    }
    
    // Only create a new instance if we have configs but no instances
    if (flowConfigs.length === 0) {
      return;
    }
    
    console.log("Creating new instance since no instances exist");
    
    // Find a config with superego enabled (preferably) or just take the first one
    const standardConfig = flowConfigs.find(c => c.superego_enabled) || flowConfigs[0];
    
    // Create a new instance using the REST API
    const newInstanceData = {
      name: "New Session",
      flow_config_id: standardConfig.id,
      description: "Automatically created session"
    };
    
    createInstanceMutation.mutate(newInstanceData as any, {
      onSuccess: (data) => {
        // Invalidate the flow instances query to refresh the list
        queryClient.invalidateQueries({ queryKey: ['flowInstances'] });
        
        // Select the newly created instance
        if (data && data.id) {
          setSelectedInstanceId(data.id);
          
          // Set the flow instance ID for WebSocket communication
          if (data.message_store_id) {
            setCurrentFlowInstanceId(data.message_store_id);
            // No need to update WebSocketClient's flow instance ID anymore
            // We'll pass it directly with each message
          }
        }
      }
    });
  };
  
  // Select first instance or create new one when configs and instances are loaded
  useEffect(() => {
    if (!configsLoading && !instancesLoading) {
      selectFirstInstanceOrCreateNew();
    }
  }, [configsLoading, instancesLoading, flowConfigs, flowInstances, selectedInstanceId]);
  
  // Handle creating a new instance
  const handleCreateInstance = (newInstanceData: {name: string, flow_config_id: string, description?: string}) => {
    // The instance is already created by the InstanceSidebar component's mutation
    // We just need to handle the selection of the new instance
    
    // Invalidate the flow instances query to refresh the list
    queryClient.invalidateQueries({ queryKey: ['flowInstances'] });
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
            <FlowChat 
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
