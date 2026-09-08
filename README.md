# Liquid 2026-09-06 incident: fork transaction replay sets

On 2026-09-06 an Elements range-proof verification-cache bug (commit `c26d719`) was
exploited to mint L-BTC on Liquid mainnet, splitting the chain at height **4,050,335**.
Most nodes rejected the exploit block (4,050,336) and stalled at 4,050,335; a minority
built an 897-block fork to 4,051,232. These files list the transactions on that
abandoned fork so anyone can watch which ones reappear when the valid chain restarts.

Match is by **exact txid** appearing on the valid chain **above height 4,050,335**.

## Files
- `expected-replay.csv` / `.json` — legitimate user transactions mined on the fork. We
  **expect** most of these to be re-mined on the valid chain during recovery.
- `do-not-expect-replay.csv` — the mint (`f24a4b17…`) and its spend-descendants. These
  move inflated L-BTC that does not exist on the valid chain, so they can **never** be
  replayed. If any ever appears on the valid chain, the inflation was accepted there.
- `replay-sets.json` — both sets plus metadata.

## Counts
| set | count |
|---|---|
| expected to replay | see `expected-replay.csv` |
| never replayable (tainted) | 8 |
| (coinbase transactions, one per fork block, are excluded — each valid block has its own) |

## Caveats
- Exact-txid only: a transaction re-signed with a different fee gets a new txid and will
  not match, even if economically equivalent.
- "Expected" is not a guarantee: a user may never rebroadcast, or a conflict may prevent
  re-mining. The list is what to watch, not a prediction each will appear.
- Fork data source: Esplora block archive of heights 4,050,336–4,051,232.
