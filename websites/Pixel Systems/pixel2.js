// pixel.js – optimized for performance with lazy and idle execution and bfcache support

let sliderInterval, sliderInterval1, slideInterval;
let visitorCount = 0; // Use in-memory storage instead of localStorage

function runCounters() {
  const counters = document.querySelectorAll(".counter");

  counters.forEach((counter) => {
    let target = +counter.getAttribute("data-target");

    if (counter.classList.contains("visitor-counter")) {
      // Use in-memory counter instead of localStorage
      visitorCount = visitorCount + 1;
      target = 3105 + visitorCount; // Start from the base number shown in HTML
    }

    const updateCounter = () => {
      const current = +counter.innerText.replace(/,/g, "");
      const increment = target / 200;

      if (current < target) {
        counter.innerText = Math.ceil(current + increment).toLocaleString();
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
  if (!imgElement) {
    console.log("Rental slider image element not found");
    return;
  }

  // Updated image paths to match your HTML structure
  const images = [
    "Pixel Images/new-modern-powerful-gaming-computer-with-beautiful-rgb-lights-different-color-glass-case-table-dark_63762-7255.avif",
    "Pixel Images/12d400b928e32c0902d39d155d10e4c0.webp",
  ];
  let current = 0;

  // Set initial image
  imgElement.src = images[current];

  sliderInterval = setInterval(() => {
    current = (current + 1) % images.length;
    imgElement.src = images[current];
    console.log("Rental slider changed to:", images[current]);
  }, 3000);
}

function initDscSlider() {
  const imgElement1 = document.getElementById("slider-img1");
  if (!imgElement1) {
    console.log("DSC slider image element not found");
    return;
  }

  const images = [
    "Pixel Images/Minimising-Data-Loss.jpg",
    "Pixel Images/Firethreat.jpg",
    "Pixel Images/side-view-male-hacker-with-gloves-laptop_23-2148578161.avif",
  ];
  let current1 = 0;

  // Set initial image
  imgElement1.src = images[current1];

  sliderInterval1 = setInterval(() => {
    current1 = (current1 + 1) % images.length;
    imgElement1.src = images[current1];
    console.log("DSC slider changed to:", images[current1]);
  }, 3000);
}

function observeSliderInit(selector, initFunction) {
  const section = document.querySelector(selector);
  if (!section) {
    console.log("Section not found for selector:", selector);
    return;
  }

  const observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        console.log("Section in view, initializing slider for:", selector);
        initFunction();
        observer.disconnect();
      }
    },
    { threshold: 0.4 }
  );

  observer.observe(section);
}

// Main slider functionality for the refurbished laptops section
let currentSlide = 0;

function initMainSlider() {
  const slides = document.querySelectorAll(".slide");
  if (slides.length === 0) {
    console.log("No slides found for main slider");
    return;
  }

  function showSlide(index) {
    slides.forEach((slide, i) => {
      slide.classList.toggle("active", i === index);
    });
  }

  function changeSlide(direction) {
    currentSlide = (currentSlide + direction + slides.length) % slides.length;
    showSlide(currentSlide);
    console.log("Main slider changed to slide:", currentSlide);
  }

  // Make changeSlide function globally available for onclick handlers
  window.changeSlide = changeSlide;

  function startSlideAutoPlay() {
    if (!slideInterval) {
      slideInterval = setInterval(() => changeSlide(1), 5000);
    }
  }

  // Initialize the slider
  showSlide(currentSlide);
  startSlideAutoPlay();
}

function observeMainSlider() {
  const slider = document.querySelector(".slider");
  if (!slider) {
    console.log("Main slider element not found");
    return;
  }

  const observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        console.log("Main slider in view, initializing");
        initMainSlider();
        observer.disconnect();
      }
    },
    { threshold: 0.4 }
  );

  observer.observe(slider);
}

function cleanupIntervals() {
  if (sliderInterval) {
    clearInterval(sliderInterval);
    sliderInterval = null;
  }
  if (sliderInterval1) {
    clearInterval(sliderInterval1);
    sliderInterval1 = null;
  }
  if (slideInterval) {
    clearInterval(slideInterval);
    slideInterval = null;
  }
  console.log("Intervals cleaned up");
}

// Image loading error handler
function handleImageError(img, fallbackSrc) {
  img.onerror = () => {
    console.log("Image failed to load:", img.src);
    if (fallbackSrc && img.src !== fallbackSrc) {
      img.src = fallbackSrc;
    }
  };
}

// Initialize everything when DOM is loaded
function initializeApp() {
  console.log("Initializing Pixel Systems app");

  // Initialize counters when about section comes into view
  initCountersOnView();

  // Initialize rental slider when rental section comes into view
  observeSliderInit("#rental", initRentalSlider);

  // Initialize DSC slider when data security section comes into view
  observeSliderInit("#data-security", initDscSlider);

  // Initialize main slider when refurbished section comes into view
  observeMainSlider();

  // Add error handling for all images
  document.querySelectorAll("img").forEach((img) => {
    handleImageError(img);
  });
}

// Wait for DOM to be ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    requestIdleCallback(() => initializeApp());
  });
} else {
  requestIdleCallback(() => initializeApp());
}

// Back/forward cache-safe cleanup
window.addEventListener("pagehide", cleanupIntervals);
window.addEventListener("pageshow", (event) => {
  if (event.persisted) {
    console.log("Page restored from cache, reinitializing");
    // Restore observers since the page was cached
    requestIdleCallback(() => initializeApp());
  }
});

// Debug function to check if images exist
function checkImages() {
  const rentalImg = document.getElementById("slider-img");
  const dscImg = document.getElementById("slider-img1");

  console.log("Rental image element:", rentalImg);
  console.log("DSC image element:", dscImg);

  if (rentalImg) console.log("Rental image current src:", rentalImg.src);
  if (dscImg) console.log("DSC image current src:", dscImg.src);
}

// Make debug function available globally
window.checkImages = checkImages;
