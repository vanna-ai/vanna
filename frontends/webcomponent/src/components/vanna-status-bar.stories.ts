import type { Meta, StoryObj } from '@storybook/web-components';
import { html } from 'lit';
import './vanna-status-bar';

const meta: Meta = {
  title: 'Components/VannaStatusBar',
  component: 'vanna-status-bar',
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
    status: {
      control: 'select',
      options: ['idle', 'working', 'error', 'success'],
    },
    message: { control: 'text' },
    detail: { control: 'text' },
    theme: {
      control: 'select',
      options: ['dark', 'light'],
      description: 'Theme variant'
    },
  },
};

export default meta;
type Story = StoryObj;

export const Idle: Story = {
  args: {
    status: 'idle',
    message: '',
    detail: '',
  },
  render: (args) => html`
    <div style="width: 500px; padding: 20px;">
      <vanna-status-bar
        .status=${args.status}
        .message=${args.message}
        .detail=${args.detail}>
      </vanna-status-bar>
      <div style="margin-top: 10px; color: #999; font-size: 12px;">
        Status bar is hidden when idle
      </div>
    </div>
  `,
};

export const Working: Story = {
  args: {
    status: 'working',
    message: 'Analyzing your database schema...',
    detail: 'Step 1 of 3',
    theme: 'light',
  },
  render: (args) => html`
    <div style="width: 500px; padding: 20px; background: ${args.theme === 'light' ? '#ffffff' : 'rgb(11, 15, 25)'};">
      <vanna-status-bar
        .status=${args.status}
        .message=${args.message}
        .detail=${args.detail}
        theme=${args.theme}>
      </vanna-status-bar>
    </div>
  `,
};

export const WorkingLight: Story = {
  args: {
    status: 'working',
    message: 'Analyzing your database schema...',
    detail: 'Step 1 of 3',
    theme: 'light',
  },
  render: (args) => html`
    <div style="width: 500px; padding: 20px; background: ${args.theme === 'light' ? '#ffffff' : 'rgb(11, 15, 25)'};">
      <vanna-status-bar
        .status=${args.status}
        .message=${args.message}
        .detail=${args.detail}
        theme=${args.theme}>
      </vanna-status-bar>
    </div>
  `,
};

export const Success: Story = {
  args: {
    status: 'success',
    message: 'Query executed successfully',
    detail: '2.3s',
  },
  render: (args) => html`
    <div style="width: 500px; padding: 20px;">
      <vanna-status-bar
        .status=${args.status}
        .message=${args.message}
        .detail=${args.detail}>
      </vanna-status-bar>
    </div>
  `,
};

export const Error: Story = {
  args: {
    status: 'error',
    message: 'Failed to connect to database',
    detail: 'Connection timeout after 30s',
  },
  render: (args) => html`
    <div style="width: 500px; padding: 20px;">
      <vanna-status-bar
        .status=${args.status}
        .message=${args.message}
        .detail=${args.detail}>
      </vanna-status-bar>
    </div>
  `,
};

export const StatusSequence: Story = {
  render: () => {
    let statusBar: any;
    let currentIndex = 0;
    const statuses = [
      { status: 'working', message: 'Starting analysis...', detail: 'Initializing' },
      { status: 'working', message: 'Querying database...', detail: 'Step 1 of 3' },
      { status: 'working', message: 'Processing results...', detail: 'Step 2 of 3' },
      { status: 'working', message: 'Generating visualization...', detail: 'Step 3 of 3' },
      { status: 'success', message: 'Analysis complete!', detail: '4.2s total' },
    ];

    const updateStatus = () => {
      if (statusBar && currentIndex < statuses.length) {
        const current = statuses[currentIndex];
        statusBar.status = current.status;
        statusBar.message = current.message;
        statusBar.detail = current.detail;
        currentIndex++;

        if (currentIndex < statuses.length) {
          setTimeout(updateStatus, 2000);
        }
      }
    };

    setTimeout(() => {
      statusBar = document.querySelector('vanna-status-bar');
      updateStatus();
    }, 100);

    return html`
      <div style="width: 500px; padding: 20px;">
        <vanna-status-bar status="idle"></vanna-status-bar>
        <div style="margin-top: 10px; color: #999; font-size: 12px;">
          Watch the status bar cycle through different states
        </div>
      </div>
    `;
  },
};