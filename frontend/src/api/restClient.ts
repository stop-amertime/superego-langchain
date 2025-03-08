/**
 * REST API client for the Superego LangGraph application.
 * This client handles all non-streaming API requests using Axios.
 */

import axios from 'axios';
import { 
    Constitution, 
    Sysprompt, 
    FlowConfig, 
    FlowTemplate, 
    FlowInstance 
} from '../types';

// Default API URL
const API_URL = 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add response interceptor to handle errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        // Log all errors clearly
        if (error.response) {
            // The request was made and the server responded with a status code
            // that falls out of the range of 2xx
            console.error('API Error Response:', {
                status: error.response.status,
                data: error.response.data,
                headers: error.response.headers,
            });
        } else if (error.request) {
            // The request was made but no response was received
            console.error('API Error Request:', error.request);
        } else {
            // Something happened in setting up the request that triggered an Error
            console.error('API Error Setup:', error.message);
        }
        
        // Rethrow the error to be handled by the caller
        return Promise.reject(error);
    }
);

// Generic API response type
export interface ApiResponse<T = any> {
    status: 'success' | 'error';
    data?: T;
    message?: string;
    code?: number;
}

/**
 * API client for constitutions
 */
export const constitutionsApi = {
    getAll: () => api.get<ApiResponse<Constitution[]>>('/api/constitutions'),
    getById: (id: string) => api.get<ApiResponse<Constitution>>(`/api/constitutions/${id}`),
    create: (constitution: Constitution) => api.post<ApiResponse<Constitution>>('/api/constitutions', constitution),
    update: (id: string, constitution: Partial<Constitution>) => api.put<ApiResponse<Constitution>>(`/api/constitutions/${id}`, constitution),
    delete: (id: string) => api.delete<ApiResponse<void>>(`/api/constitutions/${id}`),
};

/**
 * API client for system prompts
 */
export const syspromptsApi = {
    getAll: () => api.get<ApiResponse<Sysprompt[]>>('/api/sysprompts'),
    getById: (id: string) => api.get<ApiResponse<Sysprompt>>(`/api/sysprompts/${id}`),
    create: (sysprompt: Sysprompt) => api.post<ApiResponse<Sysprompt>>('/api/sysprompts', sysprompt),
    update: (id: string, sysprompt: Partial<Sysprompt>) => api.put<ApiResponse<Sysprompt>>(`/api/sysprompts/${id}`, sysprompt),
    delete: (id: string) => api.delete<ApiResponse<void>>(`/api/sysprompts/${id}`),
};

/**
 * API client for flow configurations
 */
export const flowConfigsApi = {
    getAll: () => api.get<ApiResponse<FlowConfig[]>>('/api/flow-configs'),
    getById: (id: string) => api.get<ApiResponse<FlowConfig>>(`/api/flow-configs/${id}`),
    create: (config: Omit<FlowConfig, 'id' | 'created_at' | 'updated_at'>) => 
        api.post<ApiResponse<FlowConfig>>('/api/flow-configs', config),
    update: (id: string, config: Partial<FlowConfig>) => 
        api.put<ApiResponse<FlowConfig>>(`/api/flow-configs/${id}`, config),
    delete: (id: string) => api.delete<ApiResponse<void>>(`/api/flow-configs/${id}`),
};

/**
 * API client for flow templates
 */
export const flowTemplatesApi = {
    getAll: () => api.get<ApiResponse<FlowTemplate[]>>('/api/flow-templates'),
    getById: (id: string) => api.get<ApiResponse<FlowTemplate>>(`/api/flow-templates/${id}`),
    create: (template: Omit<FlowTemplate, 'id' | 'created_at' | 'updated_at'>) => 
        api.post<ApiResponse<FlowTemplate>>('/api/flow-templates', template),
    update: (id: string, template: Partial<FlowTemplate>) => 
        api.put<ApiResponse<FlowTemplate>>(`/api/flow-templates/${id}`, template),
    delete: (id: string) => api.delete<ApiResponse<void>>(`/api/flow-templates/${id}`),
};

/**
 * API client for flow instances
 */
export const flowInstancesApi = {
    getAll: () => api.get<ApiResponse<FlowInstance[]>>('/api/flow-instances'),
    getById: (id: string) => api.get<ApiResponse<FlowInstance>>(`/api/flow-instances/${id}`),
    create: (instance: Omit<FlowInstance, 'id' | 'flow_instance_id' | 'created_at' | 'updated_at' | 'last_message_at'>) => 
        api.post<ApiResponse<FlowInstance>>('/api/flow-instances', instance),
    update: (id: string, instance: Partial<FlowInstance>) => 
        api.put<ApiResponse<FlowInstance>>(`/api/flow-instances/${id}`, instance),
    delete: (id: string) => api.delete<ApiResponse<void>>(`/api/flow-instances/${id}`),
    updateLastMessage: (id: string) => 
        api.post<ApiResponse<FlowInstance>>(`/api/flow-instances/${id}/update-last-message`),
};

// Export all APIs
export const api_client = {
    constitutions: constitutionsApi,
    sysprompts: syspromptsApi,
    flowConfigs: flowConfigsApi,
    flowTemplates: flowTemplatesApi,
    flowInstances: flowInstancesApi,
};

export default api_client;
