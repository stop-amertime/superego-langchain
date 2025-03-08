import React, { useState, useEffect } from 'react';
import { getWebSocketClient } from '../api/websocketClient';
import { FlowInstance, FlowConfig, FlowTemplate } from '../types';
import './InstanceSidebar.css';

interface InstanceSidebarProps {
  selectedInstanceId: string | null;
  onSelectInstance: (instanceId: string) => void;
  onCreateInstance: (instanceData: {name: string, flow_config_id: string, description?: string}) => void;
  flowConfigs: FlowConfig[];
  flowInstances: FlowInstance[];
  loading: boolean;
}

const InstanceSidebar: React.FC<InstanceSidebarProps> = ({
  selectedInstanceId,
  onSelectInstance,
  onCreateInstance,
  flowConfigs,
  flowInstances,
  loading
}) => {
  const [error, setError] = useState<string | null>(null);
  
  // UI state
  const [isCreating, setIsCreating] = useState(false);
  const [newInstanceName, setNewInstanceName] = useState('');
  const [newInstanceDescription, setNewInstanceDescription] = useState('');
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null);
  const [isRenaming, setIsRenaming] = useState<string | null>(null);
  const [newName, setNewName] = useState('');
  
  // Handle create instance form submission
  const handleCreateInstanceSubmit = () => {
    if (!newInstanceName || !selectedConfigId) return;
    
    // Call the parent method to create the instance
    onCreateInstance({
      name: newInstanceName,
      flow_config_id: selectedConfigId,
      description: newInstanceDescription || undefined
    });
    
    // Reset form
    setNewInstanceName('');
    setNewInstanceDescription('');
    setSelectedConfigId(null);
    setIsCreating(false);
  };
  
  // Handle rename instance via API
  const handleRenameInstance = (instanceId: string) => {
    if (!newName) return;
    
    // Use the WebSocket client directly for simple operations
    const wsClient = getWebSocketClient();
    wsClient.sendCommand('update_flow_instance', {
      id: instanceId,
      name: newName
    });
    
    // Reset form
    setNewName('');
    setIsRenaming(null);
  };
  
  // Handle delete instance via API
  const handleDeleteInstance = (instanceId: string) => {
    if (!window.confirm('Are you sure you want to delete this instance?')) return;
    
    // Use the WebSocket client directly for simple operations
    const wsClient = getWebSocketClient();
    wsClient.sendCommand('delete_flow_instance', {
      id: instanceId
    });
  };
  
  if (loading) {
    return <div className="instance-sidebar loading">Loading instances...</div>;
  }
  
  if (error) {
    return <div className="instance-sidebar error">{error}</div>;
  }
  
  return (
    <div className="instance-sidebar">
      <div className="sidebar-header">
        <h2>Instances</h2>
        <button 
          className="new-instance-btn"
          onClick={() => setIsCreating(true)}
        >
          + New
        </button>
      </div>
      
      {isCreating && (
        <div className="instance-form">
          <h3>Create New Instance</h3>
          <input
            type="text"
            placeholder="Instance name"
            value={newInstanceName}
            onChange={(e) => setNewInstanceName(e.target.value)}
          />
          <textarea
            placeholder="Description (optional)"
            value={newInstanceDescription}
            onChange={(e) => setNewInstanceDescription(e.target.value)}
          />
          <select
            value={selectedConfigId || ''}
            onChange={(e) => setSelectedConfigId(e.target.value)}
          >
            <option value="">Select a configuration</option>
            {flowConfigs.map(config => (
              <option key={config.id} value={config.id}>
                {config.name}
              </option>
            ))}
          </select>
          <div className="form-buttons">
            <button onClick={() => setIsCreating(false)}>Cancel</button>
            <button 
              onClick={handleCreateInstanceSubmit}
              disabled={!newInstanceName || !selectedConfigId}
            >
              Create
            </button>
          </div>
        </div>
      )}
      
      <div className="instances-list">
        {flowInstances.length === 0 ? (
          <div className="no-instances">
            No instances found. Create a new one to get started.
          </div>
        ) : (
          flowInstances.map(instance => (
            <div 
              key={instance.id}
              className={`instance-item ${selectedInstanceId === instance.id ? 'selected' : ''}`}
              onClick={() => onSelectInstance(instance.id)}
            >
              {isRenaming === instance.id ? (
                <div className="rename-form">
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <div className="rename-buttons">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        setIsRenaming(null);
                      }}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRenameInstance(instance.id);
                      }}
                    >
                      Save
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="instance-info">
                    <div className="instance-name">{instance.name}</div>
                    {instance.description && (
                      <div className="instance-description">{instance.description}</div>
                    )}
                    <div className="instance-meta">
                      <span className="instance-date">
                        {new Date(instance.last_message_at || instance.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                  <div className="instance-actions">
                    <button
                      className="rename-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        setIsRenaming(instance.id);
                        setNewName(instance.name);
                      }}
                    >
                      ✏️
                    </button>
                    <button
                      className="delete-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteInstance(instance.id);
                      }}
                    >
                      🗑️
                    </button>
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default InstanceSidebar;
