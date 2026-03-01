# Playdate Match-3 Prototype (Larry)

Tiny Playdate prototype focused on a **vertical slice**:
- 6x6 grid render
- cursor movement + tile swap
- single-match (3+) clear
- gravity refill

## Project layout

- `source/main.lua` — game loop + board logic
- `build.sh` — build helper (requires Playdate SDK)

## Requirements

- Playdate SDK installed
- `PLAYDATE_SDK_PATH` exported (path to SDK root)

## Build

```bash
./build.sh
```

Expected output:
- `build/Match3Prototype.pdx`

## Sideload

Use Playdate Simulator or device sideload per SDK docs.

## Notes

This is intentionally minimal to prove loop quality before polish.
