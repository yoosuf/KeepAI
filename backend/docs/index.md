# KeepAI Documentation

KeepAI is a privacy-first FastAPI backend for running local LLMs (via Ollama) with JWT authentication, database-driven RBAC, and structured JSON extraction.

---

## Quick Navigation

### Getting Started
| Doc | Description |
|-----|-------------|
| [Getting Started](guides/getting-started.md) | Set up and run KeepAI locally or with Docker |
| [Configuration](guides/configuration.md) | All environment variables and settings |
| [Walkthrough](development/walkthrough.md) | Step-by-step tour of the full system |

### Architecture & Design
| Doc | Description |
|-----|-------------|
| [Architecture Overview](architecture.md) | Hexagonal architecture, layers, request flow |
| [Extending LLM Providers](guides/extending-llm.md) | Swap Ollama for OpenAI, Anthropic, or any LLM |
| [RBAC Guide](guides/rbac.md) | Roles, permissions, and access control |

### API Reference
| Doc | Description |
|-----|-------------|
| [API Reference](api/reference.md) | Complete endpoint documentation with examples |

### Deployment
| Doc | Description |
|-----|-------------|
| [Deployment Guide](guides/deployment.md) | Docker, manual, and production hardening |

### Development
| Doc | Description |
|-----|-------------|
| [Contributing](development/contributing.md) | How to contribute, code standards, PR process |
| [Testing Guide](development/testing.md) | Testing patterns, fixtures, async tests |

### Community
| Doc | Description |
|-----|-------------|
| [FAQ](community/faq.md) | Frequently asked questions |
| [Troubleshooting](community/troubleshooting.md) | Common issues and fixes |
| [Roadmap](community/roadmap.md) | Planned features and phases |
| [Changelog](community/changelog.md) | Version history |
| [Security Policy](community/security.md) | Vulnerability reporting |
| [Code of Conduct](community/code-of-conduct.md) | Community standards |

---

## Project at a Glance

```
POST /api/v1/prompts
      │
      ▼
  Router (FastAPI)          ← Pydantic validation + JWT auth
      │
      ▼
  PromptService             ← Business logic
      │
      ▼
  LLMInterface (port)       ← Abstract contract
      │
      ▼
  OllamaClient (adapter)    ← HTTP call to local Ollama
      │
      ▼
  PostgreSQL                ← Async SQLAlchemy persistence
```

**Swap the adapter, keep everything else.** Replace `OllamaClient` with any `LLMInterface` implementation to use OpenAI, Anthropic, or any other provider.

---

## Key Design Principles

- **Privacy-first** — data never leaves your infrastructure
- **Hexagonal architecture** — swap LLM backends without changing business logic
- **Async throughout** — non-blocking I/O for LLM calls and database
- **DB-driven RBAC** — roles and permissions in PostgreSQL, not in code
- **Testable by design** — every layer mockable, no real DB or LLM required in tests
