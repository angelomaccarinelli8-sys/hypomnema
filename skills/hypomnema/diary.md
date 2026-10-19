# Hypomnema: notebook and diary (Claude Code)

Read this when the user asks what was said («cosa ci eravamo detti su…»). It is section 6 of
`SKILL.md`.

There are two places to search, and they are not the same thing:

- the **notebook** is the **chosen notes**: `P search <word>`;
- the **diary** is **the whole recorded conversation**, raw: the user's messages and, if the
  replies witness is on, your replies. `P diary <word>`; with `--around` you also see the message
  just before and just after each one found; `P diary --last 10` shows the last ten.

When the user asks «cosa ci eravamo detti su…», «cosa ti avevo detto di…», «cosa mi avevi
consigliato…»:

1. search **the notebook first**;
2. **then, if needed**, the diary;
3. always say **where** the answer comes from: «Dalle note del quaderno (scelte da te): …» or
   «Dal diario, cioè dalla conversazione registrata, non da una nota: …». A note is the user's
   choice; the diary is only what was said. Something found only in the diary is **not** a
   decision, even if it sounded like one: if the user wants to keep it, propose a note.

You can also use the diary to reread what you advised and notice if you are now saying the
opposite: in that case tell the user openly.
