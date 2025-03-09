import React from 'react';
import './FlowProcessingIndicator.css';

interface FlowProcessingIndicatorProps {
  processingStep: number;
}

const FlowProcessingIndicator: React.FC<FlowProcessingIndicatorProps> = ({ processingStep }) => {
  return (
    <div className="flow-step system">
      <div className="step-connector">
        <div className="connector-line"></div>
        <div className="connector-dot"></div>
      </div>
      
      <div className="step-content">
        <div className="flow-processing-steps">
          <div className={`processing-step ${processingStep === 0 ? 'active' : processingStep > 0 ? 'completed' : ''}`}>
            <div className={`step-number ${processingStep === 0 ? 'active' : processingStep > 0 ? 'completed' : ''}`}>
              {processingStep > 0 ? '✓' : '1'}
            </div>
            <div className="step-description">
              Preparing message processing
            </div>
            {processingStep === 0 && <div className="loading-spinner"></div>}
          </div>
          
          <div className={`processing-step ${processingStep === 1 ? 'active' : processingStep > 1 ? 'completed' : ''}`}>
            <div className={`step-number ${processingStep === 1 ? 'active' : processingStep > 1 ? 'completed' : ''}`}>
              {processingStep > 1 ? '✓' : '2'}
            </div>
            <div className="step-description">
              Content evaluation
            </div>
            {processingStep === 1 && <div className="loading-spinner"></div>}
          </div>
          
          <div className={`processing-step ${processingStep === 2 ? 'active' : processingStep > 2 ? 'completed' : ''}`}>
            <div className={`step-number ${processingStep === 2 ? 'active' : processingStep > 2 ? 'completed' : ''}`}>
              {processingStep > 2 ? '✓' : '3'}
            </div>
            <div className="step-description">
              Evaluation complete, waiting for response
            </div>
            {processingStep === 2 && <div className="loading-spinner"></div>}
          </div>
          
          <div className={`processing-step ${processingStep === 3 ? 'active' : ''}`}>
            <div className={`step-number ${processingStep === 3 ? 'active' : ''}`}>
              4
            </div>
            <div className="step-description">
              Generating response
            </div>
            {processingStep === 3 && <div className="loading-spinner"></div>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlowProcessingIndicator;
