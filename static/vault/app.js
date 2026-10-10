function csrfToken() {
  const token = document.querySelector('meta[name="csrf-token"]');
  return token ? token.content : '';
}

document.querySelectorAll('.secure-action').forEach((button) => {
  button.addEventListener('click', async () => {
    const response = await fetch(button.dataset.url, { method: 'POST', headers: { 'X-CSRFToken': csrfToken() } });
    const data = await response.json();
    document.querySelector(button.dataset.target).textContent = data.password;
  });
});

document.querySelectorAll('.secure-copy').forEach((button) => {
  button.addEventListener('click', async () => {
    const response = await fetch(button.dataset.url, { method: 'POST', headers: { 'X-CSRFToken': csrfToken() } });
    const data = await response.json();
    await navigator.clipboard.writeText(data.password);
    button.textContent = 'Copied';
  });
});

document.querySelectorAll('[data-copy-field]').forEach((button) => {
  button.addEventListener('click', async () => {
    const input = document.querySelector(button.dataset.copyField);
    await navigator.clipboard.writeText(input.value);
    button.textContent = 'Copied';
  });
});

const generateButton = document.querySelector('#generate-password');
const passwordInput = document.querySelector('#id_password');
const strengthBar = document.querySelector('#strength-bar');
const strengthSummary = document.querySelector('#strength-summary');
const strengthHints = document.querySelectorAll('#strength-hints li');
const rules = {
  length: (value) => value.length >= 12,
  lowercase: (value) => /[a-z]/.test(value),
  uppercase: (value) => /[A-Z]/.test(value),
  number: (value) => /\d/.test(value),
  special: (value) => /[!@#$%^&*()\-_=\+\[\]{}]/.test(value),
};

function updateStrength() {
  if (!passwordInput || !strengthBar || !strengthSummary) return;
  const value = passwordInput.value;
  let passed = 0;
  strengthHints.forEach((hint) => {
    const ok = rules[hint.dataset.rule](value);
    hint.classList.toggle('passed', ok);
    passed += ok ? 1 : 0;
  });
  const percent = (passed / Object.keys(rules).length) * 100;
  strengthBar.style.width = `${percent}%`;
  strengthBar.className = `progress-bar ${passed >= 5 ? 'bg-success' : passed >= 3 ? 'bg-warning' : 'bg-danger'}`;
  strengthSummary.textContent = !value ? 'Enter a password to check its strength.' : passed === 5 ? 'Strong password. Ready to encrypt and save.' : 'Improve this password before saving.';
}

if (generateButton && passwordInput) {
  generateButton.addEventListener('click', async () => {
    const response = await fetch('/passwords/generate/');
    const data = await response.json();
    passwordInput.value = data.password;
    passwordInput.type = 'text';
    updateStrength();
  });
  passwordInput.addEventListener('input', updateStrength);
  updateStrength();
}
