/**
 * Rich Component System for Vanna Agents
 *
 * Provides a generic component registry and rendering system that can display
 * any rich component sent from the Python backend.
 */

import { richComponentStyleText } from '../styles/rich-component-styles.js';

// Component interfaces matching Python backend
export interface RichComponent {
  id: string;
  type: string;
  lifecycle: 'create' | 'update' | 'replace' | 'remove';
  data: Record<string, any>;
  children: string[];
  timestamp: string;
  visible: boolean;
  interactive: boolean;
}

// Artifact event interfaces
export interface ArtifactOpenedEventDetail {
  // Core identification
  artifactId: string;

  // Artifact content
  content: string; // Full HTML/SVG/JS content
  type: 'html' | 'svg' | 'visualization' | 'interactive' | 'd3' | 'threejs';
  title?: string;
  description?: string;

  // Trigger context
  trigger: 'created' | 'user-action'; // How this event was fired

  // Control
  preventDefault: () => void; // Prevent default behavior

  // Helpers
  getStandaloneHTML: () => string; // Full page HTML with dependencies

  // Metadata
  timestamp: string;
}

declare global {
  interface GlobalEventHandlersEventMap {
    'artifact-opened': CustomEvent<ArtifactOpenedEventDetail>;
  }
}


const RICH_COMPONENT_STYLE_ATTR = 'data-vanna-rich-component-styles';

function ensureRichComponentStyles(container: HTMLElement): void {
  const doc = container.ownerDocument;
  if (!doc) {
    return;
  }

  if (container.querySelector(`style[${RICH_COMPONENT_STYLE_ATTR}]`)) {
    return;
  }

  const styleEl = doc.createElement('style');
  styleEl.setAttribute(RICH_COMPONENT_STYLE_ATTR, 'true');
  styleEl.textContent = richComponentStyleText;
  container.prepend(styleEl);
}

export interface ComponentUpdate {
  operation: 'create' | 'update' | 'replace' | 'remove' | 'reorder' | 'bulk_update';
  target_id: string;
  component?: RichComponent;
  updates?: Record<string, any>;
  position?: any;
  timestamp: string;
  batch_id?: string;
}

// Component renderer interface
export interface ComponentRenderer {
  render(component: RichComponent): HTMLElement;
  update(element: HTMLElement, component: RichComponent, updates?: Record<string, any>): void;
  remove(element: HTMLElement): void;
}

// Base component renderer with common functionality
export abstract class BaseComponentRenderer implements ComponentRenderer {
  abstract render(component: RichComponent): HTMLElement;

  update(element: HTMLElement, component: RichComponent, _updates?: Record<string, any>): void {
    // Default implementation - re-render completely
    const newElement = this.render(component);
    element.parentNode?.replaceChild(newElement, element);
  }

  remove(element: HTMLElement): void {
    element.remove();
  }

}

// Card component renderer
export class CardComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    console.log('🎴 CardComponentRenderer.render() called', {
      componentId: component.id,
      componentData: component.data,
      actions: component.data?.actions
    });

    const card = document.createElement('div');
    card.className = 'rich-component rich-card';
    card.dataset.componentId = component.id;

    const { title, content, subtitle, icon, status, actions = [], collapsible, collapsed } = component.data;

    console.log('🎴 Extracted actions:', actions, 'Length:', actions?.length);

    card.innerHTML = `
      <div class="card-header ${collapsible ? 'collapsible' : ''}">
        ${icon ? `<span class="card-icon">${icon}</span>` : ''}
        <div class="card-title-section">
          <h3 class="card-title">${title}</h3>
          ${subtitle ? `<p class="card-subtitle">${subtitle}</p>` : ''}
        </div>
        ${status ? `<span class="card-status status-${status}">${status}</span>` : ''}
        ${collapsible ? `<button class="card-toggle">${collapsed ? '▶' : '▼'}</button>` : ''}
      </div>
      <div class="card-content ${collapsed ? 'collapsed' : ''}">
        ${content}
      </div>
      ${actions && actions.length > 0 ? `
        <div class="card-actions">
          ${actions.map((action: any) => `
            <button class="card-action ${action.variant || 'secondary'}" data-action="${action.action}">
              ${action.label}
            </button>
          `).join('')}
        </div>
      ` : ''}
    `;


    // Add collapsible functionality
    if (collapsible) {
      const toggle = card.querySelector('.card-toggle') as HTMLButtonElement;
      const content = card.querySelector('.card-content') as HTMLElement;

      toggle?.addEventListener('click', () => {
        content.classList.toggle('collapsed');
        toggle.textContent = content.classList.contains('collapsed') ? '▶' : '▼';
      });
    }

    // Add click handlers for action buttons
    console.log('🎴 Checking if should add click handlers:', {
      hasActions: !!actions,
      actionsLength: actions?.length
    });

    if (actions && actions.length > 0) {
      const actionButtons = card.querySelectorAll('.card-action') as NodeListOf<HTMLButtonElement>;
      console.log('🎴 Found action buttons:', actionButtons.length);

      actionButtons.forEach((button, index) => {
        const action = actions[index];
        console.log(`🎴 Setting up listener for button ${index}:`, {
          hasAction: !!action,
          hasActionProperty: !!action?.action,
          action: action
        });

        if (action && action.action) {
          console.log('🎴 Adding click listener to button:', button);
          button.addEventListener('click', async () => {
            console.log('🔘 Card action button clicked:', action.label);
            console.log('   Sending action:', action.action);

            // Apply visual feedback
            button.disabled = true;
            button.classList.add('button-transitioning', 'button-clicked');

            // Find vanna-chat component and send message
            const vannaChat = document.querySelector('vanna-chat') as any;

            if (vannaChat && typeof vannaChat.sendMessage === 'function') {
              try {
                const success = await vannaChat.sendMessage(action.action);

                if (success) {
                  console.log('✅ Card action sent successfully');
                  // Keep button disabled after successful action
                } else {
                  console.error('❌ Failed to send card action');
                  // Re-enable button on failure
                  button.disabled = false;
                  button.classList.remove('button-transitioning', 'button-clicked');
                }
              } catch (error) {
                console.error('❌ Error sending card action:', error);
                // Re-enable button on error
                button.disabled = false;
                button.classList.remove('button-transitioning', 'button-clicked');
              }
            } else {
              console.warn('⚠️ vanna-chat component not found or sendMessage not available');
              button.disabled = false;
              button.classList.remove('button-transitioning', 'button-clicked');
            }
          });
        }
      });
    }

    return card;
  }

  update(element: HTMLElement, component: RichComponent, updates?: Record<string, any>): void {
    if (!updates) return super.update(element, component);

    // Optimized updates for common properties
    if (updates.title) {
      const titleEl = element.querySelector('.card-title');
      if (titleEl) titleEl.textContent = updates.title;
    }

    if (updates.content) {
      const contentEl = element.querySelector('.card-content');
      if (contentEl) contentEl.innerHTML = updates.content;
    }

    if (updates.status) {
      const statusEl = element.querySelector('.card-status');
      if (statusEl) {
        statusEl.className = `card-status status-${updates.status}`;
        statusEl.textContent = updates.status;
      }
    }

    // For complex updates, fall back to full re-render
    if (updates.actions || updates.collapsible) {
      super.update(element, component);
    }
  }
}

// Task list component renderer
export class TaskListComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = 'rich-component rich-task-list';
    container.dataset.componentId = component.id;

    const { title, tasks = [], show_progress, show_timestamps } = component.data;

    const completedTasks = tasks.filter((task: any) => task.status === 'completed').length;
    const progress = tasks.length > 0 ? (completedTasks / tasks.length) * 100 : 0;

    container.innerHTML = `
      <div class="task-list-header">
        <h3 class="task-list-title">${title}</h3>
        ${show_progress ? `
          <div class="task-list-progress">
            <span class="progress-text">${completedTasks}/${tasks.length} completed</span>
            <div class="progress-bar">
              <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
          </div>
        ` : ''}
      </div>
      <div class="task-list-items">
        ${tasks.map((task: any) => this.renderTask(task, show_timestamps)).join('')}
      </div>
    `;


    return container;
  }

  private renderTask(task: any, showTimestamps: boolean): string {
    const statusIcon = this.getStatusIcon(task.status);
    const progressBar = task.progress !== null && task.progress !== undefined ? `
      <div class="task-progress">
        <div class="task-progress-bar">
          <div class="task-progress-fill" style="width: ${task.progress * 100}%"></div>
        </div>
        <span class="task-progress-text">${Math.round(task.progress * 100)}%</span>
      </div>
    ` : '';

    return `
      <div class="task-item status-${task.status}" data-task-id="${task.id}">
        <div class="task-icon">${statusIcon}</div>
        <div class="task-content">
          <div class="task-title">${task.title}</div>
          ${task.description ? `<div class="task-description">${task.description}</div>` : ''}
          ${progressBar}
          ${showTimestamps && task.created_at ? `
            <div class="task-timestamp">
              Created: ${new Date(task.created_at).toLocaleString()}
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  private getStatusIcon(status: string): string {
    switch (status) {
      case 'completed': return '✅';
      case 'running': return '🔄';
      case 'failed': return '❌';
      default: return '⭕';
    }
  }
}

// Progress bar component renderer
export class ProgressBarComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = 'rich-component rich-progress-bar';
    container.dataset.componentId = component.id;

    const { value, label, show_percentage, status, animated } = component.data;
    const percentage = Math.round(value * 100);

    container.innerHTML = `
      <div class="progress-header">
        ${label ? `<span class="progress-label">${label}</span>` : ''}
        ${show_percentage ? `<span class="progress-percentage">${percentage}%</span>` : ''}
      </div>
      <div class="progress-track">
        <div class="progress-fill ${animated ? 'animated' : ''} ${status ? `status-${status}` : ''}"
             style="width: ${percentage}%"></div>
      </div>
    `;


    return container;
  }

  update(element: HTMLElement, component: RichComponent, updates?: Record<string, any>): void {
    if (!updates) return super.update(element, component);

    if (updates.value !== undefined) {
      const fill = element.querySelector('.progress-fill') as HTMLElement;
      const percentage = Math.round(updates.value * 100);

      if (fill) {
        fill.style.width = `${percentage}%`;
      }

      const percentageEl = element.querySelector('.progress-percentage');
      if (percentageEl) {
        percentageEl.textContent = `${percentage}%`;
      }
    }

    if (updates.label) {
      const labelEl = element.querySelector('.progress-label');
      if (labelEl) labelEl.textContent = updates.label;
    }

    if (updates.status) {
      const fill = element.querySelector('.progress-fill') as HTMLElement;
      if (fill) {
        fill.className = fill.className.replace(/status-\w+/, `status-${updates.status}`);
      }
    }
  }
}

// Notification component renderer
export class NotificationComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = 'rich-component rich-notification';
    container.dataset.componentId = component.id;

    const { message, title, level = 'info', icon, dismissible, auto_dismiss, actions = [] } = component.data;

    const levelIcon = icon || this.getLevelIcon(level);
    const dismissButton = dismissible ? `
      <button class="notification-dismiss" onclick="this.parentElement.remove()">×</button>
    ` : '';

    container.innerHTML = `
      <div class="notification-content level-${level}">
        ${levelIcon ? `<span class="notification-icon">${levelIcon}</span>` : ''}
        <div class="notification-body">
          ${title ? `<div class="notification-title">${title}</div>` : ''}
          <div class="notification-message">${message}</div>
        </div>
        ${actions.length > 0 ? `
          <div class="notification-actions">
            ${actions.map((action: any) => `
              <button class="notification-action ${action.variant || 'secondary'}" data-action="${action.action}">
                ${action.label}
              </button>
            `).join('')}
          </div>
        ` : ''}
        ${dismissButton}
      </div>
    `;

    // Auto-dismiss functionality
    if (auto_dismiss && component.data.auto_dismiss_delay) {
      setTimeout(() => {
        if (container.parentElement) {
          container.remove();
        }
      }, component.data.auto_dismiss_delay);
    }


    return container;
  }

  private getLevelIcon(level: string): string {
    switch (level) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      case 'info':
      default: return 'ℹ️';
    }
  }
}

// Status indicator component renderer
export class StatusIndicatorComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = 'rich-component rich-status-indicator';
    container.dataset.componentId = component.id;

    const { status, message, icon, pulse } = component.data;

    const statusIcon = icon || this.getStatusIcon(status);
    const pulseClass = pulse ? 'pulse' : '';

    container.innerHTML = `
      <div class="status-indicator-content status-${status} ${pulseClass}">
        <span class="status-icon">${statusIcon}</span>
        <span class="status-message">${message}</span>
      </div>
    `;


    return container;
  }

  private getStatusIcon(status: string): string {
    switch (status) {
      case 'loading': return '🔄';
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return 'ℹ️';
    }
  }

  update(element: HTMLElement, component: RichComponent, updates?: Record<string, any>): void {
    if (!updates) return super.update(element, component);

    const content = element.querySelector('.status-indicator-content');
    if (content && updates.status) {
      content.className = content.className.replace(/status-\w+/, `status-${updates.status}`);
    }

    if (updates.pulse !== undefined) {
      const content = element.querySelector('.status-indicator-content');
      if (content) {
        if (updates.pulse) {
          content.classList.add('pulse');
        } else {
          content.classList.remove('pulse');
        }
      }
    }

    if (updates.message) {
      const messageEl = element.querySelector('.status-message');
      if (messageEl) {
        messageEl.textContent = updates.message;
      }
    }
  }
}

// DataFrame component renderer
export class DataFrameComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = 'rich-component rich-dataframe';
    container.dataset.componentId = component.id;

    const {
      data = [],
      columns = [],
      title,
      description,
      row_count = 0,
      column_count = 0,
      max_rows_displayed = 100,
      searchable = true,
      sortable = true,
      filterable = true,
      exportable = true,
      striped = true,
      bordered = true,
      compact = false,
      column_types = {}
    } = component.data;

    // Limit displayed rows
    const displayedData = data.slice(0, max_rows_displayed);
    const hasMoreRows = data.length > max_rows_displayed;

    let headerHTML = '';
    if (title || description) {
      headerHTML = `
        <div class="dataframe-header">
          ${title ? `<h3 class="dataframe-title">${title}</h3>` : ''}
          ${description ? `<p class="dataframe-description">${description}</p>` : ''}
          <div class="dataframe-meta">
            <span class="row-count">${row_count} rows</span>
            <span class="column-count">${column_count} columns</span>
          </div>
        </div>
      `;
    }

    let actionsHTML = '';
    if (searchable || exportable || filterable) {
      actionsHTML = `
        <div class="dataframe-actions">
          ${searchable ? `
            <div class="dataframe-search">
              <input type="text" placeholder="Search..." class="search-input">
            </div>
          ` : ''}
          ${exportable ? `
            <button class="export-btn" title="Export to CSV">📥 Export</button>
          ` : ''}
        </div>
      `;
    }

    let tableHTML = '';
    if (columns.length > 0 && displayedData.length > 0) {
      const tableClasses = [
        'dataframe-table',
        striped ? 'striped' : '',
        bordered ? 'bordered' : '',
        compact ? 'compact' : ''
      ].filter(Boolean).join(' ');

      tableHTML = `
        <div class="dataframe-table-container">
          <table class="${tableClasses}">
            <thead>
              <tr>
                ${columns.map((col: string) => `
                  <th class="${sortable ? 'sortable' : ''}" data-column="${col}">
                    ${col}
                    ${sortable ? '<span class="sort-indicator"></span>' : ''}
                  </th>
                `).join('')}
              </tr>
            </thead>
            <tbody>
              ${displayedData.map((row: any) => `
                <tr>
                  ${columns.map((col: string) => {
                    const value = row[col];
                    const columnType = column_types[col] || 'string';
                    const formattedValue = this.formatCellValue(value, columnType);
                    return `<td class="cell-${columnType}">${formattedValue}</td>`;
                  }).join('')}
                </tr>
              `).join('')}
            </tbody>
          </table>
          ${hasMoreRows ? `
            <div class="dataframe-truncated">
              <em>Showing ${max_rows_displayed} of ${row_count} rows</em>
            </div>
          ` : ''}
        </div>
      `;
    } else {
      tableHTML = `
        <div class="dataframe-empty">
          <p>No data to display</p>
        </div>
      `;
    }

    container.innerHTML = `
      ${headerHTML}
      ${actionsHTML}
      ${tableHTML}
    `;


    // Add event listeners
    this.attachEventListeners(container, displayedData, columns);

    return container;
  }

  private formatCellValue(value: any, columnType: string): string {
    if (value === null || value === undefined) {
      return '<em class="null-value">NULL</em>';
    }

    switch (columnType) {
      case 'number':
        return typeof value === 'number' ? value.toLocaleString() : String(value);
      case 'date':
        try {
          return new Date(value).toLocaleDateString();
        } catch {
          return String(value);
        }
      case 'boolean':
        return value ? '✓' : '✗';
      default:
        return this.escapeHtml(String(value));
    }
  }

  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  private attachEventListeners(container: HTMLElement, data: any[], columns: string[]): void {
    // Search functionality
    const searchInput = container.querySelector('.search-input') as HTMLInputElement;
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const searchTerm = (e.target as HTMLInputElement).value.toLowerCase();
        this.filterTable(container, data, columns, searchTerm);
      });
    }

    // Export functionality
    const exportBtn = container.querySelector('.export-btn') as HTMLButtonElement;
    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        this.exportToCSV(data, columns);
      });
    }

    // Sort functionality
    const sortableHeaders = container.querySelectorAll('th.sortable');
    sortableHeaders.forEach(header => {
      header.addEventListener('click', (e) => {
        const column = (e.currentTarget as HTMLElement).dataset.column;
        if (column) {
          this.sortTable(container, data, columns, column);
        }
      });
    });
  }

  private filterTable(container: HTMLElement, data: any[], columns: string[], searchTerm: string): void {
    const tbody = container.querySelector('tbody');
    if (!tbody) return;

    const filteredData = data.filter(row => {
      return columns.some(col => {
        const value = String(row[col] || '').toLowerCase();
        return value.includes(searchTerm);
      });
    });

    tbody.innerHTML = filteredData.map(row => `
      <tr>
        ${columns.map(col => {
          const value = row[col];
          const formattedValue = this.formatCellValue(value, 'string');
          return `<td>${formattedValue}</td>`;
        }).join('')}
      </tr>
    `).join('');
  }

  private sortTable(container: HTMLElement, data: any[], columns: string[], column: string): void {
    const tbody = container.querySelector('tbody');
    const header = container.querySelector(`th[data-column="${column}"]`) as HTMLElement;
    if (!tbody || !header) return;

    // Determine sort direction
    const currentSort = header.dataset.sortDirection || 'none';
    const newSort = currentSort === 'asc' ? 'desc' : 'asc';

    // Clear all sort indicators
    container.querySelectorAll('th[data-sort-direction]').forEach(h => {
      (h as HTMLElement).removeAttribute('data-sort-direction');
      const indicator = h.querySelector('.sort-indicator');
      if (indicator) indicator.textContent = '';
    });

    // Set new sort direction
    header.dataset.sortDirection = newSort;
    const indicator = header.querySelector('.sort-indicator');
    if (indicator) {
      indicator.textContent = newSort === 'asc' ? '↑' : '↓';
    }

    // Sort data
    const sortedData = [...data].sort((a, b) => {
      const aVal = a[column];
      const bVal = b[column];

      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return newSort === 'asc' ? aVal - bVal : bVal - aVal;
      }

      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      const comparison = aStr.localeCompare(bStr);
      return newSort === 'asc' ? comparison : -comparison;
    });

    // Update table
    tbody.innerHTML = sortedData.map(row => `
      <tr>
        ${columns.map(col => {
          const value = row[col];
          const formattedValue = this.formatCellValue(value, 'string');
          return `<td>${formattedValue}</td>`;
        }).join('')}
      </tr>
    `).join('');
  }

  private exportToCSV(data: any[], columns: string[]): void {
    const csvContent = [
      columns.join(','),
      ...data.map(row =>
        columns.map(col => {
          const value = row[col];
          const strValue = value === null || value === undefined ? '' : String(value);
          // Escape quotes and wrap in quotes if contains comma, quote, or newline
          if (strValue.includes(',') || strValue.includes('"') || strValue.includes('\n')) {
            return `"${strValue.replace(/"/g, '""')}"`;
          }
          return strValue;
        }).join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'data.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

// Text component renderer
export class TextComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = 'rich-component rich-text';
    container.dataset.componentId = component.id;

    const {
      content,
      markdown = false,
      code_language,
      font_size,
      font_weight,
      text_align
    } = component.data;

    // Apply text styling
    let textStyle = '';
    if (font_size) textStyle += `font-size: ${font_size}; `;
    if (font_weight) textStyle += `font-weight: ${font_weight}; `;
    if (text_align) textStyle += `text-align: ${text_align}; `;

    if (code_language) {
      // Code block
      container.innerHTML = `
        <pre class="text-code" style="${textStyle}"><code class="language-${code_language}">${this.escapeHtml(content)}</code></pre>
      `;
    } else if (markdown) {
      // Markdown text (simple implementation)
      container.innerHTML = `
        <div class="text-markdown" style="${textStyle}">${this.renderMarkdown(content)}</div>
      `;
    } else {
      // Plain text
      container.innerHTML = `
        <div class="text-content" style="${textStyle}">${this.escapeHtml(content)}</div>
      `;
    }


    return container;
  }

  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  private renderMarkdown(text: string): string {
    // Simple markdown rendering - just basic formatting
    return text
      .replace(/^## (.*$)/gm, '<h2>$1</h2>')
      .replace(/^# (.*$)/gm, '<h1>$1</h1>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^- (.*$)/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/^(?!<[h|u|l])(.+)$/gm, '<p>$1</p>');
  }
}

// Primitive Component Renderers (Domain-Agnostic)

// Status card component renderer
export class StatusCardComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = 'rich-component rich-status-card';
    container.dataset.componentId = component.id;

    const { title, status, description, icon, actions = [], collapsible, collapsed, metadata = {} } = component.data;

    const statusIcon = icon || this.getStatusIcon(status);
    const hasMetadata = Object.keys(metadata).length > 0;

    container.innerHTML = `
      <div class="status-card-header ${collapsible ? 'collapsible' : ''}">
        <div class="status-card-icon">${statusIcon}</div>
        <div class="status-card-title-section">
          <h3 class="status-card-title">${title}</h3>
          <span class="status-card-badge status-${status}">${status}</span>
        </div>
        ${collapsible ? `<button class="status-card-toggle">${collapsed ? '▶' : '▼'}</button>` : ''}
      </div>
      ${description ? `
        <div class="status-card-content ${collapsed ? 'collapsed' : ''}">
          ${description}
        </div>
      ` : ''}
      ${hasMetadata ? `
        <details class="status-card-metadata">
          <summary class="status-card-metadata-summary">Parameters</summary>
          <div class="status-card-metadata-content">
            ${this.renderMetadataTable(metadata)}
          </div>
        </details>
      ` : ''}
      ${actions.length > 0 ? `
        <div class="status-card-actions">
          ${actions.map((action: any) => `
            <button class="status-card-action ${action.variant || 'secondary'}" data-action="${action.action}">
              ${action.label}
            </button>
          `).join('')}
        </div>
      ` : ''}
    `;

    // Add collapsible functionality
    if (collapsible) {
      const toggle = container.querySelector('.status-card-toggle') as HTMLButtonElement;
      const content = container.querySelector('.status-card-content') as HTMLElement;

      toggle?.addEventListener('click', () => {
        if (content) {
          content.classList.toggle('collapsed');
          toggle.textContent = content.classList.contains('collapsed') ? '▶' : '▼';
        }
      });
    }

    return container;
  }

  private renderMetadataTable(metadata: Record<string, any>): string {
    const rows = Object.entries(metadata).map(([key, value]) => {
      const formattedValue = this.formatMetadataValue(value);
      return `
        <tr>
          <td class="metadata-key">${this.escapeHtml(key)}</td>
          <td class="metadata-value">${formattedValue}</td>
        </tr>
      `;
    }).join('');

    return `
      <table class="metadata-table">
        <thead>
          <tr>
            <th>Parameter</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  }

  private formatMetadataValue(value: any): string {
    if (value === null) {
      return '<span class="metadata-null">null</span>';
    }
    if (value === undefined) {
      return '<span class="metadata-undefined">undefined</span>';
    }
    if (typeof value === 'boolean') {
      return `<span class="metadata-boolean">${value}</span>`;
    }
    if (typeof value === 'number') {
      return `<span class="metadata-number">${value}</span>`;
    }
    if (typeof value === 'string') {
      return `<span class="metadata-string">${this.escapeHtml(value)}</span>`;
    }
    if (Array.isArray(value) || typeof value === 'object') {
      return `<pre class="metadata-json">${JSON.stringify(value, null, 2)}</pre>`;
    }
    return this.escapeHtml(String(value));
  }

  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  private getStatusIcon(status: string): string {
    switch (status) {
      case 'pending': return '⏳';
      case 'running': return '⚙️';
      case 'completed': return '✅';
      case 'success': return '✅';
      case 'failed': return '❌';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      default: return 'ℹ️';
    }
  }
}

// Progress display component renderer
export class ProgressDisplayComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = 'rich-component rich-progress-display';
    container.dataset.componentId = component.id;

    const { label, value, description, status, show_percentage, animated, indeterminate } = component.data;
    const percentage = Math.round(value * 100);

    container.innerHTML = `
      <div class="progress-display-container">
        <div class="progress-display-header">
          <span class="progress-display-label">${label}</span>
          ${show_percentage && !indeterminate ? `<span class="progress-display-percentage">${percentage}%</span>` : ''}
        </div>
        <div class="progress-display-track">
          <div class="progress-display-fill ${animated ? 'animated' : ''} ${status ? `status-${status}` : ''} ${indeterminate ? 'indeterminate' : ''}"
               style="width: ${indeterminate ? '100' : percentage}%"></div>
        </div>
        ${description ? `<div class="progress-display-description">${description}</div>` : ''}
      </div>
    `;

    return container;
  }
}

// Log viewer component renderer
export class LogViewerComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = 'rich-component rich-log-viewer';
    container.dataset.componentId = component.id;

    const { title, entries = [], searchable, show_timestamps, auto_scroll } = component.data;

    container.innerHTML = `
      <div class="log-viewer-container">
        <div class="log-viewer-header">
          <h3 class="log-viewer-title">${title}</h3>
          ${searchable ? `
            <div class="log-viewer-search">
              <input type="text" placeholder="Search logs..." class="log-search-input">
            </div>
          ` : ''}
        </div>
        <div class="log-viewer-content ${auto_scroll ? 'auto-scroll' : ''}">
          ${entries.map((entry: any) => `
            <div class="log-entry log-${entry.level}">
              ${show_timestamps ? `<span class="log-timestamp">${new Date(entry.timestamp).toLocaleTimeString()}</span>` : ''}
              <span class="log-level">[${entry.level.toUpperCase()}]</span>
              <span class="log-message">${entry.message}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;

    // Auto-scroll to bottom if enabled
    if (auto_scroll) {
      const content = container.querySelector('.log-viewer-content');
      if (content) {
        content.scrollTop = content.scrollHeight;
      }
    }

    return container;
  }
}

// Badge component renderer
export class BadgeComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('span');
    container.className = `rich-component rich-badge badge-${component.data.variant} badge-${component.data.size}`;
    container.dataset.componentId = component.id;

    const { text, icon } = component.data;

    container.innerHTML = `
      ${icon ? `<span class="badge-icon">${icon}</span>` : ''}
      <span class="badge-text">${text}</span>
    `;

    return container;
  }
}

// Icon text component renderer
export class IconTextComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = `rich-component rich-icon-text icon-text-${component.data.variant} icon-text-${component.data.size} icon-text-${component.data.alignment}`;
    container.dataset.componentId = component.id;

    const { icon, text } = component.data;

    container.innerHTML = `
      <span class="icon-text-icon">${icon}</span>
      <span class="icon-text-text">${text}</span>
    `;

    return container;
  }
}

// Button component renderer
export class ButtonComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const button = document.createElement('button');
    button.className = `rich-component rich-button button-${component.data.variant} button-${component.data.size}`;
    button.dataset.componentId = component.id;

    const { label, action, disabled, icon, icon_position, full_width, loading } = component.data;

    if (disabled || loading) {
      button.disabled = true;
    }

    if (full_width) {
      button.classList.add('button-full-width');
    }

    if (loading) {
      button.classList.add('button-loading');
    }

    // Build button content
    let buttonContent = '';
    if (loading) {
      buttonContent = `<span class="button-spinner">⏳</span><span class="button-label">${label}</span>`;
    } else if (icon) {
      if (icon_position === 'right') {
        buttonContent = `<span class="button-label">${label}</span><span class="button-icon">${icon}</span>`;
      } else {
        buttonContent = `<span class="button-icon">${icon}</span><span class="button-label">${label}</span>`;
      }
    } else {
      buttonContent = `<span class="button-label">${label}</span>`;
    }

    button.innerHTML = buttonContent;

    // Add click handler
    if (action && !disabled && !loading) {
      button.addEventListener('click', async () => {
        console.log('🔘 Button clicked:', label);
        console.log('   Sending action:', action);

        // Apply visual feedback immediately
        button.disabled = true;
        button.classList.add('button-transitioning', 'button-clicked');

        // Find vanna-chat component and send message with button action
        const vannaChat = document.querySelector('vanna-chat') as any;
        console.log('   Found vanna-chat:', !!vannaChat);

        if (vannaChat && typeof vannaChat.sendMessage === 'function') {
          console.log('   Calling sendMessage...');
          try {
            const success = await vannaChat.sendMessage(action);
            if (success) {
              console.log('   ✓ Message sent successfully');
            } else {
              console.log('   ✗ Message failed, restoring button state');
              // Restore button state if it wasn't originally disabled
              if (!disabled) {
                button.disabled = false;
              }
              button.classList.remove('button-transitioning', 'button-clicked');
            }
          } catch (error) {
            console.error('   ✗ Message failed with error:', error);
            // Restore button state if it wasn't originally disabled
            if (!disabled) {
              button.disabled = false;
            }
            button.classList.remove('button-transitioning', 'button-clicked');
          }
        } else {
          console.error('   ✗ vanna-chat not found or sendMessage not available');
          // Restore button state if it wasn't originally disabled
          if (!disabled) {
            button.disabled = false;
          }
          button.classList.remove('button-transitioning', 'button-clicked');
        }
      });
    }

    return button;
  }

  update(element: HTMLElement, component: RichComponent, updates?: Record<string, any>): void {
    if (!updates) return super.update(element, component);

    const button = element as HTMLButtonElement;

    if (updates.disabled !== undefined) {
      button.disabled = updates.disabled;
    }

    if (updates.loading !== undefined) {
      button.disabled = updates.loading;
      if (updates.loading) {
        button.classList.add('button-loading');
      } else {
        button.classList.remove('button-loading');
      }
    }

    if (updates.label || updates.icon || updates.icon_position) {
      // Re-render content
      super.update(element, component);
    }
  }
}

// Button group component renderer
export class ButtonGroupComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = `rich-component rich-button-group button-group-${component.data.orientation} button-group-spacing-${component.data.spacing} button-group-align-${component.data.align}`;
    container.dataset.componentId = component.id;

    const { buttons = [], full_width } = component.data;

    if (full_width) {
      container.classList.add('button-group-full-width');
    }

    // Render each button
    buttons.forEach((buttonConfig: any, index: number) => {
      const button = document.createElement('button');
      button.className = `rich-button button-${buttonConfig.variant || 'secondary'} button-${buttonConfig.size || 'medium'}`;
      button.dataset.buttonIndex = String(index);

      // Store original disabled state
      if (buttonConfig.disabled) {
        button.disabled = true;
        button.dataset.originallyDisabled = 'true';
      } else {
        button.dataset.originallyDisabled = 'false';
      }

      // Build button content
      let buttonContent = '';
      if (buttonConfig.icon) {
        if (buttonConfig.icon_position === 'right') {
          buttonContent = `<span class="button-label">${buttonConfig.label}</span><span class="button-icon">${buttonConfig.icon}</span>`;
        } else {
          buttonContent = `<span class="button-icon">${buttonConfig.icon}</span><span class="button-label">${buttonConfig.label}</span>`;
        }
      } else {
        buttonContent = `<span class="button-label">${buttonConfig.label}</span>`;
      }

      button.innerHTML = buttonContent;

      // Add click handler with enhanced functionality
      if (buttonConfig.action && !buttonConfig.disabled) {
        button.addEventListener('click', async () => {
          console.log('🔘 Button Group button clicked:', buttonConfig.label);
          console.log('   Button index:', index);
          console.log('   Sending action:', buttonConfig.action);

          // Immediately apply visual changes to all buttons in the group
          this.applyButtonGroupClickState(container, index);

          // Find vanna-chat component and send message with button action
          const vannaChat = document.querySelector('vanna-chat') as any;
          console.log('   Found vanna-chat:', !!vannaChat);

          if (vannaChat && typeof vannaChat.sendMessage === 'function') {
            console.log('   Calling sendMessage...');
            try {
              const success = await vannaChat.sendMessage(buttonConfig.action);
              if (success) {
                console.log('   ✓ Message sent successfully');
              } else {
                console.log('   ✗ Message failed, restoring button state');
                this.restoreButtonGroupState(container);
              }
            } catch (error) {
              console.error('   ✗ Message failed with error:', error);
              this.restoreButtonGroupState(container);
            }
          } else {
            console.error('   ✗ vanna-chat not found or sendMessage not available');
            this.restoreButtonGroupState(container);
          }
        });
      }

      container.appendChild(button);
    });

    return container;
  }

  private applyButtonGroupClickState(container: HTMLElement, clickedIndex: number): void {
    const buttons = container.querySelectorAll('button') as NodeListOf<HTMLButtonElement>;
    
    buttons.forEach((button, index) => {
      // Disable all buttons
      button.disabled = true;
      
      // Add transition class for animation
      button.classList.add('button-transitioning');
      
      if (index === clickedIndex) {
        // Highlight the clicked button
        button.classList.add('button-clicked', 'button-highlighted');
      } else {
        // Gray out other buttons
        button.classList.add('button-grayed-out');
      }
    });
  }

  private restoreButtonGroupState(container: HTMLElement): void {
    const buttons = container.querySelectorAll('button') as NodeListOf<HTMLButtonElement>;
    
    buttons.forEach((button) => {
      // Re-enable buttons (unless they were originally disabled)
      const originallyDisabled = button.dataset.originallyDisabled === 'true';
      if (!originallyDisabled) {
        button.disabled = false;
      }
      
      // Remove all state classes
      button.classList.remove(
        'button-clicked', 
        'button-highlighted', 
        'button-grayed-out',
        'button-transitioning'
      );
    });
  }
}

// Chart component renderer (for Plotly charts)
export class ChartComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = 'rich-component rich-chart';
    container.dataset.componentId = component.id;

    // The ChartComponent.data field contains the Plotly figure directly
    // Structure: component.data = { data: [...traces...], layout: {...}, title: "...", config: {...} }
    const { data: plotlyData, layout, title, config = {} } = component.data;

    console.log('ChartComponentRenderer: Received component.data:', component.data);
    console.log('ChartComponentRenderer: plotlyData:', plotlyData);
    console.log('ChartComponentRenderer: layout:', layout);

    // Check if we have a valid Plotly figure structure
    if (plotlyData && Array.isArray(plotlyData) && layout) {
      // Create plotly-chart web component
      const chartElement = document.createElement('plotly-chart') as any;

      // Set theme to match current theme
      const vannaChat = document.querySelector('vanna-chat');
      if (vannaChat) {
        chartElement.theme = vannaChat.getAttribute('theme') || 'dark';
      }

      // Wrap in container with optional title
      if (title) {
        container.innerHTML = `
          <div class="chart-header">
            <h3 class="chart-title">${title}</h3>
          </div>
          <div class="chart-content"></div>
        `;
        container.querySelector('.chart-content')?.appendChild(chartElement);
      } else {
        container.appendChild(chartElement);
      }

      // Set data AFTER the element is in the DOM
      // This ensures the web component is fully initialized
      requestAnimationFrame(() => {
        chartElement.data = plotlyData; // Plotly traces (array)
        chartElement.layout = layout; // Plotly layout (object)
        chartElement.config = config;

        console.log('ChartComponentRenderer: Set properties after DOM attachment');
        console.log('ChartComponentRenderer: chartElement.data:', chartElement.data);
        console.log('ChartComponentRenderer: chartElement.layout:', chartElement.layout);
      });
    } else {
      // Fallback for invalid chart data
      container.innerHTML = `
        <div class="chart-error">
          <p>Invalid chart data format</p>
          <pre>${JSON.stringify(component.data, null, 2).substring(0, 200)}...</pre>
        </div>
      `;
    }

    return container;
  }
}

// Artifact component renderer
export class ArtifactComponentRenderer extends BaseComponentRenderer {
  private defaultPrevented = false;

  render(component: RichComponent): HTMLElement {
    console.log('🔧 ArtifactComponentRenderer.render called with:', component);

    const container = document.createElement('div');
    container.className = 'rich-component rich-artifact';
    container.dataset.componentId = component.id;
    container.dataset.artifactId = component.data.artifact_id;

    const {
      content,
      artifact_type,
      title,
      description,
      editable,
      fullscreen_capable,
      external_renderable
    } = component.data;

    // Create artifact preview and controls
    container.innerHTML = `
      <div class="artifact-header">
        <div class="artifact-meta">
          <h3 class="artifact-title">${title || 'Artifact'}</h3>
          ${description ? `<p class="artifact-description">${description}</p>` : ''}
          <span class="artifact-type-badge">${artifact_type}</span>
        </div>
        <div class="artifact-controls">
          ${editable ? '<button class="artifact-btn edit-btn" title="Edit">✏️</button>' : ''}
          ${fullscreen_capable ? '<button class="artifact-btn fullscreen-btn" title="Fullscreen">⛶</button>' : ''}
          ${external_renderable ? '<button class="artifact-btn external-btn" title="Open External">🔗</button>' : ''}
        </div>
      </div>
      <div class="artifact-preview">
        <iframe class="artifact-iframe" sandbox="allow-scripts allow-same-origin" srcdoc="${this.escapeHtml(content)}"></iframe>
      </div>
    `;

    // Attach event listeners
    this.attachEventListeners(container, component);

    // Fire artifact-opened event for creation
    const shouldRenderInChat = this.fireArtifactOpenedEvent(component, 'created', container);

    // If default was prevented, show a placeholder instead
    if (!shouldRenderInChat) {
      container.innerHTML = `
        <div class="artifact-placeholder">
          <div class="placeholder-content">
            <span class="placeholder-icon">🎨</span>
            <div class="placeholder-text">
              <strong>${title || 'Artifact'}</strong> opened externally
              <div class="placeholder-type">${artifact_type}</div>
            </div>
            <button class="placeholder-reopen" title="Reopen">↗</button>
          </div>
        </div>
      `;

      // Add reopen functionality
      const reopenBtn = container.querySelector('.placeholder-reopen') as HTMLButtonElement;
      if (reopenBtn) {
        reopenBtn.addEventListener('click', () => {
          this.fireArtifactOpenedEvent(component, 'user-action', container);
        });
      }
    }

    return container;
  }

  private attachEventListeners(container: HTMLElement, component: RichComponent): void {
    // External button click
    const externalBtn = container.querySelector('.external-btn') as HTMLButtonElement;
    if (externalBtn) {
      externalBtn.addEventListener('click', () => {
        this.fireArtifactOpenedEvent(component, 'user-action', container);
      });
    }

    // Fullscreen button click
    const fullscreenBtn = container.querySelector('.fullscreen-btn') as HTMLButtonElement;
    if (fullscreenBtn) {
      fullscreenBtn.addEventListener('click', () => {
        this.openFullscreen(component);
      });
    }

    // Edit button click (placeholder for future implementation)
    const editBtn = container.querySelector('.edit-btn') as HTMLButtonElement;
    if (editBtn) {
      editBtn.addEventListener('click', () => {
        this.openEditor(component);
      });
    }
  }

  private fireArtifactOpenedEvent(component: RichComponent, trigger: 'created' | 'user-action', container: HTMLElement): boolean {
    console.log('🎯 fireArtifactOpenedEvent called:', { trigger, artifactId: component.data.artifact_id });

    this.defaultPrevented = false;

    const eventDetail: ArtifactOpenedEventDetail = {
      artifactId: component.data.artifact_id,
      content: component.data.content,
      type: component.data.artifact_type,
      title: component.data.title,
      description: component.data.description,
      trigger,
      preventDefault: () => {
        console.log('🛑 preventDefault called!');
        this.defaultPrevented = true;
      },
      getStandaloneHTML: () => this.generateStandaloneHTML(component),
      timestamp: new Date().toISOString()
    };

    const event = new CustomEvent('artifact-opened', {
      detail: eventDetail,
      bubbles: true,
      cancelable: true
    });

    console.log('📡 Dispatching artifact-opened event:', event);

    // Fire the event from the container element (should bubble up to vanna-chat)
    container.dispatchEvent(event);

    // Also dispatch directly on the vanna-chat element as backup
    const vannaChat = container.closest('vanna-chat');
    if (vannaChat) {
      console.log('📡 Also dispatching on vanna-chat element');
      vannaChat.dispatchEvent(new CustomEvent('artifact-opened', {
        detail: eventDetail,
        bubbles: true,
        cancelable: true
      }));
    }

    console.log('📨 Event dispatched. defaultPrevented:', this.defaultPrevented);

    // Handle default behavior if not prevented and user triggered
    if (!this.defaultPrevented && trigger === 'user-action') {
      this.handleDefaultAction(component);
    }

    // Return whether we should render in chat (true if default not prevented)
    return !this.defaultPrevented;
  }

  private generateStandaloneHTML(component: RichComponent): string {
    const { content, title, dependencies = [] } = component.data;

    let dependenciesHTML = '';

    // Add common CDN links for dependencies
    if (dependencies.includes('d3')) {
      dependenciesHTML += '<script src="https://d3js.org/d3.v7.min.js"></script>\n';
    }
    if (dependencies.includes('plotly')) {
      dependenciesHTML += '<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>\n';
    }
    if (dependencies.includes('three') || dependencies.includes('threejs')) {
      dependenciesHTML += '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>\n';
    }

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title || 'Artifact'}</title>
    ${dependenciesHTML}
    <style>
        body {
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .artifact-container {
            width: 100%;
            min-height: 100vh;
        }
    </style>
</head>
<body>
    <div class="artifact-container">
        ${content}
    </div>
</body>
</html>`;
  }

  private handleDefaultAction(component: RichComponent): void {
    // Default action: open in new window
    const newWindow = window.open('', '_blank', 'width=800,height=600');
    if (newWindow) {
      newWindow.document.write(this.generateStandaloneHTML(component));
      newWindow.document.close();
    }
  }

  private openFullscreen(component: RichComponent): void {
    // Create fullscreen overlay
    const overlay = document.createElement('div');
    overlay.className = 'artifact-fullscreen-overlay';
    overlay.innerHTML = `
      <div class="fullscreen-header">
        <h3>${component.data.title || 'Artifact'}</h3>
        <button class="close-fullscreen">✕</button>
      </div>
      <div class="fullscreen-content">
        <iframe class="fullscreen-iframe" sandbox="allow-scripts allow-same-origin" srcdoc="${this.escapeHtml(component.data.content)}"></iframe>
      </div>
    `;

    // Add styles
    overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: white;
      z-index: 10000;
      display: flex;
      flex-direction: column;
    `;

    const header = overlay.querySelector('.fullscreen-header') as HTMLElement;
    header.style.cssText = `
      padding: 16px;
      border-bottom: 1px solid #eee;
      display: flex;
      justify-content: space-between;
      align-items: center;
    `;

    const content = overlay.querySelector('.fullscreen-content') as HTMLElement;
    content.style.cssText = `
      flex: 1;
      padding: 16px;
    `;

    const iframe = overlay.querySelector('.fullscreen-iframe') as HTMLIFrameElement;
    iframe.style.cssText = `
      width: 100%;
      height: 100%;
      border: none;
    `;

    // Close button functionality
    const closeBtn = overlay.querySelector('.close-fullscreen') as HTMLButtonElement;
    closeBtn.addEventListener('click', () => {
      document.body.removeChild(overlay);
    });

    // Escape key to close
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        document.body.removeChild(overlay);
        document.removeEventListener('keydown', handleEscape);
      }
    };
    document.addEventListener('keydown', handleEscape);

    document.body.appendChild(overlay);
  }

  private openEditor(component: RichComponent): void {
    // Placeholder for future editor implementation
    console.log('Editor functionality not yet implemented for artifact:', component.data.artifact_id);
  }

  private escapeHtml(html: string): string {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML.replace(/"/g, '&quot;');
  }
}

// User message component renderer
export class UserMessageComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const messageEl = document.createElement('vanna-message');
    messageEl.setAttribute('theme', 'light'); // Could be made dynamic
    messageEl.dataset.componentId = component.id;
    
    // Set properties for vanna-message
    (messageEl as any).content = component.data.content || '';
    (messageEl as any).type = 'user';
    (messageEl as any).timestamp = Date.parse(component.timestamp);
    
    return messageEl;
  }
}

// Assistant message component renderer  
export class AssistantMessageComponentRenderer extends BaseComponentRenderer {
  render(component: RichComponent): HTMLElement {
    const messageEl = document.createElement('vanna-message');
    messageEl.setAttribute('theme', 'light'); // Could be made dynamic
    messageEl.dataset.componentId = component.id;
    
    // Set properties for vanna-message
    (messageEl as any).content = component.data.content || '';
    (messageEl as any).type = 'assistant';
    (messageEl as any).timestamp = Date.parse(component.timestamp);
    
    return messageEl;
  }
}

// Component registry for managing all component types
export class ComponentRegistry {
  private renderers: Map<string, ComponentRenderer> = new Map();

  constructor() {
    // Register primitive component renderers (domain-agnostic)
    this.register('status_card', new StatusCardComponentRenderer());
    this.register('progress_display', new ProgressDisplayComponentRenderer());
    this.register('log_viewer', new LogViewerComponentRenderer());
    this.register('badge', new BadgeComponentRenderer());
    this.register('icon_text', new IconTextComponentRenderer());

    // Register existing component renderers
    this.register('card', new CardComponentRenderer());
    this.register('task_list', new TaskListComponentRenderer());
    this.register('progress_bar', new ProgressBarComponentRenderer());
    this.register('notification', new NotificationComponentRenderer());
    this.register('status_indicator', new StatusIndicatorComponentRenderer());
    this.register('text', new TextComponentRenderer());
    this.register('dataframe', new DataFrameComponentRenderer());
    this.register('chart', new ChartComponentRenderer());

    // Register interactive component renderers
    this.register('button', new ButtonComponentRenderer());
    this.register('button_group', new ButtonGroupComponentRenderer());

    // Register artifact component renderer
    this.register('artifact', new ArtifactComponentRenderer());

    // Register message component renderers
    this.register('user-message', new UserMessageComponentRenderer());
    this.register('assistant-message', new AssistantMessageComponentRenderer());
  }

  register(type: string, renderer: ComponentRenderer): void {
    this.renderers.set(type, renderer);
  }

  render(component: RichComponent): HTMLElement {
    // Check if this is a component that should use web components
    const webComponentTag = this.getWebComponentTag(component.type);
    if (webComponentTag) {
      return this.renderWebComponent(webComponentTag, component);
    }

    // Use the old renderer system for other components
    const renderer = this.renderers.get(component.type);
    if (!renderer) {
      return this.renderFallback(component);
    }
    return renderer.render(component);
  }

  private getWebComponentTag(type: string): string | null {
    const mapping: Record<string, string> = {
      'card': 'rich-card',
      'task_list': 'rich-task-list',
      'progress_bar': 'rich-progress-bar',
      // We'll add more mappings as we convert other components
    };
    return mapping[type] || null;
  }

  private renderWebComponent(tagName: string, component: RichComponent): HTMLElement {
    const element = document.createElement(tagName) as any;

    // Set properties based on component data
    Object.keys(component.data).forEach(key => {
      if (key === 'actions' && Array.isArray(component.data[key])) {
        element.actions = component.data[key];
      } else {
        element[key] = component.data[key];
      }
    });

    // Set theme to match the parent VannaChat theme
    element.setAttribute('theme', this.getCurrentTheme());


    return element;
  }

  private getCurrentTheme(): string {
    // Try to get theme from the parent VannaChat component
    const vannaChat = document.querySelector('vanna-chat');
    if (vannaChat) {
      return vannaChat.getAttribute('theme') || 'dark';
    }
    return 'dark';
  }


  update(element: HTMLElement, component: RichComponent, updates?: Record<string, any>): void {
    const renderer = this.renderers.get(component.type);
    if (renderer) {
      renderer.update(element, component, updates);
    }
  }

  remove(element: HTMLElement): void {
    element.remove();
  }

  private renderFallback(component: RichComponent): HTMLElement {
    const container = document.createElement('div');
    container.className = 'rich-component rich-fallback';
    container.dataset.componentId = component.id;

    container.innerHTML = `
      <div class="fallback-header">
        <strong>Unknown Component: ${component.type}</strong>
      </div>
      <pre class="fallback-data">${JSON.stringify(component.data, null, 2)}</pre>
    `;

    return container;
  }
}

// Component manager for handling component lifecycle
export class ComponentManager {
  private components: Map<string, RichComponent> = new Map();
  private elements: Map<string, HTMLElement> = new Map();
  private registry: ComponentRegistry = new ComponentRegistry();
  private container: HTMLElement;
  private readonly sharedFields = new Set([
    'id',
    'type',
    'lifecycle',
    'layout',
    'theme',
    'children',
    'timestamp',
    'visible',
    'interactive',
  ]);

  constructor(container: HTMLElement) {
    this.container = container;
    ensureRichComponentStyles(this.container);
  }

  processUpdate(update: ComponentUpdate): void {
    // Handle UI state updates with special processing
    if (update.component && this.isUIStateUpdate(update.component)) {
      this.processUIStateUpdate(update.component);
      return;
    }

    switch (update.operation) {
      case 'create':
        this.createComponent(update);
        break;
      case 'update':
        this.updateComponent(update);
        break;
      case 'replace':
        this.replaceComponent(update);
        break;
      case 'remove':
        this.removeComponent(update);
        break;
    }
  }

  private createComponent(update: ComponentUpdate): void {
    if (!update.component) return;

    const component = this.normalizeComponent(update.component);
    const element = this.registry.render(component);
    this.components.set(component.id, component);
    this.elements.set(component.id, element);

    // Determine where to place the component
    this.positionComponent(element);
  }

  private updateComponent(update: ComponentUpdate): void {
    if (!update.component) return;

    const element = this.elements.get(update.target_id);
    if (element) {
      const component = this.normalizeComponent(update.component);
      this.registry.update(element, component, update.updates);
      this.components.set(update.target_id, component);
    }
  }

  private replaceComponent(update: ComponentUpdate): void {
    if (!update.component) return;

    const oldElement = this.elements.get(update.target_id);
    if (oldElement) {
      const component = this.normalizeComponent(update.component);
      const newElement = this.registry.render(component);
      oldElement.parentNode?.replaceChild(newElement, oldElement);

      this.elements.set(component.id, newElement);
      this.components.set(component.id, component);

      // Clean up old references if ID changed
      if (update.target_id !== component.id) {
        this.elements.delete(update.target_id);
        this.components.delete(update.target_id);
      }
    }
  }

  private removeComponent(update: ComponentUpdate): void {
    const element = this.elements.get(update.target_id);
    if (element) {
      element.remove();
      this.elements.delete(update.target_id);
      this.components.delete(update.target_id);
    }
  }

  private positionComponent(element: HTMLElement): void {
    // Always append to container
    this.container.appendChild(element);

    // Trigger scroll to bottom in parent chat component
    this.triggerScroll();
  }

  private triggerScroll(): void {
    // Find the parent vanna-chat component and trigger its scroll method
    const vannaChat = document.querySelector('vanna-chat') as any;
    if (vannaChat && typeof vannaChat.scrollToLastMessage === 'function') {
      // Use requestAnimationFrame to wait for DOM update
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          vannaChat.scrollToLastMessage();
        });
      });
    }
  }

  clear(): void {
    this.components.clear();
    this.elements.clear();
    this.container.innerHTML = '';
    ensureRichComponentStyles(this.container);
  }

  getComponent(id: string): RichComponent | undefined {
    return this.components.get(id);
  }

  getAllComponents(): RichComponent[] {
    return Array.from(this.components.values());
  }

  private normalizeComponent(component: RichComponent): RichComponent {
    const data = { ...(component.data ?? {}) };

    for (const [key, value] of Object.entries(component as Record<string, any>)) {
      if (this.sharedFields.has(key) || key === 'data') continue;
      data[key] = value;
    }

    if (component.data && Object.keys(component.data).length === Object.keys(data).length) {
      return component;
    }

    return {
      ...component,
      data,
    };
  }

  private isUIStateUpdate(component: RichComponent): boolean {
    return component.type === 'status_bar_update' ||
           component.type === 'task_tracker_update' ||
           component.type === 'chat_input_update';
  }

  private processUIStateUpdate(component: RichComponent): void {
    console.log('processUIStateUpdate called with type:', component.type, 'component:', component);

    switch (component.type) {
      case 'status_bar_update':
        this.updateStatusBar(component);
        break;
      case 'task_tracker_update':
        this.updateTaskTracker(component);
        break;
      case 'chat_input_update':
        this.updateChatInput(component);
        break;
    }
  }

  private updateStatusBar(component: RichComponent): void {
    // Find the status bar component - first try shadow DOM, then document
    let statusBar: HTMLElement | null = null;

    // Look for vanna-chat and search within its shadow root
    const vannaChat = document.querySelector('vanna-chat') as any;
    if (vannaChat && vannaChat.shadowRoot) {
      statusBar = vannaChat.shadowRoot.querySelector('vanna-status-bar') as HTMLElement | null;
    }

    // Fallback to document search
    if (!statusBar) {
      statusBar = document.querySelector('vanna-status-bar') as HTMLElement | null;
    }

    if (statusBar) {
      const { status, message, detail } = component.data || {};
      // Set properties directly on the Lit component
      (statusBar as any).status = status;
      (statusBar as any).message = message || '';
      (statusBar as any).detail = detail || '';
    }
  }

  private updateTaskTracker(component: RichComponent): void {
    // Debug logging
    console.log('updateTaskTracker called with component:', component);
    console.log('component.data:', component.data);

    // Find the progress tracker component - first try shadow DOM, then document
    let progressTracker = null;

    // Look for vanna-chat and search within its shadow root
    const vannaChat = document.querySelector('vanna-chat') as any;
    if (vannaChat && vannaChat.shadowRoot) {
      progressTracker = vannaChat.shadowRoot.querySelector('vanna-progress-tracker');
    }

    // Fallback to document search
    if (!progressTracker) {
      progressTracker = document.querySelector('vanna-progress-tracker');
    }

    console.log('Found progressTracker:', progressTracker);
    if (!progressTracker) return;

    const { operation, task, task_id, status, detail } = component.data || {};
    console.log('Extracted data:', { operation, task, task_id, status, detail });

    switch (operation) {
      case 'add_task':
        console.log('Adding task:', task);
        if (task && progressTracker.addItem) {
          // Use the backend task ID instead of generating a new one
          const result = progressTracker.addItem(task.title || task.text, task.description || task.detail, task.id);
          console.log('addItem result:', result, 'using backend ID:', task.id);
        }
        break;
      case 'update_task':
        console.log('Updating task:', task_id, status, detail);
        if (task_id && progressTracker.updateItem) {
          progressTracker.updateItem(task_id, status, detail);
        }
        break;
      case 'remove_task':
        if (task_id && progressTracker.removeItem) {
          progressTracker.removeItem(task_id);
        }
        break;
      case 'clear_tasks':
        if (progressTracker.clear) {
          progressTracker.clear();
        }
        break;
    }
  }

  private updateChatInput(component: RichComponent): void {
    // Find the chat input element - first try shadow DOM, then document
    let chatInput = null;

    // Look for vanna-chat and search within its shadow root
    const vannaChat = document.querySelector('vanna-chat') as any;
    if (vannaChat && vannaChat.shadowRoot) {
      chatInput = vannaChat.shadowRoot.querySelector('textarea.message-input, input.message-input');
    }

    // Fallback to document search with multiple selectors
    if (!chatInput) {
      chatInput = document.querySelector('textarea[data-testid="message-input"], input[type="text"].message-input, .message-input input, .message-input textarea');
    }

    if (!chatInput) return;

    const { placeholder, disabled, value, focus } = component.data || {};

    if (placeholder !== undefined) {
      chatInput.placeholder = placeholder;
    }
    if (disabled !== undefined) {
      chatInput.disabled = disabled;
    }
    if (value !== undefined) {
      chatInput.value = value;
    }
    if (focus !== undefined) {
      if (focus) {
        chatInput.focus();
      } else {
        chatInput.blur();
      }
    }
  }
}
