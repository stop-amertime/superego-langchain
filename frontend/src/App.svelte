<script lang="ts">
  import NavigatorPanel from './components/layout/NavigatorPanel.svelte';
  import ConversationView from './components/conversation/ConversationView.svelte';
  import { selectedInstanceId } from './stores/currentFlowStore';
</script>

<div class="app-layout">
  <div class="navigator-panel">
    <NavigatorPanel />
  </div>
  
  <div class="conversation-panel">
    {#if $selectedInstanceId}
      <ConversationView />
    {:else}
      <div class="placeholder">
        <h2>Flow Conversation Panel</h2>
        <p>Select a flow instance or create a new one to begin</p>
      </div>
    {/if}
  </div>
  
  <div class="details-panel">
    <div class="placeholder">
      <h2>Details Panel</h2>
      <p>For future expansion</p>
    </div>
  </div>
</div>

<style>
  .app-layout {
    display: grid;
    grid-template-columns: 280px 1fr 300px;
    height: 100vh;
    width: 100%;
    overflow: hidden;
  }
  
  .navigator-panel {
    height: 100%;
    overflow-y: auto;
  }
  
  .conversation-panel {
    height: 100%;
    overflow-y: auto;
    border-right: 1px solid #eee;
  }
  
  .details-panel {
    height: 100%;
    overflow-y: auto;
  }
  
  .placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 1rem;
    color: #888;
    text-align: center;
  }
  
  h2 {
    margin: 0 0 1rem 0;
    font-size: 1.5rem;
  }
  
  p {
    margin: 0;
    font-size: 1rem;
  }
  
  /* Media query for smaller screens */
  @media (max-width: 1200px) {
    .app-layout {
      grid-template-columns: 280px 1fr 0;
    }
    
    .details-panel {
      display: none;
    }
  }
  
  @media (max-width: 768px) {
    .app-layout {
      grid-template-columns: 1fr;
      grid-template-rows: auto 1fr;
    }
    
    .navigator-panel {
      height: auto;
      max-height: 40vh;
    }
    
    .details-panel {
      display: none;
    }
  }
</style>
