import type { LyricLine, Song, Match, SnippetRange } from './types';

// @ts-ignore - Vite env
const API_BASE = import.meta.env?.VITE_API_URL || 'http://localhost:8000';

// ── Mock Songs ───────────────────────────────────────────────

const SONGS: Song[] = [
  {
    id: 'just-dance-001',
    file_path: '/music/Lady Gaga/The Fame/01 - Just Dance.mp3',
    title: 'Just Dance',
    artist: 'Lady Gaga',
    album: 'The Fame',
    duration_ms: 238000,
    lrc_path: '/music/Lady Gaga/The Fame/01 - Just Dance.lrc',
  },
  {
    id: 'dont-stop-believin-001',
    file_path: '/music/Journey/Greatest Hits/01 - Don\'t Stop Believin\'.mp3',
    title: "Don't Stop Believin'",
    artist: 'Journey',
    album: "Greatest Hits",
    duration_ms: 249000,
    lrc_path: '/music/Journey/Greatest Hits/01 - Don\'t Stop Believin\'.lrc',
  },
  {
    id: 'we-are-champions-001',
    file_path: '/music/Queen/News of the World/09 - We Are the Champions.mp3',
    title: 'We Are the Champions',
    artist: 'Queen',
    album: 'News of the World',
    duration_ms: 182000,
    lrc_path: '/music/Queen/News of the World/09 - We Are the Champions.lrc',
  },
  {
    id: 'poker-face-001',
    file_path: '/music/Lady Gaga/The Fame/02 - Poker Face.mp3',
    title: 'Poker Face',
    artist: 'Lady Gaga',
    album: 'The Fame',
    duration_ms: 237000,
    lrc_path: '/music/Lady Gaga/The Fame/02 - Poker Face.lrc',
  },
];

// ── Mock Lyrics ──────────────────────────────────────────────

const LYRICS: Record<string, LyricLine[]> = {
  'just-dance-001': [
    { timestamp_ms: 0, text: 'RedOne', timestamp_str: '00:00.00' },
    { timestamp_ms: 10250, text: 'Konvict', timestamp_str: '00:10.25' },
    { timestamp_ms: 13440, text: 'Gaga', timestamp_str: '00:13.44' },
    { timestamp_ms: 15200, text: 'Oh-oh, eh', timestamp_str: '00:15.20' },
    { timestamp_ms: 23450, text: "I've had a little bit too much, much", timestamp_str: '00:23.45' },
    { timestamp_ms: 27600, text: 'All of the people start to rush, start to rush by', timestamp_str: '00:27.60' },
    { timestamp_ms: 32500, text: "A dizzy twisted dance, can't find my drink or man", timestamp_str: '00:32.50' },
    { timestamp_ms: 36800, text: 'Where are my keys? I lost my phone, phone', timestamp_str: '00:36.80' },
    { timestamp_ms: 41200, text: "(Go, go, go, go, go, go, go, go)", timestamp_str: '00:41.20' },
    { timestamp_ms: 45000, text: "What's going on on the floor?", timestamp_str: '00:45.00' },
    { timestamp_ms: 47200, text: 'I love this record, baby, but I can\'t see straight anymore', timestamp_str: '00:47.20' },
    { timestamp_ms: 52300, text: 'Keep it cool, what\'s the name of this club?', timestamp_str: '00:52.30' },
    { timestamp_ms: 56400, text: "I can't remember but it's alright, a-alright", timestamp_str: '00:56.40' },
    { timestamp_ms: 61200, text: "Just dance, gonna be okay", timestamp_str: '01:01.20' },
    { timestamp_ms: 63400, text: "Da-da-doo-doo, just dance", timestamp_str: '01:03.40' },
    { timestamp_ms: 65600, text: 'Spin that record, babe', timestamp_str: '01:05.60' },
    { timestamp_ms: 67800, text: "Da-da-doo-doo, just dance", timestamp_str: '01:07.80' },
    { timestamp_ms: 70100, text: "Gonna be okay", timestamp_str: '01:10.10' },
    { timestamp_ms: 72300, text: "Da-da-doo-doo, just dance", timestamp_str: '01:12.30' },
    { timestamp_ms: 74500, text: "Spin that record, babe", timestamp_str: '01:14.50' },
    { timestamp_ms: 76700, text: "Da-da-doo-doo, just dance", timestamp_str: '01:16.70' },
    { timestamp_ms: 78900, text: "Gonna be okay, d-d-d-dance", timestamp_str: '01:18.90' },
    { timestamp_ms: 81100, text: "Dance, dance, just, j-j-just dance", timestamp_str: '01:21.10' },
    { timestamp_ms: 83450, text: "Gonna be okay", timestamp_str: '01:23.45' },
    { timestamp_ms: 85120, text: "Da-da-da-dance, dance, dance", timestamp_str: '01:25.12' },
    { timestamp_ms: 88000, text: "Just, j-j-just dance", timestamp_str: '01:28.00' },
    { timestamp_ms: 92000, text: "Wish I could shut my playboy mouth", timestamp_str: '01:32.00' },
    { timestamp_ms: 96300, text: "How'd I turn my shirt inside out? Inside out, babe", timestamp_str: '01:36.30' },
    { timestamp_ms: 101000, text: "Control your poison, babe, roses with thorns they say", timestamp_str: '01:41.00' },
    { timestamp_ms: 105400, text: "And we're all getting hosed tonight", timestamp_str: '01:45.40' },
    { timestamp_ms: 109800, text: "(Go, go, go, go, go, go, go, go)", timestamp_str: '01:49.80' },
    { timestamp_ms: 113500, text: "What's going on on the floor?", timestamp_str: '01:53.50' },
    { timestamp_ms: 115700, text: "I love this record, baby, but I can't see straight anymore", timestamp_str: '01:55.70' },
    { timestamp_ms: 120800, text: "Keep it cool, what's the name of this club?", timestamp_str: '02:00.80' },
    { timestamp_ms: 125000, text: "I can't remember but it's alright, a-alright", timestamp_str: '02:05.00' },
    { timestamp_ms: 129800, text: "Just dance, gonna be okay", timestamp_str: '02:09.80' },
    { timestamp_ms: 132000, text: "Da-da-doo-doo, just dance", timestamp_str: '02:12.00' },
    { timestamp_ms: 134200, text: "Spin that record, babe", timestamp_str: '02:14.20' },
    { timestamp_ms: 136400, text: "Da-da-doo-doo, just dance", timestamp_str: '02:16.40' },
    { timestamp_ms: 138600, text: "Gonna be okay", timestamp_str: '02:18.60' },
    { timestamp_ms: 140800, text: "Da-da-doo-doo, just dance", timestamp_str: '02:20.80' },
    { timestamp_ms: 143000, text: "Spin that record, babe", timestamp_str: '02:23.00' },
    { timestamp_ms: 145200, text: "Da-da-doo-doo, just dance", timestamp_str: '02:25.20' },
    { timestamp_ms: 147400, text: "Gonna be okay, d-d-d-dance", timestamp_str: '02:27.40' },
    { timestamp_ms: 149600, text: "Dance, dance, just, j-j-just dance", timestamp_str: '02:29.60' },
    { timestamp_ms: 154000, text: "Colby O'Donis:", timestamp_str: '02:34.00' },
    { timestamp_ms: 155500, text: "When I come through on the dance floor checkin' out that catalog", timestamp_str: '02:35.50' },
    { timestamp_ms: 159800, text: "Can't believe my eyes, so many women without a flaw", timestamp_str: '02:39.80' },
    { timestamp_ms: 164200, text: "And I ain't gonna give it up, steady tryna pick it up like a call", timestamp_str: '02:44.20' },
    { timestamp_ms: 168600, text: "I'ma hit it, I'ma beat it and flex and do it until tomorrow, yeah", timestamp_str: '02:48.60' },
    { timestamp_ms: 173000, text: "Shawty I can see that you got so much energy", timestamp_str: '02:53.00' },
    { timestamp_ms: 175500, text: "The way you're twirlin' up them hips 'round and 'round", timestamp_str: '02:55.50' },
    { timestamp_ms: 177400, text: "And now there's no reason at all why you can't leave here with me", timestamp_str: '02:57.40' },
    { timestamp_ms: 180600, text: "In the meantime stay and let me watch you break it down", timestamp_str: '03:00.60' },
    { timestamp_ms: 183200, text: "Just dance, gonna be okay", timestamp_str: '03:03.20' },
    { timestamp_ms: 185400, text: "Da-da-doo-doo, just dance", timestamp_str: '03:05.40' },
    { timestamp_ms: 187600, text: "Spin that record, babe", timestamp_str: '03:07.60' },
    { timestamp_ms: 189800, text: "Da-da-doo-doo, just dance", timestamp_str: '03:09.80' },
    { timestamp_ms: 192000, text: "Gonna be okay", timestamp_str: '03:12.00' },
    { timestamp_ms: 194200, text: "Da-da-doo-doo, just dance", timestamp_str: '03:14.20' },
    { timestamp_ms: 196400, text: "Spin that record, babe", timestamp_str: '03:16.40' },
    { timestamp_ms: 198600, text: "Da-da-doo-doo, just dance", timestamp_str: '03:18.60' },
    { timestamp_ms: 200800, text: "Gonna be okay, d-d-d-dance", timestamp_str: '03:20.80' },
    { timestamp_ms: 203000, text: "Dance, dance, just, j-j-just dance", timestamp_str: '03:23.00' },
    { timestamp_ms: 210000, text: "(Go, go, go, go, go, go, go, go)", timestamp_str: '03:30.00' },
    { timestamp_ms: 218000, text: "Half psychotic, sick, hypnotic", timestamp_str: '03:38.00' },
    { timestamp_ms: 220200, text: "Got my blueprint, it's symphonic", timestamp_str: '03:40.20' },
    { timestamp_ms: 222400, text: "Half psychotic, sick, hypnotic", timestamp_str: '03:42.40' },
    { timestamp_ms: 224600, text: "Got my blueprint, electronic", timestamp_str: '03:44.60' },
    { timestamp_ms: 226800, text: "Half psychotic, sick, hypnotic", timestamp_str: '03:46.80' },
    { timestamp_ms: 229000, text: "Got my blueprint, it's symphonic", timestamp_str: '03:49.00' },
    { timestamp_ms: 231200, text: "Half psychotic, sick, hypnotic", timestamp_str: '03:51.20' },
    { timestamp_ms: 233400, text: "Got my blueprint, electronic", timestamp_str: '03:53.40' },
    { timestamp_ms: 235600, text: "Go, use your muscle, carve it out, work it, hustle", timestamp_str: '03:55.60' },
    { timestamp_ms: 240000, text: "I got it, just stay close enough to get it on", timestamp_str: '04:00.00' },
    { timestamp_ms: 242200, text: "Don't slow, drive it, clean it, Lysol, bleed it", timestamp_str: '04:02.20' },
    { timestamp_ms: 246600, text: "Spend the last dough in your pocko", timestamp_str: '04:06.60' },
    { timestamp_ms: 248800, text: "Just dance, gonna be okay", timestamp_str: '04:08.80' },
    { timestamp_ms: 251000, text: "Da-da-doo-doo, just dance", timestamp_str: '04:11.00' },
    { timestamp_ms: 253200, text: "Spin that record, babe", timestamp_str: '04:13.20' },
    { timestamp_ms: 255400, text: "Da-da-doo-doo, just dance", timestamp_str: '04:15.40' },
    { timestamp_ms: 257600, text: "Gonna be okay", timestamp_str: '04:17.60' },
    { timestamp_ms: 259800, text: "Da-da-doo-doo, just dance", timestamp_str: '04:19.80' },
    { timestamp_ms: 262000, text: "Spin that record, babe", timestamp_str: '04:22.00' },
    { timestamp_ms: 264200, text: "Da-da-doo-doo, just dance", timestamp_str: '04:24.20' },
    { timestamp_ms: 266400, text: "Gonna be okay, d-d-d-dance", timestamp_str: '04:26.40' },
    { timestamp_ms: 268600, text: "Dance, dance, just, j-j-just dance", timestamp_str: '04:28.60' },
    { timestamp_ms: 273000, text: "Just, j-j-just dance", timestamp_str: '04:33.00' },
  ],
  'dont-stop-believin-001': [
    { timestamp_ms: 5200, text: "Just a small town girl", timestamp_str: '00:05.20' },
    { timestamp_ms: 10400, text: "Livin' in a lonely world", timestamp_str: '00:10.40' },
    { timestamp_ms: 15700, text: "She took the midnight train goin' anywhere", timestamp_str: '00:15.70' },
    { timestamp_ms: 26200, text: "Just a city boy", timestamp_str: '00:26.20' },
    { timestamp_ms: 31300, text: "Born and raised in South Detroit", timestamp_str: '00:31.30' },
    { timestamp_ms: 36600, text: "He took the midnight train goin' anywhere", timestamp_str: '00:36.60' },
    { timestamp_ms: 57600, text: "A singer in a smoky room", timestamp_str: '00:57.60' },
    { timestamp_ms: 63000, text: "A smell of wine and cheap perfume", timestamp_str: '01:03.00' },
    { timestamp_ms: 68200, text: "For a smile they can share the night", timestamp_str: '01:08.20' },
    { timestamp_ms: 73500, text: "It goes on and on and on and on", timestamp_str: '01:13.50' },
    { timestamp_ms: 84000, text: "Strangers waitin'", timestamp_str: '01:24.00' },
    { timestamp_ms: 86500, text: "Up and down the boulevard", timestamp_str: '01:26.50' },
    { timestamp_ms: 89200, text: "Their shadows searchin' in the night", timestamp_str: '01:29.20' },
    { timestamp_ms: 94500, text: "Streetlights, people", timestamp_str: '01:34.50' },
    { timestamp_ms: 97000, text: "Livin' just to find emotion", timestamp_str: '01:37.00' },
    { timestamp_ms: 99700, text: "Hidin', somewhere in the night", timestamp_str: '01:39.70' },
    { timestamp_ms: 115500, text: "Workin' hard to get my fill", timestamp_str: '01:55.50' },
    { timestamp_ms: 120800, text: "Everybody wants a thrill", timestamp_str: '02:00.80' },
    { timestamp_ms: 126100, text: "Payin' anything to roll the dice", timestamp_str: '02:06.10' },
    { timestamp_ms: 131400, text: "Just one more time", timestamp_str: '02:11.40' },
    { timestamp_ms: 136700, text: "Some'll win, some will lose", timestamp_str: '02:16.70' },
    { timestamp_ms: 142000, text: "Some were born to sing the blues", timestamp_str: '02:22.00' },
    { timestamp_ms: 147300, text: "Oh, the movie never ends", timestamp_str: '02:27.30' },
    { timestamp_ms: 152600, text: "It goes on and on and on and on", timestamp_str: '02:32.60' },
    { timestamp_ms: 163200, text: "Strangers waitin'", timestamp_str: '02:43.20' },
    { timestamp_ms: 165700, text: "Up and down the boulevard", timestamp_str: '02:45.70' },
    { timestamp_ms: 168400, text: "Their shadows searchin' in the night", timestamp_str: '02:48.40' },
    { timestamp_ms: 173700, text: "Streetlights, people", timestamp_str: '02:53.70' },
    { timestamp_ms: 176200, text: "Livin' just to find emotion", timestamp_str: '02:56.20' },
    { timestamp_ms: 178900, text: "Hidin', somewhere in the night", timestamp_str: '02:58.90' },
    { timestamp_ms: 194700, text: "Don't stop believin'", timestamp_str: '03:14.70' },
    { timestamp_ms: 199700, text: "Hold on to that feelin'", timestamp_str: '03:19.70' },
    { timestamp_ms: 205000, text: "Streetlights, people", timestamp_str: '03:25.00' },
    { timestamp_ms: 210300, text: "Don't stop believin'", timestamp_str: '03:30.30' },
    { timestamp_ms: 215600, text: "Hold on to that feelin'", timestamp_str: '03:35.60' },
    { timestamp_ms: 220900, text: "Streetlights, people", timestamp_str: '03:40.90' },
    { timestamp_ms: 226200, text: "Don't stop believin'", timestamp_str: '03:46.20' },
    { timestamp_ms: 231500, text: "Hold on to that feelin'", timestamp_str: '03:51.50' },
    { timestamp_ms: 236800, text: "Streetlights, people", timestamp_str: '03:56.80' },
    { timestamp_ms: 242100, text: "Don't stop believin'", timestamp_str: '04:02.10' },
    { timestamp_ms: 247400, text: "Hold on to that feelin'", timestamp_str: '04:07.40' },
  ],
  'we-are-champions-001': [
    { timestamp_ms: 12400, text: "I've paid my dues", timestamp_str: '00:12.40' },
    { timestamp_ms: 17600, text: "Time after time", timestamp_str: '00:17.60' },
    { timestamp_ms: 22800, text: "I've done my sentence", timestamp_str: '00:22.80' },
    { timestamp_ms: 28000, text: "But committed no crime", timestamp_str: '00:28.00' },
    { timestamp_ms: 34400, text: "And bad mistakes", timestamp_str: '00:34.40' },
    { timestamp_ms: 39600, text: "I've made a few", timestamp_str: '00:39.60' },
    { timestamp_ms: 45600, text: "I've had my share of sand kicked in my face", timestamp_str: '00:45.60' },
    { timestamp_ms: 53200, text: "But I've come through", timestamp_str: '00:53.20' },
    { timestamp_ms: 61200, text: "And we mean to go on and on and on and on", timestamp_str: '01:01.20' },
    { timestamp_ms: 74000, text: "We are the champions, my friends", timestamp_str: '01:14.00' },
    { timestamp_ms: 82400, text: "And we'll keep on fighting till the end", timestamp_str: '01:22.40' },
    { timestamp_ms: 91200, text: "We are the champions", timestamp_str: '01:31.20' },
    { timestamp_ms: 96800, text: "We are the champions", timestamp_str: '01:36.80' },
    { timestamp_ms: 102000, text: "No time for losers", timestamp_str: '01:42.00' },
    { timestamp_ms: 108000, text: "'Cause we are the champions of the world", timestamp_str: '01:48.00' },
    { timestamp_ms: 122000, text: "I've taken my bows", timestamp_str: '02:02.00' },
    { timestamp_ms: 127200, text: "And my curtain calls", timestamp_str: '02:07.20' },
    { timestamp_ms: 132400, text: "You brought me fame and fortune", timestamp_str: '02:12.40' },
    { timestamp_ms: 136800, text: "And everything that goes with it", timestamp_str: '02:16.80' },
    { timestamp_ms: 140000, text: "I thank you all", timestamp_str: '02:20.00' },
    { timestamp_ms: 145600, text: "But it's been no bed of roses", timestamp_str: '02:25.60' },
    { timestamp_ms: 148800, text: "No pleasure cruise", timestamp_str: '02:28.80' },
    { timestamp_ms: 154400, text: "I consider it a challenge before the whole human race", timestamp_str: '02:34.40' },
    { timestamp_ms: 162000, text: "And I ain't gonna lose", timestamp_str: '02:42.00' },
    { timestamp_ms: 169600, text: "And we mean to go on and on and on and on", timestamp_str: '02:49.60' },
    { timestamp_ms: 181600, text: "We are the champions, my friends", timestamp_str: '03:01.60' },
    { timestamp_ms: 190000, text: "And we'll keep on fighting till the end", timestamp_str: '03:10.00' },
    { timestamp_ms: 198800, text: "We are the champions", timestamp_str: '03:18.80' },
    { timestamp_ms: 204400, text: "We are the champions", timestamp_str: '03:24.40' },
    { timestamp_ms: 209600, text: "No time for losers", timestamp_str: '03:29.60' },
    { timestamp_ms: 215600, text: "'Cause we are the champions of the world", timestamp_str: '03:35.60' },
  ],
  'poker-face-001': [
    { timestamp_ms: 600, text: "Mum mum mum mah", timestamp_str: '00:00.60' },
    { timestamp_ms: 1800, text: "Mum mum mum mah", timestamp_str: '00:01.80' },
    { timestamp_ms: 11400, text: "I wanna hold 'em like they do in Texas, please", timestamp_str: '00:11.40' },
    { timestamp_ms: 16200, text: "Fold 'em, let 'em hit me, raise it, baby, stay with me", timestamp_str: '00:16.20' },
    { timestamp_ms: 21600, text: "(I love it)", timestamp_str: '00:21.60' },
    { timestamp_ms: 23400, text: "LoveGame intuition, play the cards with spades to start", timestamp_str: '00:23.40' },
    { timestamp_ms: 28200, text: "And after he's been hooked, I'll play the one that's on his heart", timestamp_str: '00:28.20' },
    { timestamp_ms: 33000, text: "Oh, whoa, oh, oh", timestamp_str: '00:33.00' },
    { timestamp_ms: 36600, text: "Whoa, oh, oh, oh, oh, oh", timestamp_str: '00:36.60' },
    { timestamp_ms: 41400, text: "I'll get him hot, show him what I've got", timestamp_str: '00:41.40' },
    { timestamp_ms: 46200, text: "Oh, whoa, oh, oh", timestamp_str: '00:46.20' },
    { timestamp_ms: 49800, text: "Whoa, oh, oh, oh, oh, oh", timestamp_str: '00:49.80' },
    { timestamp_ms: 54600, text: "I'll get him hot, show him what I've got", timestamp_str: '00:54.60' },
    { timestamp_ms: 59400, text: "Can't read my, can't read my", timestamp_str: '00:59.40' },
    { timestamp_ms: 61800, text: "No, he can't read my poker face", timestamp_str: '01:01.80' },
    { timestamp_ms: 65400, text: "(She's got me like nobody)", timestamp_str: '01:05.40' },
    { timestamp_ms: 67800, text: "Can't read my, can't read my", timestamp_str: '01:07.80' },
    { timestamp_ms: 70200, text: "No, he can't read my poker face", timestamp_str: '01:10.20' },
    { timestamp_ms: 73800, text: "(She's got me like nobody)", timestamp_str: '01:13.80' },
    { timestamp_ms: 77400, text: "P-p-p-poker face, p-p-poker face", timestamp_str: '01:17.40' },
    { timestamp_ms: 81000, text: "(Mum mum mum mah)", timestamp_str: '01:21.00' },
    { timestamp_ms: 84600, text: "P-p-p-poker face, p-p-poker face", timestamp_str: '01:24.60' },
    { timestamp_ms: 88200, text: "(Mum mum mum mah)", timestamp_str: '01:28.20' },
    { timestamp_ms: 92400, text: "I wanna roll with him, a hard pair we will be", timestamp_str: '01:32.40' },
    { timestamp_ms: 97200, text: "A little gamblin' is fun when you're with me", timestamp_str: '01:37.20' },
    { timestamp_ms: 100800, text: "(I love it)", timestamp_str: '01:40.80' },
    { timestamp_ms: 104400, text: "Russian roulette is not the same without a gun", timestamp_str: '01:44.40' },
    { timestamp_ms: 109200, text: "And baby, when it's love, if it's not rough, it isn't fun, fun", timestamp_str: '01:49.20' },
    { timestamp_ms: 118200, text: "Oh, whoa, oh, oh", timestamp_str: '01:58.20' },
    { timestamp_ms: 121800, text: "Whoa, oh, oh, oh, oh, oh", timestamp_str: '02:01.80' },
    { timestamp_ms: 126600, text: "I'll get him hot, show him what I've got", timestamp_str: '02:06.60' },
    { timestamp_ms: 130200, text: "Can't read my, can't read my", timestamp_str: '02:10.20' },
    { timestamp_ms: 132600, text: "No, he can't read my poker face", timestamp_str: '02:12.60' },
    { timestamp_ms: 136200, text: "(She's got me like nobody)", timestamp_str: '02:16.20' },
    { timestamp_ms: 138600, text: "Can't read my, can't read my", timestamp_str: '02:18.60' },
    { timestamp_ms: 141000, text: "No, he can't read my poker face", timestamp_str: '02:21.00' },
    { timestamp_ms: 144600, text: "(She's got me like nobody)", timestamp_str: '02:24.60' },
    { timestamp_ms: 148200, text: "P-p-p-poker face, p-p-poker face", timestamp_str: '02:28.20' },
    { timestamp_ms: 151800, text: "(Mum mum mum mah)", timestamp_str: '02:31.80' },
    { timestamp_ms: 155400, text: "P-p-p-poker face, p-p-poker face", timestamp_str: '02:35.40' },
    { timestamp_ms: 159000, text: "(Mum mum mum mah)", timestamp_str: '02:39.00' },
    { timestamp_ms: 162600, text: "I won't tell you that I love you, kiss or hug you", timestamp_str: '02:42.60' },
    { timestamp_ms: 167400, text: "'Cause I'm bluffin' with my muffin", timestamp_str: '02:47.40' },
    { timestamp_ms: 172200, text: "I'm not lyin', I'm just stunnin' with my love-glue-gunning", timestamp_str: '02:52.20' },
    { timestamp_ms: 177000, text: "Just like a chick in the casino", timestamp_str: '02:57.00' },
    { timestamp_ms: 179400, text: "Take your bank before I pay you out", timestamp_str: '02:59.40' },
    { timestamp_ms: 183000, text: "I promise this, promise this", timestamp_str: '03:03.00' },
    { timestamp_ms: 185400, text: "Check this hand 'cause I'm marvelous", timestamp_str: '03:05.40' },
    { timestamp_ms: 190200, text: "Can't read my, can't read my", timestamp_str: '03:10.20' },
    { timestamp_ms: 192600, text: "No, he can't read my poker face", timestamp_str: '03:12.60' },
    { timestamp_ms: 196200, text: "(She's got me like nobody)", timestamp_str: '03:16.20' },
    { timestamp_ms: 198600, text: "Can't read my, can't read my", timestamp_str: '03:18.60' },
    { timestamp_ms: 201000, text: "No, he can't read my poker face", timestamp_str: '03:21.00' },
    { timestamp_ms: 204600, text: "(She's got me like nobody)", timestamp_str: '03:24.60' },
    { timestamp_ms: 208200, text: "P-p-p-poker face, p-p-poker face", timestamp_str: '03:28.20' },
    { timestamp_ms: 211800, text: "(Mum mum mum mah)", timestamp_str: '03:31.80' },
    { timestamp_ms: 215400, text: "P-p-p-poker face, p-p-poker face", timestamp_str: '03:35.40' },
    { timestamp_ms: 219000, text: "(Mum mum mum mah)", timestamp_str: '03:39.00' },
    { timestamp_ms: 222600, text: "P-p-p-poker face, p-p-poker face", timestamp_str: '03:42.60' },
    { timestamp_ms: 226200, text: "(Mum mum mum mah)", timestamp_str: '03:46.20' },
    { timestamp_ms: 229800, text: "P-p-p-poker face, p-p-poker face", timestamp_str: '03:49.80' },
    { timestamp_ms: 233400, text: "(Mum mum mum mah)", timestamp_str: '03:53.40' },
  ],
};

// ── API Functions ────────────────────────────────────────────

export async function searchLyrics(query: string, limit = 20): Promise<Match[]> {
  await delay(150 + Math.random() * 200);

  if (!query.trim()) return [];

  const results: Match[] = [];
  const q = query.toLowerCase();

  for (const song of SONGS) {
    const lyrics = LYRICS[song.id];
    if (!lyrics) continue;

    for (let i = 0; i < lyrics.length; i++) {
      const line = lyrics[i];
      const text = line.text.toLowerCase();
      let score = 0;
      let matchType = '';

      if (text === q) {
        score = 1.0;
        matchType = 'exact';
      } else if (text.includes(q)) {
        score = 0.85 + (q.length / text.length) * 0.15;
        matchType = 'contains';
      } else {
        const lineWords = text.split(/\s+/);
        const queryWords = q.split(/\s+/);
        const matches = queryWords.filter(w => lineWords.some(lw => lw.includes(w)));
        if (matches.length > 0) {
          score = matches.length / queryWords.length * 0.7;
          matchType = 'word-match';
        }
      }

      if (score > 0) {
        const contextBefore = lyrics.slice(Math.max(0, i - 2), i);
        const contextAfter = lyrics.slice(i + 1, Math.min(lyrics.length, i + 3));

        results.push({
          song,
          matched_line: line,
          context_before: contextBefore,
          context_after: contextAfter,
          match_score: Math.round(score * 100) / 100,
          match_type: matchType,
        });
      }
    }
  }

  results.sort((a, b) => b.match_score - a.match_score);
  return results.slice(0, limit);
}

export async function getSongLyrics(songId: string): Promise<LyricLine[]> {
  await delay(100 + Math.random() * 150);
  return LYRICS[songId] || [];
}

export async function getSong(songId: string): Promise<Song | null> {
  await delay(50);
  return SONGS.find(s => s.id === songId) || null;
}

export async function playAudio(songId: string, startMs?: number, endMs?: number): Promise<string> {
  await delay(200);
  return `/api/audio/${songId}?start=${startMs ?? 0}&end=${endMs ?? ''}`;
}

export async function exportSnippet(
  songId: string,
  startMs: number,
  endMs: number,
  filename: string,
  bitrate?: string
): Promise<Blob> {
  await delay(1000 + Math.random() * 1500);

  const mockContent = `MP3_DATA:${songId}:${startMs}:${endMs}:${bitrate || '192k'}:${filename}`;
  return new Blob([mockContent], { type: 'audio/mpeg' });
}

export function getAudioUrl(songId: string, range?: SnippetRange): string {
  if (range) {
    return `${API_BASE}/api/audio/${songId}?start=${range.start_ms}&end=${range.end_ms}`;
  }
  return `${API_BASE}/api/audio/${songId}`;
}

// ── Helpers ──────────────────────────────────────────────────

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
