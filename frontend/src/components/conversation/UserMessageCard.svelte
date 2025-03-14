<script lang="ts">
  import type { FlowStep } from '../../types';
  
  export let step: FlowStep;
  
  function formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  }
</script>

<div class="user-message" data-step-id={step.step_id}>
  <div class="header">
    <span class="user-label">User</span>
    <span class="timestamp">{formatTimestamp(step.timestamp)}</span>
  </div>
  
  <div class="message">
    {step.response}
  </div>
</div>

<style>
  .user-message {
    border: 1px solid #e1e4e8;
    border-left: 4px solid #ff6b6b;
    border-radius: 8px;
    margin-bottom: 12px;
    padding: 12px;
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    align-self: flex-start;
    max-width: 90%;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    font-size: 0.9em;
  }
  
  .user-label {
    font-weight: 500;
    color: #333;
  }
  
  .timestamp {
    color: #777;
    font-size: 0.85em;
  }
  
  .message {
    white-space: pre-wrap;
    word-break: break-word;
  }
</style>
