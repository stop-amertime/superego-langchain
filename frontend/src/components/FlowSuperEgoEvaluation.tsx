import React, { useState, useRef, useEffect } from 'react';
import { SuperegoEvaluation, SuperegoDecision } from '../types';
import './FlowStep.css';
import ConstitutionSelector from './ConstitutionSelector';
import { getWebSocketClient } from '../api/websocketClient';
import { useConstitutions } from '../api/queryHooks';

interface FlowSuperEgoEvaluationProps {
  evaluation: SuperegoEvaluation;
  flowInstanceId?: string;
}

const FlowSuperEgoEvaluation: React.FC<FlowSuperEgoEvaluationProps> = ({ evaluation, flowInstanceId }) => {
  // Fetch constitutions using React Query
  const { 
    data: constitutions = [], 
    isLoading: constitutionsLoading, 
    error: constitutionsError 
  } = useConstitutions();
  
  // Determine if the evaluation is still in progress
  const isEvaluating = evaluation.status === 'started' || evaluation.status === 'thinking';
  
  // Toggle thinking visibility if available
  const [showThinking, setShowThinking] = useState(false);
  
  // Toggle debug info visibility
  const [showDebug, setShowDebug] = useState(false);
  
  // State for constitution selection with a ref to track initial render
  const [selectedConstitutionId, setSelectedConstitutionId] = useState(
    evaluation.constitutionId || 'default'
  );
  const initialRenderRef = useRef(true);
  const prevConstitutionIdRef = useRef(evaluation.constitutionId);
  
  // Flag to track if the change was triggered by user vs. prop update
  const [userTriggeredChange, setUserTriggeredChange] = useState(false);
  
  // Update selected constitution ID when it changes from parent
  useEffect(() => {
    if (evaluation.constitutionId && evaluation.constitutionId !== selectedConstitutionId && !userTriggeredChange) {
      setSelectedConstitutionId(evaluation.constitutionId);
    }
    
    // Reset the user triggered flag after the effect runs
    if (userTriggeredChange) {
      setUserTriggeredChange(false);
    }
    
    prevConstitutionIdRef.current = evaluation.constitutionId;
  }, [evaluation.constitutionId, selectedConstitutionId, userTriggeredChange]);
  
  // State for showing the rerun button
  const [showRerunButton, setShowRerunButton] = useState(false);
  
  // Handle constitution change - only update the selected ID, don't trigger rerun
  const handleConstitutionChange = (constitutionId: string) => {
    console.log(`Constitution change requested: ${constitutionId} (current: ${selectedConstitutionId})`);
    
    // Only proceed if the constitution actually changed
    if (constitutionId !== selectedConstitutionId) {
      // Set the flag to indicate this was a user-triggered change
      setUserTriggeredChange(true);
      
      // Update the selected constitution ID
      setSelectedConstitutionId(constitutionId);
      
      // Show the rerun button if we have an evaluation ID and the status is completed
      if (evaluation.id && evaluation.status === 'completed') {
        setShowRerunButton(true);
      }
    }
    
    // Mark that initial render is complete
    initialRenderRef.current = false;
  };
  
  // Handle manual rerun button click
  const handleRerunClick = () => {
    if (evaluation.id && evaluation.status === 'completed') {
      console.log('Manually triggered rerun with constitution:', selectedConstitutionId);
      
      if (!flowInstanceId) {
        console.error('No flow instance ID available for rerunning evaluation');
        return;
      }
      
      // Send command to rerun flow from this point with checkpoint ID
      const wsClient = getWebSocketClient();
      wsClient.sendCommand('rerun_from_constitution', {
        constitution_id: selectedConstitutionId,
        checkpoint_id: evaluation.id  // Use the evaluation ID as the checkpoint ID
      }, flowInstanceId);
      
      // Hide the rerun button after clicking
      setShowRerunButton(false);
    }
  };
  
  // Get the appropriate status class based on the decision
  const getStatusClass = () => {
    if (evaluation.status === 'thinking') return 'status-thinking';
    if (isEvaluating) return 'status-analyzing';
    
    switch (evaluation.decision) {
      case SuperegoDecision.ALLOW:
        return 'status-allow';
      case SuperegoDecision.CAUTION:
        return 'status-caution';
      case SuperegoDecision.BLOCK:
        return 'status-block';
      default:
        return '';
    }
  };

  // Get the appropriate status text
  const getStatusText = () => {
    if (evaluation.status === 'thinking') {
      return 'Step 1: Analyzing your message...';
    } else if (isEvaluating) {
      return 'Step 1: Evaluating content...';
    } else if (evaluation.decision) {
      return `Step 1: Content evaluation - ${evaluation.decision}`;
    } else {
      return 'Step 1: Content evaluation';
    }
  };

  return (
    <div className="flow-step superego">
      <div className="step-connector">
        <div className="connector-line"></div>
        <div className="connector-dot"></div>
      </div>
      
      <div className={`step-content ${getStatusClass()}`}>
        <div className="step-header">
          <div className="step-info">
            <span className="step-sender">{getStatusText()}</span>
            <span className="step-time">{new Date().toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })}</span>
            {evaluation.decision && (
              <span className={`decision-badge ${
                evaluation.decision === SuperegoDecision.ALLOW ? 'badge-success' :
                evaluation.decision === SuperegoDecision.CAUTION ? 'badge-warning' :
                evaluation.decision === SuperegoDecision.BLOCK ? 'badge-danger' : 'badge-secondary'
              }`}>
                {evaluation.decision}
              </span>
            )}
          </div>
          
          <div className="step-actions">
            <div className="action-buttons">
              {evaluation.thinking && !isEvaluating && (
                <button
                  className="action-button"
                  onClick={() => setShowThinking(!showThinking)}
                  title={showThinking ? "Hide thinking process" : "Show thinking process"}
                >
                  {showThinking ? "🧠❌" : "🧠"}
                </button>
              )}
              <button
                className="action-button"
                onClick={() => setShowDebug(!showDebug)}
                title={showDebug ? "Hide API data" : "Show API data"}
              >
                {showDebug ? "🔍❌" : "🔍"}
              </button>
            </div>
          </div>
        </div>
        
        {/* Constitution Selector */}
        {!isEvaluating && evaluation.status === 'completed' && (
          <div className="step-metadata">
            <span className="metadata-label">Constitution:</span>
            <ConstitutionSelector
              onSelectConstitution={handleConstitutionChange}
              selectedConstitutionId={selectedConstitutionId}
              constitutions={constitutions}
              isLoading={constitutionsLoading}
              error={constitutionsError ? String(constitutionsError) : null}
            />
            {showRerunButton && (
              <button 
                className="rerun-button"
                onClick={handleRerunClick}
              >
                Rerun with selected constitution
              </button>
            )}
          </div>
        )}
        
        {/* Show streaming thinking content if available */}
        {evaluation.status === 'thinking' && evaluation.thinking && (
          <div className="step-thinking streaming">
            <h4>AI Analysis in progress...</h4>
            <pre>{evaluation.thinking}</pre>
            <span className="cursor-blink">|</span>
          </div>
        )}
        
        {/* Show completed evaluation reason */}
        {!isEvaluating && evaluation.reason && (
          <div className="step-message">
            {evaluation.reason.split('\n').map((line, i, arr) => (
              <React.Fragment key={i}>
                {line}
                {i < arr.length - 1 && <br />}
              </React.Fragment>
            ))}
          </div>
        )}
        
        {/* Show completed thinking when toggled */}
        {evaluation.thinking && showThinking && !isEvaluating && (
          <div className="step-thinking">
            <h4>Analysis Details</h4>
            <pre>{evaluation.thinking}</pre>
          </div>
        )}
        
        {/* Show debug information when toggled */}
        {showDebug && (
          <div className="step-debug">
            <h4>API Call Details</h4>
            <pre>
              {JSON.stringify(
                evaluation,
                null,
                2
              )}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default FlowSuperEgoEvaluation;
