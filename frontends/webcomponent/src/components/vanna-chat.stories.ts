import type { Meta, StoryObj } from '@storybook/web-components';
import { html } from 'lit';
import './vanna-chat';
import './vanna-message';
import './plotly-chart';

const meta: Meta = {
  title: 'Components/VannaChat',
  component: 'vanna-chat',
  parameters: {
    layout: 'fullscreen',
    backgrounds: {
      default: 'light',
      values: [
        { name: 'light', value: '#f5f7fa' },
        { name: 'dark', value: 'rgb(11, 15, 25)' },
      ],
    },
  },
  argTypes: {
    title: { control: 'text' },
    placeholder: { control: 'text' },
    disabled: { control: 'boolean' },
    showProgress: { control: 'boolean' },
    maxAutonomy: { control: 'boolean' },
    theme: {
      control: 'select',
      options: ['dark', 'light'],
      description: 'Theme variant'
    },
  },
};

export default meta;
type Story = StoryObj;

export const Default: Story = {
  args: {
    title: 'thaink² AI Chat',
    placeholder: 'Describe what you want to build...',
    disabled: false,
    showProgress: true,
    maxAutonomy: false,
    theme: 'light',
  },
  render: (args) => html`
    <div style="height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; background: ${args.theme === 'light' ? '#f5f7fa' : 'rgb(11, 15, 25)'};">
      <vanna-chat
        .title=${args.title}
        .placeholder=${args.placeholder}
        .disabled=${args.disabled}
        .showProgress=${args.showProgress}
        .maxAutonomy=${args.maxAutonomy}
        theme=${args.theme}>
      </vanna-chat>
    </div>
  `,
};

export const LightMode: Story = {
  args: {
    title: 'thaink² AI Chat',
    placeholder: 'Describe what you want to build...',
    disabled: false,
    showProgress: true,
    maxAutonomy: false,
    theme: 'light',
  },
  render: (args) => html`
    <div style="height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; background: ${args.theme === 'light' ? '#f5f7fa' : 'rgb(11, 15, 25)'};">
      <vanna-chat
        .title=${args.title}
        .placeholder=${args.placeholder}
        .disabled=${args.disabled}
        .showProgress=${args.showProgress}
        .maxAutonomy=${args.maxAutonomy}
        theme=${args.theme}>
      </vanna-chat>
    </div>
  `,
};

export const WithConversation: Story = {
  args: {
    title: 'thaink² AI Chat',
    placeholder: 'Continue the conversation...',
    disabled: false,
    showProgress: true,
    maxAutonomy: true,
    theme: 'light',
  },
  render: (args) => {
    setTimeout(() => {
      const chat = document.querySelector('vanna-chat') as any;
      const tracker = chat?.getProgressTracker();

      if (chat && tracker) {
        // Add conversation messages
        chat.addMessage('Create a dashboard for analyzing customer data', 'user');
        chat.addMessage('I\'ll help you create a customer data dashboard. Let me break this down into steps and get started.', 'assistant');
        chat.addMessage('What specific metrics would you like to track? Revenue, acquisition, retention, or something else?', 'assistant');
        chat.addMessage('Focus on revenue and customer acquisition metrics', 'user');

        // Add progress items
        const id1 = tracker.addItem('Analyze requirements', 'Understanding dashboard needs');
        const id2 = tracker.addItem('Design data schema', 'Planning database structure');
        tracker.addItem('Create visualization components', 'Building charts and graphs');
        tracker.addItem('Implement filtering', 'Adding date range and segment filters');

        // Update progress states
        tracker.updateItem(id1, 'completed');
        tracker.updateItem(id2, 'in_progress', 'Identifying key metrics and data sources');

        // Set status
        chat.setStatus('working', 'Analyzing data requirements...', 'Step 2 of 4');
      }
    }, 100);

    return html`
      <div style="height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; background: ${args.theme === 'light' ? '#f5f7fa' : 'rgb(11, 15, 25)'};">
        <vanna-chat
          .title=${args.title}
          .placeholder=${args.placeholder}
          .disabled=${args.disabled}
          .showProgress=${args.showProgress}
          .maxAutonomy=${args.maxAutonomy}
          theme=${args.theme}>
        </vanna-chat>
      </div>
    `;
  },
};

export const MaxAutonomyMode: Story = {
  args: {
    title: 'thaink² AI Chat - Max Autonomy',
    placeholder: 'Describe your project...',
    disabled: false,
    showProgress: true,
    maxAutonomy: true,
    theme: 'light',
  },
  render: (args) => {
    setTimeout(() => {
      const chat = document.querySelector('vanna-chat') as any;
      const tracker = chat?.getProgressTracker();

      if (chat && tracker) {
        chat.addMessage('Build a full-stack e-commerce app with user authentication, product catalog, shopping cart, and payment processing', 'user');
        chat.addMessage('Perfect! I\'ll build a complete e-commerce application for you. Since Max Autonomy is enabled, I\'ll handle all the technical decisions and implementation details automatically.', 'assistant');

        // Comprehensive task list for full autonomy
        const tasks = [
          'Set up project structure',
          'Configure development environment',
          'Design database schema',
          'Implement user authentication',
          'Build product catalog API',
          'Create shopping cart functionality',
          'Integrate payment processing',
          'Develop frontend components',
          'Add responsive design',
          'Implement search & filtering',
          'Set up testing framework',
          'Configure deployment pipeline'
        ];

        tasks.forEach((task, index) => {
          const id = tracker.addItem(task, `Feature ${index + 1} of ${tasks.length}`);
          if (index < 3) tracker.updateItem(id, 'completed');
          else if (index === 3) tracker.updateItem(id, 'in_progress', 'Setting up JWT tokens and password hashing');
        });

        chat.setStatus('working', 'Building authentication system...', 'High autonomy mode active');
      }
    }, 100);

    return html`
      <div style="height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; background: ${args.theme === 'light' ? '#f5f7fa' : 'rgb(11, 15, 25)'};">
        <vanna-chat
          .title=${args.title}
          .placeholder=${args.placeholder}
          .disabled=${args.disabled}
          .showProgress=${args.showProgress}
          .maxAutonomy=${args.maxAutonomy}
          theme=${args.theme}>
        </vanna-chat>
      </div>
    `;
  },
};

export const WorkingState: Story = {
  args: {
    title: 'thaink² AI Chat',
    placeholder: 'Ask me anything...',
    disabled: true,
    showProgress: true,
    maxAutonomy: false,
    theme: 'light',
  },
  render: (args) => {
    setTimeout(() => {
      const chat = document.querySelector('vanna-chat') as any;
      const tracker = chat?.getProgressTracker();

      if (chat && tracker) {
        chat.addMessage('Generate a monthly sales report with charts', 'user');

        const id1 = tracker.addItem('Connect to database', 'Establishing secure connection');
        const id2 = tracker.addItem('Query sales data', 'Fetching monthly records');
        tracker.addItem('Process data', 'Calculating totals and trends');
        tracker.addItem('Generate charts', 'Creating visualizations');
        tracker.addItem('Format report', 'Compiling final document');

        tracker.updateItem(id1, 'completed');
        tracker.updateItem(id2, 'in_progress', 'SELECT * FROM sales WHERE date >= 2024-01...');

        chat.setStatus('working', 'Querying sales database...', 'Processing 12,543 records');
      }
    }, 100);

    return html`
      <div style="height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; background: ${args.theme === 'light' ? '#f5f7fa' : 'rgb(11, 15, 25)'};">
        <vanna-chat
          .title=${args.title}
          .placeholder=${args.placeholder}
          .disabled=${args.disabled}
          .showProgress=${args.showProgress}
          .maxAutonomy=${args.maxAutonomy}
          theme=${args.theme}>
        </vanna-chat>
      </div>
    `;
  },
};

export const CompactMode: Story = {
  args: {
    title: 'thaink² AI Chat',
    placeholder: 'Quick question...',
    disabled: false,
    showProgress: false,
    maxAutonomy: false,
    theme: 'light',
  },
  render: (args) => {
    setTimeout(() => {
      const chat = document.querySelector('vanna-chat') as any;
      if (chat) {
        chat.addMessage('What\'s the average order value this month?', 'user');
        chat.addMessage('Let me query that for you...', 'assistant');
        chat.setStatus('working', 'Calculating average order value...', '2.1s');
      }
    }, 100);

    return html`
      <div style="height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; background: ${args.theme === 'light' ? '#f5f7fa' : 'rgb(11, 15, 25)'};">
        <vanna-chat
          .title=${args.title}
          .placeholder=${args.placeholder}
          .disabled=${args.disabled}
          .showProgress=${args.showProgress}
          .maxAutonomy=${args.maxAutonomy}
          theme=${args.theme}>
        </vanna-chat>
      </div>
    `;
  },
};

export const WithRichComponents: Story = {
  args: {
    title: 'thaink² AI Chat - Rich Components',
    placeholder: 'Ask me to analyze data or build something...',
    disabled: false,
    showProgress: true,
    maxAutonomy: false,
    theme: 'light',
  },
  render: (args) => {
    setTimeout(() => {
      const chat = document.querySelector('vanna-chat') as any;
      const tracker = chat?.getProgressTracker();

      if (chat && tracker) {
        // Initial conversation
        chat.addMessage('Create a comprehensive sales dashboard with multiple visualizations and export capabilities', 'user');
        chat.addMessage('I\'ll create a comprehensive sales dashboard for you. Let me break this down into clear tasks and show you the progress with rich components.', 'assistant');

        // Add progress tasks
        const taskId1 = tracker.addItem('Analyze requirements', 'Understanding dashboard specifications');
        const taskId2 = tracker.addItem('Design data schema', 'Planning database structure');
        const taskId3 = tracker.addItem('Create visualizations', 'Building charts and graphs');
        const taskId4 = tracker.addItem('Add export features', 'Implementing PDF and Excel export');
        tracker.addItem('Deploy dashboard', 'Setting up production environment');

        tracker.updateItem(taskId1, 'completed');
        tracker.updateItem(taskId2, 'completed');
        tracker.updateItem(taskId3, 'in_progress', 'Creating revenue trend charts...');

        chat.setStatus('working', 'Building visualization components...', 'Step 3 of 5');

        // Add rich components after a delay
        setTimeout(() => {
          const componentManager = chat.componentManager;
          if (!componentManager) return;

          // Add info notification
          componentManager.processUpdate({
            operation: 'create',
            target_id: 'info-notification',
            component: {
              id: 'info-notification',
              type: 'notification',
              data: {
                title: 'Dashboard Progress',
                message: 'Your sales dashboard is being built with the following components: revenue trends, customer analytics, and performance metrics.',
                level: 'info',
                dismissible: true,
                actions: []
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

          // Add status indicator
          componentManager.processUpdate({
            operation: 'create',
            target_id: 'status-chart-generation',
            component: {
              id: 'status-chart-generation',
              type: 'status_indicator',
              data: {
                status: 'loading',
                message: 'Generating revenue trend charts...',
                pulse: true
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

          // Add progress bar for chart generation
          componentManager.processUpdate({
            operation: 'create',
            target_id: 'chart-progress',
            component: {
              id: 'chart-progress',
              type: 'progress_bar',
              data: {
                progress: 65,
                status: 'active',
                label: 'Chart Generation Progress',
                detail: 'Processing 12,543 sales records...',
                animated: true
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

          // Add task list card
          componentManager.processUpdate({
            operation: 'create',
            target_id: 'dashboard-tasks',
            component: {
              id: 'dashboard-tasks',
              type: 'task_list',
              data: {
                title: 'Dashboard Components',
                tasks: [
                  {
                    id: 'task-1',
                    title: 'Revenue Trend Chart',
                    description: 'Monthly revenue tracking with year-over-year comparison',
                    status: 'completed',
                    progress: 100,
                    timestamp: '2024-01-15 14:32:00'
                  },
                  {
                    id: 'task-2',
                    title: 'Customer Acquisition Funnel',
                    description: 'Lead to customer conversion visualization',
                    status: 'running',
                    progress: 75,
                    timestamp: '2024-01-15 14:45:00'
                  },
                  {
                    id: 'task-3',
                    title: 'Geographic Sales Map',
                    description: 'Interactive map showing sales by region',
                    status: 'pending',
                    progress: 0,
                    timestamp: null
                  },
                  {
                    id: 'task-4',
                    title: 'Performance Metrics KPIs',
                    description: 'Key performance indicators dashboard',
                    status: 'pending',
                    progress: 0,
                    timestamp: null
                  }
                ],
                progress: 58
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

          // Add data summary card
          componentManager.processUpdate({
            operation: 'create',
            target_id: 'data-summary',
            component: {
              id: 'data-summary',
              type: 'card',
              data: {
                title: 'Data Analysis Summary',
                subtitle: 'Sales Data Processing Results',
                content: 'Successfully processed 12,543 sales records from the last 12 months. Found key trends in customer behavior and revenue patterns.',
                icon: '📊',
                status: 'success',
                collapsible: true,
                actions: [
                  { label: 'View Details', action: 'view-details', variant: 'primary' },
                  { label: 'Export Data', action: 'export', variant: 'secondary' }
                ]
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

          // Add markdown text with insights
          componentManager.processUpdate({
            operation: 'create',
            target_id: 'insights-text',
            component: {
              id: 'insights-text',
              type: 'text',
              data: {
                content: `# Dashboard Insights\n\nBased on the data analysis, here are the key findings:\n\n## Revenue Trends\n- **23% increase** in Q4 sales compared to Q3\n- Peak sales month: **December** ($1.2M)\n- Lowest performing month: **February** ($680K)\n\n## Customer Behavior\n- Average order value: **$156.78**\n- Customer retention rate: **89.3%**\n- Most popular product category: **Electronics**\n\n## Recommendations\n1. **Focus marketing efforts** on February to boost sales\n2. **Expand electronics inventory** for peak seasons\n3. **Implement loyalty program** to maintain high retention\n\n*Dashboard generation is 65% complete. Estimated completion: 3-4 minutes.*`,
                markdown: true
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

        }, 1500);

        // Update components after more time
        setTimeout(() => {
          const componentManager = chat.componentManager;
          if (!componentManager) return;

          // Update status indicator to success
          componentManager.processUpdate({
            operation: 'update',
            target_id: 'status-chart-generation',
            updates: {
              status: 'success',
              message: 'Revenue charts generated successfully',
              pulse: false
            },
            timestamp: new Date().toISOString()
          });

          // Update progress bar
          componentManager.processUpdate({
            operation: 'update',
            target_id: 'chart-progress',
            updates: {
              progress: 100,
              status: 'success',
              detail: 'All charts generated successfully!',
              animated: false
            },
            timestamp: new Date().toISOString()
          });

          // Add success notification
          componentManager.processUpdate({
            operation: 'create',
            target_id: 'success-notification',
            component: {
              id: 'success-notification',
              type: 'notification',
              data: {
                title: 'Charts Ready!',
                message: 'Your revenue trend charts have been generated and are ready for review.',
                level: 'success',
                dismissible: true,
                actions: [
                  { label: 'View Charts', action: 'view-charts', variant: 'primary' },
                  { label: 'Continue', action: 'continue', variant: 'secondary' }
                ]
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

          // Update progress tracker
          tracker.updateItem(taskId3, 'completed');
          tracker.updateItem(taskId4, 'in_progress', 'Adding PDF export functionality...');
          chat.setStatus('working', 'Adding export capabilities...', 'Step 4 of 5');

        }, 4000);
      }
    }, 100);

    return html`
      <div style="height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; background: ${args.theme === 'light' ? '#f5f7fa' : 'rgb(11, 15, 25)'};">
        <vanna-chat
          .title=${args.title}
          .placeholder=${args.placeholder}
          .disabled=${args.disabled}
          .showProgress=${args.showProgress}
          .maxAutonomy=${args.maxAutonomy}
          theme=${args.theme}>
        </vanna-chat>
      </div>
    `;
  },
};

export const WithToolExecutionComponents: Story = {
  args: {
    title: 'thaink² AI Chat - Tool Execution',
    placeholder: 'Ask me to run commands or execute tools...',
    disabled: false,
    showProgress: true,
    maxAutonomy: true,
    theme: 'light',
  },
  render: (args) => {
    setTimeout(() => {
      const chat = document.querySelector('vanna-chat') as any;
      const tracker = chat?.getProgressTracker();

      if (chat && tracker) {
        // Initial conversation about running tools
        chat.addMessage('Run a data analysis script and deploy the results to production', 'user');
        chat.addMessage('I\'ll execute the data analysis script and handle the deployment. Let me run the necessary tools and show you the execution details.', 'assistant');

        // Add progress tasks
        const taskId1 = tracker.addItem('Run data analysis script', 'Executing Python analysis tools');
        const taskId2 = tracker.addItem('Process results', 'Formatting and validating output');
        const taskId3 = tracker.addItem('Deploy to production', 'Uploading to production server');

        tracker.updateItem(taskId1, 'in_progress', 'Running analysis.py...');

        chat.setStatus('working', 'Executing data analysis tools...', 'Max autonomy enabled');

        // Add tool execution components after a delay
        setTimeout(() => {
          const componentManager = chat.componentManager;
          if (!componentManager) return;

          // Add tool execution component for data analysis
          componentManager.processUpdate({
            operation: 'create',
            target_id: 'tool-analysis',
            component: {
              id: 'tool-analysis',
              type: 'tool_execution',
              data: {
                tool_name: 'Python Script Executor',
                status: 'running',
                progress: 45,
                duration: '2.3s',
                arguments: {
                  script: 'analysis.py',
                  dataset: 'sales_data_2024.csv',
                  output_format: 'json',
                  verbose: true
                },
                result: null,
                error: null,
                logs: [
                  { timestamp: '14:32:01', level: 'INFO', message: 'Loading dataset: sales_data_2024.csv' },
                  { timestamp: '14:32:02', level: 'INFO', message: 'Found 12,543 records' },
                  { timestamp: '14:32:03', level: 'INFO', message: 'Running correlation analysis...' },
                  { timestamp: '14:32:04', level: 'INFO', message: 'Processing revenue trends...' }
                ]
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

          // Add warning notification about data processing
          componentManager.processUpdate({
            operation: 'create',
            target_id: 'warning-notification',
            component: {
              id: 'warning-notification',
              type: 'notification',
              data: {
                title: 'Large Dataset Detected',
                message: 'Processing 12,543 records. This may take a few minutes to complete.',
                level: 'warning',
                dismissible: true,
                actions: [
                  { label: 'Monitor Progress', action: 'monitor', variant: 'primary' }
                ]
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

        }, 1500);

        // Complete first tool and start second
        setTimeout(() => {
          const componentManager = chat.componentManager;
          if (!componentManager) return;

          // Update first tool to completed
          componentManager.processUpdate({
            operation: 'update',
            target_id: 'tool-analysis',
            updates: {
              status: 'completed',
              progress: 100,
              duration: '4.7s',
              result: JSON.stringify({
                total_revenue: 1847259.32,
                avg_order_value: 156.78,
                top_product: 'Electronics',
                growth_rate: 0.23,
                recommendations: ['Expand Q4 marketing', 'Focus on electronics inventory']
              }, null, 2),
              logs: [
                { timestamp: '14:32:01', level: 'INFO', message: 'Loading dataset: sales_data_2024.csv' },
                { timestamp: '14:32:02', level: 'INFO', message: 'Found 12,543 records' },
                { timestamp: '14:32:03', level: 'INFO', message: 'Running correlation analysis...' },
                { timestamp: '14:32:04', level: 'INFO', message: 'Processing revenue trends...' },
                { timestamp: '14:32:06', level: 'INFO', message: 'Analysis complete! Generated insights.' },
                { timestamp: '14:32:06', level: 'INFO', message: 'Output saved to results.json' }
              ]
            },
            timestamp: new Date().toISOString()
          });

          // Update progress tracker
          tracker.updateItem(taskId1, 'completed');
          tracker.updateItem(taskId2, 'in_progress', 'Validating analysis results...');

          // Add second tool execution for deployment
          componentManager.processUpdate({
            operation: 'create',
            target_id: 'tool-deploy',
            component: {
              id: 'tool-deploy',
              type: 'tool_execution',
              data: {
                tool_name: 'Production Deployer',
                status: 'running',
                progress: 20,
                duration: '1.2s',
                arguments: {
                  source: 'results.json',
                  target: 'prod-server-01',
                  backup: true,
                  validate: true
                },
                result: null,
                error: null,
                logs: [
                  { timestamp: '14:32:08', level: 'INFO', message: 'Connecting to prod-server-01...' },
                  { timestamp: '14:32:09', level: 'INFO', message: 'Creating backup of existing data...' }
                ]
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

        }, 4000);

        // Complete deployment
        setTimeout(() => {
          const componentManager = chat.componentManager;
          if (!componentManager) return;

          // Complete second tool
          componentManager.processUpdate({
            operation: 'update',
            target_id: 'tool-deploy',
            updates: {
              status: 'completed',
              progress: 100,
              duration: '6.1s',
              result: 'Deployment successful! Results available at: https://dashboard.company.com/sales-analysis',
              logs: [
                { timestamp: '14:32:08', level: 'INFO', message: 'Connecting to prod-server-01...' },
                { timestamp: '14:32:09', level: 'INFO', message: 'Creating backup of existing data...' },
                { timestamp: '14:32:11', level: 'INFO', message: 'Uploading results.json...' },
                { timestamp: '14:32:13', level: 'INFO', message: 'Validating deployment...' },
                { timestamp: '14:32:14', level: 'INFO', message: 'Deployment successful!' }
              ]
            },
            timestamp: new Date().toISOString()
          });

          // Update progress tracker
          tracker.updateItem(taskId2, 'completed');
          tracker.updateItem(taskId3, 'completed');

          // Add success notification
          componentManager.processUpdate({
            operation: 'create',
            target_id: 'deploy-success',
            component: {
              id: 'deploy-success',
              type: 'notification',
              data: {
                title: 'Deployment Complete!',
                message: 'Data analysis results have been successfully deployed to production. Dashboard is now live.',
                level: 'success',
                dismissible: true,
                actions: [
                  { label: 'View Dashboard', action: 'view-dashboard', variant: 'primary' },
                  { label: 'Download Report', action: 'download', variant: 'secondary' }
                ]
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

          // Add final status indicator
          componentManager.processUpdate({
            operation: 'create',
            target_id: 'final-status',
            component: {
              id: 'final-status',
              type: 'status_indicator',
              data: {
                status: 'success',
                message: 'All tools executed successfully',
                pulse: false
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

          // Update chat status
          chat.setStatus('idle', 'All tasks completed successfully', 'Ready for next request');

        }, 7000);
      }
    }, 100);

    return html`
      <div style="height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; background: ${args.theme === 'light' ? '#f5f7fa' : 'rgb(11, 15, 25)'};">
        <vanna-chat
          .title=${args.title}
          .placeholder=${args.placeholder}
          .disabled=${args.disabled}
          .showProgress=${args.showProgress}
          .maxAutonomy=${args.maxAutonomy}
          theme=${args.theme}>
        </vanna-chat>
      </div>
    `;
  },
};

export const WithChart: Story = {
  args: {
    title: 'thaink² AI Chat - Chart Display',
    placeholder: 'Ask me to analyze data...',
    disabled: false,
    showProgress: true,
    maxAutonomy: false,
    theme: 'light',
  },
  render: (args) => {
    setTimeout(() => {
      const chat = document.querySelector('vanna-chat') as any;
      const tracker = chat?.getProgressTracker();

      if (chat && tracker) {
        // Initial conversation
        chat.addMessage('Show me the top 10 artists by sales', 'user');
        chat.addMessage('I\'ll analyze the sales data and create a visualization for you.', 'assistant');

        // Add progress tasks
        const taskId1 = tracker.addItem('Query sales database', 'Fetching artist sales data');
        const taskId2 = tracker.addItem('Process results', 'Calculating total sales per artist');
        const taskId3 = tracker.addItem('Create visualization', 'Generating bar chart');

        tracker.updateItem(taskId1, 'completed');
        tracker.updateItem(taskId2, 'completed');
        tracker.updateItem(taskId3, 'in_progress', 'Rendering Plotly chart...');

        chat.setStatus('working', 'Creating visualization...', 'Step 3 of 3');

        // Add chart component after a delay
        setTimeout(() => {
          const componentManager = chat.componentManager;
          if (!componentManager) return;

          // Add the chart component with the data you provided
          componentManager.processUpdate({
            operation: 'create',
            target_id: '8e275121-e3f4-4b99-87f2-fabc3ef66216',
            component: {
              id: '8e275121-e3f4-4b99-87f2-fabc3ef66216',
              type: 'chart',
              data: {
                data: [
                  {
                    hovertemplate: 'artist=%{x}<br>total_sales=%{y}<extra></extra>',
                    legendgroup: '',
                    marker: {
                      color: '#636efa',
                      pattern: {
                        shape: ''
                      }
                    },
                    name: '',
                    orientation: 'v',
                    showlegend: false,
                    textposition: 'auto',
                    x: [
                      'Deep Purple',
                      'Eric Clapton',
                      'Faith No More',
                      'Iron Maiden',
                      'Led Zeppelin',
                      'Lost',
                      'Metallica',
                      'Os Paralamas Do Sucesso',
                      'The Office',
                      'U2'
                    ],
                    xaxis: 'x',
                    y: [22.5, 19.8, 27.72, 138.6, 86.13, 81.59, 90.09, 41.49, 30, 105.93],
                    yaxis: 'y',
                    type: 'bar'
                  }
                ],
                layout: {
                  template: {
                    data: {
                      bar: [
                        {
                          error_x: {
                            color: '#2a3f5f'
                          },
                          error_y: {
                            color: '#2a3f5f'
                          },
                          marker: {
                            line: {
                              color: '#E5ECF6',
                              width: 0.5
                            },
                            pattern: {
                              fillmode: 'overlay',
                              size: 10,
                              solidity: 0.2
                            }
                          },
                          type: 'bar'
                        }
                      ]
                    },
                    layout: {
                      font: {
                        color: '#2a3f5f'
                      },
                      xaxis: {
                        gridcolor: 'white',
                        linecolor: 'white',
                        ticks: '',
                        title: {
                          standoff: 15
                        },
                        zerolinecolor: 'white',
                        automargin: true,
                        zerolinewidth: 2
                      },
                      yaxis: {
                        gridcolor: 'white',
                        linecolor: 'white',
                        ticks: '',
                        title: {
                          standoff: 15
                        },
                        zerolinecolor: 'white',
                        automargin: true,
                        zerolinewidth: 2
                      }
                    }
                  },
                  xaxis: {
                    anchor: 'y',
                    domain: [0.0, 1.0],
                    title: {
                      text: 'artist'
                    }
                  },
                  yaxis: {
                    anchor: 'x',
                    domain: [0.0, 1.0],
                    title: {
                      text: 'total_sales'
                    }
                  },
                  legend: {
                    tracegroupgap: 0
                  },
                  title: {
                    text: 'Top 10 Artists by Sales'
                  },
                  barmode: 'relative',
                  font: {
                    color: '#1f2937'
                  },
                  paper_bgcolor: 'white',
                  plot_bgcolor: 'white',
                  autosize: true
                },
                chart_type: 'plotly',
                title: 'Top 10 Artists by Sales',
                width: null,
                height: null,
                config: {
                  data_shape: {
                    rows: 10,
                    columns: 2
                  },
                  source_file: 'query_results_f42c1599.csv'
                }
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

          // Update progress tracker
          tracker.updateItem(taskId3, 'completed');
          chat.setStatus('idle', 'Visualization complete', 'Ready for next query');

          // Add text summary
          componentManager.processUpdate({
            operation: 'create',
            target_id: 'chart-summary',
            component: {
              id: 'chart-summary',
              type: 'text',
              data: {
                content: `Created visualization from 'query_results_f42c1599.csv' (10 rows, 2 columns).

**Top Artists:**
- Faith No More leads with 138.6 in total sales
- U2 follows with 105.93
- Metallica with 90.09

The chart shows the distribution of sales across the top 10 artists.`,
                markdown: true
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });

        }, 1500);
      }
    }, 100);

    return html`
      <div style="height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; background: ${args.theme === 'light' ? '#f5f7fa' : 'rgb(11, 15, 25)'};">
        <vanna-chat
          .title=${args.title}
          .placeholder=${args.placeholder}
          .disabled=${args.disabled}
          .showProgress=${args.showProgress}
          .maxAutonomy=${args.maxAutonomy}
          theme=${args.theme}>
        </vanna-chat>
      </div>
    `;
  },
};

export const WithButtons: Story = {
  args: {
    title: 'thaink² AI Chat - Button Components',
    placeholder: 'Click buttons to send messages...',
    disabled: false,
    showProgress: false,
    maxAutonomy: false,
    theme: 'dark',
  },
  render: (args) => {
    setTimeout(() => {
      const chat = document.querySelector('vanna-chat') as any;

      if (chat) {
        // Initial conversation
        chat.addMessage('Show me some button options', 'user');
        chat.addMessage('Here are some interactive buttons. Click any button to send a message with its label wrapped in square brackets.', 'assistant');

        const componentManager = chat.componentManager;
        if (!componentManager) return;

        // Add a single button example
        componentManager.processUpdate({
          operation: 'create',
          target_id: 'single-button-1',
          component: {
            id: 'single-button-1',
            type: 'button',
            data: {
              label: 'Okay',
              action: 'okay',
              variant: 'primary',
              size: 'medium',
            },
            layout: { position: 'append', size: {}, z_index: 0, classes: [] },
            theme: {},
            lifecycle: 'create'
          },
          timestamp: new Date().toISOString()
        });

        // Add button group with choices
        componentManager.processUpdate({
          operation: 'create',
          target_id: 'choice-group',
          component: {
            id: 'choice-group',
            type: 'button_group',
            data: {
              buttons: [
                {
                  label: 'Yes',
                  action: 'yes',
                  variant: 'success',
                  icon: '✓',
                },
                {
                  label: 'No',
                  action: 'no',
                  variant: 'error',
                  icon: '✗',
                },
                {
                  label: 'Maybe',
                  action: 'maybe',
                  variant: 'secondary',
                },
              ],
              orientation: 'horizontal',
              spacing: 'medium',
              align: 'left',
            },
            layout: { position: 'append', size: {}, z_index: 0, classes: [] },
            theme: {},
            lifecycle: 'create'
          },
          timestamp: new Date().toISOString()
        });

        // Add more single buttons with different variants
        const singleButtons = [
          { label: 'Continue', variant: 'primary', icon: '→', icon_position: 'right' },
          { label: 'Save Draft', variant: 'secondary', icon: '💾', icon_position: 'left' },
          { label: 'Delete', variant: 'error', icon: '🗑️' },
          { label: 'Cancel', variant: 'ghost' },
        ];

        singleButtons.forEach((btnData, index) => {
          componentManager.processUpdate({
            operation: 'create',
            target_id: `single-button-${index + 2}`,
            component: {
              id: `single-button-${index + 2}`,
              type: 'button',
              data: {
                ...btnData,
                action: btnData.label.toLowerCase().replace(' ', '_'),
                size: 'medium',
              },
              layout: { position: 'append', size: {}, z_index: 0, classes: [] },
              theme: {},
              lifecycle: 'create'
            },
            timestamp: new Date().toISOString()
          });
        });

        // Add a vertical button group
        componentManager.processUpdate({
          operation: 'create',
          target_id: 'option-group',
          component: {
            id: 'option-group',
            type: 'button_group',
            data: {
              buttons: [
                { label: 'Option A', action: 'option_a', variant: 'secondary' },
                { label: 'Option B', action: 'option_b', variant: 'secondary' },
                { label: 'Option C', action: 'option_c', variant: 'secondary' },
              ],
              orientation: 'vertical',
              spacing: 'small',
              align: 'left',
            },
            layout: { position: 'append', size: {}, z_index: 0, classes: [] },
            theme: {},
            lifecycle: 'create'
          },
          timestamp: new Date().toISOString()
        });

        // Listen for message-sent events to show feedback
        chat.addEventListener('message-sent', (e: CustomEvent) => {
          console.log('Message sent from button:', e.detail.message);
        });
      }
    }, 100);

    return html`
      <div style="height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; background: ${args.theme === 'light' ? '#f5f7fa' : 'rgb(11, 15, 25)'};">
        <vanna-chat
          .title=${args.title}
          .placeholder=${args.placeholder}
          .disabled=${args.disabled}
          .showProgress=${args.showProgress}
          .maxAutonomy=${args.maxAutonomy}
          theme=${args.theme}>
        </vanna-chat>
      </div>
    `;
  },
};