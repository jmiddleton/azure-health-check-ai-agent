param name string
param location string = resourceGroup().location
param tags object = {}

param containerRegistryName string
param identityName string
param containerAppsEnvironmentName string
param azureExistingAIProjectResourceId string
param agentDeploymentName string
param searchConnectionName string
param embeddingDeploymentName string
param aiSearchIndexName string
param embeddingDeploymentDimensions string
param searchServiceEndpoint string
param agentName string
param agentID string
param enableAzureMonitorTracing bool
param azureTracingGenAIContentRecordingEnabled bool
param projectEndpoint string
param aiServicesName string
param jiraServerUrl string
param jiraApiUser string
param jiraProjectKey string
param jiraApiToken string

resource apiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
}

resource cognitiveAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: aiServicesName
}

var env = [
  {
    name: 'OPENAI_API_KEY'
    value: 'azureopenai'
  }
  {
    name: 'OPENAI_CHAT_MODEL_ID'
    value: agentDeploymentName
  }
  {
    name: 'OPENAI_RESPONSES_MODEL_ID'
    value: agentDeploymentName
  }
  {
    name: 'AZURE_PROJECT_ENDPOINT'
    value: projectEndpoint
  }
  {
    name: 'AZURE_OPENAI_ENDPOINT'
    value: 'https://${aiServicesName}.openai.azure.com/'
  }
  {
    name: 'AZURE_OPENAI_API_VERSION'
    value: '2024-12-01-preview'
  }
  {
    name: 'AZURE_OPENAI_SUBSCRIPTION_KEY'
    value: listKeys(cognitiveAccount.id, '2023-05-01').key1
  }
  {
    name: 'AZURE_OPENAI_CHAT_DEPLOYMENT_NAME'
    value: agentDeploymentName
  }
  {
    name: 'CHAINLIT_AUTH_SECRET'
    value: '3od/$/2/NMiaC/V%%a%wIv/:T_?:UnnNz%~Oy:D,j_eR?sR9Ad:S=-/,yPM2:.>n'
  }
  {
    name: 'LOG_LEVEL'
    value: 'INFO'
  }
  {
    name: 'JIRA_SERVER_URL'
    value: jiraServerUrl
  }
  {
    name: 'JIRA_API_USER'
    value: jiraApiUser
  }
  {
    name: 'JIRA_PROJECT_KEY'
    value: jiraProjectKey
  }
  {
    name: 'JIRA_API_TOKEN'
    value: jiraApiToken
  }
  {
    name: 'DATABASE_URL'
    value: 'sqlite+aiosqlite:///./chat_history.db'
  }
  {
    name: 'DASHBOARD_SUBSCRIPTION_ID'
    value: '9c4f81d0-fc86-4c82-b49a-0897f03ac709'
  }
  {
    name: 'DASHBOARD_RESOURCE_GROUP'
    value: 'digitaldeliveryintegration-integrationdashboards-nonprod'
  }
  {
    name: 'DASHBOARD_ID'
    value: '096400de-4567-42e5-a44b-28034a46b32a'
  }
  {
    name: 'AZURE_SUBSCRIPTION_IDS'
    value: 'de93eb29-7b3a-415b-9be0-adbf6ddcf73b,b058b336-3799-455f-a415-697be77fb8c8,4bcaeb68-1793-4b98-b24e-0a778900612f,0640cfac-5a43-49fc-b08b-c0f076a45bac'
  }
  {
    name: 'AZURE_CLIENT_ID'
    value: apiIdentity.properties.clientId
  }
  {
    name: 'AZURE_EXISTING_AIPROJECT_RESOURCE_ID'
    value: azureExistingAIProjectResourceId
  }
  {
    name: 'AZURE_AI_AGENT_NAME'
    value: agentName
  }
  {
    name: 'AZURE_EXISTING_AGENT_ID'
    value: agentID
  }
  {
    name: 'AZURE_AI_AGENT_DEPLOYMENT_NAME'
    value: agentDeploymentName
  }
  {
    name: 'AZURE_AI_EMBED_DEPLOYMENT_NAME'
    value: embeddingDeploymentName
  }
  {
    name: 'AZURE_AI_EMBED_DIMENSIONS'
    value: embeddingDeploymentDimensions
  }
  {
    name: 'RUNNING_IN_PRODUCTION'
    value: 'true'
  }
  {
    name: 'AZURE_AI_SEARCH_ENDPOINT'
    value: searchServiceEndpoint
  }
  {
    name: 'ENABLE_AZURE_MONITOR_TRACING'
    value: enableAzureMonitorTracing
  }
  {
    name: 'AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED'
    value: azureTracingGenAIContentRecordingEnabled
  }
  {
    name: 'AZURE_EXISTING_AIPROJECT_ENDPOINT'
    value: projectEndpoint
  }
]


module app 'core/host/container-app-upsert.bicep' = {
  name: 'container-app-module'
  params: {
    name: name
    location: location
    tags: union(tags, { 'azd-service-name': 'api' })
    identityName: apiIdentity.name
    containerRegistryName: containerRegistryName
    containerAppsEnvironmentName: containerAppsEnvironmentName
    targetPort: 8000
    env: env
  }
}

output SERVICE_API_IDENTITY_PRINCIPAL_ID string = apiIdentity.properties.principalId
output SERVICE_API_NAME string = app.outputs.name
output SERVICE_API_URI string = app.outputs.uri
