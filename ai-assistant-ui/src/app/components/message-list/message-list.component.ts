import { Component, input, effect, viewChild, ElementRef, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Message } from '../../models/message.model';
import { MessageItemComponent } from '../message-item/message-item.component';

/**
 * Component for displaying a scrollable list of messages
 * Auto-scrolls to bottom on new messages
 */
@Component({
  selector: 'app-message-list',
  imports: [CommonModule, MessageItemComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="message-list" #messageList>
      @if (messages().length === 0) {
        <div class="empty-state">
          <div class="empty-icon">💬</div>
          <h3>Start a Conversation</h3>
          <p>Ask questions about MSI products, use math tools, check weather, and more!</p>

          <div class="example-queries">
            <h4>Try asking:</h4>
            <ul>
              <li>"How do I add a new user?"</li>
              <li>"What is 25 times 4?"</li>
              <li>"What's the weather in New York?"</li>
              <li>"What is the magic number?"</li>
            </ul>
          </div>
        </div>
      } @else {
        @for (message of messages(); track message.id) {
          <app-message-item [message]="message" />
        }
      }

      @if (isLoading()) {
        <div class="loading-indicator">
          <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span class="loading-text">MSI Assistant is thinking...</span>
        </div>
      }
    </div>
  `,
  styles: [`
    .message-list {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 2rem;
      background-color: #ffffff;
      min-height: 0; /* Critical for flexbox scrolling */
    }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      text-align: center;
      color: #666;
      padding: 2rem;
    }

    .empty-icon {
      font-size: 4rem;
      margin-bottom: 1rem;
      opacity: 0.5;
    }

    .empty-state h3 {
      margin: 0 0 0.5rem 0;
      color: #333;
      font-size: 1.5rem;
    }

    .empty-state p {
      margin: 0 0 2rem 0;
      color: #666;
      font-size: 1rem;
    }

    .example-queries {
      background-color: #f8f9fa;
      padding: 1.5rem;
      border-radius: 8px;
      max-width: 500px;
    }

    .example-queries h4 {
      margin: 0 0 1rem 0;
      color: #333;
      font-size: 1rem;
    }

    .example-queries ul {
      list-style: none;
      padding: 0;
      margin: 0;
      text-align: left;
    }

    .example-queries li {
      padding: 0.5rem;
      margin-bottom: 0.5rem;
      background-color: white;
      border-radius: 4px;
      border-left: 3px solid #667eea;
      color: #333;
      font-family: monospace;
      font-size: 0.9rem;
    }

    .loading-indicator {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem;
      background-color: rgba(102, 126, 234, 0.05);
      border-radius: 8px;
      margin-top: 1rem;
    }

    .typing-dots {
      display: flex;
      gap: 0.3rem;
    }

    .typing-dots span {
      width: 8px;
      height: 8px;
      background-color: #667eea;
      border-radius: 50%;
      animation: bounce 1.4s infinite ease-in-out both;
    }

    .typing-dots span:nth-child(1) {
      animation-delay: -0.32s;
    }

    .typing-dots span:nth-child(2) {
      animation-delay: -0.16s;
    }

    @keyframes bounce {
      0%, 80%, 100% {
        transform: scale(0);
        opacity: 0.5;
      }
      40% {
        transform: scale(1);
        opacity: 1;
      }
    }

    .loading-text {
      color: #667eea;
      font-weight: 500;
      font-size: 0.9rem;
    }

    /* Scrollbar styling */
    .message-list::-webkit-scrollbar {
      width: 8px;
    }

    .message-list::-webkit-scrollbar-track {
      background: #f1f1f1;
    }

    .message-list::-webkit-scrollbar-thumb {
      background: #ccc;
      border-radius: 4px;
    }

    .message-list::-webkit-scrollbar-thumb:hover {
      background: #999;
    }
  `]
})
export class MessageListComponent {
  messages = input.required<Message[]>();
  isLoading = input<boolean>(false);

  messageListRef = viewChild<ElementRef<HTMLDivElement>>('messageList');

  constructor() {
    // Auto-scroll on new messages
    effect(() => {
      const messages = this.messages();
      if (messages.length > 0) {
        this.scrollToBottom();
      }
    });
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      const element = this.messageListRef()?.nativeElement;
      if (element) {
        element.scrollTop = element.scrollHeight;
      }
    }, 100);
  }
}
