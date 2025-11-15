import type { Meta, StoryObj } from '@storybook/web-components';
import { ComponentManager, ComponentUpdate } from './rich-component-system';
import { vannaDesignTokens } from '../styles/vanna-design-tokens.js';
import { richComponentStyleText } from '../styles/rich-component-styles.js';

const meta: Meta = {
  title: 'Rich Components/DataFrame',
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
  argTypes: {
    theme: {
      control: { type: 'select' },
      options: ['light', 'dark'],
    },
    striped: {
      control: { type: 'boolean' },
    },
    bordered: {
      control: { type: 'boolean' },
    },
    compact: {
      control: { type: 'boolean' },
    },
    searchable: {
      control: { type: 'boolean' },
    },
    sortable: {
      control: { type: 'boolean' },
    },
    exportable: {
      control: { type: 'boolean' },
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

const ensureRichComponentStyles = () => {
  if (document.getElementById('vanna-rich-component-styles')) {
    return;
  }

  const style = document.createElement('style');
  style.id = 'vanna-rich-component-styles';
  style.textContent = richComponentStyleText;
  document.head.appendChild(style);
};

const createContainer = () => {
  ensureTokenStyles();
  ensureRichComponentStyles();

  const container = document.createElement('div');
  container.className = 'vanna-tokens';
  container.style.cssText = `
    padding: var(--vanna-space-5, 20px);
    max-width: 1200px;
    margin: 0 auto;
    background: var(--vanna-background-default, #0b0f19);
    border-radius: var(--vanna-border-radius-lg, 8px);
    box-shadow: var(--vanna-shadow-md, 0 4px 6px rgba(0, 0, 0, 0.1));
    color: var(--vanna-foreground-default, #ffffff);
  `;

  // Add some additional DataFrame-specific debugging styles
  const additionalStyles = document.createElement('style');
  additionalStyles.textContent = `
    /* Ensure DataFrame styles are applied with higher specificity */
    .vanna-tokens {
      font-family: var(--vanna-font-family-default, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif) !important;
    }

    .vanna-tokens .rich-dataframe {
      background: var(--vanna-background-default, #0b0f19) !important;
      border: 1px solid var(--vanna-outline-default, #333) !important;
      border-radius: var(--vanna-border-radius-lg, 8px) !important;
      overflow: hidden !important;
      font-family: var(--vanna-font-family-default, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif) !important;
    }

    .vanna-tokens .dataframe-table {
      width: 100% !important;
      border-collapse: collapse !important;
      font-size: 0.875rem !important;
      color: var(--vanna-foreground-default, #ffffff) !important;
      font-family: var(--vanna-font-family-default, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif) !important;
    }

    .vanna-tokens .dataframe-table th {
      background: var(--vanna-background-higher, #1a1f2e) !important;
      color: var(--vanna-foreground-default, #ffffff) !important;
      font-weight: 600 !important;
      text-align: left !important;
      padding: 12px 16px !important;
      border-bottom: 2px solid var(--vanna-outline-default, #333) !important;
      font-family: var(--vanna-font-family-default, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif) !important;
    }

    .vanna-tokens .dataframe-table td {
      padding: 12px 16px !important;
      border-bottom: 1px solid var(--vanna-outline-dimmer, #222) !important;
      color: var(--vanna-foreground-default, #ffffff) !important;
      font-family: var(--vanna-font-family-default, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif) !important;
    }

    .vanna-tokens .dataframe-table.striped tbody tr:nth-child(even) {
      background: rgba(255, 255, 255, 0.02) !important;
    }

    .vanna-tokens .dataframe-header {
      padding: 16px 20px !important;
      background: var(--vanna-background-higher, #1a1f2e) !important;
      border-bottom: 1px solid var(--vanna-outline-default, #333) !important;
      font-family: var(--vanna-font-family-default, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif) !important;
    }

    .vanna-tokens .dataframe-title {
      font-family: var(--vanna-font-family-default, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif) !important;
      color: var(--vanna-foreground-default, #ffffff) !important;
      font-weight: 600 !important;
    }

    .vanna-tokens .dataframe-description {
      font-family: var(--vanna-font-family-default, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif) !important;
      color: var(--vanna-foreground-dimmer, #b1bac4) !important;
    }

    .vanna-tokens .dataframe-actions {
      padding: 12px 20px !important;
      background: var(--vanna-background-default, #0b0f19) !important;
      border-bottom: 1px solid var(--vanna-outline-dimmer, #222) !important;
      display: flex !important;
      justify-content: space-between !important;
      align-items: center !important;
      gap: 12px !important;
    }

    .vanna-tokens .search-input {
      width: 100% !important;
      padding: 8px 12px !important;
      border: 1px solid var(--vanna-outline-default, #333) !important;
      border-radius: 6px !important;
      background: var(--vanna-background-default, #0b0f19) !important;
      color: var(--vanna-foreground-default, #ffffff) !important;
      font-size: 0.875rem !important;
      font-family: var(--vanna-font-family-default, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif) !important;
    }

    .vanna-tokens .export-btn {
      padding: 8px 12px !important;
      border: 1px solid var(--vanna-outline-default, #333) !important;
      border-radius: 6px !important;
      background: var(--vanna-background-default, #0b0f19) !important;
      color: var(--vanna-foreground-default, #ffffff) !important;
      cursor: pointer !important;
      font-size: 0.875rem !important;
      font-family: var(--vanna-font-family-default, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif) !important;
    }
  `;
  document.head.appendChild(additionalStyles);

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
  timestamp: new Date().toISOString(),
  visible: true,
  interactive: false,
  children: [],
  ...component,
});

// Sample data sets
const employeeData = [
  { id: 1, name: 'Alice Johnson', email: 'alice@example.com', age: 28, city: 'New York', salary: 75000, active: true, department: 'Engineering' },
  { id: 2, name: 'Bob Smith', email: 'bob@example.com', age: 34, city: 'San Francisco', salary: 85000, active: true, department: 'Product' },
  { id: 3, name: 'Carol Davis', email: 'carol@example.com', age: 29, city: 'Chicago', salary: 70000, active: false, department: 'Design' },
  { id: 4, name: 'David Wilson', email: 'david@example.com', age: 42, city: 'Austin', salary: 90000, active: true, department: 'Engineering' },
  { id: 5, name: 'Eve Brown', email: 'eve@example.com', age: 31, city: 'Seattle', salary: 80000, active: true, department: 'Marketing' },
  { id: 6, name: 'Frank Miller', email: 'frank@example.com', age: 38, city: 'Boston', salary: 95000, active: false, department: 'Sales' },
  { id: 7, name: 'Grace Lee', email: 'grace@example.com', age: 26, city: 'Denver', salary: 65000, active: true, department: 'HR' },
  { id: 8, name: 'Henry Taylor', email: 'henry@example.com', age: 33, city: 'Portland', salary: 72000, active: true, department: 'Engineering' },
  { id: 9, name: 'Ivy Chen', email: 'ivy@example.com', age: 27, city: 'Los Angeles', salary: 78000, active: true, department: 'Product' },
  { id: 10, name: 'Jack Anderson', email: 'jack@example.com', age: 35, city: 'Miami', salary: 82000, active: false, department: 'Finance' },
];

const sqlQueryData = [
  { TrackId: 1, Name: 'For Those About To Rock (We Salute You)', AlbumId: 1, MediaTypeId: 1, GenreId: 1, Composer: 'Angus Young, Malcolm Young, Brian Johnson', Milliseconds: 343719, Bytes: 11170334, UnitPrice: 0.99 },
  { TrackId: 2, Name: 'Balls to the Wall', AlbumId: 2, MediaTypeId: 2, GenreId: 1, Composer: null, Milliseconds: 342562, Bytes: 5510424, UnitPrice: 0.99 },
  { TrackId: 3, Name: 'Fast As a Shark', AlbumId: 3, MediaTypeId: 2, GenreId: 1, Composer: 'F. Baltes, S. Kaufman, U. Dirkscneider & W. Hoffman', Milliseconds: 230619, Bytes: 3990994, UnitPrice: 0.99 },
  { TrackId: 4, Name: 'Restless and Wild', AlbumId: 3, MediaTypeId: 2, GenreId: 1, Composer: 'F. Baltes, R.A. Smith-Diesel, S. Kaufman, U. Dirkscneider & W. Hoffman', Milliseconds: 252051, Bytes: 4331779, UnitPrice: 0.99 },
  { TrackId: 5, Name: 'Princess of the Dawn', AlbumId: 3, MediaTypeId: 2, GenreId: 1, Composer: 'Deaffy & R.A. Smith-Diesel', Milliseconds: 375418, Bytes: 6290521, UnitPrice: 0.99 },
  { TrackId: 6, Name: 'Put The Finger On You', AlbumId: 1, MediaTypeId: 1, GenreId: 1, Composer: 'Angus Young, Malcolm Young, Brian Johnson', Milliseconds: 205662, Bytes: 6713451, UnitPrice: 0.99 },
  { TrackId: 7, Name: "Let's Get It Up", AlbumId: 1, MediaTypeId: 1, GenreId: 1, Composer: 'Angus Young, Malcolm Young, Brian Johnson', Milliseconds: 233926, Bytes: 7636561, UnitPrice: 0.99 },
  { TrackId: 8, Name: 'Inject The Venom', AlbumId: 1, MediaTypeId: 1, GenreId: 1, Composer: 'Angus Young, Malcolm Young, Brian Johnson', Milliseconds: 210834, Bytes: 6852860, UnitPrice: 0.99 },
];

export const BasicDataFrame: Story = {
  render: (args) => {
    const container = createContainer();
    const manager = createManager(container);

    const component = withDefaults({
      id: 'basic-dataframe',
      type: 'dataframe',
      data: {
        data: employeeData.slice(0, 5),
        columns: ['id', 'name', 'email', 'age', 'city', 'department'],
        title: 'Employee Records',
        description: 'Basic employee data with essential information',
        row_count: 5,
        column_count: 6,
        striped: args.striped ?? true,
        bordered: args.bordered ?? true,
        compact: args.compact ?? false,
        searchable: args.searchable ?? false,
        sortable: args.sortable ?? false,
        exportable: args.exportable ?? false,
        column_types: {
          id: 'number',
          name: 'string',
          email: 'string',
          age: 'number',
          city: 'string',
          department: 'string'
        }
      },
    });

    renderComponent(manager, component);
    return container;
  },
  args: {
    striped: true,
    bordered: true,
    compact: false,
    searchable: false,
    sortable: false,
    exportable: false,
  },
};

export const InteractiveDataFrame: Story = {
  render: (args) => {
    const container = createContainer();
    const manager = createManager(container);

    const component = withDefaults({
      id: 'interactive-dataframe',
      type: 'dataframe',
      data: {
        data: employeeData,
        columns: ['id', 'name', 'email', 'age', 'city', 'salary', 'active', 'department'],
        title: 'Interactive Employee Database',
        description: 'Full dataset with search, sort, and export functionality',
        row_count: employeeData.length,
        column_count: 8,
        striped: args.striped ?? true,
        bordered: args.bordered ?? true,
        compact: args.compact ?? false,
        searchable: args.searchable ?? true,
        sortable: args.sortable ?? true,
        exportable: args.exportable ?? true,
        max_rows_displayed: 8,
        column_types: {
          id: 'number',
          name: 'string',
          email: 'string',
          age: 'number',
          city: 'string',
          salary: 'number',
          active: 'boolean',
          department: 'string'
        }
      },
    });

    renderComponent(manager, component);
    return container;
  },
  args: {
    striped: true,
    bordered: true,
    compact: false,
    searchable: true,
    sortable: true,
    exportable: true,
  },
};

export const SQLQueryResults: Story = {
  render: (args) => {
    const container = createContainer();
    const manager = createManager(container);

    const component = withDefaults({
      id: 'sql-dataframe',
      type: 'dataframe',
      data: {
        data: sqlQueryData,
        columns: ['TrackId', 'Name', 'AlbumId', 'MediaTypeId', 'GenreId', 'Composer', 'Milliseconds', 'Bytes', 'UnitPrice'],
        title: 'SQL Query Results',
        description: 'SELECT * FROM Track LIMIT 8',
        row_count: sqlQueryData.length,
        column_count: 9,
        striped: args.striped ?? true,
        bordered: args.bordered ?? true,
        compact: args.compact ?? false,
        searchable: args.searchable ?? true,
        sortable: args.sortable ?? true,
        exportable: args.exportable ?? true,
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

    renderComponent(manager, component);
    return container;
  },
  args: {
    striped: true,
    bordered: true,
    compact: false,
    searchable: true,
    sortable: true,
    exportable: true,
  },
};

export const CompactView: Story = {
  render: (args) => {
    const container = createContainer();
    const manager = createManager(container);

    const component = withDefaults({
      id: 'compact-dataframe',
      type: 'dataframe',
      data: {
        data: employeeData.slice(0, 6),
        columns: ['id', 'name', 'city', 'active'],
        title: 'Compact Employee View',
        description: 'Space-efficient display with essential columns only',
        row_count: 6,
        column_count: 4,
        striped: args.striped ?? true,
        bordered: args.bordered ?? false,
        compact: args.compact ?? true,
        searchable: args.searchable ?? false,
        sortable: args.sortable ?? true,
        exportable: args.exportable ?? false,
        column_types: {
          id: 'number',
          name: 'string',
          city: 'string',
          active: 'boolean'
        }
      },
    });

    renderComponent(manager, component);
    return container;
  },
  args: {
    striped: true,
    bordered: false,
    compact: true,
    searchable: false,
    sortable: true,
    exportable: false,
  },
};

export const EmptyDataFrame: Story = {
  render: () => {
    const container = createContainer();
    const manager = createManager(container);

    const component = withDefaults({
      id: 'empty-dataframe',
      type: 'dataframe',
      data: {
        data: [],
        columns: [],
        title: 'No Data Available',
        description: 'This dataset contains no records',
        row_count: 0,
        column_count: 0,
      },
    });

    renderComponent(manager, component);
    return container;
  },
};

export const LargeDataset: Story = {
  render: (args) => {
    const container = createContainer();
    const manager = createManager(container);

    // Generate a larger dataset
    const largeData = Array.from({ length: 50 }, (_, i) => ({
      id: i + 1,
      name: `User ${i + 1}`,
      email: `user${i + 1}@example.com`,
      score: Math.floor(Math.random() * 100),
      category: ['A', 'B', 'C'][i % 3],
      active: Math.random() > 0.3,
      created_date: new Date(2024, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1).toISOString().split('T')[0]
    }));

    const component = withDefaults({
      id: 'large-dataframe',
      type: 'dataframe',
      data: {
        data: largeData,
        columns: ['id', 'name', 'email', 'score', 'category', 'active', 'created_date'],
        title: 'Large Dataset',
        description: '50 records with pagination and search',
        row_count: largeData.length,
        column_count: 7,
        striped: args.striped ?? true,
        bordered: args.bordered ?? true,
        compact: args.compact ?? false,
        searchable: args.searchable ?? true,
        sortable: args.sortable ?? true,
        exportable: args.exportable ?? true,
        max_rows_displayed: 15,
        column_types: {
          id: 'number',
          name: 'string',
          email: 'string',
          score: 'number',
          category: 'string',
          active: 'boolean',
          created_date: 'date'
        }
      },
    });

    renderComponent(manager, component);
    return container;
  },
  args: {
    striped: true,
    bordered: true,
    compact: false,
    searchable: true,
    sortable: true,
    exportable: true,
  },
};

export const DataTypesShowcase: Story = {
  render: () => {
    const container = createContainer();
    const manager = createManager(container);

    const typesData = [
      {
        id: 1,
        name: 'Alice',
        score: 95.5,
        active: true,
        created: '2024-01-15',
        notes: 'Excellent performance',
        tags: null
      },
      {
        id: 2,
        name: 'Bob',
        score: 87.2,
        active: false,
        created: '2024-02-20',
        notes: 'Good but needs improvement',
        tags: 'priority,review'
      },
      {
        id: 3,
        name: 'Carol',
        score: 92.8,
        active: true,
        created: '2024-03-10',
        notes: null,
        tags: 'star-performer'
      },
    ];

    const component = withDefaults({
      id: 'types-dataframe',
      type: 'dataframe',
      data: {
        data: typesData,
        columns: ['id', 'name', 'score', 'active', 'created', 'notes', 'tags'],
        title: 'Data Types Showcase',
        description: 'Demonstrates different column data types and null handling',
        row_count: typesData.length,
        column_count: 7,
        striped: true,
        bordered: true,
        searchable: true,
        sortable: true,
        exportable: true,
        column_types: {
          id: 'number',
          name: 'string',
          score: 'number',
          active: 'boolean',
          created: 'date',
          notes: 'string',
          tags: 'string'
        }
      },
    });

    renderComponent(manager, component);
    return container;
  },
};