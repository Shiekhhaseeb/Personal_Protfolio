/** Portfolio client scripts */

document.addEventListener('DOMContentLoaded', () => {
  // Navbar scroll effect
  const header = document.getElementById('site-header');
  const onScroll = () => {
    if (!header) return;
    header.classList.toggle('nav-scrolled', window.scrollY > 24);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Mobile nav toggle
  const menuBtn = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');

  if (menuBtn && mobileMenu) {
    menuBtn.addEventListener('click', () => {
      mobileMenu.classList.toggle('hidden');
    });

    mobileMenu.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => mobileMenu.classList.add('hidden'));
    });
  }

  // Scroll-triggered section fade-in
  const sections = document.querySelectorAll('.section-fade');
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    },
    { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
  );

  sections.forEach((section) => observer.observe(section));

  // Active nav highlight on scroll
  const navLinks = document.querySelectorAll('.nav-link');
  const sectionIds = ['about', 'skills', 'projects', 'experience', 'contact'];

  window.addEventListener('scroll', () => {
    let current = '';
    sectionIds.forEach((id) => {
      const el = document.getElementById(id);
      if (el && window.scrollY >= el.offsetTop - 120) {
        current = id;
      }
    });

    navLinks.forEach((link) => {
      link.classList.remove('text-accent');
      if (link.getAttribute('href') === `#${current}`) {
        link.classList.add('text-accent');
      }
    });
  });
});
