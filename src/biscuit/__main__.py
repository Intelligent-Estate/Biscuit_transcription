from __future__ import annotations

import sys
from pathlib import Path

from biscuit.release import release_self_check


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--self-check" in args or "--self-check-file" in args:
        ok, lines = release_self_check()
        if "--self-check-file" in args:
            file_index = args.index("--self-check-file") + 1
            if file_index >= len(args):
                raise SystemExit(2)
            Path(args[file_index]).write_text("\n".join(lines) + "\n", encoding="utf-8")
        else:
            for line in lines:
                print(line)
        raise SystemExit(0 if ok else 1)

    from biscuit.app import main

    main()
