#!/usr/bin/env python3
"""Launch the dependency-light local NISHAN browser demonstration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[3]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Run the offline NISHAN judge demonstration in a local browser."
    )
    result.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
    result.add_argument("--port", type=int, default=8765, help="TCP port (default: 8765)")
    result.add_argument(
        "--state-dir",
        type=Path,
        default=WORKSPACE / ".nishan-demo",
        help="ignored private state directory (default: repository .nishan-demo)",
    )
    return result


def main() -> None:
    args = parser().parse_args()
    if not 0 <= args.port <= 65535:
        raise SystemExit("--port must be between 0 and 65535")
    sys.path.insert(0, str(PROJECT_DIR))
    from demo_app.engine import DemoEngine
    from demo_app.server import DemoHTTPServer

    engine = DemoEngine(WORKSPACE, args.state_dir)
    server = DemoHTTPServer((args.host, args.port), engine)
    actual_port = server.server_address[1]
    shown_host = "127.0.0.1" if args.host in {"0.0.0.0", "::"} else args.host
    print(f"NISHAN desktop: http://{shown_host}:{actual_port}/", flush=True)
    print(f"NISHAN phone:   http://127.0.0.1:{actual_port}/mobile", flush=True)
    print("Press Ctrl+C to shut down. Private run state stays in " + str(args.state_dir), flush=True)
    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        print("Warning: non-loopback binding is for a trusted local network demo only; this is not a production server.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down NISHAN demo.", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
