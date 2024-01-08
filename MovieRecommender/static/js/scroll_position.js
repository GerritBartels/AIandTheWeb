/** Skips to last scroll postion after reload **/
window.onload = function() {
    if ('scroll_position' in sessionStorage) {
        window.scrollTo({
            top: sessionStorage.getItem('scroll_position'),
            behavior: 'instant'
        });
    }
}

window.onbeforeunload = function() {
    sessionStorage.setItem('scroll_position', window.pageYOffset);
}