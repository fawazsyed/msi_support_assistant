import { Component, input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToolCall } from '../../models/message.model';

/**
 * Component for displaying MCP tool calls
 * Shows tools like math operations, weather queries, etc.
 */
@Component({
  selector: 'app-tool-calls',
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="tool-calls-container">
      <div class="tool-calls-header">
        <span class="tool-icon">🔧</span>
        <span class="tool-label">Tool Calls</span>
      </div>

      @for (tool of toolCalls(); track tool.id) {
        <div class="tool-call">
          <div class="tool-name">{{ tool.name }}</div>

          @if (hasArgs(tool.args)) {
            <div class="tool-args">
              <strong>Arguments:</strong>
              <pre>{{ formatArgs(tool.args) }}</pre>
            </div>
          }

          @if (tool.result !== undefined) {
            <div class="tool-result">
              <strong>Result:</strong>
              <pre>{{ formatResult(tool.result) }}</pre>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .tool-calls-container {
      background-color: #f8f9fa;
      border-left: 3px solid #667eea;
      padding: 0.75rem;
      margin: 0.75rem 0;
      border-radius: 4px;
      font-size: 0.85rem;
    }

    .tool-calls-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: 600;
      color: #667eea;
      margin-bottom: 0.5rem;
    }

    .tool-icon {
      font-size: 1rem;
    }

    .tool-label {
      font-size: 0.85rem;
    }

    .tool-call {
      background-color: white;
      padding: 0.75rem;
      border-radius: 4px;
      margin-bottom: 0.5rem;
    }

    .tool-call:last-child {
      margin-bottom: 0;
    }

    .tool-name {
      font-weight: 600;
      color: #333;
      margin-bottom: 0.5rem;
      font-family: 'Consolas', 'Monaco', monospace;
    }

    .tool-args,
    .tool-result {
      margin-top: 0.5rem;
    }

    .tool-args strong,
    .tool-result strong {
      color: #666;
      font-size: 0.8rem;
      display: block;
      margin-bottom: 0.25rem;
    }

    pre {
      background-color: #f4f4f4;
      padding: 0.5rem;
      border-radius: 3px;
      overflow-x: auto;
      margin: 0;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 0.8rem;
      color: #333;
    }
  `]
})
export class ToolCallsComponent {
  toolCalls = input.required<ToolCall[]>();

  hasArgs(args: Record<string, unknown>): boolean {
    return Object.keys(args).length > 0;
  }

  formatArgs(args: Record<string, unknown>): string {
    return JSON.stringify(args, null, 2);
  }

  formatResult(result: unknown): string {
    if (typeof result === 'object') {
      return JSON.stringify(result, null, 2);
    }
    return String(result);
  }
}
