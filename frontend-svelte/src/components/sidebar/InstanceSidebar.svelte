<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { 
    flowInstances, 
    activeFlowInstance, 
    setActiveFlowInstance,
    createFlowInstance,
    deleteFlowInstance
  } from '../../lib/stores/flowInstances';
  import { flowDefinitionsApi } from '../../lib/api/rest';
  
  const dispatch = createEventDispatcher();
  
  // State for flow definitions (need to select one when creating new instance)
  let flowDefinitions: FlowDefinition[] = [];
  let isLoading = true;
  let error = '';
  
  // State for new instance form
  let isCreatingNew = false;
  let newInstanceName = '';
  let selectedDefinitionId = '';
  
  // Load flow definitions on mount
  onMount(async () => {
    try {
      const response = await flowDefinitionsApi.getAll();
      if (response.success || response.status === 'success') {
        flowDefinitions = response.data;
        if (flowDefinitions.length > 0) {
          selectedDefinitionId = flowDefinitions[0].id;
        }
      } else {
        error = 'Failed to load flow definitions';
      }
    } catch (err) {
      error = 'Error loading flow definitions';
      console.error(err);
    } finally {
      isLoading = false;
    }
  });
  
  // Handle selection of a flow instance
  function selectInstance(instanceId: string) {
    setActiveFlowInstance(instanceId);
  }
  
  // Create a new flow instance
  async function handleCreateInstance() {
    if (!newInstanceName.trim() || !selectedDefinitionId) {
      return;
    }
    
    try {
      const instance = await createFlowInstance({
        name: newInstanceName,
        flow_definition_id: selectedDefinitionId
      });
      
      // Reset form
      newInstanceName = '';
      isCreatingNew = false;
      
      // New instance is automatically selected by the createFlowInstance function
    } catch (err) {
      console.error('Failed to create flow instance', err);
      error = 'Failed to create new flow instance';
    }
  }
  
  // Handle deletion of a flow instance
  async function handleDeleteInstance(e: Event, instanceId: string) {
    e.stopPropagation(); // Prevent selecting the instance when clicking delete
    
    if (confirm('Are you sure you want to delete this flow instance?')) {
      try {
        await deleteFlowInstance(instanceId);
      } catch (err) {
        console.error('Failed to delete flow instance', err);
        error = 'Failed to delete flow instance';
      }
    }
  }
</script>

<div class="sidebar">
  <h2>Flow Instances</h2>
  
  {#if error}
    <div class="error">{error}</div>
  {/if}
  
  <div class="instances">
    {#if $flowInstances.length === 0}
      <div class="empty-state">No flow instances yet</div>
    {:else}
      {#each $flowInstances as instance}
        <div 
          class="instance {$activeFlowInstance?.id === instance.id ? 'active' : ''}"
          on:click={() => selectInstance(instance.id as string)}
          on:keypress={(e) => e.key === 'Enter' && selectInstance(instance.id as string)}
          tabindex="0"
          role="button"
        >
          <div class="instance-name">{instance.name}</div>
          <button 
            class="delete-btn"
            on:click={(e) => handleDeleteInstance(e, instance.id as string)}
            aria-label="Delete flow instance"
          >
            ×
          </button>
        </div>
      {/each}
    {/if}
  </div>
  
  <div class="new-instance-container">
    {#if isCreatingNew}
      <div class="new-instance-form">
        <input 
          type="text" 
          bind:value={newInstanceName} 
          placeholder="Flow instance name" 
          autocomplete="off"
        />
        
        <select bind:value={selectedDefinitionId}>
          {#if isLoading}
            <option value="">Loading...</option>
          {:else}
            {#each flowDefinitions as definition}
              <option value={definition.id}>{definition.name}</option>
            {/each}
          {/if}
        </select>
        
        <div class="form-buttons">
          <button 
            class="create-btn" 
            on:click={handleCreateInstance}
            disabled={!newInstanceName.trim() || !selectedDefinitionId}
          >
            Create
          </button>
          <button class="cancel-btn" on:click={() => isCreatingNew = false}>
            Cancel
          </button>
        </div>
      </div>
    {:else}
      <button class="new-btn" on:click={() => isCreatingNew = true}>
        + New Flow Instance
      </button>
    {/if}
  </div>
</div>

<style>
  .sidebar {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: #f8f9fa;
    border-right: 1px solid #e9ecef;
    width: 250px;
    min-width: 250px;
    overflow-y: auto;
  }
  
  h2 {
    padding: 1rem;
    margin: 0;
    font-size: 1.2rem;
    border-bottom: 1px solid #e9ecef;
  }
  
  .instances {
    flex-grow: 1;
    overflow-y: auto;
    padding: 0.5rem;
  }
  
  .empty-state {
    padding: 1rem;
    color: #6c757d;
    text-align: center;
  }
  
  .error {
    padding: 0.5rem;
    margin: 0.5rem;
    background-color: #f8d7da;
    color: #721c24;
    border-radius: 4px;
  }
  
  .instance {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem;
    border-radius: 4px;
    cursor: pointer;
    margin-bottom: 0.25rem;
    transition: background-color 0.2s;
  }
  
  .instance:hover {
    background-color: #e9ecef;
  }
  
  .instance.active {
    background-color: #e3f2fd;
  }
  
  .instance-name {
    flex-grow: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .delete-btn {
    background: none;
    border: none;
    color: #6c757d;
    font-size: 1.2rem;
    padding: 0 0.3rem;
    cursor: pointer;
    margin-left: 0.5rem;
    opacity: 0.5;
    transition: opacity 0.2s;
  }
  
  .delete-btn:hover {
    opacity: 1;
    color: #dc3545;
  }
  
  .new-instance-container {
    padding: 1rem;
    border-top: 1px solid #e9ecef;
  }
  
  .new-btn {
    width: 100%;
    padding: 0.5rem;
    background-color: #4a90e2;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .new-btn:hover {
    background-color: #3a80d2;
  }
  
  .new-instance-form {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .form-buttons {
    display: flex;
    gap: 0.5rem;
  }
  
  .create-btn {
    flex: 1;
    padding: 0.5rem;
    background-color: #4a90e2;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .create-btn:hover:not(:disabled) {
    background-color: #3a80d2;
  }
  
  .create-btn:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
  
  .cancel-btn {
    flex: 1;
    padding: 0.5rem;
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .cancel-btn:hover {
    background-color: #5a6268;
  }
  
  input, select {
    padding: 0.5rem;
    border: 1px solid #ced4da;
    border-radius: 4px;
  }
</style>
