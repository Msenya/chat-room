document.addEventListener("DOMContentLoaded", function() {
    // Email validation
    const emailField = document.getElementById("email");
    const emailError = document.getElementById("emailError");

    const validateEmail = () => {
        const email = emailField.value.trim();
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailPattern.test(email)) {
            emailError.textContent = "Please enter a valid email address.";
            emailError.className = "emailError";
            emailField.classList.add("invalid");
            return false;
        } else {
            emailError.textContent = "";
            emailField.classList.remove("invalid");
            return true;
        }
    };

    emailField.addEventListener("input", validateEmail);

    // Initialize phone number input with intlTelInput
    var phoneInputField = document.querySelector("#phoneNumber");  
    var phoneInput = window.intlTelInput(phoneInputField, {
        initialCountry: "auto",
        geoIpLookup: function(callback) {
            fetch('https://ipinfo.io/json')
                .then(response => response.json())
                .then(data => callback(data.country))
                .catch(() => callback('us'));   // Defaults to US if geolocation fails
        },
        utilsScript: "https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.13/js/utils.js"
    });

    // Handle form submission
    const form = document.getElementById("registerForm");
    form.addEventListener("submit", function(event) {
        const phoneNumber = phoneInput.getNumber();   // Get full international phone number

        // Validate phone number
        if (!phoneInput.isValidNumber()) {
            event.preventDefault();   // Prevent form submission
            alert("Please enter a valid phone number.");
            return false;
        }

        // Get the cleaned phone number (E.164 format without plus sign)
        const cleanedPhoneNumber = phoneNumber.replace('+', '');
        var input = document.createElement("input");
        input.type = "hidden";
        input.name = "cleaned_phone_number";
        input.value = cleanedPhoneNumber;
        form.appendChild(input);
    });

    // Format the phone number input on blur
    phoneInputField.addEventListener('blur', function() {
        if (phoneInput.isValidNumber()) {
            phoneInputField.value = phoneInput.getNumber(intlTelInputUtils.numberFormat.INTERNATIONAL);
        }
    });

    // Toggle password visibility
    const togglePassword = document.getElementById("togglePassword");  
    const toggleConfirmPassword = document.getElementById("toggleConfirmPassword");  
    const passwordField = document.getElementById("password");  
    const confirmPasswordField = document.getElementById("confirmPassword");  

    togglePassword.addEventListener("click", function(){
        const type = passwordField.type === "password" ? "text" : "password";
        passwordField.type = type;
        togglePassword.textContent = type === "password" ? "Show" : "Hide";
    });

    toggleConfirmPassword.addEventListener("click", function(){
        const type = confirmPasswordField.type === "password" ? "text" : "password";
        confirmPasswordField.type = type;
        toggleConfirmPassword.textContent = type === "password" ? "Show" : "Hide";
    });

    // Password strength check
    const passwordStrength = document.getElementById("passwordStrength");

    const checkPasswordStrength = () => {
        const value = passwordField.value;
        let strength = "Weak";
        passwordStrength.className = "password-strength weak"; // Default to weak

        if (value.length > 12 && /[A-Z]/.test(value) && /[a-z]/.test(value) && /[0-9]/.test(value) && /[!@#\$%\^&\*]/.test(value)){
            strength = "Strong";
            passwordStrength.className = "password-strength strong";
        } else if (value.length >= 8 && value.length <= 11 && /[A-Z]/.test(value) && /[a-z]/.test(value) && /[0-9]/.test(value)) {
            strength = "Medium";
            passwordStrength.className = "password-strength medium";
        }

        passwordStrength.textContent = `Password strength: ${strength}`;
    };

    // Password match check
    const matchMessage = document.getElementById("matchMessage");

    const checkPasswordMatch = () => {
        if (passwordField.value !== confirmPasswordField.value){
            matchMessage.textContent = "Passwords do not match.";
            matchMessage.className = "matchMessage"; // Ensure the error message is styled
            return false;
        } else {
            matchMessage.textContent = "";
            return true;
        }
    };

    passwordField.addEventListener("input", checkPasswordStrength);
    confirmPasswordField.addEventListener("input", checkPasswordMatch);

    // Enable/Disable the register button based on the "I agree" checkbox
    const termsCheckbox = document.getElementById("termsCheckbox");
    const registerButton = document.getElementById("registerButton");

    const validateForm = () => {
        if (form.checkValidity() && termsCheckbox.checked && validateEmail() && phoneInput.isValidNumber() && checkPasswordMatch()) {
            registerButton.disabled = false;
        } else {
            registerButton.disabled = true;
        }
    };

    form.addEventListener("input", validateForm);
    termsCheckbox.addEventListener("change", validateForm);

    validateForm(); // Initial validation check

    // AJAX form submission
    $('#registerForm').on('submit', function(event) {
        event.preventDefault();  // Prevent the default form submission

        $.ajax({
            type: 'POST',
            url: '/register',
            data: $(this).serialize(),
            dataType: 'json',
            success: function(response) {
                if (response.status === 'success') {
                    alert(response.message);
                    window.location.href = '/login';  // Redirect to login page on success
                } else {
                    alert(response.message);
                    location.reload();  // Reload the registration page on error
                }
            },
            error: function() {
                alert('An error occurred while processing the request.');
                location.reload();  // Reload the registration page on error
            }
        });
    });
});
