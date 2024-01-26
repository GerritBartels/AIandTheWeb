function toggleNav() {
    var nav = document.getElementById("mySidenav");
    if (nav.style.width === '250px') {
        nav.style.width = '0';
    } else {
        nav.style.width = '250px';
    }
}

function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
}