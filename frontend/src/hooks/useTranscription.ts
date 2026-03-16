import { useState, useRef, useCallback } from 'react';

export const useTranscription = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recognitionRef = useRef<any>(null);
  const allChunksRef = useRef<Blob[]>([]);
  const whisperTranscriptRef = useRef('');
  const interimTranscriptRef = useRef('');

  const startRecording = useCallback(async (enableScreenShare: boolean = false) => {
    try {
      console.log(`Starting session (Screen Share: ${enableScreenShare})...`);
      
      const micStream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });

      let finalStream: MediaStream = micStream;

      if (enableScreenShare) {
        try {
          const screenStream = await navigator.mediaDevices.getDisplayMedia({
            video: true,
            audio: {
              echoCancellation: true,
              noiseSuppression: false,
              autoGainControl: false
            }
          });

          // Mix Mic and Screen Audio
          const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
          const dest = audioCtx.createMediaStreamDestination();

          const micSource = audioCtx.createMediaStreamSource(micStream);
          micSource.connect(dest);

          if (screenStream.getAudioTracks().length > 0) {
            const screenSource = audioCtx.createMediaStreamSource(screenStream);
            screenSource.connect(dest);
          } else {
            console.warn("Screen sharing started but no audio track was provided by the user.");
          }

          // Ensure we ONLY pass audio tracks to an audio/webm MediaRecorder.
          // Including video tracks will cause MediaRecorder.start() to throw an error.
          finalStream = new MediaStream(dest.stream.getAudioTracks());

          // Ensure cleaning up screen share stops the session or vice versa
          screenStream.getVideoTracks()[0].onended = () => {
            console.log("Screen share ended by user");
          };

          // Attach context to stream for cleanup
          (finalStream as any)._audioCtx = audioCtx;
          (finalStream as any)._screenStream = screenStream;
        } catch (screenErr) {
          console.error("Screen share cancelled or failed:", screenErr);
          // Fallback to just mic if screen share fails
          finalStream = micStream;
        }
      }
      
      let mimeType = 'audio/webm';
      const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4'];
      for (const t of types) {
        if (MediaRecorder.isTypeSupported(t)) {
          mimeType = t;
          break;
        }
      }
      
      const mediaRecorder = new MediaRecorder(finalStream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      allChunksRef.current = [];
      whisperTranscriptRef.current = '';
      interimTranscriptRef.current = '';
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          allChunksRef.current.push(e.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const finalBlob = new Blob(allChunksRef.current, { type: mimeType });
        setAudioBlob(finalBlob);
      };
      
      mediaRecorder.start(2000);

      // Web Speech API for live feedback (Note: This will likely only hear Mic)
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        recognition.onresult = (event: any) => {
          let interim = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            if (!event.results[i].isFinal) {
              interim += event.results[i][0].transcript;
            }
          }
          interimTranscriptRef.current = interim;
          setTranscript(whisperTranscriptRef.current + " " + interim);
        };

        recognition.onend = () => {
          if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            try { recognition.start(); } catch(_) {}
          }
        };

        recognition.start();
        recognitionRef.current = recognition;
      }

      setIsRecording(true);
      setTranscript('');
      setAudioBlob(null);

      // Periodic Whisper Polling
      const interval = setInterval(async () => {
        if (allChunksRef.current.length > 0 && mediaRecorderRef.current?.state === 'recording') {
          const currentBlob = new Blob(allChunksRef.current, { type: mimeType });
          if (currentBlob.size < 1000) return;
          
          const formData = new FormData();
          formData.append('file', currentBlob, 'chunk.webm');

          try {
            const response = await fetch('http://localhost:8000/api/meetings/transcribe-chunk', {
              method: 'POST',
              body: formData
            });
            if (response.ok) {
              const data = await response.json();
              if (data.transcript) {
                whisperTranscriptRef.current = data.transcript;
                setTranscript(data.transcript + " " + interimTranscriptRef.current);
              }
            }
          } catch (err) {}
        }
      }, 4000);
      (mediaRecorder as any)._intervalId = interval;

    } catch (err) {
      console.error("Failed to start recording:", err);
      setIsRecording(false);
      throw err;
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      const intervalId = (mediaRecorderRef.current as any)._intervalId;
      if (intervalId) clearInterval(intervalId);
      
      const stream = mediaRecorderRef.current.stream;
      mediaRecorderRef.current.stop();
      stream.getTracks().forEach(t => t.stop());

      // Cleanup mixed audio resources
      if ((stream as any)._audioCtx) {
        (stream as any)._audioCtx.close();
      }
      if ((stream as any)._screenStream) {
        (stream as any)._screenStream.getTracks().forEach((t: any) => t.stop());
      }
    }
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsRecording(false);
  }, []);

  return { isRecording, transcript, audioBlob, startRecording, stopRecording, setTranscript };
};
