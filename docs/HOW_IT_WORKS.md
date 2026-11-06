# How it works, in plain words

This explains what Tukang Copilot does behind each screen, for someone who doesn't write code. The technical version with diagrams is [ARCHITECTURE.md](ARCHITECTURE.md), and the model-by-model version is [AI_PIPELINE.md](AI_PIPELINE.md).

## The problem (why)

In Indonesia most people fix their own motorbike, water pump and rice cooker, or pay a bengkel without knowing if the price is fair. A lot of small faults (a fouled spark plug, a worn tap washer, an air leak on a pump) are a 10-minute job if someone shows you exactly which part to touch. A generic chatbot can't see your bike, and a YouTube video shows somebody else's bike. I wanted something that looks at **your** photo, points at **your** part, checks **your** work, and says plainly when a job is too dangerous to do yourself.

## Who it is for

Owners with a phone and a broken thing, in Bahasa Indonesia, Basa Jawa or English. No account, no app store install. Mechanics benefit too: the owner can hand them a one-page report of what was already tried.

## What happens on one repair (what, how)

1. **You send a photo and say what's wrong.** Up to 3 photos, plus a voice note or typed text.
2. **Listen.** Your voice note becomes text. Bahasa and English go to Muse Voice Transcribe. Basa Jawa goes to Muse Spark 1.2, because the speech model has no Javanese.
3. **Safety gate, before anything is spent.** If your words describe something only a professional should touch (brake failure, a gas smell, mains wiring), the app stops right there with a red STOP card and says who to call. No model is called and no money is spent. I tested 23 dangerous owner messages against the live system and all 23 were stopped.
4. **Look.** Muse Spark 1.3 looks at the photo and names the object and the parts that matter, with a rough box around each.
5. **Find the parts.** SAM 3.1 turns each rough box into an exact outline of that part on your photo. That is where the numbered coloured shapes come from.
6. **Diagnose.** Muse Spark 1.3 ranks the likely causes with a percentage. If the top cause is under 60%, it asks you one yes/no question first instead of guessing.
7. **Plan.** Muse Spark 1.3 writes the steps, the tools, the parts with an estimated price, the difficulty and the time. Each step says what it should look like when done, so the camera can check it.
8. **Second safety check.** The plan itself is checked again, by rules in the code and by the model's own safety level. A plan that touches fuel lines, gas, brake hydraulics or high voltage becomes a red STOP.
9. **Illustrate.** For a step that is hard to picture, Muse Image draws a diagram from your own photo, and Muse Spark reviews the drawing. A bad drawing is redrawn once, or dropped.
10. **Guide and check.** You follow one step per screen. After a step you take a photo and Muse Spark compares it with what the step should look like. ✅ means move on. ⚠️ says exactly what to fix.
11. **Re-plan.** If it is still broken, you say what happened and the app plans for the next likely cause, remembering what was already tried. When no safe cause is left, it tells you to see a mechanic and gives you the report to show them.

## Where your data goes

Photos and the repair live in one folder on the server and are deleted after 24 hours, or right away with the erase button. There are no accounts and no tracking. The Meta key stays on the server; the phone never sees it. Logs never contain your text or the key ([SAFETY.md](SAFETY.md)). A guide link you share lets someone read the repair, but only your phone can answer, check a step, re-plan, mark it done or erase it. If the server restarts while a repair is running, the repair comes back with a Try again button and carries on from where it got to.

## What is real and what is sample

- **Real:** every answer in live mode comes from the real Meta Model API. The recorded 1-tap demo is a real live run, saved so it plays even when the free server is asleep, and it is labelled as a recording on screen.
- **Sample:** the sample photos are AI-generated and carry a visible "Sample photo (AI-generated)" tag. Offline sample mode (no key) uses pre-written answers and says so in an orange line at the top. Bengkel prices are labelled estimates.
- **Not measured yet:** I have not run real owner trials, so I make no claims about money saved by real people ([IMPACT.md](IMPACT.md)).

## When it says no

The app refuses to guide gas, mains electricity, high voltage, brake hydraulics, fuel lines and airbags. It also stops when your words sound like an emergency. A refusal is never a dead end: it names the kind of professional to call and keeps the report so you can show them.
