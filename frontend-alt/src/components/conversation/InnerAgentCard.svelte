<script lang="ts">
  import AgentCard from './AgentCard.svelte';
  import type { FlowStep } from '../../types';
  
  export let step: FlowStep;
  export let expanded = false;
  
  // Helper function to pretty print JSON
  function formatJSON(data: any): string {
    try {
      return JSON.stringify(data, null, 2);
    } catch (e) {
      return String(data);
    }
  }
</script>

<AgentCard {step} {expanded} on:expand>
  <div slot="content" class="inner-agent-content">
    {#if step.tool_usage}
      <div class="tool-usage-badge">
        Tool: {step.tool_usage.tool_name}
      </div>
    {/if}
    <div class="response">{step.response}</div>
  </div>
  
  <div slot="details">
    {#if step.system_prompt}
      <div class="system-prompt">
        <h4>System Prompt:</h4>
        <pre>{step.system_prompt}</pre>
      </div>
    {/if}
    
    {#if step.tool_usage}
      <div class="tool-details">
        <h4>Tool: {step.tool_usage.tool_name}</h4>
        
        <div class="tool-input">
          <h5>Input:</h5>
          <pre>{formatJSON(step.tool_usage.input)}</pre>
        </div>
        
        <div class="tool-output">
          <h5>Output:</h5>
          <pre>{formatJSON(step.tool_usage.output)}</pre>
        </div>
      </div>
    {/if}
    
    {#if step.input}
      <div class="input">
        <h4>Input:</h4>
        <pre>{step.input}</pre>
      </div>
    {/if}
  </div>
</AgentCard>

<style>
  .inner-agent-content {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .tool-usage-badge {
    display: inline-block;
    background: #edf2f7;
    color: #4a5568;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: 500;
    border: 1px solid #cbd5e0;
    margin-bottom: 4px;
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
  
  h5 {
    margin: 8px 0 4px;
    font-size: 0.85em;
    color: #666;
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
  
  .system-prompt, .tool-details, .input {
    margin-bottom: 12px;
  }
  
  .tool-input, .tool-output {
    margin-left: 8px;
  }
</style>
