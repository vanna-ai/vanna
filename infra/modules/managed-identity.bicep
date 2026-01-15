// User-Assigned Managed Identity for Container App
// Provides secure authentication to Azure services without credentials

@description('Name of the managed identity')
param name string

@description('Location for the managed identity')
param location string = resourceGroup().location

@description('Tags to apply to the managed identity')
param tags object = {}

// Create user-assigned managed identity
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: name
  location: location
  tags: tags
}

// Outputs
@description('Resource ID of the managed identity')
output id string = managedIdentity.id

@description('Principal ID (Object ID) of the managed identity')
output principalId string = managedIdentity.properties.principalId

@description('Client ID of the managed identity')
output clientId string = managedIdentity.properties.clientId

@description('Name of the managed identity')
output name string = managedIdentity.name
