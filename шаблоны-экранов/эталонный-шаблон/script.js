const screen = document.querySelector('.screen');
const action = document.querySelector('#primary-action');
const status = document.querySelector('#status');
const error = document.querySelector('#error');

function setState(state) {
  screen.dataset.state = state;
  if (state === 'action-complete') {
    error.hidden = true;
    status.textContent = 'Основное действие выполнено с fixture-данными';
    return;
  }
  if (state === 'recovery-required') {
    error.hidden = false;
    status.textContent = 'Требуется действие восстановления';
    return;
  }
  error.hidden = true;
  status.textContent = 'Начальное состояние';
}

function completeAction() {
  setState('action-complete');
}

action.addEventListener('click', completeAction);

screen.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    setState('recovery-required');
  }
});

const requestedState = new URLSearchParams(window.location.search).get('state');
if (requestedState === 'action-complete' || requestedState === 'recovery-required') {
  setState(requestedState);
} else {
  setState('initial');
}
