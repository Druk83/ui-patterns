const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const scriptPath = path.join(
  __dirname,
  '..',
  'шаблоны-экранов',
  'карточная-лента',
  'card-feed.js',
);
const script = fs.readFileSync(scriptPath, 'utf8');
const listeners = new Map();
const query = { value: '' };
const status = { textContent: '' };
const emptyState = { hidden: true };

function makeCard(label, searchable) {
  const openButton = {
    addEventListener(eventName, callback) {
      listeners.set(`${label}:${eventName}`, callback);
    },
  };
  return {
    hidden: false,
    dataset: { searchable },
    querySelector(selector) {
      if (selector === '.card-open') return openButton;
      if (selector === '.card-meta') return { textContent: label };
      throw new Error(`Unexpected selector: ${selector}`);
    },
  };
}

const cards = [
  makeCard('Элемент 01', 'элемент 01 краткое описание'),
  makeCard('Элемент 02', 'элемент 02 заметка'),
  makeCard('Элемент 03', 'элемент 03 описание'),
];

const form = {
  addEventListener(eventName, callback) {
    listeners.set(`form:${eventName}`, callback);
  },
};

const document = {
  querySelector(selector) {
    const elements = {
      '#filter-form': form,
      '#card-query': query,
      '#status': status,
      '#empty-state': emptyState,
    };
    if (!(selector in elements)) throw new Error(`Unexpected selector: ${selector}`);
    return elements[selector];
  },
  querySelectorAll(selector) {
    assert.equal(selector, '.feed-card');
    return cards;
  },
};

const window = {
  requestAnimationFrame(callback) {
    callback();
  },
};

vm.runInNewContext(script, { document, window });

query.value = '02';
listeners.get('form:submit')({ preventDefault() {} });
assert.deepEqual(cards.map((card) => card.hidden), [true, false, true]);
assert.equal(status.textContent, 'Найдено карточек: 1');
assert.equal(emptyState.hidden, true);

query.value = 'нет совпадений';
listeners.get('form:submit')({ preventDefault() {} });
assert.equal(cards.every((card) => card.hidden), true);
assert.equal(emptyState.hidden, false);
assert.equal(status.textContent, 'Найдено карточек: 0');

query.value = '';
listeners.get('form:reset')();
assert.equal(cards.every((card) => !card.hidden), true);
assert.equal(emptyState.hidden, true);
assert.equal(status.textContent, 'Показаны все карточки: 3');

listeners.get('Элемент 02:click')();
assert.equal(status.textContent, 'Открыт Элемент 02');

process.stdout.write('CARD_FEED_RUNTIME_TEST: PASS\n');
