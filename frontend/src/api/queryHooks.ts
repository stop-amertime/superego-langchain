/**
 * React Query hooks for the Superego LangGraph application.
 * These hooks provide a convenient way to use the REST API client with React Query.
 */

import { useQuery, useMutation, useQueryClient, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { 
    Constitution, 
    Sysprompt, 
    FlowConfig, 
    FlowTemplate, 
    FlowInstance 
} from '../types';
import api_client, { ApiResponse } from './restClient';

// Create a client
export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
            retry: 1,
            staleTime: 5 * 60 * 1000, // 5 minutes
        },
    },
});

// Query keys
export const queryKeys = {
    constitutions: {
        all: ['constitutions'] as const,
        detail: (id: string) => ['constitutions', id] as const,
    },
    sysprompts: {
        all: ['sysprompts'] as const,
        detail: (id: string) => ['sysprompts', id] as const,
    },
    flowConfigs: {
        all: ['flowConfigs'] as const,
        detail: (id: string) => ['flowConfigs', id] as const,
    },
    flowTemplates: {
        all: ['flowTemplates'] as const,
        detail: (id: string) => ['flowTemplates', id] as const,
    },
    flowInstances: {
        all: ['flowInstances'] as const,
        detail: (id: string) => ['flowInstances', id] as const,
    },
};

// Helper to extract data from API response
const extractData = <T>(response: ApiResponse<T>): T => {
    if (response.status === 'error') {
        throw new Error(response.message || 'Unknown error');
    }
    
    if (!response.data) {
        throw new Error('No data received from server');
    }
    
    return response.data as T;
};

// Constitution hooks
export const useConstitutions = () => {
    return useQuery({
        queryKey: queryKeys.constitutions.all,
        queryFn: async () => {
            const response = await api_client.constitutions.getAll();
            const data = extractData<any>(response.data);
            
            // Handle both array and dictionary formats
            if (Array.isArray(data)) {
                return data as Constitution[];
            } else {
                // Convert dictionary to array
                return Object.values(data as Record<string, Constitution>);
            }
        },
    });
};

export const useConstitution = (id: string) => {
    return useQuery({
        queryKey: queryKeys.constitutions.detail(id),
        queryFn: async () => {
            const response = await api_client.constitutions.getById(id);
            return extractData<Constitution>(response.data);
        },
        enabled: !!id,
    });
};

export const useCreateConstitution = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (constitution: Constitution) => {
            const response = await api_client.constitutions.create(constitution);
            return extractData<Constitution>(response.data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.constitutions.all });
        },
    });
};

export const useUpdateConstitution = (id: string) => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (constitution: Partial<Constitution>) => {
            const response = await api_client.constitutions.update(id, constitution);
            return extractData<Constitution>(response.data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.constitutions.detail(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.constitutions.all });
        },
    });
};

export const useDeleteConstitution = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (id: string) => {
            const response = await api_client.constitutions.delete(id);
            return id;
        },
        onSuccess: (id) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.constitutions.all });
            queryClient.removeQueries({ queryKey: queryKeys.constitutions.detail(id) });
        },
    });
};

// System Prompts hooks
export const useSysprompts = () => {
    return useQuery({
        queryKey: queryKeys.sysprompts.all,
        queryFn: async () => {
            const response = await api_client.sysprompts.getAll();
            const data = extractData<any>(response.data);
            
            // Handle both array and dictionary formats
            if (Array.isArray(data)) {
                return data as Sysprompt[];
            } else {
                // Convert dictionary to array
                return Object.values(data as Record<string, Sysprompt>);
            }
        },
    });
};

export const useSysprompt = (id: string) => {
    return useQuery({
        queryKey: queryKeys.sysprompts.detail(id),
        queryFn: async () => {
            const response = await api_client.sysprompts.getById(id);
            return extractData<Sysprompt>(response.data);
        },
        enabled: !!id,
    });
};

export const useCreateSysprompt = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (sysprompt: Sysprompt) => {
            const response = await api_client.sysprompts.create(sysprompt);
            return extractData<Sysprompt>(response.data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.sysprompts.all });
        },
    });
};

export const useUpdateSysprompt = (id: string) => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (sysprompt: Partial<Sysprompt>) => {
            const response = await api_client.sysprompts.update(id, sysprompt);
            return extractData<Sysprompt>(response.data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.sysprompts.detail(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.sysprompts.all });
        },
    });
};

export const useDeleteSysprompt = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (id: string) => {
            const response = await api_client.sysprompts.delete(id);
            return id;
        },
        onSuccess: (id) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.sysprompts.all });
            queryClient.removeQueries({ queryKey: queryKeys.sysprompts.detail(id) });
        },
    });
};

// Flow Config hooks
export const useFlowConfigs = () => {
    return useQuery({
        queryKey: queryKeys.flowConfigs.all,
        queryFn: async () => {
            const response = await api_client.flowConfigs.getAll();
            const data = extractData<any>(response.data);
            
            // Handle both array and dictionary formats
            if (Array.isArray(data)) {
                return data as FlowConfig[];
            } else {
                // Convert dictionary to array
                return Object.values(data as Record<string, FlowConfig>);
            }
        },
    });
};

export const useFlowConfig = (id: string) => {
    return useQuery({
        queryKey: queryKeys.flowConfigs.detail(id),
        queryFn: async () => {
            const response = await api_client.flowConfigs.getById(id);
            return extractData<FlowConfig>(response.data);
        },
        enabled: !!id,
    });
};

export const useCreateFlowConfig = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (config: Omit<FlowConfig, 'id' | 'created_at' | 'updated_at'>) => {
            const response = await api_client.flowConfigs.create(config);
            return extractData<FlowConfig>(response.data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.flowConfigs.all });
        },
    });
};

export const useUpdateFlowConfig = (id: string) => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (config: Partial<FlowConfig>) => {
            const response = await api_client.flowConfigs.update(id, config);
            return extractData<FlowConfig>(response.data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.flowConfigs.detail(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.flowConfigs.all });
        },
    });
};

export const useDeleteFlowConfig = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (id: string) => {
            const response = await api_client.flowConfigs.delete(id);
            return id;
        },
        onSuccess: (id) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.flowConfigs.all });
            queryClient.removeQueries({ queryKey: queryKeys.flowConfigs.detail(id) });
        },
    });
};

// Flow Template hooks
export const useFlowTemplates = () => {
    return useQuery({
        queryKey: queryKeys.flowTemplates.all,
        queryFn: async () => {
            const response = await api_client.flowTemplates.getAll();
            const data = extractData<any>(response.data);
            
            // Handle both array and dictionary formats
            if (Array.isArray(data)) {
                return data as FlowTemplate[];
            } else {
                // Convert dictionary to array
                return Object.values(data as Record<string, FlowTemplate>);
            }
        },
    });
};

export const useFlowTemplate = (id: string) => {
    return useQuery({
        queryKey: queryKeys.flowTemplates.detail(id),
        queryFn: async () => {
            const response = await api_client.flowTemplates.getById(id);
            return extractData<FlowTemplate>(response.data);
        },
        enabled: !!id,
    });
};

export const useCreateFlowTemplate = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (template: Omit<FlowTemplate, 'id' | 'created_at' | 'updated_at'>) => {
            const response = await api_client.flowTemplates.create(template);
            return extractData<FlowTemplate>(response.data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.flowTemplates.all });
        },
    });
};

export const useUpdateFlowTemplate = (id: string) => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (template: Partial<FlowTemplate>) => {
            const response = await api_client.flowTemplates.update(id, template);
            return extractData<FlowTemplate>(response.data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.flowTemplates.detail(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.flowTemplates.all });
        },
    });
};

export const useDeleteFlowTemplate = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (id: string) => {
            const response = await api_client.flowTemplates.delete(id);
            return id;
        },
        onSuccess: (id) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.flowTemplates.all });
            queryClient.removeQueries({ queryKey: queryKeys.flowTemplates.detail(id) });
        },
    });
};

// Flow Instance hooks
export const useFlowInstances = () => {
    return useQuery({
        queryKey: queryKeys.flowInstances.all,
        queryFn: async () => {
            const response = await api_client.flowInstances.getAll();
            const data = extractData<any>(response.data);
            
            // Handle both array and dictionary formats
            if (Array.isArray(data)) {
                return data as FlowInstance[];
            } else {
                // Convert dictionary to array
                return Object.values(data as Record<string, FlowInstance>);
            }
        },
    });
};

export const useFlowInstance = (id: string) => {
    return useQuery({
        queryKey: queryKeys.flowInstances.detail(id),
        queryFn: async () => {
            const response = await api_client.flowInstances.getById(id);
            return extractData<FlowInstance>(response.data);
        },
        enabled: !!id,
    });
};

export const useCreateFlowInstance = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (instance: {name: string, flow_config_id: string, description?: string}) => {
            const response = await api_client.flowInstances.create(instance);
            return extractData<FlowInstance>(response.data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.flowInstances.all });
        },
    });
};

export const useUpdateFlowInstance = (id: string) => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (instance: Partial<FlowInstance>) => {
            const response = await api_client.flowInstances.update(id, instance);
            return extractData<FlowInstance>(response.data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.flowInstances.detail(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.flowInstances.all });
        },
    });
};

export const useDeleteFlowInstance = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (id: string) => {
            const response = await api_client.flowInstances.delete(id);
            return id;
        },
        onSuccess: (id) => {
            queryClient.invalidateQueries({ queryKey: queryKeys.flowInstances.all });
            queryClient.removeQueries({ queryKey: queryKeys.flowInstances.detail(id) });
        },
    });
};

export const useUpdateFlowInstanceLastMessage = (id: string) => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async () => {
            const response = await api_client.flowInstances.updateLastMessage(id);
            return extractData<FlowInstance>(response.data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.flowInstances.detail(id) });
            queryClient.invalidateQueries({ queryKey: queryKeys.flowInstances.all });
        },
    });
};
