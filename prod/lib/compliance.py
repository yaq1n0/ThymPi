# file containing functions that define complaince

# imports

# globals
verbose = True


class ADEvent:
    # accelerate decelerate event
    def __init__(self, event_list):
        self.list = event_list
        self.size = getEventSize(self.list)


def getEventSize(event):
    return max(event) * len(list)


def calcCompliance(accel_events, decel_events):
    ADEvents = []

    # convert into ADEvent list (to get size)
    for elem in decel_events:
        ADEvents.append(elem)

    # select largest event (by getEventSize)
    max_size = 0
    max_event = None
    for elem in ADEvents:
        if elem.size >= max_size:
            max_event = elem

    # get weighted average of event (by w_avg)
    w_avg = wAvg(max_event.list.sort(reverse=True))
    if verbose:
        print(w_avg)

    # calculate compliance relative to max
    compliance = 1.0 - (w_avg / 25)


def wAvg(_list):
    # changes to accel/decel event averaging to better represent spike
    weights = [1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]

    def rel_pos(x, xs):
        if len(xs) > 0:
            return xs.index(x) / len(xs)
        else:
            if verbose:
                print("error, list is empty")
                return 0

    wsum = 0
    for elem in _list:
        wsum += elem * weights[round(rel_pos(elem, _list) * len(weights), 0)]
    wavg = wsum / len(_list)

    return wavg

def getComplianceLEGACY(self, accel_events, decel_events):
    # calculate compliance from list of acceleration and deceleration events (accel_events not currently used)
    # NOTE: modify this function to change how compliance is calculated

    # current algorithm
    # take abs value of top decel event and use -25 as max decel
    # calculate based on inverse ratio
    decel_events.sort()

    if self.verbose:
        p = []
        for d in decel_events[-10:]:
            p.append(round(d, 2))

        print(p)

    top = abs(decel_events[0])
    compliance = 1.0 - (top / 25)

    if compliance < 0:
        compliance = 0  # cap compliance at 0

    return round(compliance, 2)
