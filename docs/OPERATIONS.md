# Running and recovering a paper portfolio

## Workflow

1. Download a completed signed edition through the author's distribution channel.
2. Configure the publisher's public key locally, verify, and install the edition.
3. Read the research and preview with your own allocation limits.
4. Inspect the target positions, cash reserve, orders, account ID, and package hash.
5. Explicitly run `execute-paper` with that plan and account ID.
6. If an order remains open, run the same command again to reconcile, or use
   `cancel-paper`. No automatic execution loop runs in the background.

The platform controls who may download future editions. This client does not
implement checkout, GitHub membership, royalties, subscription accounting, or a
license server. Downloaded files and local records remain under the customer's
control. An open-source client cannot enforce revocation of existing copies.

## Persistent state

The local state directory contains `engine.sqlite` and `engine.lock`. It must be
on a local filesystem that supports SQLite durability and `flock`, and owned by
the operator. Do not use a shared network drive or share it between machines.
CLI processes serialize on that directory's lock. Keep one state directory for
the dedicated paper account and do not run a separate trading system on it.

The database contains signed package proof chains, edition identities, reviewed
plans, account bindings, submission attempts, and broker observations. It can
contain personal account identifiers; it is ignored by Git. It never stores API
credentials. Back it up as local operational data, not as a research product.

## Recovery behavior

Before submission, the order's deterministic client ID and attempt flag are
durably recorded. A restart looks up attempted orders instead of resending them.
Only a complete verified fill allows progression to the next order; an order
recorded as completely filled is not looked up again. All sells precede buys, and
buys use currently observed cash after confirmed fills.

If the broker answers a submission with a refusal, an HTTP 4xx status other than
408 such as 403 for insufficient buying power or 429 for too many requests, it
created no order. The engine records the refusal with the order, halts the plan
and reports the stock and the broker's reason. `execute-paper` and `cancel-paper`
then report the plan as `halted`, and a fresh preview is allowed.

If a transport failure occurs, or the broker answers with a server error, run the
same `execute-paper` command again. If the broker returns the matching order, its
terms, status, and fill quantity are checked. If it cannot find an attempted
order, the engine remains blocked: a missing response is not proof that the
broker never received the submission. Inspect the paper account and its order
history. The order is never resent. A submission can start only while its plan
is fresh (120 seconds by default). Once that window and five further minutes have
passed, `cancel-paper` asks the broker again; if it still has no order under that
client ID, the order is recorded as never placed, listed under `never_placed`,
and the plan closes. Before then, `cancel-paper` refuses and names the time.

`cancel-paper` only cancels broker orders whose identity and full terms match
the stored plan. Cancellation may require another invocation to observe the
terminal result. Never delete the state directory to work around uncertainty.
An externally replaced order, an inconsistent fill, or an order the broker
reported and later cannot find requires manual investigation.

After rejection, cancellation, or expiry of a confirmed order, the remaining
plan stops. Create a fresh preview against actual resulting positions; it refuses
to plan while the account has open orders. A stale plan may reconcile existing
orders but cannot submit additional ones; cancellation still works. Avoid changing
the active research package while a plan is running.

## Endpoint and execution scope

- Orders/account: `https://paper-api.alpaca.markets/v2/`
- Quotes: `https://data.alpaca.markets/v2/stocks/quotes/latest?feed=iex`
- HTTPS redirects and proxy-environment inheritance are disabled.
- Each command reads asset tradability once per symbol, with one listing of
  active US equities for several symbols, and reuses an open market-clock reading
  until a minute before the close. Before each order it still reads the account,
  positions, open orders and current quotes.
- There is no configurable trading host, live-mode flag, dynamic plug-in loader,
  package command hook, research crawler, or LLM integration.
- Orders use whole-share quantities, DAY duration, regular sessions, and explicit
  price limits. The initial version does not support fractional positions.

API references: [orders](https://docs.alpaca.markets/us/reference/postorder),
[lookup by client ID](https://docs.alpaca.markets/us/reference/getorderbyclientorderid),
[latest quotes](https://docs.alpaca.markets/us/reference/stocklatestquotes-1).

## Optional activation addon

Version 0.2 exposes an optional `activation` argument to `build_plan` for a
separately installed local addon. Its exact fields are `package_sha256`, `symbols`,
`sides` (a buy/sell map for precisely those symbols), `valid_until`, and
`decision_sha256`. It can restrict a rebalance to selected symbols and directions;
it cannot change the publisher's target weights or bypass customer limits.
Whole-share rounding cannot reverse an activated direction. New submissions
recheck activation expiry, including after the final broker observation.

Activation is local operator input, not a publisher signature or payment proof.
The public engine contains no news collection, scoring or threshold policy. The
addon must retain and validate its own decision evidence. The plan records its
decision hash so that evidence can be inspected. A pending broker order may be
reconciled after activation expires, but no remaining new order may be submitted.
