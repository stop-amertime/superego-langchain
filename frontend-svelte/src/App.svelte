<script lang="ts">
  import { onMount } from 'svelte';
  import FlowChat from './components/flow/FlowChat.svelte';
  import InstanceSidebar from './components/sidebar/InstanceSidebar.svelte';
  import ConstitutionPanel from './components/constitution/ConstitutionPanel.svelte';
  import { wsStatus } from './lib/api/websocket';
  import { fetchFlowInstances, activeFlowInstance } from './lib/stores/flowInstances';
  import { fetchConstitutions } from './lib/stores/constitutions';
  
  // UI State
  let isConstitutionPanelOpen = false;
  
  // Toggle constitution panel
  function toggleConstitutionPanel() {
    isConstitutionPanelOpen = !isConstitutionPanelOpen;
  }
  
  // Initialize data on mount
  onMount(() => {
    // Fetch initial data
    fetchFlowInstances();
    fetchConstitutions();
  });
</script>

<main class="app-grid">
  <div class="status-bar">
    <div class="connection-status">
      <div class="status-indicator" class:connected={$wsStatus === 'connected'} class:connecting={$wsStatus === 'connecting'}></div>
      <span>
        {#if $wsStatus === 'connected'}
          Connected
        {:else if $wsStatus === 'connecting'}
          Connecting...
        {:else}
          Disconnected
        {/if}
      </span>
    </div>
  </div>
  
  <div class="sidebar-area">
    <InstanceSidebar />
  </div>
  
  <div class="header-area">
    <h1>{$activeFlowInstance?.name || 'SuperEgo LangGraph'}</h1>
    <button on:click={toggleConstitutionPanel} class="control-panel-btn">
      Control Panel
    </button>
  </div>
  
  <div class="content-area">
    {#if $activeFlowInstance}
      <FlowChat />
    {:else}
      <div class="empty-state">
        <p>Select a conversation from the sidebar or create a new one to start.</p>
      </div>
    {/if}
  </div>
  
  {#if isConstitutionPanelOpen}
    <div class="modal-overlay" on:click={toggleConstitutionPanel}>
      <div class="modal-content" on:click|stopPropagation>
        <div class="modal-header">
          <h2>Control Panel</h2>
          <button class="close-btn" on:click={toggleConstitutionPanel}>×</button>
        </div>
        <div class="modal-body">
          <div class="tabs">
            <button class="tab-btn active">Constitutions</button>
            <!-- Additional tabs can be added here -->
          </div>
          <div class="tab-content">
            <ConstitutionPanel isOpen={true} />
          </div>
        </div>
      </div>
    </div>
  {/if}
</main>

<style>
  /* Global layout */
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
  }
  
  :global(#app) {
    height: 100vh;
    width: 100vw;
    margin: 0;
    padding: 0;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }
  
  .app-grid {
    display: grid;
    grid-template-areas:
      "status status"
      "sidebar header"
      "sidebar content";
    grid-template-rows: auto auto 1fr;
    grid-template-columns: 250px 1fr;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
    margin: 0;
    padding: 0;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }
  
  .status-bar {
    grid-area: status;
    background-color: #f8f9fa;
    padding: 0.25rem 1rem;
    font-size: 0.8rem;
    border-bottom: 1px solid #e9ecef;
    width: 100%;
  }
  
  .connection-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .status-indicator {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background-color: #dc3545;
  }
  
  .status-indicator.connected {
    background-color: #28a745;
  }
  
  .status-indicator.connecting {
    background-color: #ffc107;
  }
  
  .sidebar-area {
    grid-area: sidebar;
    border-right: 1px solid #e9ecef;
    overflow: hidden;
  }
  
  .header-area {
    grid-area: header;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 1rem;
    border-bottom: 1px solid #e9ecef;
    width: 100%;
  }
  
  h1 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
  }
  
  .control-panel-btn {
    background-color: #4a90e2;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    white-space: nowrap;
    margin-left: 1rem;
  }
  
  .control-panel-btn:hover {
    background-color: #3a80d2;
  }
  
  .content-area {
    grid-area: content;
    overflow: auto;
    width: 100%;
    height: 100%;
    padding-right: 1rem;
    box-sizing: border-box;
  }
  
  /* Modal styles */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  
  .modal-content {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    width: 80%;
    max-width: 900px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #e9ecef;
  }
  
  .modal-header h2 {
    margin: 0;
    font-size: 1.5rem;
  }
  
  .close-btn {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #6c757d;
  }
  
  .close-btn:hover {
    color: #343a40;
  }
  
  .modal-body {
    padding: 1rem;
    overflow-y: auto;
    flex-grow: 1;
  }
  
  .tabs {
    display: flex;
    border-bottom: 1px solid #e9ecef;
    margin-bottom: 1rem;
  }
  
  .tab-btn {
    padding: 0.5rem 1rem;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    font-weight: 500;
    color: #6c757d;
  }
  
  .tab-btn.active {
    color: #4a90e2;
    border-bottom-color: #4a90e2;
  }
  
  .tab-content {
    padding: 0.5rem 0;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 2rem;
    color: #6c757d;
    text-align: center;
  }
</style>
