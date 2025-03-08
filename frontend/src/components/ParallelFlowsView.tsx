import React, { useState, useEffect } from 'react';
import { getWebSocketClient } from '../api/websocketClient';
import { FlowConfig, FlowInstance, ParallelFlowResult, Message } from '../types';
import MessageBubble from './MessageBubble';
import SuperegoEvaluationBox from './SuperegoEvaluationBox';
import './ParallelFlowsView.css';

interface ParallelFlowsViewProps {
  userInput: string;
  conversationId: string | null;
  appData: any;
}

const ParallelFlowsView: React.FC<ParallelFlowsViewProps> = ({
  userInput,
  conversationId,
  appData
}) => {
  const [flowConfigs, setFlowConfigs] = useState<FlowConfig[]>([]);
  const [selectedFlowIds, setSelectedFlowIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ParallelFlowResult[]>([]);
  const [isTokenStreaming, setIsTokenStreaming] = useState(false);
  const [streamingTokens, setStreamingTokens] = useState<{[flowId: string]: string}>({});

  // Load flow configs on mount
  useEffect(() => {
    const loadFlowConfigs = async () => {
      setLoading(true);
      setError(null);
      
      const wsClient = getWebSocketClient();
      
      const onMessage = (message: any) => {
        if (message.type === 'flows_response') {
          if (message.content && message.content.length > 0) {
            if (!('conversation_id' in message.content[0])) {
              setFlowConfigs(message.content);
              
              // Default select the first two configs if available
              if (message.content.length >= 2 && selectedFlowIds.length === 0) {
                setSelectedFlowIds([message.content[0].id, message.content[1].id]);
              } else if (message.content.length === 1 && selectedFlowIds.length === 0) {
                setSelectedFlowIds([message.content[0].id]);
              }
            }
          }
        } else if (message.type === 'parallel_flows_result') {
          setResults(message.content);
          setLoading(false);
          setIsTokenStreaming(false);
          setStreamingTokens({});
        } else if (message.type === 'assistant_token') {
          const flowId = message.content.flow_config_id;
          
          if (flowId) {
            setIsTokenStreaming(true);
            setStreamingTokens(prev => ({
              ...prev,
              [flowId]: (prev[flowId] || '') + message.content.token
            }));
          }
        }
      };
      
      // Update callbacks
      wsClient.updateCallbacks({ onMessage });
      
      // Request data
      wsClient.sendCommand('get_flow_configs');
      
      setLoading(false);
    };
    
    loadFlowConfigs();
  }, []);

  const handleFlowSelectionChange = (flowId: string) => {
    if (selectedFlowIds.includes(flowId)) {
      setSelectedFlowIds(selectedFlowIds.filter(id => id !== flowId));
    } else {
      setSelectedFlowIds([...selectedFlowIds, flowId]);
    }
  };

  const handleRunParallelFlows = () => {
    if (selectedFlowIds.length === 0 || !userInput.trim()) return;
    
    setLoading(true);
    setResults([]);
    setError(null);
    
    const wsClient = getWebSocketClient();
    wsClient.sendCommand('run_parallel_flows', {
      flow_config_ids: selectedFlowIds,
      content: userInput,
      conversation_id: conversationId
    });
  };

  const renderResults = () => {
    if (loading && !isTokenStreaming) {
      return <div className="parallel-loading">Running flows...</div>;
    }
    
    if (error) {
      return <div className="parallel-error">{error}</div>;
    }
    
    if (results.length === 0 && !isTokenStreaming) {
      return null;
    }
    
    return (
      <div className="parallel-results">
        <div className="flow-grid" style={{ gridTemplateColumns: `repeat(${Math.min(selectedFlowIds.length, 3)}, 1fr)` }}>
          {selectedFlowIds.map(flowId => {
            const flowConfig = flowConfigs.find(config => config.id === flowId);
            const flowResult = results.find(result => result.flow_config_id === flowId);
            
            return (
              <div key={flowId} className="flow-result-column">
                <div className="flow-result-header">
                  <h3>{flowConfig?.name || 'Unknown Flow'}</h3>
                  <div className="flow-result-meta">
                    {flowConfig?.superego_enabled ? (
                      <span className="superego-enabled">Superego Enabled</span>
                    ) : (
                      <span className="superego-disabled">Superego Disabled</span>
                    )}
                  </div>
                </div>
                
                <div className="flow-result-content">
                  {/* User message */}
                  <div className="message-bubble user">
                    <div className="message-content">{userInput}</div>
                  </div>
                  
                  {/* Superego evaluation (if available) */}
                  {flowResult?.superego_evaluation && (
                    <SuperegoEvaluationBox 
                      evaluation={{
                        ...flowResult.superego_evaluation,
                        status: 'completed'
                      }} 
                    />
                  )}
                  
                  {/* Show streaming tokens if available */}
                  {isTokenStreaming && streamingTokens[flowId] && (
                    <div className="message-bubble assistant streaming">
                      <div className="message-content">{streamingTokens[flowId]}</div>
                    </div>
                  )}
                  
                  {/* Assistant message */}
                  {flowResult?.assistant_message && (
                    <div className="message-bubble assistant">
                      <div className="message-content">{flowResult.assistant_message.content}</div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="parallel-flows-view">
      <div className="flow-selector">
        <h3>Compare Flows</h3>
        <div className="flow-checkboxes">
          {flowConfigs.map(config => (
            <div key={config.id} className="flow-checkbox">
              <input
                type="checkbox"
                id={`flow-${config.id}`}
                checked={selectedFlowIds.includes(config.id)}
                onChange={() => handleFlowSelectionChange(config.id)}
              />
              <label htmlFor={`flow-${config.id}`}>
                {config.name}
                {config.superego_enabled ? ' (with Superego)' : ' (without Superego)'}
              </label>
            </div>
          ))}
        </div>
        <button 
          className="run-flows-btn"
          onClick={handleRunParallelFlows}
          disabled={selectedFlowIds.length === 0 || !userInput.trim() || loading}
        >
          {loading ? 'Running...' : 'Compare Selected Flows'}
        </button>
      </div>
      
      {renderResults()}
    </div>
  );
};

export default ParallelFlowsView;
