import type { Meta, StoryObj } from '@storybook/web-components';
import { html } from 'lit';
import './vanna-message';

const meta: Meta = {
  title: 'Components/VannaMessage',
  component: 'vanna-message',
  parameters: {
    layout: 'centered',
  },
  argTypes: {
    content: { control: 'text' },
    type: {
      control: 'select',
      options: ['user', 'assistant'],
    },
    timestamp: { control: 'number' },
  },
};

export default meta;
type Story = StoryObj;

export const UserMessage: Story = {
  args: {
    content: 'Hello! Can you help me analyze my data?',
    type: 'user',
    timestamp: Date.now(),
  },
  render: (args) => html`
    <div style="width: 400px;">
      <vanna-message
        .content=${args.content}
        .type=${args.type}
        .timestamp=${args.timestamp}>
      </vanna-message>
    </div>
  `,
};

export const AssistantMessage: Story = {
  args: {
    content: 'Of course! I\'d be happy to help you analyze your data. Could you please tell me more about the type of data you have and what insights you\'re looking for?',
    type: 'assistant',
    timestamp: Date.now(),
  },
  render: (args) => html`
    <div style="width: 400px;">
      <vanna-message
        .content=${args.content}
        .type=${args.type}
        .timestamp=${args.timestamp}>
      </vanna-message>
    </div>
  `,
};

export const LongMessage: Story = {
  args: {
    content: 'This is a very long message that demonstrates how the component handles longer text content. It should wrap properly and maintain good readability while staying within the maximum width constraints. The message can contain multiple sentences and paragraphs of information that the AI assistant might provide in response to complex queries.',
    type: 'assistant',
    timestamp: Date.now(),
  },
  render: (args) => html`
    <div style="width: 400px;">
      <vanna-message
        .content=${args.content}
        .type=${args.type}
        .timestamp=${args.timestamp}>
      </vanna-message>
    </div>
  `,
};

export const Conversation: Story = {
  render: () => html`
    <div style="width: 400px;">
      <vanna-message
        content="What's the total revenue for Q4?"
        type="user"
        .timestamp=${Date.now() - 120000}>
      </vanna-message>
      <vanna-message
        content="I'll help you calculate the total revenue for Q4. Let me query your database for this information."
        type="assistant"
        .timestamp=${Date.now() - 60000}>
      </vanna-message>
      <vanna-message
        content="The total revenue for Q4 is $2,450,000. This represents a 15% increase compared to Q3."
        type="assistant"
        .timestamp=${Date.now()}>
      </vanna-message>
    </div>
  `,
};