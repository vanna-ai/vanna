import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { vannaDesignTokens } from '../styles/vanna-design-tokens.js';

export interface TaskItem {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  timestamp?: string;
}

@customElement('rich-task-list')
export class RichTaskList extends LitElement {
  static styles = [
    vannaDesignTokens,
    css`
      :host {
        display: block;
        margin-bottom: var(--vanna-space-4);
        font-family: var(--vanna-font-family-default);
      }

      .task-list {
        border: 1px solid var(--vanna-outline-default);
        border-radius: var(--vanna-border-radius-lg);
        background: var(--vanna-background-default);
        box-shadow: var(--vanna-shadow-sm);
        overflow: hidden;
        transition: box-shadow var(--vanna-duration-200) ease;
      }

      .task-list:hover {
        box-shadow: var(--vanna-shadow-md);
      }

      .task-list-header {
        padding: var(--vanna-space-4) var(--vanna-space-5);
        background: var(--vanna-background-higher);
        border-bottom: 1px solid var(--vanna-outline-default);
      }

      .task-list-title {
        margin: 0 0 var(--vanna-space-3) 0;
        font-size: 1rem;
        font-weight: 600;
        color: var(--vanna-foreground-default);
      }

      .task-list-progress {
        display: flex;
        align-items: center;
        gap: var(--vanna-space-3);
      }

      .progress-text {
        font-size: 0.875rem;
        color: var(--vanna-foreground-dimmer);
        min-width: fit-content;
      }

      .progress-bar {
        flex: 1;
        height: 6px;
        background: var(--vanna-background-root);
        border-radius: 3px;
        overflow: hidden;
      }

      .progress-fill {
        height: 100%;
        background: var(--vanna-accent-primary-default);
        border-radius: 3px;
        transition: width var(--vanna-duration-300) ease;
      }

      .progress-fill.animated {
        animation: progressPulse 2s ease-in-out infinite;
      }

      @keyframes progressPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
      }

      .progress-fill.status-success {
        background: var(--vanna-accent-positive-default);
      }

      .progress-fill.status-warning {
        background: var(--vanna-accent-warning-default);
      }

      .progress-fill.status-error {
        background: var(--vanna-accent-negative-default);
      }

      .task-list-items {
        padding: var(--vanna-space-2);
      }

      .task-item {
        display: flex;
        align-items: flex-start;
        gap: var(--vanna-space-3);
        padding: var(--vanna-space-3);
        border-radius: var(--vanna-border-radius-md);
        transition: background-color var(--vanna-duration-200) ease;
      }

      .task-item:hover {
        background: var(--vanna-background-root);
      }

      .task-item.status-completed {
        opacity: 0.7;
      }

      .task-item.status-failed {
        background: rgba(239, 68, 68, 0.1);
      }

      .task-icon {
        font-size: 1rem;
        margin-top: 0.125rem;
      }

      .task-content {
        flex: 1;
        min-width: 0;
      }

      .task-title {
        font-weight: 500;
        color: var(--vanna-foreground-default);
        margin-bottom: var(--vanna-space-1);
      }

      .task-description {
        font-size: 0.875rem;
        color: var(--vanna-foreground-dimmer);
        margin-bottom: var(--vanna-space-2);
      }

      .task-progress {
        display: flex;
        align-items: center;
        gap: var(--vanna-space-2);
        margin-bottom: var(--vanna-space-2);
      }

      .task-progress-bar {
        flex: 1;
        height: 4px;
        background: var(--vanna-background-root);
        border-radius: 2px;
        overflow: hidden;
      }

      .task-progress-fill {
        height: 100%;
        background: var(--vanna-accent-primary-default);
        border-radius: 2px;
        transition: width var(--vanna-duration-300) ease;
      }

      .task-progress-text {
        font-size: 0.75rem;
        color: var(--vanna-foreground-dimmer);
        min-width: fit-content;
      }

      .task-timestamp {
        font-size: 0.75rem;
        color: var(--vanna-foreground-dimmest);
      }

      /* Responsive adjustments */
      @media (max-width: 768px) {
        .task-list-header {
          padding-left: var(--vanna-space-4);
          padding-right: var(--vanna-space-4);
        }

        .task-list-progress {
          flex-direction: column;
          align-items: stretch;
          gap: var(--vanna-space-2);
        }
      }
    `
  ];

  @property() title = '';
  @property({ type: Array }) tasks: TaskItem[] = [];
  @property({ type: Boolean }) showProgress = true;
  @property({ type: Boolean }) showTimestamps = false;
  @property() theme: 'light' | 'dark' = 'dark';

  private get completedTasks(): number {
    return this.tasks.filter(task => task.status === 'completed').length;
  }

  private get progressPercentage(): number {
    return this.tasks.length > 0 ? (this.completedTasks / this.tasks.length) * 100 : 0;
  }

  private getStatusIcon(status: string): string {
    const icons = {
      'pending': '⏳',
      'running': '🔄',
      'completed': '✅',
      'failed': '❌'
    };
    return icons[status as keyof typeof icons] || '⏳';
  }

  private renderTask(task: TaskItem) {
    const statusIcon = this.getStatusIcon(task.status);

    return html`
      <div class="task-item status-${task.status}" data-task-id="${task.id}">
        <div class="task-icon">${statusIcon}</div>
        <div class="task-content">
          <div class="task-title">${task.title}</div>
          ${task.description ? html`
            <div class="task-description">${task.description}</div>
          ` : ''}
          ${task.progress !== null && task.progress !== undefined ? html`
            <div class="task-progress">
              <div class="task-progress-bar">
                <div class="task-progress-fill" style="width: ${task.progress * 100}%"></div>
              </div>
              <span class="task-progress-text">${Math.round(task.progress * 100)}%</span>
            </div>
          ` : ''}
          ${this.showTimestamps && task.timestamp ? html`
            <div class="task-timestamp">${task.timestamp}</div>
          ` : ''}
        </div>
      </div>
    `;
  }

  render() {
    return html`
      <div class="task-list">
        <div class="task-list-header">
          <h3 class="task-list-title">${this.title}</h3>
          ${this.showProgress ? html`
            <div class="task-list-progress">
              <span class="progress-text">${this.completedTasks}/${this.tasks.length} completed</span>
              <div class="progress-bar">
                <div class="progress-fill" style="width: ${this.progressPercentage}%"></div>
              </div>
            </div>
          ` : ''}
        </div>
        <div class="task-list-items">
          ${this.tasks.map(task => this.renderTask(task))}
        </div>
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'rich-task-list': RichTaskList;
  }
}