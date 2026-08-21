from __future__ import annotations

import argparse

from app.backend.robot_console import ConsoleApp


def main() -> None:
    parser = argparse.ArgumentParser(description="Mecanum robot laptop operator app")
    parser.add_argument("--host", default="100.69.39.18")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    ConsoleApp(args.host, args.port).run()


if __name__ == "__main__":
    main()
