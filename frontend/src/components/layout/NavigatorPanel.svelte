<script lang="ts">
  import FlowInstanceList from '../flow/FlowInstanceList.svelte';
  import NewFlowButton from '../flow/NewFlowButton.svelte';
  import FlowSelectionModal from '../flow/FlowSelectionModal.svelte';
  import { createFlowInstance } from '../../stores/flowInstancesStore';
  import { selectedInstanceId } from '../../stores/currentFlowStore';
  
  let isModalOpen = false;
  let isCreating = false;
  let errorMessage = '';
  
  function handleInstanceSelect(event: CustomEvent<string>) {
    $selectedInstanceId = event.detail;
  }
  
  function openModal() {
    isModalOpen = true;
  }
  
  async function handleCreate(event: CustomEvent<string>) {
    const flowDefinitionId = event.detail;
    isCreating = true;
    errorMessage = '';
    
    try {
      await createFlowInstance(flowDefinitionId);
    } catch (error) {
      errorMessage = error instanceof Error ? error.message : 'Failed to create flow';
      setTimeout(() => { errorMessage = ''; }, 5000);
    } finally {
      isCreating = false;
    }
  }
</script>

<div class="navigator-panel">
  <NewFlowButton on:openModal={openModal} />
  
  {#if isCreating}
    <div class="creating-message">Creating new flow...</div>
  {/if}
  
  {#if errorMessage}
    <div class="error-message">{errorMessage}</div>
  {/if}
  
  <FlowInstanceList on:select={handleInstanceSelect} />
  <FlowSelectionModal 
    bind:isOpen={isModalOpen} 
    on:create={handleCreate} 
  />
</div>

<style>
  .navigator-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #fafafa;
    border-right: 1px solid #eee;
  }
  
  .creating-message {
    padding: 0.5rem 1rem;
    background: #e6f7ff;
    color: #1890ff;
    text-align: center;
    margin-bottom: 1rem;
  }
  
  .error-message {
    padding: 0.5rem 1rem;
    background: #fff1f0;
    color: #f5222d;
    text-align: center;
    margin-bottom: 1rem;
  }
</style>
