document.addEventListener('DOMContentLoaded', () => {
    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // ссылка на оригинальное изображение хранится в атрибуте "data-src"
                entry.target.src = entry.target.dataset.src
                entry.target.srcset = entry.target.dataset.srcset
                observer.unobserve(entry.target)
            }
        })
    }, { rootMargin: '500px' })

    document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
});
