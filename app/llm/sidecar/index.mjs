/**
 * 0G Compute TeeML sidecar — invoked by app/llm/og_compute.py via subprocess.
 *
 * Protocol:
 *   stdin:  JSON { messages, model, max_tokens, temperature }
 *   stdout: last line is JSON { ok, content?, signature?, chat_id?, tee_verified?, error?, model?, tee_signer? }
 *
 * Env: ZERO_G_RPC_URL, ZERO_G_PRIVATE_KEY, ZERO_G_COMPUTE_PROVIDER
 *      Optional: ZERO_G_COMPUTE_SERVICE_URL, ZERO_G_COMPUTE_MODEL
 */
import { ethers } from "ethers"
import { createZGComputeNetworkBroker } from "@0gfoundation/0g-compute-ts-sdk"

const RPC = process.env.ZERO_G_RPC_URL || "https://evmrpc.0g.ai"
const PK = process.env.ZERO_G_PRIVATE_KEY || ""
const PROVIDER = process.env.ZERO_G_COMPUTE_PROVIDER || ""
const SERVICE_URL_OVERRIDE = process.env.ZERO_G_COMPUTE_SERVICE_URL || ""
const MODEL_OVERRIDE = process.env.ZERO_G_COMPUTE_MODEL || ""

function emit(obj) {
  process.stdout.write(JSON.stringify(obj) + "\n")
}

async function readStdin() {
  return new Promise((resolve) => {
    let buf = ""
    process.stdin.setEncoding("utf8")
    process.stdin.on("data", (c) => (buf += c))
    process.stdin.on("end", () => resolve(buf))
  })
}

async function main() {
  if (!PK) throw new Error("ZERO_G_PRIVATE_KEY not set")
  if (!PROVIDER) throw new Error("ZERO_G_COMPUTE_PROVIDER not set")

  const raw = await readStdin()
  const req = JSON.parse(raw || "{}")
  const messages = req.messages || []
  const max_tokens = req.max_tokens || 1024
  const temperature = req.temperature ?? 0.3

  const provider = new ethers.JsonRpcProvider(RPC)
  const wallet = new ethers.Wallet(PK, provider)
  const broker = await createZGComputeNetworkBroker(wallet)

  // Resolve service URL + model
  let endpoint = SERVICE_URL_OVERRIDE
  let model = MODEL_OVERRIDE
  let teeSigner = ""
  if (!endpoint || !model || !teeSigner) {
    const meta = await broker.inference.getServiceMetadata(PROVIDER)
    endpoint = endpoint || meta.endpoint
    model = model || meta.model
  }
  // Fetch on-chain provider signer status — proves TEE attestation.
  try {
    const status = await broker.inference.checkProviderSignerStatus(PROVIDER)
    teeSigner = status?.teeSignerAddress || ""
  } catch (_) {}

  if (!endpoint) throw new Error("service endpoint not resolved")
  if (!model) model = req.model

  // Billing content = user's last message text per SDK example.
  const lastUser = [...messages].reverse().find((m) => m.role === "user")
  const billingContent = lastUser?.content || messages.map((m) => m.content).join("\n")

  // Per-request signed headers
  const headers = await broker.inference.getRequestHeaders(PROVIDER, billingContent)

  // Direct fetch — bypasses openai SDK which adds stream_options that some
  // proxies reject. enable_thinking:false disables reasoning model token
  // burn (no-op for non-reasoning models).
  const body = {
    messages,
    model,
    max_tokens,
    temperature,
    stream: false,
    chat_template_kwargs: { enable_thinking: false },
  }
  const url = `${endpoint.replace(/\/+$/, "")}/chat/completions`

  let res, completion
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify(body),
    })
    const txt = await res.text()
    if (!res.ok) {
      emit({ ok: false, error: `chat ${res.status}: ${txt.slice(0, 400)}` })
      return
    }
    completion = JSON.parse(txt)
  } catch (e) {
    emit({ ok: false, error: `fetch failed: ${e.message}` })
    return
  }

  const choice = completion?.choices?.[0]
  const text = choice?.message?.content || ""
  const chatId = completion?.id || ""

  // Settlement + signature retrieval. Provider TTLs sig quickly; failure ok.
  let teeVerified = false
  let signature = ""
  const usageContent = JSON.stringify({
    input_tokens: completion?.usage?.prompt_tokens || 0,
    output_tokens: completion?.usage?.completion_tokens || 0,
  })
  try {
    const result = await broker.inference.processResponse(PROVIDER, chatId, usageContent)
    teeVerified = result === true || result?.valid === true
    signature = result?.signature || result?.sig || ""
  } catch (_) {
    // Provider may have already TTL'd the chat sig. The TEE attestation
    // proof still stands via on-chain teeSignerAcknowledged status.
  }

  emit({
    ok: true,
    content: text,
    signature,
    chat_id: chatId,
    tee_verified: teeVerified || !!teeSigner,
    tee_signer: teeSigner,
    model,
    usage: completion?.usage || null,
  })
}

main().catch((e) => {
  emit({ ok: false, error: e.message })
  process.exit(0)
})
