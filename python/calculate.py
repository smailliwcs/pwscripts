import sys

import metrics


def main():
    metric = metrics.parse_args()
    data = metric.calculate()
    metric.write(data, sys.stdout)


if __name__ == "__main__":
    main()
