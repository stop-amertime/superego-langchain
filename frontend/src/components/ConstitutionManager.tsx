import React, { useState, useEffect } from 'react';
import { Constitution } from '../types';
import { 
  useConstitutions, 
  useCreateConstitution, 
  useUpdateConstitution, 
  useDeleteConstitution 
} from '../api/queryHooks';
import './ConstitutionManager.css';

const ConstitutionManager: React.FC = () => {
  const [selectedConstitution, setSelectedConstitution] = useState<Constitution | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [editedContent, setEditedContent] = useState('');
  const [editedId, setEditedId] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [showStatus, setShowStatus] = useState(false);

  // Fetch constitutions using React Query
  const { 
    data: constitutions = [], 
    isLoading, 
    error: queryError,
    refetch 
  } = useConstitutions();
  
  // Mutations for creating, updating, and deleting constitutions
  const createMutation = useCreateConstitution();
  const updateMutation = useUpdateConstitution(editedId);
  const deleteMutation = useDeleteConstitution();
  
  // Error handling
  const error = queryError ? String(queryError) : 
                createMutation.error ? String(createMutation.error) : 
                updateMutation.error ? String(updateMutation.error) : 
                deleteMutation.error ? String(deleteMutation.error) : null;

  // Reset the form when switching between edit/create modes
  useEffect(() => {
    if (isCreating) {
      setEditedName('');
      setEditedContent('');
      setEditedId('');
    } else if (isEditing && selectedConstitution) {
      setEditedName(selectedConstitution.name);
      setEditedContent(selectedConstitution.content);
      setEditedId(selectedConstitution.id);
    }
  }, [isCreating, isEditing, selectedConstitution]);

  // Select a constitution to view
  const handleSelectConstitution = (constitution: Constitution) => {
    setSelectedConstitution(constitution);
    setIsEditing(false);
    setIsCreating(false);
  };

  // Start editing the selected constitution
  const handleStartEditing = () => {
    if (!selectedConstitution) return;
    setIsEditing(true);
    setIsCreating(false);
    setEditedName(selectedConstitution.name);
    setEditedContent(selectedConstitution.content);
    setEditedId(selectedConstitution.id);
  };

  // Start creating a new constitution
  const handleStartCreating = () => {
    setIsCreating(true);
    setIsEditing(false);
    setSelectedConstitution(null);
    setEditedName('');
    setEditedContent('');
    setEditedId('');
  };

  // Cancel editing or creating
  const handleCancel = () => {
    setIsEditing(false);
    setIsCreating(false);
  };

  // Save the edited or created constitution
  const handleSave = () => {
    // Validate inputs
    if (!editedName.trim()) {
      showStatusMessage('Name cannot be empty', 'error');
      return;
    }
    
    if (!editedContent.trim()) {
      showStatusMessage('Content cannot be empty', 'error');
      return;
    }
    
    // Generate an ID if creating a new constitution
    const constitutionId = isCreating 
      ? editedId.trim() || editedName.toLowerCase().replace(/\s+/g, '_')
      : editedId;
    
    // Check for duplicate ID when creating
    if (isCreating && constitutions.some(c => c.id === constitutionId)) {
      showStatusMessage(`A constitution with ID "${constitutionId}" already exists`, 'error');
      return;
    }
    
    // Create or update the constitution
    if (isCreating) {
      createMutation.mutate(
        {
          id: constitutionId,
          name: editedName,
          content: editedContent
        },
        {
          onSuccess: (data) => {
            showStatusMessage('Constitution created successfully', 'success');
            setIsEditing(false);
            setIsCreating(false);
            setSelectedConstitution(data);
          },
          onError: (error) => {
            showStatusMessage(`Failed to create constitution: ${error}`, 'error');
          }
        }
      );
      showStatusMessage('Creating constitution...', 'info');
    } else if (isEditing) {
      updateMutation.mutate(
        {
          name: editedName,
          content: editedContent
        },
        {
          onSuccess: (data) => {
            showStatusMessage('Constitution updated successfully', 'success');
            setIsEditing(false);
            setIsCreating(false);
            setSelectedConstitution(data);
          },
          onError: (error) => {
            showStatusMessage(`Failed to update constitution: ${error}`, 'error');
          }
        }
      );
      showStatusMessage('Updating constitution...', 'info');
    }
  };
  
  // Delete the selected constitution
  const handleDelete = () => {
    if (!selectedConstitution) return;
    
    if (window.confirm(`Are you sure you want to delete "${selectedConstitution.name}"?`)) {
      deleteMutation.mutate(
        selectedConstitution.id,
        {
          onSuccess: () => {
            showStatusMessage('Constitution deleted successfully', 'success');
            setSelectedConstitution(null);
          },
          onError: (error) => {
            showStatusMessage(`Failed to delete constitution: ${error}`, 'error');
          }
        }
      );
    }
  };
  
  // Show a status message for a few seconds
  const showStatusMessage = (message: string, type: 'success' | 'error' | 'info') => {
    setStatusMessage(message);
    setShowStatus(true);
    
    // Add a class based on the message type
    const statusElement = document.querySelector('.constitution-status');
    if (statusElement) {
      statusElement.className = `constitution-status ${type}`;
    }
    
    // Hide the message after a few seconds
    setTimeout(() => {
      setShowStatus(false);
    }, 3000);
  };

  if (isLoading) {
    return <div className="constitution-manager-loading">Loading constitutions...</div>;
  }

  if (error) {
    return <div className="constitution-manager-error">{error}</div>;
  }

  return (
    <div className="constitution-manager">
      <div className="constitution-sidebar">
        <h3>Constitutions</h3>
        <div className="constitution-list">
          {constitutions.map(constitution => (
            <div 
              key={constitution.id}
              className={`constitution-item ${selectedConstitution?.id === constitution.id ? 'selected' : ''}`}
              onClick={() => handleSelectConstitution(constitution)}
            >
              {constitution.name}
            </div>
          ))}
        </div>
        <button 
          className="create-constitution-button"
          onClick={handleStartCreating}
        >
          Create New Constitution
        </button>
      </div>
      
      <div className="constitution-content">
        {showStatus && (
          <div className="constitution-status">
            {statusMessage}
          </div>
        )}
        
        {isCreating ? (
          <div className="constitution-editor">
            <h3>Create New Constitution</h3>
            <div className="editor-form">
              <div className="form-group">
                <label htmlFor="constitution-id">ID (optional):</label>
                <input 
                  id="constitution-id"
                  type="text" 
                  value={editedId} 
                  onChange={e => setEditedId(e.target.value)}
                  placeholder="Leave blank to generate from name"
                />
                <small>If left blank, an ID will be generated from the name</small>
              </div>
              <div className="form-group">
                <label htmlFor="constitution-name">Name:</label>
                <input 
                  id="constitution-name"
                  type="text" 
                  value={editedName} 
                  onChange={e => setEditedName(e.target.value)}
                  placeholder="Enter constitution name"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="constitution-content">Content:</label>
                <textarea 
                  id="constitution-content"
                  value={editedContent} 
                  onChange={e => setEditedContent(e.target.value)}
                  placeholder="Enter constitution content in markdown format"
                  rows={20}
                  required
                />
              </div>
              <div className="editor-actions">
                <button onClick={handleCancel}>Cancel</button>
                <button onClick={handleSave} className="save-button">Save</button>
              </div>
            </div>
          </div>
        ) : isEditing ? (
          <div className="constitution-editor">
            <h3>Edit Constitution</h3>
            <div className="editor-form">
              <div className="form-group">
                <label htmlFor="constitution-id">ID:</label>
                <input 
                  id="constitution-id"
                  type="text" 
                  value={editedId} 
                  disabled
                />
                <small>ID cannot be changed</small>
              </div>
              <div className="form-group">
                <label htmlFor="constitution-name">Name:</label>
                <input 
                  id="constitution-name"
                  type="text" 
                  value={editedName} 
                  onChange={e => setEditedName(e.target.value)}
                  placeholder="Enter constitution name"
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="constitution-content">Content:</label>
                <textarea 
                  id="constitution-content"
                  value={editedContent} 
                  onChange={e => setEditedContent(e.target.value)}
                  placeholder="Enter constitution content in markdown format"
                  rows={20}
                  required
                />
              </div>
              <div className="editor-actions">
                <button onClick={handleCancel}>Cancel</button>
                <button onClick={handleSave} className="save-button">Save</button>
              </div>
            </div>
          </div>
        ) : selectedConstitution ? (
          <div className="constitution-viewer">
            <div className="viewer-header">
              <h3>{selectedConstitution.name}</h3>
              <button onClick={handleStartEditing}>Edit</button>
            </div>
            <div className="constitution-content-display">
              <pre>{selectedConstitution.content}</pre>
            </div>
          </div>
        ) : (
          <div className="no-selection">
            <p>Select a constitution from the list or create a new one</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConstitutionManager;
