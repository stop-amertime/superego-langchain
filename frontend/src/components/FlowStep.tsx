import React, { useState } from 'react';
import { Message, MessageRole, SuperegoEvaluation, SuperegoDecision } from '../types';
import './FlowStep.css';
import ConstitutionSelector from './ConstitutionSelector';
import SyspromptSelector from './SyspromptSelector';
import { AppData } from '../App';

interface FlowStepProps {
  message: Message;
  superEvaluation?: SuperegoEvaluation;
  toolsUsed?: any[];
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  appData: AppData;
  onRerun?: (messageId: string, constitutionId: string, syspromptId: string) => void;
}

const FlowStep: React.FC<FlowStepProps> = ({ 
  message, 
  superEvaluation, 
  toolsUsed = [], 
  isExpanded = false,
  onToggleExpand,
  appData, 
  onRerun 
}) => {
  // State for rerun settings
  const [selectedConstitutionId, setSelectedConstitutionId] = useState<string>(
    message.constitutionId || superEvaluation?.constitutionId || 'default'
  );
  const [selectedSyspromptId, setSelectedSyspromptId] = useState<string>(
    message.syspromptId || 'assistant_default'
  );
  
  // State for showing thinking process
  const [showThinking, setShowThinking] = useState(false);
  
  // State for showing tool usage details
  const [showToolDetails, setShowToolDetails] = useState(false);
  
  // Format the timestamp to a readable format
  const formattedTime = new Date(message.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });

  // Get the sender name based on role
  const getSender = (role: MessageRole) => {
    switch (role) {
      case MessageRole.USER:
        return 'You';
      case MessageRole.ASSISTANT:
        return 'Assistant';
      case MessageRole.SUPEREGO:
        return 'Superego';
      case MessageRole.SYSTEM:
        return 'System';
      default:
        return 'Unknown';
    }
  };

  // Get badge content based on superego decision
  const getDecisionBadge = () => {
    const decision = message.decision || superEvaluation?.decision;
    
    if ((message.role !== MessageRole.SUPEREGO && !superEvaluation) || !decision) {
      return null;
    }

    const badgeClassMap: Record<string, string> = {
      'ALLOW': 'badge-success',
      'CAUTION': 'badge-warning',
      'BLOCK': 'badge-danger'
    };

    const badgeClass = badgeClassMap[decision] || 'badge-secondary';

    return (
      <span className={`decision-badge ${badgeClass}`}>
        {decision}
      </span>
    );
  };
  
  // Handle rerun with selected constitution and system prompt
  const handleRerun = () => {
    if (onRerun) {
      onRerun(message.id, selectedConstitutionId, selectedSyspromptId);
    }
  };

  return (
    <div className={`flow-step ${message.role}`}>
      <div className="step-connector">
        <div className="connector-line"></div>
        <div className="connector-dot"></div>
      </div>
      
      <div className="step-content">
        <div className="step-header">
          <div className="step-info">
            <span className="step-sender">{getSender(message.role)}</span>
            <span className="step-time">{formattedTime}</span>
            {getDecisionBadge()}
          </div>
          <div className="step-actions">
            <div className="action-buttons">
              {(message.thinking || superEvaluation?.thinking) && (
                <button
                  className="action-button"
                  onClick={() => setShowThinking(!showThinking)}
                  title={showThinking ? "Hide thinking process" : "Show thinking process"}
                >
                  {showThinking ? "🧠❌" : "🧠"}
                </button>
              )}
              {toolsUsed.length > 0 && (
                <button
                  className="action-button"
                  onClick={() => setShowToolDetails(!showToolDetails)}
                  title={showToolDetails ? "Hide tool details" : "Show tool details"}
                >
                  {showToolDetails ? "🔧❌" : "🔧"}
                </button>
              )}
              {(message.role === MessageRole.SUPEREGO || message.role === MessageRole.ASSISTANT) && (
                <button
                  className="action-button rerun-action"
                  onClick={handleRerun}
                  title="Rerun with current settings"
                >
                  🔄
                </button>
              )}
              {onToggleExpand && (
                <button
                  className="action-button"
                  onClick={onToggleExpand}
                  title={isExpanded ? "Collapse" : "Expand"}
                >
                  {isExpanded ? "▲" : "▼"}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Metadata section (constitution, sysprompt) */}
        {(message.role === MessageRole.SUPEREGO || superEvaluation) && appData && (
          <div className="step-metadata">
            <span className="metadata-label">Constitution:</span> 
            <ConstitutionSelector
              onSelectConstitution={setSelectedConstitutionId}
              selectedConstitutionId={selectedConstitutionId}
              constitutions={appData?.constitutions || []}
              isLoading={appData?.constitutionsLoading || false}
              error={appData?.constitutionsError || null}
            />
          </div>
        )}
        
        {message.role === MessageRole.ASSISTANT && appData && (
          <div className="step-metadata">
            <span className="metadata-label">System Prompt:</span>
            <SyspromptSelector
              onSelectSysprompt={setSelectedSyspromptId}
              selectedSyspromptId={selectedSyspromptId}
              sysprompts={appData?.sysprompts || []}
              isLoading={appData?.syspromptsLoading || false}
              error={appData?.syspromptsError || null}
            />
          </div>
        )}
        
        {/* Main content */}
        <div className="step-message">
          {message.content.split('\n').map((line, i, arr) => (
            <React.Fragment key={i}>
              {line}
              {i < arr.length - 1 && <br />}
            </React.Fragment>
          ))}
        </div>

        {/* Thinking process */}
        {((message.thinking || superEvaluation?.thinking) && showThinking) && (
          <div className="step-thinking">
            <h4>Thinking Process</h4>
            <pre>{message.thinking || superEvaluation?.thinking}</pre>
          </div>
        )}
        
        {/* Tool usage details */}
        {toolsUsed.length > 0 && showToolDetails && (
          <div className="step-tools">
            <h4>Tools Used</h4>
            {toolsUsed.map((tool, index) => (
              <div key={index} className="tool-usage">
                <div className="tool-header">
                  <span className="tool-name">{tool.name}</span>
                </div>
                <div className="tool-arguments">
                  <strong>Arguments:</strong>
                  <pre>{JSON.stringify(tool.arguments, null, 2)}</pre>
                </div>
                <div className="tool-output">
                  <strong>Output:</strong>
                  <pre>{typeof tool.output === 'string' ? tool.output : JSON.stringify(tool.output, null, 2)}</pre>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default FlowStep;
