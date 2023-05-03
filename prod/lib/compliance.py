# functions used to calculate obstacle compliance based on sensor data

# globals
verbose = True


def getAbs(_list):
    # convert _list items to their absolute value
    abs_list = []
    for elem in _list:
        abs_list.append(abs(elem))
    return abs_list


def get2Dsize(_list):
    # use absolute values
    abs_list = getAbs(_list)
    size = max(abs_list) * len(abs_list)  # could be changed in the future
    return size


def calcCompliance(accel_events, decel_events):
    # calculate compliance using accel and decel events

    # NOTE: accel_events is currently redundant

    # select largest event (by get2DSize())
    max_size = 0
    for event in decel_events:
        if get2Dsize(event) >= max_size:
            max_event = event

    # get weighted average of event (by wAvg)
    max_event = getAbs(max_event)  # NOTE: might crash if decel_events is empty (highly unlikely)
    max_event.sort(reverse=True)  # sort max_event for largest decel first
    w_avg = wAvg(max_event)

    # calculate compliance relative to max
    # 5 is a placeholder, this can be changed based on what kind of values wAvg gives out
    maxWavg = 5
    compliance = 1.0 - (w_avg / maxWavg)

    # cap compliance at 0
    if compliance < 0:
        compliance = 0

    return compliance


def wAvg(_list):
    # weighted average to calculate compliance based on deceleration values
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
