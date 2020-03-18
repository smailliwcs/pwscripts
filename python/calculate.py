import sys

import metrics


def main():
    metric = metrics.parse_args()
    series = metric.calculate()
    metric.write(sys.stdout, series)


if __name__ == "__main__":
    main()
