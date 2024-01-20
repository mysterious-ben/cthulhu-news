const IMAGE_OFFSET = '200px';

document.addEventListener('DOMContentLoaded', () => {
    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // need attribute data-src and data-srcset
                entry.target.srcset = entry.target.dataset.srcset
                entry.target.src = entry.target.dataset.src
                observer.unobserve(entry.target)
            }
        })
    }, { rootMargin: IMAGE_OFFSET })

    document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
});
