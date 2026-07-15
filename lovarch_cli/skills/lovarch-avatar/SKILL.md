---
name: lovarch-avatar
description: Crea e usa un avatar video parlante (il TUO volto) col Content Studio Lovarch — foto per URL, la piattaforma addestra e genera (crediti). Trigger — "avatar", "il mio volto nel video", "video parlante", "digital twin", "avatar che parla", "clone video".
---

# Lovarch · Avatar

Crei un avatar riutilizzabile dal TUO ritratto e generi video in cui parla uno
script. Le foto si passano per **URL** (la piattaforma le scarica) — non serve
caricare file.

## ⚠️ Consenso (GDPR) — obbligatorio
Lovarch consente SOLO l'autoritratto dell'utente stesso. Ogni creazione richiede un
`consent_text`: un'attestazione ESPLICITA (min 20 caratteri) che il ritratto è il
proprio volto. Non inventare il consenso al posto dell'utente — chiediglielo.

## Flusso
1. **Crea l'avatar** (foto per URL; per addestrare la LoRA servono ≥10 foto, quindi
   passa più angoli/luci in `additional_photo_urls`):
   ```
   lovarch_avatar_create({
     name: "Il mio avatar",
     portrait_url: "https://…/ritratto.jpg",
     consent_text: "Confermo che il ritratto è il mio volto e autorizzo…",
     additional_photo_urls: ["https://…/1.jpg", "https://…/2.jpg", …]
   }) → { avatar_id }
   ```
2. **Addestra** (avvisa dei crediti): `lovarch_avatar_train({ avatar_id }) → job` ;
   poi `lovarch_avatar_status({ avatar_id })` fino a `ready` (con `loraUrl`).
3. **Genera** il video (avvisa dei crediti):
   ```
   lovarch_avatar_generate({ avatar_id, voice_id: "<voce>", script: "<parlato>" })
   → { job_id } ; poi lovarch_video_status
   ```

## Note
- Crediti per training e generazione (mai costi in $). Tutto in galleria.
- Per lo script parlato usa il craft di `lovarch-voce`/`@lovarch-screenwriter`.
