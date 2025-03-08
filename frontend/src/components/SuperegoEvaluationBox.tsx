import React, { useState, useRef, useEffect } from 'react';
import { SuperegoEvaluation, SuperegoDecision, Constitution } from '../types';
import './SuperegoEvaluationBox.css';
import ConstitutionSelector from './ConstitutionSelector';
import { getWebSocketClient } from '../api/websocketClient';
import { useConstitutions } from '../api/queryHooks';

interface SuperegoEvaluationBoxProps {
  evaluation: SuperegoEvaluation;
}

const SuperegoEvaluationBox: React.FC<SuperegoEvaluationBoxProps> = ({ evaluation }) => {
  // Fetch constitutions using React Query
  const { 
    data: constitutions = [], 
    isLoading: constitutionsLoading, 
    error: constitutionsError 
  } = useConstitutions();
  // Determine if the evaluation is still in progress
  const isEvaluating = evaluation.status === 'started' || evaluation.status === 'thinking';
  
  // Toggle thinking visibility if available
  const [showThinking, setShowThinking] = React.useState(false);
  
  // Toggle debug info visibility
  const [showDebug, setShowDebug] = React.useState(false);
  
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
      // Send message to rerun flow from this point with checkpoint ID
      const wsClient = getWebSocketClient();
      wsClient.sendMessage(JSON.stringify({
        type: 'rerun_from_constitution',
        constitution_id: selectedConstitutionId,
        checkpoint_id: evaluation.id  // Use the evaluation ID as the checkpoint ID
      }));
      
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
    <div className={`superego-evaluation ${getStatusClass()}`}>
      <div className="evaluation-header">
        <div className="evaluation-title">
          <h3>{getStatusText()}</h3>
          {isEvaluating && (
            <div className="evaluation-spinner"></div>
          )}
        </div>
        
        <div className="evaluation-actions">
          <div className="menu-dropdown">
            <button className="menu-button">⋮</button>
            <div className="dropdown-content">
              {evaluation.thinking && !isEvaluating && (
                <button
                  className="dropdown-item"
                  onClick={() => setShowThinking(!showThinking)}
                >
                  {showThinking ? 'Hide Details' : 'Show Details'}
                </button>
              )}
              <button
                className="dropdown-item"
                onClick={() => setShowDebug(!showDebug)}
              >
                {showDebug ? 'Hide API Data' : 'Show API Data'}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Add Constitution Selector with Rerun Button */}
      {!isEvaluating && evaluation.status === 'completed' && (
        <div className="constitution-selector-container">
          <div className="constitution-label">Constitution:</div>
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
        <div className="evaluation-thinking streaming">
          <h4>AI Analysis in progress...</h4>
          <pre>{evaluation.thinking}</pre>
          <span className="cursor-blink">|</span>
        </div>
      )}
      
      {/* Show completed evaluation reason */}
      {!isEvaluating && evaluation.reason && (
        <div className="evaluation-content">
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
        <div className="evaluation-thinking">
          <h4>Analysis Details</h4>
          <pre>{evaluation.thinking}</pre>
        </div>
      )}
      
      {/* Show debug information when toggled */}
      {showDebug && (
        <div className="evaluation-debug">
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
  );
};

export default SuperegoEvaluationBox;
