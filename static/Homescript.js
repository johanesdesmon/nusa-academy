$(document).ready(function () {
    // Spinner
    let spinner = function () {
        setTimeout(function () {
            if ($('#spinner').length > 0) {
                $('#spinner').removeClass('show');
            }
        }, 1);
    };
    spinner();
    fire()

    (function ($) {
        "use strict";

        // Initiate the wowjs
        new WOW().init();

        // Sticky Navbar
        $(window).scroll(function () {
            if ($(this).scrollTop() > 45) {
                $('.navbar').addClass('sticky-top shadow-sm');
            } else {
                $('.navbar').removeClass('sticky-top shadow-sm');
            }
        });

        // Smooth scrolling on the navbar links

        // Back to top button
        $(window).scroll(function () {
            if ($(this).scrollTop() > 100) {
                $('.back-to-top').fadeIn('slow');
            } else {
                $('.back-to-top').fadeOut('slow');
            }
        });
        $('.back-to-top').click(function () {
            $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
            return false;
        });

        // Facts counter
        $('[data-toggle="counter-up"]').counterUp({
            delay: 10,
            time: 2000
        });

        $('a[href*="#"]').on('click', function(e) {
            e.preventDefault()
          
            $('html, body').animate(
              {
                scrollTop: $($(this).attr('href')).offset().top,
              },
              500,
              'linear'
            )
          })
    
        

    })(jQuery);
});
