#!/usr/bin/env python3
"""Demo: buy the Blockchain IQ market brief through x402 with AgentKit.

Usage:
    export X402_PRIVATE_KEY=0x...   # dedicated wallet, a little USDC on Base
    python examples/demo.py [resource]

With no argument it fetches 'brief' ($0.01). 'event-risk' ($0.05) also works.
The demo invokes the provider's action directly with a ``None`` wallet
provider — the Blockchain IQ action pays off-wallet over x402 and never
touches the AgentKit wallet. In a real AgentKit agent, register
``blockchainiq_action_provider()`` alongside your other providers instead.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from blockchainiq_action_provider import blockchainiq_action_provider  # noqa: E402


def main() -> None:
    resource = sys.argv[1] if len(sys.argv) > 1 else "brief"
    provider = blockchainiq_action_provider()
    action = provider.get_actions(None)[0]
    print(f"Invoking AgentKit action '{action.name}' for resource '{resource}'...")
    print(action.invoke({"resource": resource, "max_usdc": 0.10}))


if __name__ == "__main__":
    main()
