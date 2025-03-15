/**
 * API Utilities
 * Shared utilities for API services
 */

// Default API configuration
export const API_BASE_URL = '';
export const DEFAULT_TIMEOUT = 10000; // 10 seconds

/**
 * Helper function to handle fetch requests with timeout and error handling
 */
export async function fetchWithTimeout<T>(
  url: string, 
  options: RequestInit = {}, 
  timeout: number = DEFAULT_TIMEOUT
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    
    // Check for HTTP error status
    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `API Error ${response.status}: ${response.statusText}`;
      
      try {
        // Try to parse error as JSON for more details
        const errorJson = JSON.parse(errorText);
        if (errorJson.message) {
          errorMessage = errorJson.message;
        }
      } catch {
        // If parsing fails, use the raw error text if available
        if (errorText) {
          errorMessage += ` - ${errorText}`;
        }
      }
      
      throw new Error(errorMessage);
    }
    
    return await response.json() as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeout}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Generate debounced function
 * Useful for preventing rapid-fire API calls
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: number | null = null;
  
  return function(...args: Parameters<T>): void {
    if (timeout !== null) {
      clearTimeout(timeout);
    }
    
    timeout = window.setTimeout(() => {
      func(...args);
      timeout = null;
    }, wait);
  };
}

/**
 * Simple rate limiter that ensures minimum time between API calls
 */
export function rateLimiter<T extends (...args: any[]) => Promise<any>>(
  func: T,
  minInterval: number = 500
): (...args: Parameters<T>) => Promise<ReturnType<T>> {
  let lastCall = 0;
  
  return async function(...args: Parameters<T>): Promise<ReturnType<T>> {
    const now = Date.now();
    const timeElapsed = now - lastCall;
    
    if (timeElapsed < minInterval) {
      await new Promise(resolve => setTimeout(resolve, minInterval - timeElapsed));
    }
    
    lastCall = Date.now();
    return func(...args) as ReturnType<T>;
  };
}
