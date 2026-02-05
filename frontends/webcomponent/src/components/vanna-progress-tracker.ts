import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';
import { vannaDesignTokens } from '../styles/vanna-design-tokens.js';

interface ProgressItem {
  id: string;
  text: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  detail?: string;
}

@customElement('vanna-progress-tracker')
export class VannaProgressTracker extends LitElement {
  static styles = [
    vannaDesignTokens,
    css`
      :host {
        display: block;
        background: var(--vanna-background-default);
        border: 1px solid var(--vanna-outline-default);
        border-radius: 0 0 var(--vanna-border-radius-lg) var(--vanna-border-radius-lg);
        overflow: hidden;
        font-family: var(--vanna-font-family-default);
      }

      .progress-label {
        padding: var(--vanna-space-3) var(--vanna-space-4) var(--vanna-space-2);
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .progress-label-text {
        font-size: 11px;
        font-weight: 500;
        color: var(--vanna-foreground-dimmest);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0;
      }

      .progress-summary {
        font-size: 10px;
        color: var(--vanna-foreground-dimmest);
        font-weight: 400;
      }

      .progress-list {
        max-height: 300px;
        overflow-y: auto;
        padding-top: 0;
      }

      .progress-item {
        padding: var(--vanna-space-3) var(--vanna-space-4);
        border-bottom: 1px solid var(--vanna-outline-dimmest);
        display: flex;
        align-items: flex-start;
        gap: var(--vanna-space-3);
        transition: background var(--vanna-duration-150) ease;
      }

      .progress-item:last-child {
        border-bottom: none;
      }

      .progress-item:hover {
        background: var(--vanna-background-higher);
      }

      .progress-item.in_progress {
        background: rgba(0, 123, 255, 0.05);
        border-left: 3px solid var(--vanna-accent-primary-default);
      }

      .progress-item.completed {
        opacity: 0.7;
      }

      .progress-item.error {
        background: var(--vanna-accent-negative-subtle);
        border-left: 3px solid var(--vanna-accent-negative-default);
        padding-left: calc(var(--vanna-space-3) - 3px);
      }

      .progress-item.error .progress-text {
        color: var(--vanna-accent-negative-stronger);
      }

      .progress-item.error .progress-detail {
        color: var(--vanna-accent-negative-default);
        font-weight: 500;
      }

      .progress-icon {
        width: 16px;
        height: 16px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 1px;
      }

      .progress-icon.pending {
        background: var(--vanna-outline-default);
      }

      .progress-icon.in_progress {
        background: var(--vanna-accent-primary-default);
      }

      .progress-icon.completed {
        background: var(--vanna-accent-positive-default);
      }

      .progress-icon.error {
        background: var(--vanna-accent-negative-default);
        box-shadow: 0 0 0 2px var(--vanna-accent-negative-subtle);
      }

      .progress-icon svg {
        width: 10px;
        height: 10px;
        color: white;
      }

      .progress-icon.error svg {
        width: 8px;
        height: 8px;
        color: white;
      }

      .spinner-mini {
        width: 10px;
        height: 10px;
        border: 1.5px solid rgba(255, 255, 255, 0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }

      .progress-content {
        flex: 1;
        min-width: 0;
      }

      .progress-text {
        font-size: 13px;
        color: var(--vanna-foreground-default);
        font-weight: 500;
        margin: 0 0 var(--vanna-space-1) 0;
        line-height: 1.3;
      }

      .progress-detail {
        font-size: 11px;
        color: var(--vanna-foreground-dimmest);
        margin: 0;
        line-height: 1.3;
      }

      .empty-state {
        padding: var(--vanna-space-6) var(--vanna-space-4);
        text-align: center;
        color: var(--vanna-foreground-dimmest);
        font-size: 12px;
      }

      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }
    `
  ];

  @property() title = 'Progress';
  @property() theme = 'light';
  @state() private items: ProgressItem[] = [];

  addItem(text: string, detail?: string, id?: string): string {
    const itemId = id || Date.now().toString();
    this.items = [...this.items, {
      id: itemId,
      text,
      status: 'pending',
      detail
    }];
    return itemId;
  }

  updateItem(id: string, status: ProgressItem['status'], detail?: string) {
    this.items = this.items.map(item =>
      item.id === id ? { ...item, status, detail } : item
    );
  }

  clearItems() {
    this.items = [];
  }

  private getStatusIcon(status: ProgressItem['status']) {
    switch (status) {
      case 'pending':
        return html``;
      case 'in_progress':
        return html`<div class="spinner-mini"></div>`;
      case 'completed':
        return html`
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
          </svg>
        `;
      case 'error':
        return html`
          <svg viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        `;
    }
  }

  private getProgressSummary() {
    const completed = this.items.filter(item => item.status === 'completed').length;
    const total = this.items.length;
    const inProgress = this.items.filter(item => item.status === 'in_progress').length;

    if (inProgress > 0) {
      return `${completed}/${total} completed`;
    }
    return total > 0 ? `${completed}/${total} completed` : '';
  }

  render() {
    return html`
      ${this.items.length > 0 ? html`
        <div class="progress-label">
          <span class="progress-label-text">Tasks</span>
          <span class="progress-summary">${this.getProgressSummary()}</span>
        </div>
      ` : ''}

      <div class="progress-list">
        ${this.items.length === 0
          ? html`<div class="empty-state">No tasks yet</div>`
          : this.items.map(item => html`
              <div class="progress-item ${item.status}">
                <div class="progress-icon ${item.status}">
                  ${this.getStatusIcon(item.status)}
                </div>
                <div class="progress-content">
                  <p class="progress-text">${item.text}</p>
                  ${item.detail ? html`<p class="progress-detail">${item.detail}</p>` : ''}
                </div>
              </div>
            `)
        }
      </div>
    `;
  }
}