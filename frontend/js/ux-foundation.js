(function () {
  const UX = {
    toastTimer: null,
    showStatus(message, tone) {
      let region = document.getElementById('ux-live-region');
      if (!region) {
        region = document.createElement('div');
        region.id = 'ux-live-region';
        region.className = 'ux-live-region';
        region.setAttribute('role', 'status');
        region.setAttribute('aria-live', 'polite');
        region.style.display = 'none';
        document.body.appendChild(region);
      }

      region.textContent = message;
      region.dataset.tone = tone || 'info';
      region.style.display = 'block';
      clearTimeout(this.toastTimer);
      this.toastTimer = setTimeout(() => {
        region.style.display = 'none';
      }, 2800);
    },
  };

  function injectSkipLink() {
    if (document.querySelector('.ux-skip-link')) {
      return;
    }
    const main = document.querySelector('main') || document.querySelector('#main-content') || document.body;
    if (main && !main.id) {
      main.id = 'main-content';
    }
    const skip = document.createElement('a');
    skip.href = '#' + (main.id || 'main-content');
    skip.className = 'ux-skip-link';
    skip.textContent = 'Skip to main content';
    document.body.prepend(skip);
  }

  function wireForms() {
    document.querySelectorAll('form').forEach((form) => {
      form.addEventListener('submit', function () {
        const invalid = form.querySelector(':invalid');
        if (invalid) {
          UX.showStatus('Please complete required fields.', 'error');
          invalid.focus();
          return;
        }

        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn && !submitBtn.dataset.uxLoadingAttached && !submitBtn.hasAttribute('data-custom-loading')) {
          submitBtn.dataset.uxLoadingAttached = '1';
          submitBtn.dataset.uxOriginalText = submitBtn.textContent || 'Submit';
          submitBtn.disabled = true;
          submitBtn.textContent = 'Please wait...';
          setTimeout(() => {
            submitBtn.disabled = false;
            submitBtn.textContent = submitBtn.dataset.uxOriginalText;
          }, 8000);
        }
      });
    });
  }

  function wireNavToggle() {
    const nav = document.querySelector('.nav-links');
    const topbarInner = document.querySelector('.topbar-inner');
    if (!nav || !topbarInner || document.querySelector('.ux-nav-toggle')) {
      return;
    }

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'ux-nav-toggle';
    btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-label', 'Toggle navigation');
    btn.textContent = 'Menu';
    topbarInner.insertBefore(btn, nav);

    nav.classList.add('ux-mobile-hidden');

    btn.addEventListener('click', function () {
      const hidden = nav.classList.toggle('ux-mobile-hidden');
      btn.setAttribute('aria-expanded', String(!hidden));
    });
  }

  function wireKeyboardEscape() {
    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') {
        return;
      }
      document.querySelectorAll('.modal').forEach((modal) => {
        modal.style.display = 'none';
      });
    });
  }

  function wireAriaLabels() {
    document.querySelectorAll('input, textarea, select').forEach((el) => {
      if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')) {
        return;
      }
      const id = el.id;
      if (id) {
        const label = document.querySelector(`label[for="${id}"]`);
        if (label && label.textContent.trim()) {
          el.setAttribute('aria-label', label.textContent.trim());
          return;
        }
      }
      const ph = el.getAttribute('placeholder');
      if (ph) {
        el.setAttribute('aria-label', ph);
      }
    });
  }

  function wireFeedbackDialog() {
    if (document.getElementById('ux-feedback-fab')) {
      return;
    }

    const fab = document.createElement('button');
    fab.type = 'button';
    fab.id = 'ux-feedback-fab';
    fab.className = 'ux-feedback-fab';
    fab.textContent = 'Share Feedback';

    const dialog = document.createElement('div');
    dialog.className = 'ux-feedback-dialog';
    dialog.id = 'ux-feedback-dialog';
    dialog.innerHTML = [
      '<div class="ux-feedback-card" role="dialog" aria-modal="true" aria-label="Feedback">',
      '<h3>Help Us Improve</h3>',
      '<p>Tell us what felt confusing or what should be improved.</p>',
      '<textarea id="ux-feedback-text" placeholder="Your feedback..."></textarea>',
      '<div class="ux-feedback-actions">',
      '<button type="button" id="ux-feedback-cancel">Cancel</button>',
      '<button type="button" id="ux-feedback-send">Send</button>',
      '</div>',
      '</div>'
    ].join('');

    document.body.appendChild(fab);
    document.body.appendChild(dialog);

    fab.addEventListener('click', () => {
      dialog.style.display = 'flex';
      const text = document.getElementById('ux-feedback-text');
      if (text) {
        text.focus();
      }
    });

    dialog.addEventListener('click', (event) => {
      if (event.target === dialog) {
        dialog.style.display = 'none';
      }
    });

    document.getElementById('ux-feedback-cancel')?.addEventListener('click', () => {
      dialog.style.display = 'none';
    });

    document.getElementById('ux-feedback-send')?.addEventListener('click', () => {
      const text = document.getElementById('ux-feedback-text');
      const value = (text?.value || '').trim();
      if (!value) {
        UX.showStatus('Please write feedback before sending.', 'error');
        return;
      }
      const key = 'skillsprint_feedback_' + Date.now();
      localStorage.setItem(key, value);
      dialog.style.display = 'none';
      if (text) {
        text.value = '';
      }
      UX.showStatus('Thanks for your feedback.');
    });
  }

  function init() {
    injectSkipLink();
    wireAriaLabels();
    wireForms();
    wireNavToggle();
    wireKeyboardEscape();
    wireFeedbackDialog();
    window.SkillSprintUX = UX;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
