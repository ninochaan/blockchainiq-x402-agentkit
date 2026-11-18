"""Coinbase AgentKit action provider for Blockchain IQ's x402 API.

Adds one action, ``fetch_paid_resource``, to any AgentKit agent: it buys
crypto market data from Blockchain IQ (https://www.blockchainiq.co/agents),
paying per call in USDC on Base through the x402 v2 protocol.

The payment is an EIP-3009 ``transferWithAuthorization`` signed with the key
in the ``X402_PRIVATE_KEY`` environment variable — deliberately *not* the
AgentKit wallet: Blockchain IQ needs no account, settlement is gasless, and
keeping the spend in a small dedicated wallet matches the API's own safety
advice. The AgentKit ``wallet_provider`` argument is accepted (per the
framework contract) but not used for payment.

Bounty: Blockchain IQ x402 build bounties, Coinbase AgentKit slot — a
public repo with a working paid call to ``brief`` ($0.01) or
``event-risk`` ($0.05).
"""

from __future__ import annotations

import json
from typing import Any

from coinbase_agentkit import ActionProvider, WalletProvider, create_action
from pydantic import BaseModel, Field

from blockchainiq_x402 import BASE_URL, fetch_paid_resource


class FetchPaidResourceInput(BaseModel):
    """Input schema for the fetch_paid_resource action."""

    resource: str = Field(
        default="brief",
        description=(
            "Blockchain IQ resource to fetch: a catalogue name such as "
            "'brief' (market brief, $0.01) or 'event-risk' (scheduled "
            "market-moving events, $0.05), any other path from the free "
            f"catalogue at {BASE_URL} (e.g. '/macro', '/stablecoins'), or a "
            "full URL. Paid resources are paid automatically through x402."
        ),
    )
    max_usdc: float = Field(
        default=0.10,
        description=(
            "Spend guard: refuse to pay if the resource costs more than "
            "this many USDC in a single call."
        ),
    )


class BlockchainIqActionProvider(ActionProvider):
    """Action provider that fetches Blockchain IQ data over x402."""

    def __init__(self) -> None:
        super().__init__("blockchainiq", [])

    @create_action(
        name="fetch_paid_resource",
        description=(
            "Fetch crypto market data from Blockchain IQ, paying per call "
            "in USDC on Base through the x402 protocol when the resource is "
            "paid. Use 'brief' for a $0.01 market brief (BTC/ETH/SOL/XRP "
            "prices, 48h events, risk flags) or 'event-risk' for $0.05 "
            "scheduled market-moving events. The payment signing key comes "
            "from the X402_PRIVATE_KEY environment variable. Returns a JSON "
            "string with the data and, for paid calls, the settlement proof."
        ),
        schema=FetchPaidResourceInput,
    )
    def fetch_paid_resource(
        self, wallet_provider: WalletProvider, args: dict[str, Any]
    ) -> str:
        parsed = FetchPaidResourceInput(**args)
        try:
            result = fetch_paid_resource(
                parsed.resource, max_amount_usd=parsed.max_usdc
            )
        except Exception as exc:  # surface failures to the agent as text
            return f"Error fetching Blockchain IQ resource: {exc}"
        return json.dumps(
            {
                "resource": parsed.resource,
                "paid": result.paid,
                "amount_usd": result.amount_usd,
                "settlement": result.settlement,
                "data": result.data,
            }
        )

    def supports_network(self, network) -> bool:
        """The payment runs off-wallet over HTTP; any network context works."""
        return True


def blockchainiq_action_provider() -> BlockchainIqActionProvider:
    """Factory matching AgentKit's provider conventions."""
    return BlockchainIqActionProvider()
