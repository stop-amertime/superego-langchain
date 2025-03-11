<script lang="ts">
  // Each card in the flow
  export let message: Message;
  export let isStreaming = false;

  // Simple logic to determine node appearance based on message type
  $: nodeType = message.role;
  $: isThinking = isStreaming && message.role === 'assistant';
</script>

<div class="node {nodeType}">
  <div class="header">
    <div class="role">{nodeType}</div>
    {#if message.role === 'superego' && message.decision}
      <div class="decision {message.decision?.toLowerCase()}">{message.decision}</div>
    {/if}
  </div>
  
  <div class="content">
    {#if message.role === 'superego'}
      {#if message.decision}
        <div class="reason">{(message as unknown as SuperegoEvaluation).reason || "Superego evaluation"}</div>
      {/if}
      {#if message.thinking}
        <details>
          <summary>Thinking</summary>
          <div class="thinking">{message.thinking}</div>
        </details>
      {/if}
    {:else if message.role === 'assistant' && isThinking}
      <div class="thinking-indicator">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
    {:else}
      <div class="message-content">{message.content}</div>
    {/if}
  </div>
</div>

<style>
  .node {
    width: 100%;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }
  
  .role {
    font-weight: bold;
    text-transform: capitalize;
  }
  
  .decision {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: bold;
  }
  
  .decision.allow {
    background-color: #d4edda;
    color: #155724;
  }
  
  .decision.caution {
    background-color: #fff3cd;
    color: #856404;
  }
  
  .decision.block {
    background-color: #f8d7da;
    color: #721c24;
  }
  
  .decision.analyzing, .decision.error {
    background-color: #cce5ff;
    color: #004085;
  }
  
  .content {
    margin-top: 0.5rem;
  }
  
  .reason {
    font-style: italic;
    margin-bottom: 0.5rem;
  }
  
  .thinking {
    font-family: monospace;
    white-space: pre-wrap;
    font-size: 0.9rem;
    background-color: rgba(0,0,0,0.05);
    padding: 0.5rem;
    border-radius: 4px;
    margin-top: 0.5rem;
  }
  
  /* Clean, minimal styling for different node types */
  .user { 
    background-color: #f0f4f8; 
  }
  
  .assistant { 
    background-color: #e3f2fd; 
  }
  
  .superego { 
    background-color: #fff8e1; 
  }
  
  .system {
    background-color: #f1f1f1;
    font-style: italic;
  }
  
  .message-content {
    white-space: pre-wrap;
  }
  
  /* Thinking animation */
  .thinking-indicator {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    padding: 1rem;
  }
  
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #333;
    opacity: 0.6;
    animation: pulse 1.5s infinite ease-in-out;
  }
  
  .dot:nth-child(2) {
    animation-delay: 0.2s;
  }
  
  .dot:nth-child(3) {
    animation-delay: 0.4s;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 0.4; transform: scale(0.8); }
    50% { opacity: 1; transform: scale(1); }
  }
</style>
