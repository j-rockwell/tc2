struct TimeComponents {
    let hours: Int
    let minutes: Int
    let seconds: Int
}

func secondsToComponents(_ value: Int) -> TimeComponents {
    let secs = max(0, value)
    let hours = secs / 3600
    let minutes = (secs % 3600) / 60
    let seconds = secs % 60
    return TimeComponents(hours: hours, minutes: minutes, seconds: seconds)
}

func componentsToSeconds(_ value: TimeComponents) -> Int {
    let hours = value.hours
    let minutes = value.minutes
    let seconds = value.seconds
    return max(0, hours) * 3600 + max(0, min(59, minutes)) * 60 + max(0, min(59, seconds))
}
