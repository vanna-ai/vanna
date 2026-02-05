import { css } from 'lit';

export const richComponentStyles = css`
  .rich-component {
    margin-bottom: var(--vanna-space-4);
    border-radius: var(--vanna-border-radius-lg);
    background: var(--vanna-background-default);
    border: 1px solid var(--vanna-outline-default);
    box-shadow: var(--vanna-shadow-sm);
    transition: box-shadow var(--vanna-duration-200) ease;
    font-family: var(--vanna-font-family-default);
  }

  .rich-component:hover {
    box-shadow: var(--vanna-shadow-md);
  }

  /* Shared typography */
  .rich-component h3,
  .rich-component h4 {
    margin: 0;
    color: var(--vanna-foreground-default);
    font-weight: 600;
  }

  .rich-component p,
  .rich-component span,
  .rich-component div {
    color: var(--vanna-foreground-default);
  }

  /* Card */
  .rich-card {
    overflow: hidden;
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: var(--vanna-space-3);
    padding: var(--vanna-space-4) var(--vanna-space-5);
    background: var(--vanna-background-higher);
    border-bottom: 1px solid var(--vanna-outline-default);
  }

  .card-header.collapsible {
    cursor: pointer;
  }

  .card-icon {
    font-size: 1.25rem;
    display: flex;
  }

  .card-title-section {
    flex: 1;
  }

  .card-title {
    margin: 0;
    font-size: 1rem;
    color: var(--vanna-foreground-default);
  }

  .card-subtitle {
    margin: var(--vanna-space-1) 0 0 0;
    font-size: 0.875rem;
    color: var(--vanna-foreground-dimmer);
  }

  .card-status {
    padding: var(--vanna-space-1) var(--vanna-space-2);
    border-radius: var(--vanna-border-radius-md);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    background: rgba(0, 123, 255, 0.15);
    color: var(--vanna-accent-primary-default);
  }

  .card-status.status-success {
    background: rgba(16, 185, 129, 0.15);
    color: var(--vanna-accent-positive-default);
  }

  .card-status.status-warning {
    background: rgba(245, 158, 11, 0.15);
    color: var(--vanna-accent-warning-default);
  }

  .card-status.status-error {
    background: rgba(239, 68, 68, 0.15);
    color: var(--vanna-accent-negative-default);
  }

  .card-toggle {
    margin-left: var(--vanna-space-2);
    border: none;
    background: none;
    cursor: pointer;
    color: var(--vanna-foreground-dimmer);
    font-size: 1rem;
    padding: var(--vanna-space-1);
    border-radius: var(--vanna-border-radius-sm);
    transition: background-color var(--vanna-duration-200) ease;
  }

  .card-toggle:hover {
    background: var(--vanna-background-root);
  }

  .card-content {
    padding: var(--vanna-space-4) var(--vanna-space-5);
    line-height: 1.6;
    transition: all var(--vanna-duration-200) ease;
  }

  .card-content.collapsed {
    max-height: 0;
    padding-top: 0;
    padding-bottom: 0;
    overflow: hidden;
  }

  .card-actions {
    padding: var(--vanna-space-3) var(--vanna-space-5);
    background: var(--vanna-background-root);
    border-top: 1px solid var(--vanna-outline-default);
    display: flex;
    gap: var(--vanna-space-2);
  }

  .card-action {
    padding: var(--vanna-space-2) var(--vanna-space-4);
    border-radius: var(--vanna-border-radius-md);
    border: 1px solid var(--vanna-outline-default);
    background: var(--vanna-background-default);
    color: var(--vanna-foreground-default);
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all var(--vanna-duration-200) ease;
  }

  .card-action:hover {
    background: var(--vanna-background-higher);
  }

  .card-action.primary {
    background: var(--vanna-accent-primary-default);
    border-color: var(--vanna-accent-primary-default);
    color: white;
  }

  .card-action.primary:hover {
    background: var(--vanna-accent-primary-stronger);
  }

  /* Task list */
  .rich-task-list {
    padding-bottom: var(--vanna-space-2);
  }

  .task-list-header {
    padding: var(--vanna-space-4) var(--vanna-space-5);
    background: var(--vanna-background-higher);
    border-bottom: 1px solid var(--vanna-outline-default);
  }

  .task-list-title {
    margin-bottom: var(--vanna-space-3);
    font-size: 1rem;
  }

  .task-list-progress {
    display: flex;
    align-items: center;
    gap: var(--vanna-space-3);
  }

  .task-list-progress .progress-text {
    font-size: 0.875rem;
    color: var(--vanna-foreground-dimmer);
    min-width: fit-content;
  }

  .task-list-progress .progress-bar {
    flex: 1;
    height: 6px;
    background: var(--vanna-background-root);
    border-radius: 3px;
    overflow: hidden;
  }

  .task-list-progress .progress-fill {
    height: 100%;
    background: var(--vanna-accent-primary-default);
    border-radius: 3px;
    transition: width var(--vanna-duration-300) ease;
  }

  .task-list-items {
    padding: var(--vanna-space-4) var(--vanna-space-5);
    display: flex;
    flex-direction: column;
    gap: var(--vanna-space-3);
  }

  .task-item {
    display: flex;
    gap: var(--vanna-space-3);
    padding: var(--vanna-space-3);
    border-radius: var(--vanna-border-radius-md);
    background: var(--vanna-background-default);
    border: 1px solid var(--vanna-outline-dimmer);
  }

  .task-item.status-running {
    border-color: var(--vanna-accent-primary-default);
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.2);
  }

  .task-item.status-completed {
    opacity: 0.85;
  }

  .task-icon {
    font-size: 1.2rem;
    margin-top: 2px;
  }

  .task-title {
    margin: 0;
    font-size: 0.95rem;
  }

  .task-description {
    margin: var(--vanna-space-1) 0 0 0;
    font-size: 0.85rem;
    color: var(--vanna-foreground-dimmer);
  }

  .task-progress {
    display: flex;
    gap: var(--vanna-space-2);
    align-items: center;
    margin-top: var(--vanna-space-2);
  }

  .task-progress-bar {
    flex: 1;
    height: 6px;
    background: var(--vanna-background-root);
    border-radius: 3px;
    overflow: hidden;
  }

  .task-progress-fill {
    height: 100%;
    background: var(--vanna-accent-primary-default);
    transition: width var(--vanna-duration-300) ease;
  }

  .task-progress-text {
    font-size: 0.75rem;
    color: var(--vanna-foreground-dimmer);
  }

  .task-timestamp {
    margin-top: var(--vanna-space-2);
    font-size: 0.75rem;
    color: var(--vanna-foreground-dimmest);
    font-variant-numeric: tabular-nums;
  }

  /* Tool execution */
  .rich-tool-execution {
    padding: var(--vanna-space-4) var(--vanna-space-5);
  }

  .tool-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--vanna-space-3);
  }

  .tool-status {
    display: flex;
    align-items: center;
    gap: var(--vanna-space-2);
  }

  .tool-icon {
    font-size: 1.2rem;
  }

  .tool-name {
    font-weight: 600;
  }

  .status-badge {
    padding: 2px 8px;
    border-radius: var(--vanna-border-radius-sm);
    font-size: 0.75rem;
    text-transform: uppercase;
    background: rgba(0, 123, 255, 0.15);
    color: var(--vanna-accent-primary-default);
  }

  .status-badge.status-completed {
    background: rgba(16, 185, 129, 0.15);
    color: var(--vanna-accent-positive-default);
  }

  .status-badge.status-failed {
    background: rgba(239, 68, 68, 0.15);
    color: var(--vanna-accent-negative-default);
  }

  .tool-duration {
    font-size: 0.85rem;
    color: var(--vanna-foreground-dimmest);
  }

  .tool-progress {
    display: flex;
    align-items: center;
    gap: var(--vanna-space-3);
    margin-bottom: var(--vanna-space-3);
  }

  .tool-progress .progress-bar {
    flex: 1;
    height: 8px;
    background: var(--vanna-background-root);
    border-radius: 4px;
    overflow: hidden;
  }

  .tool-progress .progress-fill {
    height: 100%;
    background: var(--vanna-accent-primary-default);
    transition: width var(--vanna-duration-300) ease;
  }

  .tool-progress .progress-text {
    font-size: 0.8rem;
    color: var(--vanna-foreground-dimmer);
  }

  .tool-section {
    margin-top: var(--vanna-space-4);
  }

  .tool-section h4 {
    margin-bottom: var(--vanna-space-2);
    font-size: 0.9rem;
  }

  .tool-arguments,
  .tool-result,
  .tool-error {
    background: var(--vanna-background-root);
    border: 1px solid var(--vanna-outline-dimmer);
    border-radius: var(--vanna-border-radius-md);
    padding: var(--vanna-space-3);
    font-family: var(--vanna-font-family-mono);
    font-size: 0.85rem;
    line-height: 1.5;
    white-space: pre-wrap;
    color: var(--vanna-foreground-default);
  }

  .tool-section.error .tool-error {
    border-color: var(--vanna-accent-negative-default);
    background: rgba(239, 68, 68, 0.1);
  }

  .tool-logs {
    display: flex;
    flex-direction: column;
    gap: var(--vanna-space-2);
    max-height: 200px;
    overflow-y: auto;
    padding-right: 4px;
  }

  .log-entry {
    display: flex;
    gap: var(--vanna-space-2);
    font-size: 0.85rem;
    color: var(--vanna-foreground-default);
  }

  .log-entry .log-timestamp {
    font-family: var(--vanna-font-family-mono);
    color: var(--vanna-foreground-dimmest);
    min-width: 110px;
  }

  .log-entry .log-level {
    color: var(--vanna-foreground-dimmer);
  }

  .log-entry.log-error .log-level {
    color: var(--vanna-accent-negative-default);
  }

  .log-entry.log-warning .log-level {
    color: var(--vanna-accent-warning-default);
  }

  /* Progress bar */
  .rich-progress-bar {
    padding: var(--vanna-space-4) var(--vanna-space-5);
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    margin-bottom: var(--vanna-space-3);
    color: var(--vanna-foreground-dimmer);
  }

  .progress-track {
    position: relative;
    height: 10px;
    background: var(--vanna-background-root);
    border-radius: 5px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: var(--vanna-accent-primary-default);
    transition: width var(--vanna-duration-300) ease;
  }

  .progress-fill.animated {
    animation: progressPulse 2s ease-in-out infinite;
  }

  .progress-fill.status-success {
    background: var(--vanna-accent-positive-default);
  }

  .progress-fill.status-error {
    background: var(--vanna-accent-negative-default);
  }

  .progress-fill.status-warning {
    background: var(--vanna-accent-warning-default);
  }

  @keyframes progressPulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
  }

  /* Notifications */
  .rich-notification {
    padding: var(--vanna-space-4) var(--vanna-space-5);
    font-family: var(--vanna-font-family-default);
  }

  .notification-content {
    display: flex;
    gap: var(--vanna-space-3);
    align-items: flex-start;
    position: relative;
  }

  .notification-content.level-info {
    border-left: 4px solid var(--vanna-accent-primary-default);
    padding-left: var(--vanna-space-3);
  }

  .notification-content.level-success {
    border-left: 4px solid var(--vanna-accent-positive-default);
    padding-left: var(--vanna-space-3);
  }

  .notification-content.level-warning {
    border-left: 4px solid var(--vanna-accent-warning-default);
    padding-left: var(--vanna-space-3);
  }

  .notification-content.level-error {
    border-left: 4px solid var(--vanna-accent-negative-default);
    padding-left: var(--vanna-space-3);
  }

  .notification-icon {
    font-size: 1.5rem;
    line-height: 1;
  }

  .notification-body {
    flex: 1;
    padding-right: var(--vanna-space-6);
  }

  .notification-title {
    margin-bottom: var(--vanna-space-2);
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--vanna-foreground-default);
  }

  .notification-message {
    margin: 0;
    font-size: 0.875rem;
    line-height: 1.5;
    color: var(--vanna-foreground-dimmer);
  }

  .notification-actions {
    margin-top: var(--vanna-space-3);
    display: flex;
    gap: var(--vanna-space-2);
    flex-wrap: wrap;
  }

  .notification-action {
    padding: var(--vanna-space-2) var(--vanna-space-4);
    border-radius: var(--vanna-border-radius-md);
    border: 1px solid var(--vanna-outline-default);
    background: transparent;
    color: var(--vanna-foreground-default);
    cursor: pointer;
    transition: background var(--vanna-duration-200) ease;
    font-size: 0.875rem;
  }

  .notification-action:hover {
    background: var(--vanna-background-higher);
  }

  .notification-action.primary {
    background: var(--vanna-accent-primary-default);
    border-color: var(--vanna-accent-primary-default);
    color: white;
  }

  .notification-action.primary:hover {
    background: var(--vanna-accent-primary-stronger);
  }

  .notification-action.secondary {
    background: var(--vanna-background-default);
  }

  .notification-dismiss {
    position: absolute;
    top: 0;
    right: 0;
    background: none;
    border: none;
    color: var(--vanna-foreground-dimmer);
    font-size: 1.2rem;
    cursor: pointer;
    padding: var(--vanna-space-1);
    line-height: 1;
    transition: color var(--vanna-duration-200) ease;
  }

  .notification-dismiss:hover {
    color: var(--vanna-foreground-default);
  }

  /* Status indicator */
  .rich-status-indicator {
    padding: var(--vanna-space-3) var(--vanna-space-4);
    font-family: var(--vanna-font-family-default);
  }

  .status-indicator-content {
    display: inline-flex;
    align-items: center;
    gap: var(--vanna-space-2);
    padding: var(--vanna-space-2) var(--vanna-space-3);
    border-radius: var(--vanna-border-radius-md);
    font-size: 0.85rem;
    font-weight: 500;
    background: rgba(0, 123, 255, 0.12);
    color: var(--vanna-accent-primary-default);
  }

  .status-indicator-content.status-success {
    background: rgba(16, 185, 129, 0.12);
    color: var(--vanna-accent-positive-default);
  }

  .status-indicator-content.status-error {
    background: rgba(239, 68, 68, 0.12);
    color: var(--vanna-accent-negative-default);
  }

  .status-indicator-content.status-warning {
    background: rgba(245, 158, 11, 0.12);
    color: var(--vanna-accent-warning-default);
  }

  .status-indicator-content.status-info {
    background: rgba(0, 123, 255, 0.12);
    color: var(--vanna-accent-primary-default);
  }

  .status-indicator-content.pulse {
    animation: statusPulse 1.4s ease-in-out infinite;
  }

  .status-icon {
    font-size: 1.1rem;
  }

  @keyframes statusPulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.35); }
    50% { box-shadow: 0 0 0 4px rgba(0, 123, 255, 0); }
  }

  /* Text components */
  .text-markdown {
    padding-left: var(--vanna-space-4);
    line-height: 1.6;
    font-family: var(--vanna-font-family-default);
  }

  .text-markdown h1,
  .text-markdown h2,
  .text-markdown h3,
  .text-markdown h4,
  .text-markdown h5,
  .text-markdown h6 {
    margin: var(--vanna-space-3) 0 var(--vanna-space-2) 0;
    color: var(--vanna-foreground-default);
  }

  .text-markdown h1:first-child,
  .text-markdown h2:first-child,
  .text-markdown h3:first-child,
  .text-markdown h4:first-child,
  .text-markdown h5:first-child,
  .text-markdown h6:first-child {
    margin-top: 0;
  }

  .text-markdown p {
    margin: var(--vanna-space-2) 0;
    color: var(--vanna-foreground-default);
  }

  .text-markdown ul,
  .text-markdown ol {
    margin: var(--vanna-space-2) 0;
    padding-left: var(--vanna-space-5);
  }

  .text-markdown li {
    margin: var(--vanna-space-1) 0;
    color: var(--vanna-foreground-default);
  }

  .text-markdown code {
    background: var(--vanna-background-root);
    border: 1px solid var(--vanna-outline-dimmer);
    border-radius: var(--vanna-border-radius-sm);
    padding: 2px 4px;
    font-family: var(--vanna-font-family-mono);
    font-size: 0.9em;
    color: var(--vanna-foreground-default);
  }

  .text-markdown pre {
    background: var(--vanna-background-root);
    border: 1px solid var(--vanna-outline-dimmer);
    border-radius: var(--vanna-border-radius-md);
    padding: var(--vanna-space-3);
    overflow-x: auto;
    margin: var(--vanna-space-3) 0;
  }

  .text-markdown pre code {
    background: none;
    border: none;
    padding: 0;
  }

  /* Chart */
  .rich-chart {
    padding: var(--vanna-space-4);
  }

  .chart-header {
    margin-bottom: var(--vanna-space-3);
  }

  .chart-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--vanna-foreground-default);
    margin: 0;
  }

  .chart-content {
    min-height: 300px;
  }

  .chart-error {
    padding: var(--vanna-space-4);
    background: var(--vanna-accent-negative-subtle);
    border-radius: var(--vanna-border-radius-md);
    color: var(--vanna-accent-negative-default);
  }

  .chart-error pre {
    margin-top: var(--vanna-space-2);
    padding: var(--vanna-space-2);
    background: var(--vanna-background-lower);
    border-radius: var(--vanna-border-radius-sm);
    font-size: 0.75rem;
    overflow-x: auto;
  }

  /* DataFrameComponent */
  .rich-dataframe {
    overflow: hidden;
    font-family: var(--vanna-font-family-default);
  }

  .dataframe-header {
    padding: var(--vanna-space-4) var(--vanna-space-5);
    background: var(--vanna-background-higher);
    border-bottom: 1px solid var(--vanna-outline-default);
  }

  .dataframe-title {
    margin: 0 0 var(--vanna-space-2) 0;
    font-size: 1rem;
    color: var(--vanna-foreground-default);
  }

  .dataframe-description {
    margin: 0 0 var(--vanna-space-3) 0;
    font-size: 0.875rem;
    color: var(--vanna-foreground-dimmer);
  }

  .dataframe-meta {
    display: flex;
    gap: var(--vanna-space-4);
    font-size: 0.75rem;
    color: var(--vanna-foreground-dimmest);
  }

  .dataframe-actions {
    padding: var(--vanna-space-3) var(--vanna-space-5);
    background: var(--vanna-background-default);
    border-bottom: 1px solid var(--vanna-outline-dimmer);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--vanna-space-3);
  }

  .dataframe-search {
    flex: 1;
    max-width: 300px;
  }

  .search-input {
    width: 100%;
    padding: var(--vanna-space-2) var(--vanna-space-3);
    border: 1px solid var(--vanna-outline-default);
    border-radius: var(--vanna-border-radius-md);
    background: var(--vanna-background-default);
    color: var(--vanna-foreground-default);
    font-size: 0.875rem;
    transition: border-color var(--vanna-duration-200) ease;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--vanna-accent-primary-default);
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.2);
  }

  .export-btn {
    padding: var(--vanna-space-2) var(--vanna-space-3);
    border: 1px solid var(--vanna-outline-default);
    border-radius: var(--vanna-border-radius-md);
    background: var(--vanna-background-default);
    color: var(--vanna-foreground-default);
    cursor: pointer;
    font-size: 0.875rem;
    transition: all var(--vanna-duration-200) ease;
  }

  .export-btn:hover {
    background: var(--vanna-background-higher);
    border-color: var(--vanna-accent-primary-default);
  }

  .dataframe-table-container {
    max-height: 600px;
    overflow: auto;
    border: 1px solid var(--vanna-outline-dimmer);
    border-radius: var(--vanna-border-radius-md);
    margin: var(--vanna-space-4) 0;
  }

  .dataframe-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    font-family: var(--vanna-font-family-default);
    table-layout: auto;
  }

  .dataframe-table.bordered {
    border: 1px solid var(--vanna-outline-dimmer);
  }

  .dataframe-table.compact th,
  .dataframe-table.compact td {
    padding: var(--vanna-space-1) var(--vanna-space-2);
  }

  .dataframe-table th {
    background: var(--vanna-background-higher);
    color: var(--vanna-foreground-default);
    font-weight: 600;
    text-align: left;
    padding: var(--vanna-space-3) var(--vanna-space-4);
    border-bottom: 2px solid var(--vanna-outline-default);
    position: sticky;
    top: 0;
    z-index: 1;
  }

  .dataframe-table th.sortable {
    cursor: pointer;
    user-select: none;
    transition: background-color var(--vanna-duration-200) ease;
  }

  .dataframe-table th.sortable:hover {
    background: var(--vanna-background-root);
  }

  .dataframe-table th .sort-indicator {
    margin-left: var(--vanna-space-2);
    color: var(--vanna-foreground-dimmer);
    font-size: 0.8rem;
  }

  .dataframe-table td {
    padding: var(--vanna-space-3) var(--vanna-space-4);
    border-bottom: 1px solid var(--vanna-outline-dimmer);
    color: var(--vanna-foreground-default);
  }

  .dataframe-table.striped tbody tr:nth-child(even) {
    background: rgba(255, 255, 255, 0.02);
  }

  .dataframe-table tbody tr:hover {
    background: var(--vanna-background-higher);
  }

  .dataframe-table .cell-number {
    text-align: right;
    font-family: var(--vanna-font-family-mono);
  }

  .dataframe-table .cell-boolean {
    text-align: center;
    font-weight: 600;
  }

  .dataframe-table .cell-date {
    font-family: var(--vanna-font-family-mono);
  }

  .dataframe-table .null-value {
    color: var(--vanna-foreground-dimmest);
    font-style: italic;
  }

  .dataframe-truncated {
    padding: var(--vanna-space-3) var(--vanna-space-5);
    text-align: center;
    color: var(--vanna-foreground-dimmer);
    background: var(--vanna-background-root);
    border-top: 1px solid var(--vanna-outline-dimmer);
    font-size: 0.875rem;
  }

  .dataframe-empty {
    padding: var(--vanna-space-8) var(--vanna-space-5);
    text-align: center;
    color: var(--vanna-foreground-dimmer);
  }

  .dataframe-empty p {
    margin: 0;
    font-size: 0.875rem;
  }

  /* Primitive Component Styles */

  /* Status Card */
  .rich-status-card {
    overflow: hidden;
  }

  .status-card-header {
    display: flex;
    align-items: center;
    gap: var(--vanna-space-3);
    padding: var(--vanna-space-4) var(--vanna-space-5);
    background: var(--vanna-background-higher);
    border-bottom: 1px solid var(--vanna-outline-default);
  }

  .status-card-header.collapsible {
    cursor: pointer;
  }

  .status-card-icon {
    font-size: 1.25rem;
    display: flex;
    align-items: center;
  }

  .status-card-title-section {
    flex: 1;
    display: flex;
    align-items: center;
    gap: var(--vanna-space-3);
  }

  .status-card-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--vanna-foreground-default);
  }

  .status-card-badge {
    padding: var(--vanna-space-1) var(--vanna-space-2);
    border-radius: var(--vanna-border-radius-md);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .status-card-badge.status-pending {
    background: var(--vanna-background-root);
    color: var(--vanna-foreground-dimmer);
  }

  .status-card-badge.status-running {
    background: rgba(59, 130, 246, 0.1);
    color: rgb(37, 99, 235);
  }

  .status-card-badge.status-success,
  .status-card-badge.status-completed {
    background: rgba(16, 185, 129, 0.1);
    color: rgb(5, 150, 105);
  }

  .status-card-badge.status-error,
  .status-card-badge.status-failed {
    background: rgba(239, 68, 68, 0.1);
    color: rgb(220, 38, 38);
  }

  .status-card-badge.status-warning {
    background: rgba(245, 158, 11, 0.1);
    color: rgb(217, 119, 6);
  }

  .status-card-content {
    padding: var(--vanna-space-4) var(--vanna-space-5);
    line-height: 1.5;
    transition: all var(--vanna-duration-200) ease;
    overflow: hidden;
  }

  .status-card-content.collapsed {
    max-height: 0;
    padding-top: 0;
    padding-bottom: 0;
  }

  .status-card-metadata {
    border-top: 1px solid var(--vanna-outline-default);
    margin: 0;
  }

  .status-card-metadata-summary {
    padding: var(--vanna-space-3) var(--vanna-space-5);
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--vanna-foreground-dimmer);
    user-select: none;
    transition: background var(--vanna-duration-200) ease;
  }

  .status-card-metadata-summary:hover {
    background: var(--vanna-background-higher);
  }

  .status-card-metadata-content {
    padding: var(--vanna-space-3) var(--vanna-space-5);
    background: var(--vanna-background-root);
  }

  .metadata-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }

  .metadata-table thead {
    background: var(--vanna-background-higher);
  }

  .metadata-table th {
    text-align: left;
    padding: var(--vanna-space-2) var(--vanna-space-3);
    font-weight: 600;
    color: var(--vanna-foreground-dimmer);
    border-bottom: 1px solid var(--vanna-outline-default);
  }

  .metadata-table td {
    padding: var(--vanna-space-2) var(--vanna-space-3);
    border-bottom: 1px solid var(--vanna-outline-dimmer);
    vertical-align: top;
  }

  .metadata-table tbody tr:last-child td {
    border-bottom: none;
  }

  .metadata-key {
    font-weight: 500;
    color: var(--vanna-foreground-default);
    width: 30%;
  }

  .metadata-value {
    color: var(--vanna-foreground-default);
    font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, 'Courier New', monospace;
  }

  .metadata-string {
    color: var(--vanna-foreground-default);
  }

  .metadata-number {
    color: rgb(37, 99, 235);
  }

  .metadata-boolean {
    color: rgb(124, 58, 237);
  }

  .metadata-null,
  .metadata-undefined {
    color: var(--vanna-foreground-dimmer);
    font-style: italic;
  }

  .metadata-json {
    margin: 0;
    padding: var(--vanna-space-2);
    background: var(--vanna-background-default);
    border: 1px solid var(--vanna-outline-default);
    border-radius: var(--vanna-border-radius-sm);
    font-size: 0.813rem;
    line-height: 1.5;
    overflow-x: auto;
  }

  /* Progress Display */
  .rich-progress-display .progress-display-container {
    padding: var(--vanna-space-4);
  }

  .progress-display-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--vanna-space-3);
  }

  .progress-display-label {
    font-weight: 500;
  }

  .progress-display-percentage {
    font-size: 0.875rem;
    color: var(--vanna-foreground-dimmer);
    font-weight: 600;
  }

  .progress-display-track {
    height: 12px;
    background: var(--vanna-background-root);
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid var(--vanna-outline-default);
  }

  .progress-display-fill {
    height: 100%;
    background: var(--vanna-accent-primary-default);
    border-radius: 6px;
    transition: width var(--vanna-duration-300) ease;
    position: relative;
    overflow: hidden;
  }

  .progress-display-fill.animated {
    animation: progressPulse 2s ease-in-out infinite;
  }

  .progress-display-fill.status-success {
    background: var(--vanna-accent-positive-default);
  }

  .progress-display-fill.status-warning {
    background: var(--vanna-accent-warning-default);
  }

  .progress-display-fill.status-error {
    background: var(--vanna-accent-negative-default);
  }

  .progress-display-description {
    margin-top: var(--vanna-space-2);
    font-size: 0.875rem;
    color: var(--vanna-foreground-dimmer);
    line-height: 1.4;
  }

  /* Log Viewer */
  .rich-log-viewer .log-viewer-container {
    overflow: hidden;
  }

  .log-viewer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--vanna-space-4) var(--vanna-space-5);
    background: var(--vanna-background-higher);
    border-bottom: 1px solid var(--vanna-outline-default);
  }

  .log-viewer-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
  }

  .log-viewer-search {
    display: flex;
    gap: var(--vanna-space-2);
  }

  .log-search-input {
    padding: var(--vanna-space-2);
    border: 1px solid var(--vanna-outline-default);
    border-radius: var(--vanna-border-radius-md);
    background: var(--vanna-background-default);
    color: var(--vanna-foreground-default);
    font-size: 0.875rem;
  }

  .log-viewer-content {
    max-height: 300px;
    overflow-y: auto;
    padding: var(--vanna-space-4);
  }

  .log-viewer-content.auto-scroll {
    scroll-behavior: smooth;
  }

  .log-entry {
    display: flex;
    gap: var(--vanna-space-2);
    padding: var(--vanna-space-2) 0;
    font-family: var(--vanna-font-family-mono);
    font-size: 0.875rem;
    line-height: 1.4;
    border-bottom: 1px solid var(--vanna-outline-default);
  }

  .log-entry:last-child {
    border-bottom: none;
  }

  .log-timestamp {
    color: var(--vanna-foreground-dimmer);
    white-space: nowrap;
  }

  .log-level {
    font-weight: 600;
    white-space: nowrap;
  }

  .log-entry.log-info .log-level {
    color: var(--vanna-accent-primary-default);
  }

  .log-entry.log-error .log-level {
    color: var(--vanna-accent-negative-default);
  }

  .log-entry.log-warning .log-level {
    color: var(--vanna-accent-warning-default);
  }

  .log-entry.log-debug .log-level {
    color: var(--vanna-foreground-dimmer);
  }

  .log-message {
    flex: 1;
    word-break: break-word;
  }

  /* Badge */
  .rich-badge {
    display: inline-flex;
    align-items: center;
    gap: var(--vanna-space-1);
    padding: var(--vanna-space-1) var(--vanna-space-2);
    border-radius: var(--vanna-border-radius-full);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.025em;
  }

  .rich-badge.badge-small {
    padding: 2px var(--vanna-space-1);
    font-size: 0.625rem;
  }

  .rich-badge.badge-large {
    padding: var(--vanna-space-2) var(--vanna-space-3);
    font-size: 0.875rem;
  }

  .rich-badge.badge-default {
    background: var(--vanna-background-root);
    color: var(--vanna-foreground-dimmer);
  }

  .rich-badge.badge-primary {
    background: var(--vanna-accent-primary-default);
    color: white;
  }

  .rich-badge.badge-success {
    background: var(--vanna-accent-positive-default);
    color: white;
  }

  .rich-badge.badge-warning {
    background: var(--vanna-accent-warning-default);
    color: white;
  }

  .rich-badge.badge-error {
    background: var(--vanna-accent-negative-default);
    color: white;
  }

  /* Icon Text */
  .rich-icon-text {
    display: inline-flex;
    align-items: center;
    gap: var(--vanna-space-2);
  }

  .rich-icon-text.icon-text-small {
    font-size: 0.875rem;
    gap: var(--vanna-space-1);
  }

  .rich-icon-text.icon-text-large {
    font-size: 1.125rem;
    gap: var(--vanna-space-3);
  }

  .rich-icon-text.icon-text-center {
    justify-content: center;
  }

  .rich-icon-text.icon-text-right {
    justify-content: flex-end;
  }

  .icon-text-icon {
    display: flex;
    align-items: center;
  }

  .rich-icon-text.icon-text-primary {
    color: var(--vanna-accent-primary-default);
  }

  .rich-icon-text.icon-text-secondary {
    color: var(--vanna-foreground-dimmer);
  }

  .rich-icon-text.icon-text-muted {
    color: var(--vanna-foreground-dimmest);
  }

  /* Artifact Component Styles */
  .rich-artifact {
    overflow: hidden;
  }

  .artifact-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: var(--vanna-space-4) var(--vanna-space-5);
    background: var(--vanna-background-subtle);
    border-bottom: 1px solid var(--vanna-outline-default);
  }

  .artifact-meta {
    flex: 1;
  }

  .artifact-title {
    margin: 0 0 var(--vanna-space-2) 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--vanna-foreground-default);
  }

  .artifact-description {
    margin: 0 0 var(--vanna-space-3) 0;
    color: var(--vanna-foreground-dimmer);
    font-size: 0.9rem;
  }

  .artifact-type-badge {
    display: inline-block;
    padding: var(--vanna-space-1) var(--vanna-space-2);
    background: var(--vanna-accent-primary-subtle);
    color: var(--vanna-accent-primary-default);
    border-radius: var(--vanna-border-radius-sm);
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
  }

  .artifact-controls {
    display: flex;
    gap: var(--vanna-space-2);
  }

  .artifact-btn {
    padding: var(--vanna-space-2);
    background: var(--vanna-background-default);
    border: 1px solid var(--vanna-outline-default);
    border-radius: var(--vanna-border-radius-sm);
    cursor: pointer;
    font-size: 1rem;
    transition: all var(--vanna-duration-200) ease;
  }

  .artifact-btn:hover {
    background: var(--vanna-background-subtle);
    border-color: var(--vanna-outline-hover);
  }

  .artifact-btn:active {
    transform: translateY(1px);
  }

  .artifact-preview {
    height: 300px;
    background: var(--vanna-background-default);
  }

  .artifact-iframe {
    width: 100%;
    height: 100%;
    border: none;
    display: block;
  }

  /* Fullscreen overlay styles */
  .artifact-fullscreen-overlay {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    background: var(--vanna-background-default) !important;
    z-index: 10000 !important;
    display: flex !important;
    flex-direction: column !important;
  }

  .fullscreen-header {
    padding: var(--vanna-space-4) !important;
    border-bottom: 1px solid var(--vanna-outline-default) !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    background: var(--vanna-background-subtle) !important;
  }

  .fullscreen-header h3 {
    margin: 0 !important;
    color: var(--vanna-foreground-default) !important;
  }

  .close-fullscreen {
    padding: var(--vanna-space-2) var(--vanna-space-3) !important;
    background: var(--vanna-background-default) !important;
    border: 1px solid var(--vanna-outline-default) !important;
    border-radius: var(--vanna-border-radius-sm) !important;
    cursor: pointer !important;
    font-size: 1.2rem !important;
    line-height: 1 !important;
  }

  .close-fullscreen:hover {
    background: var(--vanna-background-subtle) !important;
  }

  .fullscreen-content {
    flex: 1 !important;
    padding: var(--vanna-space-4) !important;
    overflow: hidden !important;
  }

  .fullscreen-iframe {
    width: 100% !important;
    height: 100% !important;
    border: none !important;
    border-radius: var(--vanna-border-radius-md) !important;
  }

  /* Artifact placeholder styles */
  .artifact-placeholder {
    padding: var(--vanna-space-4);
    background: var(--vanna-background-subtle);
    border: 2px dashed var(--vanna-outline-default);
    border-radius: var(--vanna-border-radius-md);
    text-align: center;
  }

  .placeholder-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--vanna-space-3);
    opacity: 0.8;
  }

  .placeholder-icon {
    font-size: 1.5rem;
  }

  .placeholder-text {
    text-align: left;
  }

  .placeholder-text strong {
    color: var(--vanna-foreground-default);
    font-weight: 600;
  }

  .placeholder-type {
    font-size: 0.8rem;
    color: var(--vanna-foreground-dimmer);
    text-transform: uppercase;
    margin-top: var(--vanna-space-1);
  }

  .placeholder-reopen {
    padding: var(--vanna-space-2);
    background: var(--vanna-accent-primary-default);
    color: white;
    border: none;
    border-radius: var(--vanna-border-radius-sm);
    cursor: pointer;
    font-size: 1rem;
    transition: background var(--vanna-duration-200) ease;
  }

  .placeholder-reopen:hover {
    background: var(--vanna-accent-primary-hover);
  }

  /* Button Component */
  .rich-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--vanna-space-2);
    padding: var(--vanna-space-2) var(--vanna-space-4);
    border-radius: var(--vanna-border-radius-md);
    border: 1px solid;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all var(--vanna-duration-200) ease;
    white-space: nowrap;
    user-select: none;
    font-family: var(--vanna-font-family-default);
  }

  .rich-button:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  /* Button variants */
  .rich-button.button-primary {
    background: var(--vanna-accent-primary-default);
    border-color: var(--vanna-accent-primary-default);
    color: white;
  }

  .rich-button.button-primary:hover:not(:disabled) {
    background: var(--vanna-accent-primary-stronger);
    border-color: var(--vanna-accent-primary-stronger);
  }

  .rich-button.button-secondary {
    background: var(--vanna-background-default);
    border-color: var(--vanna-outline-default);
    color: var(--vanna-foreground-default);
  }

  .rich-button.button-secondary:hover:not(:disabled) {
    background: var(--vanna-background-higher);
    border-color: var(--vanna-outline-hover);
  }

  .rich-button.button-success {
    background: var(--vanna-accent-positive-default);
    border-color: var(--vanna-accent-positive-default);
    color: white;
  }

  .rich-button.button-success:hover:not(:disabled) {
    background: var(--vanna-accent-positive-stronger);
  }

  .rich-button.button-warning {
    background: var(--vanna-accent-warning-default);
    border-color: var(--vanna-accent-warning-default);
    color: white;
  }

  .rich-button.button-warning:hover:not(:disabled) {
    background: var(--vanna-accent-warning-stronger);
  }

  .rich-button.button-error {
    background: var(--vanna-accent-negative-default);
    border-color: var(--vanna-accent-negative-default);
    color: white;
  }

  .rich-button.button-error:hover:not(:disabled) {
    background: var(--vanna-accent-negative-stronger);
  }

  .rich-button.button-ghost {
    background: transparent;
    border-color: transparent;
    color: var(--vanna-foreground-default);
  }

  .rich-button.button-ghost:hover:not(:disabled) {
    background: var(--vanna-background-higher);
  }

  .rich-button.button-link {
    background: transparent;
    border-color: transparent;
    color: var(--vanna-accent-primary-default);
    text-decoration: underline;
    padding: var(--vanna-space-1) var(--vanna-space-2);
  }

  .rich-button.button-link:hover:not(:disabled) {
    color: var(--vanna-accent-primary-stronger);
  }

  /* Button sizes */
  .rich-button.button-small {
    padding: var(--vanna-space-1) var(--vanna-space-3);
    font-size: 0.75rem;
    gap: var(--vanna-space-1);
  }

  .rich-button.button-medium {
    padding: var(--vanna-space-2) var(--vanna-space-4);
    font-size: 0.875rem;
    gap: var(--vanna-space-2);
  }

  .rich-button.button-large {
    padding: var(--vanna-space-3) var(--vanna-space-5);
    font-size: 1rem;
    gap: var(--vanna-space-2);
  }

  /* Button modifiers */
  .rich-button.button-full-width {
    width: 100%;
  }

  .rich-button.button-loading {
    position: relative;
    pointer-events: none;
  }

  .button-spinner {
    display: inline-flex;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .button-icon {
    display: inline-flex;
    align-items: center;
    font-size: 1em;
  }

  .button-label {
    display: inline-flex;
    align-items: center;
  }

  /* Button Group Component */
  .rich-button-group {
    display: flex;
    gap: var(--vanna-space-2);
    font-family: var(--vanna-font-family-default);
  }

  .rich-button-group.button-group-vertical {
    flex-direction: column;
  }

  .rich-button-group.button-group-horizontal {
    flex-direction: row;
  }

  .rich-button-group.button-group-spacing-small {
    gap: var(--vanna-space-1);
  }

  .rich-button-group.button-group-spacing-medium {
    gap: var(--vanna-space-2);
  }

  .rich-button-group.button-group-spacing-large {
    gap: var(--vanna-space-4);
  }

  .rich-button-group.button-group-align-left {
    justify-content: flex-start;
  }

  .rich-button-group.button-group-align-center {
    justify-content: center;
  }

  .rich-button-group.button-group-align-right {
    justify-content: flex-end;
  }

  .rich-button-group.button-group-align-space-between {
    justify-content: space-between;
  }

  .rich-button-group.button-group-full-width {
    width: 100%;
  }

  .rich-button-group.button-group-full-width > .rich-button {
    flex: 1;
  }

  /* Button Group Interactive States */
  .rich-button.button-transitioning {
    transition: all 0.2s ease-in-out;
  }

  .rich-button.button-highlighted {
    transform: scale(1.02);
    box-shadow: 0 0 0 2px var(--vanna-accent-primary-default);
    z-index: 1;
    position: relative;
  }

  .rich-button.button-grayed-out {
    opacity: 0.4;
    filter: grayscale(50%);
    transform: scale(0.98);
  }

  .rich-button.button-clicked {
    animation: buttonClickPulse 0.3s ease-out;
  }

  @keyframes buttonClickPulse {
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.05);
    }
    100% {
      transform: scale(1.02);
    }
  }

  /* Override hover states when in click states */
  .rich-button.button-highlighted:hover,
  .rich-button.button-grayed-out:hover {
    /* Maintain the click state even on hover */
  }

  .rich-button.button-grayed-out:hover {
    opacity: 0.4;
    filter: grayscale(50%);
  }
`;

export const richComponentStyleText = richComponentStyles.cssText;
