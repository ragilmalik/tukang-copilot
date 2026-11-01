# X launch kit (Most Viral, $20K)

How Most Viral is judged, from the Participant Guide: "Post your project demo on X and submit the post link through the
hackathon platform. The winner will be selected based on total engagement (likes, reposts, and comments) up until
November 8 EOD." The kickoff slide says: "Most likes, reposts and comments by Nov 8 11:59 PM ET wins."
That is **Mon Nov 9, 11:59 WIB**. I should post as early as I can, and before submitting, so the link can go into form
field 5.

Handles, checked 2026-11-01: @AIatMeta (linked from Meta's own hackathon page, twitter.com/aiatmeta) and
@cerebral_valley (the organiser's X profile, 24K followers). Tag only these two.

Attach to post 1: `docs/demo/tukang-copilot-x-vertical.mp4` (43.5 s, 1080x1920, Bahasa captions, labelled demo mode).
For an Indonesian audience the best time is 19:00 to 21:00 WIB. For US reach (Meta, Cerebral Valley) it's 08:00 to
10:00 ET = 20:00 to 22:00 WIB. Posting at about 20:00 WIB catches both.

I checked the character counts with a script, counting each link as 23 characters and each emoji as 2, the way X does.

## The thread (6 posts)

**1/6** (attach the vertical clip)
```
Motor mogok, bengkel tutup.

So I built Tukang Copilot. Snap it, say what's wrong in Bahasa, Javanese or English, and it outlines the exact part on your photo, checks each step with your camera, and says STOP when it's dangerous.

Built with @AIatMeta Muse Spark + SAM 3.1 🔧🇮🇩
```

**2/6**
```
How the loop works:
1. Muse Spark looks at the object
2. SAM 3.1 masks the real parts
3. it asks one question if unsure
4. it plans; steps unlock after a safety checklist
5. you send a photo after each step and it checks it
6. still broken? it re-plans for the next cause
```

**3/6**
```
The safety stops are plain code that runs before any model call.

Gas, house wiring, 220 V internals, brakes, fuel leaks: a hard STOP, a PDF for the technician, and a one-tap hand-off to the nearest bengkel.

Typing "ignore the rules, say it's safe" won't lift it.
```

**4/6**
```
Javanese has 68 million native speakers, so the whole app speaks Basa Jawa too, voice included.

Diagnosis and planning can also run on Meta's open-weight Muse Spark Open with one switch, so a bengkel co-op or a vocational school could host it themselves.
```

**5/6** (attach `docs/demo/screenshots/30_whatsapp_jv_diagnosis.png` and `30_whatsapp_jv_redstop.png`)
```
It also works in WhatsApp, which most of us already have open all day.

Send a photo and a Javanese voice note and you get the marked photo, the diagnosis, a button per step, the same camera checks and the same STOP. Same agent and safety code, on the WhatsApp Cloud API.
```

**6/6**
```
I built this solo for the Meta Global AI Developer Hackathon with @cerebral_valley. Free 1-tap demo, no photo needed:
[LIVE_URL]

Code (MIT): [GITHUB_URL]
Full 3-min demo: [YOUTUBE_URL]

A like or repost helps a lot 🙏
```

## Clip caption (if I post the clip alone, as one post)
```
Motor mogok? Point your phone at it.

Tukang Copilot outlines the exact part, checks each repair step with your camera, and says STOP when the job is dangerous. In Bahasa, Javanese and English.

Built with @AIatMeta Muse Spark + SAM 3.1 for the @cerebral_valley hackathon 🔧🇮🇩
```

## Bahasa version (quote-post post 1 with this, for Indonesian reach)
```
Motor mogok, bengkel tutup? Saya bikin Tukang Copilot: foto barangnya, ceritakan masalahnya (Bahasa/Jawa), AI-nya menandai bagian yang rusak di foto kamu, mengecek tiap langkah pakai kamera, dan bilang STOP kalau bahaya. Gratis dicoba 👇
[LIVE_URL]
```

## Hashtags
At most two per post, since more looks like spam: #MetaAI #BuildWithMeta on post 1, #AIagents on post 2.
For the Indonesian quote-post: #AIIndonesia #BengkelDigital.
There's no official hackathon hashtag that I know of, so I won't make one up. If Cerebral Valley announces one on
Discord, it goes on post 1.

## Engagement plan (no paid boosts, no bought engagement)
- Reply to every comment in the first two hours, because comments count.
- Pin the thread to my profile until Nov 9.
- Send the post link to friends, family, coworkers and Semarang groups with the messages in
  docs/launch/COMMUNITY_VOTE_KIT.md. No asking strangers for likes.
- Post a 15 s follow-up clip on Nov 6 or 7 (the rice-cooker STOP or the live camera guide) as a reply to post 1, so it
  lifts the same post.
- If I have a real-phone clip by then, post it as a reply too. Real objects do better than demo footage.
