(async function() {
  const vocalPath = document.querySelector('path[stroke="#05bde4"]');
  const beatPath = document.querySelector('path[stroke="#0da800"]');
  
  if (!vocalPath || !beatPath) {
    console.error('Path elements not found!');
    return;
  }

  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'audio/mp3,audio/mpeg';
  
  const file = await new Promise((resolve) => {
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) resolve(file);
    };
    input.click();
  });

  if (!file) {
    console.error('No file selected');
    return;
  }

  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  
  const vocalAnalyser = audioContext.createAnalyser();
  vocalAnalyser.fftSize = 8192;
  vocalAnalyser.smoothingTimeConstant = 0.1;
  const vocalBufferLength = vocalAnalyser.frequencyBinCount;
  const vocalDataArray = new Uint8Array(vocalBufferLength);
  
  const beatAnalyser = audioContext.createAnalyser();
  beatAnalyser.fftSize = 8192;
  beatAnalyser.smoothingTimeConstant = 0.1;
  const beatBufferLength = beatAnalyser.frequencyBinCount;
  const beatDataArray = new Uint8Array(beatBufferLength);

  const gainNode = audioContext.createGain();
  gainNode.gain.value = 1.0;

  const audioElement = new Audio();
  audioElement.src = URL.createObjectURL(file);
  audioElement.crossOrigin = "anonymous";
  
  const source = audioContext.createMediaElementSource(audioElement);
  
  source.connect(vocalAnalyser);
  source.connect(beatAnalyser);
  source.connect(gainNode);
  gainNode.connect(audioContext.destination);
  
  await audioElement.play();

  function parsePathData(pathD) {
    const pathCommands = pathD.split(/(?=[MLZ])/);
    const xPositions = pathCommands
      .filter(cmd => cmd.startsWith('L'))
      .map(cmd => {
        const [x] = cmd.substring(1).trim().split(' ').map(Number);
        return x;
      });
    const firstCmd = pathCommands[0].substring(1).trim().split(' ').map(Number);
    xPositions.unshift(firstCmd[0]);
    return xPositions;
  }

  const vocalOriginalD = vocalPath.getAttribute('d');
  const beatOriginalD = beatPath.getAttribute('d');
  const vocalX = parsePathData(vocalOriginalD);
  const beatX = parsePathData(beatOriginalD);

  const centerY = 200;
  let vocalAmp = 250;
  let beatAmp = 300;

  window.setVocalAmp = (val) => { vocalAmp = val; console.log('Vocal amp:', val); };
  window.setBeatAmp = (val) => { beatAmp = val; console.log('Beat amp:', val); };
  
  console.log('Use setVocalAmp(value) and setBeatAmp(value) to control amplitudes');
  console.log('Example: setVocalAmp(500) or setBeatAmp(400)');

  let animationId;

  function animate() {
    vocalAnalyser.getByteFrequencyData(vocalDataArray);
    beatAnalyser.getByteFrequencyData(beatDataArray);

    let vocalPath_new = '';
    for (let i = 0; i < vocalX.length; i++) {
      const freqIndex = Math.floor(vocalBufferLength * 0.25 + (i / vocalX.length) * vocalBufferLength * 0.55);
      const frequency = vocalDataArray[freqIndex];
      
      const freq1 = vocalDataArray[Math.min(vocalBufferLength - 1, freqIndex + 15)] || 0;
      const freq2 = vocalDataArray[Math.min(vocalBufferLength - 1, freqIndex + 30)] || 0;
      const freq3 = vocalDataArray[Math.min(vocalBufferLength - 1, freqIndex + 45)] || 0;
      const freq4 = vocalDataArray[Math.min(vocalBufferLength - 1, freqIndex + 60)] || 0;
      const avgFreq = (frequency * 5 + freq1 * 3 + freq2 * 2 + freq3 + freq4) / 12;
      
      const amplitude = Math.pow(avgFreq / 255, 1.5) * vocalAmp;
      const yPos = centerY - amplitude;
      
      if (i === 0) {
        vocalPath_new = `M ${vocalX[i]} ${yPos}`;
      } else {
        vocalPath_new += ` L ${vocalX[i]} ${yPos}`;
      }
    }
    vocalPath.setAttribute('d', vocalPath_new);

    let beatPath_new = '';
    for (let i = 0; i < beatX.length; i++) {
      const freqIndex = Math.floor((i / beatX.length) * beatBufferLength * 0.08);
      const frequency = beatDataArray[freqIndex];
      
      const freq1 = beatDataArray[Math.min(beatBufferLength - 1, freqIndex + 1)] || 0;
      const freq2 = beatDataArray[Math.min(beatBufferLength - 1, freqIndex + 2)] || 0;
      const freq3 = beatDataArray[Math.min(beatBufferLength - 1, freqIndex + 3)] || 0;
      const freq4 = beatDataArray[Math.min(beatBufferLength - 1, freqIndex + 4)] || 0;
      const freq5 = beatDataArray[Math.min(beatBufferLength - 1, freqIndex + 5)] || 0;
      const avgFreq = (frequency * 6 + freq1 * 4 + freq2 * 3 + freq3 * 2 + freq4 + freq5) / 17;
      
      const amplitude = Math.pow(avgFreq / 255, 1.3) * beatAmp;
      const yPos = centerY - amplitude;
      
      if (i === 0) {
        beatPath_new = `M ${beatX[i]} ${yPos}`;
      } else {
        beatPath_new += ` L ${beatX[i]} ${yPos}`;
      }
    }
    beatPath.setAttribute('d', beatPath_new);

    if (!audioElement.paused && !audioElement.ended) {
      animationId = requestAnimationFrame(animate);
    } else {
      vocalPath.setAttribute('d', vocalOriginalD);
      beatPath.setAttribute('d', beatOriginalD);
    }
  }

  animate();
  
  vocalPath.style.cursor = 'pointer';
  beatPath.style.cursor = 'pointer';
  
  const togglePlayback = () => {
    if (audioElement.paused) {
      audioElement.play();
      animate();
    } else {
      audioElement.pause();
      cancelAnimationFrame(animationId);
    }
  };
  
  vocalPath.addEventListener('click', togglePlayback);
  beatPath.addEventListener('click', togglePlayback);
})();
