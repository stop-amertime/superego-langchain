// API Response Types
export interface FlowDefinition {
  id: string;
  name: string;
  description: string;
}

export interface FlowDetail {
  name: string;
  description: string;
  graph: {
    start: string;
    nodes: Record<string, FlowNode>;
  };
}

export interface FlowNode {
  type: 'superego' | 'inner_agent';
  agent_id: string;
  max_iterations?: number;
  constitution?: string;
  system_prompt?: string;
  tools?: string[];
  transitions: Record<string, string | null>;
}

// Flow Execution Types
export interface FlowStep {
  step_id: string;
  agent_id: string;
  timestamp: string;
  role: 'user' | 'assistant' | 'system';
  input: string | null;
  
  // Superego-specific fields
  constitution?: string;
  decision?: 'BLOCK' | 'ACCEPT' | 'CAUTION' | 'NEEDS_CLARIFICATION';
  
  // Inner agent-specific fields
  system_prompt?: string;
  tool_usage?: {
    tool_name: string;
    input: any;
    output: any;
  };
  
  // Common fields
  response: string;
  next_agent: string | null;
}

export interface FlowInstance {
  id: string;
  name: string;
  timestamp: string;
  flow_definition_id: string;
}

// UI State Types
export interface UIState {
  isModalOpen: boolean;
  expandedCards: Set<string>;
  isLoading: boolean;
  error: string | null;
}

// Streaming Types
export interface PartialOutput {
  partial_output: string;
  complete: boolean;
  flow_step?: FlowStep;
}

export interface StreamingEvent {
  type: 'partial_output' | 'complete_step' | 'error';
  data: any;
}

// Tool Confirmation Types
export interface ToolConfirmationSettings {
  confirm_all: boolean;
  exempted_tools: string[];
}

export interface ToolConfirmation {
  tool_execution_id: string;
  confirmed: boolean;
}

// Command Types
export type SuperegoCommand = 'BLOCK' | 'ACCEPT' | 'CAUTION' | 'NEEDS_CLARIFICATION';
export type InnerAgentCommand = 'COMPLETE' | 'NEEDS_TOOL' | 'NEEDS_RESEARCH' | 'NEEDS_REVIEW' | 'ERROR';
