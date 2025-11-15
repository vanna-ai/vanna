import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { vannaDesignTokens } from '../styles/vanna-design-tokens.js';
import Plotly from 'plotly.js-dist-min';

export interface PlotlyData {
  x?: any[];
  y?: any[];
  type?: any;
  mode?: any;
  name?: string;
  marker?: any;
  line?: any;
  [key: string]: any;
}

export interface PlotlyLayout {
  title?: any;
  xaxis?: any;
  yaxis?: any;
  font?: any;
  paper_bgcolor?: string;
  plot_bgcolor?: string;
  margin?: any;
  showlegend?: boolean;
  height?: number;
  width?: number;
  modebar?: any;
  [key: string]: any;
}

@customElement('plotly-chart')
export class PlotlyChart extends LitElement {
  static styles = [
    vannaDesignTokens,
    css`
      :host {
        display: block;
        font-family: var(--vanna-font-family-default);
        width: 100%;
        height: 100%;
      }

      .plotly-div {
        width: 100%;
        min-height: 400px;
      }

      /* Plotly layering fix for Shadow DOM */
      .plotly-div,
      .plotly-div .js-plotly-plot,
      .plotly-div .plot-container,
      .plotly-div .svg-container {
        position: relative;
        width: 100%;
        height: 100%;
      }

      .plotly-div svg.main-svg {
        position: absolute;
        top: 0;
        left: 0;
      }

      .plotly-div .hoverlayer {
        pointer-events: none;
      }

      .error-message {
        padding: var(--vanna-space-4);
        color: var(--vanna-accent-negative-default);
        text-align: center;
        font-style: italic;
      }

      .loading-message {
        padding: var(--vanna-space-4);
        color: var(--vanna-foreground-dimmer);
        text-align: center;
        font-style: italic;
      }
    `
  ];

  @property({ type: Array }) data: PlotlyData[] = [];
  @property({ type: Object }) layout: PlotlyLayout = {};
  @property({ type: Object }) config = {};
  @property({ type: Boolean }) loading = false;
  @property() error = '';
  @property() theme: 'light' | 'dark' = 'dark';

  private plotlyDiv?: HTMLElement;
  private resizeObserver?: ResizeObserver;

  firstUpdated() {
    this.plotlyDiv = this.shadowRoot?.querySelector('.plotly-div') as HTMLElement;
    this._renderChart();
    this._setupResizeObserver();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.resizeObserver?.disconnect();
  }

  private _setupResizeObserver() {
    if (!this.plotlyDiv) return;

    this.resizeObserver = new ResizeObserver(() => {
      if (this.plotlyDiv && this.data.length > 0) {
        const width = this.plotlyDiv.offsetWidth;
        Plotly.relayout(this.plotlyDiv, { width });
      }
    });

    this.resizeObserver.observe(this.plotlyDiv);
  }

  updated(changedProperties: Map<string | number | symbol, unknown>) {
    if (changedProperties.has('data') || changedProperties.has('layout') || changedProperties.has('theme')) {
      this._renderChart();
    }
  }

  private _getDefaultLayout(): PlotlyLayout {
    const isDark = this.theme === 'dark';

    // Start with layout from backend (which may include white background)
    const mergedLayout = {
      ...this.layout,
      // Only add font/modebar if not already set by backend
      font: this.layout.font || {
        family: 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        color: isDark ? 'rgb(242, 244, 247)' : 'rgb(17, 24, 39)',
        size: 12
      },
      modebar: this.layout.modebar || {
        bgcolor: isDark ? 'rgba(21, 26, 38, 0.8)' : 'rgba(255, 255, 255, 0.8)',
        color: isDark ? 'rgb(177, 186, 196)' : 'rgb(75, 85, 99)',
        activecolor: isDark ? 'rgb(242, 244, 247)' : 'rgb(17, 24, 39)',
        orientation: 'h'
      },
      // Set explicit dimensions for Shadow DOM compatibility
      autosize: false,
      width: this.layout.width || undefined,
      height: this.layout.height || 400,
    };

    // If backend didn't set background colors, use transparent
    if (!this.layout.paper_bgcolor) {
      mergedLayout.paper_bgcolor = 'transparent';
    }
    if (!this.layout.plot_bgcolor) {
      mergedLayout.plot_bgcolor = 'transparent';
    }

    return mergedLayout;
  }

  private _getDefaultConfig() {
    return {
      responsive: true,
      displayModeBar: false,
      ...this.config
    };
  }

  private async _renderChart() {
    if (!this.plotlyDiv || this.loading || this.error || this.data.length === 0) {
      return;
    }

    try {
      const layout = this._getDefaultLayout();
      const config = this._getDefaultConfig();

      await Plotly.newPlot(this.plotlyDiv, this.data, layout, config);
    } catch (err) {
      this.error = err instanceof Error ? err.message : 'Failed to render chart';
      console.error('Plotly chart error:', err);
    }
  }

  render() {
    return html`
      ${this.loading ? html`
        <div class="loading-message">Loading chart...</div>
      ` : this.error ? html`
        <div class="error-message">Error: ${this.error}</div>
      ` : html`
        <div class="plotly-div"></div>
      `}
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    'plotly-chart': PlotlyChart;
  }
}