/* DocuSense Lex voice experience — integrated into PlantGuard (Days 11–15). */
(function () {
  "use strict";

  var API = window.DOCUSENSE_API_URL || "";
  var LANGS = ["en", "fr", "ar", "pt", "sw", "yo", "ha", "ig", "es", "de", "zh", "hi"];
  var LANGUAGE_TO_LOCALE = {
    en: "en-GB", fr: "fr-FR", ar: "ar-SA", pt: "pt-BR", sw: "sw-KE",
    yo: "yo-NG", ha: "ha-NG", ig: "ig-NG", es: "es-ES", de: "de-DE",
    zh: "zh-CN", hi: "hi-IN",
  };
  var LANGUAGE_NAMES = {
    en: "English", fr: "French", ar: "Arabic", pt: "Portuguese", sw: "Swahili",
    yo: "Yoruba", ha: "Hausa", ig: "Igbo", es: "Spanish", de: "German",
    zh: "Mandarin Chinese", hi: "Hindi",
  };
  var ORB_COLORS = {
    violet: { ring1: "rgba(124,77,255,.35)", ring2: "rgba(0,188,212,.25)", glow: "rgba(124,77,255,.5)" },
    cyan: { ring1: "rgba(0,188,212,.4)", ring2: "rgba(0,255,200,.2)", glow: "rgba(0,188,212,.55)" },
    gold: { ring1: "rgba(201,168,76,.45)", ring2: "rgba(255,220,100,.2)", glow: "rgba(201,168,76,.6)" },
    ember: { ring1: "rgba(255,100,50,.4)", ring2: "rgba(255,160,50,.2)", glow: "rgba(255,80,30,.5)" },
    arctic: { ring1: "rgba(200,230,255,.4)", ring2: "rgba(150,200,255,.25)", glow: "rgba(180,220,255,.5)" },
    jade: { ring1: "rgba(50,200,120,.4)", ring2: "rgba(100,255,150,.2)", glow: "rgba(40,180,100,.5)" },
    rose: { ring1: "rgba(255,100,150,.4)", ring2: "rgba(255,150,180,.2)", glow: "rgba(240,80,130,.5)" },
    solar: { ring1: "rgba(255,200,50,.4)", ring2: "rgba(255,150,0,.25)", glow: "rgba(255,180,0,.55)" },
  };
  var VOICE_TO_BROWSER_NAMES = {
    nova: ["Google UK English Female", "Samantha", "Karen", "Moira", "Fiona"],
    sterling: ["Google UK English Male", "Daniel", "Arthur", "Gordon"],
    quinn: ["Google US English", "Alex", "Zira", "David", "Mark"],
    sydney: ["Google Australian English", "Karen", "Lee", "Catherine"],
    anika: ["Google हिन्दी", "Rishi", "Veena", "Neel", "Lekha"],
    amara: ["Google français", "Thomas", "Amélie", "Julie", "Alain"],
    zara: ["Google العربية", "Maged", "Laila", "Tarik", "Majed"],
    lena: ["Google português do Brasil", "Luciana", "Joana", "Catarina"],
    sage: ["Samantha", "Google UK English Female", "Moira"],
  };
  var VOICE_DESCRIPTIONS = {
    nova: "British · warm", sterling: "British · formal", quinn: "American · clear",
    sydney: "Australian · relaxed", anika: "Hindi · native", amara: "French · native",
    zara: "Arabic · native", lena: "Portuguese · native", sage: "Neutral · calm",
  };
  var SUGGESTED_NAMES = ["Lex", "Atlas", "Nova", "Sage", "Echo", "Aria", "Rex", "Orion", "Vera", "Zara"];
  var I18N = {
    en: { empty: "Hello. I'm {name}. Your AI legal companion. Say 'Hey {name}' or type below.",
          jurisdiction: "Nigerian Law Active", voiceUnsupported: "Voice not available in this browser. Using text mode. Chrome recommended for full experience.",
          send: "Send", settings: "Settings", listening: "Listening…", idle: "Hey {name}", processing: "Thinking…" },
    fr: { empty: "Bonjour. Je suis {name}. Votre compagnon juridique IA. Dites « Salut {name} » ou écrivez ci-dessous.",
          jurisdiction: "Droit nigérian actif", voiceUnsupported: "La voix n'est pas disponible dans ce navigateur. Mode texte activé.",
          send: "Envoyer", settings: "Paramètres", listening: "Écoute…", idle: "Salut {name}", processing: "Réflexion…" },
    ar: { empty: "مرحباً، أنا {name}. مساعدك القانوني الذكي. قل «مرحبا {name}» أو اكتب أدناه.",
          jurisdiction: "القانون النيجيري نشط", voiceUnsupported: "الصوت غير متاح في هذا المتصفح. يتم استخدام وضع النص.",
          send: "إرسال", settings: "الإعدادات", listening: "أصغي…", idle: "مرحبا {name}", processing: "أفكر…" },
    pt: { empty: "Olá. Eu sou {name}. Seu assistente jurídico de IA. Diga 'Olá {name}' ou escreva abaixo.",
          jurisdiction: "Lei nigeriana ativa", voiceUnsupported: "Voz não disponível neste navegador. Usando modo texto.",
          send: "Enviar", settings: "Configurações", listening: "Ouvindo…", idle: "Olá {name}", processing: "Pensando…" },
    yo: { empty: "Bawo ni. Emi ni {name}. Alábàárín òfin rẹ. Sọ 'Ẹ jẹ {name}' tabi kọ sílẹ̀.",
          jurisdiction: "Ofin Nàìjíríà ṣiṣẹ́", voiceUnsupported: "Ohun kọ sílẹ̀ nínú ẹrọ aṣawakiri yi. A n lo ipo ọrọ.",
          send: "Firán", settings: "Àtòjọ", listening: "Ń gbọ́…", idle: "Ẹ jẹ {name}", processing: "Ń ronú…" },
    ha: { empty: "Sannu. Ni ne {name}. Abokin shari'a na AI. Ka ce 'Kai {name}' ko rubuta a ƙasa.",
          jurisdiction: "Dokar Najeriya tana aiki", voiceUnsupported: "Murya ba ta samuwa a wannan burauza. Ana amfani da rubutu.",
          send: "Aika", settings: "Saiti", listening: "Ina sauraro…", idle: "Kai {name}", processing: "Ina tunani…" },
    sw: { empty: "Habari. Mimi ni {name}. Msaidizi wako wa kisheria wa AI. Sema 'Sawa {name}' au andika hapa chini.",
          jurisdiction: "Sheria ya Nigeria inatumika", voiceUnsupported: "Sauti haipatikani kwenye kivinjari hiki. Tunatumia maandishi.",
          send: "Tuma", settings: "Mipangilio", listening: "Ninasikiliza…", idle: "Sawa {name}", processing: "Ninafikiri…" },
  };

  /* ---------- localStorage helpers ---------- */
  function getCompanionName() { return localStorage.getItem("docusense_companion_name") || "Lex"; }
  function saveCompanionName(v) { localStorage.setItem("docusense_companion_name", v); }
  function getOrbColor() { return localStorage.getItem("docusense_orb_color") || "violet"; }
  function saveOrbColor(v) { localStorage.setItem("docusense_orb_color", v); }
  function getCompanionVoice() { return localStorage.getItem("docusense_companion_voice") || "nova"; }
  function saveCompanionVoice(v) { localStorage.setItem("docusense_companion_voice", v); }
  function getPreferredLanguage() { return localStorage.getItem("docusense_preferred_language") || "en"; }
  function savePreferredLanguage(v) { localStorage.setItem("docusense_preferred_language", v); }
  function saveAllCompanionSettings(s) {
    saveCompanionName(s.name); saveOrbColor(s.color);
    saveCompanionVoice(s.voice); savePreferredLanguage(s.language);
  }
  function settings() {
    return { name: getCompanionName(), color: getOrbColor(),
             voice: getCompanionVoice(), language: getPreferredLanguage() };
  }
  function tr(key) {
    var t = I18N[getPreferredLanguage()] || I18N.en;
    return (t[key] || I18N.en[key] || key).replace(/\{name\}/g, getCompanionName());
  }

  /* ---------- wake word + intent ---------- */
  function buildWakePatterns(name, language) {
    var n = String(name || "").toLowerCase();
    var base = [n, "hey " + n, "ok " + n, "okay " + n, "hi " + n, "yo " + n, "oi " + n];
    var extra = {
      fr: ["hé " + n, "salut " + n, "bonjour " + n],
      ar: ["مرحبا " + n, n + " مرحبا"],
      yo: ["ẹ jẹ " + n], ha: ["kai " + n], ig: ["nna " + n], sw: ["sawa " + n],
    };
    return base.concat(extra[language] || []);
  }
  function detectWakeWord(transcript, name, language) {
    var text = String(transcript || "").toLowerCase().trim();
    return buildWakePatterns(name, language).some(function (p) { return text.indexOf(p) !== -1; });
  }
  function parseIntent(transcript) {
    var t = String(transcript || "").toLowerCase();
    function has() { return Array.prototype.some.call(arguments, function (w) { return t.indexOf(w) !== -1; }); }
    if (has("analyze", "analyse", "check this contract", "review this document")) return { intent: "ANALYZE_DOCUMENT", confidence: "high" };
    if (has("draft", "generate", "write a contract", "create a letter")) return { intent: "GENERATE_DOCUMENT", confidence: "high" };
    if (has("irac", "issue rule application conclusion", "case brief")) return { intent: "IRAC_MEMO", confidence: "high" };
    if (has("cite", "which act", "what law", "explain the law")) return { intent: "ASK_QUESTION", confidence: "medium" };
    return { intent: "GENERAL_CHAT", confidence: "low" };
  }

  /* ---------- context manager ---------- */
  function LexContextManager() {
    this.turns = [];
    this.context = "idle";
  }
  LexContextManager.prototype.addTurn = function (role, content, intent) {
    this.turns.push({ role: role, content: content, intent: intent || null });
    if (this.turns.length > 10) this.turns = this.turns.slice(-10);
  };
  LexContextManager.prototype.getHistory = function () {
    return this.turns.slice(-10).map(function (t) { return { role: t.role, content: t.content }; });
  };
  LexContextManager.prototype.getCurrentContext = function () { return this.context; };
  LexContextManager.prototype.setContext = function (ctx) { this.context = ctx; };
  LexContextManager.prototype.clear = function () { this.turns = []; this.context = "idle"; };

  /* ---------- API (falls back to deterministic local demo) ---------- */
  function apiCall(path, body) {
    if (!API) {
      return new Promise(function (resolve) {
        setTimeout(function () {
          if (path.indexOf("/voice") !== -1) {
            var intent = body.intent || "GENERAL_CHAT";
            resolve({
              response_text: "I've noted that. " + (intent === "ANALYZE_DOCUMENT"
                ? "Upload a document and I'll analyse it under the selected jurisdiction."
                : "Tell me a little more about the clause you're concerned about."),
              intent_processed: intent, session_id: body.session_id || "local-session",
              should_navigate_to: intent === "ANALYZE_DOCUMENT" ? "analyze" : null,
              voice_session_stats: { total_turns: 1 },
            });
          } else if (path.indexOf("/analyze") !== -1) {
            resolve({ id: "local-analysis", document_type: "Contract", risk_level: "MEDIUM",
                      risk_score: 42, overall_verdict: "NEGOTIATE",
                      verdict_reason: "Connect the DocuSense API for full analysis.",
                      summary: "Local demo analysis." });
          } else {
            resolve({ response: "Done.", session_id: body.session_id || "local-session" });
          }
        }, 260);
      });
    }
    return fetch(API + path, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(function (r) { return r.json(); });
  }

  /* ---------- TTS ---------- */
  function bestVoice(voiceKey) {
    var voices = (window.speechSynthesis && speechSynthesis.getVoices()) || [];
    var names = VOICE_TO_BROWSER_NAMES[voiceKey] || VOICE_TO_BROWSER_NAMES.nova;
    for (var i = 0; i < names.length; i++) {
      var found = voices.filter(function (v) { return v.name === names[i]; })[0];
      if (found) return found;
    }
    return voices[0] || null;
  }
  function speak(text, onAmplitude, onEnd) {
    if (!("speechSynthesis" in window)) { onAmplitude(0); if (onEnd) onEnd(); return false; }
    speechSynthesis.cancel();
    var utter = new SpeechSynthesisUtterance(text);
    var s = settings();
    utter.lang = LANGUAGE_TO_LOCALE[s.language] || "en-GB";
    utter.voice = bestVoice(s.voice);
    utter.rate = 0.96; utter.pitch = 1.05;
    var timer = setInterval(function () {
      onAmplitude(Math.abs(Math.sin(Date.now() / 200)) * 0.5 + 0.3);
    }, 50);
    utter.onstart = function () { onAmplitude(0.45); };
    utter.onend = function () { clearInterval(timer); onAmplitude(0); if (onEnd) onEnd(); };
    utter.onerror = function () { clearInterval(timer); onAmplitude(0); if (onEnd) onEnd(); };
    speechSynthesis.speak(utter);
    return true;
  }

  /* ---------- Lex page ---------- */
  window.initLex = function () {
    var root = document.getElementById("lex-inline") || document.getElementById("lex-root");
    if (!root || root.dataset.lexInit === "1") return;
    root.dataset.lexInit = "1";
    var integrated = root.id === "lex-inline";
    var state = "idle", amplitude = 0;
    var context = new LexContextManager();
    var sessionId = null, recognition = null, audioStream = null, audioCtx = null, raf = null;
    var fileFlow = null;

    var stars = "";
    for (var i = 0; i < 64; i++) {
      var left = (i * 37 % 100), top = (i * 61 % 100), delay = (i % 11) * 0.23;
      var op = 0.15 + (i % 5) * 0.12;
      stars += '<i style="left:' + left + '%;top:' + top + '%;opacity:' + op + ';animation-delay:' + delay + 's"></i>';
    }

    var head =
      '<div class="lex-panel-head"><span class="lex-dot" id="lex-dot"></span>' +
      '<strong>LEX · CORE LINK</strong><span class="lex-status" id="lex-status">IDLE</span></div>';
    var core =
      '<div class="lex-main">' +
        '<div class="lex-orb-wrap">' +
          '<div class="lex-orb" id="lex-orb" data-state="idle">' +
            '<div class="lex-ring lex-ring-1"></div><div class="lex-ring lex-ring-2"></div>' +
            '<div class="lex-ring lex-ring-3"></div><div class="lex-scan"></div>' +
            '<div class="lex-core"></div><div class="lex-corona"></div>' +
          '</div>' +
          '<div class="lex-hint" id="lex-hint">' + tr("idle") + '</div>' +
          '<div class="lex-jurisdiction">⚖ ' + (integrated ? 'PlantGuard knowledge · Lex voice' : tr("jurisdiction")) + '</div>' +
        '</div>' +
        '<div class="lex-controls">' +
          '<button type="button" class="lex-btn lex-btn-primary" id="lex-mic">🎙 Start listening</button>' +
          '<button type="button" class="lex-btn" id="lex-settings">' + tr("settings") + '</button>' +
        '</div>' +
        '<div class="lex-banner" id="lex-banner" hidden>' + tr("voiceUnsupported") + '</div>' +
      '</div>';

    if (integrated) {
      root.innerHTML =
        '<div class="lex-shell lex-shell-inline">' +
          '<div class="lex-stars">' + stars + '</div>' + head +
          '<div class="lex-inline-body">' + core +
            '<div class="lex-inline-note">Speak naturally and Lex will answer in this chat. Your typed messages below work exactly the same.</div>' +
          '</div>' +
        '</div>' +
        '<div class="lex-settings" id="lex-settings-panel" hidden></div>';
    } else {
      root.innerHTML =
        '<div class="lex-shell">' +
          '<div class="lex-stars">' + stars + '</div>' + core +
          '<aside class="lex-panel">' + head +
            '<div class="lex-messages" id="lex-messages"><p class="lex-empty">' + tr("empty") + '</p></div>' +
            '<div class="lex-filebar" id="lex-filebar" hidden><button type="button" class="lex-btn" id="lex-pick">📎 Upload document</button></div>' +
            '<form class="lex-compose" id="lex-form">' +
              '<input id="lex-input" type="text" placeholder="Ask Lex anything…" autocomplete="off" />' +
              '<button type="submit" class="lex-send">' + tr("send") + '</button>' +
            '</form>' +
          '</aside>' +
        '</div>' +
        '<div class="lex-settings" id="lex-settings-panel" hidden></div>';
    }

    var orb = document.getElementById("lex-orb");
    var hint = document.getElementById("lex-hint");
    var messages = document.getElementById("lex-messages");
    var statusEl = document.getElementById("lex-status");
    var dot = document.getElementById("lex-dot");
    var input = document.getElementById("lex-input");
    var filebar = document.getElementById("lex-filebar");

    function paintOrb() {
      var map = ORB_COLORS[getOrbColor()] || ORB_COLORS.violet;
      orb.style.setProperty("--ring1", map.ring1);
      orb.style.setProperty("--ring2", map.ring2);
      orb.style.setProperty("--glow", map.glow);
      orb.style.setProperty("--amp", amplitude.toFixed(3));
      orb.dataset.state = state;
      statusEl.textContent = state === "listening" ? "LISTENING" : state === "speaking" ? "SPEAKING" : state === "processing" ? "PROCESSING" : "IDLE";
      hint.textContent = state === "listening" ? tr("listening") : state === "processing" ? tr("processing") : tr("idle");
      dot.className = "lex-dot lex-dot-" + state;
    }
    function setState(next) { state = next; paintOrb(); }
    function setAmplitude(v) { amplitude = Math.max(0, Math.min(1, v)); paintOrb(); }

    function addMessage(role, text) {
      if (messages) {
        var empty = messages.querySelector(".lex-empty");
        if (empty) empty.remove();
        var el = document.createElement("div");
        el.className = "lex-msg lex-msg-" + role;
        el.textContent = text;
        messages.appendChild(el);
        messages.scrollTop = messages.scrollHeight;
      }
      context.addTurn(role, text);
    }

    function respond(text) {
      if (!text) { setState("idle"); return; }
      setState("speaking");
      speak(text, setAmplitude, function () { setState("idle"); });
    }

    var LEGAL_INTENTS = {
      ANALYZE_DOCUMENT: 1, GENERATE_DOCUMENT: 1, ASK_QUESTION: 1, IRAC_MEMO: 1,
    };

    function send(transcript, explicitIntent) {
      var parsed = explicitIntent || parseIntent(transcript);
      setState("processing");
      context.setContext("chatting");

      if (integrated && !LEGAL_INTENTS[parsed.intent] && window.lexAssistant) {
        addMessage("user", transcript);
        var htmlReply = window.lexAssistant.submit(transcript);
        var spoken = window.lexAssistant.replyText(htmlReply);
        addMessage("assistant", spoken);
        respond(spoken);
        return;
      }

      apiCall("/api/voice", {
        transcript: transcript, intent: parsed.intent, jurisdiction: "NG",
        session_id: sessionId, context_history: context.getHistory(), language: getPreferredLanguage(),
      }).then(function (res) {
        sessionId = res.session_id || sessionId;
        addMessage("user", transcript);
        addMessage("assistant", res.response_text || "Done.");
        if (res.should_navigate_to === "analyze" && filebar) {
          filebar.hidden = false;
          fileFlow = "analyze";
          respond("I'm ready to analyze a document. Please upload a file or take a photo.");
          return;
        }
        respond(res.response_text || "Done.");
      }).catch(function () {
        setState("idle");
        addMessage("assistant", "I couldn't reach the DocuSense API. Check the connection and try again.");
      });
    }
    window.lexSend = send;

    /* speech recognition */
    var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) document.getElementById("lex-banner").hidden = false;

    function startMic() {
      if (!SR) { (input || document.getElementById("chat-input") || document.body).focus(); return; }
      if (recognition) { stopMic(); return; }
      recognition = new SR();
      recognition.lang = LANGUAGE_TO_LOCALE[getPreferredLanguage()] || "en-GB";
      recognition.continuous = true;
      recognition.interimResults = false;
      recognition.onresult = function (event) {
        var text = "";
        for (var i = event.resultIndex; i < event.results.length; i++) text += event.results[i][0].transcript;
        text = text.trim();
        if (!text) return;
        if (detectWakeWord(text, getCompanionName(), getPreferredLanguage())) {
          setState("listening");
          addMessage("assistant", "I'm listening. What would you like me to do?");
        } else {
          send(text);
        }
      };
      recognition.onerror = function () { stopMic(); };
      recognition.start();
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
          audioStream = stream;
          try {
            var AC = window.AudioContext || window.webkitAudioContext;
            audioCtx = new AC();
            var src = audioCtx.createMediaStreamSource(stream);
            var analyser = audioCtx.createAnalyser();
            analyser.fftSize = 512;
            src.connect(analyser);
            var data = new Uint8Array(analyser.frequencyBinCount);
            function loop() {
              analyser.getByteTimeDomainData(data);
              var sum = 0;
              for (var i = 0; i < data.length; i++) { var v = (data[i] - 128) / 128; sum += v * v; }
              setAmplitude(Math.sqrt(sum / data.length) * 2.2);
              raf = requestAnimationFrame(loop);
            }
            loop();
          } catch (e) { /* amplitude stays simulated */ }
        }).catch(function () {});
      }
      setState("listening");
      document.getElementById("lex-mic").textContent = "⏹ Stop listening";
    }
    function stopMic() {
      if (recognition) { try { recognition.stop(); } catch (e) {} recognition = null; }
      if (raf) cancelAnimationFrame(raf);
      if (audioCtx) { try { audioCtx.close(); } catch (e) {} audioCtx = null; }
      if (audioStream) { audioStream.getTracks().forEach(function (t) { t.stop(); }); audioStream = null; }
      setAmplitude(0);
      setState("idle");
      document.getElementById("lex-mic").textContent = "🎙 Start listening";
    }

    document.getElementById("lex-mic").addEventListener("click", startMic);
    var form = document.getElementById("lex-form");
    if (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var v = input.value.trim(); if (!v) return;
        input.value = ""; send(v);
      });
    }

    var pick = document.getElementById("lex-pick");
    if (pick) {
      pick.addEventListener("click", function () {
        var picker = document.createElement("input");
        picker.type = "file"; picker.accept = ".pdf,.txt,.docx,image/*";
        picker.onchange = function () {
          var file = picker.files && picker.files[0]; if (!file) return;
          addMessage("user", "Uploaded " + file.name);
          setState("processing");
          apiCall("/api/analyze", { file_name: file.name, jurisdiction: "NG" }).then(function (res) {
            addMessage("assistant", "Your " + (res.document_type || "document") + " has a "
              + (res.risk_level || "MEDIUM") + " risk score of " + (res.risk_score || 0)
              + " out of 100. " + (res.verdict_reason || ""));
            filebar.hidden = true;
            respond(res.verdict_reason || "Analysis complete.");
          });
        };
        picker.click();
      });
    }

    /* settings panel */
    var panel = document.getElementById("lex-settings-panel");
    document.getElementById("lex-settings").addEventListener("click", function () {
      var cur = settings();
      panel.hidden = !panel.hidden;
      if (panel.hidden) return;
      panel.innerHTML =
        '<div class="lex-set-card"><h3>Name &amp; wake word</h3>' +
          '<input id="set-name" maxlength="20" value="' + cur.name + '" />' +
          '<div class="lex-chips">' + SUGGESTED_NAMES.map(function (n) {
            return '<button type="button" data-name="' + n + '">' + n + '</button>';
          }).join("") + '</div>' +
          '<p class="lex-note">Say “Hey ' + cur.name + '” to activate.</p></div>' +
        '<div class="lex-set-card"><h3>Orb colour</h3><div class="lex-swatches">' +
          Object.keys(ORB_COLORS).map(function (c) {
            return '<button type="button" data-color="' + c + '" class="lex-swatch' + (c === cur.color ? ' selected' : '') +
              '" style="--sw:' + ORB_COLORS[c].glow + '" title="' + c + '"></button>';
          }).join("") + '</div></div>' +
        '<div class="lex-set-card"><h3>Voice accent</h3><div class="lex-voices">' +
          Object.keys(VOICE_TO_BROWSER_NAMES).map(function (v) {
            return '<button type="button" data-voice="' + v + '" class="' + (v === cur.voice ? 'selected' : '') + '">' +
              '<strong>' + v + '</strong><small>' + VOICE_DESCRIPTIONS[v] + '</small>' +
              '<span data-play="' + v + '">▶</span></button>';
          }).join("") + '</div></div>' +
        '<div class="lex-set-card"><h3>Response language</h3><div class="lex-chips">' +
          LANGS.map(function (l) {
            return '<button type="button" data-lang="' + l + '" class="' + (l === cur.language ? 'selected' : '') + '">' +
              l.toUpperCase() + '</button>';
          }).join("") + '</div><p class="lex-note" id="lex-lang-note">' +
          'Lex will listen and respond in ' + LANGUAGE_NAMES[cur.language] + '.</p>' +
          (["yo", "ha", "ig"].indexOf(cur.language) !== -1 ? '<p class="lex-note">Voice accent may default to English. Native voice coming soon.</p>' : '') +
          '</div>' +
        '<button type="button" class="lex-btn lex-btn-primary" id="lex-save">Save settings</button>';

      var draft = Object.assign({}, cur);
      panel.querySelectorAll("[data-name]").forEach(function (b) {
        b.onclick = function () { draft.name = b.dataset.name; document.getElementById("set-name").value = draft.name; };
      });
      panel.querySelectorAll("[data-color]").forEach(function (b) {
        b.onclick = function () { draft.color = b.dataset.color; saveOrbColor(draft.color); paintOrb(); };
      });
      panel.querySelectorAll("[data-voice]").forEach(function (b) {
        b.onclick = function () { draft.voice = b.dataset.voice; };
      });
      panel.querySelectorAll("[data-play]").forEach(function (b) {
        b.onclick = function (e) {
          e.stopPropagation();
          var old = getCompanionVoice(); saveCompanionVoice(b.dataset.play);
          speak("Hello. I'm " + draft.name + ". Your AI legal companion. How can I help you today?", setAmplitude, function () {
            saveCompanionVoice(old);
          });
        };
      });
      panel.querySelectorAll("[data-lang]").forEach(function (b) {
        b.onclick = function () {
          draft.language = b.dataset.lang;
          document.getElementById("lex-lang-note").textContent =
            "Lex will listen and respond in " + LANGUAGE_NAMES[draft.language] + ".";
        };
      });
      document.getElementById("lex-save").onclick = function () {
        draft.name = (document.getElementById("set-name").value || "Lex").replace(/[^A-Za-z]/g, "").slice(0, 20) || "Lex";
        saveAllCompanionSettings({ name: draft.name, color: draft.color, voice: draft.voice, language: draft.language });
        panel.hidden = true;
        paintOrb();
        if (API) fetch(API + "/api/users/me", {
          method: "PATCH", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ companion_name: draft.name, companion_color: draft.color,
                                 companion_voice: draft.voice, preferred_language: draft.language }),
        }).catch(function () {});
      };
    });

    paintOrb();
  };
})();
