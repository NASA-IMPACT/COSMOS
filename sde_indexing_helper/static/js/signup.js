document.addEventListener("DOMContentLoaded", function () {
  const password1 = document.getElementById("id_password1");
  const password2 = document.getElementById("id_password2");
  const errorContainer = document.querySelector(".manual-errors"); // Assuming this is the container for manual errors

  function validatePasswords() {
    if (password2.value.length > 0 && password1.value !== password2.value) {
      password2.classList.add("is-invalid");
      errorContainer.style.display = "block"; // Display the error container
    } else {
      password2.classList.remove("is-invalid");
      errorContainer.style.display = "none"; // Hide the error container
    }
  }

  password1.addEventListener("input", validatePasswords);
  password2.addEventListener("input", validatePasswords);
});
