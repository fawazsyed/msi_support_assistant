import { Component, output, signal, computed, ChangeDetectionStrategy } from '@angular/core';
import { FormsModule } from '@angular/forms';

/**
 * Component for message input with send button
 * Supports Enter to send, Shift+Enter for new line
 */
@Component({
  selector: 'app-message-input',
  imports: [FormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="message-input-container">
      <div class="input-wrapper">
        <textarea
          class="message-input"
          [(ngModel)]="inputValueState"
          (ngModelChange)="updateInputValue($event)"
          (keydown)="onKeyDown($event)"
          placeholder="Ask about MSI products, use tools, or chat..."
          rows="1"
          [disabled]="isDisabled()"
          #textareaRef
        ></textarea>

        <button
          class="send-button"
          (click)="sendMessage()"
          [disabled]="!canSend()"
          [class.active]="canSend()"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M2 10L18 2L10 18L8 11L2 10Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <div class="input-footer">
        <span class="hint">Press Enter to send, Shift+Enter for new line</span>
      </div>
    </div>
  `,
  styles: [`
    .message-input-container {
      background-color: white;
      border-top: 1px solid #e0e0e0;
      padding: 1rem 2rem;
      flex-shrink: 0; /* Prevent input from shrinking */
    }

    .input-wrapper {
      display: flex;
      gap: 0.75rem;
      align-items: flex-end;
      background-color: #f8f9fa;
      border: 2px solid #e0e0e0;
      border-radius: 12px;
      padding: 0.75rem;
      transition: border-color 0.2s;
    }

    .input-wrapper:focus-within {
      border-color: #667eea;
    }

    .message-input {
      flex: 1;
      border: none;
      outline: none;
      background: transparent;
      font-size: 0.95rem;
      font-family: inherit;
      resize: none;
      max-height: 150px;
      overflow-y: auto;
      padding: 0.25rem;
      line-height: 1.5;
    }

    .message-input::placeholder {
      color: #999;
    }

    .message-input:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .send-button {
      width: 40px;
      height: 40px;
      border: none;
      border-radius: 8px;
      background-color: #e0e0e0;
      color: #999;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
      flex-shrink: 0;
    }

    .send-button:disabled {
      cursor: not-allowed;
      opacity: 0.5;
    }

    .send-button.active {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }

    .send-button.active:hover:not(:disabled) {
      transform: scale(1.05);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    .input-footer {
      margin-top: 0.5rem;
      text-align: center;
    }

    .hint {
      font-size: 0.75rem;
      color: #999;
    }

    /* Scrollbar for textarea */
    .message-input::-webkit-scrollbar {
      width: 6px;
    }

    .message-input::-webkit-scrollbar-track {
      background: transparent;
    }

    .message-input::-webkit-scrollbar-thumb {
      background: #ccc;
      border-radius: 3px;
    }
  `]
})
export class MessageInputComponent {
  messageSent = output<string>();

  inputValueSignal = signal('');
  isDisabled = signal(false);

  // Computed signal - automatically updates when inputValueSignal changes
  canSend = computed(() => this.inputValueSignal().trim().length > 0);

  // Property for ngModel binding
  get inputValueState(): string {
    return this.inputValueSignal();
  }

  set inputValueState(value: string) {
    this.inputValueSignal.set(value);
  }

  updateInputValue(value: string): void {
    this.inputValueSignal.set(value);
  }

  onKeyDown(event: KeyboardEvent): void {
    // Send on Enter, new line on Shift+Enter
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  sendMessage(): void {
    const message = this.inputValueSignal().trim();
    if (message) {
      this.messageSent.emit(message);
      this.inputValueSignal.set('');
    }
  }

  setDisabled(disabled: boolean): void {
    this.isDisabled.set(disabled);
  }
}
