import type { Meta, StoryObj } from '@storybook/web-components';
import { html } from 'lit';
import './vanna-progress-tracker';

const meta: Meta = {
  title: 'Components/VannaProgressTracker',
  component: 'vanna-progress-tracker',
  parameters: {
    layout: 'centered',
    backgrounds: {
      default: 'light',
      values: [
        { name: 'dark', value: 'rgb(11, 15, 25)' },
        { name: 'light', value: '#ffffff' },
      ],
    },
  },
  argTypes: {
    title: { control: 'text' },
    theme: {
      control: 'select',
      options: ['dark', 'light'],
      description: 'Theme variant'
    },
  },
};

export default meta;
type Story = StoryObj;

export const Empty: Story = {
  args: {
    title: 'Agent Progress',
  },
  render: (args) => html`
    <div style="width: 350px; height: 400px;">
      <vanna-progress-tracker .title=${args.title}></vanna-progress-tracker>
    </div>
  `,
};

export const WithTasks: Story = {
  args: {
    title: 'Agent Progress',
    theme: 'light',
  },
  render: (args) => {
    setTimeout(() => {
      const tracker = document.querySelector('vanna-progress-tracker') as any;
      if (tracker) {
        tracker.addItem('Analyze database schema', 'Examining table structure');
        tracker.addItem('Generate SQL query', 'Based on user request');
        tracker.addItem('Execute query', 'Running against production DB');
        tracker.addItem('Format results', 'Creating visualization');

        // Update first item to in_progress
        const items = tracker.shadowRoot?.querySelectorAll('.progress-item');
        if (items?.[0]) {
          tracker.updateItem(tracker.items[0].id, 'in_progress', 'Scanning tables...');
        }
      }
    }, 100);

    return html`
      <div style="width: 350px; height: 400px; background: ${args.theme === 'light' ? '#ffffff' : 'rgb(11, 15, 25)'}; padding: 20px;">
        <vanna-progress-tracker .title=${args.title} theme=${args.theme}></vanna-progress-tracker>
      </div>
    `;
  },
};

export const WithTasksLight: Story = {
  args: {
    title: 'Agent Progress',
    theme: 'light',
  },
  render: (args) => {
    setTimeout(() => {
      const tracker = document.querySelector('vanna-progress-tracker') as any;
      if (tracker) {
        tracker.addItem('Analyze database schema', 'Examining table structure');
        tracker.addItem('Generate SQL query', 'Based on user request');
        tracker.addItem('Execute query', 'Running against production DB');
        tracker.addItem('Format results', 'Creating visualization');

        // Update first item to in_progress
        const items = tracker.shadowRoot?.querySelectorAll('.progress-item');
        if (items?.[0]) {
          tracker.updateItem(tracker.items[0].id, 'in_progress', 'Scanning tables...');
        }
      }
    }, 100);

    return html`
      <div style="width: 350px; height: 400px; background: ${args.theme === 'light' ? '#ffffff' : 'rgb(11, 15, 25)'}; padding: 20px;">
        <vanna-progress-tracker .title=${args.title} theme=${args.theme}></vanna-progress-tracker>
      </div>
    `;
  },
};

export const MixedStatuses: Story = {
  args: {
    title: 'Data Analysis Pipeline',
  },
  render: (args) => {
    setTimeout(() => {
      const tracker = document.querySelector('vanna-progress-tracker') as any;
      if (tracker) {
        const id1 = tracker.addItem('Connect to database', 'Establishing connection');
        const id2 = tracker.addItem('Validate credentials', 'Checking access permissions');
        const id3 = tracker.addItem('Load data schema', 'Reading table definitions');
        const id4 = tracker.addItem('Parse user query', 'Understanding natural language');
        const id5 = tracker.addItem('Generate SQL', 'Converting to database query');
        const id6 = tracker.addItem('Execute query', 'Running against database');
        const id7 = tracker.addItem('Process results', 'Formatting output');

        // Simulate different states
        tracker.updateItem(id1, 'completed');
        tracker.updateItem(id2, 'completed');
        tracker.updateItem(id3, 'completed');
        tracker.updateItem(id4, 'in_progress', 'Analyzing: "Show me sales by region"');
        tracker.updateItem(id5, 'pending');
        tracker.updateItem(id6, 'pending');
        tracker.updateItem(id7, 'pending');
      }
    }, 100);

    return html`
      <div style="width: 350px; height: 400px;">
        <vanna-progress-tracker .title=${args.title}></vanna-progress-tracker>
      </div>
    `;
  },
};

export const WithError: Story = {
  args: {
    title: 'Query Processing',
  },
  render: (args) => {
    setTimeout(() => {
      const tracker = document.querySelector('vanna-progress-tracker') as any;
      if (tracker) {
        const id1 = tracker.addItem('Parse request', 'Understanding user query');
        const id2 = tracker.addItem('Generate SQL', 'Creating database query');
        const id3 = tracker.addItem('Execute query', 'Running against database');
        tracker.addItem('Format results', 'Preparing visualization');

        tracker.updateItem(id1, 'completed');
        tracker.updateItem(id2, 'completed');
        tracker.updateItem(id3, 'error', 'Table "sales_data" does not exist');
        // id4 should remain pending due to error
      }
    }, 100);

    return html`
      <div style="width: 350px; height: 400px;">
        <vanna-progress-tracker .title=${args.title}></vanna-progress-tracker>
      </div>
    `;
  },
};

export const MultipleErrors: Story = {
  args: {
    title: 'Error Scenarios',
  },
  render: (args) => {
    setTimeout(() => {
      const tracker = document.querySelector('vanna-progress-tracker') as any;
      if (tracker) {
        const id1 = tracker.addItem('Connect to database', 'Establishing connection');
        const id2 = tracker.addItem('Validate schema', 'Checking table structure');
        const id3 = tracker.addItem('Parse SQL query', 'Analyzing syntax');
        tracker.addItem('Execute query', 'Running database command');
        tracker.addItem('Process results', 'Formatting output');

        tracker.updateItem(id1, 'error', 'Connection timeout - database unreachable');
        tracker.updateItem(id2, 'error', 'Invalid credentials provided');
        tracker.updateItem(id3, 'error', 'Syntax error in SQL query');
        // Other items remain pending
      }
    }, 100);

    return html`
      <div style="width: 350px; height: 400px;">
        <vanna-progress-tracker .title=${args.title}></vanna-progress-tracker>
        <p style="font-size: 12px; color: #666; margin-top: 10px;">
          Example showing multiple error states with detailed error messages
        </p>
      </div>
    `;
  },
};

export const LiveDemo: Story = {
  args: {
    title: 'Live Progress Demo',
  },
  render: (args) => {
    let tracker: any;
    let taskIds: string[] = [];
    let currentIndex = 0;

    const tasks = [
      { text: 'Initialize AI agent', detail: 'Loading language model' },
      { text: 'Analyze user request', detail: 'Processing natural language' },
      { text: 'Query database schema', detail: 'Understanding data structure' },
      { text: 'Generate SQL query', detail: 'Converting request to SQL' },
      { text: 'Execute query', detail: 'Running against database' },
      { text: 'Process results', detail: 'Formatting data for display' },
      { text: 'Generate visualization', detail: 'Creating charts and graphs' }
    ];

    const runDemo = () => {
      if (!tracker) {
        tracker = document.querySelector('vanna-progress-tracker');
        if (!tracker) {
          setTimeout(runDemo, 100);
          return;
        }
      }

      // Add all tasks as pending
      if (taskIds.length === 0) {
        taskIds = tasks.map(task => tracker.addItem(task.text, task.detail));
        currentIndex = 0;
      }

      // Process tasks one by one
      if (currentIndex < tasks.length) {
        // Mark current as in_progress
        tracker.updateItem(taskIds[currentIndex], 'in_progress', `${tasks[currentIndex].detail}...`);

        // Complete after 2 seconds, then move to next
        setTimeout(() => {
          tracker.updateItem(taskIds[currentIndex], 'completed');
          currentIndex++;

          // Continue with next task
          if (currentIndex < tasks.length) {
            setTimeout(runDemo, 500);
          } else {
            // Demo complete - restart after 3 seconds
            setTimeout(() => {
              tracker.clearItems();
              taskIds = [];
              currentIndex = 0;
              setTimeout(runDemo, 1000);
            }, 3000);
          }
        }, 2000);
      }
    };

    setTimeout(runDemo, 500);

    return html`
      <div style="width: 350px; height: 400px;">
        <vanna-progress-tracker .title=${args.title}></vanna-progress-tracker>
        <div style="margin-top: 10px; color: #999; font-size: 12px; text-align: center;">
          Watch tasks complete automatically (demo loops)
        </div>
      </div>
    `;
  },
};