import sys
from .cli import main

if __name__ == "__main__":
    # __main__.py is ugly and confusing, monkey patch executable to say snakeviz
    sys.argv[0] = "snakeviz"
    sys.exit(main())
