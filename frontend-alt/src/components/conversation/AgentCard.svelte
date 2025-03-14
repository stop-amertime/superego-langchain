<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { slide } from 'svelte/transition';
  import type { FlowStep } from '../../types';
  
  export let step: FlowStep;
  export let expanded = false;
  
  const dispatch = createEventDispatcher();
  
  function toggleExpanded() {
    expanded = !expanded;
    dispatch('expand', { stepId: step.step_id, expanded });
  }
  
  function formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  }
</script>

<div class="agent-card" aria-expanded={expanded} data-step-id={step.step_id}>
  <div class="header">
    <div class="header-left">
      <span class="agent-id">{step.agent_id}</span>
      <span class="timestamp">{formatTimestamp(step.timestamp)}</span>
    </div>
    <button 
      class="expand-button" 
      on:click={toggleExpanded} 
      aria-label={expanded ? 'Hide details' : 'Show details'}
    >
      {expanded ? '▼' : '▶'}
    </button>
  </div>
  
  <div class="content">
    <slot name="content">
      <div class="response">{step.response}</div>
    </slot>
  </div>
  
  {#if expanded}
    <div class="details" transition:slide={{ duration: 150 }}>
      <slot name="details"></slot>
    </div>
  {/if}
</div>

<style>
  .agent-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    margin-bottom: 12px;
    padding: 12px;
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    max-width: 90%;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    font-size: 0.9em;
    color: #555;
  }
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .agent-id {
    font-weight: 500;
  }
  
  .timestamp {
    color: #777;
    font-size: 0.85em;
  }
  
  .expand-button {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 0.9em;
    color: #555;
    padding: 4px;
  }
  
  .expand-button:hover {
    color: #000;
  }
  
  .content {
    margin-bottom: 8px;
  }
  
  .response {
    white-space: pre-wrap;
    word-break: break-word;
  }
  
  .details {
    margin-top: 8px;
    padding: 8px;
    border-top: 1px solid #eee;
    background: #f9f9f9;
    border-radius: 0 0 8px 8px;
  }
</style>
