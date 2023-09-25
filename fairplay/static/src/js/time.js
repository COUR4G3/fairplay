import dayjs from 'dayjs';
import LocalizedFormat from 'dayjs/plugin/localizedFormat';
import RelativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(LocalizedFormat);
dayjs.extend(RelativeTime);


document.addEventListener('htmx:load', (ev) => {
  const timeElList = ev.detail.elt.querySelectorAll('time');
  [...timeElList].map((timeEl) => {
    const date = dayjs(timeEl.getAttribute('datetime'));

    const format = timeEl.dataset.format || 'L LT';
    const relative = timeEl.dataset.relative;

    if (relative && date.isAfter(dayjs().subtract(2, 'weeks'))) {
      timeEl.innerText = date.fromNow();

      const intervalId = setInterval(() => {
        if (!timeEl) { clearInterval(intervalId) }

        timeEl.innerText = date.fromNow();
      }, 60000);
    } else {
      timeEl.innerText = date.format(format);
    }
  });
});
