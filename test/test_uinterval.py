import support    # set up sys.path
from hypothesis import given, strategies
from _revdb.uinterval import UnionOfIntervals


bounds = strategies.integers(min_value=1, max_value=10)


@given(strategies.lists(strategies.tuples(bounds, bounds)), bounds, bounds)
def test_union_of_intervals(lst, final_start, final_stop):
    s = set()
    u = UnionOfIntervals()
    for start, stop in lst:
        u.add_range(start, stop)
        s.update(range(start, stop))
    expected = s.issuperset(range(final_start, final_stop))
    assert u.covers(final_start, final_stop) == expected
