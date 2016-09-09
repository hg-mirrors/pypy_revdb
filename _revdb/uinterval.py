import bisect


class UnionOfIntervals(object):
    def __init__(self):
        # invariant: this list is of even length, sorted, without duplicates;
        # it stands for range(x[0], x[1]) + range(x[2], x[3]) + ...
        self.interval_ends = []

    def add_range(self, start, stop):
        """Add all of range(start, stop) to the set."""
        if start >= stop:
            return
        index1 = bisect.bisect_left(self.interval_ends, start)
        index2 = bisect.bisect_right(self.interval_ends, stop)

        if index1 & 1:
            index1 -= 1
            start = self.interval_ends[index1]

        if index2 & 1:
            stop = self.interval_ends[index2]
            index2 += 1

        self.interval_ends[index1:index2] = [start, stop]
        #assert self.interval_ends == sorted(self.interval_ends)
        #assert len(set(self.interval_ends)) == len(self.interval_ends)

    def covers(self, start, stop):
        """Check if all of range(start, stop) is inside the set."""
        return stop <= self.longest(start)

    def longest(self, start):
        """Returns the largest stop such that self.covers(start, stop)."""
        index1 = bisect.bisect_right(self.interval_ends, start)
        if index1 & 1:
            return self.interval_ends[index1]
        return start
