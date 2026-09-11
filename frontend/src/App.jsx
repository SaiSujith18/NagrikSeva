import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  (window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "/api");

const LANGUAGES = {
  en: {
    name: "English",
    code: "en",
    speechCode: "en-IN",
  },
  te: {
    name: "తెలుగు",
    code: "te",
    speechCode: "te-IN",
  },
  hi: {
    name: "हिन्दी",
    code: "hi",
    speechCode: "hi-IN",
  },
  ur: {
    name: "اردو",
    code: "ur",
    speechCode: "ur-IN",
  },
};

async function parseResponse(response) {
  const contentType =
    response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return await response.json();
  }

  const text = await response.text();

  return {
    success: false,
    message:
      text || `Server returned HTTP ${response.status}`,
  };
}

/* ==========================================================
   URL HELPERS
========================================================== */

function cleanUrl(rawUrl) {
  let url = rawUrl;
  let trailing = "";

  /*
   * Remove punctuation that normally comes after URLs.
   *
   * Example:
   * https://example.com.
   *
   * becomes:
   * https://example.com
   */
  while (
    url.length > 0 &&
    /[.,!?;:]+$/.test(url)
  ) {
    trailing += url[url.length - 1];
    url = url.slice(0, -1);
  }

  /*
   * Handle closing brackets separately.
   *
   * Example:
   * https://example.com)
   */
  while (
    url.endsWith(")") &&
    (url.match(/\(/g) || []).length <
      (url.match(/\)/g) || []).length
  ) {
    trailing = ")" + trailing;
    url = url.slice(0, -1);
  }

  return {
    url,
    trailing,
  };
}

function normalizeUrl(url) {
  if (
    url.startsWith("http://") ||
    url.startsWith("https://")
  ) {
    return url;
  }

  if (url.startsWith("www.")) {
    return `https://${url}`;
  }

  return url;
}

/* ==========================================================
   INLINE TEXT RENDERER
========================================================== */

function renderInlineText(
  text,
  keyPrefix = ""
) {
  if (!text) {
    return null;
  }

  /*
   * Supports:
   *
   * 1. Markdown links
   *    [Click here](https://example.com)
   *
   * 2. HTTPS URLs
   *    https://example.com
   *
   * 3. HTTP URLs
   *    http://example.com
   *
   * 4. WWW URLs
   *    www.example.com
   *
   * 5. Bold text
   *    **Important**
   */

  const tokenRegex =
    /(\[[^\]]+\]\((?:https?:\/\/|www\.)[^)\s]+\)|(?:https?:\/\/|www\.)[^\s<>"'`\\\]}]+|\*\*[^*]+\*\*)/gi;

  const parts = [];

  let lastIndex = 0;
  let match;

  while (
    (match = tokenRegex.exec(text)) !== null
  ) {
    /*
     * Add normal text before token
     */
    if (match.index > lastIndex) {
      parts.push(
        <span
          key={`${keyPrefix}-text-${lastIndex}`}
        >
          {text.slice(
            lastIndex,
            match.index
          )}
        </span>
      );
    }

    const token = match[0];

    /* ======================================================
       MARKDOWN LINK
    ====================================================== */

    if (
      token.startsWith("[") &&
      token.includes("](")
    ) {
      const markdownMatch =
        token.match(
          /^\[([^\]]+)\]\(((?:https?:\/\/|www\.)[^)\s]+)\)$/
        );

      if (markdownMatch) {
        const linkText =
          markdownMatch[1];

        const rawUrl =
          markdownMatch[2];

        const {
          url,
          trailing,
        } = cleanUrl(rawUrl);

        const href =
          normalizeUrl(url);

        parts.push(
          <span
            key={`${keyPrefix}-markdown-link-${match.index}`}
          >
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="answer-link"
            >
              {linkText}
            </a>

            {trailing}
          </span>
        );

        lastIndex =
          match.index + token.length;

        continue;
      }
    }

    /* ======================================================
       NORMAL URL
    ====================================================== */

    if (
      token.startsWith("http://") ||
      token.startsWith("https://") ||
      token.startsWith("www.")
    ) {
      const {
        url,
        trailing,
      } = cleanUrl(token);

      const href =
        normalizeUrl(url);

      parts.push(
        <span
          key={`${keyPrefix}-url-${match.index}`}
        >
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="answer-link"
            title={`Open ${url}`}
          >
            {url}
          </a>

          {trailing}
        </span>
      );

      lastIndex =
        match.index + token.length;

      continue;
    }

    /* ======================================================
       BOLD TEXT
    ====================================================== */

    if (
      token.startsWith("**") &&
      token.endsWith("**")
    ) {
      parts.push(
        <strong
          key={`${keyPrefix}-bold-${match.index}`}
        >
          {token.slice(2, -2)}
        </strong>
      );

      lastIndex =
        match.index + token.length;

      continue;
    }

    /* ======================================================
       FALLBACK
    ====================================================== */

    parts.push(
      <span
        key={`${keyPrefix}-fallback-${match.index}`}
      >
        {token}
      </span>
    );

    lastIndex =
      match.index + token.length;
  }

  /*
   * Add remaining text
   */
  if (lastIndex < text.length) {
    parts.push(
      <span
        key={`${keyPrefix}-remaining`}
      >
        {text.slice(lastIndex)}
      </span>
    );
  }

  return parts;
}

/* ==========================================================
   ANSWER RENDERER
========================================================== */

function renderAnswer(text) {
  if (!text) {
    return null;
  }

  const lines =
    String(text).split(/\r?\n/);

  return lines.map(
    (line, index) => (
      <span key={`line-${index}`}>
        {renderInlineText(
          line,
          `line-${index}`
        )}

        {index <
          lines.length - 1 && (
          <br />
        )}
      </span>
    )
  );
}

/* ==========================================================
   APP
========================================================== */

function App() {
  const [query, setQuery] =
    useState("");

  const [answer, setAnswer] =
    useState("");

  const [serviceId, setServiceId] =
    useState("");

  const [language, setLanguage] =
    useState("en");

  const [
    detectedLanguage,
    setDetectedLanguage,
  ] = useState("en");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [
    isListening,
    setIsListening,
  ] = useState(false);

  const [
    isSpeaking,
    setIsSpeaking,
  ] = useState(false);

  const [
    voiceStatus,
    setVoiceStatus,
  ] = useState("");

  const mediaRecorderRef =
    useRef(null);

  const audioChunksRef =
    useRef([]);

  const streamRef =
    useRef(null);

  const audioRef =
    useRef(null);

  const recognitionRef =
    useRef(null);

  const isBrowserFallbackRef =
    useRef(false);

  /* ========================================================
     LANGUAGE DETECTION
  ======================================================== */

  const detectLanguageFromText =
    (text) => {
      if (!text || !text.trim()) {
        return "en";
      }

      // Telugu
      if (
        /[\u0C00-\u0C7F]/.test(text)
      ) {
        return "te";
      }

      // Hindi / Devanagari
      if (
        /[\u0900-\u097F]/.test(text)
      ) {
        return "hi";
      }

      // Urdu / Arabic
      if (
        /[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]/.test(
          text
        )
      ) {
        return "ur";
      }

      return "en";
    };

  /* ========================================================
     STOP SPEAKING
  ======================================================== */

  const stopSpeaking = () => {
    if (audioRef.current) {
      try {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      } catch {
        // Ignore
      }

      audioRef.current = null;
    }

    setIsSpeaking(false);
    setVoiceStatus("");
  };

  /* ========================================================
     LANGUAGE CHANGE
  ======================================================== */

  const handleLanguageChange = (
    event
  ) => {
    const selectedLanguage =
      event.target.value;

    setLanguage(
      selectedLanguage
    );

    setDetectedLanguage(
      selectedLanguage
    );

    setError("");
    setVoiceStatus("");

    stopSpeaking();

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // Ignore
      }

      recognitionRef.current = null;
    }

    isBrowserFallbackRef.current =
      false;

    setIsListening(false);
  };

  /* ========================================================
     BROWSER SPEECH RECOGNITION
  ======================================================== */

  const startBrowserSpeechRecognition =
    () => {
      const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

      if (!SpeechRecognition) {
        setIsListening(false);

        setVoiceStatus("");

        setError(
          "Sarvam STT has no credits available, and your browser does not support speech recognition. Please use Google Chrome or Microsoft Edge."
        );

        return;
      }

      try {
        if (recognitionRef.current) {
          try {
            recognitionRef.current.stop();
          } catch {
            // Ignore
          }
        }

        const recognition =
          new SpeechRecognition();

        recognitionRef.current =
          recognition;

        isBrowserFallbackRef.current =
          true;

        recognition.lang =
          LANGUAGES[language]
            ?.speechCode || "en-IN";

        recognition.continuous =
          false;

        recognition.interimResults =
          true;

        recognition.maxAlternatives =
          1;

        recognition.onstart = () => {
          setIsListening(true);

          setVoiceStatus(
            `🌐 Sarvam credits unavailable — using browser speech recognition in ${
              LANGUAGES[language]
                ?.name || "English"
            }...`
          );
        };

        recognition.onresult = (
          event
        ) => {
          let transcript = "";

          for (
            let i =
              event.resultIndex;
            i <
            event.results.length;
            i++
          ) {
            transcript +=
              event.results[i][0]
                .transcript;
          }

          transcript =
            transcript.trim();

          if (transcript) {
            setQuery(transcript);

            const detected =
              detectLanguageFromText(
                transcript
              );

            const finalLanguage =
              detected !== "en"
                ? detected
                : language;

            setLanguage(
              finalLanguage
            );

            setDetectedLanguage(
              finalLanguage
            );

            setVoiceStatus(
              `📝 ${
                LANGUAGES[
                  finalLanguage
                ]?.name ||
                "English"
              } speech recognized`
            );
          }
        };

        recognition.onerror = (
          event
        ) => {
          console.error(
            "Browser speech recognition error:",
            event
          );

          setIsListening(false);

          recognitionRef.current =
            null;

          isBrowserFallbackRef.current =
            false;

          if (
            event.error ===
            "not-allowed"
          ) {
            setError(
              "Browser microphone permission was denied. Please allow microphone access and try again."
            );
          } else if (
            event.error ===
            "no-speech"
          ) {
            setError(
              "No speech was detected. Please try again."
            );
          } else if (
            event.error ===
            "audio-capture"
          ) {
            setError(
              "No microphone was available for browser speech recognition."
            );
          } else {
            setError(
              `Browser speech recognition failed: ${
                event.error ||
                "Unknown error"
              }`
            );
          }

          setVoiceStatus("");
        };

        recognition.onend = () => {
          setIsListening(false);

          recognitionRef.current =
            null;

          isBrowserFallbackRef.current =
            false;

          setVoiceStatus(
            (current) =>
              current.includes(
                "recognized"
              )
                ? current
                : ""
          );
        };

        recognition.start();
      } catch (err) {
        console.error(
          "Unable to start browser speech recognition:",
          err
        );

        setIsListening(false);

        recognitionRef.current =
          null;

        isBrowserFallbackRef.current =
          false;

        setVoiceStatus("");

        setError(
          `Browser speech recognition could not start: ${
            err?.message ||
            "Unknown error"
          }`
        );
      }
    };

  /* ========================================================
     START LISTENING
  ======================================================== */

  const startListening = async () => {
    setError("");
    setVoiceStatus("");

    if (
      isBrowserFallbackRef.current
    ) {
      return;
    }

    if (
      !navigator.mediaDevices
        ?.getUserMedia
    ) {
      setError(
        "Microphone recording is not supported in this browser."
      );

      return;
    }

    if (!window.MediaRecorder) {
      setError(
        "Audio recording is not supported in this browser."
      );

      return;
    }

    if (mediaRecorderRef.current) {
      try {
        if (
          mediaRecorderRef.current
            .state !== "inactive"
        ) {
          mediaRecorderRef.current.stop();
        }
      } catch {
        // Ignore
      }
    }

    try {
      const stream =
        await navigator.mediaDevices.getUserMedia(
          {
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true,
            },
          }
        );

      streamRef.current =
        stream;

      audioChunksRef.current = [];

      let mimeType = "";

      if (
        MediaRecorder.isTypeSupported(
          "audio/webm;codecs=opus"
        )
      ) {
        mimeType =
          "audio/webm;codecs=opus";
      } else if (
        MediaRecorder.isTypeSupported(
          "audio/webm"
        )
      ) {
        mimeType = "audio/webm";
      } else if (
        MediaRecorder.isTypeSupported(
          "audio/ogg;codecs=opus"
        )
      ) {
        mimeType =
          "audio/ogg;codecs=opus";
      }

      const recorder = mimeType
        ? new MediaRecorder(
            stream,
            { mimeType }
          )
        : new MediaRecorder(stream);

      mediaRecorderRef.current =
        recorder;

      recorder.ondataavailable = (
        event
      ) => {
        if (
          event.data &&
          event.data.size > 0
        ) {
          audioChunksRef.current.push(
            event.data
          );
        }
      };

      recorder.onstart = () => {
        setIsListening(true);

        setVoiceStatus(
          `🎤 Listening in ${
            LANGUAGES[language]
              ?.name || "English"
          }... Speak now`
        );
      };

      recorder.onstop = async () => {
        setIsListening(false);

        setVoiceStatus(
          "🔄 Converting speech to text..."
        );

        if (streamRef.current) {
          streamRef.current
            .getTracks()
            .forEach((track) =>
              track.stop()
            );

          streamRef.current = null;
        }

        const chunks =
          audioChunksRef.current;

        if (!chunks.length) {
          setVoiceStatus("");

          setError(
            "No audio was recorded. Please try again."
          );

          return;
        }

        const blob = new Blob(
          chunks,
          {
            type:
              mimeType ||
              "audio/webm",
          }
        );

        await sendAudioToSarvam(
          blob
        );
      };

      recorder.onerror = (event) => {
        console.error(
          "MediaRecorder error:",
          event
        );

        setIsListening(false);
        setVoiceStatus("");

        setError(
          "Unable to record microphone audio."
        );

        if (streamRef.current) {
          streamRef.current
            .getTracks()
            .forEach((track) =>
              track.stop()
            );

          streamRef.current = null;
        }
      };

      recorder.start();
    } catch (err) {
      console.error(
        "Microphone error:",
        err
      );

      setIsListening(false);
      setVoiceStatus("");

      if (
        err?.name ===
        "NotAllowedError"
      ) {
        setError(
          "Microphone permission was denied. Please allow microphone access."
        );
      } else if (
        err?.name ===
        "NotFoundError"
      ) {
        setError(
          "No microphone was found."
        );
      } else {
        setError(
          `Unable to access microphone: ${
            err?.message ||
            "Unknown error"
          }`
        );
      }
    }
  };

  /* ========================================================
     SEND AUDIO TO SARVAM
  ======================================================== */

  const sendAudioToSarvam = async (
    audioBlob
  ) => {
    try {
      const extension =
        audioBlob.type.includes("ogg")
          ? "ogg"
          : "webm";

      const audioFile = new File(
        [audioBlob],
        `speech.${extension}`,
        {
          type:
            audioBlob.type ||
            "audio/webm",
        }
      );

      const formData =
        new FormData();

      formData.append(
        "file",
        audioFile
      );

      formData.append(
        "language",
        language
      );

      const response =
        await fetch(
          `${API_BASE}/stt`,
          {
            method: "POST",
            body: formData,
          }
        );

      const data =
        await parseResponse(
          response
        );

      console.log(
        "Sarvam STT response:",
        data
      );

      const isInsufficientQuota =
        response.status === 402 ||
        data?.error?.code ===
          "insufficient_quota_error" ||
        data?.detail?.error?.code ===
          "insufficient_quota_error" ||
        String(
          data?.message ||
            data?.detail ||
            ""
        )
          .toLowerCase()
          .includes(
            "no credits available"
          );

      if (isInsufficientQuota) {
        console.warn(
          "Sarvam STT credits exhausted. Switching to browser speech recognition."
        );

        setVoiceStatus(
          "⚠️ Sarvam credits exhausted. Switching to browser speech recognition..."
        );

        setTimeout(() => {
          startBrowserSpeechRecognition();
        }, 300);

        return;
      }

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.message ||
            `Backend returned ${response.status}`
        );
      }

      if (!data.success) {
        throw new Error(
          data.message ||
            data.detail ||
            "Unable to recognize speech."
        );
      }

      const transcript =
        data.transcript ||
        data.text ||
        "";

      if (!transcript.trim()) {
        throw new Error(
          "No speech was recognized."
        );
      }

      const backendLanguage =
        data.detected_language ||
        data.language ||
        language;

      const finalLanguage =
        LANGUAGES[backendLanguage]
          ? backendLanguage
          : language;

      setQuery(transcript);

      setLanguage(
        finalLanguage
      );

      setDetectedLanguage(
        finalLanguage
      );

      setVoiceStatus(
        `✅ ${
          LANGUAGES[finalLanguage]
            ?.name || "English"
        } detected`
      );

      setTimeout(() => {
        setVoiceStatus("");
      }, 2500);
    } catch (err) {
      console.error(
        "STT error:",
        err
      );

      setError(
        `Speech-to-text failed: ${
          err?.message ||
          "Unknown error"
        }`
      );

      setVoiceStatus("");
    }
  };

  /* ========================================================
     STOP LISTENING
  ======================================================== */

  const stopListening = () => {
    if (
      recognitionRef.current
    ) {
      try {
        recognitionRef.current.stop();
      } catch {
        // Ignore
      }

      recognitionRef.current = null;

      isBrowserFallbackRef.current =
        false;

      setIsListening(false);
      setVoiceStatus("");

      return;
    }

    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current
        .state !== "inactive"
    ) {
      try {
        mediaRecorderRef.current.stop();
      } catch {
        // Ignore
      }
    }

    setIsListening(false);
  };

  /* ========================================================
     TOGGLE LISTENING
  ======================================================== */

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  /* ========================================================
     ASK SERVICE
  ======================================================== */

  const askService = async () => {
    if (!query.trim()) {
      setError(
        "Please enter a question."
      );

      return;
    }

    if (isListening) {
      stopListening();
    }

    if (isSpeaking) {
      stopSpeaking();
    }

    setLoading(true);
    setAnswer("");
    setServiceId("");
    setError("");
    setVoiceStatus("");

    const textLanguage =
      detectLanguageFromText(query);

    let requestLanguage =
      language;

    if (textLanguage !== "en") {
      requestLanguage =
        textLanguage;
    }

    setDetectedLanguage(
      requestLanguage
    );

    try {
      const params =
        new URLSearchParams();

      params.set(
        "q",
        query.trim()
      );

      params.set(
        "language",
        requestLanguage
      );

      const url =
        `${API_BASE}/ask?${params.toString()}`;

      console.log(
        "Calling API:",
        url
      );

      const response =
        await fetch(url, {
          method: "GET",
          headers: {
            Accept:
              "application/json",
          },
        });

      const data =
        await parseResponse(
          response
        );

      console.log(
        "NagrikSeva /ask response:",
        data
      );

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.message ||
            `Backend returned ${response.status}`
        );
      }

      const backendLanguage =
        data.detected_language ||
        data.language ||
        requestLanguage;

      const finalLanguage =
        LANGUAGES[backendLanguage]
          ? backendLanguage
          : requestLanguage;

      setLanguage(
        finalLanguage
      );

      setDetectedLanguage(
        finalLanguage
      );

      if (data.success) {
        setAnswer(
          data.answer || ""
        );

        setServiceId(
          data.service_id || ""
        );

        if (
          !data.answer?.trim()
        ) {
          setError(
            "The backend returned success but no answer."
          );
        }

        return;
      }

      setAnswer(
        data.message ||
          "Service information was not found."
      );

      setServiceId(
        data.service_id || ""
      );
    } catch (err) {
      console.error(
        "NagrikSeva API error:",
        err
      );

      setError(
        `Unable to connect to backend: ${
          err?.message ||
          "Unknown error"
        }`
      );
    } finally {
      setLoading(false);
    }
  };

  /* ========================================================
     QUERY CHANGE
  ======================================================== */

  const handleQueryChange = (
    event
  ) => {
    const value =
      event.target.value;

    setQuery(value);

    setError("");

    if (value.trim()) {
      const detected =
        detectLanguageFromText(
          value
        );

      if (detected !== "en") {
        setLanguage(detected);

        setDetectedLanguage(
          detected
        );
      }
    }
  };

  /* ========================================================
     ENTER KEY
  ======================================================== */

  const handleKeyDown = (
    event
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      if (!loading) {
        askService();
      }
    }
  };

  /* ========================================================
     TEXT TO SPEECH
  ======================================================== */

  const speakAnswer = async () => {
    if (!answer?.trim()) {
      return;
    }

    setError("");

    stopSpeaking();

    setIsSpeaking(true);

    const speechLanguage =
      detectedLanguage ||
      language ||
      "en";

    setVoiceStatus(
      `🔊 Generating ${
        LANGUAGES[speechLanguage]
          ?.name || "English"
      } speech...`
    );

    try {
      const response =
        await fetch(
          `${API_BASE}/tts`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",

              Accept: "audio/*",
            },

            body: JSON.stringify({
              text: answer,
              language:
                speechLanguage,
            }),
          }
        );

      if (!response.ok) {
        let message =
          `TTS server returned ${response.status}`;

        try {
          const data =
            await parseResponse(
              response
            );

          message =
            data.detail ||
            data.message ||
            message;
        } catch {
          // Ignore
        }

        throw new Error(
          message
        );
      }

      const audioBlob =
        await response.blob();

      if (!audioBlob.size) {
        throw new Error(
          "TTS returned empty audio."
        );
      }

      const audioUrl =
        URL.createObjectURL(
          audioBlob
        );

      const audio =
        new Audio(audioUrl);

      audioRef.current = audio;

      audio.onplay = () => {
        setIsSpeaking(true);

        setVoiceStatus(
          `🔊 Speaking in ${
            LANGUAGES[
              speechLanguage
            ]?.name ||
            "English"
          }`
        );
      };

      audio.onended = () => {
        setIsSpeaking(false);

        setVoiceStatus("");

        URL.revokeObjectURL(
          audioUrl
        );

        audioRef.current = null;
      };

      audio.onerror = () => {
        setIsSpeaking(false);

        setVoiceStatus("");

        URL.revokeObjectURL(
          audioUrl
        );

        audioRef.current = null;

        setError(
          "Unable to play generated speech."
        );
      };

      await audio.play();
    } catch (err) {
      console.error(
        "TTS error:",
        err
      );

      setIsSpeaking(false);

      setVoiceStatus("");

      setError(
        `Text-to-speech failed: ${
          err?.message ||
          "Unknown error"
        }`
      );
    }
  };

  /* ========================================================
     CLEANUP
  ======================================================== */

  useEffect(() => {
    return () => {
      if (
        mediaRecorderRef.current
      ) {
        try {
          if (
            mediaRecorderRef.current
              .state !== "inactive"
          ) {
            mediaRecorderRef.current.stop();
          }
        } catch {
          // Ignore
        }
      }

      if (streamRef.current) {
        streamRef.current
          .getTracks()
          .forEach((track) =>
            track.stop()
          );
      }

      if (
        recognitionRef.current
      ) {
        try {
          recognitionRef.current.stop();
        } catch {
          // Ignore
        }
      }

      if (audioRef.current) {
        try {
          audioRef.current.pause();
        } catch {
          // Ignore
        }
      }
    };
  }, []);

  /* ========================================================
     CURRENT LANGUAGE
  ======================================================== */

  const currentLanguageName =
    LANGUAGES[
      detectedLanguage
    ]?.name || "English";

  const isRTL =
    detectedLanguage === "ur";

  /* ========================================================
     UI
  ======================================================== */

  return (
    <div
      className={`app ${
        isRTL ? "rtl" : ""
      }`}
      dir={
        isRTL ? "rtl" : "ltr"
      }
    >
      {/* HEADER */}

      <header className="header">
        <div className="brand">
          <div
            className="flag"
            aria-hidden="true"
          >
            🇮🇳
          </div>

          <div>
            <h1>NagrikSeva</h1>

            <p>
              AI Government
              Service Assistant
            </p>
          </div>
        </div>

        <div
          className="language-indicator"
          aria-live="polite"
        >
          {currentLanguageName}
        </div>
      </header>

      {/* MAIN */}

      <main className="container">
        {/* HERO */}

        <section className="hero">
          <div
            className="hero-icon"
            aria-hidden="true"
          >
            🤖
          </div>

          <h2>
            How can we help you?
          </h2>

          <p>
            Ask about TS
            government services
            in English, Telugu,
            Hindi or Urdu.
          </p>
        </section>

        {/* SEARCH CARD */}

        <section className="search-card">
          <label
            htmlFor="service-query"
            className="input-label"
          >
            Ask about a government
            service
          </label>

          <textarea
            id="service-query"
            value={query}
            onChange={
              handleQueryChange
            }
            onKeyDown={
              handleKeyDown
            }
            placeholder="Example: I need an income certificate"
            rows={4}
            disabled={loading}
            lang={
              detectedLanguage
            }
            dir={
              isRTL
                ? "rtl"
                : "ltr"
            }
            aria-describedby="query-help"
          />

          <p
            id="query-help"
            className="query-help"
          >
            Type your question or
            use the microphone.
            Press Enter to search.
          </p>

          {/* LANGUAGE */}

          <div className="voice-language-selector">
            <label htmlFor="language-select">
              Select Language
            </label>

            <select
              id="language-select"
              value={language}
              onChange={
                handleLanguageChange
              }
              disabled={
                loading ||
                isListening
              }
            >
              <option value="en">
                English
              </option>

              <option value="te">
                తెలుగు
              </option>

              <option value="hi">
                हिन्दी
              </option>

              <option value="ur">
                اردو
              </option>
            </select>

            <span>
              {LANGUAGES[
                language
              ]?.name ||
                "English"}
            </span>
          </div>

          {/* BUTTONS */}

          <div className="voice-controls">
            <button
              type="button"
              className={`voice-button ${
                isListening
                  ? "active"
                  : ""
              }`}
              onClick={
                toggleListening
              }
              disabled={loading}
              aria-pressed={
                isListening
              }
            >
              {isListening
                ? "⏹ Stop Listening"
                : "🎙️ Speak"}
            </button>

            <button
              type="button"
              className="ask-button"
              onClick={
                askService
              }
              disabled={
                loading ||
                !query.trim()
              }
            >
              {loading
                ? "Searching..."
                : "Ask NagrikSeva"}
            </button>
          </div>

          {/* VOICE STATUS */}

          <div
            className="voice-status"
            aria-live="assertive"
            aria-atomic="true"
          >
            {voiceStatus}
          </div>
        </section>

        {/* ERROR */}

        {error && (
          <div
            className="error-message"
            role="alert"
          >
            {error}
          </div>
        )}

        {/* RESULT */}

        {answer && (
          <section
            className="result-card"
            aria-labelledby="result-title"
          >
            <div className="result-header">
              <div>
                <p className="result-label">
                  Government Service
                  Information
                </p>

                <h2 id="result-title">
                  {serviceId
                    ? serviceId
                        .replaceAll(
                          "_",
                          " "
                        )
                        .replace(
                          /\b\w/g,
                          (char) =>
                            char.toUpperCase()
                        )
                    : "Service Result"}
                </h2>
              </div>

              <span className="language-badge">
                {currentLanguageName}
              </span>
            </div>

            {/* ANSWER */}

            <div
              className="answer"
              lang={
                detectedLanguage
              }
              dir={
                isRTL
                  ? "rtl"
                  : "ltr"
              }
            >
              {renderAnswer(answer)}
            </div>

            {/* TTS */}

            <div className="result-actions">
              {!isSpeaking ? (
                <button
                  type="button"
                  className="listen-button"
                  onClick={
                    speakAnswer
                  }
                >
                  🔊 Listen in{" "}
                  {
                    currentLanguageName
                  }
                </button>
              ) : (
                <button
                  type="button"
                  className="listen-button stop-speaking"
                  onClick={
                    stopSpeaking
                  }
                >
                  ⏹ Stop Speaking
                </button>
              )}
            </div>
          </section>
        )}
      </main>

      {/* FOOTER */}

      <footer>
        🇮🇳 NagrikSeva •
        Multilingual AI Government
        Service Assistant
      </footer>
    </div>
  );
}

export default App;