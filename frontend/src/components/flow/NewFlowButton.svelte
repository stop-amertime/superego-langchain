<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  function openFlowSelection() {
    dispatch('openModal');
  }
</script>

<button 
  class="new-flow-button" 
  on:click={openFlowSelection}
  aria-label="Create new flow"
>
  <span class="icon">+</span>
  <span>New Flow</span>
</button>

<style>
  .new-flow-button {
    width: 100%;
    padding: 0.75rem;
    margin-bottom: 1rem;
    background: #1890ff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .new-flow-button:hover {
    background: #40a9ff;
  }
  
  .icon {
    font-size: 1.2rem;
    margin-right: 0.5rem;
  }
</style>
