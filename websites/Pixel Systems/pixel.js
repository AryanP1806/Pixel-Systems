document.addEventListener("DOMContentLoaded", () => {
  const counters = document.querySelectorAll(".counter");

  counters.forEach((counter) => {
    let target = +counter.getAttribute("data-target");

    // Handle visitor count separately
    if (counter.classList.contains("visitor-counter")) {
      // Get current visitor count from localStorage (simulate server-side)
      let visitors = localStorage.getItem("visitorCount");
      if (!visitors) visitors = 0;

      visitors = parseInt(visitors) + 1;
      localStorage.setItem("visitorCount", visitors);
      target = visitors;
    }

    const updateCounter = () => {
      const current = +counter.innerText;
      const increment = target / 200;

      if (current < target) {
        counter.innerText = Math.ceil(current + increment);
        requestAnimationFrame(updateCounter); // smoother than setTimeout
      } else {
        counter.innerText = target.toLocaleString();
      }
    };

    updateCounter();
  });

  const images = [
    "Pixel Images/uWjEogFLUTBc8mSvagdiuP.jpg",
    "Pixel Images/1593380500279.jpeg",
  ];

  let current = 0;
  const imgElement = document.getElementById("slider-img");

  setInterval(() => {
    current = (current + 1) % images.length;
    imgElement.src = images[current];
  }, 3000); // change every 3 seconds

  const image = [
    "Pixel Images/Firethreat.jpg",
    "Pixel Images/Minimising-Data-Loss.jpg",
  ];

  let current1 = 0;
  const imgElement1 = document.getElementById("slider-img1");

  setInterval(() => {
    current1 = (current1 + 1) % image.length;
    imgElement1.src = image[current1];
  }, 3000);
});
