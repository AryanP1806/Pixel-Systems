// pixel.js — optimized for performance with lazy and idle execution and bfcache support

let sliderInterval, sliderInterval1, slideInterval;

function runCounters() {
  const counters = document.querySelectorAll(".counter");

  counters.forEach((counter) => {
    let target = +counter.getAttribute("data-target");

    if (counter.classList.contains("visitor-counter")) {
      let visitors = localStorage.getItem("visitorCount") || 0;
      visitors = parseInt(visitors) + 1;
      localStorage.setItem("visitorCount", visitors);
      target = visitors;
    }

    const updateCounter = () => {
      const current = +counter.innerText.replace(/,/g, "");
      const increment = target / 200;

      if (current < target) {
        counter.innerText = Math.ceil(current + increment);
        requestAnimationFrame(updateCounter);
      } else {
        counter.innerText = target.toLocaleString();
      }
    };

    updateCounter();
  });
}

function initCountersOnView() {
  const aboutSection = document.querySelector(".about");
  if (!aboutSection) return;

  const observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        runCounters();
        observer.disconnect();
      }
    },
    { threshold: 0.5 }
  );

  observer.observe(aboutSection);
}

function initRentalSlider() {
  const imgElement = document.getElementById("slider-img");
  if (!imgElement) return;
  const images = [
    "Pixel Images/12d400b928e32c0902d39d155d10e4c0.webp",
    "Pixel Images/new-modern-powerful-gaming-computer-with-beautiful-rgb-lights-different-color-glass-case-table-dark_63762-7255.avif",
    // "Pixel Images/425073.e0863a509bc786e573ee300d811bbb63.webp",
  ];
  let current = 0;

  sliderInterval = setInterval(() => {
    current = (current + 1) % images.length;
    imgElement.src = images[current];
  }, 3000);
}

function initDscSlider() {
  const imgElement1 = document.getElementById("slider-img1");
  if (!imgElement1) return;
  const image = [
    "Pixel Images/Firethreat.jpg",
    "Pixel Images/Minimising-Data-Loss.jpg",
    "Pixel Images/side-view-male-hacker-with-gloves-laptop_23-2148578161.avif",
  ];
  let current1 = 0;

  sliderInterval1 = setInterval(() => {
    current1 = (current1 + 1) % image.length;
    imgElement1.src = image[current1];
  }, 3000);
}

function observeSliderInit(selector, initFunction) {
  const section = document.querySelector(selector);
  if (!section) return;

  const observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        initFunction();
        observer.disconnect();
      }
    },
    { threshold: 0.4 }
  );

  observer.observe(section);
}

let currentSlide = 0;
const slides = document.querySelectorAll(".slide");

function showSlide(index) {
  slides.forEach((slide, i) => {
    slide.classList.toggle("active", i === index);
  });
}

function changeSlide(direction) {
  currentSlide = (currentSlide + direction + slides.length) % slides.length;
  showSlide(currentSlide);
}

function startSlideAutoPlay() {
  if (!slideInterval) {
    slideInterval = setInterval(() => changeSlide(1), 5000);
  }
}

function observeMainSlider() {
  const slider = document.querySelector(".slider");
  if (!slider) return;

  const observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        startSlideAutoPlay();
        observer.disconnect();
      }
    },
    { threshold: 0.4 }
  );

  observer.observe(slider);
}

function cleanupIntervals() {
  if (sliderInterval) clearInterval(sliderInterval);
  if (sliderInterval1) clearInterval(sliderInterval1);
  if (slideInterval) clearInterval(slideInterval);
  sliderInterval = null;
  sliderInterval1 = null;
  slideInterval = null;
}

window.addEventListener("DOMContentLoaded", () => {
  requestIdleCallback(() => {
    initCountersOnView();
    observeSliderInit(".rc", initRentalSlider);
    observeSliderInit(".dsc", initDscSlider);
    observeMainSlider();
  });
});

// Back/forward cache-safe cleanup
window.addEventListener("pagehide", cleanupIntervals);
window.addEventListener("pageshow", (event) => {
  if (event.persisted) {
    // Restore observers since the page was cached
    requestIdleCallback(() => {
      initCountersOnView();
      observeSliderInit(".rc", initRentalSlider);
      observeSliderInit(".dsc", initDscSlider);
      observeMainSlider();
    });
  }
});
