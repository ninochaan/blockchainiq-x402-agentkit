# Blockchain IQ for Coinbase AgentKit — pay-per-call crypto data over x402

An AgentKit **action provider** that buys crypto market data from
[Blockchain IQ](https://www.blockchainiq.co/agents) one call at a time,
paying in USDC on Base through the open **x402** protocol (HTTP 402 +
EIP-3009). No account, no API key — a wallet is the only credential.

**Bounty:** this repository is an entry for the
[Blockchain IQ x402 build bounties](https://www.blockchainiq.co/blog/x402-build-bounties),
**Coinbase AgentKit slot** ("an action provider"). It qualifies with a
working paid call to one of the two bounty resources:

| Resource | Path | Price |
| --- | --- | --- |
| Market brief | `GET /api/x402/v1/brief` | **$0.01** |
| Event risk | `GET /api/x402/v1/event-risk` | **$0.05** |

## The action

`BlockchainIqActionProvider` (name `blockchainiq`) registers one action,
`fetch_paid_resource`, with arguments:

- `resource` — a catalogue name (`brief`, `event-risk`, …), a path from the
  free catalogue (`/macro`, `/stablecoins`, …) or a full URL;
- `max_usdc` — a spend guard (default $0.10): the call aborts if the server
  asks for more.

It returns a JSON string: `{resource, paid, amount_usd, settlement, data}`,
where `settlement` is the decoded `PAYMENT-RESPONSE` header (it carries the
settlement transaction hash — the proof a bounty claim needs).

The payment is signed with the key in `X402_PRIVATE_KEY`, **not** with the
AgentKit wallet: Blockchain IQ settlement is gasless and account-free, and
keeping the spend in a small dedicated wallet matches the API's own safety
advice. The action accepts the framework's `wallet_provider` argument per
contract and does not use it.

## How the x402 flow works here

`blockchainiq_x402.py` is a small self-contained x402 v2 client:

1. **Unpaid call.** `GET` the resource with no payment header.
2. **HTTP 402.** The server replies `402 Payment Required` with a base64
   `PAYMENT-REQUIRED` header: `{x402Version: 2, accepts: [...]}`. The Base
   entry is `scheme: "exact"`, `network: "eip155:8453"`, `amount: "10000"`
   (atomic USDC — $0.01 for `brief`), `asset: 0x833589fC…2913` (USDC on
   Base), `payTo: 0x617dA938…7C9e`, and `extra: {name: "USD Coin",
   version: "2"}` — the token's EIP-712 domain fields.
3. **Sign.** The client builds an EIP-3009 `TransferWithAuthorization`
   (from = your wallet, to = `payTo`, value = amount, validity window from
   `maxTimeoutSeconds`, random 32-byte nonce) and signs it as EIP-712 typed
   data with domain `{name: "USD Coin", version: "2", chainId: 8453,
   verifyingContract: <USDC>}`. Signing is offline; nothing is broadcast.
4. **Paid retry.** The request is repeated with the base64 payment payload
   in the `PAYMENT-SIGNATURE` header. A facilitator submits the
   authorization on-chain (gasless for the payer) and the server returns
   `200` with the JSON data and a `PAYMENT-RESPONSE` settlement header.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install .
```

> **Dependency note:** `coinbase-agentkit` 0.7.x imports the synchronous
> `solana.rpc.api` client, which solana-py removed in 0.37 — a plain
> `pip install coinbase-agentkit` currently resolves a `solana` version the
> package cannot import. This repo pins `solana>=0.36,<0.37` in
> `pyproject.toml` so the install works.

## Configure

The signing key comes **only** from the environment:

```bash
export X402_PRIVATE_KEY=0x...   # dedicated wallet, a little USDC on Base
```

Use a dedicated wallet with a small balance, never a main wallet. The key
is never hardcoded, logged or committed; `.env` is git-ignored (see
`.env.example`).

## Run the demo

```bash
python examples/demo.py            # buys the market brief ($0.01)
python examples/demo.py event-risk # buys event risk ($0.05)
```

Or inside an AgentKit agent:

```python
from blockchainiq_action_provider import blockchainiq_action_provider

action_providers = [blockchainiq_action_provider()]  # + your wallet provider etc.
```

## Verify locally (no funds, nothing broadcast)

```bash
python scripts/verify_local.py
```

Checks (see `VERIFICATION.md` for recorded output):

- **(a)** the unpaid call to the real endpoint returns 402 and the payment
  requirements parse to the expected amount / asset / network / payTo /
  EIP-712 domain;
- **(b)** a payment payload built from those requirements is a well-formed
  EIP-3009 authorization, signed offline with the public Hardhat test key,
  and the signer recovers correctly — the payload is never sent;
- **(c)** the provider constructs, registers the `fetch_paid_resource`
  action with its schema, and reports network support via
  `supports_network`.

## Claiming the bounty

Make one real paid call with a funded wallet (the demo above), then email
**partnerships@blockchainiq.co** with this repository's link and the
settlement transaction hash from the `PAYMENT-RESPONSE` header. Claims are
checked in email-arrival order; the round closes 31 Dec 2026, 11:59 PM
Central. First passing claim overall is paid $150, the next three $125
each, in USDC on Base.

## License

MIT
