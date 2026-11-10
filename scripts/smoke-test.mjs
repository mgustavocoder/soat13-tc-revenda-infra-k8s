import { createHash, createHmac } from 'node:crypto'
import { execFileSync } from 'node:child_process'

const apiBaseUrl = process.env.API_BASE_URL
if (!apiBaseUrl) throw new Error('Set API_BASE_URL to the deployed API Gateway URL, including /v1')

const region = process.env.AWS_REGION || 'us-east-1'
const credentials = JSON.parse(execFileSync(
  'aws',
  ['configure', 'export-credentials', '--format', 'process'],
  { encoding: 'utf8' }
))
const timestamp = new Date().toISOString().replace(/[:-]|\.\d{3}/g, '')
const date = timestamp.slice(0, 8)
const service = 'execute-api'
const scope = `${date}/${region}/${service}/aws4_request`
const payloadHash = createHash('sha256').update('').digest('hex')
const endpoints = [
  '/api/health',
  '/api/clientes',
  '/api/veiculos/disponiveis',
  '/api/vendas'
]

const hmac = (key, value) => createHmac('sha256', key).update(value).digest()

for (const endpoint of endpoints) {
  const url = new URL(`${apiBaseUrl.replace(/\/$/, '')}${endpoint}`)
  const canonicalHeaders = [
    `host:${url.host}`,
    `x-amz-date:${timestamp}`,
    ...(credentials.SessionToken ? [`x-amz-security-token:${credentials.SessionToken}`] : [])
  ].join('\n') + '\n'
  const signedHeaders = [
    'host',
    'x-amz-date',
    ...(credentials.SessionToken ? ['x-amz-security-token'] : [])
  ].join(';')
  const canonicalRequest = [
    'GET',
    url.pathname,
    '',
    canonicalHeaders,
    signedHeaders,
    payloadHash
  ].join('\n')
  const stringToSign = [
    'AWS4-HMAC-SHA256',
    timestamp,
    scope,
    createHash('sha256').update(canonicalRequest).digest('hex')
  ].join('\n')
  const signingKey = hmac(
    hmac(
      hmac(
        hmac(`AWS4${credentials.SecretAccessKey}`, date),
        region
      ),
      service
    ),
    'aws4_request'
  )
  const signature = createHmac('sha256', signingKey).update(stringToSign).digest('hex')
  const authorization = `AWS4-HMAC-SHA256 Credential=${credentials.AccessKeyId}/${scope}, SignedHeaders=${signedHeaders}, Signature=${signature}`
  const headers = {
    'x-amz-date': timestamp,
    authorization
  }
  if (credentials.SessionToken) headers['x-amz-security-token'] = credentials.SessionToken

  const response = await fetch(url, { headers, signal: AbortSignal.timeout(20000) })
  await response.arrayBuffer()
  if (!response.ok) throw new Error(`GET ${endpoint} returned HTTP ${response.status}`)
  console.log(`GET ${endpoint} ... HTTP ${response.status}`)
}
