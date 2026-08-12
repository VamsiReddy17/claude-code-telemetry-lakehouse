# 03. Webhook Schema and Verdicts

This module explains the lifecycle of a governed request, the payload schema, and how to format verdicts for Inference Hooks.

---

## 🔄 Request Flow

The Inference Hooks evaluation happens synchronously during a user's request. 

1. **User Action**: The user submits a prompt, or Claude receives a tool result.
2. **Intercept**: Anthropic intercepts the payload before it reaches the inference model.
3. **Webhook POST**: Anthropic sends an HTTPS POST request containing the content to your configured security endpoint.
4. **Evaluation**: Your security server evaluates the content against your policies.
5. **Verdict Return**: Your server returns an **allow** or **deny** verdict.
6. **Resolution**: 
   - If allowed, inference proceeds normally.
   - If denied, the request is blocked and the user is shown a policy-blocked message.

---

## ⏱️ Latency Requirements

> [!WARNING]
> The entire round-trip evaluation **must complete within the configurable timeout** (default is 5 seconds). If your server fails to respond in time, the configured failure policy (fail open or fail closed) will be applied.

---

## 🔐 Request Signing & Authentication

To ensure that incoming requests to your security server are genuinely from Anthropic and haven't been tampered with, Anthropic uses the **Standard Webhooks** specification for request signing. 

Your server must verify the cryptographic signature in the request headers before processing the payload.

---

## 📦 Request Payload & Visibility

When an intercept occurs, the payload sent to your server includes the necessary context for evaluation.

### What is Inspectable
- **Prompt Text Content**: The raw text submitted by the user or the textual result of a tool execution.

### What is NOT Inspectable
- **Full Files**: Complete file attachments are not sent in the webhook payload.
- **Org Configuration**: Workspace or organization settings are excluded.
- **Historical Context**: Previous chat history leading up to the current prompt is not included in the payload.

---

## ⚖️ Verdict Schema

Your endpoint must return a well-formed JSON response indicating the verdict.

### Allow Verdict
Indicates that the content passed security checks. Inference proceeds normally.

```json
{
  "verdict": "allow"
}
```

### Deny Verdict
Indicates that the content violated a security policy. The request is blocked immediately.

```json
{
  "verdict": "deny",
  "reason": "This prompt contains restricted PII and violates company policy."
}
```

> [!NOTE]
> The `reason` field in a deny verdict is configurable and will be displayed directly to the user in the UI, helping them understand why their request was blocked.

---
*Next Module: [04. Failure Handling and Best Practices](04_failure_handling_and_best_practices.md)*
