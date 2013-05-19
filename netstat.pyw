from subprocess import Popen, PIPE
import re

def ping(host='google.com', n=10, timeout_milliseconds=1000):
    """
    Pings an address n times, returning a list of ping times. In case of
    timeout, the value is omitted.
    """
    command = ['ping', '-n', str(n), '-w', str(timeout_milliseconds), host]
    (stdout, sterr) = Popen(command, stdout=PIPE, shell=True).communicate()
    return map(int, re.findall('time\=(\d+)ms', stdout))

def drop_problems(ping_times, expected_n, test_name):
    """
    Checks if the given ping times have had packet loss problems.
    """
    dropped_packets = expected_n - len(ping_times)
    if dropped_packets > expected_n / 3:
        return [('packet loss', 
                 '{} is dropping packets ({} out of {}).'.format(test_name,
                                                                 dropped_packets,
                                                                 expected_n))]
    else:
        return []

def speed_problems(ping_times, expected_n, test_name):
    """
    Checks if the given list of ping times have had speed problems.
    """
    ping_times.sort()
    median = ping_times[len(ping_times) / 2]

    if median > 500:
        return [('speed',
                 '{} is extremely slow ({} ms).'.format(test_name, median))]

    elif median > 350:
        return [('speed', 
                 '{} is very slow ({} ms).'.format(test_name, median))]

    elif median > 200:
        return [('speed',
                 '{} is slow ({} ms).'.format(test_name, median))]
    else:
        return []

def get_problems(ping_times, expected_n, test_name):
    """
    Returns a list of problems with the given ping_times. Problems are a tuple
    (problem_name, description), such as ('slow', 'test_name is slow (250 ms)')

    expected_n is the number of pings sent that are expected to have completed.
    If the ping_times contain less than expected_n items, it means there are
    packet loss problems.
    """
    if len(ping_times) == 0:
        # No point in continuing with further statistics.
        return [('availability', '{} is unavailable.'.format(test_name))]

    status_functions = [drop_problems, speed_problems]
    sub_results = [f(ping_times, expected_n, test_name) for f in status_functions]
    return sum(sub_results, [])

from collections import defaultdict
results = defaultdict(list)

def process(host, test_name, n=10, timeout_milliseconds=1000):
    """
    Runs a ping test on a given host, yielding problems that have appeared or
    disappeared since the last 'process' call with the same host.

    Returns a generator that yields descriptive strings, such as 'test_name
    availability is back to normal' and 'test_name is dropping packets (2 out
    of 5)'.
    """
    ping_times = ping(host, n, timeout_milliseconds)
    new_problems = get_problems(ping_times, n, test_name) 

    new_labels = [label for label, text in new_problems]
    old_labels = [label for label, text in results[test_name]]

    results[test_name] = new_problems

    # Returns new problems that appeared.
    for new_label, new_text in new_problems:
        if new_label not in old_labels:
            yield new_text

    if 'availability' in new_labels:
        # Don't report that old problems are back to normal when the whole
        # thing doesn't work.
        return

    # Returns old problems that disappeared.
    for old_label in old_labels:
        if old_label not in new_labels:
            yield '{} {} {}'.format(test_name, old_label, 'is back to normal.')


if __name__ == '__main__':
    import time

    from background import tray, notify
    tray('Network status', 'globe-network.ico')

    while True:
        messages = []
        messages.extend(process('192.168.0.1', 'local network'))
        messages.extend(process('8.8.8.8', 'internet connection'))
        messages.extend(process('ufsc.br', 'dns server'))
        messages.extend(process('www.google.com', 'google search'))
        if messages:
            notify('Network', '\n'.join(messages))

        time.sleep(60)
