<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { confirmTool } from '../../api/toolService';
  import { setError } from '../../stores/uiStateStore';
  
  // Props
  export let instanceId: string;
  export let toolExecutionId: string;
  export let toolName: string;
  export let toolInput: any;
  export let onConfirm: () => void;
  export let onReject: () => void;
  
  // State
  let isLoading = false;
  let timeoutId: number | undefined;
  const TIMEOUT_DURATION = 30000; // 30 seconds timeout
  
  // Handle confirmation
  async function handleConfirm() {
    isLoading = true;
    try {
      await confirmTool(instanceId, toolExecutionId, true);
      onConfirm();
    } catch (error: any) {
      setError(`Failed to confirm tool: ${error.message || 'Unknown error'}`);
    } finally {
      isLoading = false;
    }
  }
  
  // Handle rejection
  async function handleReject() {
    isLoading = true;
    try {
      await confirmTool(instanceId, toolExecutionId, false);
      onReject();
    } catch (error: any) {
      setError(`Failed to reject tool: ${error.message || 'Unknown error'}`);
    } finally {
      isLoading = false;
    }
  }
  
  // Set up timeout
  onMount(() => {
    timeoutId = window.setTimeout(() => {
      handleReject();
      setError('Tool confirmation timed out');
    }, TIMEOUT_DURATION);
  });
  
  // Clean up timeout
  onDestroy(() => {
    if (timeoutId) {
      window.clearTimeout(timeoutId);
    }
  });
  
  // Format tool input for display
  function formatInput(input: any): string {
    try {
      return typeof input === 'object'
        ? JSON.stringify(input, null, 2)
        : String(input);
    } catch (e) {
      return String(input);
    }
  }
</script>

<div class="tool-confirmation">
  <div class="header">
    <h3>Tool Confirmation Required</h3>
  </div>
  
  <div class="body">
    <div class="tool-info">
      <div class="tool-name">
        <span class="label">Tool:</span>
        <span class="value">{toolName}</span>
      </div>
      
      <div class="tool-input">
        <span class="label">Input:</span>
        <pre class="value">{formatInput(toolInput)}</pre>
      </div>
    </div>
    
    <p class="confirmation-message">
      Do you want to allow this tool to execute?
    </p>
  </div>
  
  <div class="actions">
    <button 
      class="reject-button" 
      on:click={handleReject} 
      disabled={isLoading}
    >
      Reject
    </button>
    
    <button 
      class="confirm-button" 
      on:click={handleConfirm} 
      disabled={isLoading}
    >
      {isLoading ? 'Processing...' : 'Confirm'}
    </button>
  </div>
</div>

<style>
  .tool-confirmation {
    background-color: #f8f9fa;
    border-radius: 8px;
    border-left: 4px solid #ffc107; /* Warning yellow */
    margin: 12px 0;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }
  
  .header {
    background-color: #fff8e1;
    padding: 12px 16px;
    border-bottom: 1px solid #ffe082;
  }
  
  .header h3 {
    margin: 0;
    font-size: 16px;
    color: #856404;
  }
  
  .body {
    padding: 16px;
  }
  
  .tool-info {
    margin-bottom: 16px;
  }
  
  .tool-name, .tool-input {
    margin-bottom: 8px;
  }
  
  .label {
    font-weight: bold;
    margin-right: 8px;
  }
  
  pre.value {
    background-color: #fff;
    padding: 8px;
    border-radius: 4px;
    border: 1px solid #eee;
    overflow-x: auto;
    margin: 4px 0;
    font-size: 13px;
  }
  
  .confirmation-message {
    font-size: 14px;
    margin-top: 12px;
    margin-bottom: 0;
  }
  
  .actions {
    display: flex;
    justify-content: flex-end;
    padding: 12px 16px;
    background-color: #fff;
    border-top: 1px solid #eee;
    gap: 8px;
  }
  
  button {
    padding: 6px 12px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
    transition: background-color 0.2s;
  }
  
  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .confirm-button {
    background-color: #4CAF50;
    color: white;
  }
  
  .confirm-button:hover:not(:disabled) {
    background-color: #3e8e41;
  }
  
  .reject-button {
    background-color: #f44336;
    color: white;
  }
  
  .reject-button:hover:not(:disabled) {
    background-color: #d32f2f;
  }
</style>
