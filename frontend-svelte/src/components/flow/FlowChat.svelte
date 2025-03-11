<script lang="ts">
  import { onMount } from 'svelte';
  import FlowNode from './FlowNode.svelte';
  import FlowConnector from './FlowConnector.svelte';
  import { 
    activeMessages, 
    activeFlowInstance, 
    sendUserMessage,
    addMessageToActiveInstance
  } from '../../lib/stores/flowInstances';
  import { wsClient } from '../../lib/api/websocket';
  import { wsStatus } from '../../lib/api/websocket';
  
  // State for input field
  let messageInput = '';
  let isSending = false;
  
  // Helper function to send a user message
  async function submitMessage() {
    if (!messageInput.trim() || isSending) return;
    
    isSending = true;
    
    // Get the active flow instance ID
    let flowInstanceId: string | undefined;
    const unsubscribe = activeFlowInstance.subscribe(instance => {
      flowInstanceId = instance?.id;
    });
    unsubscribe();
    
    if (!flowInstanceId) {
      console.error('No active flow instance');
      isSending = false;
      return;
    }
    
    // Create a local message object for immediate display
    const userMessage: Message = {
      id: `tmp-${Date.now()}`,
      role: 'user',
      content: messageInput,
      timestamp: new Date().toISOString(),
    };
    
    // Add to local messages for immediate feedback
    addMessageToActiveInstance(userMessage);
    
    // Send the message via WebSocket
    console.log(`Sending message to flow instance ${flowInstanceId}:`, messageInput);
    const success = sendUserMessage(messageInput, flowInstanceId);
    
    // Reset input field
    messageInput = '';
    isSending = false;
    
    if (!success) {
      console.error('Failed to send message');
      // Handle error state
    }
  }
  
  // Scroll to bottom when messages change
  let chatContainer: HTMLElement;
  $: if (chatContainer && $activeMessages) {
    setTimeout(() => {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 0);
  }
  
  onMount(() => {
    // Ensure WebSocket connection when component mounts
    if ($wsStatus !== 'connected') {
      wsClient.connect();
    }
  });
</script>

<div class="flow-chat-container">
  <div class="chat-container" bind:this={chatContainer}>
    {#if $activeMessages.length === 0}
      <div class="empty-state">
        <p>No messages yet. Start the conversation!</p>
      </div>
    {:else}
      <div class="messages">
        {#each $activeMessages as message, i}
          {#if i > 0}
            <FlowConnector />
          {/if}
          <FlowNode {message} isStreaming={message.isStreaming} />
        {/each}
      </div>
    {/if}
  </div>
  
  <div class="input-container">
    <textarea 
      bind:value={messageInput} 
      on:keydown={(e) => e.key === 'Enter' && !e.shiftKey && submitMessage()}
      placeholder="Type your message here..." 
      disabled={isSending || $wsStatus !== 'connected'}
    ></textarea>
    <button 
      on:click={submitMessage} 
      disabled={isSending || !messageInput.trim() || $wsStatus !== 'connected'}
    >
      Send
    </button>
  </div>
</div>

<style>
  .flow-chat-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;
  }
  
  .chat-container {
    flex-grow: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
  }
  
  .messages {
    width: 100%;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #888;
  }
  
  .input-container {
    display: flex;
    padding: 1rem;
    border-top: 1px solid #eee;
    background-color: white;
    width: 100%;
    box-sizing: border-box;
  }
  
  textarea {
    flex-grow: 1;
    resize: none;
    min-height: 60px;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-family: inherit;
  }
  
  button {
    margin-left: 0.5rem;
    padding: 0.5rem 1rem;
    background-color: #4a90e2;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    white-space: nowrap;
    min-width: 60px;
  }
  
  button:hover {
    background-color: #3a80d2;
  }
  
  button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
</style>
