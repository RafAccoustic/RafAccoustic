
// script.js
let currentIndex = 0;
const slides = document.querySelectorAll('.slide');
const totalSlides = slides.length;

// Function to show the current slide
function showSlide(index) {
    slides.forEach((slide, i) => {
        slide.classList.remove('active', 'prev', 'next'); // Remove all classes
        if (i === index) {
            slide.classList.add('active');  // Show the active slide in the center
        } else if (i === (index - 1 + totalSlides) % totalSlides) {
            slide.classList.add('prev');   // Show the previous slide off-screen to the left
        } else if (i === (index + 1) % totalSlides) {
            slide.classList.add('next');   // Show the next slide off-screen to the right
        }
    });
}

// Function to move slides based on the step
function moveSlide(step) {
    currentIndex += step;
    if (currentIndex >= totalSlides) {
        currentIndex = 0;
    }
    if (currentIndex < 0) {
        currentIndex = totalSlides - 1;
    }
    showSlide(currentIndex);
}

// Auto slide every 3 seconds
function autoSlide() {
    setInterval(() => {
        moveSlide(1); // Move to the next slide
    }, 5000); // 3000 milliseconds = 3 seconds
}

// Initial display and start auto-slide
showSlide(currentIndex);
autoSlide();




// Small Slider
let currentSlide = 0;

function showSlide1(slideIndex) {
    const slides1 = document.querySelectorAll('.slide1');
    const totalSlides = slides1.length;

    // Remove active and previous classes from all slides
    slides1.forEach(slide => {
        slide.classList.remove('actives');
        slide.classList.remove('prevs');
    });

    // Calculate the previous slide index
    const prevSlideIndex = (slideIndex - 1 + totalSlides) % totalSlides;

    // Add 'active' class to current slide and 'prev' class to the previous slide
    slides1[slideIndex].classList.add('actives');
    slides1[prevSlideIndex].classList.add('prevs');
    
    // Update currentSlide
    currentSlide = slideIndex;
}

function nextSlide() {
    const slides1 = document.querySelectorAll('.slide1');
    const totalSlides = slides1.length;
    showSlide1((currentSlide + 1) % totalSlides);
}

// Automatically move to the next slide every 5 seconds
setInterval(nextSlide, 4000);

// Initialize the slider by showing the first slide
showSlide1(currentSlide);


let currentIndexs = 0;
let startX = 0;
let endX = 0;

function moveSlides(n) {
  const slider = document.querySelector('.sliders');
  const totalSlides = document.querySelectorAll('.slidess').length;
  const slidesToShow = 8; // Number of slides visible at once

  currentIndexs += n;

  // Prevent moving beyond available slides
  if (currentIndexs < 0) {
    currentIndexs = totalSlides - slidesToShow;
  } else if (currentIndexs >= totalSlides - slidesToShow + 1) {
    currentIndexs = 0;
  }

  const slideWidth = document.querySelector('.slidess').offsetWidth;
  slider.style.transform = `translateX(${-slideWidth * currentIndexs}px)`;
}

// Add mouse scroll functionality
const sliderContainer = document.querySelector('.slider-containers'); // Make sure you wrap your slider in a container with this class

sliderContainer.addEventListener('wheel', (event) => {
  if (event.deltaY > 0) {
    moveSlides(1); // Scroll down to move to the right
  } else {
    moveSlides(-1); // Scroll up to move to the left
  }

  event.preventDefault(); // Prevent default scroll behavior
  
});
// Add touch functionality for smartphones/small screens
sliderContainer.addEventListener('touchstart', (event) => {
    startX = event.touches[0].clientX; // Get the starting touch position
  });
  
  sliderContainer.addEventListener('touchmove', (event) => {
    endX = event.touches[0].clientX; // Continuously update the touch position as the user moves
  });
  
  sliderContainer.addEventListener('touchend', () => {
    const threshold = 50; // Minimum distance in pixels for a valid swipe
  
    if (startX - endX > threshold) {
      // Swiped left, move to the next slide
      moveSlides(1);
    } else if (endX - startX > threshold) {
      // Swiped right, move to the previous slide
      moveSlides(-1);
    }
});