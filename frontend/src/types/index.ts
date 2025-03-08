// Basic data types
export interface Constitution {
  id: string;
  name: string;
  content: string;
}

export interface Sysprompt {
  id: string;
  name: string;
  content: string;
}

// Message roles
export enum MessageRole {
  USER = "user",
  ASSISTANT = "assistant",
  SUPEREGO = "superego",
  SYSTEM = "system"
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  decision?: string;
  constitutionId?: string;
  syspromptId?: string;
  thinking?: string;
  thinkingTime?: string;
  withoutSuperego?: string;
}

export enum SuperegoDecision {
  ALLOW = "ALLOW",
  BLOCK = "BLOCK",
  CAUTION = "CAUTION",
  ANALYZING = "ANALYZING",
  ERROR = "ERROR"
}

export interface SuperegoEvaluation {
  status: "started" | "completed" | "thinking";
  decision?: SuperegoDecision;
  reason?: string;
  thinking?: string;
  id?: string;
  message?: string;
  constitutionId?: string;
  checkpoint_id?: string;
}

export enum WebSocketMessageType {
  USER_MESSAGE = "user_message",
  SUPEREGO_EVALUATION = "superego_evaluation",
  ASSISTANT_MESSAGE = "assistant_message",
  ASSISTANT_TOKEN = "assistant_token",
  TOOL_USAGE = "tool_usage",
  SUPEREGO_INTERVENTION = "superego_intervention",
  ERROR = "error",
  SYSTEM_MESSAGE = "system_message",
  CONSTITUTIONS_RESPONSE = "constitutions_response",
  RERUN_FROM_CONSTITUTION = "rerun_from_constitution",
  SYSPROMPTS_RESPONSE = "sysprompts_response",
  CONVERSATION_UPDATE = "conversation_update",
  FLOW_TEMPLATES_RESPONSE = "flow_templates_response",
  FLOW_CONFIGS_RESPONSE = "flow_configs_response",
  FLOW_INSTANCES_RESPONSE = "flow_instances_response",
  FLOWS_RESPONSE = "flows_response", // Keeping for backward compatibility
  PARALLEL_FLOWS_RESULT = "parallel_flows_result"
}

export interface AssistantToken {
  id: string;
  token: string;
}

export interface WebSocketMessage {
  type: WebSocketMessageType;
  content: any;
  timestamp: string;
  conversation_id?: string;
}

export interface ConversationState {
  id: string;
  name: string;
  messages: Message[];
  lastUpdated: string;
}

export interface AssistantResponse {
  id: string;
  content: string;
}

// Flow-related types
export interface FlowConfig {
  id: string;
  name: string;
  constitution_id: string;
  sysprompt_id?: string;
  superego_enabled: boolean;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface FlowTemplate {
  id: string;
  name: string;
  description: string;
  config: FlowConfig;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface FlowInstance {
  id: string;
  flow_config_id: string;
  conversation_id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
}

export interface ParallelFlowResult {
  flow_config_id: string;
  flow_name: string;
  superego_evaluation?: SuperegoEvaluation;
  assistant_message?: Message;
  constitution_id?: string;
  sysprompt_id?: string;
  superego_enabled: boolean;
}
