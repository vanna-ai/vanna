import type { Preview } from '@storybook/web-components';

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    docs: {
      autodocs: 'tag',
    },
  },
};

export default preview;