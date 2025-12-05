import { Component, input, ChangeDetectionStrategy, SecurityContext, effect, signal, inject } from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';
import { marked } from 'marked';
import { markedHighlight } from 'marked-highlight';
import hljs from 'highlight.js';

/**
 * Component for rendering markdown content with syntax highlighting
 */
@Component({
  selector: 'app-markdown',
  imports: [],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="markdown-content" [innerHTML]="renderedContent()"></div>
  `,
  styles: [`
    .markdown-content {
      font-size: 0.95rem;
      line-height: 1.6;
    }

    .markdown-content :first-child {
      margin-top: 0;
    }

    .markdown-content :last-child {
      margin-bottom: 0;
    }

    .markdown-content h1,
    .markdown-content h2,
    .markdown-content h3 {
      margin-top: 1.5rem;
      margin-bottom: 0.75rem;
      font-weight: 600;
      color: #333;
    }

    .markdown-content h1 { font-size: 1.5rem; }
    .markdown-content h2 { font-size: 1.3rem; }
    .markdown-content h3 { font-size: 1.1rem; }

    .markdown-content p {
      margin-bottom: 0.75rem;
    }

    .markdown-content ul,
    .markdown-content ol {
      margin-bottom: 0.75rem;
      padding-left: 1.5rem;
    }

    .markdown-content li {
      margin-bottom: 0.25rem;
    }

    .markdown-content code {
      background-color: #f4f4f4;
      padding: 0.2rem 0.4rem;
      border-radius: 3px;
      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
      font-size: 0.9em;
      color: #e83e8c;
    }

    .markdown-content pre {
      background-color: #282c34;
      color: #abb2bf;
      padding: 1rem;
      border-radius: 6px;
      overflow-x: auto;
      margin-bottom: 0.75rem;
    }

    .markdown-content pre code {
      background-color: transparent;
      padding: 0;
      color: inherit;
      font-size: 0.85rem;
    }

    .markdown-content blockquote {
      border-left: 4px solid #ddd;
      padding-left: 1rem;
      margin-left: 0;
      color: #666;
      font-style: italic;
    }

    .markdown-content a {
      color: #667eea;
      text-decoration: none;
    }

    .markdown-content a:hover {
      text-decoration: underline;
    }

    .markdown-content table {
      border-collapse: collapse;
      width: 100%;
      margin-bottom: 0.75rem;
    }

    .markdown-content th,
    .markdown-content td {
      border: 1px solid #ddd;
      padding: 0.5rem;
      text-align: left;
    }

    .markdown-content th {
      background-color: #f4f4f4;
      font-weight: 600;
    }
  `]
})
export class MarkdownComponent {
  private sanitizer = inject(DomSanitizer);

  content = input.required<string>();
  renderedContent = signal<string>('');

  constructor() {
    // Configure marked with syntax highlighting
    marked.use(
      markedHighlight({
        highlight: (code, lang) => {
          if (lang && hljs.getLanguage(lang)) {
            try {
              return hljs.highlight(code, { language: lang }).value;
            } catch (err) {
              console.error('Highlight error:', err);
            }
          }
          return hljs.highlightAuto(code).value;
        }
      })
    );

    // Use effect to handle async markdown parsing
    effect(() => {
      const contentValue = this.content();
      console.log('[Markdown] Rendering content:', contentValue);

      // marked.parse() returns Promise<string> in v17+
      Promise.resolve(marked.parse(contentValue)).then((html) => {
        console.log('[Markdown] Parsed HTML:', html);
        const sanitized = this.sanitizer.sanitize(SecurityContext.HTML, html) || '';
        console.log('[Markdown] Sanitized HTML:', sanitized);
        this.renderedContent.set(sanitized);
      });
    });
  }
}
