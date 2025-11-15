import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { vannaDesignTokens } from '../styles/vanna-design-tokens.js';

@customElement('rich-progress-bar')
export class RichProgressBar extends LitElement {
  static styles = [
    vannaDesignTokens,
    css`
      :host {
        display: block;
        margin-bottom: var(--vanna-space-4);
        font-family: var(--vanna-font-family-default);
      }

      .progress-container {
        padding: var(--vanna-space-4);
        border: 1px solid var(--vanna-outline-default);
        border-radius: var(--vanna-border-radius-lg);
        background: var(--vanna-background-default);
        box-shadow: var(--vanna-shadow-sm);
        transition: box-shadow var(--vanna-duration-200) ease;
      }

      .progress-container:hover {
        box-shadow: var(--vanna-shadow-md);
      }

      .progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--vanna-space-3);
      }

      .progress-label {
        font-weight: 500;
        color: var(--vanna-foreground-default);
      }

      .progress-percentage {
        font-size: 0.875rem;
        color: var(--vanna-foreground-dimmer);
        font-weight: 600;
      }

      .progress-track {
        height: 12px;
        background: var(--vanna-background-root);
        border-radius: 6px;
        overflow: hidden;
        border: 1px solid var(--vanna-outline-default);
        position: relative;
      }

      .progress-fill {
        height: 100%;
        background: var(--vanna-accent-primary-default);
        border-radius: 6px;
        transition: width var(--vanna-duration-300) ease;
        position: relative;
        overflow: hidden;
      }

      .progress-fill.animated {
        animation: progressPulse 2s ease-in-out infinite;
      }

      .progress-fill.animated::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        bottom: 0;
        right: 0;
        background: linear-gradient(
          90deg,
          transparent,
          rgba(255, 255, 255, 0.2),
          transparent
        );
        animation: progressShimmer 1.5s infinite;
      }

      @keyframes progressPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
      }

      @keyframes progressShimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
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

      .progress-fill.status-info {
        background: var(--vanna-accent-primary-default);
      }

      /* Indeterminate progress animation */
      .progress-fill.indeterminate {
        background: linear-gradient(
          90deg,
          transparent 0%,
          var(--vanna-accent-primary-default) 50%,
          transparent 100%
        );
        background-size: 200% 100%;
        animation: indeterminateProgress 2s linear infinite;
        width: 100% !important;
      }

      @keyframes indeterminateProgress {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
      }

      /* Text content for description */
      .progress-description {
        margin-top: var(--vanna-space-2);
        font-size: 0.875rem;
        color: var(--vanna-foreground-dimmer);
        line-height: 1.4;
      }
    `
  ];

  @property({ type: Number }) value = 0;
  @property() label = '';
  @property() description = '';
  @property({ type: Boolean }) showPercentage = true;
  @property() status: 'info' | 'success' | 'warning' | 'error' = 'info';
  @property({ type: Boolean }) animated = false;
  @property({ type: Boolean }) indeterminate = false;
  @property() theme: 'light' | 'dark' = 'dark';

  private get percentage(): number {
    if (this.indeterminate) return 100;
    return Math.round(Math.max(0, Math.min(1, this.value)) * 100);
  }

  private get progressClasses(): string {
    const classes = ['progress-fill'];

    if (this.animated) {
      classes.push('animated');
    }

    if (this.indeterminate) {
      classes.push('indeterminate');
    }

    if (this.status) {
      classes.push(`status-${this.status}`);
    }

    return classes.join(' ');
  }

  render() {
    return html`
      <div class="progress-container">
        ${this.label || this.showPercentage ? html`
          <div class="progress-header">
            ${this.label ? html`<span class="progress-label">${this.label}</span>` : ''}
            ${this.showPercentage && !this.indeterminate ? html`
              <span class="progress-percentage">${this.percentage}%</span>
            ` : ''}
          </div>
        ` : ''}

        <div class="progress-track">
          <div
            class="${this.progressClasses}"
            style="width: ${this.indeterminate ? '100' : this.percentage}%">
          </div>
        </div>

        ${this.description ? html`
          <div class="progress-description">${this.description}</div>
        ` : ''}
      </div>
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'rich-progress-bar': RichProgressBar;
  }
}