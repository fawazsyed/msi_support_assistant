import { inject } from '@angular/core';
import { LangchainApiService } from './services/langchain-api.service';

/**
 * Application initializer that waits for the backend to be ready
 * before the Angular app fully loads
 */
export function initializeApp(): () => Promise<void> {
  const apiService = inject(LangchainApiService);

  return async () => {
    console.log('⏳ Waiting for backend to be ready...');

    const isReady = await apiService.waitForBackend(30000);

    if (isReady) {
      console.log('✅ Backend is ready!');
    } else {
      console.error('❌ Backend did not become ready within timeout period');
      throw new Error('Backend startup timeout - please check if all services are running');
    }
  };
}