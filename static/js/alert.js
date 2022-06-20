$(document).ready(function () {
    // Run this code only when the DOM (all elements) are ready

    $('form[name="login"]').on("submit", function (e) {
        // Find all <form>s with the name "login", and bind a "submit" event handler

        // Find the <input /> element with the name "username"
        var username = $(this).find('input[name="username"]');
        var password = $(this).find('input[name="password"]');
        if ($.trim(username.val()) === "") {
            // If its value is empty
            e.preventDefault();    // Stop the form from submitting
            $("#formAlert").slideDown(400);    // Show the Alert
        } else if ($.trim(password.val()) === "") {
            // If its value is empty
            e.preventDefault();    // Stop the form from submitting
            $("#formAlert").slideDown(400);    // Show the Alert
        } else {
            e.preventDefault();    // Not needed, just for demonstration
            $("#formAlert").slideUp(400, function () {    // Hide the Alert (if visible)
                alert("Would be submitting form");    // Not needed, just for demonstration
                username.val("");    // Not needed, just for demonstration
            });
        }
    });

    $(".alert").find(".close").on("click", function (e) {
        // Find all elements with the "alert" class, get all descendant elements with the class "close", and bind a "click" event handler
        e.stopPropagation();    // Don't allow the click to bubble up the DOM
        e.preventDefault();    // Don't let any default functionality occur (in case it's a link)
        $(this).closest(".alert").slideUp(400);    // Hide this specific Alert
    });
});