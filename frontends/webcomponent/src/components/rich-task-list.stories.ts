import type { Meta, StoryObj } from '@storybook/web-components';
import { html } from 'lit';
import './rich-task-list';

const meta: Meta = {
  title: 'Rich Components/Rich Task List',
  component: 'rich-task-list',
  parameters: {
    layout: 'padded',
    backgrounds: {
      default: 'light',
      values: [
        { name: 'dark', value: 'rgb(11, 15, 25)' },
        { name: 'light', value: '#f5f7fa' },
      ],
    },
  },
  argTypes: {
    title: { control: 'text' },
    tasks: { control: 'object' },
    showProgress: { control: 'boolean' },
    showTimestamps: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj;

const sampleTasks = [
  {
    id: '1',
    title: 'Initialize project setup',
    description: 'Setting up the basic project structure and dependencies',
    status: 'completed',
    progress: 1.0,
    timestamp: '2024-01-15 10:30:00'
  },
  {
    id: '2',
    title: 'Configure database connection',
    description: 'Establishing secure connection to PostgreSQL database',
    status: 'completed',
    progress: 1.0,
    timestamp: '2024-01-15 10:45:00'
  },
  {
    id: '3',
    title: 'Implement user authentication',
    description: 'Building JWT-based authentication system',
    status: 'running',
    progress: 0.7,
    timestamp: '2024-01-15 11:00:00'
  },
  {
    id: '4',
    title: 'Create API endpoints',
    description: 'Developing RESTful API for user management',
    status: 'pending',
    timestamp: '2024-01-15 11:30:00'
  },
  {
    id: '5',
    title: 'Write unit tests',
    description: 'Comprehensive test coverage for all modules',
    status: 'pending',
  }
];

export const Default: Story = {
  args: {
    title: 'Development Tasks',
    tasks: sampleTasks,
    showProgress: true,
    showTimestamps: false,
  },
  render: (args) => html`
    <div style="max-width: 600px; margin: 0 auto;">
      <rich-task-list
        title=${args.title}
        .tasks=${args.tasks}
        ?showProgress=${args.showProgress}
        ?showTimestamps=${args.showTimestamps}>
      </rich-task-list>
    </div>
  `,
};

export const WithTimestamps: Story = {
  args: {
    title: 'Build Pipeline',
    tasks: sampleTasks,
    showProgress: true,
    showTimestamps: true,
  },
  render: (args) => html`
    <div style="max-width: 600px; margin: 0 auto;">
      <rich-task-list
        title=${args.title}
        .tasks=${args.tasks}
        ?showProgress=${args.showProgress}
        ?showTimestamps=${args.showTimestamps}>
      </rich-task-list>
    </div>
  `,
};

export const WithoutProgress: Story = {
  args: {
    title: 'Simple Task List',
    tasks: [
      { id: '1', title: 'Review code changes', status: 'completed' },
      { id: '2', title: 'Update documentation', status: 'running' },
      { id: '3', title: 'Deploy to staging', status: 'pending' },
      { id: '4', title: 'Run integration tests', status: 'failed' },
    ],
    showProgress: false,
    showTimestamps: false,
  },
  render: (args) => html`
    <div style="max-width: 600px; margin: 0 auto;">
      <rich-task-list
        title=${args.title}
        .tasks=${args.tasks}
        ?showProgress=${args.showProgress}
        ?showTimestamps=${args.showTimestamps}>
      </rich-task-list>
    </div>
  `,
};

export const AllStatuses: Story = {
  args: {
    title: 'Task Status Examples',
    tasks: [
      {
        id: '1',
        title: 'Completed Task',
        description: 'This task has been successfully completed',
        status: 'completed',
        progress: 1.0,
      },
      {
        id: '2',
        title: 'Running Task',
        description: 'This task is currently in progress',
        status: 'running',
        progress: 0.6,
      },
      {
        id: '3',
        title: 'Pending Task',
        description: 'This task is waiting to be started',
        status: 'pending',
      },
      {
        id: '4',
        title: 'Failed Task',
        description: 'This task encountered an error',
        status: 'failed',
        progress: 0.3,
      },
    ],
    showProgress: true,
    showTimestamps: false,
  },
  render: (args) => html`
    <div style="max-width: 600px; margin: 0 auto;">
      <rich-task-list
        title=${args.title}
        .tasks=${args.tasks}
        ?showProgress=${args.showProgress}
        ?showTimestamps=${args.showTimestamps}>
      </rich-task-list>
    </div>
  `,
};

export const EmptyList: Story = {
  args: {
    title: 'No Tasks',
    tasks: [],
    showProgress: true,
    showTimestamps: false,
  },
  render: (args) => html`
    <div style="max-width: 600px; margin: 0 auto;">
      <rich-task-list
        title=${args.title}
        .tasks=${args.tasks}
        ?showProgress=${args.showProgress}
        ?showTimestamps=${args.showTimestamps}>
      </rich-task-list>
    </div>
  `,
};

export const ErrorStates: Story = {
  args: {
    title: 'Error Handling Examples',
    tasks: [
      {
        id: '1',
        title: 'Database Connection Failed',
        description: 'Could not establish connection to the database server. Check network connectivity and credentials.',
        status: 'failed',
        progress: 0.1,
        timestamp: '2024-01-15 10:15:00'
      },
      {
        id: '2',
        title: 'API Authentication Error',
        description: 'Invalid API key or expired token. Please refresh your credentials.',
        status: 'failed',
        progress: 0.0,
        timestamp: '2024-01-15 10:20:00'
      },
      {
        id: '3',
        title: 'File Processing Error',
        description: 'Unable to process uploaded file. File may be corrupted or in an unsupported format.',
        status: 'failed',
        progress: 0.45,
        timestamp: '2024-01-15 10:25:00'
      },
      {
        id: '4',
        title: 'Network Timeout',
        description: 'Request timed out after 30 seconds. This may be due to high server load.',
        status: 'failed',
        progress: 0.8,
        timestamp: '2024-01-15 10:30:00'
      },
    ],
    showProgress: true,
    showTimestamps: true,
  },
  render: (args) => html`
    <div style="max-width: 600px; margin: 0 auto;">
      <rich-task-list
        title=${args.title}
        .tasks=${args.tasks}
        ?showProgress=${args.showProgress}
        ?showTimestamps=${args.showTimestamps}>
      </rich-task-list>
    </div>
  `,
};

export const LightTheme: Story = {
  args: {
    title: 'Light Theme Task List',
    tasks: sampleTasks.slice(0, 3),
    showProgress: true,
    showTimestamps: true,
  },
  parameters: {
    backgrounds: { default: 'light' }
  },
  render: (args) => html`
    <div style="max-width: 600px; margin: 0 auto;">
      <rich-task-list
        theme="light"
        title=${args.title}
        .tasks=${args.tasks}
        ?showProgress=${args.showProgress}
        ?showTimestamps=${args.showTimestamps}>
      </rich-task-list>
    </div>
  `,
};