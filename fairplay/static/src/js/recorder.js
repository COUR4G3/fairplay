let events = [];

rrweb.record({
    emit(event) {
        events.push(event);
    },
})
