import { writable } from 'svelte/store';
import { getFlowInstances, getFlowDefinitions, getFlowDefinition } from '../api/flowService';
import { selectFlowInstance } from './currentFlowStore';

// Simple promise-based stores - components can use with #await
export const flowInstancesPromise = writable<Promise<FlowInstance[]>>(getFlowInstances());
export const flowDefinitionsPromise = writable<Promise<FlowDefinition[]>>(getFlowDefinitions());

// Refresh actions
export const refreshFlowInstances = () => flowInstancesPromise.set(getFlowInstances());
export const refreshFlowDefinitions = () => flowDefinitionsPromise.set(getFlowDefinitions());

// Create new instance - minimal implementation
export const createFlowInstance = async (flowDefinitionId: string) => {
  const definition = await getFlowDefinition(flowDefinitionId);
  const newInstance: FlowInstance = {
    id: `flow-${Date.now()}`,
    flow_definition_id: flowDefinitionId,
    flow_name: definition.name,
    status: 'active',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
  
  // Update and select
  refreshFlowInstances();
  selectFlowInstance(newInstance.id);
  return newInstance;
};
