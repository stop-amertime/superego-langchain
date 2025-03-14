// API Response Types
interface FlowDefinition {
  id: string;
  name: string;
  description: string;
}

interface FlowDetail {
  name: string;
  description: string;
  graph: {
    start: string;
    nodes: Record<string, FlowNode>;
  };
}

interface FlowNode {
  type: 'superego' | 'inner_agent';
  agent_id: string;
  max_iterations?: number;
  constitution?: string;
  system_prompt?: string;
  tools?: string[];
  transitions: Record<string, string | null>;
}

// Flow Execution Types
interface FlowStep {
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

interface FlowInstance {
  id: string;
  name?: string;
  timestamp?: string;
  flow_definition_id?: string;
  status?: 'active' | 'completed' | 'error';
  updated_at?: string;
  flow_name?: string;
  flow_id?: string;
  created_at?: string;
  last_message?: string;
}

// UI State Types
interface UIState {
  isModalOpen: boolean;
  expandedCards: Set<string>;
  isLoading: boolean;
  error: string | null;
}

// Streaming Types
interface PartialOutput {
  partial_output: string;
  complete: boolean;
  flow_step?: FlowStep;
}

interface StreamingEvent {
  type: 'partial_output' | 'complete_step' | 'error';
  data: any;
}

// Stream Event Types
interface PartialOutputEvent {
  type: 'partial_output';
  data: {
    partial_output: string;
    complete?: boolean;
  };
}

interface CompleteStepEvent {
  type: 'complete_step';
  data: FlowStep;
}

interface ErrorEvent {
  type: 'error';
  data: {
    message: string;
    code?: string;
  };
}

// Tool Confirmation Types
interface ToolConfirmationSettings {
  confirm_all: boolean;
  exempted_tools: string[];
}

interface ToolConfirmation {
  tool_execution_id: string;
  confirmed: boolean;
}

interface ToolConfirmationResponse {
  status: string;
  result?: {
    tool_name: string;
    input: any;
    output: any;
  };
  message: string;
}

// Flow Execution Request
interface FlowExecuteRequest {
  flow_id: string;
  input: string;
  conversation_id?: string;
  metadata?: Record<string, any>;
}

// Health Check Response
interface HealthResponse {
  status: string;
  version: string;
}

// Reconnection State for Stream Services
interface ReconnectionState {
  attempt: number;
  maxAttempts: number;
  backoffMs: number;
  timer: number | null;
}

// Command Types
type SuperegoCommand = 'BLOCK' | 'ACCEPT' | 'CAUTION' | 'NEEDS_CLARIFICATION';
type InnerAgentCommand = 'COMPLETE' | 'NEEDS_TOOL' | 'NEEDS_RESEARCH' | 'NEEDS_REVIEW' | 'ERROR';
