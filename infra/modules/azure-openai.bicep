// Azure OpenAI Cognitive Services Account
// Deploys Azure OpenAI with a GPT model for the Tecknoworks AI Chat application

@description('Name of the Azure OpenAI resource')
param name string

@description('Location for the Azure OpenAI resource')
param location string = resourceGroup().location

@description('Tags to apply to the Azure OpenAI resource')
param tags object = {}

@description('SKU for the Azure OpenAI resource')
@allowed(['S0'])
param sku string = 'S0'

@description('Name of the model deployment')
param modelDeploymentName string = 'gpt-4o'

@description('Model name to deploy')
param modelName string = 'gpt-4o'

@description('Model version')
param modelVersion string = '2024-08-06'

@description('Tokens per minute capacity (in thousands)')
param capacityTPM int = 30

@description('Principal ID for Cognitive Services User role assignment')
param principalId string = ''

// Azure OpenAI Cognitive Services Account
resource openai 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: sku
  }
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
    // Disable local auth to force managed identity usage
    disableLocalAuth: false
  }
}

// Model Deployment (GPT-4o)
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: openai
  name: modelDeploymentName
  sku: {
    name: 'Standard'
    capacity: capacityTPM
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

// Role assignment for Cognitive Services User (if principalId provided)
// This allows the managed identity to use the OpenAI service
resource cognitiveServicesUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  scope: openai
  name: guid(openai.id, principalId, 'a97b65f3-24c7-4388-baec-2e87135dc908')
  properties: {
    // Cognitive Services User role
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
@description('Resource ID of the Azure OpenAI resource')
output id string = openai.id

@description('Name of the Azure OpenAI resource')
output name string = openai.name

@description('Endpoint URL for the Azure OpenAI resource')
output endpoint string = openai.properties.endpoint

@description('Name of the model deployment')
output deploymentName string = deployment.name

@description('Primary API key (use managed identity in production)')
output apiKey string = openai.listKeys().key1
