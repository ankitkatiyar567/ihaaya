# Ihaaya Star Chart

A picture star chart for young children. Every evening she rates her own day: 1 to 5 stars, or 1 to 5 crosses, for each picture. Tap a picture to hear the question. Grown-ups tap + each time she cries. On Friday evening the weekly report shows running stars when the week's score reaches the goal (60%), and a gentle "not this time" with what to practise when it doesn't.

The app opens on a logo screen that asks for the 4-digit parent PIN (the first time, you choose it). With more than one child it then asks who is rating today. After 5 minutes in the background it locks again. Use it as a phone app: iPhone Safari → Share → Add to Home Screen; Android Chrome → ⋮ → Install app. It opens full screen in portrait and works without internet (sw.js keeps a copy, network first).

🎮 Daily game: when every picture is rated and the day reaches the goal, the day's game opens for 3 minutes (2, 3 or 5 in Settings), for that day only. Six games: 🎈 balloon pop, 🃏 memory match, 🧺 star catcher, 🐹 peek-a-boo, 🔢 counting and ⭕ tic-tac-toe with a kind Teddy. Each child gets one a day in a shuffled order (every game once in six days, never twice in a row). She can stop and come back; the time adds up, and her best score is kept per game.

🌙 Bedtime story: every night, one story from LibriVox.org (free public-domain recordings read by volunteers, played from the Internet Archive): 1,140 nights, about 3 years, starting with Peter Rabbit. Arthur Scott Bailey's animal tales, Beatrix Potter, Raggedy Ann and Andy, The Sandman, the Hollow Tree books, the Velveteen Rabbit, Just So Stories and Aesop. Only authors who died before 1956 are used, so the stories are free in the EU too. A heard story moves on the next day; a half-heard one carries on where it stopped. `tools/build-stories.py` rebuilds `stories.json` and checks every file against the Internet Archive.

Each child has a profile with their own pictures, goal, reward, stars and Friday report. Grown-ups tap the child's picture at the top right to open the parent menu (switch child, add a child, settings, backup). The menu is locked with a 4-digit parent PIN, a lock for little fingers; only a salted hash of the PIN is stored. While locked, a child can add a cry to the counter but not take one away.

Open the page: https://ankitkatiyar567.github.io/ihaya/

The stars, notes and photos stay in the browser that you use (localStorage). Nothing is sent anywhere. Use ⚙️ Settings → Download backup (all children) to keep a copy or to move the stars to another phone or computer.
