# 01. Overview and Core Concepts

**Inference Hooks** are an inline security feature for Claude Enterprise that allows organizations to inspect and govern prompts in real-time before inference occurs.

---

## 🛡️ What are Inference Hooks?

Inference Hooks act as an inline interceptor for user interactions. When a user submits a governed prompt or when Claude receives a tool result, Anthropic intercepts the request and sends an HTTPS POST to your configured security endpoint. Your server evaluates the content and returns an allow or deny verdict before the model is allowed to process the request.

---

## 🌐 Scope and Availability

> [!WARNING]
> **Platform Availability**: Inference Hooks are ONLY available on the **Claude Enterprise** plan. They are NOT available on standard Claude plans (Pro, Team), the Claude API, Amazon Bedrock, or Google Cloud.

- **Supported Surfaces**: Organization-wide covering **claude.ai**, **Claude Code**, and **Claude Cowork**.

---

## 🎯 Target Audience & Use Cases

**Primary Audience**: Security teams, Compliance officers, and Data Loss Prevention (DLP) engineers.

**Core Use Cases**:
- **DLP & PII Detection**: Prevent sensitive company data or Personally Identifiable Information from being processed by the model.
- **Content Policy Enforcement**: Enforce acceptable use policies by blocking inappropriate or off-topic prompts.
- **Attack Protection**: Detect and block prompt injection or jailbreak attempts in real-time.

---

## ⚖️ Feature Comparisons

Understanding how Inference Hooks compare to other compliance tools is crucial for designing your security architecture.

### Inference Hooks vs Compliance API

| Feature | Inference Hooks | Compliance API |
| :--- | :--- | :--- |
| **Timing** | Real-time, inline pre-inference | Post-hoc, asynchronous retrieval |
| **Action** | Block or allow requests | Audit, export, or hard-delete |
| **Content Scope** | Prompt text only | Full chats, files, projects, sessions |

### Inference Hooks vs Claude Code Hooks & SDK Permissions

| Feature | Enterprise Inference Hooks | Claude Code Hooks & SDK Permissions |
| :--- | :--- | :--- |
| **Location** | Server-side enterprise | Client-side local environment / application process |
| **Governance** | Org-wide enforced by Admins | Local execution configured by developer / SDK policy |
| **Target** | All claude.ai and Code traffic | Specific local commands, file ops, and tool calls |

> [!TIP]
> For client-side SDK permission modes and `canUseTool` callbacks, see the official docs: [Permissions](../../docs/en/permissions.md), [Permission modes](../../docs/en/permission-modes.md), [Agent SDK permissions](../../docs/en/agent-sdk/permissions.md). For the 3-layer governance matrix, see [Governance defense-in-depth](../governance-defense-in-depth.md).

---
*Next Module: [02. Configuration and Setup](02_configuration_and_setup.md)*
