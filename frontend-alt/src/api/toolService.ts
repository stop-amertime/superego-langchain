/**
 * Tool Service
 * Handles API calls related to tool confirmation and settings
 */
import { API_BASE_URL, fetchWithTimeout, rateLimiter } from './apiUtils.js';

/**
 * Confirm or deny a pending tool execution
 */
export async function confirmTool(
  instanceId: string, 
  toolExecutionId: string, 
  confirmed: boolean
): Promise<ToolConfirmationResponse> {
  return fetchWithTimeout<ToolConfirmationResponse>(
    `${API_BASE_URL}/flow/${encodeURIComponent(instanceId)}/confirm_tool`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        tool_execution_id: toolExecutionId,
        confirmed
      })
    }
  );
}

/**
 * Update tool confirmation settings for a flow instance
 */
export async function updateToolConfirmationSettings(
  instanceId: string,
  settings: { confirmAll: boolean; exemptedTools: string[] }
): Promise<ToolConfirmationSettings> {
  return fetchWithTimeout<ToolConfirmationSettings>(
    `${API_BASE_URL}/flow/${encodeURIComponent(instanceId)}/confirmation_settings`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        confirm_all: settings.confirmAll,
        exempted_tools: settings.exemptedTools
      })
    }
  );
}

/**
 * Get current tool confirmation settings for a flow instance
 * Apply rate limiting to avoid excessive API calls
 */
export const getToolConfirmationSettings = rateLimiter(
  async (instanceId: string): Promise<ToolConfirmationSettings> => {
    return fetchWithTimeout<ToolConfirmationSettings>(
      `${API_BASE_URL}/flow/${encodeURIComponent(instanceId)}/confirmation_settings`
    );
  },
  500 // Rate limit to one call every 500ms
);

/**
 * Toggle a specific tool's exempt status
 */
export async function toggleToolExemption(
  instanceId: string,
  toolName: string,
  currentSettings: ToolConfirmationSettings
): Promise<ToolConfirmationSettings> {
  const updatedExemptedTools = [...currentSettings.exempted_tools];
  const toolIndex = updatedExemptedTools.indexOf(toolName);
  
  // If tool is already exempted, remove it; otherwise add it
  if (toolIndex >= 0) {
    updatedExemptedTools.splice(toolIndex, 1);
  } else {
    updatedExemptedTools.push(toolName);
  }
  
  return updateToolConfirmationSettings(instanceId, {
    confirmAll: currentSettings.confirm_all,
    exemptedTools: updatedExemptedTools
  });
}
