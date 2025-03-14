<script lang="ts">
  import { onMount } from 'svelte';
  import { 
    getToolConfirmationSettings, 
    updateToolConfirmationSettings,
    toggleToolExemption 
  } from '../../api/toolService';
  import { setError } from '../../stores/uiStateStore';

  // Props
  export let instanceId: string;
  export let availableTools: string[] = [];
  
  // State
  let settings: ToolConfirmationSettings = {
    confirm_all: true,
    exempted_tools: []
  };
  let isLoading = true;
  
  // Load initial settings
  onMount(async () => {
    try {
      settings = await getToolConfirmationSettings(instanceId);
    } catch (error: any) {
      setError(`Failed to load tool settings: ${error.message || 'Unknown error'}`);
    } finally {
      isLoading = false;
    }
  });
  
  // Toggle confirm all setting
  async function toggleConfirmAll() {
    isLoading = true;
    try {
      settings = await updateToolConfirmationSettings(instanceId, {
        confirmAll: !settings.confirm_all,
        exemptedTools: settings.exempted_tools
      });
    } catch (error: any) {
      setError(`Failed to update settings: ${error.message || 'Unknown error'}`);
    } finally {
      isLoading = false;
    }
  }
  
  // Toggle exemption for a specific tool
  async function handleToggleTool(toolName: string) {
    isLoading = true;
    try {
      settings = await toggleToolExemption(instanceId, toolName, settings);
    } catch (error: any) {
      setError(`Failed to update tool exemption: ${error.message || 'Unknown error'}`);
    } finally {
      isLoading = false;
    }
  }
  
  // Check if a tool requires confirmation
  function requiresConfirmation(toolName: string): boolean {
    return settings.confirm_all && !settings.exempted_tools.includes(toolName);
  }
</script>

<div class="tool-settings-panel">
  <div class="panel-header">
    <h3>Tool Confirmation Settings</h3>
  </div>
  
  {#if isLoading}
    <div class="loading">Loading settings...</div>
  {:else}
    <div class="settings-group">
      <div class="setting-item master-switch">
        <label class="switch-label">
          <input 
            type="checkbox" 
            checked={settings.confirm_all} 
            on:change={toggleConfirmAll}
            disabled={isLoading}
          />
          <span class="switch-text">Require confirmation for all tools</span>
        </label>
      </div>
      
      {#if availableTools.length > 0}
        <div class="tool-list">
          <div class="tool-list-header">
            <span>Tool Name</span>
            <span>Requires Confirmation</span>
          </div>
          
          {#each availableTools as toolName}
            <div class="tool-item">
              <span class="tool-name">{toolName}</span>
              <label class="toggle-switch">
                <input 
                  type="checkbox" 
                  checked={requiresConfirmation(toolName)} 
                  on:change={() => handleToggleTool(toolName)}
                  disabled={isLoading || !settings.confirm_all}
                />
                <span class="toggle-slider"></span>
              </label>
            </div>
          {/each}
        </div>
      {:else}
        <div class="no-tools">
          No tools available for this flow.
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .tool-settings-panel {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    overflow: hidden;
    margin-bottom: 16px;
  }
  
  .panel-header {
    background-color: #f5f5f5;
    padding: 12px 16px;
    border-bottom: 1px solid #ddd;
  }
  
  .panel-header h3 {
    margin: 0;
    font-size: 16px;
    color: #333;
  }
  
  .loading {
    padding: 16px;
    text-align: center;
    color: #666;
    font-style: italic;
  }
  
  .settings-group {
    padding: 16px;
  }
  
  .setting-item {
    margin-bottom: 16px;
  }
  
  .master-switch {
    margin-bottom: 20px;
  }
  
  .switch-label {
    display: flex;
    align-items: center;
    cursor: pointer;
  }
  
  .switch-label input {
    margin-right: 8px;
  }
  
  .switch-text {
    font-weight: 500;
  }
  
  .tool-list {
    border: 1px solid #eee;
    border-radius: 4px;
    overflow: hidden;
  }
  
  .tool-list-header {
    display: flex;
    justify-content: space-between;
    padding: 10px 16px;
    background-color: #f9f9f9;
    border-bottom: 1px solid #eee;
    font-weight: 500;
    font-size: 14px;
  }
  
  .tool-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    border-bottom: 1px solid #eee;
  }
  
  .tool-item:last-child {
    border-bottom: none;
  }
  
  .tool-name {
    font-family: monospace;
    font-size: 14px;
  }
  
  .toggle-switch {
    position: relative;
    display: inline-block;
    width: 40px;
    height: 22px;
  }
  
  .toggle-switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  
  .toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: .3s;
    border-radius: 22px;
  }
  
  .toggle-slider:before {
    position: absolute;
    content: "";
    height: 16px;
    width: 16px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: .3s;
    border-radius: 50%;
  }
  
  input:checked + .toggle-slider {
    background-color: #4CAF50;
  }
  
  input:disabled + .toggle-slider {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  input:checked + .toggle-slider:before {
    transform: translateX(18px);
  }
  
  .no-tools {
    padding: 16px;
    text-align: center;
    color: #666;
    font-style: italic;
  }
</style>
