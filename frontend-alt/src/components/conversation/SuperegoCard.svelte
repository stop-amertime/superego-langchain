<script lang="ts">
  import AgentCard from './AgentCard.svelte';
  import type { FlowStep } from '../../types';
  
  export let step: FlowStep;
  export let expanded = false;
  
  // Ensure we have a decision (for type safety)
  const decision = step.decision || 'UNKNOWN';
  
  // Decision style class mapping
  const decisionClasses = {
    'ACCEPT': 'accept',
    'BLOCK': 'block',
    'CAUTION': 'caution',
    'NEEDS_CLARIFICATION': 'needs-clarification',
    'UNKNOWN': ''
  };
</script>

<AgentCard {step} {expanded} on:expand>
  <div slot="content" class="superego-content">
    <div class="decision {decisionClasses[decision]}">
      Decision: {decision}
    </div>
    <div class="response">{step.response}</div>
  </div>
  
  <div slot="details">
    {#if step.constitution}
      <div class="constitution">
        <h4>Constitution:</h4>
        <pre>{step.constitution}</pre>
      </div>
    {/if}
    
    {#if step.input}
      <div class="input">
        <h4>Evaluated Input:</h4>
        <pre>{step.input}</pre>
      </div>
    {/if}
  </div>
</AgentCard>

<style>
  .superego-content {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .decision {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-weight: 500;
    font-size: 0.9em;
    margin-bottom: 4px;
  }
  
  .accept {
    background: #e6ffed;
    color: #22863a;
    border: 1px solid #b7ebc8;
  }
  
  .block {
    background: #ffeef0;
    color: #cb2431;
    border: 1px solid #ffcdd2;
  }
  
  .caution {
    background: #fff5b1;
    color: #735c0f;
    border: 1px solid #f9e589;
  }
  
  .needs-clarification {
    background: #f1f8ff;
    color: #0366d6;
    border: 1px solid #c8e1ff;
  }
  
  .response {
    white-space: pre-wrap;
    word-break: break-word;
  }
  
  h4 {
    margin: 10px 0 5px;
    font-size: 0.9em;
    color: #555;
  }
  
  pre {
    background: #f6f8fa;
    padding: 8px;
    border-radius: 4px;
    overflow: auto;
    font-size: 0.9em;
    margin: 5px 0;
    max-height: 300px;
  }
  
  .constitution, .input {
    margin-bottom: 12px;
  }
</style>
