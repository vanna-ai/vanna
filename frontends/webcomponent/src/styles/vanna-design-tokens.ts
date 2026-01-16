import { css } from 'lit';

// Vanna 2.0 design tokens - Data-First Agents branding
export const vannaDesignTokens = css`
  :host {
    /* Vanna 2.0 Brand Colors */
    --vanna-navy: #013DFF;
    --vanna-cream: rgb(231, 225, 207);
    --vanna-teal: #013DFF;
    --vanna-orange: rgb(254, 93, 38);
    --vanna-magenta: rgb(191, 19, 99);

    /* Color Palette - Light mode (default) */
    --vanna-background-root: rgb(255, 255, 255);
    --vanna-background-default: rgb(231, 225, 207);
    --vanna-background-higher: rgb(244, 246, 248);
    --vanna-background-highest: rgb(229, 231, 235);
    --vanna-background-subtle: rgb(248, 250, 252);
    --vanna-background-lower: rgb(239, 242, 245);

    --vanna-foreground-default: rgb(2, 61, 96);
    --vanna-foreground-dimmer: rgb(71, 85, 105);
    --vanna-foreground-dimmest: rgb(100, 116, 139);

    --vanna-accent-primary-default: #013DFF;
    --vanna-accent-primary-stronger: rgb(2, 61, 96);
    --vanna-accent-primary-strongest: rgb(2, 61, 96);
    --vanna-accent-primary-subtle: rgba(21, 168, 168, 0.1);
    --vanna-accent-primary-hover: #013DFF;

    --vanna-accent-positive-default: #013DFF;
    --vanna-accent-positive-stronger: rgb(2, 61, 96);
    --vanna-accent-positive-subtle: rgba(21, 168, 168, 0.1);

    --vanna-accent-negative-default: rgb(239, 68, 68);
    --vanna-accent-negative-stronger: rgb(220, 38, 38);
    --vanna-accent-negative-subtle: rgba(239, 68, 68, 0.1);

    --vanna-accent-warning-default: rgb(254, 93, 38);
    --vanna-accent-warning-stronger: rgb(254, 93, 38);
    --vanna-accent-warning-subtle: rgba(254, 93, 38, 0.1);

    /* Outline/Border colors */
    --vanna-outline-default: rgba(21, 168, 168, 0.3);
    --vanna-outline-dimmer: rgb(241, 245, 249);
    --vanna-outline-dimmest: rgb(248, 250, 252);
    --vanna-outline-hover: #013DFF;

    /* Typography */
    --vanna-font-family-default: "Space Grotesk", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
    --vanna-font-family-serif: "Roboto Slab", ui-serif, Georgia, serif;
    --vanna-font-family-mono: "Space Mono", ui-monospace, SFMono-Regular, "SF Mono", Monaco, Inconsolata, "Roboto Mono", "Ubuntu Mono", monospace;

    /* Spacing scale */
    --vanna-space-0: 0px;
    --vanna-space-1: 4px;
    --vanna-space-2: 8px;
    --vanna-space-3: 12px;
    --vanna-space-4: 16px;
    --vanna-space-5: 20px;
    --vanna-space-6: 24px;
    --vanna-space-7: 28px;
    --vanna-space-8: 32px;
    --vanna-space-10: 40px;
    --vanna-space-12: 48px;
    --vanna-space-16: 64px;

    /* Border radius */
    --vanna-border-radius-sm: 6px;
    --vanna-border-radius-md: 10px;
    --vanna-border-radius-lg: 14px;
    --vanna-border-radius-xl: 20px;
    --vanna-border-radius-2xl: 24px;
    --vanna-border-radius-full: 9999px;

    /* Shadows - Preline-inspired */
    --vanna-shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --vanna-shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
    --vanna-shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
    --vanna-shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
    --vanna-shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    --vanna-shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);

    /* Animation durations */
    --vanna-duration-75: 75ms;
    --vanna-duration-100: 100ms;
    --vanna-duration-150: 150ms;
    --vanna-duration-200: 200ms;
    --vanna-duration-300: 300ms;
    --vanna-duration-500: 500ms;
    --vanna-duration-700: 700ms;

    /* Z-index scale */
    --vanna-z-dropdown: 1000;
    --vanna-z-sticky: 1020;
    --vanna-z-fixed: 1030;
    --vanna-z-modal: 1040;
    --vanna-z-popover: 1050;
    --vanna-z-tooltip: 1060;

    /* Chat-specific tokens */
    --vanna-chat-bubble-radius: 18px;
    --vanna-chat-bubble-radius-sm: 12px;
    --vanna-chat-spacing: 16px;
    --vanna-chat-avatar-size: 40px;
  }

  /* Dark theme overrides */
  :host([theme="dark"]) {
    --vanna-background-root: rgb(9, 11, 17);
    --vanna-background-default: rgb(15, 18, 25);
    --vanna-background-higher: rgb(24, 29, 39);
    --vanna-background-highest: rgb(31, 39, 51);
    --vanna-background-subtle: rgb(17, 21, 28);
    --vanna-background-lower: rgb(6, 8, 12);

    --vanna-foreground-default: rgb(248, 250, 252);
    --vanna-foreground-dimmer: rgb(203, 213, 225);
    --vanna-foreground-dimmest: rgb(148, 163, 184);

    --vanna-accent-primary-default: #013DFF;
    --vanna-accent-primary-stronger: #013DFF;
    --vanna-accent-primary-strongest: rgb(2, 61, 96);
    --vanna-accent-primary-subtle: rgba(21, 168, 168, 0.15);
    --vanna-accent-primary-hover: #013DFF;

    --vanna-accent-positive-default: #013DFF;
    --vanna-accent-positive-stronger: #013DFF;
    --vanna-accent-positive-subtle: rgba(21, 168, 168, 0.15);

    --vanna-accent-negative-default: rgb(248, 113, 113);
    --vanna-accent-negative-stronger: rgb(239, 68, 68);
    --vanna-accent-negative-subtle: rgba(248, 113, 113, 0.15);

    --vanna-accent-warning-default: rgb(254, 93, 38);
    --vanna-accent-warning-stronger: rgb(254, 93, 38);
    --vanna-accent-warning-subtle: rgba(254, 93, 38, 0.15);

    --vanna-outline-default: rgba(21, 168, 168, 0.3);
    --vanna-outline-dimmer: rgb(31, 41, 55);
    --vanna-outline-dimmest: rgb(17, 24, 39);
    --vanna-outline-hover: #013DFF;

    --vanna-shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.6);
    --vanna-shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.5), 0 1px 2px -1px rgba(0, 0, 0, 0.5);
    --vanna-shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -2px rgba(0, 0, 0, 0.4);
    --vanna-shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -4px rgba(0, 0, 0, 0.4);
    --vanna-shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
    --vanna-shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
  }
`;
