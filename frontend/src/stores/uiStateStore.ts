/**
 * UI State Store
 * Manages UI-specific state like modals, expanded cards, loading states
 */
import { writable, derived } from 'svelte/store';

// Initial UI state
const initialState: UIState = {
  isModalOpen: false,
  expandedCards: new Set<string>(),
  isLoading: false,
  error: null
};

// Create the core store
const uiState = writable<UIState>(initialState);

// Derived stores for specific pieces of UI state
export const isModalOpen = derived(uiState, $state => $state.isModalOpen);
export const expandedCards = derived(uiState, $state => $state.expandedCards);
export const isLoading = derived(uiState, $state => $state.isLoading);
export const error = derived(uiState, $state => $state.error);

// Actions to update UI state
export function openModal() {
  uiState.update(state => ({ ...state, isModalOpen: true }));
}

export function closeModal() {
  uiState.update(state => ({ ...state, isModalOpen: false }));
}

export function toggleCardExpanded(cardId: string) {
  uiState.update(state => {
    const newExpandedCards = new Set(state.expandedCards);
    
    if (newExpandedCards.has(cardId)) {
      newExpandedCards.delete(cardId);
    } else {
      newExpandedCards.add(cardId);
    }
    
    return { ...state, expandedCards: newExpandedCards };
  });
}

export function setLoading(loading: boolean) {
  uiState.update(state => ({ ...state, isLoading: loading }));
}

export function setError(errorMessage: string | null) {
  uiState.update(state => ({ ...state, error: errorMessage }));
}

export function resetUiState() {
  uiState.set(initialState);
}

export { uiState };
