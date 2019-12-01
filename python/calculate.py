import sys

import metrics


def main():
    metric = metrics.parse_args()
    metric.write_arguments(sys.stdout)
    metric.write_data(metric.calculate(), sys.stdout)


if __name__ == "__main__":
    main()
