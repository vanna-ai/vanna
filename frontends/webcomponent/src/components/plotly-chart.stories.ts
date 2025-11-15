import type { Meta, StoryObj } from '@storybook/web-components';
import { html } from 'lit';
import './plotly-chart';

const meta: Meta = {
  title: 'Rich Components/Plotly Chart',
  component: 'plotly-chart',
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
    theme: {
      control: 'select',
      options: ['light', 'dark']
    },
    loading: { control: 'boolean' },
    error: { control: 'text' },
  },
};

export default meta;
type Story = StoryObj;

export const LineChart: Story = {
  args: {
    theme: 'light',
    loading: false,
    error: '',
  },
  render: (args) => html`
    <div style="max-width: 800px; margin: 0 auto;">
      <plotly-chart
        theme=${args.theme}
        ?loading=${args.loading}
        error=${args.error}
        .data=${[
          {
            x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            y: [20, 14, 23, 25, 22, 16],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Sales',
            line: { color: 'rgb(0, 123, 255)' }
          }
        ]}
        .layout=${{
          xaxis: { title: 'Month' },
          yaxis: { title: 'Sales (in thousands)' }
        }}>
      </plotly-chart>
    </div>
  `,
};

export const BarChart: Story = {
  args: {
    theme: 'light',
  },
  render: (args) => html`
    <div style="max-width: 800px; margin: 0 auto;">
      <plotly-chart
        theme=${args.theme}
        .data=${[
          {
            x: ['Product A', 'Product B', 'Product C', 'Product D'],
            y: [45, 32, 28, 35],
            type: 'bar',
            name: 'Revenue',
            marker: {
              color: ['rgb(16, 185, 129)', 'rgb(0, 123, 255)', 'rgb(245, 158, 11)', 'rgb(239, 68, 68)']
            }
          }
        ]}
        .layout=${{
          xaxis: { title: 'Products' },
          yaxis: { title: 'Revenue ($M)' }
        }}>
      </plotly-chart>
    </div>
  `,
};

export const ScatterPlot: Story = {
  args: {
    theme: 'light',
  },
  render: (args) => html`
    <div style="max-width: 800px; margin: 0 auto;">
      <plotly-chart
        theme=${args.theme}
        .data=${[
          {
            x: [85, 78, 92, 88, 76, 95, 82, 89, 93, 79],
            y: [450, 320, 580, 490, 280, 650, 380, 520, 610, 310],
            type: 'scatter',
            mode: 'markers',
            name: 'Business Units',
            marker: {
              size: 12,
              color: 'rgb(0, 123, 255)',
              opacity: 0.7
            }
          }
        ]}
        .layout=${{
          xaxis: { title: 'Customer Satisfaction Score' },
          yaxis: { title: 'Revenue ($K)' }
        }}>
      </plotly-chart>
    </div>
  `,
};

export const MultipleLines: Story = {
  args: {
    theme: 'light',
  },
  render: (args) => html`
    <div style="max-width: 800px; margin: 0 auto;">
      <plotly-chart
        theme=${args.theme}
        .data=${[
          {
            x: ['Q1', 'Q2', 'Q3', 'Q4'],
            y: [85, 88, 92, 89],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'User Engagement',
            line: { color: 'rgb(16, 185, 129)' }
          },
          {
            x: ['Q1', 'Q2', 'Q3', 'Q4'],
            y: [65, 72, 78, 81],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Conversion Rate',
            line: { color: 'rgb(0, 123, 255)' }
          },
          {
            x: ['Q1', 'Q2', 'Q3', 'Q4'],
            y: [42, 48, 55, 58],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Customer Retention',
            line: { color: 'rgb(245, 158, 11)' }
          }
        ]}
        .layout=${{
          xaxis: { title: 'Quarter' },
          yaxis: { title: 'Percentage (%)' }
        }}>
      </plotly-chart>
    </div>
  `,
};

export const LoadingState: Story = {
  args: {
    theme: 'light',
    loading: true,
  },
  render: (args) => html`
    <div style="max-width: 800px; margin: 0 auto;">
      <plotly-chart
        theme=${args.theme}
        ?loading=${args.loading}
        .data=${[]}>
      </plotly-chart>
    </div>
  `,
};

export const ErrorState: Story = {
  args: {
    theme: 'light',
    error: 'Failed to load chart data from API',
  },
  render: (args) => html`
    <div style="max-width: 800px; margin: 0 auto;">
      <plotly-chart
        theme=${args.theme}
        error=${args.error}
        .data=${[]}>
      </plotly-chart>
    </div>
  `,
};

export const LightTheme: Story = {
  args: {
    theme: 'light',
  },
  parameters: {
    backgrounds: { default: 'light' }
  },
  render: (args) => html`
    <div style="max-width: 800px; margin: 0 auto;">
      <plotly-chart
        theme=${args.theme}
        .data=${[
          {
            x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            y: [20, 14, 23, 25, 22, 16],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Sales',
            line: { color: 'rgb(0, 123, 255)' }
          }
        ]}
        .layout=${{
          xaxis: { title: 'Month' },
          yaxis: { title: 'Sales (in thousands)' }
        }}>
      </plotly-chart>
    </div>
  `,
};

export const CustomLayout: Story = {
  args: {
    theme: 'light',
  },
  render: (args) => html`
    <div style="max-width: 800px; margin: 0 auto;">
      <plotly-chart
        theme=${args.theme}
        .data=${[
          {
            x: [1, 2, 3, 4, 5],
            y: [10, 11, 12, 13, 14],
            type: 'scatter',
            mode: 'lines',
            name: 'Trend A',
            line: { color: 'rgb(16, 185, 129)', width: 3 }
          },
          {
            x: [1, 2, 3, 4, 5],
            y: [8, 9, 10, 11, 12],
            type: 'scatter',
            mode: 'lines',
            name: 'Trend B',
            line: { color: 'rgb(239, 68, 68)', width: 3, dash: 'dash' }
          }
        ]}
        .layout=${{
          title: {
            text: 'Custom Styled Chart',
            font: { size: 18 }
          },
          xaxis: {
            title: 'Time Period',
            gridcolor: 'rgba(255, 255, 255, 0.1)'
          },
          yaxis: {
            title: 'Value',
            gridcolor: 'rgba(255, 255, 255, 0.1)'
          },
          height: 500,
          showlegend: true
        }}>
      </plotly-chart>
    </div>
  `,
};

