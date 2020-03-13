import sys

import metrics


def main():
    metric = metrics.parse_args()
    values = metric.calculate()
    metric.write(sys.stdout, values)


if __name__ == "__main__":
    main()
