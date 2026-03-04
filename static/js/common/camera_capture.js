/**
 * camera_capture.js — Componente reutilizable de captura de fotos
 * Soporta: selección de archivos, captura con cámara (móvil/escritorio)
 *
 * Uso:
 *   <div data-camera-widget="photos">
 *     <!-- Se renderiza automáticamente -->
 *   </div>
 *
 * El atributo data-camera-widget debe coincidir con el name del input file
 * del formulario al que se adjuntarán las fotos capturadas.
 */
(function () {
  'use strict';

  class CameraWidget {
    constructor(container) {
      this.container = container;
      this.fieldName = container.dataset.cameraWidget;
      this.files = [];          // DataTransfer para adjuntar al form
      this.dt = new DataTransfer();
      this.stream = null;
      this.render();
      this.bind();
    }

    render() {
      this.container.innerHTML = `
        <div class="d-flex gap-2 mb-2 flex-wrap">
          <label class="btn btn-outline-primary mb-0">
            <i class="bi bi-folder2-open"></i> Seleccionar archivos
            <input type="file" accept="image/*" multiple class="d-none cw-file-input">
          </label>
          <button type="button" class="btn btn-outline-success cw-camera-btn">
            <i class="bi bi-camera-fill"></i> Tomar foto
          </button>
        </div>
        <!-- Visor de cámara (oculto por defecto) -->
        <div class="cw-camera-view d-none mb-3">
          <div class="position-relative d-inline-block">
            <video class="cw-video rounded border" autoplay playsinline
                   style="max-width:100%; max-height:300px;"></video>
            <div class="mt-2 d-flex gap-2">
              <button type="button" class="btn btn-success btn-sm cw-snap">
                <i class="bi bi-camera"></i> Capturar
              </button>
              <button type="button" class="btn btn-secondary btn-sm cw-close-cam">
                <i class="bi bi-x-lg"></i> Cerrar cámara
              </button>
            </div>
          </div>
          <canvas class="d-none cw-canvas"></canvas>
        </div>
        <!-- Preview de fotos seleccionadas -->
        <div class="cw-preview row g-2"></div>
        <!-- Input oculto real que viaja con el form -->
        <input type="file" name="${this.fieldName}" multiple class="d-none cw-hidden-input">
        <small class="text-muted d-block mt-1">Puede seleccionar o capturar múltiples imágenes</small>
      `;

      this.fileInput = this.container.querySelector('.cw-file-input');
      this.hiddenInput = this.container.querySelector('.cw-hidden-input');
      this.cameraBtn = this.container.querySelector('.cw-camera-btn');
      this.cameraView = this.container.querySelector('.cw-camera-view');
      this.video = this.container.querySelector('.cw-video');
      this.canvas = this.container.querySelector('.cw-canvas');
      this.snapBtn = this.container.querySelector('.cw-snap');
      this.closeCamBtn = this.container.querySelector('.cw-close-cam');
      this.preview = this.container.querySelector('.cw-preview');
    }

    bind() {
      // Seleccionar archivos
      this.fileInput.addEventListener('change', () => {
        Array.from(this.fileInput.files).forEach(f => this.addFile(f));
        this.fileInput.value = '';
      });

      // Abrir cámara
      this.cameraBtn.addEventListener('click', () => this.openCamera());

      // Capturar foto
      this.snapBtn.addEventListener('click', () => this.snap());

      // Cerrar cámara
      this.closeCamBtn.addEventListener('click', () => this.closeCamera());

      // Delegación para eliminar preview
      this.preview.addEventListener('click', (e) => {
        const btn = e.target.closest('.cw-remove');
        if (btn) {
          const idx = parseInt(btn.dataset.idx, 10);
          this.removeFile(idx);
        }
      });
    }

    addFile(file) {
      this.files.push(file);
      this.syncHiddenInput();
      this.renderPreview();
    }

    removeFile(idx) {
      this.files.splice(idx, 1);
      this.syncHiddenInput();
      this.renderPreview();
    }

    syncHiddenInput() {
      const dt = new DataTransfer();
      this.files.forEach(f => dt.items.add(f));
      this.hiddenInput.files = dt.files;
    }

    renderPreview() {
      this.preview.innerHTML = '';
      this.files.forEach((file, idx) => {
        const url = URL.createObjectURL(file);
        const col = document.createElement('div');
        col.className = 'col-4 col-md-3 col-lg-2';
        col.innerHTML = `
          <div class="card h-100 shadow-sm">
            <img src="${url}" class="card-img-top" style="height:100px;object-fit:cover;" alt="preview">
            <div class="card-body p-1 text-center">
              <button type="button" class="btn btn-sm btn-outline-danger cw-remove" data-idx="${idx}">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>
        `;
        this.preview.appendChild(col);
      });
    }

    async openCamera() {
      try {
        // Preferir cámara trasera en móviles
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment' },
          audio: false,
        });
        this.video.srcObject = this.stream;
        this.cameraView.classList.remove('d-none');
      } catch (err) {
        // Fallback: intenta cualquier cámara
        try {
          this.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
          this.video.srcObject = this.stream;
          this.cameraView.classList.remove('d-none');
        } catch (err2) {
          alert('No se pudo acceder a la cámara. Verifique los permisos del navegador.');
          console.error(err2);
        }
      }
    }

    snap() {
      const video = this.video;
      const canvas = this.canvas;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0);
      canvas.toBlob((blob) => {
        if (blob) {
          const ts = new Date().toISOString().replace(/[:.]/g, '-');
          const file = new File([blob], `captura-${ts}.jpg`, { type: 'image/jpeg' });
          this.addFile(file);
        }
      }, 'image/jpeg', 0.92);
    }

    closeCamera() {
      if (this.stream) {
        this.stream.getTracks().forEach(t => t.stop());
        this.stream = null;
      }
      this.video.srcObject = null;
      this.cameraView.classList.add('d-none');
    }
  }

  // Auto-inicializar en DOMContentLoaded
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-camera-widget]').forEach(function (el) {
      new CameraWidget(el);
    });
  });
})();
