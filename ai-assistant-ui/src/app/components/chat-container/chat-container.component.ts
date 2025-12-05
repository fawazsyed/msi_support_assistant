import { Component, computed, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SidebarComponent } from '../sidebar/sidebar.component';
import { MessageListComponent } from '../message-list/message-list.component';
import { MessageInputComponent } from '../message-input/message-input.component';
import { LangchainApiService } from '../../services/langchain-api.service';

/**
 * Main chat container component
 * Orchestrates sidebar, message list, and input
 */
@Component({
  selector: 'app-chat-container',
  imports: [CommonModule, SidebarComponent, MessageListComponent, MessageInputComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="chat-container">
      <app-sidebar
        [conversations]="apiService.conversations()"
        [currentConversationId]="currentConversationId()"
        (newConversation)="onNewConversation()"
        (conversationSelected)="onConversationSelected($event)"
        (conversationDeleted)="onConversationDeleted($event)"
      />

      <div class="main-content">
        <div class="chat-header">
          <h2>{{ currentConversationTitle() }}</h2>
          @if (apiService.error()) {
            <div class="error-banner">
              ⚠️ {{ apiService.error() }}
            </div>
          }
        </div>

        <app-message-list
          [messages]="currentMessages()"
          [isLoading]="apiService.isLoading()"
        />

        <app-message-input
          (messageSent)="onMessageSent($event)"
        />
      </div>
    </div>
  `,
  styles: [`
    .chat-container {
      display: flex;
      height: 100vh;
      width: 100%;
      overflow: hidden;
    }

    .main-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      background-color: #f8f9fa;
      overflow: hidden;
      min-height: 0; /* Critical for flexbox scrolling */
    }

    .chat-header {
      background-color: white;
      border-bottom: 1px solid #e0e0e0;
      padding: 1.5rem 2rem;
      flex-shrink: 0; /* Prevent header from shrinking */
    }

    .chat-header h2 {
      margin: 0;
      font-size: 1.25rem;
      color: #333;
      font-weight: 600;
    }

    .error-banner {
      margin-top: 0.75rem;
      padding: 0.75rem;
      background-color: #fff3cd;
      border: 1px solid #ffc107;
      border-radius: 6px;
      color: #856404;
      font-size: 0.9rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
  `]
})
export class ChatContainerComponent {
  apiService = inject(LangchainApiService);

  currentConversationId = computed(() => {
    return this.apiService.currentConversation()?.id || null;
  });

  currentConversationTitle = computed(() => {
    return this.apiService.currentConversation()?.title || 'MSI AI Assistant';
  });

  currentMessages = computed(() => {
    return this.apiService.currentConversation()?.messages || [];
  });

  onNewConversation(): void {
    this.apiService.createNewConversation();
  }

  onConversationSelected(id: string): void {
    this.apiService.loadConversation(id);
  }

  onConversationDeleted(id: string): void {
    if (confirm('Are you sure you want to delete this conversation?')) {
      this.apiService.deleteConversation(id);
    }
  }

  async onMessageSent(content: string): Promise<void> {
    await this.apiService.sendMessage(content);
  }
}
