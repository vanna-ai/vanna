// Application Insights for APM (Application Performance Monitoring)
// Provides telemetry, logging, and diagnostics for the application

@description('Name of the Application Insights resource')
param name string

@description('Location for the Application Insights resource')
param location string = resourceGroup().location

@description('Tags to apply to the Application Insights resource')
param tags object = {}

@description('Resource ID of the Log Analytics Workspace')
param logAnalyticsWorkspaceId string

// Application Insights resource
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspaceId
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    // Disable IP masking for better debugging (optional)
    DisableIpMasking: false
    // Sampling percentage (100 = no sampling)
    SamplingPercentage: 100
  }
}

// Outputs
@description('Resource ID of the Application Insights resource')
output id string = appInsights.id

@description('Name of the Application Insights resource')
output name string = appInsights.name

@description('Connection string for Application Insights')
output connectionString string = appInsights.properties.ConnectionString

@description('Instrumentation key for Application Insights')
output instrumentationKey string = appInsights.properties.InstrumentationKey
