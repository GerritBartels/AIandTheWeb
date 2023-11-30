/**
 * Represents a star in the night sky.
 */
class Star {
    /**
     * Creates a star with initial properties.
     * @param {number} left - The initial left position.
     * @param {number} top - The initial top position.
     */
    constructor(left, top) {
      this.element = document.createElement('div');
      this.element.className = 'star';
      this.left = left;
      this.top = top;
      this.vx = (Math.random() - 0.5) * 0.2;
      this.vy = (Math.random() - 0.5) * 0.2;
      this.updateStyle();
      document.body.appendChild(this.element);
    }
  
    /**
     * Updates the CSS style of the star based on its position.
     */
    updateStyle() {
      this.element.style.left = `${this.left}px`;
      this.element.style.top = `${this.top}px`;
    }
  }
  
  /**
   * Represents a collection of stars in the night sky.
   */
  class StarField {
    /**
     * Creates a StarField with a specified star density.
     * @param {number} starDensity - The density of stars.
     */
    constructor(starDensity) {
      this.stars = [];
      this.starDensity = starDensity;
      this.generateStars();
      this.lastMousePosition = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    }
  
    /**
     * Generates stars based on the star density.
     */
    generateStars() {
      const starCount = Math.floor(window.innerWidth * window.innerHeight / this.starDensity);
      for (let i = 0; i < starCount; i++) {
        const star = new Star(Math.random() * window.innerWidth, Math.random() * window.innerHeight);
        this.stars.push(star);
      }
    }
  
    /**
     * Moves stars based on mouse movement.
     * @param {MouseEvent} e - The mouse event.
     */
    moveStarsOnMouseMove(e) {
        const dx = e.clientX - this.lastMousePosition.x;
        const dy = e.clientY - this.lastMousePosition.y;
        this.stars.forEach(star => {
            star.left -= dx * 0.01;
            star.top -= dy * 0.01;
        });
        this.lastMousePosition = { x: e.clientX, y: e.clientY };
    }
  
    /**
     * Handles window resize event.
     */
    handleResize() {
      const newWidth = window.innerWidth;
      const newHeight = window.innerHeight;
      const newStarCount = Math.floor((newWidth * newHeight - this.prevWidth * this.prevHeight) / this.starDensity);
  
      for (let i = 0; i < newStarCount; i++) {
        const left = newWidth > this.prevWidth ? Math.random() * (newWidth - this.prevWidth) + this.prevWidth : Math.random() * newWidth;
        const top = newHeight > this.prevHeight ? Math.random() * (newHeight - this.prevHeight) + this.prevHeight : Math.random() * newHeight;
        const star = new Star(left, top);
        this.stars.push(star);
      }
  
      this.prevWidth = newWidth;
      this.prevHeight = newHeight;
    }
  
    /**
     * Animates the stars and submits the form when there are no stars left.
     * @param {HTMLFormElement} form - The form to be submitted.
     */
    animateStarsAndSubmitForm(form) {
      const centerX = window.innerWidth / 2;
      const centerY = window.innerHeight / 2;
  
      this.stars.forEach(star => {
        const dx = star.left - centerX;
        const dy = star.top - centerY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        star.vx = dx / distance * 14;
        star.vy = dy / distance * 14;
      });
  
      const remainingStars = this.stars.filter(star => {
        star.left += star.vx;
        star.top += star.vy;
        star.updateStyle();
  
        const targetDistance = Math.sqrt((star.left - centerX) ** 2 + (star.top - centerY) ** 2);
  
        if (targetDistance > Math.max(window.innerWidth, window.innerHeight)) {
          star.element.remove();
          return false;
        }
  
        return true;
      });
  
      this.stars = remainingStars;
  
      if (this.stars.length === 0) {
        form.submit();
      } else {
        requestAnimationFrame(() => this.animateStarsAndSubmitForm(form));
      }
    }
  
    /**
     * Animates the stars within the window.
     */
    animateStars() {
      this.stars.forEach(star => {
        star.left += star.vx;
        star.top += star.vy;
        star.updateStyle();
  
        if (star.left < -100 || star.left > window.innerWidth + 100 || star.top < -100 || star.top > window.innerHeight + 100) {
          star.element.remove();
        }
      });
  
      requestAnimationFrame(() => this.animateStars());
    }
  
    /**
     * Starts the animation.
     */
    startAnimation() {
      this.animateStars();
    }
  }
  
  // Initialize the star field with a star density
  const starField = new StarField(20000);
  
  // Set up event listeners
  window.addEventListener('mousemove', (e) => starField.moveStarsOnMouseMove(e));
  window.addEventListener('resize', () => starField.handleResize());
  
  // Get the form and set up submit event listener
  const form = document.getElementById('searchForm');
  if (!form) {
    console.error('Form not found.');
  } else {
    form.querySelector('button[type="submit"]').addEventListener('click', (e) => {
      e.preventDefault();
      starField.animateStarsAndSubmitForm(form);
    });
  }
  
  // Start the animation
  starField.startAnimation();
  