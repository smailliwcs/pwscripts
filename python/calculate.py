import sys

import metrics


def main():
    metrics.parse_args().calculate().to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
