import React, { useState, useEffect } from 'react';
import { getWebSocketClient } from '../api/websocketClient';
import { useFlowConfigs } from '../api/queryHooks';
import { FlowConfig, FlowInstance, ParallelFlowResult, Message, MessageRole } from '../types';
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
  // Fetch flow configs using React Query
  const { 
    data: flowConfigs = [], 
    isLoading: configsLoading, 
    error: configsError 
  } = useFlowConfigs();
  
  const [selectedFlowIds, setSelectedFlowIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ParallelFlowResult[]>([]);
  const [isTokenStreaming, setIsTokenStreaming] = useState(false);
  const [streamingTokens, setStreamingTokens] = useState<{[flowId: string]: string}>({});

  // Set default selected flows when configs are loaded
  useEffect(() => {
    if (flowConfigs.length > 0 && !configsLoading && selectedFlowIds.length === 0) {
      if (flowConfigs.length >= 2) {
        setSelectedFlowIds([flowConfigs[0].id, flowConfigs[1].id]);
      } else if (flowConfigs.length === 1) {
        setSelectedFlowIds([flowConfigs[0].id]);
      }
    }
  }, [flowConfigs, configsLoading, selectedFlowIds]);

  // Setup WebSocket listeners for streaming tokens and results
  useEffect(() => {
    const wsClient = getWebSocketClient();
    
    const onMessage = (message: any) => {
      if (message.type === 'parallel_flows_result') {
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
    
    return () => {
      // Clean up by removing our specific message handler
      wsClient.updateCallbacks({ onMessage: undefined });
    };
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
                    <div className="message-bubble superego">
                      <div className="message-header">
                        <div className="message-info">
                          <span className="message-sender">Superego</span>
                          <span className="message-time">{new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}</span>
                          {flowResult.superego_evaluation.decision && (
                            <span className={`decision-badge badge-${flowResult.superego_evaluation.decision === 'ALLOW' ? 'success' : 
                                             flowResult.superego_evaluation.decision === 'CAUTION' ? 'warning' : 'danger'}`}>
                              {flowResult.superego_evaluation.decision}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="message-content">
                        {flowResult.superego_evaluation.reason && flowResult.superego_evaluation.reason.split('\n').map((line, i, arr) => (
                          <React.Fragment key={i}>
                            {line}
                            {i < arr.length - 1 && <br />}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Show streaming tokens if available */}
                  {isTokenStreaming && streamingTokens[flowId] && (
                    <div className="message-bubble assistant streaming">
                      <div className="message-content">{streamingTokens[flowId]}</div>
                    </div>
                  )}
                  
                  {/* Assistant message */}
                  {flowResult?.assistant_message && (
                    <MessageBubble
                      message={flowResult.assistant_message}
                      appData={appData}
                      onRerun={() => {}}
                    />
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
