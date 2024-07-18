$(document).ready(function () {
    $('#Logout').click(function () {
        logout();
    });
    let menu = $('#menu-bar');
    let navbar = $('.navbar');

    menu.click(function () {
        menu.toggleClass('fa-times');
        navbar.toggleClass('active');
    });

    $(window).scroll(function () {
        menu.removeClass('fa-times');
        navbar.removeClass('active');
    });
    animateNumbers();
    numCounter('.counter-up1');
    numCounter('.counter-up2');
    dropdown();
    DropMenu()
    

});

let spinner = function () {
    setTimeout(function () {
        if ($('#spinner').length > 0) {
            $('#spinner').removeClass('show');
        }
    }, 1);
};
spinner();

// Back to top button
$(window).scroll(function () {
    if ($(this).scrollTop() > 300) {
        $('.back-to-top').fadeIn('slow');
    } else {
        $('.back-to-top').fadeOut('slow');
    }
});
$('.back-to-top').click(function () {
    $('html, body').animate({ scrollTop: 0 }, 1500, 'easeInOutExpo');
    return false;
});

// Initiate the wowjs animation library





function animateNumbers() {
    let valueDisplays = $(".num");
    let interval = 4000;

    valueDisplays.each(function (index, valueDisplay) {
        let startValue = 0;
        let endValue = parseInt($(valueDisplay).data("val"));
        let duration = Math.floor(interval / endValue);
        let counter = setInterval(function () {
            startValue += 1;
            $(valueDisplay).text(startValue);
            if (startValue === endValue) {
                clearInterval(counter);
                // Call counterUp after the numbers are rendered
                $(valueDisplay).counterUp({
                    delay: 10,
                    time: 2000
                });
            }
        }, duration);
    });
}

function numCounter(element) {
    $(element).waypoint(function () {
        let $counter = $(this.element);
        let countTo = $counter.attr('data-count');

        $({ countNum: $counter.text() }).animate({
            countNum: countTo
        }, {
            duration: 100,
            easing: 'linear',
            step: function () {
                $counter.text(Math.floor(this.countNum));
            },
            complete: function () {
                $counter.text(this.countNum);
            }
        }, { offset: '75%' }); // Adjust the offset as needed
    });
}

function logout() {
    console.log('Logout function called');
    $.removeCookie('mytoken', { path: '/' });
    Swal.fire({
        title: 'Log Out',
        text: 'Sign Out.',
        icon: 'success',
        confirmButtonText: 'Ok'
    })
    window.location.href = "/login";
}

function dropdown() {
    let userDropdown = document.getElementById('userDropdown');
    let logoutButton = document.getElementById('logout-button');
    let dropdownMenu = userDropdown.nextElementSibling;

    userDropdown.addEventListener('click', function (event) {
        // Prevent the default link behavior
        event.preventDefault();

        // Toggle the visibility of the dropdown menu
        dropdownMenu.classList.toggle('show');
    });

    logoutButton.addEventListener('click', function () {
        // Call the logout function when the logout button is clicked
        logout();
    });

    // Close the dropdown menu when clicking outside of it
    window.addEventListener('click', function (event) {
        if (event.target !== userDropdown && event.target !== logoutButton) {
            if (dropdownMenu.classList.contains('show')) {
                dropdownMenu.classList.remove('show');
            }
        }
    });
}

function DropMenu() {
    $(document).on('click', function(event){
        if (!$(event.target).closest('.nav-dropdown').length) {
            $('.dropdown-menu').hide();
        }
    });
}


