import type { Meta, StoryObj } from '@storybook/web-components';
import { ComponentManager, ComponentUpdate } from './rich-component-system';
import { vannaDesignTokens } from '../styles/vanna-design-tokens.js';

const meta: Meta = {
  title: 'Rich Components/Buttons',
  parameters: {
    layout: 'padded',
    backgrounds: {
      default: 'dark',
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

const addMockVannaChat = (container: HTMLElement) => {
  // Create a mock vanna-chat element with sendMessage method
  const mockVannaChat = document.createElement('div');
  mockVannaChat.setAttribute('id', 'mock-vanna-chat');

  // Store the original querySelector
  const originalQuerySelector = document.querySelector.bind(document);

  // Override querySelector to return our mock when looking for vanna-chat
  document.querySelector = function(selector: string) {
    if (selector === 'vanna-chat') {
      return mockVannaChat as any;
    }
    return originalQuerySelector(selector);
  } as any;

  // Add sendMessage method that logs to console and shows in UI
  (mockVannaChat as any).sendMessage = (message: string) => {
    console.log('📤 Button clicked - Message:', message);

    // Show a visual feedback in the storybook
    const feedback = document.createElement('div');
    feedback.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #4CAF50;
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.3);
      font-family: monospace;
      z-index: 10000;
      animation: slideIn 0.3s ease-out;
    `;
    feedback.textContent = `Message sent: ${message}`;

    // Add animation
    const style = document.createElement('style');
    style.textContent = `
      @keyframes slideIn {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
    `;
    document.head.appendChild(style);

    document.body.appendChild(feedback);

    setTimeout(() => {
      feedback.style.opacity = '0';
      feedback.style.transition = 'opacity 0.3s ease-out';
      setTimeout(() => feedback.remove(), 300);
    }, 2000);
  };

  container.appendChild(mockVannaChat);
  return mockVannaChat;
};

export const SingleButtons: Story = {
  render: () => {
    const container = createContainer();
    const manager = createManager(container);
    addMockVannaChat(container);

    // Add title
    const title = document.createElement('h2');
    title.textContent = 'Single Button Components';
    title.style.cssText = 'margin-bottom: 20px; color: var(--vanna-text-primary);';
    container.appendChild(title);

    const buttons = [
      withDefaults({
        id: 'primary-button',
        type: 'button',
        data: {
          label: 'Primary Action',
          action: 'primary_action',
          variant: 'primary',
          size: 'medium',
        },
      }),
      withDefaults({
        id: 'secondary-button',
        type: 'button',
        data: {
          label: 'Save Draft',
          action: 'save_draft',
          variant: 'secondary',
          size: 'medium',
          icon: '💾',
          icon_position: 'left',
        },
      }),
      withDefaults({
        id: 'success-button',
        type: 'button',
        data: {
          label: 'Approve',
          action: 'approve',
          variant: 'success',
          size: 'medium',
          icon: '✓',
        },
      }),
      withDefaults({
        id: 'warning-button',
        type: 'button',
        data: {
          label: 'Caution',
          action: 'warning',
          variant: 'warning',
          size: 'medium',
          icon: '⚠️',
        },
      }),
      withDefaults({
        id: 'error-button',
        type: 'button',
        data: {
          label: 'Delete',
          action: 'delete',
          variant: 'error',
          size: 'medium',
          icon: '🗑️',
        },
      }),
      withDefaults({
        id: 'ghost-button',
        type: 'button',
        data: {
          label: 'Ghost Style',
          action: 'ghost',
          variant: 'ghost',
          icon: '👻',
        },
      }),
      withDefaults({
        id: 'link-button',
        type: 'button',
        data: {
          label: 'Learn More',
          action: 'learn_more',
          variant: 'link',
        },
      }),
      withDefaults({
        id: 'loading-button',
        type: 'button',
        data: {
          label: 'Processing...',
          action: 'loading',
          variant: 'primary',
          loading: true,
        },
      }),
      withDefaults({
        id: 'disabled-button',
        type: 'button',
        data: {
          label: 'Disabled',
          action: 'disabled',
          variant: 'secondary',
          disabled: true,
        },
      }),
    ];

    buttons.forEach((component) => {
      renderComponent(manager, component);
      // Add some spacing
      const spacer = document.createElement('div');
      spacer.style.height = '12px';
      container.appendChild(spacer);
    });

    // Add instruction
    const instruction = document.createElement('p');
    instruction.textContent = 'Click any button to see the message it sends (wrapped in square brackets)';
    instruction.style.cssText = 'margin-top: 20px; color: var(--vanna-text-secondary); font-style: italic;';
    container.appendChild(instruction);

    return container;
  },
};

export const ButtonSizes: Story = {
  render: () => {
    const container = createContainer();
    const manager = createManager(container);
    addMockVannaChat(container);

    const title = document.createElement('h2');
    title.textContent = 'Button Sizes';
    title.style.cssText = 'margin-bottom: 20px; color: var(--vanna-text-primary);';
    container.appendChild(title);

    const sizes = ['small', 'medium', 'large'];

    sizes.forEach((size) => {
      const button = withDefaults({
        id: `button-${size}`,
        type: 'button',
        data: {
          label: `${size.charAt(0).toUpperCase() + size.slice(1)} Button`,
          action: `${size}_action`,
          variant: 'primary',
          size,
          icon: '⭐',
        },
      });

      renderComponent(manager, button);

      const spacer = document.createElement('div');
      spacer.style.height = '12px';
      container.appendChild(spacer);
    });

    return container;
  },
};

export const ButtonGroups: Story = {
  render: () => {
    const container = createContainer();
    const manager = createManager(container);
    addMockVannaChat(container);

    const title = document.createElement('h2');
    title.textContent = 'Button Group Components';
    title.style.cssText = 'margin-bottom: 20px; color: var(--vanna-text-primary);';
    container.appendChild(title);

    // Horizontal action group
    const actionGroup = withDefaults({
      id: 'action-group',
      type: 'button_group',
      data: {
        buttons: [
          {
            label: 'Accept',
            action: 'accept',
            variant: 'success',
            icon: '✓',
          },
          {
            label: 'Reject',
            action: 'reject',
            variant: 'error',
            icon: '✗',
          },
          {
            label: 'Cancel',
            action: 'cancel',
            variant: 'secondary',
          },
        ],
        orientation: 'horizontal',
        spacing: 'medium',
        align: 'left',
      },
    });

    const sectionTitle1 = document.createElement('h3');
    sectionTitle1.textContent = 'Horizontal Action Group';
    sectionTitle1.style.cssText = 'margin: 20px 0 10px 0; color: var(--vanna-text-primary); font-size: 16px;';
    container.appendChild(sectionTitle1);
    renderComponent(manager, actionGroup);

    // Centered navigation
    const navigationGroup = withDefaults({
      id: 'navigation-group',
      type: 'button_group',
      data: {
        buttons: [
          {
            label: 'Back',
            action: 'back',
            variant: 'ghost',
            icon: '←',
          },
          {
            label: 'Continue',
            action: 'continue',
            variant: 'primary',
            icon: '→',
            icon_position: 'right',
          },
        ],
        orientation: 'horizontal',
        spacing: 'large',
        align: 'center',
      },
    });

    const sectionTitle2 = document.createElement('h3');
    sectionTitle2.textContent = 'Centered Navigation';
    sectionTitle2.style.cssText = 'margin: 20px 0 10px 0; color: var(--vanna-text-primary); font-size: 16px;';
    container.appendChild(sectionTitle2);
    renderComponent(manager, navigationGroup);

    // Vertical options
    const verticalGroup = withDefaults({
      id: 'vertical-group',
      type: 'button_group',
      data: {
        buttons: [
          { label: 'Option 1', action: 'option1', variant: 'secondary' },
          { label: 'Option 2', action: 'option2', variant: 'secondary' },
          { label: 'Option 3', action: 'option3', variant: 'secondary' },
        ],
        orientation: 'vertical',
        spacing: 'small',
        align: 'left',
      },
    });

    const sectionTitle3 = document.createElement('h3');
    sectionTitle3.textContent = 'Vertical Options';
    sectionTitle3.style.cssText = 'margin: 20px 0 10px 0; color: var(--vanna-text-primary); font-size: 16px;';
    container.appendChild(sectionTitle3);
    renderComponent(manager, verticalGroup);

    // Toolbar
    const toolbarGroup = withDefaults({
      id: 'toolbar-group',
      type: 'button_group',
      data: {
        buttons: [
          {
            label: 'New',
            action: 'new',
            variant: 'primary',
            icon: '➕',
            size: 'small',
          },
          {
            label: 'Edit',
            action: 'edit',
            variant: 'secondary',
            icon: '✏️',
            size: 'small',
          },
          {
            label: 'Delete',
            action: 'delete',
            variant: 'error',
            icon: '🗑️',
            size: 'small',
          },
          {
            label: 'Share',
            action: 'share',
            variant: 'ghost',
            icon: '🔗',
            size: 'small',
          },
        ],
        orientation: 'horizontal',
        spacing: 'small',
        align: 'left',
      },
    });

    const sectionTitle4 = document.createElement('h3');
    sectionTitle4.textContent = 'Toolbar (Small Buttons)';
    sectionTitle4.style.cssText = 'margin: 20px 0 10px 0; color: var(--vanna-text-primary); font-size: 16px;';
    container.appendChild(sectionTitle4);
    renderComponent(manager, toolbarGroup);

    // Full width confirmation
    const confirmationGroup = withDefaults({
      id: 'confirmation-group',
      type: 'button_group',
      data: {
        buttons: [
          { label: 'Yes', action: 'yes', variant: 'success' },
          { label: 'No', action: 'no', variant: 'error' },
        ],
        orientation: 'horizontal',
        spacing: 'medium',
        align: 'space-between',
        full_width: true,
      },
    });

    const sectionTitle5 = document.createElement('h3');
    sectionTitle5.textContent = 'Full Width Confirmation';
    sectionTitle5.style.cssText = 'margin: 20px 0 10px 0; color: var(--vanna-text-primary); font-size: 16px;';
    container.appendChild(sectionTitle5);
    renderComponent(manager, confirmationGroup);

    // Add instruction
    const instruction = document.createElement('p');
    instruction.textContent = 'Click any button in the groups to see the message it sends';
    instruction.style.cssText = 'margin-top: 20px; color: var(--vanna-text-secondary); font-style: italic;';
    container.appendChild(instruction);

    return container;
  },
};

export const InteractiveDemo: Story = {
  render: () => {
    const container = createContainer();
    const manager = createManager(container);
    addMockVannaChat(container);

    const title = document.createElement('h2');
    title.textContent = 'Interactive Button Demo';
    title.style.cssText = 'margin-bottom: 20px; color: var(--vanna-text-primary);';
    container.appendChild(title);

    const description = document.createElement('p');
    description.textContent = 'This demo shows how buttons send messages with their labels wrapped in square brackets.';
    description.style.cssText = 'margin-bottom: 20px; color: var(--vanna-text-secondary);';
    container.appendChild(description);

    // Simple choice buttons
    const choiceGroup = withDefaults({
      id: 'choice-group',
      type: 'button_group',
      data: {
        buttons: [
          { label: 'Okay', action: 'okay', variant: 'primary' },
          { label: 'Not now', action: 'not_now', variant: 'secondary' },
          { label: 'Never', action: 'never', variant: 'ghost' },
        ],
        orientation: 'horizontal',
        spacing: 'medium',
        align: 'center',
      },
    });

    renderComponent(manager, choiceGroup);

    const codeExample = document.createElement('pre');
    codeExample.textContent = `// When you click "Okay", the message sent is: [Okay]
// When you click "Not now", the message sent is: [Not now]
// When you click "Never", the message sent is: [Never]`;
    codeExample.style.cssText = `
      margin-top: 20px;
      padding: 12px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 6px;
      color: #a0aec0;
      font-size: 12px;
      font-family: 'Courier New', monospace;
      overflow-x: auto;
    `;
    container.appendChild(codeExample);

    return container;
  },
};
