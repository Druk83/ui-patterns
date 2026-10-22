const landing = document.querySelector('.landing');
const action = document.querySelector('#primary-action');
const status = document.querySelector('#status');
const error = document.querySelector('#error');
const variant = document.querySelector('#variant');
const formVariant = document.querySelector('#form-variant');
const fixtureField = document.querySelector('#fixture-field');

function setState(state) {
  landing.dataset.state = state;
  error.hidden = state !== 'recovery-required';
  if (state === 'action-complete') {
    status.textContent = 'Основное действие выполнено с fixture-данными';
  } else if (state === 'recovery-required') {
    status.textContent = 'Требуется действие восстановления';
  } else {
    status.textContent = 'Начальное состояние';
  }
}

function setVariant(value) {
  const withForm = value === 'with-form';
  variant.value = withForm ? 'with-form' : 'without-form';
  formVariant.hidden = !withForm;
  fixtureField.required = withForm;
  if (!withForm) fixtureField.value = '';
  setState('initial');
}

action.addEventListener('click', () => {
  if (!formVariant.hidden && !fixtureField.reportValidity()) {
    setState('recovery-required');
    fixtureField.focus();
    return;
  }
  setState('action-complete');
});

variant.addEventListener('change', () => setVariant(variant.value));
landing.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') setState('recovery-required');
});

const query = new URLSearchParams(window.location.search);
setVariant(query.get('variant') === 'form' ? 'with-form' : 'without-form');
const requestedState = query.get('state');
if (requestedState === 'action-complete' || requestedState === 'recovery-required') {
  setState(requestedState);
}
