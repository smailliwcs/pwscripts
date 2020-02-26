import sys

import metrics


def main():
    metrics.parse_args().write(sys.stdout)


if __name__ == "__main__":
    main()
