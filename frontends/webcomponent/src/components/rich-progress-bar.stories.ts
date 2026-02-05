import type { Meta, StoryObj } from '@storybook/web-components';
import { html } from 'lit';
import './rich-progress-bar';

const meta: Meta = {
  title: 'Rich Components/Rich Progress Bar',
  component: 'rich-progress-bar',
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
    value: { control: { type: 'range', min: 0, max: 1, step: 0.01 } },
    label: { control: 'text' },
    description: { control: 'text' },
    showPercentage: { control: 'boolean' },
    status: {
      control: 'select',
      options: ['info', 'success', 'warning', 'error']
    },
    animated: { control: 'boolean' },
    indeterminate: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj;

export const Default: Story = {
  args: {
    value: 0.65,
    label: 'Processing',
    showPercentage: true,
    status: 'info',
    animated: false,
    indeterminate: false,
  },
  render: (args) => html`
    <div style="max-width: 500px; margin: 0 auto;">
      <rich-progress-bar
        .value=${args.value}
        label=${args.label}
        description=${args.description}
        ?showPercentage=${args.showPercentage}
        status=${args.status}
        ?animated=${args.animated}
        ?indeterminate=${args.indeterminate}>
      </rich-progress-bar>
    </div>
  `,
};

export const WithDescription: Story = {
  args: {
    value: 0.4,
    label: 'Installing dependencies',
    description: 'Downloading and installing npm packages for the project. This may take a few minutes.',
    showPercentage: true,
    status: 'info',
    animated: true,
    indeterminate: false,
  },
  render: (args) => html`
    <div style="max-width: 500px; margin: 0 auto;">
      <rich-progress-bar
        .value=${args.value}
        label=${args.label}
        description=${args.description}
        ?showPercentage=${args.showPercentage}
        status=${args.status}
        ?animated=${args.animated}
        ?indeterminate=${args.indeterminate}>
      </rich-progress-bar>
    </div>
  `,
};

export const Animated: Story = {
  args: {
    value: 0.75,
    label: 'Uploading files',
    showPercentage: true,
    status: 'info',
    animated: true,
    indeterminate: false,
  },
  render: (args) => html`
    <div style="max-width: 500px; margin: 0 auto;">
      <rich-progress-bar
        .value=${args.value}
        label=${args.label}
        description=${args.description}
        ?showPercentage=${args.showPercentage}
        status=${args.status}
        ?animated=${args.animated}
        ?indeterminate=${args.indeterminate}>
      </rich-progress-bar>
    </div>
  `,
};

export const Indeterminate: Story = {
  args: {
    value: 0,
    label: 'Loading...',
    description: 'Please wait while we process your request',
    showPercentage: false,
    status: 'info',
    animated: false,
    indeterminate: true,
  },
  render: (args) => html`
    <div style="max-width: 500px; margin: 0 auto;">
      <rich-progress-bar
        .value=${args.value}
        label=${args.label}
        description=${args.description}
        ?showPercentage=${args.showPercentage}
        status=${args.status}
        ?animated=${args.animated}
        ?indeterminate=${args.indeterminate}>
      </rich-progress-bar>
    </div>
  `,
};

export const StatusVariants: Story = {
  render: () => html`
    <div style="max-width: 500px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px;">
      <rich-progress-bar
        .value=${0.8}
        label="Info Status"
        status="info"
        showPercentage>
      </rich-progress-bar>

      <rich-progress-bar
        .value=${1.0}
        label="Success Status"
        status="success"
        showPercentage>
      </rich-progress-bar>

      <rich-progress-bar
        .value=${0.6}
        label="Warning Status"
        status="warning"
        showPercentage>
      </rich-progress-bar>

      <rich-progress-bar
        .value=${0.3}
        label="Error Status"
        status="error"
        showPercentage>
      </rich-progress-bar>
    </div>
  `,
};

export const Minimal: Story = {
  args: {
    value: 0.45,
    showPercentage: false,
    status: 'info',
    animated: false,
    indeterminate: false,
  },
  render: (args) => html`
    <div style="max-width: 500px; margin: 0 auto;">
      <rich-progress-bar
        .value=${args.value}
        ?showPercentage=${args.showPercentage}
        status=${args.status}
        ?animated=${args.animated}
        ?indeterminate=${args.indeterminate}>
      </rich-progress-bar>
    </div>
  `,
};

export const MultipleSteps: Story = {
  render: () => html`
    <div style="max-width: 500px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px;">
      <rich-progress-bar
        .value=${1.0}
        label="Step 1: Initialize"
        description="Project initialization completed"
        status="success"
        showPercentage>
      </rich-progress-bar>

      <rich-progress-bar
        .value=${1.0}
        label="Step 2: Download dependencies"
        description="All packages downloaded successfully"
        status="success"
        showPercentage>
      </rich-progress-bar>

      <rich-progress-bar
        .value=${0.7}
        label="Step 3: Build project"
        description="Compiling TypeScript and bundling assets"
        status="info"
        animated
        showPercentage>
      </rich-progress-bar>

      <rich-progress-bar
        .value=${0}
        label="Step 4: Deploy"
        description="Waiting for build to complete"
        status="info"
        showPercentage>
      </rich-progress-bar>
    </div>
  `,
};

export const LightTheme: Story = {
  args: {
    value: 0.55,
    label: 'Light Theme Progress',
    description: 'Progress bar styled for light backgrounds',
    showPercentage: true,
    status: 'success',
    animated: true,
  },
  parameters: {
    backgrounds: { default: 'light' }
  },
  render: (args) => html`
    <div style="max-width: 500px; margin: 0 auto;">
      <rich-progress-bar
        theme="light"
        .value=${args.value}
        label=${args.label}
        description=${args.description}
        ?showPercentage=${args.showPercentage}
        status=${args.status}
        ?animated=${args.animated}>
      </rich-progress-bar>
    </div>
  `,
};