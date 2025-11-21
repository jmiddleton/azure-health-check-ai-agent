param name string
param location string = resourceGroup().location
param tags object = {}
param containerRegistryName string
param containerAppsEnvironmentName string
param identityName string
param assistantBaseUrl string
param apiHealthcheckBaseUrl string

param env array = [
  {
    name: 'API_HEALTHCHECK_BASE_URL'
    value: apiHealthcheckBaseUrl
  }
  {
    name: 'NEXT_PUBLIC_ASSISTANT_BASE_URL'
    value: assistantBaseUrl
  }
]

resource frontendIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

module frontend 'core/host/container-app-upsert.bicep' = {
  name: 'container-app-module'
  params: {
    name: name
    location: location
    tags: union(tags, { 'azd-service-name': 'frontend' })
    identityName: frontendIdentity.name
    containerRegistryName: containerRegistryName
    containerAppsEnvironmentName: containerAppsEnvironmentName
    targetPort: 3000
    env: env
  }
}


output SERVICE_FRONTEND_IDENTITY_PRINCIPAL_ID string = frontendIdentity.properties.principalId
output SERVICE_FRONTEND_NAME string = frontend.outputs.name
output SERVICE_FRONTEND_URI string = frontend.outputs.uri
