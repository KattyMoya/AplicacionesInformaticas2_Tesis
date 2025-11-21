/* ==================== HERBARIO ESPOCH - GALERÍA DE IMÁGENES ==================== */

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {

        // ==================== LIGHTBOX MODAL ====================
        let currentImageIndex = 0;
        let images = [];

        // Crear modal de lightbox
        function createLightboxModal() {
            if (document.getElementById('herbario-lightbox')) return;

            const modal = document.createElement('div');
            modal.id = 'herbario-lightbox';
            modal.className = 'herbario-lightbox';
            modal.innerHTML = `
                <div class="herbario-lightbox-overlay"></div>
                <div class="herbario-lightbox-content">
                    <button class="herbario-lightbox-close" aria-label="Cerrar">&times;</button>
                    <button class="herbario-lightbox-prev" aria-label="Anterior">&#10094;</button>
                    <button class="herbario-lightbox-next" aria-label="Siguiente">&#10095;</button>
                    <img class="herbario-lightbox-image" src="" alt="">
                    <div class="herbario-lightbox-info">
                        <h3 class="herbario-lightbox-title"></h3>
                        <p class="herbario-lightbox-family"></p>
                    </div>
                    <div class="herbario-lightbox-counter"></div>
                </div>
            `;
            document.body.appendChild(modal);

            // Event listeners
            modal.querySelector('.herbario-lightbox-close').addEventListener('click', closeLightbox);
            modal.querySelector('.herbario-lightbox-overlay').addEventListener('click', closeLightbox);
            modal.querySelector('.herbario-lightbox-prev').addEventListener('click', showPrevImage);
            modal.querySelector('.herbario-lightbox-next').addEventListener('click', showNextImage);

            // Teclado
            document.addEventListener('keydown', function(e) {
                if (!modal.classList.contains('active')) return;
                
                if (e.key === 'Escape') closeLightbox();
                if (e.key === 'ArrowLeft') showPrevImage();
                if (e.key === 'ArrowRight') showNextImage();
            });
        }

        // Inicializar galería
        function initGallery() {
            const galleryItems = document.querySelectorAll('.herbario-gallery-item');
            
            if (galleryItems.length === 0) return;

            createLightboxModal();

            images = Array.from(galleryItems).map(item => {
                return {
                    src: item.querySelector('img').src,
                    title: item.dataset.title || '',
                    family: item.dataset.family || '',
                    url: item.dataset.url || '#'
                };
            });

            galleryItems.forEach((item, index) => {
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    openLightbox(index);
                });
            });
        }

        function openLightbox(index) {
            currentImageIndex = index;
            const modal = document.getElementById('herbario-lightbox');
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            updateLightboxContent();
        }

        function closeLightbox() {
            const modal = document.getElementById('herbario-lightbox');
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }

        function showPrevImage() {
            currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
            updateLightboxContent();
        }

        function showNextImage() {
            currentImageIndex = (currentImageIndex + 1) % images.length;
            updateLightboxContent();
        }

        function updateLightboxContent() {
            const modal = document.getElementById('herbario-lightbox');
            const image = images[currentImageIndex];
            
            modal.querySelector('.herbario-lightbox-image').src = image.src;
            modal.querySelector('.herbario-lightbox-title').textContent = image.title;
            modal.querySelector('.herbario-lightbox-family').textContent = image.family;
            modal.querySelector('.herbario-lightbox-counter').textContent = `${currentImageIndex + 1} / ${images.length}`;

            // Ocultar botones si solo hay una imagen
            if (images.length <= 1) {
                modal.querySelector('.herbario-lightbox-prev').style.display = 'none';
                modal.querySelector('.herbario-lightbox-next').style.display = 'none';
            }
        }

        // ==================== LAZY LOADING DE IMÁGENES ====================
        function initLazyLoading() {
            const lazyImages = document.querySelectorAll('img[data-src]');
            
            if ('IntersectionObserver' in window) {
                const imageObserver = new IntersectionObserver((entries, observer) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            img.classList.add('loaded');
                            observer.unobserve(img);
                        }
                    });
                });

                lazyImages.forEach(img => imageObserver.observe(img));
            } else {
                // Fallback para navegadores antiguos
                lazyImages.forEach(img => {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                });
            }
        }

        // ==================== FILTRO DE GALERÍA ====================
        const galleryFilterSelect = document.getElementById('herbario-gallery-filter');
        if (galleryFilterSelect) {
            galleryFilterSelect.addEventListener('change', function() {
                const familia = this.value;
                const url = new URL(window.location.href);
                
                if (familia) {
                    url.searchParams.set('familia', familia);
                } else {
                    url.searchParams.delete('familia');
                }
                
                url.searchParams.delete('page'); // Reset página
                window.location.href = url.toString();
            });
        }

        // ==================== GRID LAYOUT DINÁMICO ====================
        function adjustGalleryLayout() {
            const gallery = document.querySelector('.herbario-gallery-grid');
            if (!gallery) return;

            const items = gallery.querySelectorAll('.herbario-gallery-item');
            const width = window.innerWidth;

            let columns = 4;
            if (width < 576) columns = 2;
            else if (width < 768) columns = 3;
            else if (width < 992) columns = 4;
            else columns = 5;

            gallery.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
        }

        // ==================== ANIMACIÓN DE ENTRADA ====================
        function animateGalleryItems() {
            const items = document.querySelectorAll('.herbario-gallery-item');
            
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry, index) => {
                    if (entry.isIntersecting) {
                        setTimeout(() => {
                            entry.target.style.opacity = '1';
                            entry.target.style.transform = 'translateY(0)';
                        }, index * 50);
                        observer.unobserve(entry.target);
                    }
                });
            }, {
                threshold: 0.1
            });

            items.forEach(item => {
                item.style.opacity = '0';
                item.style.transform = 'translateY(20px)';
                item.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                observer.observe(item);
            });
        }

        // Inicializar todo
        initGallery();
        initLazyLoading();
        adjustGalleryLayout();
        animateGalleryItems();

        window.addEventListener('resize', adjustGalleryLayout);

    });

})();

/* ==================== ESTILOS CSS PARA LIGHTBOX ==================== */
const style = document.createElement('style');
style.textContent = `
    .herbario-lightbox {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 9999;
    }
    
    .herbario-lightbox.active {
        display: block;
    }
    
    .herbario-lightbox-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.95);
    }
    
    .herbario-lightbox-content {
        position: relative;
        width: 90%;
        height: 90%;
        margin: 5% auto;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
    }
    
    .herbario-lightbox-image {
        max-width: 90%;
        max-height: 80vh;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
    }
    
    .herbario-lightbox-close {
        position: absolute;
        top: 20px;
        right: 40px;
        font-size: 50px;
        color: white;
        background: none;
        border: none;
        cursor: pointer;
        opacity: 0.7;
        transition: opacity 0.3s;
        z-index: 10000;
    }
    
    .herbario-lightbox-close:hover {
        opacity: 1;
    }
    
    .herbario-lightbox-prev,
    .herbario-lightbox-next {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        font-size: 40px;
        color: white;
        background: rgba(0, 0, 0, 0.5);
        border: none;
        cursor: pointer;
        padding: 20px;
        opacity: 0.7;
        transition: opacity 0.3s;
        border-radius: 4px;
    }
    
    .herbario-lightbox-prev:hover,
    .herbario-lightbox-next:hover {
        opacity: 1;
        background: rgba(0, 0, 0, 0.8);
    }
    
    .herbario-lightbox-prev {
        left: 20px;
    }
    
    .herbario-lightbox-next {
        right: 20px;
    }
    
    .herbario-lightbox-info {
        text-align: center;
        color: white;
        margin-top: 20px;
        max-width: 600px;
    }
    
    .herbario-lightbox-title {
        font-size: 1.5rem;
        font-style: italic;
        margin-bottom: 10px;
    }
    
    .herbario-lightbox-family {
        font-size: 1rem;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .herbario-lightbox-counter {
        position: absolute;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        color: white;
        font-size: 1rem;
        background: rgba(0, 0, 0, 0.5);
        padding: 10px 20px;
        border-radius: 20px;
    }
    
    @media (max-width: 768px) {
        .herbario-lightbox-prev,
        .herbario-lightbox-next {
            font-size: 30px;
            padding: 15px;
        }
        
        .herbario-lightbox-close {
            font-size: 40px;
            right: 20px;
        }
    }
`;
document.head.appendChild(style);