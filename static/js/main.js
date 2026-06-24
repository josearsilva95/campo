/* Controle de Viagem — JS principal */

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(() => {});
}

// Auto-dismiss flash messages
document.addEventListener('DOMContentLoaded', () => {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });

  // Checklist: toggle visual ao clicar
  document.querySelectorAll('.checklist-item').forEach(item => {
    const cb = item.querySelector('input[type="checkbox"]');
    if (cb) {
      cb.addEventListener('change', () => {
        item.classList.toggle('checked', cb.checked);
      });
    }
  });

  // Category selector: seleciona visualmente ao clicar
  document.querySelectorAll('.cat-option').forEach(opt => {
    const radio = opt.querySelector('input[type="radio"]');
    if (radio) {
      radio.addEventListener('change', () => {
        document.querySelectorAll('.cat-option').forEach(o => o.classList.remove('selected'));
        if (radio.checked) opt.classList.add('selected');
      });
      if (radio.checked) opt.classList.add('selected');
    }
  });

  // Confirmar ação em formulários com data-confirm
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });
});

// Formatação de valor monetário
function formatarMoeda(input) {
  let val = input.value.replace(/\D/g, '');
  val = (parseInt(val || '0', 10) / 100).toFixed(2);
  input.value = val;
}
