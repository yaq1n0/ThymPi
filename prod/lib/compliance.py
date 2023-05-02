# file containing functions that define complaince

# imports

# globals
verbose = True


def getAbs(_list):
    abs_list = []
    for elem in _list:
        abs_list.append(abs(elem))
    return abs_list
        
def get2Dsize(_list):
    # use absolute values
    abs_list = getAbs(_list)
        
    return max(abs_list) * len(abs_list)


def calcCompliance(accel_events, decel_events):
    # select largest event (by getEventSize)
    max_size = 0
    for event in decel_events:
        if get2Dsize(event) >= max_size:
            max_event = event

    # get weighted average of event (by w_avg)
    max_event = getAbs(max_event)
    max_event.sort(reverse=True)
    w_avg = wAvg(max_event)

    # calculate compliance relative to max
    
    compliance = 1.0 - (w_avg / 5)
    
    # cap compliance at 0
    if compliance < 0:
        compliance = 0
    
    return compliance


def wAvg(_list):
    # changes to accel/decel event averaging to better represent spike
    weights = [5, 2, 1, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]

    def rel_pos(x, xs):
        if len(xs) > 0:
            return xs.index(x) / len(xs)
        else:
            if verbose:
                print("error, list is empty")
                return 0

    wsum = 0
    for elem in _list:
        x = int(round((rel_pos(elem, _list)) * len(weights), 0))
        wsum += elem * weights[x]
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
