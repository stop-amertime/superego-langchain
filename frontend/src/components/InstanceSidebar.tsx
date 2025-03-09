import React, { useState, useEffect } from 'react';
import { 
  useFlowInstances, 
  useFlowConfigs, 
  useCreateFlowInstance, 
  useUpdateFlowInstance, 
  useDeleteFlowInstance 
} from '../api/queryHooks';
import { FlowInstance, FlowConfig, FlowTemplate } from '../types';
import './InstanceSidebar.css';

interface InstanceSidebarProps {
  selectedInstanceId: string | null;
  onSelectInstance: (instanceId: string) => void;
  onCreateInstance: (instanceData: {name: string, flow_config_id: string, description?: string}) => void;
  onToggleSidebar: () => void;
  flowConfigs: FlowConfig[];
  flowInstances: FlowInstance[];
  loading: boolean;
}

const InstanceSidebar: React.FC<InstanceSidebarProps> = ({
  selectedInstanceId,
  onSelectInstance,
  onCreateInstance,
  onToggleSidebar,
  flowConfigs,
  flowInstances,
  loading
}) => {
  // UI state
  const [isCreating, setIsCreating] = useState(false);
  const [newInstanceName, setNewInstanceName] = useState('');
  const [newInstanceDescription, setNewInstanceDescription] = useState('');
  const [selectedConfigId, setSelectedConfigId] = useState<string | null>(null);
  const [isRenaming, setIsRenaming] = useState<string | null>(null);
  const [newName, setNewName] = useState('');
  const [showConfigs, setShowConfigs] = useState(false);
  
  // Use React Query hooks for data fetching and mutations
  const { data: fetchedInstances, isLoading: instancesLoading } = useFlowInstances();
  const { data: fetchedConfigs, isLoading: configsLoading } = useFlowConfigs();
  const createInstanceMutation = useCreateFlowInstance();
  const updateInstanceMutation = useUpdateFlowInstance(isRenaming || '');
  const deleteInstanceMutation = useDeleteFlowInstance();
  
  // Use React Query data exclusively
  const instances = fetchedInstances || [];
  const configs = fetchedConfigs || [];
  const isDataLoading = instancesLoading || configsLoading;
  
  // Handle create instance form submission
  const handleCreateInstanceSubmit = () => {
    if (!newInstanceName || !selectedConfigId) return;
    
    // Create the instance data object
    const newInstanceData = {
      name: newInstanceName,
      flow_config_id: selectedConfigId,
      description: newInstanceDescription || undefined
    };
    
    // Use the mutation to create the instance
    createInstanceMutation.mutate(newInstanceData as any, {
      onSuccess: (data) => {
        // Call the parent method to update UI
        onCreateInstance(newInstanceData);
        
        // Reset form
        setNewInstanceName('');
        setNewInstanceDescription('');
        setSelectedConfigId(null);
        setIsCreating(false);
      }
    });
  };
  
  // Handle rename instance via API
  const handleRenameInstance = (instanceId: string) => {
    if (!newName) return;
    
    updateInstanceMutation.mutate({
      name: newName
    }, {
      onSuccess: () => {
        // Reset form
        setNewName('');
        setIsRenaming(null);
      }
    });
  };
  
  // Handle delete instance via API
  const handleDeleteInstance = (instanceId: string) => {
    if (!window.confirm('Are you sure you want to delete this instance?')) return;
    
    deleteInstanceMutation.mutate(instanceId);
  };
  
  // Select an instance (renamed from handleStartFlow for clarity)
  const handleSelectFlow = (instanceId: string) => {
    // Select the instance in the parent component
    onSelectInstance(instanceId);
  };
  
  if (isDataLoading) {
    return <div className="instance-sidebar loading">Loading instances...</div>;
  }
  
  return (
    <div className="instance-sidebar">
      <div className="sidebar-header">
        <h2>Instances</h2>
        <div className="sidebar-actions">
          <button 
            className="new-instance-btn"
            onClick={() => setIsCreating(true)}
            title="Create new instance"
          >
            + New
          </button>
          <button 
            className="hide-sidebar-btn"
            onClick={onToggleSidebar}
            title="Hide sidebar"
          >
            ◀
          </button>
        </div>
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
            {configs.map(config => (
              <option key={config.id} value={config.id}>
                {config.name} {config.superego_enabled ? '(with Superego)' : '(no Superego)'}
              </option>
            ))}
          </select>
          <div className="form-buttons">
            <button onClick={() => setIsCreating(false)}>Cancel</button>
            <button 
              onClick={handleCreateInstanceSubmit}
              disabled={!newInstanceName || !selectedConfigId || createInstanceMutation.isPending}
            >
              {createInstanceMutation.isPending ? 'Creating...' : 'Create'}
            </button>
          </div>
        </div>
      )}
      
      <div className="instances-list">
        {instances.length === 0 ? (
          <div className="no-instances">
            No instances found. Create a new one to get started.
          </div>
        ) : (
          instances.map(instance => {
            // Find the config for this instance to show more details
            const config = configs.find(c => c.id === instance.flow_config_id);
            
            return (
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
                        disabled={updateInstanceMutation.isPending}
                      >
                        {updateInstanceMutation.isPending ? 'Saving...' : 'Save'}
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
                      {config && (
                        <div className="instance-config">
                          <span className="config-badge" title={`Constitution: ${config.constitution_id}`}>
                            {config.superego_enabled ? '🛡️ Superego' : '🔓 No Superego'}
                          </span>
                        </div>
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
                        title="Rename instance"
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
                        title="Delete instance"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteInstance(instance.id);
                        }}
                        disabled={deleteInstanceMutation.isPending}
                      >
                        🗑️
                      </button>
                    </div>
                  </>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default InstanceSidebar;
