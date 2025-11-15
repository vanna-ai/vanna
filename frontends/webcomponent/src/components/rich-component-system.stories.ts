import type { Meta, StoryObj } from '@storybook/web-components';
import { ComponentManager, ComponentUpdate } from './rich-component-system';
import { vannaDesignTokens } from '../styles/vanna-design-tokens.js';

const meta: Meta = {
  title: 'Rich Components/Component System',
  parameters: {
    layout: 'padded',
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#f5f7fa' },
        { name: 'dark', value: 'rgb(11, 15, 25)' },
      ],
    },
  },
};

export default meta;
type Story = StoryObj;

const ensureTokenStyles = () => {
  if (document.getElementById('vanna-token-style')) {
    return;
  }

  const style = document.createElement('style');
  style.id = 'vanna-token-style';
  style.textContent = vannaDesignTokens.cssText.replace(/:host/g, '.vanna-tokens');
  document.head.appendChild(style);
};

const createContainer = () => {
  ensureTokenStyles();

  const container = document.createElement('div');
  container.className = 'vanna-tokens';
  container.style.cssText = `
    padding: var(--vanna-space-5, 20px);
    max-width: 800px;
    margin: 0 auto;
    background: var(--vanna-background-default);
    border-radius: var(--vanna-border-radius-lg);
    box-shadow: var(--vanna-shadow-md);
  `;

  return container;
};

const createManager = (container: HTMLElement) => new ComponentManager(container);

const renderComponent = (manager: ComponentManager, component: any) => {
  const update: ComponentUpdate = {
    operation: 'create',
    target_id: component.id,
    component,
    timestamp: new Date().toISOString(),
  } as ComponentUpdate;

  manager.processUpdate(update);
};

const withDefaults = (component: any) => ({
  layout: { position: 'append', size: {}, z_index: 0, classes: [] },
  theme: {},
  lifecycle: 'create',
  ...component,
});

export const NotificationComponents: Story = {
  render: () => {
    const container = createContainer();
    const manager = createManager(container);

    const components = [
      withDefaults({
        id: 'info-notification',
        type: 'notification',
        data: {
          message: 'This is an informational message',
          title: 'Information',
          level: 'info',
          dismissible: true,
          actions: [],
        },
      }),
      withDefaults({
        id: 'success-notification',
        type: 'notification',
        data: {
          message: 'Operation completed successfully!',
          title: 'Success',
          level: 'success',
          dismissible: true,
          actions: [
            { label: 'View Details', action: 'view', variant: 'primary' },
            { label: 'Dismiss', action: 'dismiss', variant: 'secondary' },
          ],
        },
      }),
      withDefaults({
        id: 'warning-notification',
        type: 'notification',
        data: {
          message: 'Please review the configuration before proceeding',
          title: 'Warning',
          level: 'warning',
          dismissible: true,
          actions: [],
        },
      }),
      withDefaults({
        id: 'error-notification',
        type: 'notification',
        data: {
          message: 'Failed to connect to the database. Please check your connection.',
          title: 'Connection Error',
          level: 'error',
          dismissible: true,
          actions: [
            { label: 'Retry', action: 'retry', variant: 'primary' },
            { label: 'Cancel', action: 'cancel', variant: 'secondary' },
          ],
        },
      }),
    ];

    components.forEach((component) => renderComponent(manager, component));

    return container;
  },
};

export const StatusIndicatorComponents: Story = {
  render: () => {
    const container = createContainer();
    const manager = createManager(container);

    const statuses = [
      { status: 'loading', message: 'Processing your request...', pulse: true },
      { status: 'success', message: 'Request completed successfully', pulse: false },
      { status: 'warning', message: 'Operation completed with warnings', pulse: false },
      { status: 'error', message: 'Request failed - please try again', pulse: false },
    ];

    statuses.forEach((statusData, index) => {
      const component = withDefaults({
        id: `status-${index}`,
        type: 'status_indicator',
        data: statusData,
      });

      renderComponent(manager, component);
    });

    return container;
  },
};

export const TextComponents: Story = {
  render: () => {
    const container = createContainer();
    const manager = createManager(container);

    const plainText = withDefaults({
      id: 'plain-text',
      type: 'text',
      data: {
        content: 'This is a plain text component with some sample content to demonstrate text rendering.',
        markdown: false,
      },
    });

    const markdownText = withDefaults({
      id: 'markdown-text',
      type: 'text',
      data: {
        content: `# Rich Components Demo\n\nThis is a **markdown** text component with various formatting:\n\n- **Bold text** for emphasis\n- *Italic text* for style\n- Lists for organization\n\n## Features\n\nThe text component supports:\n- Plain text rendering\n- Basic markdown formatting\n- Code syntax highlighting`,
        markdown: true,
      },
    });

    [plainText, markdownText].forEach((component) => renderComponent(manager, component));

    return container;
  },
};

export const DataFrameComponents: Story = {
  render: () => {
    const container = createContainer();
    const manager = createManager(container);

    // Sample data for different scenarios
    const sampleData = [
      { id: 1, name: 'Alice Johnson', email: 'alice@example.com', age: 28, city: 'New York', salary: 75000, active: true },
      { id: 2, name: 'Bob Smith', email: 'bob@example.com', age: 34, city: 'San Francisco', salary: 85000, active: true },
      { id: 3, name: 'Carol Davis', email: 'carol@example.com', age: 29, city: 'Chicago', salary: 70000, active: false },
      { id: 4, name: 'David Wilson', email: 'david@example.com', age: 42, city: 'Austin', salary: 90000, active: true },
      { id: 5, name: 'Eve Brown', email: 'eve@example.com', age: 31, city: 'Seattle', salary: 80000, active: true },
      { id: 6, name: 'Frank Miller', email: 'frank@example.com', age: 38, city: 'Boston', salary: 95000, active: false },
      { id: 7, name: 'Grace Lee', email: 'grace@example.com', age: 26, city: 'Denver', salary: 65000, active: true },
      { id: 8, name: 'Henry Taylor', email: 'henry@example.com', age: 33, city: 'Portland', salary: 72000, active: true },
    ];

    const columns = ['id', 'name', 'email', 'age', 'city', 'salary', 'active'];

    // Basic DataFrame
    const basicDataFrame = withDefaults({
      id: 'basic-dataframe',
      type: 'dataframe',
      data: {
        data: sampleData.slice(0, 5),
        columns: columns,
        title: 'Employee Records',
        description: 'Sample employee data with various fields',
        row_count: 5,
        column_count: columns.length,
        column_types: {
          id: 'number',
          name: 'string',
          email: 'string',
          age: 'number',
          city: 'string',
          salary: 'number',
          active: 'boolean'
        }
      },
    });

    // Large DataFrame with all features
    const fullDataFrame = withDefaults({
      id: 'full-dataframe',
      type: 'dataframe',
      data: {
        data: sampleData,
        columns: columns,
        title: 'Complete Employee Database',
        description: 'Full dataset with search, sort, and export functionality',
        row_count: sampleData.length,
        column_count: columns.length,
        searchable: true,
        sortable: true,
        filterable: true,
        exportable: true,
        striped: true,
        bordered: true,
        max_rows_displayed: 6,
        column_types: {
          id: 'number',
          name: 'string',
          email: 'string',
          age: 'number',
          city: 'string',
          salary: 'number',
          active: 'boolean'
        }
      },
    });

    // Empty DataFrame
    const emptyDataFrame = withDefaults({
      id: 'empty-dataframe',
      type: 'dataframe',
      data: {
        data: [],
        columns: [],
        title: 'Empty Dataset',
        description: 'No data available to display',
        row_count: 0,
        column_count: 0,
      },
    });

    // Compact DataFrame
    const compactDataFrame = withDefaults({
      id: 'compact-dataframe',
      type: 'dataframe',
      data: {
        data: sampleData.slice(0, 4),
        columns: ['id', 'name', 'city', 'active'],
        title: 'Compact View',
        description: 'Space-efficient display with essential columns only',
        row_count: 4,
        column_count: 4,
        compact: true,
        searchable: false,
        exportable: false,
        column_types: {
          id: 'number',
          name: 'string',
          city: 'string',
          active: 'boolean'
        }
      },
    });

    [basicDataFrame, fullDataFrame, emptyDataFrame, compactDataFrame].forEach((component) => {
      renderComponent(manager, component);
    });

    return container;
  },
};

export const SQLQueryDataFrame: Story = {
  render: () => {
    const container = createContainer();
    const manager = createManager(container);

    // SQL query result simulation
    const sqlResultData = [
      { TrackId: 1, Name: 'For Those About To Rock (We Salute You)', AlbumId: 1, MediaTypeId: 1, GenreId: 1, Composer: 'Angus Young, Malcolm Young, Brian Johnson', Milliseconds: 343719, Bytes: 11170334, UnitPrice: 0.99 },
      { TrackId: 2, Name: 'Balls to the Wall', AlbumId: 2, MediaTypeId: 2, GenreId: 1, Composer: null, Milliseconds: 342562, Bytes: 5510424, UnitPrice: 0.99 },
      { TrackId: 3, Name: 'Fast As a Shark', AlbumId: 3, MediaTypeId: 2, GenreId: 1, Composer: 'F. Baltes, S. Kaufman, U. Dirkscneider & W. Hoffman', Milliseconds: 230619, Bytes: 3990994, UnitPrice: 0.99 },
      { TrackId: 4, Name: 'Restless and Wild', AlbumId: 3, MediaTypeId: 2, GenreId: 1, Composer: 'F. Baltes, R.A. Smith-Diesel, S. Kaufman, U. Dirkscneider & W. Hoffman', Milliseconds: 252051, Bytes: 4331779, UnitPrice: 0.99 },
      { TrackId: 5, Name: 'Princess of the Dawn', AlbumId: 3, MediaTypeId: 2, GenreId: 1, Composer: 'Deaffy & R.A. Smith-Diesel', Milliseconds: 375418, Bytes: 6290521, UnitPrice: 0.99 },
    ];

    const sqlColumns = ['TrackId', 'Name', 'AlbumId', 'MediaTypeId', 'GenreId', 'Composer', 'Milliseconds', 'Bytes', 'UnitPrice'];

    const sqlDataFrame = withDefaults({
      id: 'sql-dataframe',
      type: 'dataframe',
      data: {
        data: sqlResultData,
        columns: sqlColumns,
        title: 'Query Results',
        description: 'SELECT * FROM Track LIMIT 5',
        row_count: sqlResultData.length,
        column_count: sqlColumns.length,
        searchable: true,
        sortable: true,
        exportable: true,
        column_types: {
          TrackId: 'number',
          Name: 'string',
          AlbumId: 'number',
          MediaTypeId: 'number',
          GenreId: 'number',
          Composer: 'string',
          Milliseconds: 'number',
          Bytes: 'number',
          UnitPrice: 'number'
        }
      },
    });

    renderComponent(manager, sqlDataFrame);

    return container;
  },
};
