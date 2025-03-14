<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import ToolConfirmationModal from './ToolConfirmationModal.svelte';
  import { confirmTool } from '../../api/toolService';
  import { setError } from '../../stores/uiStateStore';
  
  // Props
  export let instanceId: string;
  export let onToolConfirmed: () => void = () => {};
  export let onToolRejected: () => void = () => {};
  
  // Local state (no stores needed)
  let pendingConfirmation: {
    id: string;
    toolName: string;
    toolInput: any;
  } | null = null;
  
  // This function would be called from the parent component
  // when a tool requires confirmation (e.g. from a streaming event)
  export function requestConfirmation(toolExecutionId: string, toolName: string, toolInput: any) {
    pendingConfirmation = {
      id: toolExecutionId,
      toolName,
      toolInput
    };
  }
  
  // Clear confirmation
  export function clearConfirmation() {
    pendingConfirmation = null;
  }
  
  // Confirm the tool execution
  async function handleConfirm() {
    if (!pendingConfirmation) return;
    
    try {
      await confirmTool(instanceId, pendingConfirmation.id, true);
      onToolConfirmed();
    } catch (error: any) {
      setError(`Failed to confirm tool: ${error.message || 'Unknown error'}`);
    } finally {
      pendingConfirmation = null;
    }
  }
  
  // Reject the tool execution
  async function handleReject() {
    if (!pendingConfirmation) return;
    
    try {
      await confirmTool(instanceId, pendingConfirmation.id, false);
      onToolRejected();
    } catch (error: any) {
      setError(`Failed to reject tool: ${error.message || 'Unknown error'}`);
    } finally {
      pendingConfirmation = null;
    }
  }
</script>

{#if pendingConfirmation}
  <ToolConfirmationModal
    instanceId={instanceId}
    toolExecutionId={pendingConfirmation.id}
    toolName={pendingConfirmation.toolName}
    toolInput={pendingConfirmation.toolInput}
    onConfirm={handleConfirm}
    onReject={handleReject}
  />
{/if}
