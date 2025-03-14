<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { currentSteps, partialOutput, executionState } from '../../stores/currentFlowStore';
  import type { FlowStep } from '../../types';
  
  import SuperegoCard from './SuperegoCard.svelte';
  import InnerAgentCard from './InnerAgentCard.svelte';
  import UserMessageCard from './UserMessageCard.svelte';
  import ConnectionLine from './ConnectionLine.svelte';
  
  // Keep track of expanded card states
  let expandedCards = new Set<string>();
  
  // Reference to the conversation container for auto-scrolling
  let conversationContainer: HTMLElement;
  
  // Function to handle expand/collapse of cards
  function handleExpand(event: CustomEvent) {
    const { stepId, expanded } = event.detail;
    
    if (expanded) {
      expandedCards.add(stepId);
    } else {
      expandedCards.delete(stepId);
    }
    expandedCards = expandedCards; // Trigger reactivity
  }
  
  // Auto-scroll when new messages are added
  $: if ($currentSteps && conversationContainer) {
    // Wait for DOM to update before scrolling
    setTimeout(() => {
      conversationContainer.scrollTop = conversationContainer.scrollHeight;
    }, 50);
  }
  
  // Helper to determine if connections should be shown
  function shouldShowConnection(index: number, steps: FlowStep[]): boolean {
    if (index === steps.length - 1) return false;
    return true;
  }
  
  // Helper to check if a card should be expanded
  function isCardExpanded(stepId: string): boolean {
    return expandedCards.has(stepId);
  }
</script>

<div class="conversation-container" bind:this={conversationContainer}>
  {#if $currentSteps.length === 0}
    <div class="empty-state">
      <p>No conversation started. Send a message to begin.</p>
    </div>
  {:else}
    {#each $currentSteps as step, index}
      {#if step.role === 'user'}
        <UserMessageCard {step} />
      {:else if step.agent_id.includes('superego')}
        <SuperegoCard 
          {step} 
          expanded={isCardExpanded(step.step_id)} 
          on:expand={handleExpand} 
        />
      {:else}
        <InnerAgentCard 
          {step} 
          expanded={isCardExpanded(step.step_id)} 
          on:expand={handleExpand} 
        />
      {/if}
      
      {#if shouldShowConnection(index, $currentSteps)}
        <ConnectionLine />
      {/if}
    {/each}
    
    {#if $executionState.isExecuting && $partialOutput}
      <div class="partial-output">
        <div class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
        <div class="partial-text">{$partialOutput}</div>
      </div>
    {/if}
    
    {#if $executionState.error}
      <div class="error-message">
        Error: {$executionState.error}
      </div>
    {/if}
  {/if}
</div>

<style>
  .conversation-container {
    display: flex;
    flex-direction: column;
    padding: 16px;
    overflow-y: auto;
    height: 100%;
    background-color: #f8f9fa;
  }
  
  .empty-state {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: #666;
    font-style: italic;
  }
  
  .partial-output {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 12px;
    background: white;
    opacity: 0.8;
  }
  
  .typing-indicator {
    display: flex;
    gap: 4px;
    margin-bottom: 8px;
  }
  
  .typing-indicator span {
    width: 8px;
    height: 8px;
    background: #999;
    border-radius: 50%;
    display: inline-block;
    animation: pulse 1s infinite;
  }
  
  .typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
  }
  
  .typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
  }
  
  .partial-text {
    white-space: pre-wrap;
    word-break: break-word;
  }
  
  .error-message {
    padding: 12px;
    margin-bottom: 12px;
    background-color: #ffeef0;
    border: 1px solid #ffcdd2;
    border-radius: 4px;
    color: #cb2431;
  }
</style>
