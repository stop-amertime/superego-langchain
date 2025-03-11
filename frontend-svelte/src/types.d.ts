// Global types for SuperEgo LangGraph frontend

// Message Models
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'superego' | 'system';
  content: string;
  timestamp: string;
  decision?: Decision;
  constitutionId?: string;
  thinking?: string;
  thinkingTime?: string;
  isStreaming?: boolean;
  withoutSuperego?: string;
  node_id?: string;  // Added to track which node generated the message
}

type Decision = 'ALLOW' | 'BLOCK' | 'CAUTION' | 'ANALYZING' | 'ERROR';

interface SuperegoEvaluation {
  decision: Decision;
  reason: string;
  thinking?: string;
  timestamp?: string;
  constitutionId?: string;
  status?: string;
  id?: string;
}

// Flow Models
interface NodeConfig {
  type: string;
  config: Record<string, any>;
}

interface EdgeConfig {
  from_node: string;
  to_node: string;
  condition?: string;
}

interface FlowDefinition {
  id: string;
  name: string;
  description?: string;
  nodes: Record<string, NodeConfig>;
  edges: EdgeConfig[];
  created_at: string;
  updated_at: string;
}

interface FlowInstance {
  id: string;
  flow_definition_id: string;
  current_node?: string;
  status: 'created' | 'running' | 'paused' | 'completed' | 'error';
  name: string;
  description?: string;
  messages: Message[];
  history: NodeExecution[];
  agent_states: Record<string, Record<string, any>>;
  tool_usages: ToolUsage[];
  parameters: Record<string, Record<string, any>>;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
}

interface NodeExecution {
  node_id: string;
  input: any;
  output: any;
  timestamp: string;
  status: 'success' | 'error' | 'running';
}

interface ToolUsage {
  tool_name: string;
  input_data: Record<string, any>;
  output: any;
  timestamp: string;
}

// Constitution Model
interface Constitution {
  id: string;
  name: string;
  content: string;
}

// WebSocket Message Types
interface WebSocketMessage<T = any> {
  type: string;
  content?: T;
  payload?: T;
  timestamp: string;
  flow_instance_id?: string;
}

interface UserMessageInput {
  message: string;
}

interface FlowOperation {
  operation: string;
  user_input?: string;
  parameters?: Record<string, any>;
}
