const form = document.querySelector('#filter-form');
const query = document.querySelector('#card-query');
const cards = [...document.querySelectorAll('.feed-card')];
const status = document.querySelector('#status');
const emptyState = document.querySelector('#empty-state');

function applyFilter() {
  const normalizedQuery = query.value.trim().toLocaleLowerCase('ru');
  let visibleCount = 0;

  for (const card of cards) {
    const matches = card.dataset.searchable.toLocaleLowerCase('ru').includes(normalizedQuery);
    card.hidden = !matches;
    visibleCount += Number(matches);
  }

  emptyState.hidden = visibleCount !== 0;
  status.textContent = normalizedQuery
    ? `Найдено карточек: ${visibleCount}`
    : `Показаны все карточки: ${visibleCount}`;
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  applyFilter();
});

form.addEventListener('reset', () => {
  window.requestAnimationFrame(applyFilter);
});

for (const card of cards) {
  card.querySelector('.card-open').addEventListener('click', () => {
    status.textContent = `Открыт ${card.querySelector('.card-meta').textContent}`;
  });
}
