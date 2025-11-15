import type { Meta, StoryObj } from '@storybook/web-components';
import { html } from 'lit';
import './rich-card';

const meta: Meta = {
  title: 'Rich Components/Rich Card',
  component: 'rich-card',
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
    subtitle: { control: 'text' },
    content: { control: 'text' },
    icon: { control: 'text' },
    status: {
      control: 'select',
      options: ['info', 'success', 'warning', 'error']
    },
    collapsible: { control: 'boolean' },
    collapsed: { control: 'boolean' },
  },
};

export default meta;
type Story = StoryObj;

export const Default: Story = {
  args: {
    title: 'Sample Card',
    subtitle: 'This is a subtitle',
    content: 'This is the content of the card. It can contain any text or HTML.',
    status: 'info',
    collapsible: false,
    collapsed: false,
  },
  render: (args) => html`
    <div style="max-width: 600px; margin: 0 auto;">
      <rich-card
        title=${args.title}
        subtitle=${args.subtitle}
        content=${args.content}
        icon=${args.icon}
        status=${args.status}
        ?collapsible=${args.collapsible}
        ?collapsed=${args.collapsed}>
      </rich-card>
    </div>
  `,
};

export const WithIcon: Story = {
  args: {
    title: 'Card with Icon',
    subtitle: 'Featuring an emoji icon',
    content: 'This card demonstrates how icons work with the rich card component.',
    icon: '🚀',
    status: 'success',
    collapsible: false,
  },
  render: (args) => html`
    <div style="max-width: 600px; margin: 0 auto;">
      <rich-card
        title=${args.title}
        subtitle=${args.subtitle}
        content=${args.content}
        icon=${args.icon}
        status=${args.status}
        ?collapsible=${args.collapsible}>
      </rich-card>
    </div>
  `,
};

export const WithActions: Story = {
  args: {
    title: 'Interactive Card',
    subtitle: 'With action buttons',
    content: 'This card includes action buttons that can trigger events.',
    status: 'info',
    collapsible: false,
  },
  render: (args) => html`
    <div style="max-width: 600px; margin: 0 auto;">
      <rich-card
        title=${args.title}
        subtitle=${args.subtitle}
        content=${args.content}
        status=${args.status}
        ?collapsible=${args.collapsible}
        .actions=${[
          { label: 'Primary Action', action: 'primary', variant: 'primary' },
          { label: 'Secondary Action', action: 'secondary', variant: 'secondary' }
        ]}
        @card-action=${(e: CustomEvent) => {
          console.log('Card action:', e.detail.action);
          alert(`Action triggered: ${e.detail.action}`);
        }}>
      </rich-card>
    </div>
  `,
};

export const Collapsible: Story = {
  args: {
    title: 'Collapsible Card',
    subtitle: 'Click to expand/collapse',
    content: 'This content can be hidden by clicking the toggle button in the header.',
    status: 'warning',
    collapsible: true,
    collapsed: false,
  },
  render: (args) => html`
    <div style="max-width: 600px; margin: 0 auto;">
      <rich-card
        title=${args.title}
        subtitle=${args.subtitle}
        content=${args.content}
        status=${args.status}
        ?collapsible=${args.collapsible}
        ?collapsed=${args.collapsed}>
      </rich-card>
    </div>
  `,
};

export const StatusVariants: Story = {
  render: () => html`
    <div style="max-width: 600px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px;">
      <rich-card
        title="Info Status"
        content="This card shows the info status variant."
        status="info">
      </rich-card>

      <rich-card
        title="Success Status"
        content="This card shows the success status variant."
        status="success">
      </rich-card>

      <rich-card
        title="Warning Status"
        content="This card shows the warning status variant."
        status="warning">
      </rich-card>

      <rich-card
        title="Error Status"
        content="This card shows the error status variant."
        status="error">
      </rich-card>
    </div>
  `,
};

export const LightTheme: Story = {
  args: {
    title: 'Light Theme Card',
    subtitle: 'Styled for light backgrounds',
    content: 'This card is displayed with the light theme variant.',
    icon: '☀️',
    status: 'success',
  },
  parameters: {
    backgrounds: { default: 'light' }
  },
  render: (args) => html`
    <div style="max-width: 600px; margin: 0 auto;">
      <rich-card
        theme="light"
        title=${args.title}
        subtitle=${args.subtitle}
        content=${args.content}
        icon=${args.icon}
        status=${args.status}>
      </rich-card>
    </div>
  `,
};