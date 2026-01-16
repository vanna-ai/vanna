// Tecknoworks AI Agent - Azure Infrastructure
// Deploys Container App with Azure AI Foundry or Azure OpenAI integration

targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment (e.g., dev, staging, prod)')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Deploy Azure OpenAI resource (set to false to use existing endpoint)')
param deployAzureOpenAI bool = true

@description('Azure OpenAI endpoint URL (used when deployAzureOpenAI is false)')
@secure()
param azureOpenAIEndpoint string = ''

@description('Azure OpenAI API key (used when deployAzureOpenAI is false)')
@secure()
param azureOpenAIApiKey string = ''

@description('Azure OpenAI model deployment name')
param azureOpenAIModel string = 'gpt-4o'

@description('Azure OpenAI capacity in TPM (tokens per minute) in thousands')
param azureOpenAICapacityTPM int = 30

// Azure AI Foundry parameters (takes priority over Azure OpenAI)
@description('Azure AI Foundry endpoint URL (takes priority over Azure OpenAI when set)')
@secure()
param azureAIFoundryEndpoint string = ''

@description('Azure AI Foundry API key')
@secure()
param azureAIFoundryApiKey string = ''

@description('Azure AI Foundry model name (optional, uses default if not specified)')
param azureAIFoundryModel string = ''

// Generate unique suffix for resources
var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = {
  'azd-env-name': environmentName
  'application': 'tecknoworks-ai-agent'
}

// Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

// Log Analytics Workspace
module logAnalytics './modules/log-analytics.bicep' = {
  name: 'log-analytics'
  scope: rg
  params: {
    name: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    location: location
    tags: tags
  }
}

// User-Assigned Managed Identity
module managedIdentity './modules/managed-identity.bicep' = {
  name: 'managed-identity'
  scope: rg
  params: {
    name: '${abbrs.managedIdentityUserAssignedIdentities}${resourceToken}'
    location: location
    tags: tags
  }
}

// Azure OpenAI (conditionally deployed)
module azureOpenAI './modules/azure-openai.bicep' = if (deployAzureOpenAI) {
  name: 'azure-openai'
  scope: rg
  params: {
    name: '${abbrs.cognitiveServicesAccounts}${resourceToken}'
    location: location
    tags: tags
    modelDeploymentName: azureOpenAIModel
    modelName: 'gpt-4o'
    capacityTPM: azureOpenAICapacityTPM
    principalId: managedIdentity.outputs.principalId
  }
}

// Key Vault for secrets
module keyVault './modules/key-vault.bicep' = {
  name: 'key-vault'
  scope: rg
  params: {
    name: '${abbrs.keyVaultVaults}${resourceToken}'
    location: location
    tags: tags
    principalId: managedIdentity.outputs.principalId
  }
}

// Application Insights for APM
module appInsights './modules/application-insights.bicep' = {
  name: 'app-insights'
  scope: rg
  params: {
    name: '${abbrs.insightsComponents}${resourceToken}'
    location: location
    tags: tags
    logAnalyticsWorkspaceId: logAnalytics.outputs.id
  }
}

// Container Registry
module containerRegistry './modules/container-registry.bicep' = {
  name: 'container-registry'
  scope: rg
  params: {
    name: '${abbrs.containerRegistryRegistries}${resourceToken}'
    location: location
    tags: tags
  }
}

// Container Apps Environment
module containerAppsEnvironment './modules/container-apps-environment.bicep' = {
  name: 'container-apps-environment'
  scope: rg
  params: {
    name: '${abbrs.appManagedEnvironments}${resourceToken}'
    location: location
    tags: tags
    logAnalyticsWorkspaceName: logAnalytics.outputs.name
  }
}

// Container App
module containerApp './modules/container-app.bicep' = {
  name: 'container-app'
  scope: rg
  params: {
    name: '${abbrs.appContainerApps}api-${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'api' })
    containerAppsEnvironmentName: containerAppsEnvironment.outputs.name
    containerRegistryName: containerRegistry.outputs.name
    // Azure AI Foundry (takes priority when set)
    azureAIFoundryEndpoint: azureAIFoundryEndpoint
    azureAIFoundryApiKey: azureAIFoundryApiKey
    azureAIFoundryModel: azureAIFoundryModel
    // Use deployed Azure OpenAI if available, otherwise use provided endpoint (fallback)
    azureOpenAIEndpoint: deployAzureOpenAI ? azureOpenAI.outputs.endpoint : azureOpenAIEndpoint
    azureOpenAIApiKey: deployAzureOpenAI ? azureOpenAI.outputs.apiKey : azureOpenAIApiKey
    azureOpenAIModel: deployAzureOpenAI ? azureOpenAI.outputs.deploymentName : azureOpenAIModel
    // Application Insights for monitoring
    appInsightsConnectionString: appInsights.outputs.connectionString
  }
}

// Outputs
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = containerRegistry.outputs.name
output SERVICE_API_ENDPOINT_URL string = containerApp.outputs.uri
output SERVICE_API_NAME string = containerApp.outputs.name

// Azure AI Foundry outputs (when configured)
output AZURE_AI_FOUNDRY_ENDPOINT string = azureAIFoundryEndpoint
output AZURE_AI_FOUNDRY_MODEL string = azureAIFoundryModel

// Azure OpenAI outputs (when deployed, fallback)
output AZURE_OPENAI_ENDPOINT string = deployAzureOpenAI ? azureOpenAI.outputs.endpoint : azureOpenAIEndpoint
output AZURE_OPENAI_MODEL string = deployAzureOpenAI ? azureOpenAI.outputs.deploymentName : azureOpenAIModel

// Monitoring outputs
output APPLICATIONINSIGHTS_CONNECTION_STRING string = appInsights.outputs.connectionString

// Key Vault outputs
output AZURE_KEY_VAULT_NAME string = keyVault.outputs.name
output AZURE_KEY_VAULT_URI string = keyVault.outputs.uri
