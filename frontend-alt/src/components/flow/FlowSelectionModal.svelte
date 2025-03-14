<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { flowDefinitionsPromise, refreshFlowDefinitions } from '../../stores/flowInstancesStore';
  
  export let isOpen = false;
  const dispatch = createEventDispatcher();
  
  let selectedDefinitionId: string | null = null;
  
  function closeModal() {
    isOpen = false;
    dispatch('close');
  }
  
  function createFlow() {
    if (selectedDefinitionId) {
      dispatch('create', selectedDefinitionId);
      closeModal();
    }
  }
  
  function handleBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      closeModal();
    }
  }
  
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      closeModal();
    }
  }
</script>

<svelte:window on:keydown={isOpen ? handleKeydown : null} />

{#if isOpen}
  <div class="modal-backdrop" on:click={handleBackdropClick}>
    <div class="modal-content" role="dialog" aria-labelledby="modal-title">
      <div class="modal-header">
        <h2 id="modal-title">Select Flow Type</h2>
        <button class="close-button" on:click={closeModal} aria-label="Close modal">×</button>
      </div>
      
      <div class="modal-body">
        {#await $flowDefinitionsPromise}
          <div class="loading">Loading flow definitions...</div>
        {:then definitions}
          {#if definitions.length === 0}
            <div class="empty-state">No flow definitions available</div>
          {:else}
            <ul class="definition-list">
              {#each definitions as definition}
                <li>
                  <label class="definition-item">
                    <input 
                      type="radio" 
                      name="flowDefinition"
                      value={definition.id}
                      bind:group={selectedDefinitionId}
                    />
                    <div class="definition-info">
                      <div class="definition-name">{definition.name}</div>
                      <div class="definition-description">{definition.description}</div>
                    </div>
                  </label>
                </li>
              {/each}
            </ul>
          {/if}
        {:catch error}
          <div class="error-state">
            <p>Error loading flow definitions: {error.message}</p>
            <button on:click={refreshFlowDefinitions}>Retry</button>
          </div>
        {/await}
      </div>
      
      <div class="modal-footer">
        <button class="cancel-button" on:click={closeModal}>Cancel</button>
        <button 
          class="create-button" 
          on:click={createFlow} 
          disabled={!selectedDefinitionId}
        >
          Create Flow
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .modal-content {
    background: white;
    border-radius: 4px;
    width: 90%;
    max-width: 500px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
  }
  
  .modal-header {
    padding: 1rem;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .modal-body {
    padding: 1rem;
    overflow-y: auto;
    flex: 1;
  }
  
  .modal-footer {
    padding: 1rem;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
  }
  
  h2 {
    margin: 0;
    font-size: 1.2rem;
  }
  
  .close-button {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    color: #666;
  }
  
  .definition-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .definition-item {
    display: flex;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border: 1px solid #eee;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .definition-item:hover {
    background: #f5f5f5;
  }
  
  .definition-info {
    margin-left: 0.5rem;
  }
  
  .definition-name {
    font-weight: 500;
    margin-bottom: 0.25rem;
  }
  
  .definition-description {
    font-size: 0.9rem;
    color: #666;
  }
  
  .loading, .empty-state, .error-state {
    text-align: center;
    padding: 1rem;
    color: #666;
  }
  
  .cancel-button {
    background: #f5f5f5;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .create-button {
    background: #1890ff;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .create-button:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
</style>
