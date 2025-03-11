<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { 
    constitutions, 
    activeConstitutionId,
    createConstitution,
    updateConstitution,
    deleteConstitution 
  } from '../../lib/stores/constitutions';
  
  const dispatch = createEventDispatcher();
  
  // Panel visibility state
  export let isOpen = false;
  
  // Toggle panel visibility
  function togglePanel() {
    isOpen = !isOpen;
  }
  
  // Editing state
  let isEditing = false;
  let isCreating = false;
  let editingConstitution: Constitution | null = null;
  let newConstitutionName = '';
  let newConstitutionContent = '';
  
  // Start editing a constitution
  function startEdit(constitution: Constitution) {
    editingConstitution = { ...constitution };
    isEditing = true;
    isCreating = false;
  }
  
  // Start creating a new constitution
  function startCreate() {
    newConstitutionName = '';
    newConstitutionContent = '# New Constitution\n\nAdd your rules here...';
    isCreating = true;
    isEditing = false;
    editingConstitution = null;
  }
  
  // Cancel editing or creating
  function cancelEdit() {
    isEditing = false;
    isCreating = false;
    editingConstitution = null;
  }
  
  // Save constitution changes
  async function saveChanges() {
    if (isEditing && editingConstitution) {
      try {
        await updateConstitution(editingConstitution.id, {
          name: editingConstitution.name,
          content: editingConstitution.content
        });
        
        isEditing = false;
        editingConstitution = null;
      } catch (error) {
        console.error('Failed to update constitution', error);
        // Show error message
      }
    }
  }
  
  // Create a new constitution
  async function saveNewConstitution() {
    if (isCreating && newConstitutionName.trim() && newConstitutionContent.trim()) {
      try {
        await createConstitution({
          name: newConstitutionName,
          content: newConstitutionContent
        });
        
        isCreating = false;
      } catch (error) {
        console.error('Failed to create constitution', error);
        // Show error message
      }
    }
  }
  
  // Delete a constitution
  async function handleDelete(constitutionId: string) {
    if (confirm('Are you sure you want to delete this constitution?')) {
      try {
        await deleteConstitution(constitutionId);
      } catch (error) {
        console.error('Failed to delete constitution', error);
        // Show error message
      }
    }
  }
  
  // Set active constitution
  function setActive(constitutionId: string) {
    activeConstitutionId.set(constitutionId);
  }
</script>

<div class="constitution-container">
  {#if isOpen}
    <div class="panel">
      
      {#if isEditing && editingConstitution}
        <div class="edit-form">
          <input 
            type="text" 
            bind:value={editingConstitution.name} 
            placeholder="Constitution name"
          />
          <textarea 
            bind:value={editingConstitution.content} 
            placeholder="Constitution content"
            rows="10"
          ></textarea>
          <div class="button-group">
            <button on:click={saveChanges}>Save</button>
            <button on:click={cancelEdit}>Cancel</button>
          </div>
        </div>
      {:else if isCreating}
        <div class="edit-form">
          <input 
            type="text" 
            bind:value={newConstitutionName} 
            placeholder="Constitution name"
          />
          <textarea 
            bind:value={newConstitutionContent} 
            placeholder="Constitution content"
            rows="10"
          ></textarea>
          <div class="button-group">
            <button on:click={saveNewConstitution} disabled={!newConstitutionName.trim()}>
              Create
            </button>
            <button on:click={cancelEdit}>Cancel</button>
          </div>
        </div>
      {:else}
        {#if Object.keys($constitutions).length === 0}
          <div class="empty-state">No constitutions available</div>
        {:else}
          <div class="constitution-list">
            {#each Object.values($constitutions) as constitution (constitution.id)}
              <div class="constitution-item" 
                class:active={$activeConstitutionId === constitution.id}
              >
                <div class="constitution-header">
                  <h3>{constitution.name}</h3>
                  <div class="actions">
                    <button 
                      class="action-btn set-btn" 
                      on:click={() => setActive(constitution.id)}
                      disabled={$activeConstitutionId === constitution.id}
                    >
                      Set Active
                    </button>
                    <button 
                      class="action-btn edit-btn" 
                      on:click={() => startEdit(constitution)}
                    >
                      Edit
                    </button>
                    <button 
                      class="action-btn delete-btn"
                      on:click={() => handleDelete(constitution.id)}
                      disabled={constitution.id === 'default' || constitution.id === 'none'}
                    >
                      Delete
                    </button>
                  </div>
                </div>
                <div class="constitution-preview">
                  <pre>{constitution.content.slice(0, 100)}...</pre>
                </div>
              </div>
            {/each}
          </div>
        {/if}
        
        <button class="add-btn" on:click={startCreate}>
          Add New Constitution
        </button>
      {/if}
    </div>
  {/if}
</div>

<style>
  .constitution-container {
    width: 100%;
  }
  
  .panel {
    width: 100%;
  }
  
  h2 {
    margin-top: 0;
    border-bottom: 1px solid #e9ecef;
    padding-bottom: 0.5rem;
  }
  
  .empty-state {
    padding: 1rem;
    text-align: center;
    color: #6c757d;
  }
  
  .constitution-list {
    margin-bottom: 1rem;
  }
  
  .constitution-item {
    border: 1px solid #e9ecef;
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 1rem;
  }
  
  .constitution-item.active {
    border-color: #4a90e2;
    background-color: #f0f7ff;
  }
  
  .constitution-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }
  
  .constitution-header h3 {
    margin: 0;
    font-size: 1.1rem;
  }
  
  .actions {
    display: flex;
    gap: 0.5rem;
  }
  
  .action-btn {
    padding: 0.3rem 0.5rem;
    background-color: #f8f9fa;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-size: 0.8rem;
    cursor: pointer;
  }
  
  .action-btn:hover:not(:disabled) {
    background-color: #e9ecef;
  }
  
  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .set-btn {
    background-color: #e3f2fd;
    border-color: #90caf9;
  }
  
  .edit-btn {
    background-color: #fff3cd;
    border-color: #ffeeba;
  }
  
  .delete-btn {
    background-color: #f8d7da;
    border-color: #f5c6cb;
  }
  
  .constitution-preview {
    font-size: 0.9rem;
    background-color: #f8f9fa;
    padding: 0.5rem;
    border-radius: 4px;
    white-space: pre-wrap;
    max-height: 100px;
    overflow-y: auto;
  }
  
  .add-btn {
    margin-top: 1rem;
    width: 100%;
    padding: 0.5rem;
    background-color: #4a90e2;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .add-btn:hover {
    background-color: #3a80d2;
  }
  
  .edit-form {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  input, textarea {
    padding: 0.5rem;
    border: 1px solid #ced4da;
    border-radius: 4px;
    font-family: inherit;
  }
  
  textarea {
    font-family: monospace;
    resize: vertical;
  }
  
  .button-group {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }
  
  .button-group button {
    flex: 1;
    padding: 0.5rem;
    background-color: #4a90e2;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .button-group button:last-child {
    background-color: #6c757d;
  }
  
  .button-group button:hover:not(:disabled) {
    opacity: 0.9;
  }
  
  .button-group button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
</style>
