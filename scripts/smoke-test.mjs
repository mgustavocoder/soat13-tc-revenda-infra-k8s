const apiBaseUrl = process.env.API_BASE_URL
if (!apiBaseUrl) throw new Error('Set API_BASE_URL to the deployed API Gateway URL, including /v1')

const apiKey = process.env.API_KEY
if (!apiKey) throw new Error('Set API_KEY to the deployed API Gateway key')

const endpoints = [
  '/api/health',
  '/api/clientes',
  '/api/veiculos/disponiveis',
  '/api/vendas'
]

const baseUrl = apiBaseUrl.replace(/\/$/, '')
const healthUrl = new URL(`${baseUrl}${endpoints[0]}`)
const unauthenticatedResponse = await fetch(healthUrl, {
  signal: AbortSignal.timeout(20000)
})
await unauthenticatedResponse.arrayBuffer()
if (unauthenticatedResponse.status !== 403) {
  throw new Error(`GET ${endpoints[0]} without an API key returned HTTP ${unauthenticatedResponse.status}; expected 403`)
}
console.log(`GET ${endpoints[0]} without API key ... HTTP 403 (expected)`)

const preflightResponse = await fetch(healthUrl, {
  method: 'OPTIONS',
  headers: {
    origin: 'https://example.com',
    'access-control-request-method': 'GET',
    'access-control-request-headers': 'x-api-key'
  },
  signal: AbortSignal.timeout(20000)
})
await preflightResponse.arrayBuffer()
const allowedHeaders = preflightResponse.headers
  .get('access-control-allow-headers')
  ?.toLowerCase()
  .split(',')
  .map(header => header.trim())
if (
  preflightResponse.status !== 200 ||
  !allowedHeaders?.includes('x-api-key') ||
  preflightResponse.headers.get('access-control-allow-origin') !== '*'
) {
  throw new Error(`OPTIONS ${endpoints[0]} returned HTTP ${preflightResponse.status} with invalid CORS headers`)
}
console.log(`OPTIONS ${endpoints[0]} preflight ... HTTP ${preflightResponse.status}`)

for (const endpoint of endpoints) {
  const url = new URL(`${baseUrl}${endpoint}`)
  const response = await fetch(url, {
    headers: { 'x-api-key': apiKey },
    signal: AbortSignal.timeout(20000)
  })
  await response.arrayBuffer()
  if (response.status !== 200) throw new Error(`GET ${endpoint} returned HTTP ${response.status}; expected 200`)
  console.log(`GET ${endpoint} ... HTTP ${response.status}`)
}
