<script lang="ts">
  /**
   * ChatInput component for user message entry
   * Features: auto-resizing, accessibility, responsive design, keyboard navigation
   */
  import { createEventDispatcher, onMount } from 'svelte';
  
  // Props
  export let disabled = false;      // Whether input is disabled
  export let placeholder = 'Send a message...';  // Placeholder text
  export let value = '';            // Current input value
  export let minRows = 1;           // Minimum number of rows
  export let maxRows = 10;          // Maximum number of rows
  export let loading = false;       // Whether the system is processing a message
  
  // Local state
  let textarea: HTMLTextAreaElement;
  let rows = minRows;
  
  // Event dispatcher
  const dispatch = createEventDispatcher<{
    submit: { message: string };
    input: { value: string };
  }>();
  
  // Auto-resize textarea based on content
  function autoResize() {
    if (!textarea) return;
    
    // Reset height to calculate new height properly
    textarea.style.height = 'auto';
    
    // Calculate line height based on computed styles
    const lineHeight = parseInt(window.getComputedStyle(textarea).lineHeight) || 20;
    
    // Calculate number of rows based on scroll height
    const computedRows = Math.floor(textarea.scrollHeight / lineHeight);
    
    // Constrain rows within min/max range
    rows = Math.min(Math.max(computedRows, minRows), maxRows);
    
    // Set height directly to avoid layout shifts
    textarea.style.height = `${textarea.scrollHeight}px`;
  }
  
  // Handle text input
  function handleInput(event: Event) {
    const target = event.target as HTMLTextAreaElement;
    value = target.value;
    dispatch('input', { value });
    autoResize();
  }
  
  // Handle form submission
  function handleSubmit() {
    if (!value.trim() || disabled || loading) return;
    
    dispatch('submit', { message: value.trim() });
    value = '';
    
    // Reset textarea height
    if (textarea) {
      textarea.style.height = 'auto';
      rows = minRows;
    }
    
    // Focus back on textarea after submission
    setTimeout(() => {
      if (textarea) textarea.focus();
    }, 0);
  }
  
  // Handle keyboard events (Enter to submit, Shift+Enter for new line)
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  }
  
  // Initialize and set up resize observer
  onMount(() => {
    if (textarea && value) {
      autoResize();
    }
    
    // Set up resize observer to handle window resize events
    const resizeObserver = new ResizeObserver(() => {
      if (textarea && value) {
        autoResize();
      }
    });
    
    if (textarea) {
      resizeObserver.observe(textarea);
    }
    
    return () => {
      resizeObserver.disconnect();
    };
  });
</script>

<form 
  class="chat-input {disabled || loading ? 'disabled' : ''}"
  on:submit|preventDefault={handleSubmit}
>
  <div class="textarea-container">
    <textarea
      bind:this={textarea}
      {value}
      on:input={handleInput}
      on:keydown={handleKeydown}
      {rows}
      {placeholder}
      disabled={disabled || loading}
      aria-label="Message input"
      aria-required="true"
      data-gramm="false"
    ></textarea>
    
    {#if loading}
      <div class="loading-indicator" aria-live="polite" aria-label="Processing message">
        <span></span><span></span><span></span>
      </div>
    {/if}
  </div>
  
  <button 
    type="submit" 
    class="send-button"
    disabled={disabled || loading || !value.trim()}
    aria-label="Send message"
  >
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="22" y1="2" x2="11" y2="13"></line>
      <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
    </svg>
  </button>
</form>

<style>
  .chat-input {
    display: flex;
    align-items: flex-end;
    gap: 0.5rem;
    width: 100%;
    max-width: 100%;
    background: #fff;
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 0.5rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }
  
  .chat-input.disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
  
  .textarea-container {
    position: relative;
    flex: 1;
    min-width: 0;
  }
  
  textarea {
    width: 100%;
    resize: none;
    border: none;
    outline: none;
    background: transparent;
    padding: 0.5rem 0;
    font-family: inherit;
    font-size: 1rem;
    line-height: 1.5;
    overflow-y: auto;
    max-height: 200px; /* Prevent excessive height */
  }
  
  textarea:disabled {
    cursor: not-allowed;
    opacity: 0.7;
  }
  
  .send-button {
    display: flex;
    justify-content: center;
    align-items: center;
    background: #4a6cf7;
    color: white;
    border: none;
    border-radius: 50%;
    width: 2.5rem;
    height: 2.5rem;
    padding: 0.5rem;
    cursor: pointer;
    transition: background-color 0.2s ease;
    flex-shrink: 0;
  }
  
  .send-button:hover:not(:disabled) {
    background: #3a5ce5;
  }
  
  .send-button:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
  
  /* Loading indicator animation */
  .loading-indicator {
    position: absolute;
    right: 0.5rem;
    bottom: 0.5rem;
    display: flex;
    gap: 0.25rem;
  }
  
  .loading-indicator span {
    display: inline-block;
    width: 8px;
    height: 8px;
    background-color: #666;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
  }
  
  .loading-indicator span:nth-child(1) {
    animation-delay: -0.32s;
  }
  
  .loading-indicator span:nth-child(2) {
    animation-delay: -0.16s;
  }
  
  @keyframes bounce {
    0%, 80%, 100% { 
      transform: scale(0);
    } 
    40% { 
      transform: scale(1.0);
    }
  }
  
  /* Responsive styles */
  @media (max-width: 600px) {
    .chat-input {
      border-radius: 16px;
    }
    
    .send-button {
      width: 2.25rem;
      height: 2.25rem;
    }
  }
  
  /* Accessibility - reduce animation if user prefers */
  @media (prefers-reduced-motion: reduce) {
    .loading-indicator span {
      animation: none;
      opacity: 0.7;
    }
  }
</style>
