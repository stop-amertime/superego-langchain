<script lang="ts">
  /**
   * StreamingText component for displaying streaming text content with typing indicator
   * Handles partial outputs from the backend streaming API
   */
  import { onMount, onDestroy } from 'svelte';
  import { defaultFormat, isErrorMessage } from '../../lib/textFormatters';
  
  // Props
  export let text = '';            // The current text to display (can be partial)
  export let isStreaming = false;  // Whether text is currently streaming
  export let done = false;         // Whether the streaming is complete
  export let formatText = true;    // Whether to apply text formatting 
  
  // Local state
  let typingIndicatorVisible = true;
  let typingInterval: number | null = null;
  let formattedText: string;
  
  // Format text when it changes
  $: formattedText = formatText ? defaultFormat(text) : text;
  
  // Check for error messages
  $: hasError = isErrorMessage(text);
  
  // Watch for streaming state changes
  $: {
    if (isStreaming && !done) {
      startTypingIndicator();
    } else if (!isStreaming || done) {
      stopTypingIndicator();
    }
  }
  
  // Handle typing indicator animation
  function startTypingIndicator() {
    if (!typingInterval) {
      typingInterval = window.setInterval(() => {
        typingIndicatorVisible = !typingIndicatorVisible;
      }, 500);
    }
  }
  
  function stopTypingIndicator() {
    if (typingInterval) {
      clearInterval(typingInterval);
      typingInterval = null;
    }
  }
  
  // Clean up on component destruction
  onDestroy(() => {
    stopTypingIndicator();
  });
</script>

<div class="streaming-text {isStreaming && !done ? 'streaming' : 'done'} {hasError ? 'error' : ''}">
  <!-- Text content with formatting -->
  {#if formatText}
    <span class="content">{@html formattedText}</span>
  {:else}
    <span class="content">{text}</span>
  {/if}
  
  <!-- Typing indicator shown only when streaming is active and not done -->
  {#if isStreaming && !done}
    <span class="typing-indicator" class:visible={typingIndicatorVisible}>●</span>
  {/if}
</div>

<style>
  .streaming-text {
    white-space: pre-wrap;
    word-break: break-word;
    line-height: 1.5;
  }
  
  /* Styling for error messages */
  .streaming-text.error {
    color: #d32f2f;
  }
  
  /* Styling for code blocks */
  .streaming-text :global(code) {
    font-family: 'Courier New', Courier, monospace;
    background-color: #f5f5f5;
    padding: 0.1em 0.3em;
    border-radius: 3px;
    font-size: 0.9em;
    border: 1px solid #e0e0e0;
  }
  
  .typing-indicator {
    display: inline-block;
    opacity: 0;
    font-size: 0.8em;
    vertical-align: middle;
    margin-left: 2px;
    color: #666;
    transition: opacity 0.15s ease-in-out;
  }
  
  .typing-indicator.visible {
    opacity: 1;
  }
  
  /* Ensure smooth animations for typing indicator */
  @media (prefers-reduced-motion: no-preference) {
    .typing-indicator {
      transition: opacity 0.3s ease-in-out;
    }
  }
</style>
