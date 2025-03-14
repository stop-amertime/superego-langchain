<script lang="ts">
  import { onMount } from 'svelte';
  import { flowInstancesPromise, refreshFlowInstances } from '../../stores/flowInstancesStore';
  import { createEventDispatcher } from 'svelte';
  import { formatDistanceToNow } from 'date-fns';
  
  const dispatch = createEventDispatcher();
  let selectedInstanceId: string | null = null;

  function selectInstance(instanceId: string) {
    selectedInstanceId = instanceId;
    dispatch('select', instanceId);
  }

  onMount(refreshFlowInstances);
</script>

<div class="flow-instances">
  <h3>Recent Flows</h3>
  
  {#await $flowInstancesPromise}
    <div class="loading">Loading...</div>
  {:then instances}
    {#if instances.length === 0}
      <div class="empty-state">No flow instances available</div>
    {:else}
      <ul>
        {#each instances as instance}
          <li 
            class:active={selectedInstanceId === instance.id}
            on:click={() => selectInstance(instance.id)}
            on:keydown={(e: KeyboardEvent) => e.key === 'Enter' && selectInstance(instance.id)}
            tabindex="0"
            role="button"
            aria-pressed={selectedInstanceId === instance.id}
          >
            <div class="instance-name">{instance.flow_name}</div>
            <div class="instance-meta">
              <span class="instance-time">
                {instance.updated_at ? formatDistanceToNow(new Date(instance.updated_at), { addSuffix: true }) : ''}
              </span>
              <span class="instance-status {instance.status}">{instance.status}</span>
            </div>
            {#if instance.last_message}
              <div class="instance-preview">{instance.last_message}</div>
            {/if}
          </li>
        {/each}
      </ul>
    {/if}
  {:catch error}
    <div class="error-state">
      <p>Error: {error.message}</p>
      <button on:click={refreshFlowInstances}>Retry</button>
    </div>
  {/await}
</div>

<style>
  .flow-instances {
    padding: 1rem;
    height: 100%;
  }
  
  h3 {
    font-size: 1.1rem;
    margin: 0 0 1rem 0;
  }
  
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  li {
    padding: 0.75rem;
    border-radius: 4px;
    cursor: pointer;
    background: #f5f5f5;
    border-left: 3px solid transparent;
  }
  
  li:hover { background: #eaeaea; }
  li.active { 
    background: #e6f7ff;
    border-left-color: #1890ff;
  }
  
  .instance-name {
    font-weight: 500;
    margin-bottom: 0.25rem;
  }
  
  .instance-meta {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    color: #666;
    margin-bottom: 0.5rem;
  }
  
  .instance-preview {
    font-size: 0.85rem;
    color: #666;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .instance-status {
    padding: 0.1rem 0.4rem;
    border-radius: 10px;
    font-size: 0.7rem;
  }
  
  .instance-status.active { background: #e6f7ff; color: #1890ff; }
  .instance-status.completed { background: #f6ffed; color: #52c41a; }
  .instance-status.error { background: #fff1f0; color: #f5222d; }
  
  .loading, .empty-state, .error-state {
    text-align: center;
    padding: 1rem;
    color: #666;
  }
  
  button {
    background: #1890ff;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    margin-top: 0.5rem;
  }
</style>
