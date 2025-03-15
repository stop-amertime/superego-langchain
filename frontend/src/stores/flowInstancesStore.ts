import { writable } from 'svelte/store';
import { 
  getFlowInstances, 
  getFlowDefinitions, 
  getFlowDefinition, 
  createNewFlowInstance
} from '../api/flowService';
import { selectFlowInstance } from './currentFlowStore';
import { setLoading, setError } from './uiStateStore';

// Simple promise-based stores - components can use with #await
export const flowInstancesPromise = writable<Promise<FlowInstance[]>>(getFlowInstances());
export const flowDefinitionsPromise = writable<Promise<FlowDefinition[]>>(getFlowDefinitions());

// Refresh actions
export const refreshFlowInstances = () => flowInstancesPromise.set(getFlowInstances());
export const refreshFlowDefinitions = () => flowDefinitionsPromise.set(getFlowDefinitions());

// Create new instance - using backend API
export const createFlowInstance = async (flowDefinitionId: string) => {
  try {
    setLoading(true);
    
    // Create instance on backend
    const newInstance = await createNewFlowInstance(flowDefinitionId);
    
    // Update local state and select the instance
    refreshFlowInstances();
    
    // Pass both the instance ID and flow ID
    // The backend API returns both in the response
    selectFlowInstance(newInstance.id, newInstance.flow_id);
    
    setLoading(false);
    return newInstance;
  } catch (error) {
    console.error('Failed to create flow instance:', error);
    setError(`Failed to create flow instance: ${error instanceof Error ? error.message : String(error)}`);
    setLoading(false);
    throw error;
  }
};
